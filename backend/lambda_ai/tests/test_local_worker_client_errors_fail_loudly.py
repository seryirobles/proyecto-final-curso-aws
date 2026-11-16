"""An SQS ClientError is a misconfiguration, not a transient fault: it must stop
the local worker."""

from __future__ import annotations

import time
from typing import Any

import pytest
from botocore.exceptions import ClientError

from planner_ai import local_worker

_QUEUE_URL = "http://localhost:9324/000000000000/wrong-queue"


def _no_such_queue() -> ClientError:
    error: dict[str, Any] = {
        "Error": {
            "Code": "AWS.SimpleQueueService.NonExistentQueue",
            "Message": "The specified queue does not exist.",
        }
    }
    return ClientError(error, "ReceiveMessage")


class _ScriptedSqs:
    """Raises the ClientError, then a KeyboardInterrupt if polling went on."""

    def __init__(self) -> None:
        self._receives: list[BaseException] = [_no_such_queue(), KeyboardInterrupt()]
        self.receive_calls = 0

    def receive_message(self, **kwargs: Any) -> dict[str, Any]:
        self.receive_calls += 1
        raise self._receives.pop(0)

    def delete_message(self, **kwargs: Any) -> None:
        raise AssertionError("nothing was received, so nothing is deleted")


def test_a_receive_client_error_stops_the_worker(monkeypatch: pytest.MonkeyPatch) -> None:
    """Guard: only transport errors are logged and retried, never a ClientError."""
    for name, value in {
        "DYNAMODB_ENDPOINT_URL": "http://localhost:8000",
        "SQS_ENDPOINT_URL": "http://localhost:9324",
        "GENERATION_QUEUE_URL": _QUEUE_URL,
        "AWS_BEARER_TOKEN_BEDROCK": "test-bedrock-api-key",
    }.items():
        monkeypatch.setenv(name, value)
    sqs = _ScriptedSqs()
    monkeypatch.setattr(local_worker, "create_data_table", lambda: None)
    monkeypatch.setattr(local_worker, "build_local_dependencies", lambda: object())
    monkeypatch.setattr(local_worker, "_sqs", lambda: sqs)
    # Any back-off the fix adds must not slow the suite.
    monkeypatch.setattr(time, "sleep", lambda seconds: None)

    with pytest.raises(ClientError) as raised:
        local_worker.main()

    assert raised.value.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue"
    assert sqs.receive_calls == 1
