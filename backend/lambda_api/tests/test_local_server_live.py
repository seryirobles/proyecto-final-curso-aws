"""Real HTTP round trip (stdlib `http.client`, no mocked dispatch) against a
`local_server` instance backed by real DynamoDB Local (docs/verification.md
"Docker (local)" tier)."""

from __future__ import annotations

import json
import threading
import uuid
from collections.abc import Iterator
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

import pytest
from _docker_fixtures import docker_dynamodb as docker_dynamodb  # re-exported fixture
from planner_core.domain.role import Role
from planner_core.ports.accounts import AccountRecord

from planner_api import local_server
from planner_api.wiring import build_dependencies

pytestmark = pytest.mark.docker


@pytest.fixture
def live_server(docker_dynamodb: None) -> Iterator[int]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), local_server._RequestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield port
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def _seed_user() -> tuple[str, str]:
    # Each request handled by the running server calls build_dependencies()
    # again itself; both land on the same real table/secret via env, so
    # seeding through a freshly-built Dependencies is visible to it.
    username = f"live-{uuid.uuid4().hex[:8]}"
    deps = build_dependencies()
    deps.accounts.create(
        AccountRecord(
            user_id=f"u-{username}",
            username=username,
            role=Role.USER,
            password_hash=deps.hasher.hash("s3cret1234"),
            password_reset_required=False,
            credentials_valid_since=deps.clock.now(),
        )
    )
    return username, "s3cret1234"


def test_an_unauthenticated_request_is_denied(live_server: int) -> None:
    conn = HTTPConnection("127.0.0.1", live_server)
    conn.request("GET", "/v1/live-weeks")
    response = conn.getresponse()

    assert response.status == 403


def test_login_sets_a_session_cookie(live_server: int) -> None:
    username, password = _seed_user()
    conn = HTTPConnection("127.0.0.1", live_server)
    body = json.dumps({"username": username, "password": password})

    conn.request("POST", "/v1/session", body=body, headers={"Content-Type": "application/json"})
    response = conn.getresponse()
    response.read()

    assert response.status == 200
    assert "session=" in (response.getheader("Set-Cookie") or "")


def _login(port: int, username: str, password: str) -> str:
    conn = HTTPConnection("127.0.0.1", port)
    conn.request(
        "POST",
        "/v1/session",
        body=json.dumps({"username": username, "password": password}),
        headers={"Content-Type": "application/json"},
    )
    response = conn.getresponse()
    response.read()
    cookie = response.getheader("Set-Cookie") or ""
    return cookie.split(";")[0]


def test_authenticated_shopping_list_read_hits_real_dynamodb(live_server: int) -> None:
    username, password = _seed_user()
    cookie = _login(live_server, username, password)

    conn = HTTPConnection("127.0.0.1", live_server)
    conn.request("GET", "/v1/shopping-list", headers={"Cookie": cookie})
    response = conn.getresponse()
    payload = json.loads(response.read())

    assert response.status == 200
    assert "items" in payload


def test_a_lowercase_if_none_match_header_still_304s(live_server: int) -> None:
    # The shopping list is a global singleton (docs/data_model.md SHOPPING_LIST_ID
    # = "default"), not per-user, and the container persists across test runs -
    # read the current marker instead of assuming a fresh 0.
    username, password = _seed_user()
    cookie = _login(live_server, username, password)

    conn = HTTPConnection("127.0.0.1", live_server)
    conn.request("GET", "/v1/shopping-list", headers={"Cookie": cookie})
    first = conn.getresponse()
    first.read()
    etag = first.getheader("ETag")
    assert etag is not None

    conn = HTTPConnection("127.0.0.1", live_server)
    # lowercase header proves _normalize_headers runs over a real socket, not
    # just the in-process handle_request unit test.
    conn.request(
        "GET",
        "/v1/shopping-list",
        headers={"cookie": cookie, "if-none-match": etag},
    )
    response = conn.getresponse()
    response.read()

    assert response.status == 304


def test_a_trailing_slash_does_not_match_the_canonical_route(live_server: int) -> None:
    username, password = _seed_user()
    cookie = _login(live_server, username, password)

    conn = HTTPConnection("127.0.0.1", live_server)
    conn.request("GET", "/v1/shopping-list/", headers={"Cookie": cookie})
    response = conn.getresponse()
    response.read()

    assert response.status == 404
