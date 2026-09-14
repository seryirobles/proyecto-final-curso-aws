"""Tests for per-rule editing: whole-set satisfiability before the single-item
write, unsatisfiable never writes (R15, R16, R17, R29)."""

from __future__ import annotations

import dataclasses

import pytest
from support.fakes import FakeRecipeRepository, FakeRuleRepository

from planner_core.application import rule_editing
from planner_core.domain.calendar import MealSlot
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Recipe
from planner_core.domain.rules import (
    CategoryCountRule,
    DisabledDay,
    PinRule,
    RuleSet,
    UnsatisfiableRuleSet,
)
from planner_core.messages import RECIPE_NOT_FOUND
from planner_core.ports.recipes import LibraryRecipe

PIN = PinRule(day=1, slot=MealSlot.LUNCH, recipe_id="r1")


def test_save_rule_writes_and_returns_the_marker() -> None:
    repo = FakeRuleRepository()
    marker = rule_editing.save_rule(PIN, rules=repo)
    assert marker == 1
    assert repo.get() == RuleSet(pins=(PIN,))


def test_save_rule_validates_the_whole_resulting_set() -> None:
    """R15 — a category count that fits alone but not with the disabled days."""
    repo = FakeRuleRepository()
    for day in (2, 3, 4, 5, 6):
        rule_editing.save_rule(DisabledDay(day=day), rules=repo)
    writes_before = repo.writes

    with pytest.raises(UnsatisfiableRuleSet) as excinfo:
        rule_editing.save_rule(
            CategoryCountRule(category=IngredientCategory.MEAT, count=5), rules=repo
        )

    assert repo.writes == writes_before  # R17 — nothing written
    # R16 — the payload names the conflicting existing rules, not the attempt.
    assert set(excinfo.value.conflicting) == {DisabledDay(day=day) for day in (2, 3, 4, 5, 6)}


def test_delete_rule_writes_and_returns_the_marker() -> None:
    repo = FakeRuleRepository()
    rule_editing.save_rule(PIN, rules=repo)
    marker = rule_editing.delete_rule("pin#1#1", rules=repo)
    assert marker == 2
    assert repo.get() == RuleSet()


def test_rules_view_is_frozen() -> None:
    """docs/conventions.md: every new frozen dataclass gets this test."""
    view = rule_editing.RulesView(rule_set=RuleSet(), marker=1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        view.__setattr__("marker", 2)


def test_read_rules_returns_the_shared_set() -> None:
    repo = FakeRuleRepository()
    rule_editing.save_rule(PIN, rules=repo)
    view = rule_editing.read_rules(rules=repo, recipes=FakeRecipeRepository())
    assert view.rule_set == RuleSet(pins=(PIN,))


def test_read_rules_resolves_a_pin_recipe_name_from_the_library() -> None:
    """R34 (AP22): recipeName is resolved at read time, never stored on the
    pin itself (docs/data_model.md section 6)."""
    rules_repo = FakeRuleRepository()
    rule_editing.save_rule(PIN, rules=rules_repo)
    recipes_repo = FakeRecipeRepository()
    recipe = Recipe(
        name="Lentejas", ingredients=(), tools=(), procedure=(), category=IngredientCategory.LEGUME
    )
    recipes_repo.save(LibraryRecipe(id="r1", recipe=recipe, author="u1"))

    view = rule_editing.read_rules(rules=rules_repo, recipes=recipes_repo)

    assert view.pin_recipe_names["r1"] == "Lentejas"


def test_read_rules_falls_back_when_a_pinned_recipe_is_missing() -> None:
    """Should not happen (G-20 cascade-deletes the pin), but a repository
    read is never trusted to be exhaustive without a fallback."""
    rules_repo = FakeRuleRepository()
    rule_editing.save_rule(PIN, rules=rules_repo)

    view = rule_editing.read_rules(rules=rules_repo, recipes=FakeRecipeRepository())

    assert view.pin_recipe_names["r1"] == RECIPE_NOT_FOUND
