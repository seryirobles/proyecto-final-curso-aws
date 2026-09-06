"""REQUEST-type Lambda authorizer: the `Cookie` header -> `authenticate()` ->
allow + `{userId, role, passwordResetRequired}` context, or Deny (R6-R10).
A separate entry point in this same package (docs/architecture.md section 1.2)."""

from __future__ import annotations

import logging
from http.cookies import SimpleCookie
from typing import Any  # untyped JSON in/out is the wire boundary itself (conventions.md)

from planner_core.application.authentication import authenticate
from planner_core.domain.session_policy import SessionExpired

from planner_api.wiring import Dependencies, build_dependencies

logger = logging.getLogger("planner_api")

_COOKIE_NAME = "session"


def _read_session_cookie(header: str | None) -> str | None:
    """IF the cookie is absent or unparseable, THEN there is no token to try
    (R9) - `SimpleCookie.load` never raises on garbage input."""
    if not header:
        return None
    jar = SimpleCookie()
    jar.load(header)
    morsel = jar.get(_COOKIE_NAME)
    return None if morsel is None else morsel.value


def _policy(principal_id: str, effect: str, method_arn: str) -> dict[str, Any]:
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {"Action": "execute-api:Invoke", "Effect": effect, "Resource": method_arn}
            ],
        },
    }


def handle(event: dict[str, Any], deps: Dependencies | None = None) -> dict[str, Any]:
    """R7, R10 - `authenticate` runs on every call; nothing here caches a
    decision (the API Gateway authorizer cache TTL is feature 21 IaC)."""
    method_arn = str(event["methodArn"])
    token = _read_session_cookie((event.get("headers") or {}).get("Cookie"))
    if token is None:
        logger.info("Denying authorizer request with no session cookie")
        return _policy("deny", "Deny", method_arn)

    resolved = deps or build_dependencies()
    try:
        account = authenticate(
            token, accounts=resolved.accounts, signer=resolved.signer, clock=resolved.clock
        )
    except SessionExpired:
        logger.info("Denying authorizer request with an expired session")
        return _policy("deny", "Deny", method_arn)

    policy = _policy(account.user_id, "Allow", method_arn)
    policy["context"] = {
        "userId": account.user_id,
        "role": account.role.value,
        "passwordResetRequired": "true" if account.password_reset_required else "false",
    }
    return policy


lambda_handler = handle
