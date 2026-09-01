"""GQ3 additions to domain/rules: DisabledDay value object, natural-key rule
ids, single-rule apply/remove, and the pin-cascade exception (feature 27)."""

from __future__ import annotations

import dataclasses

import pytest

from planner_core.domain.calendar import MealSlot
from planner_core.domain.errors import PlannerError
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.rules import (
    CategoryCountRule,
    DisabledDay,
    InvalidRuleId,
    InvalidWeekday,
    PinRule,
    PinRulesAffected,
    Rule,
    RuleSet,
    UnsatisfiableRuleSet,
    apply_rule,
    remove_rule_by_id,
    rule_id,
)

CAT = CategoryCountRule(category=IngredientCategory.MEAT, count=2)
PIN = PinRule(day=1, slot=MealSlot.LUNCH, recipe_id="r1")
DAY = DisabledDay(day=7)


def test_disabled_day_rejects_a_non_weekday() -> None:
    with pytest.raises(InvalidWeekday):
        DisabledDay(day=8)


def test_disabled_day_is_frozen() -> None:
    day = DisabledDay(day=3)
    with pytest.raises(dataclasses.FrozenInstanceError):
        day.__setattr__("day", 4)


def test_pin_rules_affected_carries_the_pins_and_is_a_planner_error() -> None:
    exc = PinRulesAffected((PIN,))
    assert isinstance(exc, PlannerError)
    assert exc.pins == (PIN,)


@pytest.mark.parametrize(
    ("rule", "expected"),
    [(CAT, "cat#meat"), (PIN, "pin#1#1"), (DAY, "day#7")],
)
def test_rule_id_is_the_deterministic_natural_key(rule: Rule, expected: str) -> None:
    assert rule_id(rule) == expected


def test_apply_rule_routes_each_kind_through_its_mutator() -> None:
    rs = apply_rule(RuleSet(), CAT)
    rs = apply_rule(rs, PIN)
    rs = apply_rule(rs, DAY)
    assert rs == RuleSet(category_counts=(CAT,), pins=(PIN,), disabled_days=(7,))


def test_apply_rule_raises_on_an_unsatisfiable_result_and_writes_nothing_first() -> None:
    disabled = RuleSet(disabled_days=(2, 3, 4, 5, 6))  # 4 slots left
    with pytest.raises(UnsatisfiableRuleSet):
        apply_rule(disabled, CategoryCountRule(category=IngredientCategory.MEAT, count=5))


def test_remove_rule_by_id_drops_exactly_the_named_rule() -> None:
    rs = RuleSet(category_counts=(CAT,), pins=(PIN,), disabled_days=(7,))
    assert remove_rule_by_id(rs, "pin#1#1") == RuleSet(category_counts=(CAT,), disabled_days=(7,))
    assert remove_rule_by_id(rs, "day#7") == RuleSet(category_counts=(CAT,), pins=(PIN,))
    assert remove_rule_by_id(rs, "cat#meat") == RuleSet(pins=(PIN,), disabled_days=(7,))


def test_remove_rule_by_id_is_a_no_op_for_an_absent_rule() -> None:
    rs = RuleSet(pins=(PIN,))
    assert remove_rule_by_id(rs, "day#3") == rs


def test_remove_rule_by_id_rejects_an_unknown_prefix() -> None:
    with pytest.raises(InvalidRuleId):
        remove_rule_by_id(RuleSet(), "weird#1")


@pytest.mark.parametrize(
    "rule_id_value",
    ["cat#notacategory", "pin#x#1", "pin#9#9", "day#abc"],
)
def test_remove_rule_by_id_rejects_a_known_prefix_with_a_malformed_body(rule_id_value: str) -> None:
    """A malformed body must raise the named domain exception, not a bare
    ValueError -> 500 (architecture.md section 4, invariant 12)."""
    with pytest.raises(InvalidRuleId):
        remove_rule_by_id(RuleSet(), rule_id_value)
