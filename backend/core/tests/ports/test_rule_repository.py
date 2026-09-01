"""Tests for the RuleRepository port and its in-memory fake (GQ3: per-rule
writes keyed by natural id, no whole-RuleSet blob write).

Named test_rule_repository.py, not test_rules.py: pytest's prepend import
mode collides on basename with the existing domain/test_rules.py, since
neither tests/ directory carries an __init__.py.
"""

from __future__ import annotations

from typing import get_type_hints

from support.fakes import FakeRuleRepository

from planner_core.domain.calendar import MealSlot
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.rules import CategoryCountRule, DisabledDay, PinRule, RuleSet, rule_id
from planner_core.ports.rules import RuleRepository

CAT = CategoryCountRule(category=IngredientCategory.MEAT, count=2)
PIN = PinRule(day=1, slot=MealSlot.LUNCH, recipe_id="r1")


def test_fake_rule_repository_satisfies_the_rule_repository_port() -> None:
    assert isinstance(FakeRuleRepository(), RuleRepository)


def test_get_returns_an_empty_rule_set_before_any_save() -> None:
    assert FakeRuleRepository().get() == RuleSet()


def test_save_rule_then_get_reconstructs_the_set() -> None:
    repo = FakeRuleRepository()
    repo.save_rule(CAT)
    repo.save_rule(PIN)
    repo.save_rule(DisabledDay(day=7))
    assert repo.get() == RuleSet(category_counts=(CAT,), pins=(PIN,), disabled_days=(7,))


def test_save_rule_replaces_by_natural_key() -> None:
    repo = FakeRuleRepository()
    repo.save_rule(CategoryCountRule(category=IngredientCategory.MEAT, count=2))
    repo.save_rule(CategoryCountRule(category=IngredientCategory.MEAT, count=3))
    assert repo.get() == RuleSet(
        category_counts=(CategoryCountRule(category=IngredientCategory.MEAT, count=3),)
    )


def test_delete_rule_drops_the_item_by_id() -> None:
    repo = FakeRuleRepository()
    repo.save_rule(PIN)
    repo.delete_rule(rule_id(PIN))
    assert repo.get() == RuleSet()


# --- change marker (FR-RT-01): R10, R11, R12 ---


def test_the_port_exposes_per_rule_writes_and_no_whole_set_write() -> None:
    """R12: save(RuleSet) is gone; the per-rule writes return the marker int."""
    assert "save" not in RuleRepository.__dict__
    assert "current_version" in RuleRepository.__dict__
    assert get_type_hints(RuleRepository.save_rule)["return"] is int
    assert get_type_hints(RuleRepository.delete_rule)["return"] is int


def test_current_version_is_zero_before_any_write() -> None:
    assert FakeRuleRepository().current_version() == 0


def test_each_mutation_advances_the_marker_and_returns_the_new_value() -> None:
    repo = FakeRuleRepository()
    first = repo.save_rule(CAT)
    second = repo.delete_rule("cat#meat")
    assert (first, second) == (1, 2)  # R10, R11
    assert repo.current_version() == second


def test_get_does_not_advance_the_marker() -> None:
    repo = FakeRuleRepository()
    repo.save_rule(CAT)
    repo.get()
    repo.current_version()
    assert repo.current_version() == 1
