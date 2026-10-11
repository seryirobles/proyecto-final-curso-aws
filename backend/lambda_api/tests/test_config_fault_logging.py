"""A server-side configuration fault answered as 4xx is logged; ordinary client
errors are not (issues/silent-failures-not-logged E5-E6)."""

from __future__ import annotations

import logging
from typing import Any

import pytest
from _helpers import api_event, authorizer_context, make_deps, seed_user
from planner_core.domain.ai_prompt import PROMPT_VERSION_CONFIG_KEY
from support.fakes import FakeConfig

from planner_api.handler import handle

RECIPE_BODY: dict[str, Any] = {
    "type": "recipe",
    "target": {"kind": "library"},
    "source": {"kind": "specification", "ingredients": ["lentejas"], "tools": ["olla"]},
}


def _warnings(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.levelno >= logging.WARNING]


@pytest.mark.parametrize(
    ("config", "expected"),
    [({}, PROMPT_VERSION_CONFIG_KEY), ({PROMPT_VERSION_CONFIG_KEY: "v99"}, "v99")],
    ids=["unset", "unknown"],
)
def test_an_unresolvable_prompt_version_is_logged(
    caplog: pytest.LogCaptureFixture, config: dict[str, str], expected: str
) -> None:
    """E5 - issue 13's 422 left no cause in the log (FR-AI-14, NFR-OBS-01)."""
    deps = make_deps(config=FakeConfig(config))
    seed_user(deps, user_id="u-1")
    event = api_event("POST", "/v1/generations", body=RECIPE_BODY, context=authorizer_context())

    with caplog.at_level(logging.WARNING):
        response = handle(event, deps)

    assert response["statusCode"] == 422
    assert _warnings(caplog)
    assert expected in caplog.text


def test_an_ordinary_client_error_logs_no_warning(caplog: pytest.LogCaptureFixture) -> None:
    """E6 - expected 4xx stay out of WARNING, or the log floods."""
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    event = api_event(
        "POST", "/v1/generations", body={"type": "bogus"}, context=authorizer_context()
    )

    with caplog.at_level(logging.WARNING):
        response = handle(event, deps)

    assert response["statusCode"] == 400
    assert _warnings(caplog) == []
