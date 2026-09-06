"""Contract suite for GenerationQueue: the in-memory fake and the moto-backed
SQS + PETICIONIA adapter agree on the idempotency-record surface (FR-AI-08)."""

from __future__ import annotations

import inspect
from collections.abc import Callable

import pytest
from planner_core.domain.calendar import IsoWeek
from planner_core.domain.generation import GenerationMode, GenerationRequest
from planner_core.ports.generation_queue import GenerationQueue, StoredGeneration
from support.fakes import FakeGenerationQueue

from tests.contract.dynamo_contract import sqs_generation_queue

IMPLEMENTATIONS: list[Callable[[], GenerationQueue]] = [FakeGenerationQueue, sqs_generation_queue]

REQUEST = GenerationRequest(week=IsoWeek(2026, 34), mode=GenerationMode.MIX)


def _force_done(queue: GenerationQueue, idempotency_key: str, result: str) -> None:
    """Advance the stored record as the ai worker would (feature 17), so a
    resubmit can be checked for clobbering (docs/data_model.md section 4.6)."""
    if isinstance(queue, FakeGenerationQueue):
        queue.stored[idempotency_key] = StoredGeneration(idempotency_key, "done", result)
    else:
        from planner_api.adapters.dynamo import _table

        _table.table().put_item(
            Item={
                "PK": f"PETICIONIA#{idempotency_key}",
                "SK": "METADATA",
                "estado": "done",
                "resultado": result,
            }
        )


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_stored_generation_is_none_for_an_unknown_id(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    assert queue_factory().stored_generation("unknown") is None


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_submit_creates_a_readable_record(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    queue = queue_factory()

    queue.submit("hash-1", REQUEST)

    stored = queue.stored_generation("hash-1")
    assert stored is not None
    assert stored.idempotency_key == "hash-1"
    assert stored.status == "pending"


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_resubmit_never_clobbers_a_stored_result(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    """FR-AI-08 / docs/data_model.md section 4.6 — losing the payload means
    paying for a result that then exists nowhere; submit is create-if-absent."""
    queue = queue_factory()
    queue.submit("hash-1", REQUEST)
    _force_done(queue, "hash-1", '{"ok": true}')

    queue.submit("hash-1", REQUEST)

    assert queue.stored_generation("hash-1") == StoredGeneration("hash-1", "done", '{"ok": true}')


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_discard_removes_a_stored_record(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    """R31/R32 (AP27) — submit then discard leaves no stored record."""
    queue = queue_factory()
    queue.submit("hash-1", REQUEST)

    queue.discard("hash-1")

    assert queue.stored_generation("hash-1") is None


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_discard_of_an_unknown_id_does_not_raise(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    """R33 — an unconditional DeleteItem; an absent key succeeds silently."""
    queue_factory().discard("never-stored")


def test_the_sqs_discard_passes_no_condition_expression() -> None:
    """R32/R33 — the adapter's discard is an unconditional DeleteItem, so an
    absent key succeeds silently."""
    from planner_api.adapters.sqs import SqsGenerationQueue

    source = inspect.getsource(SqsGenerationQueue.discard)
    code = "".join(line.split("#", 1)[0] for line in source.splitlines())
    assert "ConditionExpression" not in code
