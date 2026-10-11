"""Rendered v4 prompts carry the fallback sentence in every mode
(specs/ai_fallback_recipe R2-R9, R12, R13, R17)."""

from __future__ import annotations

import re

import pytest
from planner_core.domain.ai_prompt import (
    HEALTHY_BALANCED_INSTRUCTION_V4,
    build_category_prompt,
    build_reference_prompt,
    build_specification_prompt,
)
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Ingredient, Recipe
from planner_core.domain.rules import CategoryCountRule
from planner_core.domain.units import parse_unit
from planner_core.ports.ai_provider import AiPrompt

from planner_ai.adapters.bedrock import _render

MODES = ("specification", "reference", "week_slot")
_REFERENCE = Recipe(
    name="Tortilla de patatas",
    ingredients=(Ingredient(name="patata", quantity=500, unit=parse_unit("g")),),
    tools=("sarten",),
    procedure=("Freir la patata.", "Cuajar con el huevo."),
    category=IngredientCategory.CARBOHYDRATE,
)


def _prompt(mode: str, version_id: str) -> AiPrompt:
    prompts: dict[str, AiPrompt] = {
        "specification": build_specification_prompt(("test",), ("test",), version_id),
        "reference": build_reference_prompt(_REFERENCE, ("asdf",), version_id),
        "week_slot": build_category_prompt(
            (CategoryCountRule(category=IngredientCategory.FISH, count=2),), version_id
        ),
    }
    return prompts[mode]


@pytest.mark.parametrize("mode", MODES)
def test_the_fallback_sentence_is_rendered(mode: str) -> None:
    assert HEALTHY_BALANCED_INSTRUCTION_V4 in _render(_prompt(mode, "v4"))


@pytest.mark.parametrize("mode", MODES)
def test_it_names_the_four_unusable_cases_and_the_keep_usable_clause(mode: str) -> None:
    rendered = _render(_prompt(mode, "v4")).lower()

    for case in ("empty", "generic", "unrelated to cooking", "unintelligible"):
        assert case in rendered
    assert "follows these guidelines" in rendered
    assert "honour any part that is usable" in rendered


@pytest.mark.parametrize("mode", MODES)
def test_the_guidelines_and_language_are_still_rendered(mode: str) -> None:
    rendered = _render(_prompt(mode, "v4")).lower()

    for word in ("healthy", "balanced", "protein", "medical", "es-es"):
        assert word in rendered


@pytest.mark.parametrize("mode", MODES)
def test_only_the_healthy_balanced_line_differs_from_v3(mode: str) -> None:
    v3 = _render(_prompt(mode, "v3")).splitlines()
    v4 = _render(_prompt(mode, "v4")).splitlines()

    assert v3[1:] == v4[1:]


@pytest.mark.parametrize("mode", MODES)
def test_v4_never_asks_to_generate_a_menu(mode: str) -> None:
    pattern = r"\bgenerate\b[^.\n]*\bmenu"
    assert not re.search(pattern, _render(_prompt(mode, "v4")), re.IGNORECASE)


def test_the_specification_strings_reach_the_prompt_unchanged() -> None:
    prompt = build_specification_prompt(("test",), ("test",), "v4")

    assert (prompt.ingredients, prompt.tools) == (("test",), ("test",))
