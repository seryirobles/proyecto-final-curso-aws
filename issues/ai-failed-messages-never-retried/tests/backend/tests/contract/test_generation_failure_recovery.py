"""The failure path end to end on moto: the api adapter's real message bodies, the
worker's real record and week adapters, and the api's per-slot retry afterwards
(issues/ai-failed-messages-never-retried/plan.md E1, E3, E4, E6, E9, E11)."""

from __future__ import annotations

import json
from typing import Any

from planner_ai.adapters.dynamo.generations import DynamoGenerationRecords
from planner_ai.adapters.dynamo.weeks import DynamoWeekRepository
from planner_ai.handler import handle
from planner_ai.wiring import Dependencies
from planner_api.adapters.sqs import SqsGenerationQueue
from planner_core.domain.calendar import IsoWeek, SlotRef
from planner_core.domain.candidate import SlotContents
from planner_core.domain.generation import (
    GenerationMode,
    GenerationRequest,
    SingleRecipeRequest,
    SlotStatus,
    SpecificationSource,
)
from planner_core.domain.rules import RuleSet
from planner_core.ports.weeks import WeekRepository
from support.fakes import FakeAiProvider, FakeClock, FakeGenerationGate, FakeRecipeRepository

from tests.contract.dynamo_contract import received_generation_messages

_WEEK = IsoWeek(2026, 34)
_OPEN_SLOTS = 14


class _FailingWeeks(DynamoWeekRepository):
    """The worker's real adapter, failing every write after `saves_left` saves."""

    def __init__(self, saves_left: int) -> None:
        self._saves_left = saves_left

    def save_slot(self, week: IsoWeek, slot: SlotRef, contents: SlotContents) -> int:
        if self._saves_left == 0:
            raise RuntimeError("fake rejected transaction")
        self._saves_left -= 1
        return super().save_slot(week, slot, contents)


def _deps(weeks: WeekRepository, provider: FakeAiProvider) -> Dependencies:
    return Dependencies(
        provider=provider,
        weeks=weeks,
        recipes=FakeRecipeRepository(),
        records=DynamoGenerationRecords(),
        gate=FakeGenerationGate(),
        clock=FakeClock.at("2026-08-17T10:00:00+00:00"),
    )


def _submit_week(api: SqsGenerationQueue) -> str:
    request = GenerationRequest(week=_WEEK, mode=GenerationMode.MIX, rule_override=None)
    api.submit("k1", request, effective_rules=RuleSet(), prompt_version_id="v1", author="u-1")
    return received_generation_messages()[0]


def _submit_recipe(api: SqsGenerationQueue) -> str:
    source = SpecificationSource(ingredients=("lentejas",), tools=("olla",))
    request = SingleRecipeRequest(target=None, source=source)
    api.submit_recipe("k1", request, reference_recipe=None, prompt_version_id="v1", author="u-1")
    return received_generation_messages()[0]


# The value is untyped because it mirrors the JSON AWS reads back.
def _deliver(body: str, deps: Dependencies, receives: int = 1) -> list[str]:
    record = {
        "messageId": "m-1",
        "receiptHandle": "r-1",
        "body": body,
        "attributes": {"ApproximateReceiveCount": str(receives)},
    }
    result: Any = handle({"Records": [record]}, deps)
    return [] if result is None else [f["itemIdentifier"] for f in result["batchItemFailures"]]


def _in_flight(records: DynamoGenerationRecords) -> list[tuple[int, int]]:
    stored = records.stored_generation("k1")
    assert stored is not None
    return [
        (p.day, p.slot)
        for p in stored.slots or ()
        if p.status in {SlotStatus.PENDING, SlotStatus.RUNNING}
    ]


def _status(records: DynamoGenerationRecords) -> str:
    stored = records.stored_generation("k1")
    assert stored is not None
    return stored.status


def test_a_mid_run_failure_ends_terminal_and_the_api_can_retry_the_slot() -> None:
    api, records = SqsGenerationQueue(), DynamoGenerationRecords()
    body = _submit_week(api)

    reported = _deliver(body, _deps(_FailingWeeks(saves_left=1), FakeAiProvider()))

    assert reported == []
    assert _in_flight(records) == []
    assert _status(records) == "partial"
    stored = records.stored_generation("k1")
    assert stored is not None
    failed = next(p for p in stored.slots or () if p.status is SlotStatus.ERROR)
    assert failed.error is not None and failed.error.message

    api.retry_slot("k1", failed.day, failed.slot, author="u-2")
    retry_body = received_generation_messages()[0]
    _deliver(retry_body, _deps(DynamoWeekRepository(), FakeAiProvider()))

    retried = records.stored_generation("k1")
    assert retried is not None
    assert (
        next(p.status for p in retried.slots or () if (p.day, p.slot) == (failed.day, failed.slot))
        is SlotStatus.DONE
    )


def test_a_crash_before_any_slot_is_failed_by_the_redelivery_and_retryable() -> None:
    api, records = SqsGenerationQueue(), DynamoGenerationRecords()
    body = _submit_week(api)
    assert records.claim("k1") is True  # the crash hit before any slot was recorded
    provider = FakeAiProvider()

    reported = _deliver(body, _deps(DynamoWeekRepository(), provider), receives=2)

    assert reported == []
    assert provider.calls == 0
    assert _status(records) == "failed"
    stored = records.stored_generation("k1")
    assert stored is not None
    errors = [p for p in stored.slots or () if p.status is SlotStatus.ERROR]
    assert len(errors) == _OPEN_SLOTS
    assert all(p.error is not None and p.error.message for p in errors)
    api.retry_slot("k1", errors[0].day, errors[0].slot, author="u-2")
    assert received_generation_messages()


def test_a_redelivered_recipe_behind_its_claim_is_recorded_as_failed() -> None:
    api, records = SqsGenerationQueue(), DynamoGenerationRecords()
    body = _submit_recipe(api)
    assert records.claim("k1") is True
    provider = FakeAiProvider()

    reported = _deliver(body, _deps(DynamoWeekRepository(), provider), receives=2)

    assert reported == []
    assert provider.calls == 0
    stored = records.stored_generation("k1")
    assert stored is not None and stored.status == "failed"
    assert stored.result is not None
    assert json.loads(stored.result)["error"]["message"]


def test_a_first_receive_behind_the_claim_leaves_the_record_alone() -> None:
    api, records = SqsGenerationQueue(), DynamoGenerationRecords()
    body = _submit_week(api)
    assert records.claim("k1") is True
    provider = FakeAiProvider()

    reported = _deliver(body, _deps(DynamoWeekRepository(), provider), receives=1)

    assert reported == []
    assert provider.calls == 0
    assert _status(records) == "running"
