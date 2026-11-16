"""A non-positive ingredient quantity is rejected wherever one is admitted.

Issue 7 (negative-ingredient-quantity): E2, E3, plus the shopping-arithmetic
regression.
"""

from __future__ import annotations

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
from planner_core.domain.recipe import Ingredient
from planner_core.domain.shopping import aggregate_ingredients, outstanding_amounts
from planner_core.domain.units import parse_unit


def _raw(quantity: float) -> RawRecipeOutput:
    return RawRecipeOutput(
        name="Lentejas con chorizo",
        ingredients=(RawIngredient(name="lentejas", quantity=quantity, unit="g"),),
        tools=("olla",),
        procedure=("Cocer las lentejas.",),
        category="legume",
    )


@pytest.mark.parametrize("quantity", [-500.0, -0.5, 0.0])
def test_ai_output_validation_rejects_a_non_positive_quantity(quantity: float) -> None:
    """E2: the AI path resolves unit and category; the quantity is resolved too."""
    with pytest.raises(PlannerError):
        validate_ai_recipe_output(_raw(quantity))


def test_ai_output_validation_accepts_a_positive_quantity() -> None:
    recipe = validate_ai_recipe_output(_raw(500.0))

    assert recipe.ingredients[0].quantity == 500.0
    assert recipe.category is IngredientCategory.LEGUME


@pytest.mark.parametrize("quantity", [-500.0, 0.0])
def test_a_non_positive_quantity_surfaces_as_a_generation_failure(quantity: float) -> None:
    """E3: validate_and_preview returns a value, never a propagated raise (G-48)."""
    outcome = validate_and_preview(_raw(quantity))

    assert isinstance(outcome, GenerationFailure)
    assert outcome.reason is GenerationFailureReason.INVALID_OUTPUT
    assert outcome.message == messages.AI_GENERATION_INVALID_OUTPUT


def test_a_positive_quantity_still_previews() -> None:
    assert isinstance(validate_and_preview(_raw(500.0)), GenerationSuccess)


def test_aggregation_of_positive_quantities_is_unchanged() -> None:
    """Regression: the FR-SHOP-03/-06 arithmetic keeps summing validated input."""
    gram = parse_unit("g")
    merged = aggregate_ingredients(
        (
            Ingredient(name="arroz", quantity=500.0, unit=gram),
            Ingredient(name="Arroz", quantity=200.0, unit=gram),
        )
    )

    assert merged == (Ingredient(name="arroz", quantity=700.0, unit=gram),)
    assert outstanding_amounts((), merged) == merged
