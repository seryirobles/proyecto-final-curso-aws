"""Whole-week generation worker use case (FR-AI-03, FR-AI-09, FR-AI-12,
NFR-AI-01): claim, resolve the open slots, fill them from the library and/or
the AI per mode, record each slot's progress, then settle the run status.

Pinned-slot candidates are NOT this worker's job — feature 27's
generation_submission writes them synchronously at submit
(specs/ai_lambda/design.md section 3). Mode semantics and the progress
vocabulary: specs/week_generation_backend/design.md sections 1-4."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from uuid import uuid4

from planner_core.application.week_editing import add_slot_candidate
from planner_core.domain.ai_output import (
    GenerationFailure,
    GenerationFailureReason,
    accept_preview,
    build_generation_failure,
    validate_and_preview,
)
from planner_core.domain.ai_prompt import CategoryPrompt, build_category_prompt
from planner_core.domain.calendar import IsoWeek, SlotRef
from planner_core.domain.candidate import SlotContents, definitive, new_candidate
from planner_core.domain.generation import (
    GenerationMode,
    GenerationRequest,
    RunStatus,
    SlotError,
    SlotProgress,
    SlotStatus,
    reduce_needs,
    resolve_targets,
    run_status,
    select_library_fill,
)
from planner_core.domain.recipe import snapshot
from planner_core.domain.rules import CategoryCountRule, RuleSet
from planner_core.domain.text import normalize
from planner_core.ports.ai_provider import AiProvider, AiProviderError
from planner_core.ports.generation_gate import GenerationGate
from planner_core.ports.generation_queue import GenerationResultSink
from planner_core.ports.recipes import LibraryRecipe, RecipeRepository
from planner_core.ports.weeks import WeekRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WeekGenerationOutcome:
    """Whether this worker claimed the message, the run status settled (None
    when the claim was lost or slots are still in flight) and the outcome of
    every slot it processed."""

    claimed: bool
    terminal_status: RunStatus | None
    per_slot: tuple[SlotProgress, ...]


@dataclass(frozen=True)
class _Run:
    """The collaborators and constants shared by every slot of one run."""

    key: str
    week: IsoWeek
    mode: GenerationMode
    prompt_version_id: str
    author: str
    provider: AiProvider
    weeks: WeekRepository
    recipes: RecipeRepository
    queue: GenerationResultSink
    gate: GenerationGate


def settle_run(key: str, sink: GenerationResultSink) -> RunStatus | None:
    """Record the run status once no slot is pending or running (R27, R51).

    Idempotent: two simultaneous finishers compute the same terminal value.
    """
    stored = sink.stored_generation(key)
    if stored is None:
        return None
    status = run_status(stored.slots or ())
    if status is RunStatus.RUNNING:
        return None
    sink.record_status(key, status)
    return status


def _progress(slot: SlotRef, status: SlotStatus, error: SlotError | None = None) -> SlotProgress:
    return SlotProgress(slot.day_number, int(slot.slot.value), status, error)


def _error(slot: SlotRef, failure: GenerationFailure) -> SlotProgress:
    return _progress(slot, SlotStatus.ERROR, SlotError(failure.reason.value, failure.message))


def _write_library_candidate(run: _Run, slot: SlotRef, entry: LibraryRecipe) -> SlotProgress:
    current = run.weeks.get_week(run.week).get(slot, SlotContents())  # re-read at write time
    if definitive(current) is None:  # R14 — a definitive outranks; R13 — add only
        candidate = new_candidate(uuid4().hex, snapshot(entry.recipe), run.author)
        add_slot_candidate(run.week, slot, candidate, weeks=run.weeks)
    return _progress(slot, SlotStatus.DONE)


def _generate_with_ai(run: _Run, slot: SlotRef, prompt: CategoryPrompt) -> SlotProgress:
    if not run.gate.is_generation_enabled():  # R50, NFR-AI-01
        unavailable = build_generation_failure(GenerationFailureReason.GENERATION_UNAVAILABLE)
        return _error(slot, unavailable)

    run.queue.record_slot(run.key, _progress(slot, SlotStatus.RUNNING))  # R18
    try:
        raw = run.provider.generate(prompt)
    except AiProviderError as error:  # per-slot isolation
        logger.warning("AI provider failed for %s: %s", run.key, error)
        return _error(slot, build_generation_failure(GenerationFailureReason.INVALID_OUTPUT))

    outcome = validate_and_preview(raw)
    if isinstance(outcome, GenerationFailure):
        logger.warning("AI output rejected for %s: %s; %.500r", run.key, outcome.cause, raw)
        return _error(slot, outcome)

    current = run.weeks.get_week(run.week).get(slot, SlotContents())
    if definitive(current) is None:  # a definitive outranks the candidate
        meal = snapshot(accept_preview(outcome.preview))
        add_slot_candidate(
            run.week, slot, new_candidate(uuid4().hex, meal, run.author), weeks=run.weeks
        )
    return _progress(slot, SlotStatus.DONE)


def _fill_slots(
    run: _Run,
    slots: Sequence[SlotRef],
    occupancy: dict[SlotRef, SlotContents],
    needs: tuple[CategoryCountRule, ...],
) -> list[SlotProgress]:
    """Library fill for every slot first (R5), then the AI for the rest (R6)."""
    picks: dict[SlotRef, LibraryRecipe] = {}
    if run.mode is not GenerationMode.AI_ONLY:  # R4 — ai_only never reads the library
        used = frozenset(
            normalize(c.meal.name) for contents in occupancy.values() for c in contents.candidates
        )
        picks = select_library_fill(slots, run.recipes.list_all(), needs, used, run.key)

    results: list[SlotProgress] = []
    for slot in slots:
        if slot in picks:
            progress = _write_library_candidate(run, slot, picks[slot])
            run.queue.record_slot(run.key, progress)  # R19
            results.append(progress)

    prompt = build_category_prompt(
        reduce_needs(needs, (entry.recipe.category for entry in picks.values())),  # R12
        run.prompt_version_id,
    )
    for slot in slots:
        if slot in picks:
            continue
        if run.mode is GenerationMode.LIBRARY_ONLY:  # R1, R3 — no gate, no provider
            insufficient = GenerationFailureReason.INSUFFICIENT_LIBRARY_RECIPES
            progress = _error(slot, build_generation_failure(insufficient))
        else:
            progress = _generate_with_ai(run, slot, prompt)
        run.queue.record_slot(run.key, progress)  # R19, R20
        results.append(progress)
    return results


def run_week_generation(
    idempotency_key: str,
    request: GenerationRequest,
    effective_rules: RuleSet,
    prompt_version_id: str,
    author: str,
    first_day: date,
    *,
    provider: AiProvider,
    weeks: WeekRepository,
    recipes: RecipeRepository,
    queue: GenerationResultSink,
    gate: GenerationGate,
) -> WeekGenerationOutcome:
    """effective_rules / prompt_version_id / author arrive enriched on the SQS
    message; no RuleRepository or ConfigPort is read here. `recipes` is read-only."""
    if not queue.claim(idempotency_key):  # redelivery guard
        return WeekGenerationOutcome(claimed=False, terminal_status=None, per_slot=())

    occupancy = dict(weeks.get_week(request.week))
    targets = resolve_targets(request.week, effective_rules, first_day, occupancy)
    queue.begin_slots(  # R17 — every open slot pending before any is processed
        idempotency_key, tuple(_progress(s, SlotStatus.PENDING) for s in targets.open_slots)
    )
    run = _Run(
        key=idempotency_key,
        week=request.week,
        mode=request.mode,
        prompt_version_id=prompt_version_id,
        author=author,
        provider=provider,
        weeks=weeks,
        recipes=recipes,
        queue=queue,
        gate=gate,
    )
    results = _fill_slots(run, targets.open_slots, occupancy, targets.remaining_category_counts)
    status = settle_run(idempotency_key, queue)
    return WeekGenerationOutcome(claimed=True, terminal_status=status, per_slot=tuple(results))


def run_slot_retry(
    idempotency_key: str,
    day: int,
    slot_number: int,
    request: GenerationRequest,
    effective_rules: RuleSet,
    prompt_version_id: str,
    author: str,
    first_day: date,
    *,
    provider: AiProvider,
    weeks: WeekRepository,
    recipes: RecipeRepository,
    queue: GenerationResultSink,
    gate: GenerationGate,
) -> WeekGenerationOutcome:
    """Re-run one slot of a stored run under the parent's mode and rules (R44-R53)."""
    if not queue.claim_slot(idempotency_key, day, slot_number):  # R47, R48
        return WeekGenerationOutcome(claimed=False, terminal_status=None, per_slot=())

    occupancy = dict(weeks.get_week(request.week))
    targets = resolve_targets(request.week, effective_rules, first_day, occupancy)
    target = next(
        (s for s in targets.open_slots if s.day_number == day and int(s.slot.value) == slot_number),
        None,
    )
    run = _Run(
        key=idempotency_key,
        week=request.week,
        mode=request.mode,
        prompt_version_id=prompt_version_id,
        author=author,
        provider=provider,
        weeks=weeks,
        recipes=recipes,
        queue=queue,
        gate=gate,
    )
    if target is None:  # no longer open since the retry was accepted: nothing to generate (R14)
        done = SlotProgress(day, slot_number, SlotStatus.DONE)
        queue.record_slot(idempotency_key, done)
        results = [done]
    else:
        results = _fill_slots(run, (target,), occupancy, targets.remaining_category_counts)
    status = settle_run(idempotency_key, queue)
    return WeekGenerationOutcome(claimed=True, terminal_status=status, per_slot=tuple(results))
