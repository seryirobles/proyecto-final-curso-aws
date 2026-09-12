"""Candidate CRUD and definitive selection for a live week (AP10-AP13).

The WeekRepository works at SlotContents granularity, so each mutation loads
the slot, applies one domain/candidate mutator, writes the slot back, and
returns the week's change marker (R9)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from planner_core.domain.calendar import IsoWeek, SlotRef
from planner_core.domain.candidate import (
    Candidate,
    SlotContents,
    add_candidate,
    clear_definitive,
    edit_candidate,
    promote,
    remove_candidate,
)
from planner_core.domain.recipe import MealSnapshot
from planner_core.ports.weeks import WeekRepository


@dataclass(frozen=True)
class AddCandidateOutcome:
    """The write's marker plus the same-name warning add never blocks on (G-59)."""

    marker: int
    duplicate_warning: bool


@dataclass(frozen=True)
class WeekView:
    """AP8 read: the week's slot contents plus its change marker (R34). The
    marker is read before the payload (R35). GET /v1/weeks/{weekId}/summary is
    a projection of this and shares the marker."""

    slots: Mapping[SlotRef, SlotContents]
    marker: int


def load_week(week: IsoWeek, *, weeks: WeekRepository) -> WeekView:
    """AP8 — the whole week's slot contents and its marker, marker read first."""
    marker = weeks.current_version(week)  # marker before payload (R35)
    return WeekView(slots=weeks.get_week(week), marker=marker)


def poll_marker(week: IsoWeek, *, weeks: WeekRepository) -> int:
    """Feature 26's conditional-GET short-circuit: the marker alone, without
    `get_week`'s payload — keeps the marker name out of `planner_api/routing.py`
    (test_change_marker_is_not_a_write_condition.py's R12 scan, feature 27)."""
    return weeks.current_version(week)


def load_candidate(
    week: IsoWeek, slot: SlotRef, candidate_id: str, *, weeks: WeekRepository
) -> Candidate | None:
    """AP10 — one candidate of one slot, or None."""
    plan = weeks.get_week(week).get(slot, SlotContents())
    return next((c for c in plan.candidates if c.id == candidate_id), None)


def _slot(week: IsoWeek, slot: SlotRef, weeks: WeekRepository) -> SlotContents:
    return weeks.get_week(week).get(slot, SlotContents())


def add_slot_candidate(
    week: IsoWeek, slot: SlotRef, candidate: Candidate, *, weeks: WeekRepository
) -> AddCandidateOutcome:
    """AP13 (add)."""
    result = add_candidate(_slot(week, slot, weeks), candidate)
    marker = weeks.save_slot(week, slot, result.plan)
    return AddCandidateOutcome(marker=marker, duplicate_warning=result.duplicate_warning)


def edit_slot_candidate(
    week: IsoWeek, slot: SlotRef, candidate_id: str, meal: MealSnapshot, *, weeks: WeekRepository
) -> int:
    """AP13 (edit in place)."""
    plan = edit_candidate(_slot(week, slot, weeks), candidate_id, meal)
    return weeks.save_slot(week, slot, plan)


def delete_slot_candidate(
    week: IsoWeek, slot: SlotRef, candidate_id: str, *, weeks: WeekRepository
) -> int:
    """AP12."""
    plan = remove_candidate(_slot(week, slot, weeks), candidate_id)
    return weeks.save_slot(week, slot, plan)


def set_definitive(
    week: IsoWeek, slot: SlotRef, candidate_id: str, *, weeks: WeekRepository
) -> int:
    """AP11 (set)."""
    plan = promote(_slot(week, slot, weeks), candidate_id)
    return weeks.save_slot(week, slot, plan)


def clear_slot_definitive(week: IsoWeek, slot: SlotRef, *, weeks: WeekRepository) -> int:
    """AP11 (clear) — FR-CAND-08."""
    plan = clear_definitive(_slot(week, slot, weeks))
    return weeks.save_slot(week, slot, plan)
