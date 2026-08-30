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


# --- change marker (FR-RT-01): R2, R4, R5, R8, R11 ---


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_save_advances_the_marker_and_returns_the_new_value(
    repository_factory: type[FakeRuleRepository],
) -> None:
    repo = repository_factory()

    assert repo.save(RuleSet()) == 1  # R4, R5
    assert repo.current_version() == 1


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_reads_leave_the_marker_unchanged(
    repository_factory: type[FakeRuleRepository],
) -> None:
    repo = repository_factory()
    repo.save(RuleSet())

    repo.get()
    repo.current_version()

    assert repo.current_version() == 1  # R2


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_two_successive_writes_both_apply_and_advance_the_marker_twice(
    repository_factory: type[FakeRuleRepository],
) -> None:
    repo = repository_factory()

    first = repo.save(RuleSet())
    second = repo.save(RuleSet())  # no raise: last-write-wins (R8)

    assert (first, second) == (1, 2)  # R11
