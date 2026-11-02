"""build_authorizer_dependencies signs with the configured session secret
(env key, or the Secrets Manager secret for SESSION_SECRET_ARN, which wins)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import boto3
import pytest
from planner_core.ports.tokens import HmacTokenSigner, InvalidToken

from planner_api.adapters import secrets
from planner_api.wiring import build_authorizer_dependencies

ARN = "arn:aws:secretsmanager:eu-west-1:123456789012:secret:session-AbCdEf"
WHEN = datetime(2026, 1, 1, tzinfo=UTC)


class _Config:
    def __init__(self, **values: str) -> None:
        self._values = values

    def get(self, key: str) -> str | None:
        return self._values.get(key)


class _FakeSecretsClient:
    def get_secret_value(self, SecretId: str) -> dict[str, Any]:
        return {"SecretString": "from-secrets-manager"}


@pytest.fixture(autouse=True)
def _isolate() -> Iterator[None]:
    secrets.fetch_session_secret.cache_clear()
    yield
    secrets.fetch_session_secret.cache_clear()


def _accepts(signer: Any, key: str) -> bool:
    token = HmacTokenSigner(key.encode()).issue("u", WHEN)
    try:
        signer.verify(token)
    except InvalidToken:
        return False
    return True


def test_env_key_signer_accepts_its_key_and_rejects_another() -> None:
    deps = build_authorizer_dependencies(_Config(SESSION_SECRET_KEY="env-key"))
    assert _accepts(deps.signer, "env-key")
    assert not _accepts(deps.signer, "other-key")


def test_arn_secret_wins_over_the_env_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(boto3, "client", lambda *a, **k: _FakeSecretsClient())
    deps = build_authorizer_dependencies(
        _Config(SESSION_SECRET_ARN=ARN, SESSION_SECRET_KEY="env-key")
    )
    assert _accepts(deps.signer, "from-secrets-manager")
    assert not _accepts(deps.signer, "env-key")


def test_no_secret_configured_is_a_clear_error() -> None:
    with pytest.raises(RuntimeError, match="SESSION_SECRET_KEY is not configured"):
        build_authorizer_dependencies(_Config())
