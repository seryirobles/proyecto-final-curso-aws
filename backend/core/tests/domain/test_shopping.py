"""Tests for shopping aggregation: scope, definitive lookup and merge (R1-R8)."""

from __future__ import annotations

import dataclasses
from datetime import date

from planner_core.domain.calendar import MealSlot, SlotRef, next_week
from planner_core.domain.candidate import Candidate, SlotContents
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Ingredient, MealSnapshot
from planner_core.domain.shopping import (
    InsufficientNewIds,
    ShoppingItem,
    ShoppingItemNotFound,
    add_item,
    aggregate_ingredients,
    check_item,
    checked_items,
    definitive_ingredients,
    edit_item,
    in_scope_slots,
    outstanding_amounts,
    remove_item,
    required_shopping_items,
    resync,
    uncheck_item,
    unchecked_items,
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


# --- R1: ShoppingItem shape ---------------------------------------------------


def test_shopping_item_has_exactly_the_fixed_fields() -> None:
    assert {f.name for f in dataclasses.fields(ShoppingItem)} == {
        "id",
        "name",
        "quantity",
        "unit",
        "checked",
    }


# --- R2, R19: add_item ---------------------------------------------------------


def test_add_item_appends_unconditionally() -> None:
    existing = ShoppingItem(id="1", name="pan", quantity=1, unit=Unit.UNIT)
    new = ShoppingItem(id="2", name="leche", quantity=1, unit=Unit.MILLILITRE)

    result = add_item((existing,), new)

    assert result == (existing, new)


def test_add_item_does_not_reject_a_matching_normalized_name_and_unit() -> None:
    existing = ShoppingItem(id="1", name="Arroz", quantity=200, unit=Unit.GRAM)
    duplicate = ShoppingItem(id="2", name="arroz", quantity=300, unit=Unit.GRAM)

    result = add_item((existing,), duplicate)

    assert result == (existing, duplicate)


# --- R3, R4, R6: edit_item -------------------------------------------------------


def test_edit_item_replaces_name_and_quantity() -> None:
    item = ShoppingItem(id="1", name="pan", quantity=1, unit=Unit.UNIT)

    result = edit_item((item,), "1", "pan integral", 2)

    assert result[0].name == "pan integral"
    assert result[0].quantity == 2


def test_edit_item_preserves_unit_and_check_state() -> None:
    item = ShoppingItem(id="1", name="pan", quantity=1, unit=Unit.UNIT, checked=True)

    result = edit_item((item,), "1", "pan integral", 2)

    assert result[0].unit == Unit.UNIT
    assert result[0].checked is True


def test_edit_item_on_unknown_id_raises_shopping_item_not_found() -> None:
    try:
        edit_item((), "missing", "pan", 1)
        raise AssertionError("expected ShoppingItemNotFound")
    except ShoppingItemNotFound as exc:
        assert exc.item_id == "missing"


# --- R5, R6: remove_item ----------------------------------------------------------


def test_remove_item_deletes_the_matching_item() -> None:
    kept = ShoppingItem(id="1", name="pan", quantity=1, unit=Unit.UNIT)
    removed = ShoppingItem(id="2", name="leche", quantity=1, unit=Unit.MILLILITRE)

    result = remove_item((kept, removed), "2")

    assert result == (kept,)


def test_remove_item_on_unknown_id_raises_shopping_item_not_found() -> None:
    try:
        remove_item((), "missing")
        raise AssertionError("expected ShoppingItemNotFound")
    except ShoppingItemNotFound as exc:
        assert exc.item_id == "missing"


# --- R6, R7, R8: check_item / uncheck_item ----------------------------------------


def test_check_item_sets_checked_true() -> None:
    item = ShoppingItem(id="1", name="pan", quantity=1, unit=Unit.UNIT, checked=False)

    result = check_item((item,), "1")

    assert result[0].checked is True
    assert result[0].name == "pan"
    assert result[0].quantity == 1
    assert result[0].unit == Unit.UNIT


def test_uncheck_item_sets_checked_false() -> None:
    item = ShoppingItem(id="1", name="pan", quantity=1, unit=Unit.UNIT, checked=True)

    result = uncheck_item((item,), "1")

    assert result[0].checked is False


def test_check_and_uncheck_on_unknown_id_raise() -> None:
    for op in (check_item, uncheck_item):
        try:
            op((), "missing")
            raise AssertionError("expected ShoppingItemNotFound")
        except ShoppingItemNotFound as exc:
            assert exc.item_id == "missing"


# --- R9: unchecked_items / checked_items -------------------------------------------


def test_unchecked_items_and_checked_items_partition_the_list() -> None:
    a = ShoppingItem(id="1", name="pan", quantity=1, unit=Unit.UNIT, checked=False)
    b = ShoppingItem(id="2", name="leche", quantity=1, unit=Unit.MILLILITRE, checked=True)
    c = ShoppingItem(id="3", name="huevos", quantity=6, unit=Unit.UNIT, checked=False)
    items = (a, b, c)

    unchecked = unchecked_items(items)
    checked = checked_items(items)

    assert set(unchecked) | set(checked) == set(items)
    assert set(unchecked) & set(checked) == set()
    assert all(not i.checked for i in unchecked)
    assert all(i.checked for i in checked)


# --- R10, R13: outstanding_amounts --------------------------------------------------


def test_outstanding_amounts_computes_required_minus_checked() -> None:
    checked = ShoppingItem(id="1", name="arroz", quantity=500, unit=Unit.GRAM, checked=True)
    required = (Ingredient(name="arroz", quantity=800, unit=Unit.GRAM),)

    result = outstanding_amounts((checked,), required)

    assert result == (Ingredient(name="arroz", quantity=300, unit=Unit.GRAM),)


def test_outstanding_amounts_omits_zero_or_negative() -> None:
    checked = ShoppingItem(id="1", name="arroz", quantity=800, unit=Unit.GRAM, checked=True)
    required = (Ingredient(name="arroz", quantity=500, unit=Unit.GRAM),)

    result = outstanding_amounts((checked,), required)

    assert result == ()


def test_outstanding_amounts_omits_the_exact_zero_boundary() -> None:
    """The zero half of the "zero or negative" claim - checked covers required exactly."""
    checked = ShoppingItem(id="1", name="arroz", quantity=500, unit=Unit.GRAM, checked=True)
    required = (Ingredient(name="arroz", quantity=500, unit=Unit.GRAM),)

    result = outstanding_amounts((checked,), required)

    assert result == ()

    resynced = resync((checked,), required, new_ids=())
    assert resynced == (checked,)


# --- R20: resync's first-occurrence tie-break -----------------------------------------


def test_resync_writes_to_the_first_of_two_matching_unchecked_items() -> None:
    first = ShoppingItem(id="1", name="Arroz", quantity=100, unit=Unit.GRAM, checked=False)
    second = ShoppingItem(id="2", name="arroz", quantity=100, unit=Unit.GRAM, checked=False)
    required = (Ingredient(name="arroz", quantity=500, unit=Unit.GRAM),)

    result = resync((first, second), required, new_ids=())

    updated_first = next(i for i in result if i.id == "1")
    updated_second = next(i for i in result if i.id == "2")
    assert updated_first.quantity == 500
    assert updated_second == second


# --- R21: resync's write-scope guard (quantity only) ----------------------------------


def test_resync_preserves_the_matched_items_own_name_and_unit() -> None:
    existing = ShoppingItem(id="1", name="Arroz ", quantity=100, unit=Unit.GRAM, checked=False)
    required = (Ingredient(name="arroz", quantity=500, unit=Unit.GRAM),)

    result = resync((existing,), required, new_ids=())

    assert result == (
        ShoppingItem(id="1", name="Arroz ", quantity=500, unit=Unit.GRAM, checked=False),
    )


# --- R11-R18: resync -----------------------------------------------------------------


def test_resync_writes_outstanding_to_the_matching_unchecked_item() -> None:
    unchecked = ShoppingItem(id="1", name="arroz", quantity=200, unit=Unit.GRAM, checked=False)
    required = (Ingredient(name="arroz", quantity=500, unit=Unit.GRAM),)

    result = resync((unchecked,), required, new_ids=())

    assert result == (
        ShoppingItem(id="1", name="arroz", quantity=500, unit=Unit.GRAM, checked=False),
    )


def test_resync_creates_a_new_unchecked_item_when_none_matches() -> None:
    required = (Ingredient(name="arroz", quantity=500, unit=Unit.GRAM),)

    result = resync((), required, new_ids=("new-1",))

    assert result == (
        ShoppingItem(id="new-1", name="arroz", quantity=500, unit=Unit.GRAM, checked=False),
    )


def test_resync_new_item_carries_the_remainder_not_the_gross_amount() -> None:
    """The G-77 scenario: checked arroz 500 g, required raised to 800 g."""
    checked = ShoppingItem(id="checked-1", name="arroz", quantity=500, unit=Unit.GRAM, checked=True)
    required = (Ingredient(name="arroz", quantity=800, unit=Unit.GRAM),)

    result = resync((checked,), required, new_ids=("new-1",))

    assert checked in result
    new_item = next(i for i in result if i.id == "new-1")
    assert new_item.quantity == 300
    assert new_item.unit == Unit.GRAM
    assert new_item.checked is False


def test_resync_never_removes_a_stale_or_manual_item() -> None:
    stale = ShoppingItem(id="1", name="clavo", quantity=1, unit=Unit.UNIT, checked=False)
    required = (Ingredient(name="arroz", quantity=500, unit=Unit.GRAM),)

    result = resync((stale,), required, new_ids=("new-1",))

    assert stale in result


def test_resync_never_modifies_a_checked_items_quantity_or_state() -> None:
    checked = ShoppingItem(id="checked-1", name="arroz", quantity=500, unit=Unit.GRAM, checked=True)
    required = (Ingredient(name="arroz", quantity=900, unit=Unit.GRAM),)

    result = resync((checked,), required, new_ids=("new-1",))

    assert checked in result


def test_resync_leaves_a_manual_item_absent_from_the_computed_set_untouched() -> None:
    manual = ShoppingItem(id="1", name="bolsas de basura", quantity=1, unit=Unit.UNIT)
    required = (Ingredient(name="arroz", quantity=500, unit=Unit.GRAM),)

    result = resync((manual,), required, new_ids=("new-1",))

    assert manual in result


def test_resync_is_idempotent_across_two_consecutive_presses() -> None:
    required = (Ingredient(name="arroz", quantity=500, unit=Unit.GRAM),)

    first = resync((), required, new_ids=("new-1",))
    second = resync(first, required, new_ids=())

    assert first == second


def test_resync_retains_checked_and_new_unchecked_item_sharing_a_key() -> None:
    checked = ShoppingItem(id="checked-1", name="arroz", quantity=500, unit=Unit.GRAM, checked=True)
    required = (Ingredient(name="arroz", quantity=800, unit=Unit.GRAM),)

    result = resync((checked,), required, new_ids=("new-1",))

    checked_ids = {i.id for i in result if i.checked}
    unchecked_ids = {i.id for i in result if not i.checked}
    assert "checked-1" in checked_ids
    assert "new-1" in unchecked_ids
    assert len(result) == 2


def test_resync_raises_insufficient_new_ids_when_supply_is_exhausted() -> None:
    required = (Ingredient(name="arroz", quantity=500, unit=Unit.GRAM),)

    try:
        resync((), required, new_ids=())
        raise AssertionError("expected InsufficientNewIds")
    except InsufficientNewIds:
        pass
