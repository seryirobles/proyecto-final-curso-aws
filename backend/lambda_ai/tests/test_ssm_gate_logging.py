"""A kill-switch read that fails closed says so in the log
(issues/ai-generation-422-unavailable E7)."""

from __future__ import annotations

import logging
from typing import Any

import pytest
from botocore.exceptions import ClientError, NoCredentialsError

from planner_ai.adapters.ssm import SsmGenerationGate

_SECRET = "bedrock-api-key-must-not-be-logged"
_DENIED = ClientError(
    {"Error": {"Code": "UnrecognizedClientException", "Message": "invalid token"}},
    "GetParameter",
)


class _FailingSsm:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def get_parameter(self, **kwargs: Any) -> Any:
        raise self._error


@pytest.mark.parametrize("error", [NoCredentialsError(), _DENIED], ids=["no-creds", "denied"])
def test_a_failed_switch_read_fails_closed_with_a_warning(
    error: Exception, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E7 - NFR-AI-01 stays fail-closed; the cause becomes visible."""
    monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", _SECRET)
    gate = SsmGenerationGate(env="dev", client=_FailingSsm(error), ttl_seconds=0.0)

    with caplog.at_level(logging.WARNING):
        enabled = gate.is_generation_enabled()

    assert enabled is False
    assert any(r.levelno >= logging.WARNING for r in caplog.records)
    assert "/planner/dev/ai-generation-enabled" in caplog.text
    assert _SECRET not in caplog.text
