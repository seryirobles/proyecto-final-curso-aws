"""The worker's per-record log lines name the generation in the message text."""

from __future__ import annotations

import json
import logging

import pytest
from planner_core.ports.generation_queue import StoredGeneration
from support.fakes import (
    FakeAiProvider,
    FakeClock,
    FakeGenerationGate,
    FakeGenerationQueue,
    FakeRecipeRepository,
    FakeWeekRepository,
)

from planner_ai.handler import handle
from planner_ai.wiring import Dependencies

KEY = "k-log-line-1"


def _deps(queue: FakeGenerationQueue) -> Dependencies:
    return Dependencies(
        provider=FakeAiProvider(),
        weeks=FakeWeekRepository(),
        recipes=FakeRecipeRepository(),
        records=queue,
        gate=FakeGenerationGate(),
        clock=FakeClock.at("2026-08-17T10:00:00+00:00"),
    )


def _recipe_body() -> str:
    return json.dumps(
        {
            "type": "recipe",
            "idPeticionIA": KEY,
            "target": {"kind": "library"},
            "source": {"kind": "specification", "ingredients": ["lentejas"], "tools": ["olla"]},
            "referenceRecipe": None,
            "promptVersionId": "v1",
            "authorUserId": "u-1",
        }
    )


def _week_body() -> str:
    return json.dumps(
        {
            "idPeticionIA": KEY,
            "weekId": "2026-W34",
            "mode": "mix",
            "promptVersionId": "v1",
            "authorUserId": "u-1",
            "effectiveRules": {},
        }
    )


@pytest.mark.parametrize("body", [_recipe_body(), _week_body()], ids=["recipe", "week"])
def test_the_processed_line_names_the_generation(
    caplog: pytest.LogCaptureFixture, body: str
) -> None:
    """E8 - the key a failed record is looked up by appears in the text."""
    queue = FakeGenerationQueue()
    queue.stored[KEY] = StoredGeneration(idempotency_key=KEY, status="pending")
    caplog.set_level(logging.INFO, logger="planner_ai")

    handle({"Records": [{"body": body}]}, _deps(queue))

    assert any(KEY in r.getMessage() for r in caplog.records if r.name.startswith("planner_ai"))
