"""Tests for AI output validation and the preview lifecycle.

R1-R21 below are specs/ai_output_validation/requirements.md (feature 12).
Tests naming R10-R15 explicitly are specs/recipe_metadata_fields/requirements.md
(feature 25) instead - the two specs' numbering collides, disambiguated by name.
"""

from __future__ import annotations

import dataclasses
from datetime import date
from typing import get_type_hints

import pytest

from planner_core.domain.ai_output import (
    GenerationFailure,
    GenerationFailureReason,
    GenerationSuccess,
    RawIngredient,
    RawRecipeOutput,
    RecipePreview,
    SlotGenerationResult,
    accept_preview,
    build_generation_failure,
    discard_preview,
    new_preview,
    validate_ai_recipe_output,
    validate_and_preview,
)
from planner_core.domain.calendar import MealSlot, SlotRef
from planner_core.domain.ingredient_category import IngredientCategory, UnknownIngredientCategory
from planner_core.domain.units import Unit, UnknownUnit
from planner_core.messages import (
    AI_GENERATION_INSUFFICIENT_LIBRARY_RECIPES,
    AI_GENERATION_INVALID_OUTPUT,
    AI_GENERATION_UNAVAILABLE,
)


def _make_raw() -> RawRecipeOutput:
    return RawRecipeOutput(
        name="Lentejas con chorizo",
        ingredients=(
            RawIngredient(name="lentejas", quantity=500, unit="g"),
            RawIngredient(name="agua", quantity=750, unit="ml"),
        ),
        tools=("olla",),
        procedure=("Sofreir el chorizo.", "Anadir las lentejas y cocer."),
        category="legume",
    )


# --- R1, R2: field shape and frozen-ness -----------------------------------


def test_raw_ingredient_fields_are_exactly_the_fixed_shape() -> None:
    """R1."""
    field_names = {field.name for field in dataclasses.fields(RawIngredient)}
    assert field_names == {"name", "quantity", "unit"}


def test_raw_ingredient_is_frozen() -> None:
    """R1."""
    ingredient = RawIngredient(name="tomate", quantity=2, unit="unit")

    with pytest.raises(dataclasses.FrozenInstanceError):
        ingredient.__setattr__("quantity", 3)


def test_raw_recipe_output_fields_are_exactly_the_fixed_shape() -> None:
    """R2."""
    field_names = {field.name for field in dataclasses.fields(RawRecipeOutput)}
    assert field_names == {
        "name",
        "ingredients",
        "tools",
        "procedure",
        "category",
        "servings",
        "estimated_time",
    }


def test_raw_recipe_output_is_frozen() -> None:
    """R2."""
    raw = _make_raw()

    with pytest.raises(dataclasses.FrozenInstanceError):
        raw.__setattr__("name", "Otra receta")


# --- R3-R9: validate_ai_recipe_output ---------------------------------------


def test_validate_ai_recipe_output_resolves_units_in_order() -> None:
    """R3: ingredients carry parse_unit of each RawIngredient's unit, order preserved."""
    recipe = validate_ai_recipe_output(_make_raw())

    assert recipe.ingredients[0].unit == Unit.GRAM
    assert recipe.ingredients[1].unit == Unit.MILLILITRE
    assert recipe.ingredients[0].name == "lentejas"
    assert recipe.ingredients[1].name == "agua"


def test_validate_ai_recipe_output_raises_unknown_unit_for_unresolvable_unit() -> None:
    """R4."""
    raw = dataclasses.replace(
        _make_raw(),
        ingredients=(RawIngredient(name="tomate", quantity=1, unit="kg"),),
    )

    with pytest.raises(UnknownUnit):
        validate_ai_recipe_output(raw)


def test_validate_ai_recipe_output_resolves_category() -> None:
    """R5."""
    recipe = validate_ai_recipe_output(_make_raw())

    assert recipe.category == IngredientCategory.LEGUME


def test_validate_ai_recipe_output_raises_unknown_ingredient_category_for_bad_category() -> None:
    """R6."""
    raw = dataclasses.replace(_make_raw(), category="dessert")

    with pytest.raises(UnknownIngredientCategory):
        validate_ai_recipe_output(raw)


