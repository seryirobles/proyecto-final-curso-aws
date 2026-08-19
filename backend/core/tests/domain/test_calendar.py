"""Tests for the ISO week calendar in Europe/Madrid.

Every instant below is an explicit ISO-8601 value with an explicit offset, fed
through FakeClock. Nothing here manipulates the host's TZ: on Windows
`time.tzset` does not exist, and in this environment every IANA name but UTC
silently falls back to Europe/Madrid, so a TZ sweep would pass for the wrong
reason. Correctness is proved by construction instead - see
specs/week_calendar/design.md section 6.2.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, tzinfo

import pytest
from support.fakes import FakeClock

from planner_core.domain.calendar import (
    MADRID,
    InvalidIsoWeek,
    IsoWeek,
    MealSlot,
    NaiveInstant,
    SlotRef,
    civil_date,
    current_week,
    next_week,
    slots_from,
)


class OffsetlessTz(tzinfo):
    """A tzinfo whose utcoffset() is None: still a naive value, despite tzinfo being set."""

    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return None

    def dst(self, dt: datetime | None) -> timedelta | None:
        return None

    def tzname(self, dt: datetime | None) -> str | None:
        return "offsetless"


def civil_date_at(iso_8601: str) -> date:
    return civil_date(FakeClock.at(iso_8601).now())


def week_id_at(iso_8601: str) -> str:
    return current_week(civil_date_at(iso_8601)).week_id


# --- civil date and timezone -------------------------------------------------


def test_civil_date_rejects_a_naive_instant() -> None:
    """R3."""
    with pytest.raises(NaiveInstant):
        civil_date(datetime(2026, 7, 16, 12, 0))

    with pytest.raises(NaiveInstant):
        civil_date(datetime(2026, 7, 16, 12, 0, tzinfo=OffsetlessTz()))


def test_civil_date_uses_madrid_not_utc() -> None:
    """R4: the conversion is not a no-op - these instants differ in date by zone."""
    assert civil_date_at("2026-07-19T21:59:59+00:00") == date(2026, 7, 19)
    assert civil_date_at("2026-07-19T22:00:00+00:00") == date(2026, 7, 20)

    assert civil_date_at("2026-01-18T22:59:59+00:00") == date(2026, 1, 18)
    assert civil_date_at("2026-01-18T23:00:00+00:00") == date(2026, 1, 19)


def test_the_same_moment_in_any_offset_gives_the_same_civil_date() -> None:
    """R5: one absolute moment, three offsets, one answer."""
    same_moment = (
        "2026-07-19T22:00:00+00:00",
        "2026-07-20T03:00:00+05:00",
        "2026-07-19T14:00:00-08:00",
    )

    days = {civil_date_at(instant) for instant in same_moment}
    weeks = {week_id_at(instant) for instant in same_moment}
    scopes = {
        slots_from(current_week(civil_date_at(instant)), civil_date_at(instant))
        for instant in same_moment
    }

    assert days == {date(2026, 7, 20)}
    assert weeks == {"2026-W30"}
    assert len(scopes) == 1
    assert len(scopes.pop()) == 14


# --- week identity -----------------------------------------------------------


def test_current_week_is_the_iso_week_containing_today() -> None:
    """R6."""
    assert week_id_at("2026-07-19T21:59:59+00:00") == "2026-W29"
    assert week_id_at("2026-07-19T22:00:00+00:00") == "2026-W30"

    assert week_id_at("2026-01-18T22:59:59+00:00") == "2026-W03"
    assert week_id_at("2026-01-18T23:00:00+00:00") == "2026-W04"


def test_next_week_is_the_week_after_the_current_one() -> None:
    """R7, R21: 53-week and 52-week ISO years alike, with no special case."""
    assert next_week(date(2026, 7, 16)).week_id == "2026-W30"

    assert next_week(date(2026, 12, 31)).week_id == "2027-W01"
    assert next_week(date(2027, 1, 1)).week_id == "2027-W01"
    assert next_week(date(2020, 12, 31)).week_id == "2021-W01"
    assert next_week(date(2027, 12, 27)).week_id == "2028-W01"

    assert next_week(date(2026, 7, 16)) == current_week(date(2026, 7, 16)).following()


def test_week_id_uses_the_iso_year_and_pads_the_week_number() -> None:
    """R8, R21: date.year would give 2025-W01 and 2027-W53, one of which does not exist."""
    assert current_week(date(2025, 12, 31)).week_id == "2026-W01"
    assert date(2025, 12, 31).year == 2025

    assert current_week(date(2027, 1, 1)).week_id == "2026-W53"
    assert date(2027, 1, 1).year == 2027

    assert IsoWeek(2026, 1).week_id == "2026-W01"
    assert IsoWeek(2026, 9).week_id == "2026-W09"
    assert IsoWeek(2026, 53).week_id == "2026-W53"


def test_a_week_number_absent_from_its_iso_year_is_rejected() -> None:
    """R9."""
    assert IsoWeek(2026, 53).week_id == "2026-W53"

    for iso_year, iso_week in ((2027, 53), (2026, 0), (2026, 54)):
        with pytest.raises(InvalidIsoWeek):
            IsoWeek(iso_year, iso_week)


# --- week shape --------------------------------------------------------------


def test_a_week_has_seven_days_from_monday_to_sunday() -> None:
    """R10."""
    days = IsoWeek(2026, 29).days

    assert len(days) == 7
    assert days[0].day == date(2026, 7, 13)
    assert days[-1].day == date(2026, 7, 19)
    assert [day.day for day in days] == [date(2026, 7, 13) + timedelta(days=n) for n in range(7)]


def test_day_numbers_run_one_for_monday_to_seven_for_sunday() -> None:
    """R11: date.weekday() would report Sunday as 6 (docs/data_model.md section 2)."""
    days = IsoWeek(2026, 29).days

    assert [day.day_number for day in days] == [1, 2, 3, 4, 5, 6, 7]

    sunday = days[-1]
    assert sunday.day == date(2026, 7, 19)
    assert sunday.day_number == 7
    assert sunday.day.weekday() == 6

    assert SlotRef(date(2026, 7, 19), MealSlot.DINNER).day_number == 7


def test_each_day_offers_lunch_then_dinner() -> None:
    """R12."""
    monday = IsoWeek(2026, 29).days[0]

    assert len(monday.slots) == 2
    assert [slot.slot for slot in monday.slots] == [MealSlot.LUNCH, MealSlot.DINNER]
    assert [int(slot.slot) for slot in monday.slots] == [1, 2]
    assert all(slot.day == date(2026, 7, 13) for slot in monday.slots)


def test_a_week_has_fourteen_slots_ordered_by_day_then_slot() -> None:
    """R13."""
    slots = IsoWeek(2026, 29).slots

    assert len(slots) == 14
    assert [(slot.day_number, int(slot.slot)) for slot in slots] == [
        (day_number, meal) for day_number in range(1, 8) for meal in (1, 2)
    ]
    assert slots[0] == SlotRef(date(2026, 7, 13), MealSlot.LUNCH)
    assert slots[-1] == SlotRef(date(2026, 7, 19), MealSlot.DINNER)


def test_week_date_range_runs_monday_to_sunday() -> None:
    """R15, R21: 2026-W53 spans two calendar years, and the UI label has to survive it."""
    assert IsoWeek(2026, 29).date_range == (date(2026, 7, 13), date(2026, 7, 19))

    week_53 = IsoWeek(2026, 53)
    assert week_53.date_range == (date(2026, 12, 28), date(2027, 1, 3))
    assert week_53.monday == date(2026, 12, 28)
    assert week_53.sunday == date(2027, 1, 3)


# --- DST transitions ---------------------------------------------------------


def test_spring_forward_sunday_stays_in_its_week() -> None:
    """R20: Madrid moves CET -> CEST on the last Sunday of March, an ISO week's last day."""
    assert civil_date_at("2026-03-28T23:30:00+00:00") == date(2026, 3, 29)
    assert week_id_at("2026-03-28T23:30:00+00:00") == "2026-W13"

    assert civil_date_at("2026-03-29T01:30:00+00:00") == date(2026, 3, 29)
    assert week_id_at("2026-03-29T01:30:00+00:00") == "2026-W13"

    assert civil_date_at("2026-03-29T22:30:00+00:00") == date(2026, 3, 30)
    assert week_id_at("2026-03-29T22:30:00+00:00") == "2026-W14"


