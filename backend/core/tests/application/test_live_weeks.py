"""Tests for resolving the two live weeks from one reading of the clock."""

from __future__ import annotations

from datetime import date

from support.fakes import FakeClock

from planner_core.application.live_weeks import LiveWeek, resolve_live_weeks

REFERENCE = "2026-07-16T10:00:00+00:00"  # Thursday 2026-07-16 12:00 in Madrid


def test_live_weeks_come_from_a_single_clock_reading() -> None:
    """R14: two readings could straddle midnight and return a non-adjacent pair."""
    clock = FakeClock.at(REFERENCE)

    live = resolve_live_weeks(clock)

    assert clock.readings == 1
    assert live.today == date(2026, 7, 16)
    assert live.current_week.week_id == "2026-W29"
    assert live.next_week == live.current_week.following()
    assert live.next_week.week_id == "2026-W30"


def test_live_week_labels_are_stable_identifiers() -> None:
    """R16: an enum, not display text. The es-ES label belongs to the frontend."""
    assert list(LiveWeek) == [LiveWeek.CURRENT, LiveWeek.NEXT]
    assert LiveWeek.CURRENT.value == "current"
    assert LiveWeek.NEXT.value == "next"
    assert all(member.value.isascii() for member in LiveWeek)


def test_current_week_scopes_from_today_and_next_week_scopes_whole() -> None:
    """R14, R17, R18, R19: one rule, two weeks, no branch."""
    live = resolve_live_weeks(FakeClock.at(REFERENCE))

    current = live.slots_in_scope(LiveWeek.CURRENT)
    following = live.slots_in_scope(LiveWeek.NEXT)

    assert len(current) == 8
    assert current[0].day == date(2026, 7, 16)
    assert min(slot.day for slot in current) == date(2026, 7, 16)

    assert len(following) == 14
    assert following == live.next_week.slots

    assert live.week(LiveWeek.CURRENT) is live.current_week
    assert live.week(LiveWeek.NEXT) is live.next_week


def test_live_weeks_expose_each_week_date_range() -> None:
    """R15: the Monday-Sunday range every week label needs (FR-UX-06)."""
    live = resolve_live_weeks(FakeClock.at(REFERENCE))

    assert live.date_range(LiveWeek.CURRENT) == (date(2026, 7, 13), date(2026, 7, 19))
    assert live.date_range(LiveWeek.NEXT) == (date(2026, 7, 20), date(2026, 7, 26))
