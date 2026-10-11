"""Every prompt asks for one dish named after itself, not a "menu" the model
echoes as the title; the change is a new version (FR-AI-01, FR-AI-02, FR-AI-06,
FR-AI-14) (issues/generated-recipe-title-is-the-instruction)."""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import pytest
from planner_core.domain.ai_output import recipe_output_schema
from planner_core.domain.ai_prompt import (
    HEALTHY_BALANCED_INSTRUCTION_V4,
    PROMPT_INSTRUCTION_VERSIONS,
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

# The registry is append-only (R2), so the newest version is the last key.
LATEST = list(PROMPT_INSTRUCTION_VERSIONS)[-1]
RETAINED_AT_TRIAGE = ("v1", "v2", "v3")
MODES = ("specification", "reference", "week_slot")
_DOC = Path(__file__).resolve().parents[3] / "docs" / "local_development.md"

_REFERENCE = Recipe(
    name="Tortilla de patatas",
    ingredients=(Ingredient(name="patata", quantity=500, unit=parse_unit("g")),),
    tools=("sarten",),
    procedure=("Freir la patata.", "Cuajar con el huevo."),
    category=IngredientCategory.CARBOHYDRATE,
)


def _rendered(mode: str, version_id: str = LATEST) -> str:
    prompts: dict[str, AiPrompt] = {
        "specification": build_specification_prompt(("test",), ("test",), version_id),
        "reference": build_reference_prompt(_REFERENCE, ("sin gluten",), version_id),
        "week_slot": build_category_prompt(
            (CategoryCountRule(category=IngredientCategory.FISH, count=2),), version_id
        ),
    }
    return _render(prompts[mode])


@pytest.mark.parametrize("mode", MODES)
def test_the_prompt_never_asks_the_model_to_generate_a_menu(mode: str) -> None:
    """Reproduction: 'Generate a healthy, balanced menu' came back as the title."""
    assert not re.search(r"\bgenerate\b[^.\n]*\bmenu", _rendered(mode), re.IGNORECASE)


@pytest.mark.parametrize("mode", MODES)
def test_the_prompt_asks_for_one_dish(mode: str) -> None:
    """FR-AI-01/02: a single recipe; a week slot is one dish too (FR-AI-03)."""
    rendered = _rendered(mode)

    assert re.search(r"\b(one|single)\b[^.\n]*\b(dish|recipe)\b", rendered, re.IGNORECASE)


@pytest.mark.parametrize("mode", MODES)
def test_the_prompt_asks_to_name_the_recipe_after_the_dish(mode: str) -> None:
    rendered = _rendered(mode)

    assert re.search(r"\bname\b[^.\n]*\bdish\b", rendered, re.IGNORECASE)


def test_the_schema_name_description_asks_for_the_dish_name() -> None:
    """The tool schema, which the model also reads, names the dish too (owner Q4)."""
    description = str(recipe_output_schema()["properties"]["name"]["description"])

    assert re.search(r"\bdish\b", description, re.IGNORECASE)


@pytest.mark.parametrize("mode", MODES)
def test_the_prompt_still_carries_the_fr_ai_06_and_fr_ai_07_instructions(mode: str) -> None:
    """Guard: healthy, balanced, varied protein, non-medical label, es-ES."""
    rendered = _rendered(mode).lower()

    for word in ("healthy", "balanced", "protein", "medical", "es-es"):
        assert word in rendered


def test_the_fix_ships_as_a_new_prompt_version() -> None:
    """FR-AI-14: wording changes append a version; none is edited in place."""
    assert LATEST not in RETAINED_AT_TRIAGE
    assert set(RETAINED_AT_TRIAGE) <= set(PROMPT_INSTRUCTION_VERSIONS)


def test_v4_differs_from_v3_only_in_the_healthy_balanced_instruction() -> None:
    """Guard: v4 keeps v3's other wording, e.g. G-90's whole-minutes time."""
    v3, v4 = PROMPT_INSTRUCTION_VERSIONS["v3"], PROMPT_INSTRUCTION_VERSIONS["v4"]

    assert v4 == dataclasses.replace(
        v3, version_id="v4", healthy_balanced_instruction=HEALTHY_BALANCED_INSTRUCTION_V4
    )


def test_v3_renders_byte_for_byte_as_at_triage() -> None:
    """Guard: a retained version keeps its exact wording (FR-AI-14)."""
    rendered = _render(build_specification_prompt(("pollo", "arroz"), ("sarten",), "v3"))

    assert rendered == "\n".join(
        [
            "Generate a healthy, balanced menu, varying the protein sources across dishes. "
            "This instruction is for household meal-planning purposes only and does not "
            "constitute medical advice.",
            "Also state the number of diners it serves and an estimated preparation and "
            "cooking time, in whole minutes, for each generated recipe. These are purely "
            "informational: do not adjust the ingredient quantities based on them.",
            "Output language: es-ES.",
            "Allowed units: g, ml, unit.",
            "Ingredients: pollo, arroz.",
            "Tools: sarten.",
            "Respond EXCLUSIVELY with a JSON object with the keys: name (str), ingredients "
            "(list of {name, quantity, unit}), tools (list of str), procedure (list of str), "
            "category (str), servings (int|null); estimated_time (int|null, whole minutes "
            "from 0 to 6000 inclusive). No additional text.",
        ]
    )


def test_the_documented_local_env_selects_the_newest_version() -> None:
    text = _DOC.read_text(encoding="utf-8")
    found = re.search(r"^export\s+AI_PROMPT_VERSION_ID=(\S+)", text, re.MULTILINE)

    assert found is not None
    assert found.group(1) == LATEST
