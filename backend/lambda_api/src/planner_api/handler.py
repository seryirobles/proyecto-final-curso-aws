"""The `api` Lambda's HTTP entry point (docs/conventions.md - thin: parse the
event, call one use case, map the result). Structured logging on every
invocation (R22); no `print` (R23); `Cache-Control: no-store` always (R30)."""

from __future__ import annotations

import json
import logging
from typing import Any  # untyped JSON in/out is the wire boundary itself (conventions.md)

from planner_core.domain.authentication_guards import PasswordResetPending
from planner_core.domain.authorization import Forbidden
from planner_core.domain.role import Role

from planner_api import errors
from planner_api import serialization as ser
from planner_api.conditional_get import parse_if_none_match
from planner_api.routing import ROUTES, AuthContext, quoted_etag
from planner_api.serialization import RouteNotFound
from planner_api.wiring import Dependencies, build_dependencies

logger = logging.getLogger("planner_api")


def _auth_context(event: dict[str, Any]) -> AuthContext:
    """R8, R12 - taken verbatim from the authorizer context, never re-read."""
    context = event.get("requestContext", {}).get("authorizer", {})
    return AuthContext(
        user_id=str(context["userId"]),
        role=Role(str(context["role"])),
        password_reset_required=str(context.get("passwordResetRequired", "false")) == "true",
    )


def _response(
    status: int,
    body: dict[str, Any] | None,
    *,
    etag: str | None = None,
    location: str | None = None,
    set_cookie: str | None = None,
) -> dict[str, Any]:
    headers: dict[str, str] = {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",  # R30, on every response including errors
    }
    if etag is not None:
        headers["ETag"] = etag
    if location is not None:
        headers["Location"] = location
    if set_cookie is not None:
        headers["Set-Cookie"] = set_cookie
    return {
        "statusCode": status,
        "headers": headers,
        "body": "" if body is None else json.dumps(body),
    }


def handle(event: dict[str, Any], deps: Dependencies | None = None) -> dict[str, Any]:
    """`deps` is injected by tests; a deployed function resolves the real
    stack from `wiring.build_dependencies()` (T13)."""
    method = str(event["httpMethod"])
    resource = str(event["resource"])
    status = 500
    try:
        spec = ROUTES.get((method, resource))
        if spec is None:
            raise RouteNotFound
        auth = None if spec.public else _auth_context(event)
        if auth is not None:
            if spec.requires_role is not None and auth.role is not spec.requires_role:
                raise Forbidden(auth.role)
            if auth.password_reset_required and not spec.allow_during_password_reset:
                raise PasswordResetPending
        resolved_deps = deps or build_dependencies()
        path_params = event.get("pathParameters") or {}
        query_params = event.get("queryStringParameters") or {}
        if method == "GET" and spec.current_version_reader is not None:
            held = parse_if_none_match((event.get("headers") or {}).get("If-None-Match"))
            if held is not None:
                current = spec.current_version_reader(path_params, resolved_deps)
                if held == current:  # R2 - matched marker short-circuits to 304
                    status = 304
                    return _response(304, None, etag=quoted_etag(current))
        body = ser.parse_json_body(event.get("body"))
        result = spec.handler(path_params, query_params, body, auth, resolved_deps)
        status = result.status
        return _response(
            result.status,
            result.body,
            etag=result.etag,
            location=result.location,
            set_cookie=result.set_cookie,
        )
    except Exception as exc:  # the sanctioned boundary catch (conventions.md)
        problem = errors.build_problem_response(exc)
        status = problem.status
        return _response(problem.status, problem.body)
    finally:
        logger.info(  # R22 - one structured record per invocation
            "Handled request", extra={"method": method, "resource": resource, "status": status}
        )


lambda_handler = handle
