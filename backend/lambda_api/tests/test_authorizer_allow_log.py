"""An allowed authorizer request leaves one fixed INFO record, with no identity
(issues/deployed-lambdas-drop-info-logs E11)."""

from __future__ import annotations

import logging

import pytest
from _helpers import make_deps, seed_user
from planner_core.domain.role import Role

from planner_api.authorizer import handle

_METHOD_ARN = "arn:aws:execute-api:eu-west-1:123:abc/prod/GET/v1/weeks/2026-W33"
_USER_ID = "u-allow-log-1"


def test_an_allowed_request_emits_one_fixed_info_record_without_identity(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """E11 - no user id, role or token in the text or in `extra`."""
    caplog.set_level(logging.INFO, logger="planner_api")
    deps = make_deps()
    token = seed_user(deps, user_id=_USER_ID, role=Role.ADMIN)
    event = {"methodArn": _METHOD_ARN, "headers": {"Cookie": f"session={token}"}}

    result = handle(event, deps)

    assert result["policyDocument"]["Statement"][0]["Effect"] == "Allow"
    records = [r for r in caplog.records if r.name.startswith("planner_api")]
    assert [r.levelno for r in records] == [logging.INFO]
    assert records[0].getMessage() == "Allowing authorizer request"
    standard = set(vars(logging.makeLogRecord({}))) | {"message", "asctime"}
    extras = [str(v) for k, v in vars(records[0]).items() if k not in standard]
    dumped = " ".join([records[0].getMessage(), *extras])
    for secret in (_USER_ID, Role.ADMIN.value, token):
        assert secret not in dumped


def _info_texts(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.name.startswith("planner_api")]


def test_a_request_with_no_cookie_logs_only_its_deny_line(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """E11 - the Deny branches stay as they were; no Allow text."""
    caplog.set_level(logging.INFO, logger="planner_api")

    handle({"methodArn": _METHOD_ARN, "headers": {}}, make_deps())

    assert _info_texts(caplog) == ["Denying authorizer request with no session cookie"]
    assert [r.levelno for r in caplog.records] == [logging.INFO]


def test_an_expired_session_logs_only_its_deny_line(caplog: pytest.LogCaptureFixture) -> None:
    """E11 - same, for the expired-session branch."""
    caplog.set_level(logging.INFO, logger="planner_api")
    deps = make_deps()
    token = deps.signer.issue("ghost", deps.clock.now())  # no matching account
    event = {"methodArn": _METHOD_ARN, "headers": {"Cookie": f"session={token}"}}

    handle(event, deps)

    assert _info_texts(caplog) == ["Denying authorizer request with an expired session"]
    assert [r.levelno for r in caplog.records] == [logging.INFO]
