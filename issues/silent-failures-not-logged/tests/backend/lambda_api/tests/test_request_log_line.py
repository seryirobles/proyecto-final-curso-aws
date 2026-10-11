"""The per-invocation log lines carry their facts in the message text, so any
log format shows them, not only one that prints `extra`
(issues/silent-failures-not-logged E8)."""

from __future__ import annotations

import logging

import pytest
from _helpers import api_event, authorizer_context, make_deps, seed_user

from planner_api import scheduled
from planner_api.handler import handle


def _info_messages(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.name.startswith("planner_api")]


def test_the_request_line_shows_method_resource_and_status(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """E8 - R22's record is readable in the default formatter."""
    caplog.set_level(logging.INFO, logger="planner_api")

    handle(api_event("GET", "/v1/does-not-exist"), make_deps())

    assert any(
        "GET" in m and "/v1/does-not-exist" in m and "404" in m for m in _info_messages(caplog)
    )


def test_the_request_line_omits_cookie_query_and_path_values(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """E8 - NFR-SEC: no session cookie, query string or path id in the text."""
    caplog.set_level(logging.INFO, logger="planner_api")
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    event = api_event(
        "GET",
        "/v1/generations/{generationId}",
        path_params={"generationId": "path-value-123"},
        query={"q": "query-value-456"},
        cookie="cookie-value-789",
        context=authorizer_context(),
    )

    handle(event, deps)

    messages = _info_messages(caplog)
    assert any("/v1/generations/{generationId}" in m for m in messages)
    for secret in ("path-value-123", "query-value-456", "cookie-value-789"):
        assert all(secret not in m for m in messages)


def test_the_rollover_line_shows_the_archived_week(caplog: pytest.LogCaptureFixture) -> None:
    """E8 - same extra-only pattern in scheduled.py."""
    caplog.set_level(logging.INFO, logger="planner_api")

    result = scheduled.handle({}, make_deps())

    assert any(result["archivedWeekId"] in m for m in _info_messages(caplog))
