"""Tests for the WeekRepository port and its in-memory fake."""

from __future__ import annotations

from datetime import date

from support.fakes import FakeWeekRepository

from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import Candidate, SlotContents
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import MealSnapshot
from planner_core.ports.weeks import WeekRepository

WEEK = IsoWeek(2026, 30)
MONDAY = SlotRef(date(2026, 7, 20), MealSlot.LUNCH)


def _meal() -> MealSnapshot:
    return MealSnapshot(
        name="Lentejas",
        ingredients=(),
        tools=(),
        procedure=(),
        category=IngredientCategory.LEGUME,
    )


def test_fake_week_repository_satisfies_the_week_repository_port() -> None:
    assert isinstance(FakeWeekRepository(), WeekRepository)


def test_get_week_returns_an_empty_mapping_for_an_unwritten_week() -> None:
    assert FakeWeekRepository().get_week(WEEK) == {}


def test_save_slot_round_trip() -> None:
    repo = FakeWeekRepository()
    contents = SlotContents(candidates=(Candidate(id="c1", meal=_meal(), author="u1"),))

    repo.save_slot(WEEK, MONDAY, contents)

    assert repo.get_week(WEEK) == {MONDAY: contents}


def test_save_week_overwrites_every_slot_at_once() -> None:
    repo = FakeWeekRepository()
    repo.save_slot(WEEK, MONDAY, SlotContents(candidates=(Candidate("c1", _meal(), "u1"),)))

    other_slot = SlotRef(date(2026, 7, 21), MealSlot.DINNER)
    new_plans = {other_slot: SlotContents(candidates=(Candidate("c2", _meal(), "u2"),))}
    repo.save_week(WEEK, new_plans)

    assert repo.get_week(WEEK) == new_plans
