"""The week repository port: persistence for SEMANA (docs/data_model.md section 1)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from planner_core.domain.calendar import IsoWeek, SlotRef
from planner_core.domain.candidate import SlotContents


@runtime_checkable
class WeekRepository(Protocol):
    """Persistence for a live week's slot contents. Operates at SlotContents
    granularity, not DynamoDB's per-item split (candidates vs. the DEFINITIVO
    pointer) — design.md section 9, rejected alternative A."""

    def current_version(self, week: IsoWeek) -> int:
        """This week's change marker (docs/data_model.md section 4.7, AP29).
        A real adapter reads it strongly-consistently, marker attribute only;
        0 for a week never written. No side effects (R2)."""
        ...

    def get_week(self, week: IsoWeek) -> Mapping[SlotRef, SlotContents]:
        """Returns an empty mapping for a week with no data yet — weeks are
        created lazily on first write (docs/data_model.md section 9)."""
        ...

    def save_slot(self, week: IsoWeek, slot: SlotRef, contents: SlotContents) -> int:
        """Overwrite one slot; return this week's marker as advanced by this
        write, bumped in the same operation (docs/data_model.md section 1.1/5.5)."""
        ...

    def save_week(self, week: IsoWeek, plans: Mapping[SlotRef, SlotContents]) -> int:
        """Overwrite every slot at once (rollover's promote/init, FR-MENU-06);
        return this week's marker as advanced by this write, bumped in the same
        operation (docs/data_model.md section 1.1/5.5)."""
        ...
