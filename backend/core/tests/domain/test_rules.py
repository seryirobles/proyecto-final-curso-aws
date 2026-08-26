"""Tests for the shared rule set, its satisfiability gate and per-run override (R1-R22)."""

from __future__ import annotations

import dataclasses
import inspect

import pytest

import planner_core.domain.rules as rules_module
from planner_core.domain.calendar import MealSlot
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.rules import (
    CategoryCountRule,
    InvalidWeekday,
    PinRule,
    RuleSet,
    UnsatisfiableRuleSet,
    apply_override,
    available_days_for_pin,
    available_days_to_disable,
    disable_day,
    enable_day,
    max_selectable_count,
    remove_category_count,
    remove_pin,
    remove_pins_referencing,
    set_category_count,
    set_pin,
)


def test_rule_set_declares_exactly_the_three_fields() -> None:
    """R1: category_counts, pins, disabled_days -- no other field."""
    field_names = {f.name for f in dataclasses.fields(RuleSet)}
    assert field_names == {"category_counts", "pins", "disabled_days"}


def test_rule_set_is_frozen() -> None:
    """R1: mutating means constructing a new instance (docs/conventions.md)."""
    rule_set = RuleSet()

    with pytest.raises(dataclasses.FrozenInstanceError):
        rule_set.__setattr__("disabled_days", (1,))


def test_no_rules_function_takes_a_week_identity_parameter() -> None:
    """R2: no IsoWeek, SlotRef or date parameter anywhere in this module (design.md section 1)."""
    banned_names = {"IsoWeek", "SlotRef", "date"}
    callables_to_check = [RuleSet.__init__]
    for name in dir(rules_module):
        obj = getattr(rules_module, name)
        if inspect.isfunction(obj) and obj.__module__ == rules_module.__name__:
            callables_to_check.append(obj)

    for target in callables_to_check:
        for parameter in inspect.signature(target).parameters.values():
            annotation = parameter.annotation
            assert not isinstance(annotation, str) or all(
                banned not in annotation for banned in banned_names
            )
            assert annotation not in banned_names


def test_category_count_rule_fields_are_exactly_the_fixed_shape() -> None:
    """R3."""
    field_names = {f.name for f in dataclasses.fields(CategoryCountRule)}
    assert field_names == {"category", "count"}


def test_category_count_rule_is_frozen() -> None:
    """R3: mutating means constructing a new instance (docs/conventions.md)."""
    rule = CategoryCountRule(category=IngredientCategory.MEAT, count=2)

    with pytest.raises(dataclasses.FrozenInstanceError):
        rule.__setattr__("count", 3)


def test_pin_rule_fields_are_exactly_the_fixed_shape() -> None:
    """R4."""
    field_names = {f.name for f in dataclasses.fields(PinRule)}
    assert field_names == {"day", "slot", "recipe_id"}


def test_pin_rule_is_frozen() -> None:
    """R4: mutating means constructing a new instance (docs/conventions.md)."""
    pin = PinRule(day=1, slot=MealSlot.LUNCH, recipe_id="r1")

    with pytest.raises(dataclasses.FrozenInstanceError):
        pin.__setattr__("recipe_id", "r2")


def test_rule_set_rejects_an_out_of_range_disabled_day() -> None:
    """R5."""
    with pytest.raises(InvalidWeekday):
        RuleSet(disabled_days=(8,))
    with pytest.raises(InvalidWeekday):
        RuleSet(disabled_days=(0,))


def test_rule_set_rejects_an_out_of_range_pin_day() -> None:
    """R5."""
    with pytest.raises(InvalidWeekday):
        RuleSet(pins=(PinRule(day=9, slot=MealSlot.LUNCH, recipe_id="r1"),))


def test_rule_set_rejects_category_totals_exceeding_available_slots() -> None:
    """R6: 14 available slots, 15 required."""
    with pytest.raises(UnsatisfiableRuleSet):
        RuleSet(
            category_counts=(
                CategoryCountRule(category=IngredientCategory.MEAT, count=8),
                CategoryCountRule(category=IngredientCategory.FISH, count=7),
            ),
            disabled_days=(),
        )


def test_disabling_a_day_can_make_a_previously_valid_total_invalid() -> None:
    """R6: 13 required fits 14 available; disabling a day drops available to 12 (design.md 5)."""
    rule_set = RuleSet(
        category_counts=(CategoryCountRule(category=IngredientCategory.MEAT, count=13),),
        disabled_days=(),
    )

    with pytest.raises(UnsatisfiableRuleSet):
        disable_day(rule_set, 1)


def test_rule_set_rejects_a_pin_on_a_disabled_day() -> None:
    """R7."""
    with pytest.raises(UnsatisfiableRuleSet):
        RuleSet(
            pins=(PinRule(day=3, slot=MealSlot.DINNER, recipe_id="r1"),),
            disabled_days=(3,),
        )


