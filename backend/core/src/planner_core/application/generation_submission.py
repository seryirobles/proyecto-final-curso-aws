"""Whole-week generation submission (AP25/AP26, FR-AI-08): derive the
idempotency key through domain/generation, return an already-stored result on a
hit, otherwise hand the request off once."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from planner_core.domain.generation import GenerationRequest, GenerationTargets, build_plan
from planner_core.ports.generation_queue import GenerationQueue, StoredGeneration
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
) -> SubmissionOutcome:
    """R27, R28. first_day is the caller-resolved "today onward" scope boundary
    (FR-AI-11); no clock is read here (tier-1 ruling)."""
    plan = build_plan(request, rules.get(), first_day, weeks.get_week(request.week))
    stored = queue.stored_generation(plan.idempotency_key)
    if stored is not None:
        return SubmissionOutcome(
            idempotency_key=plan.idempotency_key,
            targets=plan.targets,
            stored=stored,
            enqueued=False,
        )
    queue.submit(plan.idempotency_key, request)
    return SubmissionOutcome(
        idempotency_key=plan.idempotency_key, targets=plan.targets, stored=None, enqueued=True
    )
