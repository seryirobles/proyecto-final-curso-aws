"""Tests for the whole-week generation worker use case (FR-AI-03, FR-AI-09,
FR-AI-12, NFR-AI-01): mode semantics, per-slot progress, per-slot isolation,
additive writes, the idempotent-invocation guard and the kill-switch."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from datetime import date

import pytest
from support.fakes import (
    FakeAiProvider,
    FakeGenerationGate,
    FakeGenerationQueue,
    FakeRecipeRepository,
    FakeWeekRepository,
)

from planner_core.application.week_generation import (
    WeekGenerationOutcome,
    run_week_generation,
)
from planner_core.domain.ai_output import RawIngredient, RawRecipeOutput
from planner_core.domain.ai_prompt import CategoryPrompt
from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import Candidate, SlotContents
from planner_core.domain.generation import (
    GenerationMode,
    GenerationRequest,
    RunStatus,
    SlotProgress,
    SlotStatus,
)
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import MealSnapshot, Recipe
from planner_core.domain.rules import CategoryCountRule, RuleSet
from planner_core.messages import (
    AI_GENERATION_INSUFFICIENT_LIBRARY_RECIPES,
    AI_GENERATION_UNAVAILABLE,
)
from planner_core.ports.ai_provider import AiPrompt, AiProviderError
from planner_core.ports.generation_queue import StoredGeneration
from planner_core.ports.recipes import LibraryRecipe

WEEK = IsoWeek(2026, 34)
KEY = "hash-1"
SATURDAY = date.fromisocalendar(2026, 34, 6)  # 4 open slots: Sat + Sun, lunch + dinner
SUNDAY = date.fromisocalendar(2026, 34, 7)  # 2 open slots


def _submitted_queue() -> FakeGenerationQueue:
    queue = FakeGenerationQueue()
    queue.stored[KEY] = StoredGeneration(idempotency_key=KEY, status="pending", slots=())
    return queue


def _run(
    *,
    queue: FakeGenerationQueue,
    weeks: FakeWeekRepository,
    provider: FakeAiProvider | None = None,
    gate: FakeGenerationGate | None = None,
    recipes: FakeRecipeRepository | None = None,
    mode: GenerationMode = GenerationMode.MIX,
    rules: RuleSet | None = None,
    first_day: date = SUNDAY,
    author: str = "u-1",
) -> WeekGenerationOutcome:
    return run_week_generation(
        KEY,
        GenerationRequest(week=WEEK, mode=mode),
        rules if rules is not None else RuleSet(),
        "v1",
        author,
        first_day,
        provider=provider if provider is not None else FakeAiProvider(),
        weeks=weeks,
        recipes=recipes if recipes is not None else FakeRecipeRepository(),
        queue=queue,
        gate=gate if gate is not None else FakeGenerationGate(),
    )


def _meal(name: str = "Existente") -> MealSnapshot:
    return MealSnapshot(
        name=name, ingredients=(), tools=(), procedure=(), category=IngredientCategory.MEAT
    )


def _library(*specs: tuple[str, str, IngredientCategory]) -> FakeRecipeRepository:
    repo = FakeRecipeRepository()
    for recipe_id, name, category in specs:
        recipe = Recipe(
            name=name,
            ingredients=(),
            tools=("olla",),
            procedure=("Cocer.",),
            category=category,
        )
        repo.entries[recipe_id] = LibraryRecipe(id=recipe_id, recipe=recipe, author="chef")
    return repo


def _statuses(queue: FakeGenerationQueue) -> dict[tuple[int, int], SlotStatus]:
    return {(p.day, p.slot): p.status for p in queue.stored[KEY].slots or ()}


def test_outcome_and_progress_are_frozen() -> None:
    """docs/conventions.md — every new frozen dataclass gets this test."""
    outcome = WeekGenerationOutcome(claimed=True, terminal_status=RunStatus.COMPLETED, per_slot=())
    with pytest.raises(dataclasses.FrozenInstanceError):
        outcome.__setattr__("claimed", False)


# --- per-slot independence + authorship -------------------------------------


def test_a_provider_failure_on_one_slot_leaves_the_others_persisted() -> None:
    weeks = FakeWeekRepository()
    good = RawRecipeOutput(
        name="Buena",
        ingredients=(RawIngredient(name="arroz", quantity=100.0, unit="g"),),
        tools=("olla",),
        procedure=("Cocer.",),
        category="carbohydrate",
    )
    provider = FakeAiProvider(responses=[good, AiProviderError("boom"), good, good])
    queue = _submitted_queue()

    outcome = _run(queue=queue, weeks=weeks, provider=provider, first_day=SATURDAY)

    statuses = [r.status for r in outcome.per_slot]
    assert statuses.count(SlotStatus.DONE) == 3 and statuses.count(SlotStatus.ERROR) == 1
    persisted = [c for slot in weeks.get_week(WEEK).values() for c in slot.candidates]
    assert len(persisted) == 3
    assert all(c.author == "u-1" for c in persisted)
    assert outcome.terminal_status is RunStatus.PARTIAL  # R25


def test_each_success_is_its_own_week_write() -> None:
    weeks = FakeWeekRepository()

    _run(queue=_submitted_queue(), weeks=weeks, first_day=SUNDAY)

    assert weeks.versions[WEEK] == 2


# --- additive, definitive outranks -----------------------------------------


def test_generation_is_additive_and_skips_a_slot_that_is_definitive_now() -> None:
    weeks = FakeWeekRepository()
    lunch = SlotRef(SUNDAY, MealSlot.LUNCH)
    dinner = SlotRef(SUNDAY, MealSlot.DINNER)
    existing = Candidate(id="c0", meal=_meal(), author="chef")
    weeks.save_slot(WEEK, lunch, SlotContents(candidates=(existing,), definitive_id="c0"))
    weeks.save_slot(WEEK, dinner, SlotContents(candidates=(existing,)))
    baseline = weeks.versions[WEEK]

    outcome = _run(queue=_submitted_queue(), weeks=weeks, first_day=SUNDAY)

    lunch_now = weeks.get_week(WEEK)[lunch]
    assert lunch_now.candidates == (existing,) and lunch_now.definitive_id == "c0"
    dinner_now = weeks.get_week(WEEK)[dinner]
    assert existing in dinner_now.candidates and len(dinner_now.candidates) == 2
    assert weeks.versions[WEEK] == baseline + 1  # only the dinner write
    assert {(r.day, r.status) for r in outcome.per_slot} == {(7, SlotStatus.DONE)}


def test_a_definitive_appearing_after_target_resolution_is_not_overwritten() -> None:
    """The skip is governed by the same-step re-read, not the stale pre-loop occupancy."""
    lunch = SlotRef(SUNDAY, MealSlot.LUNCH)
    dinner = SlotRef(SUNDAY, MealSlot.DINNER)
    promoted = Candidate(id="c0", meal=_meal(), author="chef")
    saved: list[SlotRef] = []
    reads = 0

    class _Weeks(FakeWeekRepository):
        def get_week(self, week: IsoWeek) -> Mapping[SlotRef, SlotContents]:
            nonlocal reads
            reads += 1
            if reads == 1:  # resolve_targets sees both SUNDAY slots open
                return {}
            return {lunch: SlotContents(candidates=(promoted,), definitive_id="c0")}

        def save_slot(self, week: IsoWeek, slot: SlotRef, contents: SlotContents) -> int:
            saved.append(slot)
            return super().save_slot(week, slot, contents)

    outcome = _run(queue=_submitted_queue(), weeks=_Weeks(), first_day=SUNDAY)

    assert lunch not in saved
    assert dinner in saved
    lunch_result = next(r for r in outcome.per_slot if r.slot == int(MealSlot.LUNCH.value))
    assert (lunch_result.status, lunch_result.error) == (SlotStatus.DONE, None)


# --- idempotent invocation ---------------------------------------------------


def test_a_lost_claim_invokes_no_provider_and_records_nothing() -> None:
    provider = FakeAiProvider()
    queue = FakeGenerationQueue()
    queue.stored[KEY] = StoredGeneration(idempotency_key=KEY, status="running")

    outcome = _run(queue=queue, weeks=FakeWeekRepository(), provider=provider)

    assert outcome.claimed is False and outcome.per_slot == ()
    assert provider.calls == 0
    assert queue.events == []


def test_a_redelivery_after_completion_invokes_no_provider() -> None:
    provider = FakeAiProvider()
    queue = FakeGenerationQueue()
    queue.stored[KEY] = StoredGeneration(idempotency_key=KEY, status="completed", result="[]")

    _run(queue=queue, weeks=FakeWeekRepository(), provider=provider)

    assert provider.calls == 0


# --- live per-slot progress (R17-R27) ---------------------------------------


def test_progress_is_pending_first_then_running_then_done_then_the_run_status() -> None:
    queue = _submitted_queue()

    _run(queue=queue, weeks=FakeWeekRepository(), first_day=SUNDAY)

    assert queue.events == [
        "begin_slots",  # R17
        "slot:7-1:running",  # R18
        "slot:7-1:done",  # R19
        "slot:7-2:running",
        "slot:7-2:done",
        "status:completed",  # R27 — last
    ]
    assert queue.stored[KEY].status == "completed"


def test_begin_slots_records_every_open_slot_pending() -> None:
    seen: list[tuple[SlotProgress, ...]] = []

    class _Queue(FakeGenerationQueue):
        def begin_slots(self, idempotency_key: str, slots: tuple[SlotProgress, ...]) -> None:
            seen.append(slots)
            super().begin_slots(idempotency_key, slots)

    queue = _Queue()
    queue.stored[KEY] = StoredGeneration(idempotency_key=KEY, status="pending", slots=())

    _run(queue=queue, weeks=FakeWeekRepository(), first_day=SUNDAY)

    assert [p.status for p in seen[0]] == [SlotStatus.PENDING] * 2
    assert [(p.day, p.slot) for p in seen[0]] == [(7, 1), (7, 2)]


def test_a_failed_slot_carries_a_code_and_an_es_message() -> None:
    queue = _submitted_queue()
    provider = FakeAiProvider(responses=[AiProviderError("x"), AiProviderError("y")])

    outcome = _run(queue=queue, weeks=FakeWeekRepository(), provider=provider)

    assert all(p.error is not None and p.error.code == "invalid_output" for p in outcome.per_slot)
    assert outcome.terminal_status is RunStatus.FAILED  # R26


def test_a_run_with_no_open_slot_completes() -> None:
    queue = _submitted_queue()
    rules = RuleSet(disabled_days=(6, 7))

    outcome = _run(queue=queue, weeks=FakeWeekRepository(), rules=rules, first_day=SUNDAY)

    assert outcome.terminal_status is RunStatus.COMPLETED  # R24
    assert queue.stored[KEY].status == "completed"


# --- kill-switch -------------------------------------------------------------


def test_a_disabled_gate_invokes_no_provider_and_marks_every_slot_unavailable() -> None:
    weeks = FakeWeekRepository()
    provider = FakeAiProvider()
    queue = _submitted_queue()

    outcome = _run(
        queue=queue,
        weeks=weeks,
        provider=provider,
        gate=FakeGenerationGate(enabled=False),
        first_day=SUNDAY,
    )

    assert provider.calls == 0
    assert weeks.versions.get(WEEK) is None
    errors = [p.error for p in outcome.per_slot]
    assert [e.message for e in errors if e] == [AI_GENERATION_UNAVAILABLE] * 2
    assert [e.code for e in errors if e] == ["generation_unavailable"] * 2
    assert outcome.terminal_status is RunStatus.FAILED


def test_the_gate_is_read_before_every_ai_slot() -> None:
    gate = FakeGenerationGate(enabled=True)

    _run(queue=_submitted_queue(), weeks=FakeWeekRepository(), gate=gate, first_day=SUNDAY)

    assert gate.reads == 2


# --- mode semantics (R1-R16) -------------------------------------------------


def test_library_only_never_invokes_the_provider_even_with_the_gate_disabled() -> None:
    """R1, R15 — library fill ignores the kill-switch."""
    provider = FakeAiProvider()
    gate = FakeGenerationGate(enabled=False)
    library = _library(
        ("r1", "Lentejas", IngredientCategory.LEGUME), ("r2", "Arroz", IngredientCategory.MEAT)
    )
    queue = _submitted_queue()
    weeks = FakeWeekRepository()

    outcome = _run(
        queue=queue,
        weeks=weeks,
        provider=provider,
        gate=gate,
        recipes=library,
        mode=GenerationMode.LIBRARY_ONLY,
    )

    assert provider.calls == 0 and gate.reads == 0
    assert outcome.terminal_status is RunStatus.COMPLETED
    persisted = [c for s in weeks.get_week(WEEK).values() for c in s.candidates]
    assert {c.meal.name for c in persisted} == {"Lentejas", "Arroz"}  # R2
    assert all(c.author == "u-1" for c in persisted)


def test_library_only_records_insufficient_library_recipes_for_unfilled_slots() -> None:
    """R3 — one recipe for two slots."""
    library = _library(("r1", "Lentejas", IngredientCategory.LEGUME))
    queue = _submitted_queue()

    outcome = _run(
        queue=queue, weeks=FakeWeekRepository(), recipes=library, mode=GenerationMode.LIBRARY_ONLY
    )

    by_slot = {(p.day, p.slot): p for p in outcome.per_slot}
    failed = next(p for p in by_slot.values() if p.status is SlotStatus.ERROR)
    assert failed.error is not None
    assert failed.error.code == "insufficient_library_recipes"
    assert failed.error.message == AI_GENERATION_INSUFFICIENT_LIBRARY_RECIPES
    assert outcome.terminal_status is RunStatus.PARTIAL


def test_ai_only_never_reads_the_library() -> None:
    """R4."""

    class _Exploding(FakeRecipeRepository):
        def list_all(self) -> tuple[LibraryRecipe, ...]:
            raise AssertionError("ai_only read the library")

    outcome = _run(
        queue=_submitted_queue(),
        weeks=FakeWeekRepository(),
        recipes=_Exploding(),
        mode=GenerationMode.AI_ONLY,
        first_day=SUNDAY,
    )

    assert outcome.terminal_status is RunStatus.COMPLETED


def test_mix_fills_from_the_library_before_any_provider_call() -> None:
    """R5, R6 — library slots first; the AI only for the slot left without a candidate."""
    library = _library(("r1", "Lentejas", IngredientCategory.LEGUME))
    provider = FakeAiProvider()
    queue = _submitted_queue()

    outcome = _run(queue=queue, weeks=FakeWeekRepository(), recipes=library, provider=provider)

    assert provider.calls == 1
    assert queue.events[1].endswith(":done")  # the library slot is settled first
    assert queue.events[2].endswith(":running")  # then the AI slot starts
    assert outcome.terminal_status is RunStatus.COMPLETED


def test_mix_sends_the_ai_only_the_needs_the_library_did_not_cover() -> None:
    """R12 — one legume came from the library; the prompt asks for none."""
    library = _library(("r1", "Lentejas", IngredientCategory.LEGUME))
    prompts: list[AiPrompt] = []

    class _Provider(FakeAiProvider):
        def generate(self, prompt: AiPrompt) -> RawRecipeOutput:
            prompts.append(prompt)
            return super().generate(prompt)

    rules = RuleSet(category_counts=(CategoryCountRule(IngredientCategory.LEGUME, 1),))
    _run(
        queue=_submitted_queue(),
        weeks=FakeWeekRepository(),
        recipes=library,
        provider=_Provider(),
        rules=rules,
    )

    assert len(prompts) == 1
    assert isinstance(prompts[0], CategoryPrompt)
    assert prompts[0].category_counts == (CategoryCountRule(IngredientCategory.LEGUME, 0),)


def test_library_fill_excludes_a_name_already_in_the_week() -> None:
    """R8."""
    weeks = FakeWeekRepository()
    lunch = SlotRef(SUNDAY, MealSlot.LUNCH)
    existing = Candidate(id="c0", meal=_meal("LENTEJAS"), author="chef")
    weeks.save_slot(WEEK, lunch, SlotContents(candidates=(existing,)))
    library = _library(("r1", "lentejas", IngredientCategory.LEGUME))

    outcome = _run(
        queue=_submitted_queue(), weeks=weeks, recipes=library, mode=GenerationMode.LIBRARY_ONLY
    )

    assert {p.status for p in outcome.per_slot} == {SlotStatus.ERROR}


def test_a_library_pick_is_a_candidate_and_never_replaces_a_definitive() -> None:
    """R13, R14 — the definitive appeared after target resolution."""
    lunch = SlotRef(SUNDAY, MealSlot.LUNCH)
    promoted = Candidate(id="c0", meal=_meal(), author="chef")
    reads = 0

    class _Weeks(FakeWeekRepository):
        def get_week(self, week: IsoWeek) -> Mapping[SlotRef, SlotContents]:
            nonlocal reads
            reads += 1
            if reads == 1:
                return {}
            return {lunch: SlotContents(candidates=(promoted,), definitive_id="c0")}

    library = _library(("r1", "Lentejas", IngredientCategory.LEGUME))
    weeks = _Weeks()

    outcome = _run(
        queue=_submitted_queue(), weeks=weeks, recipes=library, mode=GenerationMode.LIBRARY_ONLY
    )

    assert weeks.versions.get(WEEK) is None  # nothing written
    assert any(p.status is SlotStatus.DONE for p in outcome.per_slot)


def test_equal_inputs_give_equal_library_picks() -> None:
    """R11."""
    library = _library(*((f"r{i}", f"Plato {i}", IngredientCategory.MEAT) for i in range(8)))

    def names() -> list[str]:
        weeks = FakeWeekRepository()
        _run(
            queue=_submitted_queue(), weeks=weeks, recipes=library, mode=GenerationMode.LIBRARY_ONLY
        )
        week = weeks.get_week(WEEK)
        return [
            week[s].candidates[0].meal.name
            for s in sorted(week, key=lambda r: r.day_number * 10 + int(r.slot.value))
        ]

    assert names() == names()