def test_validate_ai_recipe_output_carries_name_tools_procedure_unchanged() -> None:
    """R7, R8, R9."""
    raw = _make_raw()
    recipe = validate_ai_recipe_output(raw)

    assert recipe.name == raw.name
    assert recipe.tools == raw.tools
    assert recipe.procedure == raw.procedure


# --- recipe_metadata_fields R10-R15: servings and estimated_time -----------


def test_raw_recipe_output_servings_and_estimated_time_default_to_none() -> None:
    """recipe_metadata_fields R10, R11."""
    raw = _make_raw()

    assert raw.servings is None
    assert raw.estimated_time is None


def test_validate_ai_recipe_output_does_not_raise_when_both_fields_are_absent() -> None:
    """recipe_metadata_fields R12, R13: absence is not a failure."""
    recipe = validate_ai_recipe_output(_make_raw())

    assert recipe.servings is None
    assert recipe.estimated_time is None


def test_validate_ai_recipe_output_copies_servings_and_estimated_time_when_present() -> None:
    """recipe_metadata_fields R14, R15."""
    raw = dataclasses.replace(_make_raw(), servings=4, estimated_time="30 min")

    recipe = validate_ai_recipe_output(raw)

    assert recipe.servings == raw.servings
    assert recipe.estimated_time == raw.estimated_time


def test_validate_ai_recipe_output_copies_one_field_present_one_absent() -> None:
    """recipe_metadata_fields R12-R15: each field's presence is independent of the other's."""
    raw = dataclasses.replace(_make_raw(), servings=2, estimated_time=None)

    recipe = validate_ai_recipe_output(raw)

    assert recipe.servings == 2
    assert recipe.estimated_time is None


# --- R10-R13: preview lifecycle ---------------------------------------------


def test_recipe_preview_fields_are_exactly_recipe() -> None:
    """R10: no per-user quota, count or usage field (G-70)."""
    field_names = {field.name for field in dataclasses.fields(RecipePreview)}
    assert field_names == {"recipe"}


def test_recipe_preview_is_frozen() -> None:
    """R10."""
    recipe = validate_ai_recipe_output(_make_raw())
    preview = new_preview(recipe)

    with pytest.raises(dataclasses.FrozenInstanceError):
        preview.__setattr__("recipe", recipe)


def test_new_preview_carries_the_recipe() -> None:
    """R11."""
    recipe = validate_ai_recipe_output(_make_raw())

    assert new_preview(recipe).recipe == recipe


def test_accept_preview_returns_the_recipe() -> None:
    """R12."""
    recipe = validate_ai_recipe_output(_make_raw())
    preview = new_preview(recipe)

    assert accept_preview(preview) == recipe


def test_discard_preview_returns_none() -> None:
    """R13: mypy strict already forbids a `-> None` function from returning
    anything else, so the type hint plus a clean call proves the claim."""
    preview = new_preview(validate_ai_recipe_output(_make_raw()))
    discard_preview(preview)

    assert get_type_hints(discard_preview)["return"] is type(None)


# --- R14-R17: failure vocabulary and messages -------------------------------


def test_generation_failure_reason_has_exactly_the_three_members() -> None:
    """R14."""
    assert {member.name for member in GenerationFailureReason} == {
        "INVALID_OUTPUT",
        "INSUFFICIENT_LIBRARY_RECIPES",
        "GENERATION_UNAVAILABLE",
    }


def test_generation_failure_fields_are_exactly_the_fixed_shape() -> None:
    """R15."""
    field_names = {field.name for field in dataclasses.fields(GenerationFailure)}
    assert field_names == {"reason", "message"}


def test_generation_failure_is_frozen() -> None:
    """R15."""
    failure = build_generation_failure(GenerationFailureReason.INVALID_OUTPUT)

    with pytest.raises(dataclasses.FrozenInstanceError):
        failure.__setattr__("message", "otro mensaje")


def test_generation_success_fields_are_exactly_the_fixed_shape() -> None:
    """R16."""
    field_names = {field.name for field in dataclasses.fields(GenerationSuccess)}
    assert field_names == {"preview"}


def test_generation_success_is_frozen() -> None:
    """R16."""
    preview = new_preview(validate_ai_recipe_output(_make_raw()))
    success = GenerationSuccess(preview=preview)

    with pytest.raises(dataclasses.FrozenInstanceError):
        success.__setattr__("preview", preview)