def test_set_category_count_replaces_the_existing_rule_for_that_category() -> None:
    """R8."""
    rule_set = RuleSet(
        category_counts=(
            CategoryCountRule(category=IngredientCategory.MEAT, count=2),
            CategoryCountRule(category=IngredientCategory.FISH, count=1),
        )
    )

    result = set_category_count(rule_set, IngredientCategory.MEAT, 4)

    assert result.category_counts == (
        CategoryCountRule(category=IngredientCategory.FISH, count=1),
        CategoryCountRule(category=IngredientCategory.MEAT, count=4),
    )


def test_set_category_count_adds_a_new_rule_when_none_existed() -> None:
    """R8."""
    result = set_category_count(RuleSet(), IngredientCategory.FISH, 3)

    assert result.category_counts == (CategoryCountRule(category=IngredientCategory.FISH, count=3),)


def test_remove_category_count_removes_the_matching_rule() -> None:
    """R9."""
    rule_set = RuleSet(
        category_counts=(
            CategoryCountRule(category=IngredientCategory.MEAT, count=2),
            CategoryCountRule(category=IngredientCategory.FISH, count=1),
        )
    )

    result = remove_category_count(rule_set, IngredientCategory.MEAT)

    assert result.category_counts == (CategoryCountRule(category=IngredientCategory.FISH, count=1),)


def test_remove_category_count_is_a_no_op_when_absent() -> None:
    """R9: idempotent no-op, not an exception (design.md section 8, alt D)."""
    fish_rule = CategoryCountRule(category=IngredientCategory.FISH, count=1)
    rule_set = RuleSet(category_counts=(fish_rule,))

    result = remove_category_count(rule_set, IngredientCategory.MEAT)

    assert result == rule_set


def test_set_pin_replaces_the_existing_pin_for_that_slot() -> None:
    """R10."""
    rule_set = RuleSet(pins=(PinRule(day=2, slot=MealSlot.LUNCH, recipe_id="r1"),))

    result = set_pin(rule_set, 2, MealSlot.LUNCH, "r2")

    assert result.pins == (PinRule(day=2, slot=MealSlot.LUNCH, recipe_id="r2"),)


def test_remove_pin_removes_the_matching_pin() -> None:
    """R11."""
    rule_set = RuleSet(
        pins=(
            PinRule(day=2, slot=MealSlot.LUNCH, recipe_id="r1"),
            PinRule(day=3, slot=MealSlot.DINNER, recipe_id="r2"),
        )
    )

    result = remove_pin(rule_set, 2, MealSlot.LUNCH)

    assert result.pins == (PinRule(day=3, slot=MealSlot.DINNER, recipe_id="r2"),)


def test_remove_pin_is_a_no_op_when_absent() -> None:
    """R11: idempotent no-op (design.md section 8, alt D)."""
    rule_set = RuleSet(pins=(PinRule(day=3, slot=MealSlot.DINNER, recipe_id="r2"),))

    result = remove_pin(rule_set, 2, MealSlot.LUNCH)

    assert result == rule_set


def test_disable_day_adds_the_day() -> None:
    """R12."""
    result = disable_day(RuleSet(), 5)

    assert result.disabled_days == (5,)


def test_disable_day_is_idempotent() -> None:
    """R12."""
    once = disable_day(RuleSet(), 5)
    twice = disable_day(once, 5)

    assert twice.disabled_days == (5,)


def test_enable_day_removes_the_day() -> None:
    """R13."""
    result = enable_day(RuleSet(disabled_days=(5,)), 5)

    assert result.disabled_days == ()


def test_enable_day_is_a_no_op_when_absent() -> None:
    """R13: idempotent no-op (design.md section 8, alt D)."""
    rule_set = RuleSet(disabled_days=(3,))

    result = enable_day(rule_set, 5)

    assert result == rule_set


def test_max_selectable_count_subtracts_other_categories_and_disabled_days() -> None:
    """R14: 14 - 2 disabled slots = 12 available; 12 - 2 (FISH) = 10; MEAT's own count excluded."""
    rule_set = RuleSet(
        category_counts=(
            CategoryCountRule(category=IngredientCategory.MEAT, count=3),
            CategoryCountRule(category=IngredientCategory.FISH, count=2),
        ),
        disabled_days=(1,),
    )

    assert max_selectable_count(rule_set, IngredientCategory.MEAT) == 10


def test_max_selectable_count_floors_at_zero() -> None:
    """R14: never negative even when other categories already exceed the budget."""
    fish_rule = CategoryCountRule(category=IngredientCategory.FISH, count=14)
    rule_set = RuleSet(category_counts=(fish_rule,))

    assert max_selectable_count(rule_set, IngredientCategory.MEAT) == 0


def test_available_days_for_pin_excludes_disabled_days() -> None:
    """R15."""
    rule_set = RuleSet(disabled_days=(1, 7))

    assert available_days_for_pin(rule_set) == (2, 3, 4, 5, 6)


