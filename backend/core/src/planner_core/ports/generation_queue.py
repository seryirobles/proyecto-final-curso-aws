"""The generation hand-off port: idempotent submission of a whole-week
generation request and lookup of an already-stored result (FR-AI-08, AP25/AP26).

The name says "queue" but the signature names no queue technology: an adapter
may back it with SQS plus a DynamoDB idempotency record, or anything else
(docs/architecture.md section 3.1 — storage/transport-agnostic ports)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from planner_core.domain.errors import PlannerError
from planner_core.domain.generation import (
    GenerationRequest,
    GenerationSnapshot,
    RunStatus,
    SingleRecipeRequest,
    SlotProgress,
)
from planner_core.domain.recipe import Recipe
from planner_core.domain.rules import RuleSet

PerSlotResult = Mapping[str, object]
"""One entry of record_result's per_slot payload: {day, slot, status, message}."""

ResultPayload = list[PerSlotResult] | Mapping[str, object]
"""record_result's payload: the whole-week per-slot list, or a single-recipe
result dict (the wire recipe, or {"error": {...}}) (specs/single_recipe_generation)."""


@dataclass(frozen=True)
class StoredGeneration:
    """A generation record already persisted for a generation request (AP26):
    its status and, if finished, its result payload. Opaque here — the AI
    generation semantics are feature 17's. `idempotency_key` is the domain's
    term (`domain/generation.py`); the adapter maps it to the persisted
    `idPeticionIA` (`docs/data_model.md` section 2)."""

    idempotency_key: str
    status: str
    result: str | None = None
    slots: tuple[SlotProgress, ...] | None = None
    """Per-slot progress of a whole-week run, ordered by day then slot; None on
    a single-recipe record (week_generation_backend design section 2)."""
    snapshot: GenerationSnapshot | None = None


class GenerationNotFound(PlannerError):
    """No generation record exists for this id (AP26)."""

    def __init__(self, generation_id: str) -> None:
        super().__init__(generation_id)
        self.generation_id = generation_id


class GenerationSlotNotFound(PlannerError):
    """The run has no entry for the addressed slot."""


class SlotNotRetryable(PlannerError):
    """The slot is not in `error`, or is no longer an open slot (FR-AI-09, FR-AI-11)."""


@runtime_checkable
class GenerationResultSink(Protocol):
    """The subset the asynchronous `ai` worker needs: claim the message, then
    record the run's result (specs/ai_lambda/design.md section 3). Its own
    DynamoDB adapter lives in `planner_ai`; `GenerationQueue` is also one."""

    def claim(self, idempotency_key: str) -> bool:
        """Atomically move the stored record pending -> running; return whether
        this call applied that transition (R36). Conditional on estado=pending,
        so a redelivered request finds it already claimed and returns False
        (R37) — the idempotent-consumer guard (docs/data_model.md section 4.6)."""
        ...

    def record_result(self, idempotency_key: str, status: str, payload: ResultPayload) -> None:
        """Write the terminal estado and resultado (R38), unconditionally (R39).
        Single-recipe runs only; whole-week runs use the per-slot methods below
        (docs/data_model.md section 4.6)."""
        ...

    def stored_generation(self, idempotency_key: str) -> StoredGeneration | None:
        """The record already stored for this id, or None (AP26). Strongly
        consistent, no side effects."""
        ...

    def begin_slots(self, idempotency_key: str, slots: tuple[SlotProgress, ...]) -> None:
        """Record every given slot entry in one write (R17); a no-op when empty."""
        ...

    def record_slot(self, idempotency_key: str, progress: SlotProgress) -> None:
        """Replace one slot's entry, touching no other (R21): unconditional."""
        ...

    def claim_slot(self, idempotency_key: str, day: int, slot: int) -> bool:
        """Atomically move one slot pending -> running; False if it was not
        pending (R47, R48)."""
        ...

    def record_status(self, idempotency_key: str, status: RunStatus) -> None:
        """Write the run's `estado` only (R27)."""
        ...


@runtime_checkable
class GenerationQueue(GenerationResultSink, Protocol):
    """Hands a generation request off for asynchronous processing, keyed by a
    caller-derived idempotency id (docs/data_model.md section 2 — the id is not
    re-derived here)."""

    def submit(
        self,
        idempotency_key: str,
        request: GenerationRequest,
        *,
        effective_rules: RuleSet,
        prompt_version_id: str | None = None,
        author: str | None = None,
    ) -> None:
        """Hand the request off for processing under this id (AP25 + enqueue).
        Only called when stored_generation returned None. The enrichment args
        travel on the hand-off so the worker holds no RuleRepository/ConfigPort
        (R40, specs/ai_lambda/design.md section 8). effective_rules is required —
        an un-enriched message must never generate against empty rules (finding 1)."""
        ...

    def submit_recipe(
        self,
        idempotency_key: str,
        request: SingleRecipeRequest,
        *,
        reference_recipe: Recipe | None,
        prompt_version_id: str,
        author: str,
    ) -> None:
        """Hand a single-recipe request off (AP25 + enqueue), like `submit`. The
        reference recipe snapshot travels on the message so the worker holds no
        RecipeRepository (specs/single_recipe_generation/design.md section 3)."""
        ...

    def retry_slot(self, idempotency_key: str, day: int, slot: int, *, author: str) -> None:
        """Set an `error` slot pending and the run running in one conditional
        write, then enqueue one `slot_retry` message; raises SlotNotRetryable if
        the slot was not in `error` (R36, R38, R40, R45). A failed enqueue
        restores the slot to `error` (R46)."""
        ...

    def discard(self, idempotency_key: str) -> None:
        """Discard the stored generation record for this id (AP27). A no-op when
        no record exists — HTTP DELETE idempotency (docs/data_model.md section 4)."""
        ...
