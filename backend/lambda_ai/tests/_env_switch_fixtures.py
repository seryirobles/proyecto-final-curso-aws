"""Shared set-up for the AI_GENERATION_SWITCH tests
(issues/ai-kill-switch-unreadable-under-shared-role)."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from planner_ai.adapters import ssm

SWITCH = "AI_GENERATION_SWITCH"
LOCAL_OVERRIDE = "AI_GENERATION_ENABLED"
_PARAMETER = "/planner/dev/ai-generation-enabled"


# Named as botocore's generated class, so the log line matches CloudWatch's.
_ACCESS_DENIED: Any = type("AccessDeniedException", (ClientError,), {})  # botocore has no stubs


class DeniedSsm:
    """SSM as studentLambdaExecutionRole sees it; `reads` counts the attempts."""

    def __init__(self) -> None:
        self.reads = 0

    def get_parameter(self, **kwargs: Any) -> Any:  # boto3 ships no stubs
        self.reads += 1
        raise _ACCESS_DENIED(
            {"Error": {"Code": "AccessDeniedException", "Message": "not authorized"}},
            "GetParameter",
        )


def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLANNER_ENV", "dev")
    monkeypatch.delenv(SWITCH, raising=False)
    monkeypatch.delenv(LOCAL_OVERRIDE, raising=False)


@pytest.fixture
def shared_role(monkeypatch: pytest.MonkeyPatch) -> Iterator[DeniedSsm]:
    """The deployed role: SSM refused, every other client moto-backed."""
    _clean_env(monkeypatch)
    denied = DeniedSsm()
    real_client = boto3.client

    def client(service: str, *args: Any, **kwargs: Any) -> Any:  # boto3 ships no stubs
        return denied if service == "ssm" else real_client(service, *args, **kwargs)

    monkeypatch.setattr(boto3, "client", client)
    with mock_aws():
        yield denied


@pytest.fixture
def ssm_says(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[[str], None]]:
    """A readable moto-backed SSM switch, set to the given value."""
    _clean_env(monkeypatch)
    with mock_aws():
        client = boto3.client("ssm", region_name=ssm._REGION)

        def put(value: str) -> None:
            client.put_parameter(Name=_PARAMETER, Value=value, Type="String", Overwrite=True)

        yield put
