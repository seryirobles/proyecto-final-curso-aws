"""authorizer.py: the REQUEST-type Lambda authorizer (R6-R10)."""

from __future__ import annotations

from datetime import timedelta

from _helpers import make_deps, seed_user
from planner_core.application.authentication import logout
from planner_core.domain.role import Role
from support.fakes import FakeClock

from planner_api.authorizer import handle

_METHOD_ARN = "arn:aws:execute-api:eu-west-1:123:abc/prod/GET/v1/weeks/2026-W33"


def _event(cookie_header: str | None) -> dict[str, object]:
    headers: dict[str, str] = {} if cookie_header is None else {"Cookie": cookie_header}
    return {"methodArn": _METHOD_ARN, "headers": headers}


def test_a_valid_session_cookie_is_allowed_with_userid_role_and_password_context() -> None:
    deps = make_deps()
    token = seed_user(deps, user_id="u-1", role=Role.ADMIN, password_reset_required=True)

    result = handle(_event(f"session={token}"), deps)

    assert result["policyDocument"]["Statement"][0]["Effect"] == "Allow"
    assert result["context"] == {
        "userId": "u-1",
        "role": "admin",
        "passwordResetRequired": "true",
    }


def test_a_missing_cookie_header_is_denied() -> None:
    deps = make_deps()

    result = handle(_event(None), deps)

    assert result["policyDocument"]["Statement"][0]["Effect"] == "Deny"


def test_an_unparseable_cookie_is_denied() -> None:
    deps = make_deps()

    result = handle(_event("not a cookie header at all;;;="), deps)

    assert result["policyDocument"]["Statement"][0]["Effect"] == "Deny"


def test_an_expired_session_token_is_denied() -> None:
    deps = make_deps()
    token = deps.signer.issue("ghost", deps.clock.now())  # no matching account was ever created

    result = handle(_event(f"session={token}"), deps)

    assert result["policyDocument"]["Statement"][0]["Effect"] == "Deny"


def test_authenticate_is_evaluated_on_every_call_never_cached() -> None:
    """R10 - two calls with a token later revoked must each get a fresh answer."""
    clock = FakeClock.at("2026-08-17T10:00:00+00:00")
    deps = make_deps(clock=clock)
    token = seed_user(deps, user_id="u-1")

    first = handle(_event(f"session={token}"), deps)
    assert first["policyDocument"]["Statement"][0]["Effect"] == "Allow"

    clock.instant = clock.instant + timedelta(days=1)  # revocation must postdate issuance
    logout("u-1", accounts=deps.accounts, clock=deps.clock)
    second = handle(_event(f"session={token}"), deps)

    assert second["policyDocument"]["Statement"][0]["Effect"] == "Deny"
