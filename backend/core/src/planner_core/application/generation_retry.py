"""Per-slot retry of a whole-week run (FR-AI-09, FR-AI-11, FR-AI-12): check the
slot exists and is still open under the parent run's stored rules, then hand
the conditional pending-write and the enqueue to the queue port
(specs/week_generation_backend/design.md section 4)."""

from __future__ import annotations

from datetime import date

from planner_core.domain.generation import resolve_targets
from planner_core.ports.generation_queue import (
    GenerationNotFound,
    GenerationQueue,
    GenerationSlotNotFound,
    SlotNotRetryable,
    StoredGeneration,
)
from planner_core.ports.weeks import WeekRepository


def retry_slot(
    generation_id: str,
    day: int,
    slot: int,
    first_day: date,
    *,
    queue: GenerationQueue,
    weeks: WeekRepository,
    author: str,
) -> StoredGeneration:
    """R36-R42, R44. Returns the record as it stands after the slot went pending."""
    stored = queue.stored_generation(generation_id)
    if stored is None:
        raise GenerationNotFound(generation_id)  # R41
    entry = next((s for s in stored.slots or () if (s.day, s.slot) == (day, slot)), None)
    if entry is None or stored.snapshot is None:
        raise GenerationSlotNotFound(f"{day}-{slot}")  # R42

    snap = stored.snapshot  # R44 — the parent run's effective rules, not the shared ones
    targets = resolve_targets(snap.week, snap.rules, first_day, weeks.get_week(snap.week))
    if not any(s.day_number == day and int(s.slot.value) == slot for s in targets.open_slots):
        raise SlotNotRetryable(f"{day}-{slot}")  # R39

    queue.retry_slot(generation_id, day, slot, author=author)  # R38, R40 — conditional
    refreshed = queue.stored_generation(generation_id)
    return refreshed if refreshed is not None else stored
