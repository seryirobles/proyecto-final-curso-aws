"""Tests for the rollover transition: archive, promote, init, cleanup (R1-R13)."""

from __future__ import annotations

import dataclasses
import inspect

import pytest

from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import Candidate, SlotContents
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import MealSnapshot
from planner_core.domain.rollover import (
    ArchivedWeek,
    RolloverResult,
    archive_week,
    init_empty_next_week,
    promote_next_to_current,
    roll_over,
)
from planner_core.domain.shopping import ShoppingItem, unchecked_items
from planner_core.domain.units import Unit

WEEK = IsoWeek(2026, 35)
MONDAY = WEEK.monday
SLOT = SlotRef(MONDAY, MealSlot.LUNCH)


def _meal(name: str = "Lentejas") -> MealSnapshot:
    return MealSnapshot(
        name=name, ingredients=(), tools=(), procedure=(), category=IngredientCategory.LEGUME
    )


def _plan_with_definitive(name: str = "Lentejas") -> SlotContents:
    candidate = Candidate(id="c1", meal=_meal(name), author="u1")
    return SlotContents(candidates=(candidate,), definitive_id="c1")


def _shopping_items() -> tuple[ShoppingItem, ...]:
    return (
        ShoppingItem(id="1", name="pan", quantity=1, unit=Unit.UNIT, checked=False),
        ShoppingItem(id="2", name="leche", quantity=1, unit=Unit.MILLILITRE, checked=True),
        ShoppingItem(id="3", name="huevos", quantity=6, unit=Unit.UNIT, checked=False),
    )


# --- R1, R2: ArchivedWeek shape and frozen-ness ------------------------------


def test_archived_week_has_exactly_the_fixed_fields() -> None:
    assert {f.name for f in dataclasses.fields(ArchivedWeek)} == {
        "week",
        "plans",
        "shopping_snapshot",
    }


def test_archived_week_is_frozen() -> None:
    archived = ArchivedWeek(week=WEEK, plans={}, shopping_snapshot=())

    with pytest.raises(dataclasses.FrozenInstanceError):
        archived.week = IsoWeek(2026, 36)  # type: ignore[misc]


# --- R3: RolloverResult shape -------------------------------------------------


def test_rollover_result_has_exactly_the_fixed_fields() -> None:
    assert {f.name for f in dataclasses.fields(RolloverResult)} == {
        "archived",
        "new_current_plans",
        "new_next_plans",
        "shopping_items",
    }


def test_rollover_result_is_frozen() -> None:
    result = RolloverResult(
        archived=ArchivedWeek(week=WEEK, plans={}, shopping_snapshot=()),
        new_current_plans={},
        new_next_plans={},
        shopping_items=(),
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        result.new_current_plans = {}  # type: ignore[misc]


# --- R4, R5, R6: roll_over's archive fields -----------------------------------


def test_roll_over_archives_the_former_current_week_identity() -> None:
    result = roll_over(WEEK, {}, {}, _shopping_items())

    assert result.archived.week == WEEK


def test_roll_over_archives_the_former_current_plans_unchanged() -> None:
    former_current_plans = {SLOT: _plan_with_definitive()}

    result = roll_over(WEEK, former_current_plans, {}, _shopping_items())

    assert result.archived.plans == former_current_plans


def test_roll_over_archives_the_shopping_list_before_cleanup() -> None:
    """R6 vs R9: the archive keeps the checked item; the final list drops it (G-53)."""
    items = _shopping_items()

    result = roll_over(WEEK, {}, {}, items)

    assert result.archived.shopping_snapshot == items
    assert any(i.checked for i in result.archived.shopping_snapshot)


# --- R7: promote_next_to_current / new_current_plans --------------------------


def test_promote_next_to_current_returns_next_plans_unchanged() -> None:
    next_plans = {SLOT: _plan_with_definitive()}

    assert promote_next_to_current(next_plans) == next_plans


def test_roll_over_new_current_plans_equals_former_next_plans_with_candidates_and_definitive() -> (
    None
):
    former_next_plans = {SLOT: _plan_with_definitive()}

    result = roll_over(WEEK, {}, former_next_plans, _shopping_items())

    assert result.new_current_plans == former_next_plans


# --- R8, R10: init_empty_next_week / new_next_plans ----------------------------


def test_init_empty_next_week_returns_an_empty_mapping() -> None:
    assert init_empty_next_week() == {}


def test_init_empty_next_week_takes_no_parameters() -> None:
    assert inspect.signature(init_empty_next_week).parameters == {}


def test_roll_over_new_next_plans_is_always_empty_regardless_of_inputs() -> None:
    former_current_plans = {SLOT: _plan_with_definitive("A")}
    former_next_plans = {SLOT: _plan_with_definitive("B")}

    result = roll_over(WEEK, former_current_plans, former_next_plans, _shopping_items())

    assert result.new_next_plans == {}


# --- R9: cleanup -----------------------------------------------------------------


def test_roll_over_shopping_items_equals_the_unchecked_subset_in_order() -> None:
    items = _shopping_items()

    result = roll_over(WEEK, {}, {}, items)

    assert result.shopping_items == tuple(i for i in items if not i.checked)


# --- R11: archive_week / promote_next_to_current / init_empty_next_week determinism --


@pytest.mark.parametrize(
    "call_first, call_second",
    [
        (
            lambda: archive_week(WEEK, {SLOT: _plan_with_definitive()}, _shopping_items()),
            lambda: archive_week(WEEK, {SLOT: _plan_with_definitive()}, _shopping_items()),
        ),
        (
            lambda: promote_next_to_current({SLOT: _plan_with_definitive()}),
            lambda: promote_next_to_current({SLOT: _plan_with_definitive()}),
        ),
        (
            lambda: init_empty_next_week(),
            lambda: init_empty_next_week(),
        ),
    ],
)
def test_step_is_deterministic_on_identical_arguments(call_first, call_second) -> None:  # type: ignore[no-untyped-def]
    assert call_first() == call_second()


# --- R12: unchecked_items is a fixed point on an already-clean list -----------------


def test_unchecked_items_of_an_already_clean_list_is_unchanged() -> None:
    items = (
        ShoppingItem(id="1", name="pan", quantity=1, unit=Unit.UNIT, checked=False),
        ShoppingItem(id="2", name="huevos", quantity=6, unit=Unit.UNIT, checked=False),
    )

    assert unchecked_items(items) == items


# --- R13: roll_over as a whole is deterministic -------------------------------------


def test_roll_over_is_deterministic_on_identical_arguments() -> None:
    former_current_plans = {SLOT: _plan_with_definitive("A")}
    former_next_plans = {SLOT: _plan_with_definitive("B")}
    items = _shopping_items()

    first = roll_over(WEEK, former_current_plans, former_next_plans, items)
    second = roll_over(WEEK, former_current_plans, former_next_plans, items)

    assert first == second
