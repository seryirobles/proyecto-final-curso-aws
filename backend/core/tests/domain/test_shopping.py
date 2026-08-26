"""Tests for shopping aggregation: scope, definitive lookup and merge (R1-R8)."""

from __future__ import annotations

import dataclasses
from datetime import date

from planner_core.domain.calendar import MealSlot, SlotRef, next_week
from planner_core.domain.candidate import Candidate, SlotContents
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Ingredient, MealSnapshot
from planner_core.domain.shopping import (
    aggregate_ingredients,
    definitive_ingredients,
    in_scope_slots,
    required_shopping_items,
)
from planner_core.domain.units import Unit

# A Wednesday, so both "earlier this week" and "later this week" are exercisable.
WEDNESDAY = date(2026, 8, 26)


def _meal(name: str = "Lentejas", *ingredients: Ingredient) -> MealSnapshot:
    return MealSnapshot(
        name=name,
        ingredients=ingredients,
        tools=(),
        procedure=(),
        category=IngredientCategory.LEGUME,
    )


def _plan_with_definitive(*ingredients: Ingredient, name: str = "Lentejas") -> SlotContents:
    candidate = Candidate(id="c1", meal=_meal(name, *ingredients), author="u1")
    return SlotContents(candidates=(candidate,), definitive_id="c1")


def _plan_with_only_candidates(*ingredients: Ingredient) -> SlotContents:
    candidate = Candidate(id="c1", meal=_meal("Lentejas", *ingredients), author="u1")
    return SlotContents(candidates=(candidate,), definitive_id=None)


# --- R1, R2: in_scope_slots -------------------------------------------------


def test_in_scope_slots_includes_current_week_from_today_onward() -> None:
    slots = in_scope_slots(WEDNESDAY)

    monday = date(2026, 8, 24)
    tuesday = date(2026, 8, 25)
    sunday = date(2026, 8, 30)

    assert SlotRef(WEDNESDAY, MealSlot.LUNCH) in slots
    assert SlotRef(WEDNESDAY, MealSlot.DINNER) in slots
    assert SlotRef(sunday, MealSlot.LUNCH) in slots
    assert SlotRef(monday, MealSlot.LUNCH) not in slots
    assert SlotRef(tuesday, MealSlot.LUNCH) not in slots


def test_in_scope_slots_includes_the_whole_next_week() -> None:
    slots = in_scope_slots(WEDNESDAY)

    next_monday = next_week(WEDNESDAY).monday
    next_tuesday = date(2026, 9, 1)

    next_week_slots = {slot for slot in slots if slot.day >= next_monday}
    assert len(next_week_slots) == 14
    assert SlotRef(next_monday, MealSlot.LUNCH) in slots
    assert SlotRef(next_tuesday, MealSlot.LUNCH) in slots


# --- R3, R4: definitive_ingredients ------------------------------------------


def test_definitive_ingredients_includes_a_slots_definitive_meal() -> None:
    slot = SlotRef(WEDNESDAY, MealSlot.LUNCH)
    ingredients = (
        Ingredient(name="lentejas", quantity=500, unit=Unit.GRAM),
        Ingredient(name="chorizo", quantity=1, unit=Unit.UNIT),
    )
    plan = _plan_with_definitive(*ingredients)

    result = definitive_ingredients({slot: plan}, (slot,))

    assert result == ingredients


def test_definitive_ingredients_ignores_a_slot_with_only_candidates() -> None:
    slot = SlotRef(WEDNESDAY, MealSlot.LUNCH)
    plan = _plan_with_only_candidates(Ingredient(name="tomate", quantity=200, unit=Unit.GRAM))

    result = definitive_ingredients({slot: plan}, (slot,))

    assert result == ()


def test_definitive_ingredients_ignores_a_slot_absent_from_plans() -> None:
    slot = SlotRef(WEDNESDAY, MealSlot.LUNCH)

    result = definitive_ingredients({}, (slot,))

    assert result == ()


def test_definitive_ingredients_preserves_slot_and_ingredient_order() -> None:
    slot_a = SlotRef(WEDNESDAY, MealSlot.LUNCH)
    slot_b = SlotRef(WEDNESDAY, MealSlot.DINNER)
    ingredients_a = (
        Ingredient(name="arroz", quantity=200, unit=Unit.GRAM),
        Ingredient(name="pollo", quantity=1, unit=Unit.UNIT),
    )
    ingredients_b = (
        Ingredient(name="patata", quantity=300, unit=Unit.GRAM),
        Ingredient(name="leche", quantity=200, unit=Unit.MILLILITRE),
    )
    plans = {
        slot_a: _plan_with_definitive(*ingredients_a),
        slot_b: _plan_with_definitive(*ingredients_b),
    }

    result = definitive_ingredients(plans, (slot_a, slot_b))

    assert result == ingredients_a + ingredients_b


# --- R5, R6: aggregate_ingredients -------------------------------------------


def test_aggregate_ingredients_sums_matching_name_and_unit() -> None:
    result = aggregate_ingredients(
        (
            Ingredient(name="tomate", quantity=200, unit=Unit.GRAM),
            Ingredient(name="tomate", quantity=300, unit=Unit.GRAM),
        )
    )

    assert result == (Ingredient(name="tomate", quantity=500, unit=Unit.GRAM),)


