"""A failed generation never strands its run: what the worker records and what it
reports back to SQS (issues/ai-failed-messages-never-retried/plan.md E1-E12, E14-E16)."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import pytest
from botocore.exceptions import ClientError
from planner_core import messages
from planner_core.domain.ai_output import GenerationFailureReason
from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import Candidate, SlotContents
from planner_core.domain.generation import RunStatus, SlotProgress, SlotStatus
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import MealSnapshot, Recipe
from planner_core.ports.generation_queue import ResultPayload, StoredGeneration
from planner_core.ports.recipes import LibraryRecipe
from support.fakes import (
    FakeAiProvider,
    FakeClock,
    FakeGenerationGate,
    FakeGenerationQueue,
    FakeRecipeRepository,
    FakeWeekRepository,
)

from planner_ai import handler, wiring
from planner_ai.adapters.bedrock import BedrockAiProvider
from planner_ai.handler import handle
from planner_ai.wiring import Dependencies

_WEEK = IsoWeek(2026, 34)
_OPEN_SLOTS = 14  # every slot of 2026-W34 when the clock reads its Monday
_RECEIVE_LIMIT = 5  # maxReceiveCount of aws_sqs_queue.generation (terraform/sqs.tf)
_REASONS = {reason.value for reason in GenerationFailureReason}
_ES_MESSAGES = {value for value in vars(messages).values() if isinstance(value, str)}
_IN_FLIGHT = {SlotStatus.PENDING, SlotStatus.RUNNING}


def _throttled() -> ClientError:
    error = {"Code": "ProvisionedThroughputExceededException", "Message": "fake"}
    return ClientError({"Error": error}, "UpdateItem")


@dataclass
class _FlakyQueue(FakeGenerationQueue):
    """The records fake with an injectable fault: the next `failures[method]`
    calls raise `error`, and `outage` makes every call raise it."""

    failures: dict[str, int] = field(default_factory=dict)
    failing_claims: set[str] = field(default_factory=set)
    outage: bool = False
    error: Exception = field(default_factory=_throttled)

    def _trip(self, method: str) -> None:
        if self.outage:
            raise self.error
        if self.failures.get(method, 0) > 0:
            self.failures[method] -= 1
            raise self.error

    def stored_generation(self, idempotency_key: str) -> StoredGeneration | None:
        self._trip("stored_generation")
        return super().stored_generation(idempotency_key)

    def claim(self, idempotency_key: str) -> bool:
        if idempotency_key in self.failing_claims:
            raise self.error
        self._trip("claim")
        return super().claim(idempotency_key)

    def claim_slot(self, idempotency_key: str, day: int, slot: int) -> bool:
        self._trip("claim_slot")
        return super().claim_slot(idempotency_key, day, slot)

    def begin_slots(self, idempotency_key: str, slots: tuple[SlotProgress, ...]) -> None:
        self._trip("begin_slots")
        super().begin_slots(idempotency_key, slots)

    def record_slot(self, idempotency_key: str, progress: SlotProgress) -> None:
        self._trip("record_slot")
        super().record_slot(idempotency_key, progress)

    def record_status(self, idempotency_key: str, status: RunStatus) -> None:
        self._trip("record_status")
        super().record_status(idempotency_key, status)

    def record_result(self, idempotency_key: str, status: str, payload: ResultPayload) -> None:
        self._trip("record_result")
        super().record_result(idempotency_key, status, payload)


@dataclass
class _FlakyWeeks(FakeWeekRepository):
    """Fails the first `failed_reads` reads and every save after `saves_left`
    saves; a failed save takes `takes_down` with it, like a table outage."""

    saves_left: int | None = None
    failed_reads: int = 0
    takes_down: _FlakyQueue | None = None

    def get_week(self, week: IsoWeek) -> Mapping[SlotRef, SlotContents]:
        if self.failed_reads > 0:
            self.failed_reads -= 1
            raise _throttled()
        return super().get_week(week)

    def save_slot(self, week: IsoWeek, slot: SlotRef, contents: SlotContents) -> int:
        if self.saves_left == 0:
            if self.takes_down is not None:
                self.takes_down.outage = True
            raise _throttled()
        if self.saves_left is not None:
            self.saves_left -= 1
        return super().save_slot(week, slot, contents)


def _deps(
    queue: FakeGenerationQueue,
    *,
    weeks: FakeWeekRepository | None = None,
    provider: FakeAiProvider | None = None,
    recipes: FakeRecipeRepository | None = None,
) -> Dependencies:
    return Dependencies(
        provider=provider if provider is not None else FakeAiProvider(),
        weeks=weeks if weeks is not None else FakeWeekRepository(),
        recipes=recipes if recipes is not None else FakeRecipeRepository(),
        records=queue,
        gate=FakeGenerationGate(),
        clock=FakeClock.at("2026-08-17T10:00:00+00:00"),
    )


def _week_body(key: str = "k1") -> str:
    return json.dumps(
        {
            "idPeticionIA": key,
            "weekId": _WEEK.week_id,
            "mode": "mix",
            "promptVersionId": "v1",
            "authorUserId": "u-1",
            "effectiveRules": {},
        }
    )


def _recipe_body(key: str = "k1") -> str:
    return json.dumps(
        {
            "type": "recipe",
            "idPeticionIA": key,
            "target": {"kind": "library"},
            "source": {"kind": "specification", "ingredients": ["lentejas"], "tools": ["olla"]},
            "referenceRecipe": None,
            "promptVersionId": "v1",
            "authorUserId": "u-1",
        }
    )


def _retry_body(day: int, slot: int, key: str = "k1") -> str:
    return json.dumps(
        {
            **json.loads(_week_body(key)),
            "type": "slot_retry",
            "day": day,
            "slot": slot,
        }
    )


def _record(body: str, receives: int = 1, message_id: str = "m-1") -> dict[str, Any]:
    """The event record AWS delivers (docs: Lambda, "Using Lambda with Amazon SQS")."""
    return {
        "messageId": message_id,
        "receiptHandle": f"r-{message_id}",
        "body": body,
        "attributes": {"ApproximateReceiveCount": str(receives)},
    }


# The value is untyped because it mirrors the JSON AWS reads back.
def _reported(result: Mapping[str, Any] | None) -> list[str]:
    """The ids handed back for redelivery; AWS reads a null response as success."""
    if result is None:
        return []
    return [failure["itemIdentifier"] for failure in result["batchItemFailures"]]


def _deliver(body: str, deps: Dependencies, *, receives: int = 1) -> list[str]:
    return _reported(handle({"Records": [_record(body, receives)]}, deps))


def _play_queue(body: str, deps: Dependencies, *, first_receive: int = 1) -> str:
    """Plays SQS: a reported message comes back, and past maxReceiveCount it is dead-lettered."""
    for receives in range(first_receive, _RECEIVE_LIMIT + 1):
        if not _deliver(body, deps, receives=receives):
            return "deleted"
    return "dead-lettered"


def _submitted(key: str = "k1", *, slots: tuple[SlotProgress, ...] | None = ()) -> _FlakyQueue:
    queue = _FlakyQueue()
    queue.stored[key] = StoredGeneration(idempotency_key=key, status="pending", slots=slots)
    return queue


def _claimed(*slots: SlotProgress) -> _FlakyQueue:
    """A week run whose worker attempt got past the claim and then died."""
    queue = _FlakyQueue()
    queue.stored["k1"] = StoredGeneration(idempotency_key="k1", status="running", slots=slots)
    return queue


def _claimed_recipe() -> _FlakyQueue:
    queue = _FlakyQueue()
    queue.stored["k1"] = StoredGeneration(idempotency_key="k1", status="running")
    return queue


def _slots(queue: FakeGenerationQueue, key: str = "k1") -> tuple[SlotProgress, ...]:
    return queue.stored[key].slots or ()


def _in_flight(queue: FakeGenerationQueue) -> list[tuple[int, int]]:
    return [(p.day, p.slot) for p in _slots(queue) if p.status in _IN_FLIGHT]


def _slot_status(queue: FakeGenerationQueue, day: int, slot: int) -> SlotStatus:
    return next(p.status for p in _slots(queue) if (p.day, p.slot) == (day, slot))


def _status(queue: FakeGenerationQueue, key: str = "k1") -> str:
    return queue.stored[key].status


def _errored(queue: FakeGenerationQueue) -> list[tuple[int, int]]:
    return [(p.day, p.slot) for p in _slots(queue) if p.status is SlotStatus.ERROR]


def _candidates(weeks: FakeWeekRepository) -> int:
    return sum(len(contents.candidates) for contents in weeks.get_week(_WEEK).values())


# E1 - a failure behind the claim makes every slot terminal (reproduction).


def test_a_write_failure_mid_run_leaves_no_slot_in_flight() -> None:
    queue = _submitted()

    _deliver(_week_body(), _deps(queue, weeks=_FlakyWeeks(saves_left=1)))

    assert _in_flight(queue) == []


def test_a_write_failure_mid_run_settles_the_run_status() -> None:
    queue = _submitted()

    _deliver(_week_body(), _deps(queue, weeks=_FlakyWeeks(saves_left=1)))

    assert _status(queue) == "partial"


def test_a_write_failure_on_the_first_slot_settles_the_run_as_failed() -> None:
    queue = _submitted()

    _deliver(_week_body(), _deps(queue, weeks=_FlakyWeeks(saves_left=0)))

    assert _status(queue) == "failed"


def test_the_candidates_written_before_the_failure_are_kept() -> None:
    weeks = _FlakyWeeks(saves_left=1)

    _deliver(_week_body(), _deps(_submitted(), weeks=weeks))

    assert [c for contents in weeks.get_week(_WEEK).values() for c in contents.candidates]


def test_a_failure_the_run_could_record_is_not_handed_back_for_redelivery() -> None:
    reported = _deliver(_week_body(), _deps(_submitted(), weeks=_FlakyWeeks(saves_left=1)))

    assert reported == []


# E2 - every interrupted slot carries a code and an es-ES message.


def test_each_interrupted_slot_carries_a_named_reason_and_a_spanish_message() -> None:
    queue = _submitted()

    _deliver(_week_body(), _deps(queue, weeks=_FlakyWeeks(saves_left=1)))

    errors = [p.error for p in _slots(queue) if p.status is SlotStatus.ERROR]
    assert len(errors) == _OPEN_SLOTS - 1
    assert all(e is not None and e.code in _REASONS for e in errors)
    assert all(e is not None and e.message in _ES_MESSAGES for e in errors)


# E3 - the user gets the per-slot retry FR-AI-12 promises.


def test_an_interrupted_slot_accepts_the_per_slot_retry() -> None:
    queue = _submitted()
    _deliver(_week_body(), _deps(queue, weeks=_FlakyWeeks(saves_left=1)))

    errored = [p for p in _slots(queue) if p.status is SlotStatus.ERROR]
    assert errored
    queue.retry_slot("k1", errored[0].day, errored[0].slot, author="u-2")

    assert queue.retries == [("k1", errored[0].day, errored[0].slot, "u-2")]


# E4 - a redelivery behind a dead attempt's claim settles the run (reproduction).


def test_a_redelivery_settles_a_run_its_dead_attempt_left_running() -> None:
    queue = _claimed(
        SlotProgress(1, 1, SlotStatus.DONE),
        SlotProgress(1, 2, SlotStatus.RUNNING),
        SlotProgress(2, 1, SlotStatus.PENDING),
    )

    reported = _deliver(_week_body(), _deps(queue), receives=2)

    assert _in_flight(queue) == []
    assert _status(queue) == "partial"
    assert reported == []


def test_a_redelivery_of_a_run_that_never_started_a_slot_settles_it_as_failed() -> None:
    queue = _claimed(SlotProgress(1, 1, SlotStatus.PENDING), SlotProgress(1, 2, SlotStatus.PENDING))

    _deliver(_week_body(), _deps(queue), receives=2)

    assert _status(queue) == "failed"


def test_a_redelivery_finishes_a_run_that_only_lost_its_final_status() -> None:
    queue = _claimed(SlotProgress(1, 1, SlotStatus.DONE), SlotProgress(1, 2, SlotStatus.DONE))

    _deliver(_week_body(), _deps(queue), receives=2)

    assert _status(queue) == "completed"


def test_a_redelivery_keeps_a_finished_slot_finished() -> None:
    queue = _claimed(SlotProgress(1, 1, SlotStatus.DONE), SlotProgress(1, 2, SlotStatus.RUNNING))

    _deliver(_week_body(), _deps(queue), receives=2)

    assert _slot_status(queue, 1, 1) is SlotStatus.DONE


# E5 - no redelivery pays for a slot again (FR-AI-08).


@pytest.mark.parametrize("left_as", [SlotStatus.PENDING, SlotStatus.RUNNING])
def test_a_redelivery_never_invokes_the_provider(left_as: SlotStatus) -> None:
    provider = FakeAiProvider()
    queue = _claimed(SlotProgress(1, 1, left_as))

    _deliver(_week_body(), _deps(queue, provider=provider), receives=2)

    assert provider.calls == 0


def test_replaying_a_failed_run_through_the_queue_pays_for_nothing_extra() -> None:
    provider = FakeAiProvider()
    weeks = _FlakyWeeks(saves_left=1)
    deps = _deps(_submitted(), weeks=weeks, provider=provider)

    _deliver(_week_body(), deps)
    paid = provider.calls
    for receives in range(2, _RECEIVE_LIMIT + 1):
        _deliver(_week_body(), deps, receives=receives)

    assert paid > 0
    assert provider.calls == paid


def test_a_redelivery_never_adds_a_candidate() -> None:
    weeks = FakeWeekRepository()
    queue = _claimed(SlotProgress(1, 1, SlotStatus.RUNNING))

    _deliver(_week_body(), _deps(queue, weeks=weeks), receives=2)

    assert weeks.versions == {}


def test_a_late_delivery_of_a_run_never_claimed_settles_it_without_paying() -> None:
    provider = FakeAiProvider()
    queue = _submitted()

    reported = _deliver(_week_body(), _deps(queue, provider=provider), receives=2)

    assert _status(queue) == "failed"
    assert provider.calls == 0
    assert reported == []


# E6 - a failure before any slot began is settled on the spot: every target becomes error.


def test_a_read_failure_right_after_the_claim_fails_the_run_on_the_spot() -> None:
    provider = FakeAiProvider()
    queue = _submitted()
    deps = _deps(queue, weeks=_FlakyWeeks(failed_reads=1), provider=provider)

    reported = _deliver(_week_body(), deps)

    assert _status(queue) == "failed"
    assert len(_errored(queue)) == _OPEN_SLOTS
    assert provider.calls == 0
    assert reported == []


def test_a_failed_slot_setup_fails_the_run_on_the_spot() -> None:
    provider = FakeAiProvider()
    queue = _submitted()
    queue.failures = {"begin_slots": 1}

    reported = _deliver(_week_body(), _deps(queue, provider=provider))

    assert _status(queue) == "failed"
    assert len(_errored(queue)) == _OPEN_SLOTS
    assert provider.calls == 0
    assert reported == []


def test_a_week_still_unreadable_while_settling_is_settled_from_the_rules() -> None:
    queue = _submitted()

    _deliver(_week_body(), _deps(queue, weeks=_FlakyWeeks(failed_reads=2)))

    assert _status(queue) == "failed"
    assert len(_errored(queue)) == _OPEN_SLOTS


def test_settling_an_unstarted_run_leaves_a_definitive_slot_out() -> None:
    weeks = _FlakyWeeks(failed_reads=1)
    meal = MealSnapshot(
        name="Existente", ingredients=(), tools=(), procedure=(), category=IngredientCategory.MEAT
    )
    chosen = SlotContents(
        candidates=(Candidate(id="c0", meal=meal, author="u-1"),), definitive_id="c0"
    )
    weeks.weeks[_WEEK] = {SlotRef(date(2026, 8, 17), MealSlot.LUNCH): chosen}
    queue = _submitted()

    _deliver(_week_body(), _deps(queue, weeks=weeks))

    assert len(_errored(queue)) == _OPEN_SLOTS - 1
    assert (1, 1) not in _errored(queue)


def test_a_run_a_dead_attempt_left_with_no_slots_is_failed_on_redelivery() -> None:
    provider = FakeAiProvider()
    queue = _claimed()

    reported = _deliver(_week_body(), _deps(queue, provider=provider), receives=2)

    assert _status(queue) == "failed"
    assert len(_errored(queue)) == _OPEN_SLOTS
    assert provider.calls == 0
    assert reported == []


def test_a_redelivered_run_with_no_open_slots_still_completes() -> None:
    queue = _claimed()
    every_day_off = {"disabledDays": [*range(1, 8)]}
    body = json.dumps({**json.loads(_week_body()), "effectiveRules": every_day_off})

    _play_queue(body, _deps(queue), first_receive=2)

    assert _status(queue) == "completed"


# E7 - a failure before the claim is handed back to SQS (reproduction of the report).


def test_a_throttled_claim_is_reported_for_redelivery() -> None:
    provider = FakeAiProvider()
    queue = _submitted()
    queue.failures = {"claim": 1}

    reported = _deliver(_week_body(), _deps(queue, provider=provider))

    assert reported == ["m-1"]
    assert _status(queue) == "pending"
    assert provider.calls == 0


def test_a_claim_throttled_once_is_failed_by_the_next_delivery_without_paying() -> None:
    provider = FakeAiProvider()
    queue = _submitted()
    queue.failures = {"claim": 1}

    outcome = _play_queue(_week_body(), _deps(queue, provider=provider))

    assert outcome == "deleted"
    assert _status(queue) == "failed"
    assert provider.calls == 0


def test_a_message_that_keeps_failing_reaches_the_dead_letter_queue() -> None:
    queue = _submitted()
    queue.outage = True

    assert _play_queue(_week_body(), _deps(queue)) == "dead-lettered"


@pytest.mark.parametrize(
    "bug", [ValueError("fake"), KeyError("fake"), AttributeError("fake"), TypeError("fake")]
)
def test_a_parser_shaped_error_behind_the_parse_is_not_taken_for_poison(bug: Exception) -> None:
    queue = _submitted()
    queue.failures = {"claim": 1}
    queue.error = bug

    assert _deliver(_week_body(), _deps(queue)) == ["m-1"]


# E8 - a failure the worker cannot record comes back until it can.


def test_a_failure_during_an_outage_is_reported_and_settled_on_redelivery() -> None:
    queue = _submitted()
    deps = _deps(queue, weeks=_FlakyWeeks(saves_left=1, takes_down=queue))

    assert _deliver(_week_body(), deps) == ["m-1"]
    queue.outage = False
    assert _deliver(_week_body(), deps, receives=2) == []

    assert _in_flight(queue) == []
    assert _status(queue) == "partial"


def test_a_lost_final_status_write_still_settles_the_run() -> None:
    queue = _submitted()
    queue.failures = {"record_status": 1}

    _deliver(_week_body(), _deps(queue))

    assert _status(queue) == "completed"


# E9 - single-recipe: a failure behind the claim is recorded as failed, never paid twice.


def test_a_lost_recipe_result_fails_the_run_instead_of_stranding_it() -> None:
    provider = FakeAiProvider()
    queue = _submitted(slots=None)
    queue.failures = {"record_result": 1}

    reported = _deliver(_recipe_body(), _deps(queue, provider=provider))

    assert _status(queue) == "failed"
    assert provider.calls == 1
    assert reported == []


def test_a_failed_recipe_run_carries_a_reason_and_a_spanish_message() -> None:
    queue = _claimed_recipe()

    _deliver(_recipe_body(), _deps(queue), receives=2)

    payload = queue.results["k1"]
    assert isinstance(payload, Mapping)
    error = payload["error"]
    assert isinstance(error, Mapping)
    assert error["code"] in _REASONS
    assert error["message"] in _ES_MESSAGES


def test_a_redelivered_recipe_behind_its_claim_fails_without_paying_again() -> None:
    provider = FakeAiProvider()
    queue = _claimed_recipe()

    reported = _deliver(_recipe_body(), _deps(queue, provider=provider), receives=2)

    assert _status(queue) == "failed"
    assert provider.calls == 0
    assert reported == []


def test_a_recipe_claim_throttled_once_is_failed_by_the_next_delivery() -> None:
    provider = FakeAiProvider()
    queue = _submitted(slots=None)
    queue.failures = {"claim": 1}

    outcome = _play_queue(_recipe_body(), _deps(queue, provider=provider))

    assert outcome == "deleted"
    assert _status(queue) == "failed"
    assert provider.calls == 0


# E10 - per-slot retry: a failure touches its own slot, then settles the run.


def test_a_redelivered_slot_retry_fails_its_own_slot_only() -> None:
    provider = FakeAiProvider()
    queue = _claimed(SlotProgress(7, 1, SlotStatus.RUNNING), SlotProgress(7, 2, SlotStatus.PENDING))

    reported = _deliver(_retry_body(7, 1), _deps(queue, provider=provider), receives=2)

    assert _slot_status(queue, 7, 1) is SlotStatus.ERROR
    assert _slot_status(queue, 7, 2) is SlotStatus.PENDING  # its own message is still queued
    assert _status(queue) == "running"
    assert provider.calls == 0
    assert reported == []


def test_a_redelivered_slot_retry_settles_a_run_with_nothing_else_in_flight() -> None:
    queue = _claimed(SlotProgress(7, 1, SlotStatus.RUNNING), SlotProgress(7, 2, SlotStatus.DONE))

    _deliver(_retry_body(7, 1), _deps(queue), receives=2)

    assert _status(queue) == "partial"


def test_a_slot_retry_that_cannot_write_its_candidate_settles_the_run() -> None:
    queue = _claimed(SlotProgress(7, 1, SlotStatus.PENDING), SlotProgress(7, 2, SlotStatus.DONE))

    reported = _deliver(_retry_body(7, 1), _deps(queue, weeks=_FlakyWeeks(saves_left=0)))

    assert _slot_status(queue, 7, 1) is SlotStatus.ERROR
    assert _status(queue) == "partial"
    assert reported == []


def test_a_slot_claim_throttled_once_is_failed_by_the_next_delivery() -> None:
    provider = FakeAiProvider()
    queue = _claimed(SlotProgress(7, 1, SlotStatus.PENDING), SlotProgress(7, 2, SlotStatus.DONE))
    queue.failures = {"claim_slot": 1}

    outcome = _play_queue(_retry_body(7, 1), _deps(queue, provider=provider))

    assert outcome == "deleted"
    assert _slot_status(queue, 7, 1) is SlotStatus.ERROR
    assert _status(queue) == "partial"
    assert provider.calls == 0


# E11 - a duplicate of a live attempt, a finished run and a discarded run stay untouched.


def test_a_first_receive_behind_the_claim_is_a_duplicate_of_a_live_attempt() -> None:
    provider = FakeAiProvider()
    live = (SlotProgress(1, 1, SlotStatus.RUNNING), SlotProgress(1, 2, SlotStatus.PENDING))
    queue = _claimed(*live)

    reported = _deliver(_week_body(), _deps(queue, provider=provider), receives=1)

    assert _slots(queue) == live
    assert _status(queue) == "running"
    assert provider.calls == 0
    assert reported == []


def test_a_record_without_a_receive_count_is_taken_for_a_first_receive() -> None:
    queue = _claimed(SlotProgress(1, 1, SlotStatus.RUNNING))

    handle({"Records": [{"messageId": "m-1", "body": _week_body()}]}, _deps(queue))

    assert _status(queue) == "running"
    assert _slot_status(queue, 1, 1) is SlotStatus.RUNNING


def test_a_first_receive_of_a_recipe_behind_the_claim_is_a_duplicate_too() -> None:
    queue = _claimed_recipe()

    _deliver(_recipe_body(), _deps(queue), receives=1)

    assert _status(queue) == "running"


@pytest.mark.parametrize("terminal", ["completed", "partial", "failed"])
def test_a_redelivery_of_a_finished_run_changes_nothing(terminal: str) -> None:
    provider = FakeAiProvider()
    slots = (SlotProgress(1, 1, SlotStatus.DONE),)
    queue = _FlakyQueue()
    queue.stored["k1"] = StoredGeneration(idempotency_key="k1", status=terminal, slots=slots)

    reported = _deliver(_week_body(), _deps(queue, provider=provider), receives=2)

    assert _status(queue) == terminal
    assert _slots(queue) == slots
    assert provider.calls == 0
    assert reported == []


@pytest.mark.parametrize("body", [_week_body(), _recipe_body(), _retry_body(7, 1)])
def test_a_redelivery_of_a_discarded_run_is_acknowledged(body: str) -> None:
    queue = _FlakyQueue()

    assert _deliver(body, _deps(queue), receives=2) == []
    assert queue.stored == {}


# E12 - a poison message is dropped on sight: no retry, no claim, no spend.

_MISSING_FIELD = json.dumps({"idPeticionIA": "k1", "weekId": "2026-W34"})
_BAD_WEEK = json.dumps({**json.loads(_week_body()), "weekId": "not-a-week"})
_BAD_SLOT = json.dumps({**json.loads(_retry_body(9, 1))})
_UNKNOWN_TYPE = json.dumps({**json.loads(_week_body()), "type": "quux"})
_POISON = {
    "not json": "{not json",
    "json but not an object": "[1, 2]",
    "missing field": _MISSING_FIELD,
    "unparseable week": _BAD_WEEK,
    "slot out of range": _BAD_SLOT,
    "unknown type": _UNKNOWN_TYPE,
}


@pytest.fixture(params=sorted(_POISON))
def poison(request: pytest.FixtureRequest) -> str:
    return _POISON[request.param]


def test_a_poison_message_is_never_handed_back(poison: str) -> None:
    assert _play_queue(poison, _deps(_submitted())) == "deleted"


def test_a_poison_message_claims_nothing_and_pays_nothing(poison: str) -> None:
    provider = FakeAiProvider()
    queue = _submitted()

    _deliver(poison, _deps(queue, provider=provider))

    assert queue.claims == []
    assert provider.calls == 0


def test_a_poison_message_is_logged_as_an_error(
    poison: str, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.ERROR, logger="planner_ai"):
        _deliver(poison, _deps(_submitted()))

    assert [r for r in caplog.records if r.levelno >= logging.ERROR]


def test_a_failure_behind_the_claim_is_logged_as_an_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.ERROR, logger="planner_ai"):
        _deliver(_week_body(), _deps(_submitted(), weeks=_FlakyWeeks(saves_left=1)))

    assert [r for r in caplog.records if r.levelno >= logging.ERROR]


# E14 - one bad record never stops the next (FR-AI-09, single_recipe_generation R27).


def test_only_the_failing_record_of_a_batch_is_reported() -> None:
    queue = _submitted("k1")
    queue.stored["k2"] = StoredGeneration(idempotency_key="k2", status="pending", slots=())
    queue.failing_claims = {"k1"}
    event = {
        "Records": [
            _record(_week_body("k1"), message_id="m-1"),
            _record(_week_body("k2"), message_id="m-2"),
        ]
    }

    result = handle(event, _deps(queue))

    assert _reported(result) == ["m-1"]
    assert _status(queue, "k2") == "completed"


def test_a_poison_record_does_not_stop_the_next() -> None:
    queue = _submitted("k2")
    event = {
        "Records": [
            _record("{not json", message_id="m-1"),
            _record(_week_body("k2"), message_id="m-2"),
        ]
    }

    result = handle(event, _deps(queue))

    assert _reported(result) == []
    assert _status(queue, "k2") == "completed"


# E15 - the Lambda entry point hands the response to AWS, and a wiring failure stays loud.


def _plenty(calls: int) -> int:
    return 900_000


@dataclass
class _FakeContext:
    """The Lambda context; the time left is a function of the provider calls made so far."""

    provider: FakeAiProvider | None = None
    left_ms: Callable[[int], int] = _plenty
    function_name: str = "planner-dev-ai"
    aws_request_id: str = "req-1"

    def get_remaining_time_in_millis(self) -> int:
        return self.left_ms(self.provider.calls if self.provider is not None else 0)


def _patch_builder(monkeypatch: pytest.MonkeyPatch, build: Any) -> None:
    monkeypatch.setattr(wiring, "build_dependencies", build)
    monkeypatch.setattr(handler, "build_dependencies", build)


def test_the_lambda_entry_point_returns_the_partial_batch_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queue = _submitted()
    queue.failures = {"claim": 1}
    _patch_builder(monkeypatch, lambda: _deps(queue))

    response = handler.lambda_handler({"Records": [_record(_week_body())]}, _FakeContext())

    assert response == {"batchItemFailures": [{"itemIdentifier": "m-1"}]}


def test_a_wiring_failure_fails_the_invocation_so_sqs_redelivers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuse() -> Dependencies:
        raise RuntimeError("fake wiring failure")

    _patch_builder(monkeypatch, refuse)

    with pytest.raises(RuntimeError):
        handler.lambda_handler({"Records": [_record(_week_body())]}, _FakeContext())


# E16 - the run stops starting slots when one more cannot finish, and keeps what is done.

_SHORT_MS = 100_000  # less than one worst-case slot


def _bedrock_worst_case_ms() -> int:
    """One provider call at the client's own limits: every attempt times out,
    plus the 20 s backoff cap (botocore standard retry mode)."""
    config = BedrockAiProvider()._bedrock().meta.config
    attempts = (config.retries or {}).get("total_max_attempts", 5)  # legacy default
    return int((attempts * (config.connect_timeout + config.read_timeout) + 20) * 1000)


def _against_the_clock(
    monkeypatch: pytest.MonkeyPatch,
    left_ms: Callable[[int], int],
    *,
    queue: FakeGenerationQueue | None = None,
    body: str | None = None,
    weeks: FakeWeekRepository | None = None,
    recipes: FakeRecipeRepository | None = None,
) -> tuple[FakeGenerationQueue, FakeAiProvider, list[str]]:
    queue = queue if queue is not None else _submitted()
    provider = FakeAiProvider()
    deps = _deps(queue, weeks=weeks, provider=provider, recipes=recipes)
    _patch_builder(monkeypatch, lambda: deps)
    event = {"Records": [_record(body if body is not None else _week_body())]}
    response = handler.lambda_handler(event, _FakeContext(provider, left_ms))
    return queue, provider, _reported(response)


def test_a_run_short_of_time_stops_after_the_slots_it_could_finish(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queue, provider, reported = _against_the_clock(
        monkeypatch, lambda calls: 900_000 if calls < 3 else _SHORT_MS
    )

    assert provider.calls == 3
    assert len(_errored(queue)) == _OPEN_SLOTS - 3
    assert _status(queue) == "partial"
    assert reported == []


def test_the_last_slot_is_cut_when_only_it_does_not_fit(monkeypatch: pytest.MonkeyPatch) -> None:
    queue, provider, _ = _against_the_clock(
        monkeypatch, lambda calls: 900_000 if calls < _OPEN_SLOTS - 1 else _SHORT_MS
    )

    assert provider.calls == _OPEN_SLOTS - 1
    assert len(_errored(queue)) == 1


def test_slots_finished_before_the_deadline_keep_their_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    weeks = FakeWeekRepository()

    queue, _, _ = _against_the_clock(
        monkeypatch, lambda calls: 900_000 if calls < 3 else _SHORT_MS, weeks=weeks
    )

    done = [p for p in _slots(queue) if p.status is SlotStatus.DONE]
    assert len(done) == 3
    assert _candidates(weeks) == 3


def test_no_slot_starts_when_only_a_worst_case_provider_call_is_left(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    left = _bedrock_worst_case_ms()

    queue, provider, _ = _against_the_clock(monkeypatch, lambda calls: left)

    assert provider.calls == 0
    assert _status(queue) == "failed"


def test_a_run_with_ten_minutes_left_finishes_every_slot(monkeypatch: pytest.MonkeyPatch) -> None:
    queue, provider, _ = _against_the_clock(monkeypatch, lambda calls: 600_000)

    assert provider.calls == _OPEN_SLOTS
    assert _status(queue) == "completed"


def test_a_library_run_short_of_time_writes_no_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    recipes = FakeRecipeRepository()
    for n in range(3):
        recipe = Recipe(
            name=f"Receta {n}",
            ingredients=(),
            tools=("olla",),
            procedure=("Cocer.",),
            category=IngredientCategory.LEGUME,
        )
        recipes.entries[f"r{n}"] = LibraryRecipe(id=f"r{n}", recipe=recipe, author="chef")
    weeks = FakeWeekRepository()
    body = json.dumps({**json.loads(_week_body()), "mode": "library_only"})

    queue, _, _ = _against_the_clock(
        monkeypatch, lambda calls: _SHORT_MS, body=body, weeks=weeks, recipes=recipes
    )

    assert _candidates(weeks) == 0
    assert len(_errored(queue)) == _OPEN_SLOTS


def test_a_slot_retry_short_of_time_fails_its_slot_without_paying(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queue = _claimed(SlotProgress(7, 1, SlotStatus.PENDING), SlotProgress(7, 2, SlotStatus.DONE))

    _, provider, reported = _against_the_clock(
        monkeypatch, lambda calls: _SHORT_MS, queue=queue, body=_retry_body(7, 1)
    )

    assert provider.calls == 0
    assert _slot_status(queue, 7, 1) is SlotStatus.ERROR
    assert _status(queue) == "partial"
    assert reported == []
