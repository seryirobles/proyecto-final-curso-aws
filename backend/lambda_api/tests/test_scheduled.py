"""scheduled.py: the EventBridge rollover entry point (R32-R34) and the no-op
`ArchiveRepository` archive is parked behind (R40, R41)."""

from __future__ import annotations

import pytest
from _helpers import make_deps
from planner_core.domain.calendar import IsoWeek
from planner_core.domain.rollover import ArchivedWeek
from planner_core.domain.shopping import ShoppingItem
from planner_core.domain.units import Unit

from planner_api.scheduled import handle
from planner_api.wiring import NoOpArchiveRepository


def test_rollover_cleans_checked_items_and_keeps_unchecked_ones() -> None:
    deps = make_deps()
    deps.shopping.save_item(
        ShoppingItem(id="s-1", name="arroz", quantity=1, unit=Unit.GRAM, checked=True)
    )
    deps.shopping.save_item(
        ShoppingItem(id="s-2", name="pasta", quantity=1, unit=Unit.GRAM, checked=False)
    )

    result = handle({}, deps)

    ids = {item.id for item in deps.shopping.list_items()}
    assert ids == {"s-2"}
    assert result["status"] == "ok"


def test_rerunning_rollover_for_the_same_boundary_changes_nothing_further() -> None:
    deps = make_deps()
    deps.shopping.save_item(
        ShoppingItem(id="s-1", name="arroz", quantity=1, unit=Unit.GRAM, checked=True)
    )

    handle({}, deps)
    version_after_first_run = deps.shopping.current_version()
    handle({}, deps)

    assert deps.shopping.current_version() == version_after_first_run
    assert list(deps.shopping.list_items()) == []


def test_the_noop_archive_repository_retains_nothing() -> None:
    repo = NoOpArchiveRepository()
    week = IsoWeek(2026, 33)

    repo.save(ArchivedWeek(week=week, plans={}, shopping_snapshot=()))

    assert repo.get(week) is None


def test_the_noop_archive_repository_logs_the_discarded_record(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level("INFO", logger="planner_api")
    repo = NoOpArchiveRepository()
    week = IsoWeek(2026, 33)

    repo.save(ArchivedWeek(week=week, plans={}, shopping_snapshot=()))

    logged = [r for r in caplog.records if r.name == "planner_api"]
    assert any(r.__dict__.get("weekId") == "2026-W33" for r in logged)
