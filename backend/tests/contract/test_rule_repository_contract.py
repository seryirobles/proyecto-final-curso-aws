"""Contract suite for RuleRepository: one suite, run against every registered
implementation (R9)."""

from __future__ import annotations

import pytest
from planner_core.domain.calendar import MealSlot
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.rules import CategoryCountRule, PinRule, RuleSet
from support.fakes import FakeRuleRepository

IMPLEMENTATIONS = [FakeRuleRepository]


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_get_returns_an_empty_rule_set_before_any_save(
    repository_factory: type[FakeRuleRepository],
) -> None:
    assert repository_factory().get() == RuleSet()


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_save_then_get_round_trip(repository_factory: type[FakeRuleRepository]) -> None:
    repo = repository_factory()
    rule_set = RuleSet(
        category_counts=(CategoryCountRule(category=IngredientCategory.MEAT, count=2),),
        pins=(PinRule(day=1, slot=MealSlot.LUNCH, recipe_id="r1"),),
        disabled_days=(7,),
    )

    repo.save(rule_set)

    assert repo.get() == rule_set
