"""The ai worker handler: one use-case run per SQS record, per-record isolation
(R1, R4)."""

from __future__ import annotations

import json

from support.fakes import (
    FakeAiProvider,
    FakeClock,
    FakeGenerationGate,
    FakeGenerationQueue,
    FakeWeekRepository,
)

from planner_ai.handler import handle
from planner_ai.wiring import Dependencies


def _deps(queue: FakeGenerationQueue, weeks: FakeWeekRepository) -> Dependencies:
    return Dependencies(
        provider=FakeAiProvider(),
        weeks=weeks,
        records=queue,
        gate=FakeGenerationGate(),
        clock=FakeClock.at("2026-08-17T10:00:00+00:00"),
    )


def _body(key: str, week_id: str) -> str:
    return json.dumps(
        {
            "idPeticionIA": key,
            "weekId": week_id,
            "mode": "mix",
            "promptVersionId": "v1",
            "authorUserId": "u-1",
            "effectiveRules": {},
        }
    )


def test_a_two_record_batch_runs_both_and_isolates_a_failure() -> None:
    from planner_core.ports.generation_queue import StoredGeneration

    queue = FakeGenerationQueue()
    queue.stored["k1"] = StoredGeneration(idempotency_key="k1", status="pending")
    queue.stored["k2"] = StoredGeneration(idempotency_key="k2", status="pending")
    weeks = FakeWeekRepository()
    event = {
        "Records": [
            {"body": _body("k1", "not-a-week")},  # malformed — parse raises before any claim
            {"body": _body("k2", "2026-W34")},
        ]
    }

    handle(event, _deps(queue, weeks))

    assert queue.claims == ["k2"]  # k1 never reached claim; k2 processed (R4)
    assert queue.stored["k2"].status == "completed"
    assert queue.stored["k1"].status == "pending"  # untouched


def test_each_record_is_one_use_case_run() -> None:
    from planner_core.ports.generation_queue import StoredGeneration

    queue = FakeGenerationQueue()
    queue.stored["k1"] = StoredGeneration(idempotency_key="k1", status="pending")
    queue.stored["k2"] = StoredGeneration(idempotency_key="k2", status="pending")
    weeks = FakeWeekRepository()
    event = {"Records": [{"body": _body("k1", "2026-W34")}, {"body": _body("k2", "2026-W35")}]}

    handle(event, _deps(queue, weeks))

    assert set(queue.claims) == {"k1", "k2"}
    assert queue.results.keys() == {"k1", "k2"}  # R1 — one record, one recorded result
