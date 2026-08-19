"""ISO weeks in Europe/Madrid: week identity, days, meal slots and today-onward scoping."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import IntEnum
from typing import Final
from zoneinfo import ZoneInfo

from planner_core.domain.errors import PlannerError

MADRID: Final = ZoneInfo("Europe/Madrid")


class NaiveInstant(PlannerError):
    """Raised when an instant carries no UTC offset."""


class InvalidIsoWeek(PlannerError):
    """Raised when a week number does not exist in its ISO week-numbering year."""


class MealSlot(IntEnum):
    """The two meals planned per day. The value is numeroComida itself."""

    LUNCH = 1
    DINNER = 2


@dataclass(frozen=True)
class SlotRef:
    """One meal slot of one day."""

    day: date
    slot: MealSlot

    @property
    def day_number(self) -> int:
        # numeroDia is isocalendar().weekday (1..7), never date.weekday() (0..6).
        # The two differ by one, and mixing them lands Sunday in the next week's
        # partition while passing every test written on a Monday
        # (docs/data_model.md section 2).
        return self.day.isocalendar().weekday


@dataclass(frozen=True)
class WeekDay:
    """One day of a week, with its two meal slots."""

    day: date

    @property
    def day_number(self) -> int:
        return self.day.isocalendar().weekday

    @property
    def slots(self) -> tuple[SlotRef, SlotRef]:
        return (SlotRef(self.day, MealSlot.LUNCH), SlotRef(self.day, MealSlot.DINNER))


@dataclass(frozen=True)
class IsoWeek:
    """An ISO week, Monday through Sunday, identified by its ISO week-numbering year."""

    iso_year: int
    iso_week: int

    def __post_init__(self) -> None:
        try:
            date.fromisocalendar(self.iso_year, self.iso_week, 1)
        except ValueError as exc:
            raise InvalidIsoWeek(self.week_id) from exc

    @classmethod
    def containing(cls, day: date) -> IsoWeek:
        iso_year, iso_week, _ = day.isocalendar()
        return cls(iso_year, iso_week)

    @property
    def week_id(self) -> str:
        # idSemana takes the ISO week-numbering year, never the calendar year, and
        # pads the week number: keys sort as bytes, so W9 would sort after W10
        # (docs/data_model.md section 2).
        return f"{self.iso_year}-W{self.iso_week:02d}"

    @property
    def monday(self) -> date:
        return date.fromisocalendar(self.iso_year, self.iso_week, 1)

    @property
    def sunday(self) -> date:
        return date.fromisocalendar(self.iso_year, self.iso_week, 7)

    @property
    def date_range(self) -> tuple[date, date]:
        return (self.monday, self.sunday)

    @property
    def days(self) -> tuple[WeekDay, ...]:
        monday = self.monday
        return tuple(WeekDay(monday + timedelta(days=offset)) for offset in range(7))

    @property
    def slots(self) -> tuple[SlotRef, ...]:
        return tuple(slot for day in self.days for slot in day.slots)

    def following(self) -> IsoWeek:
        # Never iso_week + 1: ISO years hold 52 or 53 weeks, so the increment
        # overflows into a week that does not exist. Date arithmetic, then
        # re-derivation, needs no special case for either length.
        return IsoWeek.containing(self.monday + timedelta(days=7))


def civil_date(instant: datetime) -> date:
    """Return the Europe/Madrid civil date of an instant."""
    # utcoffset() is None, not tzinfo is None: a tzinfo whose utcoffset() returns
    # None is still a naive value, and the tzinfo check would wave it through.
    if instant.utcoffset() is None:
        raise NaiveInstant(repr(instant))
    return instant.astimezone(MADRID).date()


def current_week(today: date) -> IsoWeek:
    """Return the ISO week containing the given civil date."""
    return IsoWeek.containing(today)


def next_week(today: date) -> IsoWeek:
    """Return the ISO week immediately after the one containing the given civil date."""
    return current_week(today).following()


def slots_from(week: IsoWeek, first_day: date) -> tuple[SlotRef, ...]:
    """Return the week's slots for days on or after first_day, in day then slot order.

    The single implementation of "which slots are in scope" (FR-AI-11, FR-SHOP-05).
    Scoping is day-granular, not slot-granular: both slots of first_day survive,
    whatever the time of day (G-45).
    """
    return tuple(slot for slot in week.slots if slot.day >= first_day)
