"""A transient SQS transport error must not kill the local worker's poll loop
(docs/local_development.md section 3)."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

import pytest
from botocore.exceptions import EndpointConnectionError, ReadTimeoutError

from planner_ai import local_worker

_QUEUE_URL = "http://localhost:9324/000000000000/generation-queue"
_MESSAGE = {"MessageId": "m-1", "ReceiptHandle": "r-1", "Body": "{}"}


def _read_timeout() -> Exception:
    return ReadTimeoutError(endpoint_url="http://localhost:9324/")


def _connection_refused() -> Exception:
    return EndpointConnectionError(endpoint_url="http://localhost:9324/")


class _ScriptedSqs:
    """Plays receive/delete outcomes in order; a KeyboardInterrupt ends main()."""

    def __init__(self, receives: list[Any], deletes: list[Any] | None = None) -> None:
        self._receives = receives
        self._deletes = deletes or []
        self.deleted: list[str] = []

    def receive_message(self, **kwargs: Any) -> Any:
        outcome = self._receives.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    def delete_message(self, **kwargs: Any) -> None:
        if self._deletes:
            raise self._deletes.pop(0)
        self.deleted.append(kwargs["ReceiptHandle"])


@pytest.fixture
def run_worker(monkeypatch: pytest.MonkeyPatch) -> Callable[[_ScriptedSqs], list[Any]]:
    for name, value in {
        "DYNAMODB_ENDPOINT_URL": "http://localhost:8000",
        "SQS_ENDPOINT_URL": "http://localhost:9324",
        "GENERATION_QUEUE_URL": _QUEUE_URL,
        "AWS_BEARER_TOKEN_BEDROCK": "test-bedrock-api-key",
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(local_worker, "create_data_table", lambda: None)
    monkeypatch.setattr(local_worker, "build_local_dependencies", lambda: object())
    # Any back-off the fix adds must not slow the suite.
    monkeypatch.setattr(time, "sleep", lambda seconds: None)
    handled: list[Any] = []
    monkeypatch.setattr(local_worker, "handle", lambda event, deps=None: handled.append(event))

    def run(sqs: _ScriptedSqs) -> list[Any]:
        monkeypatch.setattr(local_worker, "_sqs", lambda: sqs)
        local_worker.main()
        return handled

    return run


def _warnings(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.levelno >= logging.WARNING]


def test_a_receive_read_timeout_is_logged_and_polling_continues(
    run_worker: Callable[[_ScriptedSqs], list[Any]], caplog: pytest.LogCaptureFixture
) -> None:
    """Reproduction: the reported ReadTimeoutError ended the process."""
    sqs = _ScriptedSqs([_read_timeout(), {"Messages": [_MESSAGE]}, KeyboardInterrupt()])

    handled = run_worker(sqs)

    assert len(handled) == 1
    assert sqs.deleted == ["r-1"]
    assert len(_warnings(caplog)) >= 1


def test_an_unreachable_emulator_is_logged_and_polling_continues(
    run_worker: Callable[[_ScriptedSqs], list[Any]], caplog: pytest.LogCaptureFixture
) -> None:
    """Blast radius: an ElasticMQ container restart refuses connections briefly."""
    sqs = _ScriptedSqs([_connection_refused(), {"Messages": [_MESSAGE]}, KeyboardInterrupt()])

    handled = run_worker(sqs)

    assert len(handled) == 1
    assert len(_warnings(caplog)) >= 1


def test_a_delete_read_timeout_is_logged_and_polling_continues(
    run_worker: Callable[[_ScriptedSqs], list[Any]], caplog: pytest.LogCaptureFixture
) -> None:
    """Blast radius: delete_message shares the client; a redelivery is claim-guarded."""
    sqs = _ScriptedSqs(
        [{"Messages": [_MESSAGE]}, {"Messages": []}, KeyboardInterrupt()],
        deletes=[_read_timeout()],
    )

    handled = run_worker(sqs)

    assert len(handled) == 1
    assert len(_warnings(caplog)) >= 1


def test_ctrl_c_still_stops_the_worker_cleanly(
    run_worker: Callable[[_ScriptedSqs], list[Any]], caplog: pytest.LogCaptureFixture
) -> None:
    """Guard: catching transport errors must not swallow KeyboardInterrupt."""
    sqs = _ScriptedSqs([KeyboardInterrupt(), {"Messages": [_MESSAGE]}])

    handled = run_worker(sqs)

    assert handled == []
    assert _warnings(caplog) == []
