"""Tests for the domain error base class.

`errors.py` declares no behaviour, only a lineage: every domain error descends
from `PlannerError`, so the handler layer can catch the whole family by its base
(`docs/conventions.md` section Error handling) and features 3-13 inherit from a
single place. That lineage is what this module asserts.

`NaiveInstant` is raised directly rather than provoked through `civil_date`:
this module is about the exception hierarchy, not about time, and the scan in
`test_no_ambient_time.py` requires any test that reads a civil date to obtain it
from `FakeClock`.
"""

from __future__ import annotations

import pytest

from planner_core.domain.calendar import InvalidIsoWeek, IsoWeek, NaiveInstant
from planner_core.domain.errors import PlannerError


def test_planner_error_is_a_plain_exception() -> None:
    """R3, R9: the base is raisable and catchable like any other exception."""
    assert issubclass(PlannerError, Exception)

    with pytest.raises(PlannerError):
        raise PlannerError("boom")


def test_every_domain_error_descends_from_planner_error() -> None:
    """R3, R9: later features extend this list; the base they extend does not change."""
    assert issubclass(NaiveInstant, PlannerError)
    assert issubclass(InvalidIsoWeek, PlannerError)

    for error in (NaiveInstant, InvalidIsoWeek):
        with pytest.raises(PlannerError):
            raise error("boom")


def test_a_domain_error_raised_by_real_code_is_caught_by_the_base() -> None:
    """R9: how the handler layer catches domain failures - by the base, never by name."""
    with pytest.raises(PlannerError) as raised:
        IsoWeek(2026, 54)

    assert isinstance(raised.value, InvalidIsoWeek)
