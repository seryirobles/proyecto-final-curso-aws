"""AI output with an empty ingredients, tools or procedure list never becomes
a preview: it surfaces as a per-slot failure (G-89, G-66, FR-AI-12).

Issue 8 (recipe-saved-without-required-sections): E4, E5, E7.
"""

from __future__ import annotations

from typing import Any

import pytest

from planner_core import messages
from planner_core.domain.ai_output import (
    GenerationFailure,
    GenerationFailureReason,
    GenerationSuccess,
    RawIngredient,
    RawRecipeOutput,
    validate_ai_recipe_output,
    validate_and_preview,
)
from planner_core.domain.errors import PlannerError
from planner_core.domain.ingredient_category import IngredientCategory

SECTIONS = ["ingredients", "tools", "procedure"]


def _raw(**overrides: Any) -> RawRecipeOutput:
    fields: dict[str, Any] = {
        "name": "Lentejas con chorizo",
        "ingredients": (RawIngredient(name="lentejas", quantity=500.0, unit="g"),),
        "tools": ("olla",),
        "procedure": ("Cocer las lentejas.",),
        "category": "legume",
    }
    fields.update(overrides)
    return RawRecipeOutput(**fields)


@pytest.mark.parametrize("section", SECTIONS)
def test_ai_output_validation_rejects_an_empty_section(section: str) -> None:
    """E4: the validator refuses to build a Recipe from a section-less output."""
    with pytest.raises(PlannerError):
        validate_ai_recipe_output(_raw(**{section: ()}))


@pytest.mark.parametrize("section", SECTIONS)
def test_an_empty_section_surfaces_as_a_generation_failure(section: str) -> None:
    """E5: validate_and_preview returns a value, never a propagated raise (G-48, G-66)."""
    outcome = validate_and_preview(_raw(**{section: ()}))

    assert isinstance(outcome, GenerationFailure)
    assert outcome.reason is GenerationFailureReason.INVALID_OUTPUT
    assert outcome.message == messages.AI_GENERATION_INVALID_OUTPUT


def test_a_complete_ai_recipe_still_validates() -> None:
    """E7."""
    recipe = validate_ai_recipe_output(_raw())

    assert len(recipe.ingredients) == 1
    assert recipe.tools == ("olla",)
    assert recipe.procedure == ("Cocer las lentejas.",)
    assert recipe.category is IngredientCategory.LEGUME


def test_a_complete_ai_recipe_still_previews() -> None:
    """E7."""
    assert isinstance(validate_and_preview(_raw()), GenerationSuccess)
