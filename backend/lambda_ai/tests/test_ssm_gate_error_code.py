"""The fail-closed warning also carries the ClientError code, never a secret."""

from __future__ import annotations

import logging
from typing import Any

import pytest
from botocore.exceptions import ClientError

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


def test_the_client_error_code_is_logged(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", _SECRET)
    gate = SsmGenerationGate(env="dev", client=_FailingSsm(_DENIED), ttl_seconds=0.0)

    with caplog.at_level(logging.WARNING):
        gate.is_generation_enabled()

    assert "UnrecognizedClientException" in caplog.text
    assert _SECRET not in caplog.text
