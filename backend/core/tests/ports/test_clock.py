"""Tests for the Clock port, its default implementation, and the fake tests read time from."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from support.fakes import FakeClock

from planner_core.ports.clock import Clock, SystemClock


def test_fake_clock_satisfies_the_clock_port() -> None:
    """R1, R22: the only source of time is the port, and the fake implements it."""
    clock = FakeClock.at("2026-07-16T10:00:00+00:00")

    assert isinstance(clock, Clock)

    instant = clock.now()
    assert instant == datetime(2026, 7, 16, 10, 0, tzinfo=UTC)
    assert instant.utcoffset() == timedelta(0)

    assert clock.now() == instant
    assert clock.readings == 2


def test_system_clock_satisfies_the_clock_port_and_returns_an_aware_instant() -> None:
    """R23: the default implementation honours the port's timezone-aware contract.

    The only test in the suite permitted to read a real clock, which is why
    tests/test_no_ambient_time.py excludes exactly this module and no other.
    """
    clock = SystemClock()

    assert isinstance(clock, Clock)

    instant = clock.now()
    assert isinstance(instant, datetime)
    assert instant.utcoffset() is not None
    assert instant.utcoffset() == timedelta(0)
