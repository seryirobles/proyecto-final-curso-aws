"""Tests for the RuleRepository port and its in-memory fake.

Named test_rule_repository.py, not test_rules.py: pytest's prepend import
mode collides on basename with the existing domain/test_rules.py, since
neither tests/ directory carries an __init__.py.
"""

from __future__ import annotations

from typing import get_type_hints

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


# --- change marker (FR-RT-01): R1, R2, R3, R4, R5 ---


def test_the_rule_repository_protocol_pins_the_marker_surface() -> None:
    """R1: current_version and the int-returning save are on the Protocol itself,
    not only the fake — deleting either from ports/rules.py fails here."""
    assert "current_version" in RuleRepository.__dict__
    assert get_type_hints(RuleRepository.save)["return"] is int


def test_current_version_is_zero_before_any_write() -> None:
    assert FakeRuleRepository().current_version() == 0  # R3


def test_save_advances_the_marker_and_returns_the_new_value() -> None:
    repo = FakeRuleRepository()

    first = repo.save(RuleSet())
    second = repo.save(RuleSet())

    assert (first, second) == (1, 2)  # R4, R5
    assert repo.current_version() == second  # R4


def test_get_does_not_advance_the_marker() -> None:
    repo = FakeRuleRepository()
    repo.save(RuleSet())

    repo.get()
    repo.current_version()

    assert repo.current_version() == 1  # R2
