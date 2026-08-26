"""Tests for the ArchiveRepository port and its in-memory fake."""

from __future__ import annotations

from support.fakes import FakeArchiveRepository

from planner_core.domain.calendar import IsoWeek
from planner_core.domain.rollover import ArchivedWeek
from planner_core.ports.archive import ArchiveRepository

WEEK = IsoWeek(2026, 29)


def _archived(week: IsoWeek = WEEK) -> ArchivedWeek:
    return ArchivedWeek(week=week, plans={}, shopping_snapshot=())


def test_fake_archive_repository_satisfies_the_archive_repository_port() -> None:
    assert isinstance(FakeArchiveRepository(), ArchiveRepository)


def test_get_returns_none_when_absent() -> None:
    assert FakeArchiveRepository().get(WEEK) is None


def test_save_then_get_round_trip() -> None:
    repo = FakeArchiveRepository()
    archived = _archived()

    repo.save(archived)

    assert repo.get(WEEK) == archived


def test_save_is_idempotent_when_re_saving_an_equal_archived_week() -> None:
    repo = FakeArchiveRepository()
    archived = _archived()

    repo.save(archived)
    repo.save(archived)

    assert repo.get(WEEK) == archived
