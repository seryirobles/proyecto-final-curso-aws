"""A worker run through the real wiring's gate: switch off gives what the SSM off
path gives, switch on reaches the provider under the shared role
(issues/ai-kill-switch-unreadable-under-shared-role E1, E7)."""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Callable
from typing import Any

import pytest
from _env_switch_fixtures import SWITCH, DeniedSsm
from _env_switch_fixtures import shared_role as shared_role  # re-exported fixture
from _env_switch_fixtures import ssm_says as ssm_says  # re-exported fixture
from planner_core.domain.generation import SlotProgress, SlotStatus
from planner_core.messages import AI_GENERATION_UNAVAILABLE
from planner_core.ports.generation_queue import StoredGeneration
from support.fakes import (
    FakeAiProvider,
    FakeClock,
    FakeGenerationQueue,
    FakeRecipeRepository,
    FakeWeekRepository,
)

from planner_ai import wiring
from planner_ai.handler import handle

_KEY = "k1"
_WEEK: dict[str, Any] = {
    "idPeticionIA": _KEY,
    "weekId": "2026-W34",
    "mode": "mix",
    "promptVersionId": "v1",
    "authorUserId": "u-1",
    "effectiveRules": {},
}
_BODIES: dict[str, dict[str, Any]] = {
    "week": _WEEK,
    "slot_retry": {**_WEEK, "type": "slot_retry", "day": 7, "slot": 1},
    "recipe": {
        "type": "recipe",
        "idPeticionIA": _KEY,
        "target": {"kind": "library"},
        "source": {"kind": "specification", "ingredients": ["lentejas"], "tools": ["olla"]},
        "referenceRecipe": None,
        "promptVersionId": "v1",
        "authorUserId": "u-1",
    },
}
_FRIENDLY = {"code": "generation_unavailable", "message": AI_GENERATION_UNAVAILABLE}


def _stored(kind: str) -> StoredGeneration:
    if kind != "slot_retry":
        return StoredGeneration(idempotency_key=_KEY, status="pending")
    slots = (SlotProgress(7, 1, SlotStatus.PENDING), SlotProgress(7, 2, SlotStatus.DONE))
    return StoredGeneration(idempotency_key=_KEY, status="running", slots=slots)


def _run(kind: str) -> tuple[FakeGenerationQueue, FakeAiProvider]:
    """Everything fake except the gate, which is whatever the real wiring picks."""
    queue = FakeGenerationQueue()
    queue.stored[_KEY] = _stored(kind)
    provider = FakeAiProvider()
    deps = dataclasses.replace(
        wiring.build_dependencies(),
        provider=provider,
        weeks=FakeWeekRepository(),
        recipes=FakeRecipeRepository(),
        records=queue,
        clock=FakeClock.at("2026-08-17T10:00:00+00:00"),
    )
    handle({"Records": [{"body": json.dumps(_BODIES[kind])}]}, deps)
    return queue, provider


@pytest.mark.parametrize("kind", ["week", "recipe", "slot_retry"])
def test_a_run_with_the_switch_off_matches_the_ssm_off_path(
    ssm_says: Callable[[str], None], monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """E7 - SSM says on for the switch run, so only the variable can stop it."""
    ssm_says("false")
    ssm_off, _ = _run(kind)

    ssm_says("true")
    monkeypatch.setenv(SWITCH, "false")
    switch_off, provider = _run(kind)

    assert provider.calls == 0
    assert switch_off.stored[_KEY] == ssm_off.stored[_KEY]
    assert switch_off.results == ssm_off.results


def test_a_week_run_with_the_switch_off_shows_the_friendly_message_on_every_slot(
    ssm_says: Callable[[str], None], monkeypatch: pytest.MonkeyPatch
) -> None:
    """E7 - NFR-AI-01's message in the per-slot shape FR-AI-12 asks for."""
    ssm_says("true")
    monkeypatch.setenv(SWITCH, "false")

    queue, _ = _run("week")

    slots = queue.stored[_KEY].slots or ()
    assert slots
    assert {p.status for p in slots} == {SlotStatus.ERROR}
    assert {(p.error.code, p.error.message) for p in slots if p.error} == {
        (_FRIENDLY["code"], _FRIENDLY["message"])
    }
    assert queue.stored[_KEY].status == "failed"


def test_a_recipe_run_with_the_switch_off_records_the_friendly_failure(
    ssm_says: Callable[[str], None], monkeypatch: pytest.MonkeyPatch
) -> None:
    """E7 - R22."""
    ssm_says("true")
    monkeypatch.setenv(SWITCH, "false")

    queue, _ = _run("recipe")

    assert queue.results[_KEY] == {"error": _FRIENDLY}
    assert queue.stored[_KEY].status == "failed"


def test_a_week_run_with_the_switch_on_reaches_the_provider_under_the_shared_role(
    shared_role: DeniedSsm, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E1 - reproduction end to end: the deployed app generates again."""
    monkeypatch.setenv(SWITCH, "true")

    queue, provider = _run("week")

    assert provider.calls > 0
    assert queue.stored[_KEY].status == "completed"
    assert shared_role.reads == 0
