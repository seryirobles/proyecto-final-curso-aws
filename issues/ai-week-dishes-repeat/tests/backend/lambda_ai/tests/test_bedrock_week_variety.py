"""Issue ai-week-dishes-repeat: the text Bedrock receives for a later slot of a
whole-week run names the dishes the earlier slots produced
(issues/ai-week-dishes-repeat/plan.md E1, E5). No live call."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from planner_core.application.week_generation import run_week_generation
from planner_core.domain.ai_prompt import PROMPT_INSTRUCTION_VERSIONS
from planner_core.domain.calendar import IsoWeek
from planner_core.domain.generation import GenerationMode, GenerationRequest
from planner_core.domain.rules import RuleSet
from planner_core.ports.generation_queue import StoredGeneration
from support.fakes import (
    FakeGenerationGate,
    FakeGenerationQueue,
    FakeRecipeRepository,
    FakeWeekRepository,
)

from planner_ai.adapters.bedrock import BedrockAiProvider

WEEK = IsoWeek(2026, 34)
KEY = "hash-1"
SATURDAY = date.fromisocalendar(2026, 34, 6)  # 4 open slots
LATEST = list(PROMPT_INSTRUCTION_VERSIONS)[-1]
DISHES = (
    "Ensalada de quinoa con aguacate",
    "Lentejas estofadas",
    "Merluza en salsa verde",
    "Pollo al horno con patatas",
)


class _Client:
    """Converse stand-in: one forced-tool recipe per call, in DISHES order."""

    def __init__(self) -> None:
        self.texts: list[str] = []

    def converse(self, **kwargs: Any) -> dict[str, Any]:
        self.texts.append(kwargs["messages"][0]["content"][0]["text"])
        recipe = {
            "name": DISHES[len(self.texts) - 1],
            "ingredients": [{"name": "arroz", "quantity": 100, "unit": "g"}],
            "tools": ["olla"],
            "procedure": ["Cocer."],
            "category": "carbohydrate",
        }
        tool_use = {"toolUseId": "t-1", "name": "submit_recipe", "input": recipe}
        return {"output": {"message": {"content": [{"toolUse": tool_use}]}}}


@pytest.fixture(autouse=True)
def _default_inference(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("AI_TEMPERATURE", "AI_TOP_P", "AI_REASONING_ENABLED", "AI_REASONING_EFFORT"):
        monkeypatch.delenv(name, raising=False)


def test_the_model_is_told_the_dishes_of_earlier_slots_in_the_run() -> None:
    """E1, E5 — reproduction at the model boundary."""
    client = _Client()
    queue = FakeGenerationQueue()
    queue.stored[KEY] = StoredGeneration(idempotency_key=KEY, status="pending", slots=())

    run_week_generation(
        KEY,
        GenerationRequest(week=WEEK, mode=GenerationMode.AI_ONLY),
        RuleSet(),
        LATEST,
        "u-1",
        SATURDAY,
        provider=BedrockAiProvider(client=client),
        weeks=FakeWeekRepository(),
        recipes=FakeRecipeRepository(),
        queue=queue,
        gate=FakeGenerationGate(),
    )

    assert len(client.texts) == 4
    last = client.texts[-1].casefold()
    assert [name for name in DISHES[:3] if name.casefold() not in last] == []
