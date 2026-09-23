"""Tests for the whole-week AI generation worker use case (FR-AI-09, NFR-AI-01):
per-slot isolation, additive writes, the idempotent-invocation guard and the
cost-cap kill-switch (R1-R21)."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from datetime import date

import pytest
from support.fakes import (
    FakeAiProvider,
    FakeGenerationGate,
    FakeGenerationQueue,
    FakeWeekRepository,
)

from planner_core.application.week_generation import (
    SlotResult,
    WeekGenerationOutcome,
    run_week_generation,
)
from planner_core.domain.ai_output import RawIngredient, RawRecipeOutput
from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import Candidate, SlotContents
from planner_core.domain.generation import GenerationMode, GenerationRequest
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import MealSnapshot
from planner_core.domain.rules import RuleSet
from planner_core.ports.ai_provider import AiProviderError
from planner_core.ports.generation_queue import PerSlotResult, StoredGeneration

WEEK = IsoWeek(2026, 34)
KEY = "hash-1"
REQUEST = GenerationRequest(week=WEEK, mode=GenerationMode.MIX)
SATURDAY = date.fromisocalendar(2026, 34, 6)  # 4 open slots: Sat + Sun, lunch + dinner
SUNDAY = date.fromisocalendar(2026, 34, 7)  # 2 open slots


def _submitted_queue() -> FakeGenerationQueue:
    queue = FakeGenerationQueue()
    queue.stored[KEY] = StoredGeneration(idempotency_key=KEY, status="pending")
    return queue


def _run(
    *,
    queue: FakeGenerationQueue,
    weeks: FakeWeekRepository,
    provider: FakeAiProvider | None = None,
    gate: FakeGenerationGate | None = None,
    first_day: date = SUNDAY,
    author: str = "u-1",
) -> WeekGenerationOutcome:
    return run_week_generation(
        KEY,
        REQUEST,
        RuleSet(),
        "v1",
        author,
        first_day,
        provider=provider if provider is not None else FakeAiProvider(),
        weeks=weeks,
        queue=queue,
        gate=gate if gate is not None else FakeGenerationGate(),
    )


def _meal() -> MealSnapshot:
    return MealSnapshot(
        name="Existente", ingredients=(), tools=(), procedure=(), category=IngredientCategory.MEAT
    )


def test_slot_result_and_outcome_are_frozen() -> None:
    """docs/conventions.md — every new frozen dataclass gets this test."""
    result = SlotResult(day=1, slot=1, status="completed", message=None)
    outcome = WeekGenerationOutcome(claimed=True, terminal_status="completed", per_slot=(result,))
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.__setattr__("status", "failed")
    with pytest.raises(dataclasses.FrozenInstanceError):
        outcome.__setattr__("claimed", False)


# --- R2-R5, R21: per-slot independence + authorship --------------------------


def test_a_provider_failure_on_one_slot_leaves_the_others_persisted() -> None:
    weeks = FakeWeekRepository()
    # Non-empty tools (issue recipe-saved-without-required-sections, G-89).
    good = RawRecipeOutput(
        name="Buena",
        ingredients=(RawIngredient(name="arroz", quantity=100.0, unit="g"),),
        tools=("olla",),
        procedure=("Cocer.",),
        category="carbohydrate",
    )
    provider = FakeAiProvider(responses=[good, AiProviderError("boom"), good, good])

    outcome = _run(queue=_submitted_queue(), weeks=weeks, provider=provider, first_day=SATURDAY)

    statuses = [r.status for r in outcome.per_slot]
    assert statuses.count("completed") == 3 and statuses.count("failed") == 1
    persisted = [c for slot in weeks.get_week(WEEK).values() for c in slot.candidates]
    assert len(persisted) == 3  # R3, R5 — one write per success, failures kept out
    assert all(c.author == "u-1" for c in persisted)  # R21


def test_each_success_is_its_own_week_write() -> None:
    weeks = FakeWeekRepository()

    _run(queue=_submitted_queue(), weeks=weeks, first_day=SUNDAY)

    assert weeks.versions[WEEK] == 2  # R3 — two open slots, two save_slot calls


# --- R8, R9, R10: additive, definitive outranks -----------------------------


def test_generation_is_additive_and_skips_a_slot_that_is_definitive_now() -> None:
    weeks = FakeWeekRepository()
    lunch = SlotRef(SUNDAY, MealSlot.LUNCH)
    dinner = SlotRef(SUNDAY, MealSlot.DINNER)
    existing = Candidate(id="c0", meal=_meal(), author="chef")
    weeks.save_slot(WEEK, lunch, SlotContents(candidates=(existing,), definitive_id="c0"))
    weeks.save_slot(WEEK, dinner, SlotContents(candidates=(existing,)))
    baseline = weeks.versions[WEEK]

    outcome = _run(queue=_submitted_queue(), weeks=weeks, first_day=SUNDAY)

    lunch_now = weeks.get_week(WEEK)[lunch]
    assert lunch_now.candidates == (existing,) and lunch_now.definitive_id == "c0"  # R9, R10
    dinner_now = weeks.get_week(WEEK)[dinner]
    assert existing in dinner_now.candidates and len(dinner_now.candidates) == 2  # R8, R9
    assert weeks.versions[WEEK] == baseline + 1  # only the dinner write
    assert {(r.day, r.status) for r in outcome.per_slot} == {(7, "completed")}


def test_a_definitive_appearing_after_target_resolution_is_not_overwritten() -> None:
    """R8, R10 — the skip is governed by the same-step re-read, not the stale
    pre-loop occupancy. Kills the two week_generation.py:106-107 mutants."""
    lunch = SlotRef(SUNDAY, MealSlot.LUNCH)
    dinner = SlotRef(SUNDAY, MealSlot.DINNER)
    promoted = Candidate(id="c0", meal=_meal(), author="chef")
    saved: list[SlotRef] = []
    reads = 0

    class _Weeks(FakeWeekRepository):
        def get_week(self, week: IsoWeek) -> Mapping[SlotRef, SlotContents]:
            nonlocal reads
            reads += 1
            if reads == 1:  # resolve_targets sees both SUNDAY slots open
                return {}
            # a definitive was promoted into lunch since submit
            return {lunch: SlotContents(candidates=(promoted,), definitive_id="c0")}

        def save_slot(self, week: IsoWeek, slot: SlotRef, contents: SlotContents) -> int:
            saved.append(slot)
            return super().save_slot(week, slot, contents)

    outcome = _run(queue=_submitted_queue(), weeks=_Weeks(), first_day=SUNDAY)

    assert lunch not in saved  # the promoted definitive is never written over
    assert dinner in saved
    lunch_result = next(r for r in outcome.per_slot if r.slot == int(MealSlot.LUNCH.value))
    assert (lunch_result.status, lunch_result.message) == ("completed", None)


# --- R11-R15: idempotent invocation ----------------------------------------


def test_a_lost_claim_invokes_no_provider_and_records_nothing() -> None:
    weeks = FakeWeekRepository()
    provider = FakeAiProvider()
    queue = FakeGenerationQueue()
    queue.stored[KEY] = StoredGeneration(idempotency_key=KEY, status="running")  # already claimed

    outcome = _run(queue=queue, weeks=weeks, provider=provider)

    assert outcome.claimed is False and outcome.per_slot == ()
    assert provider.calls == 0  # R12, R13
    assert KEY not in queue.results  # R14 not reached


def test_a_redelivery_after_completion_invokes_no_provider() -> None:
    weeks = FakeWeekRepository()
    provider = FakeAiProvider()
    queue = FakeGenerationQueue()
    queue.stored[KEY] = StoredGeneration(idempotency_key=KEY, status="completed", result="[]")

    _run(queue=queue, weeks=weeks, provider=provider)

    assert provider.calls == 0  # R13


def test_record_result_runs_after_the_last_week_write() -> None:
    events: list[str] = []

    class _Weeks(FakeWeekRepository):
        def save_slot(self, week: IsoWeek, slot: SlotRef, contents: SlotContents) -> int:
            events.append("save")
            return super().save_slot(week, slot, contents)

    class _Queue(FakeGenerationQueue):
        def record_result(
            self, idempotency_key: str, status: str, per_slot: list[PerSlotResult]
        ) -> None:
            events.append("record")
            super().record_result(idempotency_key, status, per_slot)

    queue = _Queue()
    queue.stored[KEY] = StoredGeneration(idempotency_key=KEY, status="pending")

    _run(queue=queue, weeks=_Weeks(), first_day=SUNDAY)

    assert events == ["save", "save", "record"]  # R15


def test_the_terminal_status_and_per_slot_payload_reach_the_record() -> None:
    weeks = FakeWeekRepository()
    queue = _submitted_queue()

    _run(queue=queue, weeks=weeks, first_day=SUNDAY)

    assert queue.stored[KEY].status == "completed"  # R14
    assert queue.results[KEY] == [
        {"day": 7, "slot": 1, "status": "completed", "message": None},
        {"day": 7, "slot": 2, "status": "completed", "message": None},
    ]


# --- R16-R18: cost-cap kill-switch ----------------------------------------


def test_a_disabled_gate_invokes_no_provider_and_marks_every_slot_unavailable() -> None:
    from planner_core.messages import AI_GENERATION_UNAVAILABLE

    weeks = FakeWeekRepository()
    provider = FakeAiProvider()

    outcome = _run(
        queue=_submitted_queue(),
        weeks=weeks,
        provider=provider,
        gate=FakeGenerationGate(enabled=False),
        first_day=SUNDAY,
    )

    assert provider.calls == 0  # R17
    assert weeks.versions.get(WEEK) is None  # nothing written
    assert [r.message for r in outcome.per_slot] == [AI_GENERATION_UNAVAILABLE] * 2  # R18
    assert all(r.status == "failed" for r in outcome.per_slot)


def test_the_gate_is_read_before_every_slot() -> None:
    weeks = FakeWeekRepository()
    gate = FakeGenerationGate(enabled=True)

    _run(queue=_submitted_queue(), weeks=weeks, gate=gate, first_day=SUNDAY)

    assert gate.reads == 2  # R16 — once per open slot
