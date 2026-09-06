"""The generation hand-off port: idempotent submission of a whole-week
generation request and lookup of an already-stored result (FR-AI-08, AP25/AP26).

The name says "queue" but the signature names no queue technology: an adapter
may back it with SQS plus a DynamoDB idempotency record, or anything else
(docs/architecture.md section 3.1 — storage/transport-agnostic ports)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from planner_core.domain.generation import GenerationRequest


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


@runtime_checkable
class GenerationQueue(Protocol):
    """Hands a generation request off for asynchronous processing, keyed by a
    caller-derived idempotency id (docs/data_model.md section 2 — the id is not
    re-derived here)."""

    def stored_generation(self, idempotency_key: str) -> StoredGeneration | None:
        """The record already stored for this id, or None (AP26). No side effects."""
        ...

    def submit(self, idempotency_key: str, request: GenerationRequest) -> None:
        """Hand the request off for processing under this id (AP25 + enqueue).
        Only called when stored_generation returned None."""
        ...

    def discard(self, idempotency_key: str) -> None:
        """Discard the stored generation record for this id (AP27). A no-op when
        no record exists — HTTP DELETE idempotency (docs/data_model.md section 4)."""
        ...
