"""Whole-week generation submission (AP25/AP26, FR-AI-08): derive the
idempotency key through domain/generation, return an already-stored result on a
hit, otherwise write the deterministic pinned-slot candidates and hand the
request off once (design.md section 3b/3c)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import uuid4

from planner_core.application.prompt_version import resolve_active_prompt_version
from planner_core.application.week_editing import add_slot_candidate
from planner_core.domain.candidate import new_candidate
from planner_core.domain.generation import GenerationRequest, GenerationTargets, build_plan
from planner_core.domain.recipe import snapshot
from planner_core.ports.config import ConfigPort
from planner_core.ports.generation_queue import GenerationQueue, StoredGeneration
from planner_core.ports.recipes import RecipeNotFound, RecipeRepository
from planner_core.ports.rules import RuleRepository
from planner_core.ports.weeks import WeekRepository


@dataclass(frozen=True)
class SubmissionOutcome:
    """The derived idempotency id and resolved targets, plus either the stored
    record (idempotent hit, nothing enqueued) or None (freshly enqueued)."""

    idempotency_key: str
    targets: GenerationTargets
    stored: StoredGeneration | None
    enqueued: bool


def submit_generation(
    request: GenerationRequest,
    first_day: date,
    *,
    weeks: WeekRepository,
    rules: RuleRepository,
    queue: GenerationQueue,
    recipes: RecipeRepository,
    author: str,
    config: ConfigPort,
) -> SubmissionOutcome:
    """R27, R28, R40-R43. first_day is the caller-resolved "today onward" scope
    boundary (FR-AI-11); no clock is read here (tier-1 ruling). The active prompt
    version is resolved through feature 24's guard (finding 2): an unset or
    unknown key raises UnknownPromptVersion here, before anything is enqueued."""
    plan = build_plan(request, rules.get(), first_day, weeks.get_week(request.week))
    stored = queue.stored_generation(plan.idempotency_key)
    if stored is not None:
        # R43: the pinned-slot candidates were written on the original fresh submit.
        return SubmissionOutcome(
            idempotency_key=plan.idempotency_key,
            targets=plan.targets,
            stored=stored,
            enqueued=False,
        )
    version = resolve_active_prompt_version(config)  # finding 2 — fail before any write
    # R41/R42: the pinned-slot candidates are a deterministic library-snapshot
    # copy (no model call) — written before the hand-off so they land regardless
    # of whether the queue accepts the message (design.md section 3c).
    for pinned in plan.targets.pinned_slots:
        entry = recipes.get(pinned.recipe_id)
        if entry is None:
            raise RecipeNotFound(pinned.recipe_id)
        candidate = new_candidate(uuid4().hex, snapshot(entry.recipe), author)
        add_slot_candidate(request.week, pinned.slot, candidate, weeks=weeks)
    queue.submit(
        plan.idempotency_key,
        request,
        effective_rules=plan.effective_rules,
        prompt_version_id=version.version_id,
        author=author,
    )
    return SubmissionOutcome(
        idempotency_key=plan.idempotency_key, targets=plan.targets, stored=None, enqueued=True
    )