@pytest.mark.parametrize(
    ("reason", "message"),
    [
        (GenerationFailureReason.INVALID_OUTPUT, AI_GENERATION_INVALID_OUTPUT),
        (
            GenerationFailureReason.INSUFFICIENT_LIBRARY_RECIPES,
            AI_GENERATION_INSUFFICIENT_LIBRARY_RECIPES,
        ),
        (GenerationFailureReason.GENERATION_UNAVAILABLE, AI_GENERATION_UNAVAILABLE),
    ],
)
def test_build_generation_failure_maps_reason_to_its_message(
    reason: GenerationFailureReason, message: str
) -> None:
    """R17: FR-UX-03, message equals the matching messages.py constant."""
    failure = build_generation_failure(reason)

    assert failure.reason == reason
    assert failure.message == message


# --- R18-R19: validate_and_preview ------------------------------------------


def test_validate_and_preview_success_wraps_a_new_preview() -> None:
    """R18."""
    raw = _make_raw()

    result = validate_and_preview(raw)

    assert isinstance(result, GenerationSuccess)
    assert result.preview.recipe == validate_ai_recipe_output(raw)


def test_validate_and_preview_returns_invalid_output_failure_for_unknown_unit() -> None:
    """R19."""
    raw = dataclasses.replace(
        _make_raw(),
        ingredients=(RawIngredient(name="tomate", quantity=1, unit="kg"),),
    )

    result = validate_and_preview(raw)

    assert result == build_generation_failure(GenerationFailureReason.INVALID_OUTPUT)


def test_validate_and_preview_returns_invalid_output_failure_for_unknown_category() -> None:
    """R19."""
    raw = dataclasses.replace(_make_raw(), category="dessert")

    result = validate_and_preview(raw)

    assert result == build_generation_failure(GenerationFailureReason.INVALID_OUTPUT)


# --- R20-R21: SlotGenerationResult -------------------------------------------


def test_slot_generation_result_fields_are_exactly_the_fixed_shape() -> None:
    """R20."""
    field_names = {field.name for field in dataclasses.fields(SlotGenerationResult)}
    assert field_names == {"slot", "outcome"}


def test_slot_generation_result_is_frozen() -> None:
    """R20, R21: unwritable so no entry's outcome can be exchanged after the
    fact — the structural precondition R21's independence claim relies on."""
    result = SlotGenerationResult(
        slot=SlotRef(day=date(2026, 8, 24), slot=MealSlot.LUNCH),
        outcome=build_generation_failure(GenerationFailureReason.INVALID_OUTPUT),
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        result.__setattr__("outcome", validate_and_preview(_make_raw()))


def test_slot_generation_results_preserve_each_entrys_own_outcome_independently() -> None:
    """R21: FR-AI-09, one slot's failure does not affect another slot's success.

    entry 0 and entry 2 use distinct success outcomes (different raw recipe
    names) so an accidental exchange between them is actually detectable by
    equality, not just by type.
    """
    slot_a = SlotRef(day=date(2026, 8, 24), slot=MealSlot.LUNCH)
    slot_b = SlotRef(day=date(2026, 8, 24), slot=MealSlot.DINNER)
    slot_c = SlotRef(day=date(2026, 8, 25), slot=MealSlot.LUNCH)

    success_outcome_a = validate_and_preview(_make_raw())
    success_outcome_c = validate_and_preview(dataclasses.replace(_make_raw(), name="Tortilla"))
    failure_outcome = build_generation_failure(GenerationFailureReason.INSUFFICIENT_LIBRARY_RECIPES)

    results = (
        SlotGenerationResult(slot=slot_a, outcome=success_outcome_a),
        SlotGenerationResult(slot=slot_b, outcome=failure_outcome),
        SlotGenerationResult(slot=slot_c, outcome=success_outcome_c),
    )

    assert results[0].slot == slot_a
    assert results[0].outcome == success_outcome_a
    assert results[1].slot == slot_b
    assert results[1].outcome == failure_outcome
    assert results[2].slot == slot_c
    assert results[2].outcome == success_outcome_c
