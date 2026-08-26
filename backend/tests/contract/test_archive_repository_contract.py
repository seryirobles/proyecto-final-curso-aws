"""Contract suite for ArchiveRepository: one suite, run against every registered
implementation (R9)."""

from __future__ import annotations

import pytest
from planner_core.domain.calendar import IsoWeek
from planner_core.domain.rollover import ArchivedWeek
from support.fakes import FakeArchiveRepository

IMPLEMENTATIONS = [FakeArchiveRepository]

WEEK = IsoWeek(2026, 29)


def _archived(week: IsoWeek = WEEK) -> ArchivedWeek:
    return ArchivedWeek(week=week, plans={}, shopping_snapshot=())


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_get_returns_none_when_absent(repository_factory: type[FakeArchiveRepository]) -> None:
    assert repository_factory().get(WEEK) is None


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_save_then_get_round_trip_and_is_idempotent(
    repository_factory: type[FakeArchiveRepository],
) -> None:
    repo = repository_factory()
    archived = _archived()

    repo.save(archived)
    repo.save(archived)

    assert repo.get(WEEK) == archived
