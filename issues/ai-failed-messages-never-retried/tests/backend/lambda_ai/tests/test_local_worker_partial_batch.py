"""The local poller mirrors the SQS trigger: a reported message stays on the queue
and comes back with its receive count (issues/ai-failed-messages-never-retried E13)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws
from planner_core.domain.generation import SlotProgress, SlotStatus
from planner_core.ports.generation_queue import StoredGeneration
from support.fakes import (
    FakeAiProvider,
    FakeClock,
    FakeGenerationGate,
    FakeGenerationQueue,
    FakeRecipeRepository,
    FakeWeekRepository,
)

from planner_ai import local_worker
from planner_ai.wiring import Dependencies


@dataclass
class _ThrottledQueue(FakeGenerationQueue):
    throttled_claims: set[str] = field(default_factory=set)

    def claim(self, idempotency_key: str) -> bool:
        if idempotency_key in self.throttled_claims:
            error = {"Code": "ProvisionedThroughputExceededException", "Message": "fake"}
            raise ClientError({"Error": error}, "UpdateItem")
        return super().claim(idempotency_key)


def _deps(queue: FakeGenerationQueue) -> Dependencies:
    return Dependencies(
        provider=FakeAiProvider(),
        weeks=FakeWeekRepository(),
        recipes=FakeRecipeRepository(),
        records=queue,
        gate=FakeGenerationGate(),
        clock=FakeClock.at("2026-08-17T10:00:00+00:00"),
    )


def _week_body(key: str) -> str:
    return json.dumps(
        {
            "idPeticionIA": key,
            "weekId": "2026-W34",
            "mode": "mix",
            "promptVersionId": "v1",
            "authorUserId": "u-1",
            "effectiveRules": {},
        }
    )


def _pending(*keys: str) -> _ThrottledQueue:
    queue = _ThrottledQueue()
    for key in keys:
        queue.stored[key] = StoredGeneration(idempotency_key=key, status="pending", slots=())
    return queue


# The client is untyped: boto3 ships no stubs (docs/conventions.md).
@pytest.fixture
def sqs(monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    """moto stands in for ElasticMQ; a zero timeout makes a kept message visible at once."""
    monkeypatch.setattr(local_worker, "_WAIT_TIME_SECONDS", 0)
    with mock_aws():
        yield boto3.client("sqs", region_name="us-east-1")


def _queue_url(sqs: Any, *bodies: str) -> str:
    attributes = {"VisibilityTimeout": "0"}
    url = str(sqs.create_queue(QueueName="generation", Attributes=attributes)["QueueUrl"])
    for body in bodies:
        sqs.send_message(QueueUrl=url, MessageBody=body)
    return url


def _bodies_left(sqs: Any, url: str) -> list[str]:
    received = sqs.receive_message(QueueUrl=url, MaxNumberOfMessages=10)
    return sorted(str(message["Body"]) for message in received.get("Messages", []))


def test_a_reported_message_stays_on_the_queue(sqs: Any) -> None:
    url = _queue_url(sqs, _week_body("k1"))
    queue = _pending("k1")
    queue.throttled_claims = {"k1"}

    local_worker._poll_once(sqs, url, _deps(queue))

    assert _bodies_left(sqs, url) == [_week_body("k1")]


def test_only_the_reported_message_of_a_batch_stays_on_the_queue(sqs: Any) -> None:
    url = _queue_url(sqs, _week_body("k1"), _week_body("k2"))
    queue = _pending("k1", "k2")
    queue.throttled_claims = {"k1"}

    local_worker._poll_once(sqs, url, _deps(queue))

    assert _bodies_left(sqs, url) == [_week_body("k1")]
    assert queue.stored["k2"].status == "completed"


def test_a_redelivered_message_reaches_the_handler_with_its_receive_count(sqs: Any) -> None:
    url = _queue_url(sqs, _week_body("k1"))
    queue = _pending("k1")
    queue.throttled_claims = {"k1"}
    local_worker._poll_once(sqs, url, _deps(queue))

    queue.throttled_claims = set()
    queue.stored["k1"] = StoredGeneration(
        idempotency_key="k1", status="running", slots=(SlotProgress(1, 1, SlotStatus.RUNNING),)
    )
    local_worker._poll_once(sqs, url, _deps(queue))

    assert queue.stored["k1"].status == "failed"
    assert _bodies_left(sqs, url) == []


def test_a_processed_message_is_deleted(sqs: Any) -> None:
    url = _queue_url(sqs, _week_body("k1"))
    queue = _pending("k1")

    local_worker._poll_once(sqs, url, _deps(queue))

    assert queue.stored["k1"].status == "completed"
    assert _bodies_left(sqs, url) == []


def test_a_poison_message_is_deleted_rather_than_looping(sqs: Any) -> None:
    url = _queue_url(sqs, "{not json")

    local_worker._poll_once(sqs, url, _deps(_pending("k1")))

    assert _bodies_left(sqs, url) == []