def test_available_days_to_disable_excludes_disabled_and_pinned_days() -> None:
    """R16."""
    rule_set = RuleSet(
        disabled_days=(1,),
        pins=(PinRule(day=3, slot=MealSlot.LUNCH, recipe_id="r1"),),
    )

    assert available_days_to_disable(rule_set) == (2, 4, 5, 6, 7)


def test_remove_pins_referencing_removes_every_matching_pin() -> None:
    """R17."""
    other_pin = PinRule(day=4, slot=MealSlot.DINNER, recipe_id="recipe-b")
    rule_set = RuleSet(
        pins=(
            PinRule(day=1, slot=MealSlot.LUNCH, recipe_id="recipe-a"),
            PinRule(day=2, slot=MealSlot.DINNER, recipe_id="recipe-a"),
            other_pin,
        )
    )

    result = remove_pins_referencing(rule_set, "recipe-a")

    assert result.rule_set.pins == (other_pin,)


def test_remove_pins_referencing_reports_exactly_what_it_removed() -> None:
    """R18."""
    removed_a = PinRule(day=1, slot=MealSlot.LUNCH, recipe_id="recipe-a")
    removed_b = PinRule(day=2, slot=MealSlot.DINNER, recipe_id="recipe-a")
    rule_set = RuleSet(
        pins=(removed_a, removed_b, PinRule(day=4, slot=MealSlot.DINNER, recipe_id="recipe-b"))
    )

    result = remove_pins_referencing(rule_set, "recipe-a")

    assert result.removed_pins == (removed_a, removed_b)


def test_remove_pins_referencing_is_a_no_op_when_nothing_matches() -> None:
    """R17, R18: negative case."""
    rule_set = RuleSet(pins=(PinRule(day=4, slot=MealSlot.DINNER, recipe_id="recipe-b"),))

    result = remove_pins_referencing(rule_set, "recipe-a")

    assert result.rule_set == rule_set
    assert result.removed_pins == ()


def test_apply_override_uses_the_override_value_when_given() -> None:
    """R19."""
    meat_rule = CategoryCountRule(category=IngredientCategory.MEAT, count=2)
    shared = RuleSet(category_counts=(meat_rule,))
    override_counts = (CategoryCountRule(category=IngredientCategory.FISH, count=1),)

    result = apply_override(shared, category_counts=override_counts)

    assert result.category_counts == override_counts
    assert result.pins == shared.pins
    assert result.disabled_days == shared.disabled_days


def test_apply_override_uses_the_pins_override_when_given() -> None:
    """R19: the pins axis, independent of category_counts/disabled_days."""
    shared = RuleSet(pins=(PinRule(day=1, slot=MealSlot.LUNCH, recipe_id="r1"),))
    override_pins = (PinRule(day=2, slot=MealSlot.DINNER, recipe_id="r2"),)

    result = apply_override(shared, pins=override_pins)

    assert result.pins == override_pins
    assert result.category_counts == shared.category_counts
    assert result.disabled_days == shared.disabled_days


def test_apply_override_uses_the_disabled_days_override_when_given() -> None:
    """R19: the disabled_days axis, independent of category_counts/pins."""
    shared = RuleSet(disabled_days=(3,))
    override_days = (5, 6)

    result = apply_override(shared, disabled_days=override_days)

    assert result.disabled_days == override_days
    assert result.category_counts == shared.category_counts
    assert result.pins == shared.pins


def test_apply_override_inherits_the_shared_value_when_none_given() -> None:
    """R19."""
    shared = RuleSet(
        category_counts=(CategoryCountRule(category=IngredientCategory.MEAT, count=2),),
        pins=(PinRule(day=1, slot=MealSlot.LUNCH, recipe_id="r1"),),
        disabled_days=(2,),
    )

    result = apply_override(shared)

    assert result == shared


def test_apply_override_never_mutates_shared() -> None:
    """R20: shared's fields are unchanged after the call (design.md section 8, alt B)."""
    shared = RuleSet(disabled_days=(3,))
    before = shared.disabled_days

    result = apply_override(shared, disabled_days=(2,))

    assert shared.disabled_days is before
    assert shared.disabled_days == (3,)
    assert result.disabled_days == (2,)


def test_no_rule_type_declares_an_author_field() -> None:
    """R21 (G-76, G-78)."""
    for dataclass_type in (RuleSet, CategoryCountRule, PinRule, rules_module.RemovePinsResult):
        for field in dataclasses.fields(dataclass_type):
            assert "author" not in field.name
            assert "editor" not in field.name
            assert "owner" not in field.name


def test_no_mutating_function_takes_an_actor_parameter() -> None:
    """R22 (G-76), mirrors week_plan_model's test_promote_takes_no_author_or_promoter_argument."""
    functions = (
        set_category_count,
        remove_category_count,
        set_pin,
        remove_pin,
        disable_day,
        enable_day,
        apply_override,
    )
    for function in functions:
        for name in inspect.signature(function).parameters:
            assert "user" not in name
            assert "author" not in name
            assert "actor" not in name
