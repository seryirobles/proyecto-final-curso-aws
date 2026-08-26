"""Slot contents: candidates, at most one definitive, and author attribution."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from typing import Final

from planner_core.domain.calendar import SlotRef
from planner_core.domain.errors import PlannerError
from planner_core.domain.recipe import MealSnapshot, Recipe
from planner_core.domain.text import normalize

UNKNOWN_USER_ID: Final[str] = "unknown-user"


class CandidateNotFound(PlannerError):
    """Raised when an operation targets a candidate id absent from the slot."""

    candidate_id: str

    def __init__(self, candidate_id: str) -> None:
        super().__init__(candidate_id)
        self.candidate_id = candidate_id


@dataclass(frozen=True)
class Candidate:
    """One authored meal proposal, addressable by a caller-supplied id (FR-CAND-04)."""

    id: str
    meal: MealSnapshot
    author: str


@dataclass(frozen=True)
class SlotContents:
    """A slot's candidates plus at most one definitive, held as a pointer (design.md section 5)."""

    candidates: tuple[Candidate, ...] = ()
    definitive_id: str | None = None

    def __post_init__(self) -> None:
        if self.definitive_id is None:
            return
        if not any(c.id == self.definitive_id for c in self.candidates):
            raise CandidateNotFound(self.definitive_id)


@dataclass(frozen=True)
class AddCandidateResult:
    """The plan after an add, plus whether the new candidate's name duplicates one already there."""

    plan: SlotContents
    duplicate_warning: bool


@dataclass(frozen=True)
class LibraryEntryResult:
    """The new Recipe built from a snapshot, plus whether its name duplicates an existing one."""

    recipe: Recipe
    duplicate_warning: bool


def new_candidate(id: str, meal: MealSnapshot, author: str) -> Candidate:
    """The single construction path for a candidate, whatever authoring source produced meal."""
    return Candidate(id=id, meal=meal, author=author)


def definitive(plan: SlotContents) -> Candidate | None:
    """The candidate plan.definitive_id points at, re-resolved on every call (G-67)."""
    for candidate in plan.candidates:
        if candidate.id == plan.definitive_id:
            return candidate
    return None


def add_candidate(plan: SlotContents, candidate: Candidate) -> AddCandidateResult:
    """Append candidate unconditionally; warn, never block, on a normalized name match (G-59)."""
    duplicate_warning = any(
        normalize(existing.meal.name) == normalize(candidate.meal.name)
        for existing in plan.candidates
    )
    new_plan = SlotContents(
        candidates=(*plan.candidates, candidate), definitive_id=plan.definitive_id
    )
    return AddCandidateResult(plan=new_plan, duplicate_warning=duplicate_warning)


def edit_candidate(plan: SlotContents, candidate_id: str, meal: MealSnapshot) -> SlotContents:
    """Replace the matching candidate's meal, preserving id, author and position (FR-CAND-01)."""
    if not any(c.id == candidate_id for c in plan.candidates):
        raise CandidateNotFound(candidate_id)
    candidates = tuple(
        Candidate(id=c.id, meal=meal, author=c.author) if c.id == candidate_id else c
        for c in plan.candidates
    )
    return SlotContents(candidates=candidates, definitive_id=plan.definitive_id)


def remove_candidate(plan: SlotContents, candidate_id: str) -> SlotContents:
    """Remove the matching candidate; silently clear a definitive pointer at it (design.md 5)."""
    if not any(c.id == candidate_id for c in plan.candidates):
        raise CandidateNotFound(candidate_id)
    candidates = tuple(c for c in plan.candidates if c.id != candidate_id)
    definitive_id = None if plan.definitive_id == candidate_id else plan.definitive_id
    return SlotContents(candidates=candidates, definitive_id=definitive_id)


def promote(plan: SlotContents, candidate_id: str) -> SlotContents:
    """Set candidate_id as the definitive, replacing any previous one. No promoter param (G-79)."""
    if not any(c.id == candidate_id for c in plan.candidates):
        raise CandidateNotFound(candidate_id)
    return SlotContents(candidates=plan.candidates, definitive_id=candidate_id)


def clear_definitive(plan: SlotContents) -> SlotContents:
    """Unset the definitive, leaving candidates unchanged (FR-CAND-08)."""
    return SlotContents(candidates=plan.candidates, definitive_id=None)


def summary(plans: Mapping[SlotRef, SlotContents]) -> tuple[tuple[SlotRef, Candidate], ...]:
    """Exactly the slots holding a definitive, each paired with it (FR-SUM-01)."""
    result: list[tuple[SlotRef, Candidate]] = []
    for slot_ref, plan in plans.items():
        candidate = definitive(plan)
        if candidate is not None:
            result.append((slot_ref, candidate))
    return tuple(result)


def to_library_entry(meal: MealSnapshot, existing_names: Iterable[str]) -> LibraryEntryResult:
    """Build a new Recipe from meal; warn, never block, on a same-name collision (G-26)."""
    recipe = Recipe(
        name=meal.name,
        ingredients=meal.ingredients,
        tools=meal.tools,
        procedure=meal.procedure,
        category=meal.category,
        servings=meal.servings,
        estimated_time=meal.estimated_time,
    )
    duplicate_warning = any(
        normalize(recipe.name) == normalize(existing) for existing in existing_names
    )
    return LibraryEntryResult(recipe=recipe, duplicate_warning=duplicate_warning)


def resolve_author(author_id: str, known_user_ids: AbstractSet[str]) -> str:
    """Return author_id unchanged if known, else the reserved placeholder (FR-SUM-03)."""
    if author_id in known_user_ids:
        return author_id
    return UNKNOWN_USER_ID
