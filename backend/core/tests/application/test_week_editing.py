"""Tests for candidate CRUD and definitive selection: every mutation returns
the week's change marker (R9, R29, R30)."""

from __future__ import annotations

import dataclasses
from datetime import date

import pytest
from support.fakes import FakeWeekRepository

from planner_core.application import week_editing
from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import Candidate, CandidateNotFound
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import MealSnapshot

WEEK = IsoWeek(2026, 30)
SLOT = SlotRef(date(2026, 7, 20), MealSlot.LUNCH)


def _meal(name: str = "Lentejas") -> MealSnapshot:
    return MealSnapshot(
        name=name, ingredients=(), tools=(), procedure=(), category=IngredientCategory.LEGUME
    )


def _candidate(cid: str = "c1", name: str = "Lentejas") -> Candidate:
    return Candidate(id=cid, meal=_meal(name), author="u1")


def test_add_candidate_outcome_is_frozen() -> None:
    """docs/conventions.md: every new frozen dataclass gets this test."""
    outcome = week_editing.AddCandidateOutcome(marker=1, duplicate_warning=False)
    with pytest.raises(dataclasses.FrozenInstanceError):
        outcome.__setattr__("marker", 2)


def test_add_candidate_returns_marker_and_duplicate_warning() -> None:
    repo = FakeWeekRepository()

    first = week_editing.add_slot_candidate(WEEK, SLOT, _candidate("c1"), weeks=repo)
    second = week_editing.add_slot_candidate(WEEK, SLOT, _candidate("c2", "Lentejas"), weeks=repo)

    assert first.marker == 1 and first.duplicate_warning is False
    assert second.marker == 2 and second.duplicate_warning is True


def test_edit_delete_promote_clear_each_return_the_new_marker() -> None:
    repo = FakeWeekRepository()
    week_editing.add_slot_candidate(WEEK, SLOT, _candidate("c1"), weeks=repo)

    assert week_editing.edit_slot_candidate(WEEK, SLOT, "c1", _meal("Arroz"), weeks=repo) == 2
    assert week_editing.set_definitive(WEEK, SLOT, "c1", weeks=repo) == 3
    assert week_editing.clear_slot_definitive(WEEK, SLOT, weeks=repo) == 4
    assert week_editing.delete_slot_candidate(WEEK, SLOT, "c1", weeks=repo) == 5


def test_promote_an_absent_candidate_raises_and_does_not_write() -> None:
    repo = FakeWeekRepository()
    with pytest.raises(CandidateNotFound):
        week_editing.set_definitive(WEEK, SLOT, "missing", weeks=repo)
    assert repo.current_version(WEEK) == 0


def test_load_week_and_load_candidate_read_without_writing() -> None:
    repo = FakeWeekRepository()
    week_editing.add_slot_candidate(WEEK, SLOT, _candidate("c1"), weeks=repo)

    assert set(week_editing.load_week(WEEK, weeks=repo)) == {SLOT}
    found = week_editing.load_candidate(WEEK, SLOT, "c1", weeks=repo)
    assert found is not None and found.id == "c1"
    assert week_editing.load_candidate(WEEK, SLOT, "nope", weeks=repo) is None
    assert repo.current_version(WEEK) == 1
