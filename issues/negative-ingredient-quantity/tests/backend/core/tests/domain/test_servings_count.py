"""A non-positive servings count from the AI is rejected, never persisted.

Issue 7 (negative-ingredient-quantity), servings extension: E8, E9.
Contingent on the FR-LIB-03 lift named in the issue's analysis.md.
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


def _raw(servings: int | None) -> RawRecipeOutput:
    return RawRecipeOutput(
        name="Lentejas con chorizo",
        ingredients=(RawIngredient(name="lentejas", quantity=500.0, unit="g"),),
        tools=("olla",),
        procedure=("Cocer las lentejas.",),
        category="legume",
        servings=servings,
    )


@pytest.mark.parametrize("servings", [-4, -1, 0])
def test_ai_output_validation_rejects_a_non_positive_servings(servings: int) -> None:
    """E8: servings is resolved like estimated_time already is (G-90)."""
    with pytest.raises(PlannerError):
        validate_ai_recipe_output(_raw(servings))


@pytest.mark.parametrize("servings", [1, 4, None])
def test_ai_output_validation_keeps_a_positive_or_absent_servings(servings: int | None) -> None:
    assert validate_ai_recipe_output(_raw(servings)).servings == servings


@pytest.mark.parametrize("servings", [-4, 0])
def test_a_non_positive_servings_surfaces_as_a_generation_failure(servings: int) -> None:
    """E9: validate_and_preview returns a value, never a propagated raise (G-48)."""
    outcome = validate_and_preview(_raw(servings))

    assert isinstance(outcome, GenerationFailure)
    assert outcome.reason is GenerationFailureReason.INVALID_OUTPUT
    assert outcome.message == messages.AI_GENERATION_INVALID_OUTPUT


def test_a_positive_servings_still_previews() -> None:
    outcome = validate_and_preview(_raw(4))

    assert isinstance(outcome, GenerationSuccess)
    assert outcome.preview.recipe.servings == 4
