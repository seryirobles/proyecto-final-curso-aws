"""Contract suite for WeekRepository: one suite, run against every registered
implementation (R9)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

import pytest
from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import Candidate, SlotContents
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import MealSnapshot
from planner_core.ports.weeks import WeekRepository
from support.fakes import FakeWeekRepository

from tests.contract.dynamo_contract import ai_dynamo_week_repository, dynamo_week_repository

IMPLEMENTATIONS: list[Callable[[], WeekRepository]] = [
    FakeWeekRepository,
    dynamo_week_repository,
    ai_dynamo_week_repository,  # the planner_ai copy — drift between the two fails here (T21)
]

WEEK = IsoWeek(2026, 30)
MONDAY = SlotRef(date(2026, 7, 20), MealSlot.LUNCH)


def _meal() -> MealSnapshot:
    return MealSnapshot(
        name="Lentejas", ingredients=(), tools=(), procedure=(), category=IngredientCategory.LEGUME
    )


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_get_week_returns_an_empty_mapping_for_an_unwritten_week(
    repository_factory: Callable[[], WeekRepository],
) -> None:
    assert repository_factory().get_week(WEEK) == {}


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_save_slot_round_trip(repository_factory: Callable[[], WeekRepository]) -> None:
    repo = repository_factory()
    contents = SlotContents(candidates=(Candidate(id="c1", meal=_meal(), author="u1"),))

    repo.save_slot(WEEK, MONDAY, contents)

    assert repo.get_week(WEEK) == {MONDAY: contents}


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_save_week_overwrites_every_slot_at_once(
    repository_factory: Callable[[], WeekRepository],
) -> None:
    repo = repository_factory()
    repo.save_slot(WEEK, MONDAY, SlotContents(candidates=(Candidate("c1", _meal(), "u1"),)))

    other_slot = SlotRef(date(2026, 7, 21), MealSlot.DINNER)
    new_plans = {other_slot: SlotContents(candidates=(Candidate("c2", _meal(), "u2"),))}
    repo.save_week(WEEK, new_plans)

    assert repo.get_week(WEEK) == new_plans


# --- change marker (FR-RT-01): R2, R4, R5, R8, R11 ---

_CONTENTS = SlotContents(candidates=(Candidate(id="c1", meal=_meal(), author="u1"),))


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_every_mutating_method_advances_the_marker_and_returns_the_new_value(
    repository_factory: Callable[[], WeekRepository],
) -> None:
    repo = repository_factory()

    assert repo.save_slot(WEEK, MONDAY, _CONTENTS) == 1  # R4, R5
    assert repo.current_version(WEEK) == 1
    assert repo.save_week(WEEK, {MONDAY: _CONTENTS}) == 2
    assert repo.current_version(WEEK) == 2


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_reads_leave_the_marker_unchanged(
    repository_factory: Callable[[], WeekRepository],
) -> None:
    repo = repository_factory()
    repo.save_slot(WEEK, MONDAY, _CONTENTS)

    repo.get_week(WEEK)
    repo.current_version(WEEK)

    assert repo.current_version(WEEK) == 1  # R2


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_two_successive_writes_both_apply_and_advance_the_marker_twice(
    repository_factory: Callable[[], WeekRepository],
) -> None:
    repo = repository_factory()

    first = repo.save_slot(WEEK, MONDAY, _CONTENTS)
    second = repo.save_slot(WEEK, MONDAY, _CONTENTS)  # no raise: last-write-wins (R8)

    assert (first, second) == (1, 2)  # R11 — one bump per call


def test_the_two_dynamo_copies_read_each_other_back_over_the_same_table() -> None:
    """T21 — a key-format or attribute-name drift between the planner_api and
    planner_ai copies is only visible when one writes and the other reads."""
    api_repo, ai_repo = dynamo_week_repository(), ai_dynamo_week_repository()
    contents = SlotContents(candidates=(Candidate(id="c1", meal=_meal(), author="u1"),))
    other = SlotRef(date(2026, 7, 21), MealSlot.DINNER)

    api_repo.save_slot(WEEK, MONDAY, contents)
    assert ai_repo.get_week(WEEK) == {MONDAY: contents}

    ai_repo.save_slot(WEEK, other, contents)
    assert api_repo.get_week(WEEK) == {MONDAY: contents, other: contents}
