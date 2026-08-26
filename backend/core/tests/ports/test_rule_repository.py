"""Tests for the RuleRepository port and its in-memory fake.

Named test_rule_repository.py, not test_rules.py: pytest's prepend import
mode collides on basename with the existing domain/test_rules.py, since
neither tests/ directory carries an __init__.py.
"""

from __future__ import annotations

from support.fakes import FakeRuleRepository

from planner_core.domain.calendar import MealSlot
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.rules import CategoryCountRule, PinRule, RuleSet
from planner_core.ports.rules import RuleRepository


def test_fake_rule_repository_satisfies_the_rule_repository_port() -> None:
    assert isinstance(FakeRuleRepository(), RuleRepository)


def test_get_returns_an_empty_rule_set_before_any_save() -> None:
    assert FakeRuleRepository().get() == RuleSet()


def test_save_then_get_round_trip() -> None:
    repo = FakeRuleRepository()
    rule_set = RuleSet(
        category_counts=(CategoryCountRule(category=IngredientCategory.MEAT, count=2),),
        pins=(PinRule(day=1, slot=MealSlot.LUNCH, recipe_id="r1"),),
        disabled_days=(7,),
    )

    repo.save(rule_set)

    assert repo.get() == rule_set
