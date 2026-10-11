"""The documented local environment (docs/local_development.md sections 2-3)
must reach AI generation (issues/ai-generation-422-unavailable E1-E4)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from _helpers import api_event, authorizer_context, make_deps, seed_user
from planner_core.domain.ai_prompt import PROMPT_INSTRUCTION_VERSIONS, PROMPT_VERSION_CONFIG_KEY
from planner_core.ports.config import EnvConfig
from support.fakes import FakeGenerationQueue

from planner_api.handler import handle

_DOC = Path(__file__).resolve().parents[3] / "docs" / "local_development.md"
_EXPORT = re.compile(r"^export\s+([A-Z_][A-Z0-9_]*)=(\S+)", re.MULTILINE)

RECIPE_BODY: dict[str, Any] = {
    "type": "recipe",
    "target": {"kind": "library"},
    "source": {"kind": "specification", "ingredients": ["lentejas"], "tools": ["olla"]},
}
WEEK_BODY: dict[str, Any] = {"type": "week", "weekId": "2026-W34", "mode": "library_only"}


def _documented_env(section_number: int) -> dict[str, str]:
    """The `export` lines of the first bash block in the numbered section."""
    text = _DOC.read_text(encoding="utf-8")
    section = text.split(f"\n## {section_number}.", 1)[1].split("\n## ", 1)[0]
    block = section.split("```bash", 1)[1].split("```", 1)[0]
    return dict(_EXPORT.findall(block))


def _documented_api_env() -> dict[str, str]:
    return _documented_env(2)


def _post_under_documented_env(
    monkeypatch: pytest.MonkeyPatch, body: dict[str, Any]
) -> dict[str, Any]:
    monkeypatch.delenv(PROMPT_VERSION_CONFIG_KEY, raising=False)
    for key, value in _documented_api_env().items():
        monkeypatch.setenv(key, value)
    deps = make_deps(queue=FakeGenerationQueue(), config=EnvConfig())
    seed_user(deps, user_id="u-1")
    event = api_event("POST", "/v1/generations", body=body, context=authorizer_context("u-1"))
    return handle(event, deps)


def test_documented_api_env_selects_a_registered_prompt_version() -> None:
    """E1 - FR-AI-14: selected explicitly, and to a version that resolves."""
    env = _documented_api_env()

    assert env.get(PROMPT_VERSION_CONFIG_KEY) in PROMPT_INSTRUCTION_VERSIONS


def test_single_recipe_generation_is_accepted_under_the_documented_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E1 - the reported 422 UNKNOWN_PROMPT_VERSION on "Generar receta" (FR-AI-01)."""
    response = _post_under_documented_env(monkeypatch, RECIPE_BODY)

    assert response["statusCode"] == 202, response["body"]


def test_week_generation_is_accepted_under_the_documented_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E2 - same cause on whole-week generation (FR-AI-03)."""
    response = _post_under_documented_env(monkeypatch, WEEK_BODY)

    assert response["statusCode"] == 202, response["body"]


def test_documented_worker_env_enables_generation_locally() -> None:
    """E4 - section 3 (the ai worker) opts in without reading SSM."""
    assert _documented_env(3).get("AI_GENERATION_ENABLED") == "true"


@pytest.mark.parametrize("body", [RECIPE_BODY, WEEK_BODY], ids=["recipe", "week"])
def test_an_unset_prompt_version_still_fails_without_a_silent_default(
    monkeypatch: pytest.MonkeyPatch, body: dict[str, Any]
) -> None:
    """E3 - FR-AI-14 / G-84: the fix is configuration, never a code default."""
    monkeypatch.delenv(PROMPT_VERSION_CONFIG_KEY, raising=False)
    deps = make_deps(queue=FakeGenerationQueue(), config=EnvConfig())
    seed_user(deps, user_id="u-1")
    event = api_event("POST", "/v1/generations", body=body, context=authorizer_context("u-1"))

    response = handle(event, deps)

    assert response["statusCode"] == 422
    assert json.loads(response["body"])["code"] == "UNKNOWN_PROMPT_VERSION"
