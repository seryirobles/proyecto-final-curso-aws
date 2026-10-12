"""Whole-week generation requests: effective rules, target slots, idempotency key."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Protocol

from planner_core.domain.calendar import IsoWeek, SlotRef, slots_from
from planner_core.domain.candidate import SlotContents, definitive
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Recipe
from planner_core.domain.rules import CategoryCountRule, PinRule, RuleSet, apply_override
from planner_core.domain.text import normalize


class GenerationMode(StrEnum):
    """The three whole-week generation modes (FR-AI-03). Behavior is not this feature's."""

    LIBRARY_ONLY = "library_only"
    AI_ONLY = "ai_only"
    MIX = "mix"


@dataclass(frozen=True)
class RuleOverride:
    """A per-run override of the shared rules; any field left None inherits (FR-RULE-05)."""

    category_counts: tuple[CategoryCountRule, ...] | None = None
    pins: tuple[PinRule, ...] | None = None
    disabled_days: tuple[int, ...] | None = None


@dataclass(frozen=True)
class GenerationRequest:
    """A whole-week generation submission: which week, which mode, which override."""

    week: IsoWeek
    mode: GenerationMode
    rule_override: RuleOverride | None = None


@dataclass(frozen=True)
class SpecificationSource:
    """FR-AI-01: a recipe generated from the user's ingredients and tools."""

    ingredients: tuple[str, ...]
    tools: tuple[str, ...]


@dataclass(frozen=True)
class ReferenceSource:
    """FR-AI-02: a recipe generated from a library recipe plus extra specifications."""

    recipe_id: str
    extra_specifications: tuple[str, ...]


@dataclass(frozen=True)
class SingleRecipeRequest:
    """A single-recipe submission; `target` None means the library (FR-CAND-03)."""

    target: SlotRef | None
    source: SpecificationSource | ReferenceSource


@dataclass(frozen=True)
class PinnedTarget:
    """An unoccupied slot resolving deterministically to its pinned library meal."""

    slot: SlotRef
    recipe_id: str


@dataclass(frozen=True)
class SkippedPin:
    """A pin an existing definitive outranked; reported rather than applied silently (G-71)."""

    slot: SlotRef
    pin: PinRule


@dataclass(frozen=True)
class GenerationTargets:
    """The slots a generation run must act on, and the week's remaining category needs."""

    open_slots: tuple[SlotRef, ...]
    pinned_slots: tuple[PinnedTarget, ...]
    skipped_pins: tuple[SkippedPin, ...]
    remaining_category_counts: tuple[CategoryCountRule, ...]


@dataclass(frozen=True)
class GenerationPlan:
    """The full result of resolving one GenerationRequest: rules, targets, key."""

    effective_rules: RuleSet
    targets: GenerationTargets
    mode: GenerationMode
    idempotency_key: str


def effective_rules(shared: RuleSet, override: RuleOverride | None) -> RuleSet:
    """The run's effective rules; shared is never written to (FR-AI-05, FR-RULE-05)."""
    if override is None:
        return shared
    return apply_override(shared, override.category_counts, override.pins, override.disabled_days)


def resolve_targets(
    week: IsoWeek,
    rules: RuleSet,
    first_day: date,
    occupancy: Mapping[SlotRef, SlotContents],
) -> GenerationTargets:
    """Resolve which slots generation must act on, folding occupancy into the same pass.

    A slot's current occupancy, not the rules alone, decides whether it is a
    target: an existing definitive always outranks a pin, and the outranked
    pin is reported rather than silently dropped (G-71, design.md section 5).
    """
    candidate_slots = tuple(
        slot for slot in slots_from(week, first_day) if slot.day_number not in rules.disabled_days
    )

    day_by_number = {week_day.day_number: week_day.day for week_day in week.days}
    pin_by_slot: dict[SlotRef, PinRule] = {}
    for pin in rules.pins:
        day = day_by_number.get(pin.day)
        if day is not None:
            pin_by_slot[SlotRef(day, pin.slot)] = pin

    open_slots: list[SlotRef] = []
    pinned_slots: list[PinnedTarget] = []
    skipped_pins: list[SkippedPin] = []

    for slot in candidate_slots:
        plan = occupancy.get(slot, SlotContents())
        occupant = definitive(plan)
        resolved_pin = pin_by_slot.get(slot)
        if occupant is not None:
            if resolved_pin is not None:
                skipped_pins.append(SkippedPin(slot=slot, pin=resolved_pin))
            continue
        if resolved_pin is not None:
            pinned_slots.append(PinnedTarget(slot=slot, recipe_id=resolved_pin.recipe_id))
        else:
            open_slots.append(slot)

    # A second, independent pass over the WHOLE occupancy (R15): a definitive
    # on a disabled or past day still counts toward the week's final state.
    occupied_counts = Counter(
        occupant.meal.category
        for plan in occupancy.values()
        if (occupant := definitive(plan)) is not None
    )
    remaining_category_counts = tuple(
        CategoryCountRule(
            category=rule.category, count=max(0, rule.count - occupied_counts[rule.category])
        )
        for rule in rules.category_counts
    )

    return GenerationTargets(
        open_slots=tuple(open_slots),
        pinned_slots=tuple(pinned_slots),
        skipped_pins=tuple(skipped_pins),
        remaining_category_counts=remaining_category_counts,
    )


