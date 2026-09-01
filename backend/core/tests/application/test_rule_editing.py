"""Tests for per-rule editing: whole-set satisfiability before the single-item
write, unsatisfiable never writes (R15, R16, R17, R29)."""

from __future__ import annotations

import pytest
from support.fakes import FakeRuleRepository

from planner_core.application import rule_editing
from planner_core.domain.calendar import MealSlot
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.rules import (
    CategoryCountRule,
    DisabledDay,
    PinRule,
    RuleSet,
    UnsatisfiableRuleSet,
)

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


def test_read_rules_returns_the_shared_set() -> None:
    repo = FakeRuleRepository()
    rule_editing.save_rule(PIN, rules=repo)
    assert rule_editing.read_rules(rules=repo) == RuleSet(pins=(PIN,))
