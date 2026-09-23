"""Issue 11 (E1, E5, E7, E8): `tiempo` is a whole number of minutes from 0 to
6000 inclusive, or absent (`G-90`, amending `G-85` and `FR-LIB-03`). The rule
lives in one domain parser; the wire boundary and AI-output validation both use
it, and neither the `Recipe` nor the `MealSnapshot` constructor enforces it — a
recipe already persisted with free text must still be readable (`G-90`, same
reasoning as `G-89`).
"""

from __future__ import annotations

import dataclasses
from typing import Any, get_type_hints

import pytest

from planner_core.domain.ai_output import (
    GenerationFailure,
    GenerationFailureReason,
    GenerationSuccess,
    RawIngredient,
    RawRecipeOutput,
    validate_ai_recipe_output,
    validate_and_preview,
)
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import (
    MAX_ESTIMATED_MINUTES,
    Ingredient,
    InvalidEstimatedTime,
    MealSnapshot,
    Recipe,
    parse_estimated_minutes,
    snapshot,
)
from planner_core.domain.units import Unit
from planner_core.messages import AI_GENERATION_INVALID_OUTPUT


def _recipe() -> Recipe:
    return Recipe(
        name="Lentejas al curry",
        ingredients=(Ingredient(name="lentejas", quantity=300.0, unit=Unit.GRAM),),
        tools=("olla",),
        procedure=("Cocer.",),
        category=IngredientCategory.LEGUME,
    )


def _raw() -> RawRecipeOutput:
    return RawRecipeOutput(
        name="Lentejas al curry",
        ingredients=(RawIngredient(name="lentejas", quantity=300.0, unit="g"),),
        tools=("olla",),
        procedure=("Cocer.",),
        category="legume",
    )


# --- E1, E8: the parser and its range ---------------------------------------


def test_the_permitted_range_ends_at_six_thousand_minutes() -> None:
    """`G-90`: 0 to 6000 inclusive, stated once and reused by both boundaries."""
    assert MAX_ESTIMATED_MINUTES == 6000


@pytest.mark.parametrize("value", [0, 1, 45, 5999, 6000])
def test_parse_estimated_minutes_accepts_an_integer_inside_the_range(value: int) -> None:
    assert parse_estimated_minutes(value) == value


def test_parse_estimated_minutes_accepts_both_bounds_exactly() -> None:
    """Boundary regression: the range is inclusive at both ends."""
    assert parse_estimated_minutes(0) == 0
    assert parse_estimated_minutes(MAX_ESTIMATED_MINUTES) == MAX_ESTIMATED_MINUTES


def test_parse_estimated_minutes_reads_an_absent_value_as_none() -> None:
    assert parse_estimated_minutes(None) is None


@pytest.mark.parametrize("value", [-1, 6001, 100000])
def test_parse_estimated_minutes_rejects_a_count_outside_the_range(value: int) -> None:
    """E8: `G-90` bounds the count at both ends, 6001 as much as -1."""
    with pytest.raises(InvalidEstimatedTime):
        parse_estimated_minutes(value)


@pytest.mark.parametrize("value", ["45 min", "hora y media", "45", "", 45.5, True, []])
def test_parse_estimated_minutes_rejects_a_value_that_is_not_an_integer(value: Any) -> None:
    """Free text, a numeric string, a fraction of a minute and a bool are all
    outside the shape `G-90` fixed."""
    with pytest.raises(InvalidEstimatedTime):
        parse_estimated_minutes(value)


# --- E5: the domain type ---------------------------------------------------


def test_recipe_and_snapshot_declare_estimated_time_as_an_optional_integer() -> None:
    assert get_type_hints(Recipe)["estimated_time"] == (int | None)
    assert get_type_hints(MealSnapshot)["estimated_time"] == (int | None)


def test_snapshot_copies_an_integer_estimated_time() -> None:
    recipe = dataclasses.replace(_recipe(), estimated_time=45)

    assert snapshot(recipe).estimated_time == 45


def test_constructing_a_recipe_with_a_legacy_free_text_value_does_not_raise() -> None:
    """`G-90`: enforcement is at the write boundary, never a constructor
    invariant — a recipe already persisted as "45 min" stays readable."""
    legacy: Any = "45 min"

    recipe = dataclasses.replace(_recipe(), estimated_time=legacy)

    assert recipe.estimated_time == legacy
    assert snapshot(recipe).estimated_time == legacy


# --- E6, E7: AI output validation ------------------------------------------


def test_validate_ai_recipe_output_keeps_an_integer_minute_count() -> None:
    raw = dataclasses.replace(_raw(), estimated_time=30)

    assert validate_ai_recipe_output(raw).estimated_time == 30


def test_validate_ai_recipe_output_reads_an_absent_estimated_time_as_none() -> None:
    assert validate_ai_recipe_output(_raw()).estimated_time is None


def test_validate_ai_recipe_output_rejects_a_free_text_estimated_time() -> None:
    raw = dataclasses.replace(_raw(), estimated_time="30 min")

    with pytest.raises(InvalidEstimatedTime):
        validate_ai_recipe_output(raw)


def test_a_free_text_estimated_time_surfaces_as_an_invalid_output_failure() -> None:
    """E7: the per-slot mechanism `G-66` established, not a propagated raise —
    the same path an unknown unit or category already takes."""
    raw = dataclasses.replace(_raw(), estimated_time="media hora")

    outcome = validate_and_preview(raw)

    assert isinstance(outcome, GenerationFailure)
    assert outcome.reason is GenerationFailureReason.INVALID_OUTPUT
    assert outcome.message == AI_GENERATION_INVALID_OUTPUT


def test_an_out_of_range_estimated_time_surfaces_as_an_invalid_output_failure() -> None:
    """E8 on the AI side: 6001 minutes is as invalid as "media hora"."""
    raw = dataclasses.replace(_raw(), estimated_time=MAX_ESTIMATED_MINUTES + 1)

    outcome = validate_and_preview(raw)

    assert isinstance(outcome, GenerationFailure)
    assert outcome.reason is GenerationFailureReason.INVALID_OUTPUT


def test_an_integer_estimated_time_still_previews() -> None:
    raw = dataclasses.replace(_raw(), estimated_time=30)

    outcome = validate_and_preview(raw)

    assert isinstance(outcome, GenerationSuccess)
    assert outcome.preview.recipe.estimated_time == 30