def idempotency_key(
    week: IsoWeek, targets: GenerationTargets, rules: RuleSet, mode: GenerationMode
) -> str:
    """A deterministic hash of week + target slots + effective rules + mode (FR-AI-08).

    Every collection is sorted before encoding so tuple order never affects
    the hash. mode is a fourth payload field by explicit human override of
    design.md section 9 gate question 3 (2026-08-26).
    """
    slot_ids = sorted(
        [(slot.day.isoformat(), slot.slot.value) for slot in targets.open_slots]
        + [(target.slot.day.isoformat(), target.slot.slot.value) for target in targets.pinned_slots]
    )
    category_counts = sorted((rule.category.value, rule.count) for rule in rules.category_counts)
    pins = sorted((pin.day, pin.slot.value, pin.recipe_id) for pin in rules.pins)
    disabled_days = sorted(rules.disabled_days)

    payload = {
        "week": week.week_id,
        "slots": slot_ids,
        "category_counts": category_counts,
        "pins": pins,
        "disabled_days": disabled_days,
        "mode": mode.value,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_plan(
    request: GenerationRequest,
    shared_rules: RuleSet,
    first_day: date,
    occupancy: Mapping[SlotRef, SlotContents],
) -> GenerationPlan:
    """Compose effective_rules, resolve_targets and idempotency_key for one request."""
    rules = effective_rules(shared_rules, request.rule_override)
    targets = resolve_targets(request.week, rules, first_day, occupancy)
    key = idempotency_key(request.week, targets, rules, request.mode)
    return GenerationPlan(
        effective_rules=rules, targets=targets, mode=request.mode, idempotency_key=key
    )


def single_recipe_key(request: SingleRecipeRequest, attempt: int) -> str:
    """Hash of scope, source and attempt; lists sorted so order is moot (FR-AI-08, G-92)."""
    target = request.target
    scope: dict[str, object] | str = (
        "library"
        if target is None
        else {
            "week": IsoWeek.containing(target.day).week_id,
            "day": target.day_number,
            "slot": target.slot.value,
        }
    )
    source = request.source
    payload_source: dict[str, object]
    if isinstance(source, SpecificationSource):
        payload_source = {
            "kind": "specification",
            "ingredients": sorted(source.ingredients),
            "tools": sorted(source.tools),
        }
    else:
        payload_source = {
            "kind": "reference",
            "recipe_id": source.recipe_id,
            "extra_specifications": sorted(source.extra_specifications),
        }
    payload = {"type": "recipe", "scope": scope, "source": payload_source, "attempt": attempt}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class SlotStatus(StrEnum):
    """One open slot's progress in a whole-week run (FR-AI-12)."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class RunStatus(StrEnum):
    """A whole-week run's status; `pending` until a worker claims it (FR-AI-12)."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True)
class SlotError:
    """Why a slot failed: a `GenerationFailureReason` value and its es-ES message."""

    code: str
    message: str


@dataclass(frozen=True)
class SlotProgress:
    """One slot's entry in a run; `error` is set only when `status` is ERROR."""

    day: int
    slot: int
    status: SlotStatus
    error: SlotError | None = None


@dataclass(frozen=True)
class GenerationSnapshot:
    """What a run was submitted with, stored so a retry reproduces it (FR-AI-05)."""

    week: IsoWeek
    mode: GenerationMode
    rules: RuleSet
    prompt_version_id: str


def run_status(slots: Sequence[SlotProgress]) -> RunStatus:
    """The run's status from its slot entries (FR-AI-12); no slots means completed."""
    statuses = {progress.status for progress in slots}
    if statuses & {SlotStatus.PENDING, SlotStatus.RUNNING}:
        return RunStatus.RUNNING
    if SlotStatus.ERROR not in statuses:
        return RunStatus.COMPLETED
    return RunStatus.PARTIAL if SlotStatus.DONE in statuses else RunStatus.FAILED


class _LibraryEntry(Protocol):
    """The shape `select_library_fill` needs of a library recipe (ports.recipes.LibraryRecipe)."""

    @property
    def id(self) -> str: ...

    @property
    def recipe(self) -> Recipe: ...


def reduce_needs(
    needs: tuple[CategoryCountRule, ...], picked: Iterable[IngredientCategory]
) -> tuple[CategoryCountRule, ...]:
    """Subtract the picked categories from the remaining counts, flooring at 0 (FR-AI-04)."""
    taken = Counter(picked)
    return tuple(
        CategoryCountRule(category=rule.category, count=max(0, rule.count - taken[rule.category]))
        for rule in needs
    )


def select_library_fill[Entry: _LibraryEntry](
    open_slots: Sequence[SlotRef],
    library: Sequence[Entry],
    needs: tuple[CategoryCountRule, ...],
    used_names: frozenset[str],
    seed: str,
) -> dict[SlotRef, Entry]:
    """Pick a library recipe per open slot, chronologically (FR-AI-03, FR-AI-04, FR-AI-08).

    The pool is the library minus recipes whose case-folded name is used,
    sorted by id then shuffled with `seed`, so equal inputs give equal picks.
    """
    pool = [
        e for e in sorted(library, key=lambda e: e.id) if normalize(e.recipe.name) not in used_names
    ]
    random.Random(seed).shuffle(pool)
    remaining = {rule.category: rule.count for rule in needs}
    taken = set(used_names)
    picks: dict[SlotRef, Entry] = {}
    for slot in open_slots:
        candidates = [e for e in pool if normalize(e.recipe.name) not in taken]
        chosen = next(
            (
                e
                for rule in needs
                if remaining[rule.category] > 0
                for e in candidates
                if e.recipe.category == rule.category
            ),
            None,
        )
        if chosen is None and candidates:
            chosen = candidates[0]
        if chosen is None:
            continue
        picks[slot] = chosen
        taken.add(normalize(chosen.recipe.name))
        if chosen.recipe.category in remaining:
            remaining[chosen.recipe.category] = max(0, remaining[chosen.recipe.category] - 1)
    return picks
