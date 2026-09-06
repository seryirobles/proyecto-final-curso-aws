"""Tests for library CRUD and the pin cascade on delete (R18, R19, R29)."""

from __future__ import annotations

import dataclasses

import pytest
from support.fakes import FakeRecipeRepository, FakeRuleRepository

from planner_core.application import library_editing
from planner_core.domain.calendar import MealSlot
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Recipe
from planner_core.domain.rules import PinRule, PinRulesAffected
from planner_core.ports.recipes import LibraryRecipe


def _entry(rid: str = "r1", name: str = "Tortilla") -> LibraryRecipe:
    recipe = Recipe(
        name=name, ingredients=(), tools=(), procedure=(), category=IngredientCategory.EGGS
    )
    return LibraryRecipe(id=rid, recipe=recipe, author="u1")


def test_save_recipe_outcome_is_frozen() -> None:
    """docs/conventions.md: every new frozen dataclass gets this test."""
    outcome = library_editing.SaveRecipeOutcome(marker=1, duplicate_warning=False)
    with pytest.raises(dataclasses.FrozenInstanceError):
        outcome.__setattr__("marker", 2)


def test_delete_recipe_outcome_is_frozen() -> None:
    """docs/conventions.md: every new frozen dataclass gets this test."""
    outcome = library_editing.DeleteRecipeOutcome(marker=1, removed_pins=())
    with pytest.raises(dataclasses.FrozenInstanceError):
        outcome.__setattr__("marker", 2)


def test_library_view_is_frozen() -> None:
    """docs/conventions.md: every new frozen dataclass gets this test."""
    view = library_editing.LibraryView(entries=(), marker=1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        view.__setattr__("marker", 2)


def test_save_recipe_returns_marker_and_duplicate_warning() -> None:
    recipes = FakeRecipeRepository()

    first = library_editing.save_recipe(_entry("r1", "Tortilla"), recipes=recipes)
    second = library_editing.save_recipe(_entry("r2", "tortilla"), recipes=recipes)

    assert first.marker == 1 and first.duplicate_warning is False
    assert second.marker == 2 and second.duplicate_warning is True


def test_unconfirmed_delete_of_a_pinned_recipe_reports_pins_and_writes_nothing() -> None:
    recipes = FakeRecipeRepository()
    recipes.save(_entry("r1"))
    rules = FakeRuleRepository()
    pin = PinRule(day=7, slot=MealSlot.LUNCH, recipe_id="r1")
    rules.save_rule(pin)
    writes_before = (recipes.version, rules.writes)

    with pytest.raises(PinRulesAffected) as excinfo:
        library_editing.delete_recipe("r1", confirm_cascade=False, recipes=recipes, rules=rules)

    assert excinfo.value.pins == (pin,)
    assert (recipes.version, rules.writes) == writes_before
    assert recipes.get("r1") is not None


def test_confirmed_delete_removes_the_recipe_and_every_referencing_pin() -> None:
    recipes = FakeRecipeRepository()
    recipes.save(_entry("r1"))
    rules = FakeRuleRepository()
    pin_a = PinRule(day=7, slot=MealSlot.LUNCH, recipe_id="r1")
    pin_b = PinRule(day=6, slot=MealSlot.DINNER, recipe_id="r1")
    other = PinRule(day=5, slot=MealSlot.LUNCH, recipe_id="r2")
    for pin in (pin_a, pin_b, other):
        rules.save_rule(pin)

    outcome = library_editing.delete_recipe(
        "r1", confirm_cascade=True, recipes=recipes, rules=rules
    )

    assert recipes.get("r1") is None
    assert set(outcome.removed_pins) == {pin_a, pin_b}
    assert rules.get().pins == (other,)
    assert outcome.marker == recipes.version


def test_delete_of_an_unpinned_recipe_needs_no_confirmation() -> None:
    recipes = FakeRecipeRepository()
    recipes.save(_entry("r1"))
    rules = FakeRuleRepository()

    outcome = library_editing.delete_recipe(
        "r1", confirm_cascade=False, recipes=recipes, rules=rules
    )

    assert recipes.get("r1") is None
    assert outcome.removed_pins == ()


def test_list_library_reads_without_writing() -> None:
    recipes = FakeRecipeRepository()
    recipes.save(_entry("r1"))
    assert library_editing.list_library(recipes=recipes).entries == (_entry("r1"),)
    assert recipes.current_version() == 1
