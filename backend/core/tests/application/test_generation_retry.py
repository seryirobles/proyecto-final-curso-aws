"""Per-slot retry, api use case and worker (week_generation_backend R35-R53)."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest
from support.fakes import (
    FakeAiProvider,
    FakeGenerationGate,
    FakeGenerationQueue,
    FakeRecipeRepository,
    FakeWeekRepository,
)

from planner_core.application.generation_retry import retry_slot
from planner_core.application.week_generation import WeekGenerationOutcome, run_slot_retry
from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import Candidate, SlotContents
from planner_core.domain.generation import (
    GenerationMode,
    GenerationRequest,
    GenerationSnapshot,
    RunStatus,
    SlotError,
    SlotProgress,
    SlotStatus,
)
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import MealSnapshot, Recipe
from planner_core.domain.rules import PinRule, RuleSet
from planner_core.ports.generation_queue import (
    GenerationNotFound,
    GenerationSlotNotFound,
    SlotNotRetryable,
    StoredGeneration,
)
from planner_core.ports.recipes import LibraryRecipe

WEEK = IsoWeek(2026, 34)
KEY = "k"
SUNDAY = date.fromisocalendar(2026, 34, 7)
ERR = SlotError("invalid_output", "x")


def _queue(
    *statuses: tuple[int, int, SlotStatus], mode: GenerationMode = GenerationMode.MIX
) -> FakeGenerationQueue:
    queue = FakeGenerationQueue()
    slots = tuple(
        SlotProgress(d, s, st, ERR if st is SlotStatus.ERROR else None) for d, s, st in statuses
    )
    queue.stored[KEY] = StoredGeneration(
        idempotency_key=KEY,
        status="partial",
        slots=slots,
        snapshot=GenerationSnapshot(WEEK, mode, RuleSet(), "v1"),
    )
    return queue


def _retry(
    queue: FakeGenerationQueue,
    day: int = 7,
    slot: int = 1,
    weeks: FakeWeekRepository | None = None,
) -> StoredGeneration:
    return retry_slot(
        KEY, day, slot, SUNDAY, queue=queue, weeks=weeks or FakeWeekRepository(), author="u-2"
    )


def test_an_error_slot_goes_pending_and_the_run_running() -> None:  # R36, R37, R45
    queue = _queue((7, 1, SlotStatus.ERROR), (7, 2, SlotStatus.DONE))

    stored = _retry(queue)

    assert stored.status == "running"
    assert stored.slots is not None and stored.slots[0].status is SlotStatus.PENDING
    assert stored.slots[1].status is SlotStatus.DONE  # R52
    assert queue.retries == [(KEY, 7, 1, "u-2")]


@pytest.mark.parametrize("status", [SlotStatus.PENDING, SlotStatus.RUNNING, SlotStatus.DONE])
def test_a_slot_not_in_error_is_not_retryable(status: SlotStatus) -> None:  # R38
    queue = _queue((7, 1, status))

    with pytest.raises(SlotNotRetryable):
        _retry(queue)
    assert queue.retries == []


def test_a_second_retry_of_the_same_slot_is_refused() -> None:  # R40
    queue = _queue((7, 1, SlotStatus.ERROR))
    _retry(queue)

    with pytest.raises(SlotNotRetryable):
        _retry(queue)
    assert len(queue.retries) == 1


def test_a_slot_with_a_definitive_is_not_retryable() -> None:  # R39
    weeks = FakeWeekRepository()
    meal = MealSnapshot("M", (), (), (), IngredientCategory.MEAT)
    weeks.save_slot(
        WEEK,
        SlotRef(SUNDAY, MealSlot.LUNCH),
        SlotContents(candidates=(Candidate("c", meal, "a"),), definitive_id="c"),
    )
    queue = _queue((7, 1, SlotStatus.ERROR))

    with pytest.raises(SlotNotRetryable):
        _retry(queue, weeks=weeks)


def test_a_past_slot_is_not_retryable() -> None:  # R39
    queue = _queue((6, 1, SlotStatus.ERROR))

    with pytest.raises(SlotNotRetryable):
        _retry(queue, day=6)


def test_an_unknown_generation_is_not_found() -> None:  # R41
    with pytest.raises(GenerationNotFound):
        _retry(FakeGenerationQueue())


def test_a_slot_the_run_does_not_hold_is_not_found() -> None:  # R42
    with pytest.raises(GenerationSlotNotFound):
        _retry(_queue((7, 1, SlotStatus.ERROR)), slot=2)


def test_a_single_recipe_record_has_no_slot() -> None:  # R42
    queue = FakeGenerationQueue()
    queue.stored[KEY] = StoredGeneration(idempotency_key=KEY, status="failed")

    with pytest.raises(GenerationSlotNotFound):
        _retry(queue)


# --- worker side (R47-R53) --------------------------------------------------


def _worker(
    queue: FakeGenerationQueue,
    *,
    mode: GenerationMode = GenerationMode.MIX,
    provider: FakeAiProvider | None = None,
    gate: FakeGenerationGate | None = None,
    recipes: FakeRecipeRepository | None = None,
    weeks: FakeWeekRepository | None = None,
) -> WeekGenerationOutcome:
    return run_slot_retry(
        KEY,
        7,
        1,
        GenerationRequest(week=WEEK, mode=mode),
        RuleSet(),
        "v1",
        "u-2",
        SUNDAY,
        provider=provider or FakeAiProvider(),
        weeks=weeks or FakeWeekRepository(),
        recipes=recipes or FakeRecipeRepository(),
        queue=queue,
        gate=gate or FakeGenerationGate(),
    )


def test_a_slot_not_pending_is_not_processed() -> None:  # R48
    queue = _queue((7, 1, SlotStatus.ERROR))
    provider = FakeAiProvider()

    outcome = _worker(queue, provider=provider)

    assert outcome.claimed is False and provider.calls == 0


def test_a_redelivered_retry_message_is_processed_once() -> None:  # R47, R48
    queue = _queue((7, 1, SlotStatus.PENDING))
    provider = FakeAiProvider()

    first = _worker(queue, provider=provider)
    second = _worker(queue, provider=provider)

    assert first.claimed is True and second.claimed is False
    assert provider.calls == 1


def test_the_retry_writes_an_ai_candidate_for_the_retrying_user_and_settles() -> None:
    queue = _queue((7, 1, SlotStatus.PENDING), (7, 2, SlotStatus.DONE))
    weeks = FakeWeekRepository()

    outcome = _worker(queue, weeks=weeks)

    candidate = weeks.get_week(WEEK)[SlotRef(SUNDAY, MealSlot.LUNCH)].candidates[0]
    assert candidate.author == "u-2"  # R53
    assert outcome.terminal_status is RunStatus.COMPLETED  # R51
    assert queue.stored[KEY].status == "completed"
    slots = queue.stored[KEY].slots or ()
    assert slots[1] == SlotProgress(7, 2, SlotStatus.DONE)  # R52


def test_a_failing_retry_leaves_the_run_failed_or_partial() -> None:  # R51
    from planner_core.ports.ai_provider import AiProviderError

    queue = _queue((7, 1, SlotStatus.PENDING), (7, 2, SlotStatus.ERROR))

    outcome = _worker(queue, provider=FakeAiProvider(responses=[AiProviderError("x")]))

    assert outcome.terminal_status is RunStatus.FAILED


def test_library_only_retry_never_calls_the_provider_or_the_gate() -> None:  # R49
    queue = _queue((7, 1, SlotStatus.PENDING), mode=GenerationMode.LIBRARY_ONLY)
    provider, gate = FakeAiProvider(), FakeGenerationGate(enabled=False)
    repo = FakeRecipeRepository()
    recipe = Recipe("Lentejas", (), ("olla",), ("x",), IngredientCategory.LEGUME)
    repo.entries["r"] = LibraryRecipe("r", recipe, "chef")

    outcome = _worker(
        queue, mode=GenerationMode.LIBRARY_ONLY, provider=provider, gate=gate, recipes=repo
    )

    assert provider.calls == 0 and gate.reads == 0
    assert outcome.terminal_status is RunStatus.COMPLETED


def test_the_gate_is_read_before_the_retry_provider_call() -> None:  # R50
    queue = _queue((7, 1, SlotStatus.PENDING))
    provider, gate = FakeAiProvider(), FakeGenerationGate(enabled=False)

    outcome = _worker(queue, provider=provider, gate=gate)

    assert gate.reads == 1 and provider.calls == 0
    assert outcome.terminal_status is RunStatus.FAILED


def test_the_parent_runs_stored_rules_decide_whether_the_slot_is_open() -> None:  # R44
    queue = _queue((7, 1, SlotStatus.ERROR))
    stored = queue.stored[KEY]
    assert stored.snapshot is not None
    queue.stored[KEY] = replace(
        stored, snapshot=replace(stored.snapshot, rules=RuleSet(disabled_days=(7,)))
    )

    with pytest.raises(SlotNotRetryable):
        _retry(queue)  # the shared state (no rules) would leave day 7 open


def test_a_pin_in_the_stored_rules_closes_the_slot() -> None:  # R44
    queue = _queue((7, 1, SlotStatus.ERROR))
    stored = queue.stored[KEY]
    assert stored.snapshot is not None
    rules = RuleSet(pins=(PinRule(7, MealSlot.LUNCH, "r"),))
    queue.stored[KEY] = replace(stored, snapshot=replace(stored.snapshot, rules=rules))

    with pytest.raises(SlotNotRetryable):
        _retry(queue)


def test_a_retry_whose_slot_is_no_longer_open_records_done_and_writes_nothing() -> None:
    """The worker branch for a slot that gained a definitive after acceptance."""
    queue = _queue((7, 1, SlotStatus.PENDING))
    weeks = FakeWeekRepository()
    meal = MealSnapshot("M", (), (), (), IngredientCategory.MEAT)
    lunch = SlotRef(SUNDAY, MealSlot.LUNCH)
    weeks.save_slot(
        WEEK, lunch, SlotContents(candidates=(Candidate("c", meal, "a"),), definitive_id="c")
    )
    version = weeks.versions[WEEK]
    provider = FakeAiProvider()

    outcome = _worker(queue, provider=provider, weeks=weeks)

    assert outcome.claimed is True and provider.calls == 0
    assert weeks.versions[WEEK] == version
    assert outcome.per_slot == (SlotProgress(7, 1, SlotStatus.DONE),)
    assert queue.stored[KEY].status == "completed"
