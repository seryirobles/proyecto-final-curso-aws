"""Tests for the Recipe content shape and the snapshot value object (R1-R3, R9-R14)."""

from __future__ import annotations

import dataclasses
import typing

import pytest

from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Ingredient, MealSnapshot, Recipe, snapshot
from planner_core.domain.units import Unit, UnknownUnit, parse_unit


def _make_recipe() -> Recipe:
    return Recipe(
        name="Lentejas con chorizo",
        ingredients=(
            Ingredient(name="lentejas", quantity=500, unit=parse_unit("g")),
            Ingredient(name="chorizo", quantity=200, unit=parse_unit("g")),
        ),
        tools=("olla",),
        procedure=("Sofreir el chorizo.", "Anadir las lentejas y cocer."),
        category=IngredientCategory.LEGUME,
    )


def test_recipe_is_frozen() -> None:
    """R1: mutating means constructing a new instance (docs/conventions.md)."""
    recipe = _make_recipe()

    with pytest.raises(dataclasses.FrozenInstanceError):
        recipe.__setattr__("name", "Otro")


def test_recipe_fields_are_exactly_the_fixed_shape() -> None:
    """R2: no cuisine, difficulty or kcal field (G-68, G-36)."""
    field_names = {field.name for field in dataclasses.fields(Recipe)}
    assert field_names == {"name", "ingredients", "tools", "procedure", "category"}


def test_ingredient_fields_are_exactly_the_fixed_shape() -> None:
    """R3: an ingredient is a name, a quantity and a unit, nothing else."""
    field_names = {field.name for field in dataclasses.fields(Ingredient)}
    assert field_names == {"name", "quantity", "unit"}


def test_ingredient_unit_is_the_shared_unit_enum() -> None:
    """R3: the unit field is declared as feature 3's shared Unit, never a raw string.

    get_type_hints checks the declaration itself, not a value: parse_unit
    always returns a Unit regardless of the field's annotation (F2).
    """
    assert typing.get_type_hints(Ingredient)["unit"] is Unit

    ingredient = Ingredient(name="arroz", quantity=100, unit=parse_unit("g"))
    assert isinstance(ingredient.unit, Unit)
    assert ingredient.unit is Unit.GRAM


def test_an_unlisted_unit_can_never_reach_an_ingredient() -> None:
    """R9: the only path into Ingredient.unit rejects an out-of-list value first."""
    with pytest.raises(UnknownUnit):
        parse_unit("kg")


def test_meal_snapshot_is_a_distinct_frozen_type() -> None:
    """R10: a distinct type from Recipe, not a subclass, not an alias."""
    # type[object]: mypy --strict rejects `MealSnapshot is not Recipe` outright
    # as a non-overlapping identity check between two known-distinct literals.
    meal_snapshot_type: type[object] = MealSnapshot
    recipe_type: type[object] = Recipe
    assert meal_snapshot_type is not recipe_type

    field_names = {field.name for field in dataclasses.fields(MealSnapshot)}
    assert field_names == {field.name for field in dataclasses.fields(Recipe)}

    taken = snapshot(_make_recipe())
    with pytest.raises(dataclasses.FrozenInstanceError):
        taken.__setattr__("name", "Otro")


def test_snapshot_copies_the_recipes_content() -> None:
    """R11, R14: ingredients, tools, procedure and category equal the source recipe's."""
    recipe = _make_recipe()
    taken = snapshot(recipe)

    assert taken.name == recipe.name
    assert taken.ingredients == recipe.ingredients
    assert taken.tools == recipe.tools
    assert taken.procedure == recipe.procedure
    assert taken.category == recipe.category


def test_meal_snapshot_holds_no_reference_to_the_recipe() -> None:
    """R12: no field typed Recipe, and no id/recipe/source field."""
    field_names = {field.name for field in dataclasses.fields(MealSnapshot)}
    assert "id" not in field_names
    assert "recipe" not in field_names
    assert "source" not in field_names

    for field in dataclasses.fields(MealSnapshot):
        assert field.type != "Recipe"


def test_editing_or_deleting_the_library_recipe_leaves_an_existing_snapshot_unchanged() -> None:
    """R13: the docs/verification.md Level 4 scenario for G-05."""
    original = _make_recipe()
    library: dict[str, Recipe] = {"r1": original}
    taken = snapshot(library["r1"])

    library["r1"] = Recipe(
        name="Pollo al horno",
        ingredients=(Ingredient(name="pollo", quantity=1, unit=parse_unit("unit")),),
        tools=("horno",),
        procedure=("Hornear el pollo.",),
        category=IngredientCategory.MEAT,
    )
    assert taken.name == original.name
    assert taken.category == original.category

    del library["r1"]
    assert taken.name == original.name
    assert taken.ingredients == original.ingredients
    assert taken.tools == original.tools
    assert taken.procedure == original.procedure
    assert taken.category == original.category
