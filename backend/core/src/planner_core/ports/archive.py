"""The archive repository port: persistence for a rolled-over week's frozen
record (FR-ARCH-01, FR-ARCH-02, out of covers; docs/data_model.md section 9)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from planner_core.domain.calendar import IsoWeek
from planner_core.domain.rollover import ArchivedWeek


@runtime_checkable
class ArchiveRepository(Protocol):
    """Persistence for ArchivedWeek — the menu and the shopping-list snapshot
    together, exactly as feature 13 produces it. No listing or browsing
    operation: FR-ARCH-04's reverse-chronological browse is out of this
    feature's scope and blocked on feature 19 (design.md section 11, gate
    question 4)."""

    def get(self, week: IsoWeek) -> ArchivedWeek | None: ...

    def save(self, archived: ArchivedWeek) -> None:
        """Overwrite, not create-only: idempotent so a rollover retry
        (FR-MENU-08, out of covers) can call this again safely."""
        ...
