"""Tests for the WeekRepository port and its in-memory fake."""

from __future__ import annotations

from datetime import date
from typing import get_type_hints

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


# --- change marker (FR-RT-01): R1, R2, R3, R4, R5 ---

_CONTENTS = SlotContents(candidates=(Candidate(id="c1", meal=_meal(), author="u1"),))


def test_the_week_repository_protocol_pins_the_marker_surface() -> None:
    """R1: current_version and the int-returning writes are on the Protocol
    itself, not only the fake — deleting either from ports/weeks.py fails here."""
    assert "current_version" in WeekRepository.__dict__
    for method in ("save_slot", "save_week"):
        assert get_type_hints(getattr(WeekRepository, method))["return"] is int


def test_current_version_is_zero_for_a_week_never_written() -> None:
    assert FakeWeekRepository().current_version(WEEK) == 0  # R3


def test_save_slot_advances_the_marker_and_returns_the_new_value() -> None:
    repo = FakeWeekRepository()

    returned = repo.save_slot(WEEK, MONDAY, _CONTENTS)

    assert returned == 1  # first write returns 1 (R4, R5)
    assert repo.current_version(WEEK) == returned  # R4


def test_save_week_advances_the_marker_and_returns_the_new_value() -> None:
    repo = FakeWeekRepository()
    repo.save_slot(WEEK, MONDAY, _CONTENTS)

    returned = repo.save_week(WEEK, {MONDAY: _CONTENTS})

    assert returned == 2
    assert repo.current_version(WEEK) == returned  # R4


def test_reads_do_not_advance_the_marker() -> None:
    repo = FakeWeekRepository()
    repo.save_slot(WEEK, MONDAY, _CONTENTS)

    repo.get_week(WEEK)
    repo.current_version(WEEK)

    assert repo.current_version(WEEK) == 1  # R2


def test_two_weeks_carry_independent_markers() -> None:
    repo = FakeWeekRepository()
    other = IsoWeek(2026, 31)

    repo.save_slot(WEEK, MONDAY, _CONTENTS)

    assert repo.current_version(WEEK) == 1
    assert repo.current_version(other) == 0  # R3
