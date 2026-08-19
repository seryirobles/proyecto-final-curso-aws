"""The two live weeks, resolved from one reading of the clock."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from planner_core.domain.calendar import (
    IsoWeek,
    SlotRef,
    civil_date,
    current_week,
    next_week,
    slots_from,
)
from planner_core.ports.clock import Clock


class LiveWeek(Enum):
    """Which of the two planned weeks is meant.

    A stable identifier, never display text: the es-ES rendering of the
    current/next label belongs to the frontend messages module.
    """

    CURRENT = "current"
    NEXT = "next"


@dataclass(frozen=True)
class LiveWeeks:
    """The pair of weeks in play, plus the civil date they were derived from."""

    today: date
    current_week: IsoWeek
    next_week: IsoWeek

    def week(self, which: LiveWeek) -> IsoWeek:
        match which:
            case LiveWeek.CURRENT:
                return self.current_week
            case LiveWeek.NEXT:
                return self.next_week

    def date_range(self, which: LiveWeek) -> tuple[date, date]:
        return self.week(which).date_range

    def slots_in_scope(self, which: LiveWeek) -> tuple[SlotRef, ...]:
        # One rule, not two: today always precedes the next week's Monday, so all
        # fourteen of its slots survive without a second branch.
        return slots_from(self.week(which), self.today)


def resolve_live_weeks(clock: Clock) -> LiveWeeks:
    """Resolve both live weeks from a single reading of the clock.

    Reading twice could straddle midnight on a Sunday and return a current/next
    pair that is not adjacent, which is the disagreement every user must be
    protected from.
    """
    today = civil_date(clock.now())
    return LiveWeeks(today=today, current_week=current_week(today), next_week=next_week(today))
