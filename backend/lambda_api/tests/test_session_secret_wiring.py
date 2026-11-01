"""wiring.build_dependencies sources the HMAC session key from Secrets Manager
(SESSION_SECRET_ARN) or, failing that, SESSION_SECRET_KEY."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import boto3
import pytest
from planner_core.ports.tokens import HmacTokenSigner

from planner_api.adapters import secrets
from planner_api.wiring import build_dependencies

ARN = "arn:aws:secretsmanager:eu-west-1:123456789012:secret:session-AbCdEf"


class _Config:
    def __init__(self, **values: str) -> None:
        self._values = values

    def get(self, key: str) -> str | None:
        return self._values.get(key)


class _FakeSecretsClient:
    def __init__(self, response: dict[str, Any] | Exception) -> None:
        self.response = response
        self.calls: list[str] = []

    def get_secret_value(self, SecretId: str) -> dict[str, Any]:
        self.calls.append(SecretId)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


@pytest.fixture(autouse=True)
def _isolate(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("GENERATION_QUEUE_URL", "http://queue.invalid")
    secrets.fetch_session_secret.cache_clear()
    yield
    secrets.fetch_session_secret.cache_clear()


def _install(
    monkeypatch: pytest.MonkeyPatch, response: dict[str, Any] | Exception
) -> _FakeSecretsClient:
    client = _FakeSecretsClient(response)
    monkeypatch.setattr(boto3, "client", lambda *a, **k: client)
    return client


def _signed_with(key: str, deps: Any) -> bool:
    when = datetime(2026, 1, 1, tzinfo=UTC)
    return bool(deps.signer.issue("u", when) == HmacTokenSigner(key.encode()).issue("u", when))


def test_arn_set_fetches_the_secret_and_uses_it(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _install(monkeypatch, {"SecretString": "from-secrets-manager"})
    deps = build_dependencies(_Config(SESSION_SECRET_ARN=ARN))
    assert client.calls == [ARN]
    assert _signed_with("from-secrets-manager", deps)


def test_arn_unset_uses_the_env_key(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _install(monkeypatch, {"SecretString": "unused"})
    deps = build_dependencies(_Config(SESSION_SECRET_KEY="env-key"))
    assert client.calls == []
    assert _signed_with("env-key", deps)


def test_both_set_arn_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, {"SecretString": "from-secrets-manager"})
    deps = build_dependencies(_Config(SESSION_SECRET_ARN=ARN, SESSION_SECRET_KEY="env-key"))
    assert _signed_with("from-secrets-manager", deps)


def test_secret_is_fetched_once_across_builds(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _install(monkeypatch, {"SecretString": "k"})
    build_dependencies(_Config(SESSION_SECRET_ARN=ARN))
    build_dependencies(_Config(SESSION_SECRET_ARN=ARN))
    assert client.calls == [ARN]


def test_fetch_failure_is_a_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, RuntimeError("AccessDenied"))
    with pytest.raises(RuntimeError, match="Could not read the session secret"):
        build_dependencies(_Config(SESSION_SECRET_ARN=ARN, SESSION_SECRET_KEY="env-key"))


@pytest.mark.parametrize("response", [{"SecretString": ""}, {}])
def test_empty_or_missing_secret_string_is_rejected(
    monkeypatch: pytest.MonkeyPatch, response: dict[str, Any]
) -> None:
    _install(monkeypatch, response)
    with pytest.raises(RuntimeError, match="is empty"):
        build_dependencies(_Config(SESSION_SECRET_ARN=ARN))


def test_neither_set_keeps_the_existing_failure() -> None:
    with pytest.raises(RuntimeError, match="SESSION_SECRET_KEY is not configured"):
        build_dependencies(_Config())
