"""Contract suite for GenerationResultSink.claim / record_result: the in-memory
fake, the planner_api SQS+PETICIONIA adapter and the planner_ai DynamoDB
write-back all agree (FR-AI-09; specs/ai_lambda/design.md section 6)."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping

import pytest
from planner_core.ports.generation_queue import GenerationResultSink, StoredGeneration
from support.fakes import FakeGenerationQueue

from tests.contract.dynamo_contract import ai_generation_records, sqs_generation_queue

IMPLEMENTATIONS: list[Callable[[], GenerationResultSink]] = [
    FakeGenerationQueue,
    sqs_generation_queue,
    ai_generation_records,
]

_PER_SLOT: list[Mapping[str, object]] = [
    {"day": 1, "slot": 1, "status": "completed", "message": None}
]


def _seed_pending(sink: GenerationResultSink, key: str) -> None:
    if isinstance(sink, FakeGenerationQueue):
        sink.stored[key] = StoredGeneration(idempotency_key=key, status="pending")
        return
    from planner_api.adapters.dynamo import _table

    _table.table().put_item(
        Item={"PK": f"PETICIONIA#{key}", "SK": "METADATA", "estado": "pending", "resultado": None}
    )


def _read(sink: GenerationResultSink, key: str) -> tuple[str, object]:
    if isinstance(sink, FakeGenerationQueue):
        record = sink.stored[key]
        return record.status, json.loads(record.result or "null")
    from planner_api.adapters.dynamo import _table

    item = _table.get_item(f"PETICIONIA#{key}", "METADATA")
    assert item is not None
    return str(item["estado"]), json.loads(str(item["resultado"]))


@pytest.mark.parametrize("factory", IMPLEMENTATIONS)
def test_the_first_claim_transitions_pending_and_a_second_fails(
    factory: Callable[[], GenerationResultSink],
) -> None:
    sink = factory()
    _seed_pending(sink, "k")

    assert sink.claim("k") is True
    assert sink.claim("k") is False


@pytest.mark.parametrize("factory", IMPLEMENTATIONS)
def test_claim_of_an_absent_record_returns_false(
    factory: Callable[[], GenerationResultSink],
) -> None:
    assert factory().claim("never-seeded") is False


@pytest.mark.parametrize("factory", IMPLEMENTATIONS)
def test_record_result_writes_the_terminal_status_and_payload(
    factory: Callable[[], GenerationResultSink],
) -> None:
    sink = factory()
    _seed_pending(sink, "k")
    sink.claim("k")

    sink.record_result("k", "completed", _PER_SLOT)

    status, payload = _read(sink, "k")
    assert status == "completed"
    assert payload == _PER_SLOT