def test_aggregate_ingredients_matches_on_normalized_name() -> None:
    result = aggregate_ingredients(
        (
            Ingredient(name="Tomate", quantity=200, unit=Unit.GRAM),
            Ingredient(name=" tomate ", quantity=300, unit=Unit.GRAM),
        )
    )

    assert len(result) == 1
    assert result[0].quantity == 500


def test_aggregate_ingredients_keeps_different_units_separate() -> None:
    result = aggregate_ingredients(
        (
            Ingredient(name="leche", quantity=500, unit=Unit.MILLILITRE),
            Ingredient(name="leche", quantity=1, unit=Unit.UNIT),
        )
    )

    assert len(result) == 2
    quantities = {item.unit: item.quantity for item in result}
    assert quantities == {Unit.MILLILITRE: 500, Unit.UNIT: 1}


def test_aggregate_ingredients_keeps_different_normalized_names_separate() -> None:
    """G-56: no stemming or singular/plural fold, so 'tomate' and 'tomates' stay apart."""
    result = aggregate_ingredients(
        (
            Ingredient(name="tomate", quantity=200, unit=Unit.GRAM),
            Ingredient(name="tomates", quantity=200, unit=Unit.GRAM),
        )
    )

    assert len(result) == 2


def test_aggregate_ingredients_keeps_the_first_occurrences_spelling() -> None:
    result = aggregate_ingredients(
        (
            Ingredient(name="Tomate", quantity=200, unit=Unit.GRAM),
            Ingredient(name="tomate", quantity=100, unit=Unit.GRAM),
        )
    )

    assert len(result) == 1
    assert result[0].name == "Tomate"


def test_aggregate_ingredients_result_items_are_ingredient_instances() -> None:
    """R8: exactly {name, quantity, unit}, no provenance field (G-72, G-73)."""
    result = aggregate_ingredients((Ingredient(name="tomate", quantity=200, unit=Unit.GRAM),))

    assert all(isinstance(item, Ingredient) for item in result)
    assert {f.name for f in dataclasses.fields(Ingredient)} == {"name", "quantity", "unit"}


def test_aggregate_ingredients_of_empty_input_is_an_empty_tuple() -> None:
    assert aggregate_ingredients(()) == ()


# --- required_shopping_items: composition ------------------------------------


def test_required_shopping_items_excludes_candidates_never_promoted() -> None:
    definitive_slot = SlotRef(WEDNESDAY, MealSlot.LUNCH)
    candidate_only_slot = SlotRef(WEDNESDAY, MealSlot.DINNER)
    plans = {
        definitive_slot: _plan_with_definitive(
            Ingredient(name="lentejas", quantity=500, unit=Unit.GRAM)
        ),
        candidate_only_slot: _plan_with_only_candidates(
            Ingredient(name="tomate", quantity=200, unit=Unit.GRAM)
        ),
    }

    result = required_shopping_items(plans, WEDNESDAY)

    assert all(item.name != "tomate" for item in result)


def test_required_shopping_items_excludes_a_definitive_outside_scope() -> None:
    past_day = date(2026, 8, 24)  # Monday, before WEDNESDAY
    past_slot = SlotRef(past_day, MealSlot.LUNCH)
    plans = {past_slot: _plan_with_definitive(Ingredient(name="pan", quantity=1, unit=Unit.UNIT))}

    result = required_shopping_items(plans, WEDNESDAY)

    assert result == ()


def test_required_shopping_items_merges_across_both_weeks() -> None:
    current_slot = SlotRef(WEDNESDAY, MealSlot.LUNCH)
    next_slot = SlotRef(next_week(WEDNESDAY).monday, MealSlot.LUNCH)
    plans = {
        current_slot: _plan_with_definitive(Ingredient(name="arroz", quantity=200, unit=Unit.GRAM)),
        next_slot: _plan_with_definitive(Ingredient(name="arroz", quantity=300, unit=Unit.GRAM)),
    }

    result = required_shopping_items(plans, WEDNESDAY)

    assert result == (Ingredient(name="arroz", quantity=500, unit=Unit.GRAM),)


def test_required_shopping_items_is_deterministic_across_repeated_invocations() -> None:
    slot = SlotRef(WEDNESDAY, MealSlot.LUNCH)
    plans = {slot: _plan_with_definitive(Ingredient(name="arroz", quantity=200, unit=Unit.GRAM))}

    first = required_shopping_items(plans, WEDNESDAY)
    second = required_shopping_items(plans, WEDNESDAY)

    assert first == second


def test_required_shopping_items_is_idempotent_by_construction() -> None:
    """FR-SHOP-10, G-54: a third run against an equal-but-distinct copy still converges."""
    slot = SlotRef(WEDNESDAY, MealSlot.LUNCH)
    plans = {slot: _plan_with_definitive(Ingredient(name="arroz", quantity=200, unit=Unit.GRAM))}
    plans_copy = dict(plans)

    first = required_shopping_items(plans, WEDNESDAY)
    third = required_shopping_items(plans_copy, WEDNESDAY)

    assert first == third


def test_required_shopping_items_returns_empty_tuple_when_nothing_is_required() -> None:
    result = required_shopping_items({}, WEDNESDAY)

    assert result == ()
    assert result is not None