def test_autumn_ambiguous_hour_resolves_to_one_date_and_week() -> None:
    """R20: the repeated 02:30 local hour is two instants, and both land in the same week."""
    ambiguous = ("2026-10-25T00:30:00+00:00", "2026-10-25T01:30:00+00:00")

    for instant in ("2026-10-24T23:30:00+00:00", *ambiguous):
        assert civil_date_at(instant) == date(2026, 10, 25)
        assert week_id_at(instant) == "2026-W43"

    earlier = FakeClock.at(ambiguous[0]).now()
    later = FakeClock.at(ambiguous[1]).now()
    assert earlier != later
    assert earlier.astimezone(MADRID).time() == later.astimezone(MADRID).time()
    assert earlier.astimezone(MADRID).utcoffset() != later.astimezone(MADRID).utcoffset()

    assert civil_date_at("2026-10-25T23:00:00+00:00") == date(2026, 10, 26)
    assert week_id_at("2026-10-25T23:00:00+00:00") == "2026-W44"


# --- today-onward scoping ----------------------------------------------------


def test_scope_drops_days_before_the_given_day() -> None:
    """R17: Thursday of 2026-W29 leaves Thu, Fri, Sat, Sun - eight slots."""
    today = civil_date_at("2026-07-16T10:00:00+00:00")
    assert today == date(2026, 7, 16)

    week = current_week(today)
    assert week.week_id == "2026-W29"

    in_scope = slots_from(week, today)
    assert len(in_scope) == 8
    assert in_scope[0] == SlotRef(date(2026, 7, 16), MealSlot.LUNCH)
    assert in_scope[-1] == SlotRef(date(2026, 7, 19), MealSlot.DINNER)
    assert {slot.day for slot in in_scope} == {
        date(2026, 7, 16),
        date(2026, 7, 17),
        date(2026, 7, 18),
        date(2026, 7, 19),
    }


def test_scope_keeps_the_whole_week_when_the_day_precedes_its_monday() -> None:
    """R18: no second code path - the next week's Monday is always after today."""
    today = civil_date_at("2026-07-16T10:00:00+00:00")

    following = next_week(today)
    assert following.week_id == "2026-W30"
    assert slots_from(following, today) == following.slots
    assert len(slots_from(following, today)) == 14


def test_scope_keeps_both_slots_of_the_given_day() -> None:
    """R19: scoping is day-granular, not slot-granular (G-45)."""
    monday = civil_date_at("2026-07-13T05:00:00+00:00")
    assert monday == date(2026, 7, 13)
    assert len(slots_from(current_week(monday), monday)) == 14

    sunday_evening = civil_date_at("2026-07-19T20:00:00+00:00")
    assert sunday_evening == date(2026, 7, 19)

    in_scope = slots_from(current_week(sunday_evening), sunday_evening)
    assert in_scope == (
        SlotRef(date(2026, 7, 19), MealSlot.LUNCH),
        SlotRef(date(2026, 7, 19), MealSlot.DINNER),
    )
