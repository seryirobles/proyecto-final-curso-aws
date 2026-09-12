"""Tests for shopping-list editing and the re-sync composition (R20-R24, R29)."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from datetime import UTC, date, datetime, timedelta

import pytest
from support.fakes import FakeShoppingListRepository, FakeWeekRepository

from planner_core.application import shopping_editing
from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import Candidate, SlotContents
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Ingredient, MealSnapshot
from planner_core.domain.shopping import ShoppingItem
from planner_core.domain.units import Unit
from planner_core.ports.shopping_list import ShoppingListLockHeld

TODAY = date(2026, 7, 20)  # Monday, ISO 2026-W30
NOW = datetime(2026, 7, 20, 9, 0, tzinfo=UTC)
EXPIRES = NOW + timedelta(minutes=5)
MEAL_SLOT = SlotRef(date(2026, 7, 22), MealSlot.LUNCH)


def _week_with_rice(grams: float) -> FakeWeekRepository:
    meal = MealSnapshot(
        name="Arroz",
        ingredients=(Ingredient(name="arroz", quantity=grams, unit=Unit.GRAM),),
        tools=(),
        procedure=(),
        category=IngredientCategory.CARBOHYDRATE,
    )
    plan = SlotContents(
        candidates=(Candidate(id="c1", meal=meal, author="u1"),), definitive_id="c1"
    )
    weeks = FakeWeekRepository()
    weeks.save_slot(IsoWeek(2026, 30), MEAL_SLOT, plan)
    return weeks


def test_resync_outcome_is_frozen() -> None:
    """docs/conventions.md: every new frozen dataclass gets this test."""
    outcome = shopping_editing.ResyncOutcome(items=(), marker=None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        outcome.__setattr__("marker", 1)


def test_shopping_view_is_frozen() -> None:
    """docs/conventions.md: every new frozen dataclass gets this test."""
    view = shopping_editing.ShoppingView(items=(), marker=1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        view.__setattr__("marker", 2)


def test_resync_appends_the_outstanding_item_and_returns_the_write_marker() -> None:
    weeks = _week_with_rice(500)
    shopping = FakeShoppingListRepository()

    outcome = shopping_editing.resync_shopping_list(
        "owner-a", TODAY, NOW, EXPIRES, ["s-new"], shopping=shopping, weeks=weeks
    )

    assert outcome.marker == 1
    assert shopping.list_items() == (
        ShoppingItem(id="s-new", name="arroz", quantity=500, unit=Unit.GRAM),
    )


def test_resync_raises_an_existing_unchecked_item_quantity_and_writes_it_back() -> None:
    """R20/R9 — merge-in-place onto an unchecked match (contract section 3.3,
    design.md section 7 tie-break): the store must hold the merged quantity and
    the outcome must carry the advanced marker."""
    weeks = _week_with_rice(500)
    shopping = FakeShoppingListRepository()
    shopping.save_item(ShoppingItem(id="s-1", name="arroz", quantity=200, unit=Unit.GRAM))

    outcome = shopping_editing.resync_shopping_list(
        "owner-a", TODAY, NOW, EXPIRES, [], shopping=shopping, weeks=weeks
    )

    assert (
        ShoppingItem(id="s-1", name="arroz", quantity=500, unit=Unit.GRAM) in shopping.list_items()
    )
    assert outcome.marker is not None


def test_resync_never_writes_a_checked_item_and_never_removes_one() -> None:
    """R21, R22 — G-77: 500 g bought, requirement now 800 g."""
    weeks = _week_with_rice(800)
    shopping = FakeShoppingListRepository()
    bought = ShoppingItem(id="s-1", name="arroz", quantity=500, unit=Unit.GRAM, checked=True)
    shopping.save_item(bought)

    outcome = shopping_editing.resync_shopping_list(
        "owner-a", TODAY, NOW, EXPIRES, ["s-2"], shopping=shopping, weeks=weeks
    )

    items = shopping.list_items()
    assert bought in items  # untouched
    assert ShoppingItem(id="s-2", name="arroz", quantity=300, unit=Unit.GRAM) in items
    assert len(items) == 2
    assert outcome.marker is not None


def test_resync_acquires_the_lock_before_reading_the_week() -> None:
    """R23 — a fake week repo that fails the test if read before the lock is held."""
    shopping = FakeShoppingListRepository()

    class GuardedWeeks(FakeWeekRepository):
        def get_week(self, week: IsoWeek) -> Mapping[SlotRef, SlotContents]:
            assert shopping.lock is not None, "week read before lock acquired"
            return super().get_week(week)

    shopping_editing.resync_shopping_list(
        "owner-a", TODAY, NOW, EXPIRES, [], shopping=shopping, weeks=GuardedWeeks()
    )


def test_resync_raises_when_the_lock_is_held_by_another_owner() -> None:
    """R24."""
    weeks = _week_with_rice(500)
    shopping = FakeShoppingListRepository()
    shopping.acquire_lock("owner-b", NOW, EXPIRES)

    with pytest.raises(ShoppingListLockHeld):
        shopping_editing.resync_shopping_list(
            "owner-a", TODAY, NOW, EXPIRES, ["s"], shopping=shopping, weeks=weeks
        )


def test_resync_releases_the_lock_when_done() -> None:
    weeks = _week_with_rice(500)
    shopping = FakeShoppingListRepository()

    shopping_editing.resync_shopping_list(
        "owner-a", TODAY, NOW, EXPIRES, ["s"], shopping=shopping, weeks=weeks
    )

    shopping.acquire_lock("owner-c", NOW, EXPIRES)  # would raise if still held


def test_resync_needing_three_new_items_bumps_the_marker_once_not_three_times() -> None:
    """Feature 26, R8/R9 — the re-sync write step is one `save_items` call, so
    three differing items advance `current_version()` by exactly 1."""
    weeks = FakeWeekRepository()
    for index, ingredient_name in enumerate(("arroz", "pasta", "lenteja")):
        meal = MealSnapshot(
            name=f"Plato {index}",
            ingredients=(Ingredient(name=ingredient_name, quantity=100, unit=Unit.GRAM),),
            tools=(),
            procedure=(),
            category=IngredientCategory.CARBOHYDRATE,
        )
        plan = SlotContents(
            candidates=(Candidate(id=f"c{index}", meal=meal, author="u1"),),
            definitive_id=f"c{index}",
        )
        slot = SlotRef(date(2026, 7, 21 + index), MealSlot.LUNCH)
        weeks.save_slot(IsoWeek(2026, 30), slot, plan)
    shopping = FakeShoppingListRepository()
    before_version = shopping.current_version()

    outcome = shopping_editing.resync_shopping_list(
        "owner-a", TODAY, NOW, EXPIRES, ["s1", "s2", "s3"], shopping=shopping, weeks=weeks
    )

    assert shopping.current_version() == before_version + 1
    assert outcome.marker == before_version + 1
    assert len(outcome.items) == 3


def test_plain_edits_return_the_write_marker() -> None:
    shopping = FakeShoppingListRepository()
    item = ShoppingItem(id="i1", name="sal", quantity=1, unit=Unit.UNIT)

    assert shopping_editing.save_item(item, shopping=shopping) == 1
    assert shopping_editing.set_checked("i1", True, shopping=shopping) == 2
    assert shopping.list_items()[0].checked is True
    assert shopping_editing.delete_item("i1", shopping=shopping) == 3
