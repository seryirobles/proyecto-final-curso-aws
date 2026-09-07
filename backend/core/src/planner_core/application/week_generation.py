"""Whole-week AI generation worker use case (FR-AI-09, NFR-AI-01): claim the
message, resolve the open target slots, generate each one independently, write
the successful candidates through WeekRepository, then record the run's result.

Pinned-slot candidates are NOT this worker's job — feature 27's
generation_submission writes them synchronously at submit
(specs/ai_lambda/design.md section 3)."""

from __future__ import annotations

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
from planner_core.domain.ai_prompt import build_category_prompt
from planner_core.domain.candidate import SlotContents, definitive, new_candidate
from planner_core.domain.generation import GenerationRequest, resolve_targets
from planner_core.domain.recipe import snapshot
from planner_core.domain.rules import RuleSet
from planner_core.ports.ai_provider import AiProvider, AiProviderError
from planner_core.ports.generation_gate import GenerationGate
from planner_core.ports.generation_queue import GenerationResultSink, PerSlotResult
from planner_core.ports.weeks import WeekRepository

_TERMINAL_STATUS = "completed"


@dataclass(frozen=True)
class SlotResult:
    """One target slot's terminal outcome, in the shape record_result serialises
    and GET /v1/generations/{id} returns (specs/ai_lambda/design.md section 6)."""

    day: int
    slot: int
    status: str  # "completed" | "failed"
    message: str | None


@dataclass(frozen=True)
class WeekGenerationOutcome:
    """The run's result: whether this worker claimed the message, the terminal
    status recorded (None when the claim was lost), and every target slot."""

    claimed: bool
    terminal_status: str | None
    per_slot: tuple[SlotResult, ...]


def _payload(results: tuple[SlotResult, ...]) -> list[PerSlotResult]:
    return [
        {"day": r.day, "slot": r.slot, "status": r.status, "message": r.message} for r in results
    ]


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
    queue: GenerationResultSink,
    gate: GenerationGate,
) -> WeekGenerationOutcome:
    """R1-R21. effective_rules / prompt_version_id / author arrive enriched on
    the SQS message; no RuleRepository or ConfigPort is read here."""
    if not queue.claim(idempotency_key):  # R11-R13 — redelivery guard
        return WeekGenerationOutcome(claimed=False, terminal_status=None, per_slot=())

    occupancy = weeks.get_week(request.week)
    targets = resolve_targets(request.week, effective_rules, first_day, occupancy)
    prompt = build_category_prompt(targets.remaining_category_counts, prompt_version_id)

    results: list[SlotResult] = []
    for slot in targets.open_slots:
        day_n, meal_n = slot.day_number, int(slot.slot.value)

        if not gate.is_generation_enabled():  # R16, R17
            failure = build_generation_failure(GenerationFailureReason.GENERATION_UNAVAILABLE)
            results.append(SlotResult(day_n, meal_n, "failed", failure.message))  # R18
            continue

        try:
            raw = provider.generate(prompt)
        except AiProviderError:  # R4 — per-slot isolation
            invalid = build_generation_failure(GenerationFailureReason.INVALID_OUTPUT)
            results.append(SlotResult(day_n, meal_n, "failed", invalid.message))
            continue

        outcome = validate_and_preview(raw)
        if isinstance(outcome, GenerationFailure):
            results.append(SlotResult(day_n, meal_n, "failed", outcome.message))
            continue

        current = weeks.get_week(request.week).get(slot, SlotContents())  # R8 — read now
        if definitive(current) is not None:  # R10 — a definitive outranks the candidate
            results.append(SlotResult(day_n, meal_n, "completed", None))
            continue

        candidate = new_candidate(
            uuid4().hex, snapshot(accept_preview(outcome.preview)), author
        )  # R6, R21
        add_slot_candidate(request.week, slot, candidate, weeks=weeks)  # R6, R7
        results.append(SlotResult(day_n, meal_n, "completed", None))

    frozen = tuple(results)
    queue.record_result(idempotency_key, _TERMINAL_STATUS, _payload(frozen))  # R14, R15
    return WeekGenerationOutcome(claimed=True, terminal_status=_TERMINAL_STATUS, per_slot=frozen)
