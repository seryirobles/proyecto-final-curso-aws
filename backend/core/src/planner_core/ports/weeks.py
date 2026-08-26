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

    def get_week(self, week: IsoWeek) -> Mapping[SlotRef, SlotContents]:
        """Returns an empty mapping for a week with no data yet — weeks are
        created lazily on first write (docs/data_model.md section 9)."""
        ...

    def save_slot(self, week: IsoWeek, slot: SlotRef, contents: SlotContents) -> None:
        """Overwrite one slot's contents. contents is already invariant-checked
        by SlotContents.__post_init__ before this is ever called."""
        ...

    def save_week(self, week: IsoWeek, plans: Mapping[SlotRef, SlotContents]) -> None:
        """Overwrite every slot at once — rollover's promote/init steps need
        a whole-week write, not fourteen slot writes (FR-MENU-06, out of covers,
        cited only as the caller this method exists for)."""
        ...
