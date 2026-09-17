"""local_server.py: the HTTP-request -> proxy-event translation and the
authorizer-then-handler orchestration, exercised the same way test_handler.py
and test_authorizer.py exercise their entry points - no real socket."""

from __future__ import annotations

import json

from _helpers import make_deps, seed_user
from planner_core.domain.role import Role
from planner_core.ports.accounts import AccountRecord

from planner_api import local_server


def test_match_resource_extracts_path_parameters() -> None:
    matched = local_server.match_resource("/v1/weeks/2026-W30/days/1/slots/1/candidates/c-1")

    assert matched is not None
    assert matched.resource == "/v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates/{candidateId}"
    assert matched.path_params == {
        "weekId": "2026-W30",
        "day": "1",
        "slot": "1",
        "candidateId": "c-1",
    }


def test_match_resource_returns_none_for_an_unrouted_path() -> None:
    assert local_server.match_resource("/v1/does-not-exist") is None


def test_match_resource_rejects_a_trailing_slash() -> None:
    """Real API Gateway resource matching is exact - a trailing slash must not
    resolve to the same route as the canonical path."""
    assert local_server.match_resource("/v1/live-weeks/") is None


def test_match_resource_rejects_a_doubled_slash() -> None:
    assert local_server.match_resource("//v1//live-weeks") is None


def test_a_request_with_no_session_cookie_is_denied_before_the_handler_runs() -> None:
    deps = make_deps()

    response = local_server.handle_request("GET", "/v1/live-weeks", {}, None, deps=deps)

    assert response["statusCode"] == 403


def test_an_authenticated_request_round_trips_through_the_real_handler() -> None:
    deps = make_deps()
    token = seed_user(deps, user_id="u-1")
    headers = {"Cookie": f"session={token}"}

    response = local_server.handle_request("GET", "/v1/live-weeks", headers, None, deps=deps)

    assert response["statusCode"] == 200
    assert "today" in json.loads(response["body"])


def test_a_lowercase_if_none_match_header_still_304s() -> None:
    """`http.server` preserves whatever case the client sent (`fetch`/curl
    send lowercase); `handler.py` looks up the exact-case `If-None-Match`, so
    `handle_request` must normalize headers before building the proxy event."""
    deps = make_deps()
    token = seed_user(deps, user_id="u-1")
    headers = {"cookie": f"session={token}", "if-none-match": '"0"'}  # fresh list -> marker 0

    response = local_server.handle_request("GET", "/v1/shopping-list", headers, None, deps=deps)

    assert response["statusCode"] == 304


def test_a_public_route_never_reaches_the_authorizer() -> None:
    """POST /v1/session is public (routing.ROUTES) - API Gateway would not
    attach the authorizer to it, so this must not deny a login for lack of a
    cookie the client cannot have yet."""
    deps = make_deps()
    deps.accounts.create(
        AccountRecord(
            user_id="u-1",
            username="marta",
            role=Role.USER,
            password_hash=deps.hasher.hash("s3cret1234"),
            password_reset_required=False,
            credentials_valid_since=deps.clock.now(),
        )
    )
    body = json.dumps({"username": "marta", "password": "s3cret1234"}).encode("utf-8")

    response = local_server.handle_request("POST", "/v1/session", {}, body, deps=deps)

    assert response["statusCode"] == 200
