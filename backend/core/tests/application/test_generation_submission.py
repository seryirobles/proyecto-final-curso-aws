"""Tests for whole-week generation submission: deterministic idPeticionIA, an
idempotent hit returns the stored result without enqueuing (R27, R28, R29)."""

from __future__ import annotations

import dataclasses
from datetime import date

import pytest
from support.fakes import FakeGenerationQueue, FakeRuleRepository, FakeWeekRepository

from planner_core.application.generation_submission import SubmissionOutcome, submit_generation
from planner_core.domain.calendar import IsoWeek
from planner_core.domain.generation import (
    GenerationMode,
    GenerationRequest,
    GenerationTargets,
    build_plan,
)
from planner_core.domain.rules import RuleSet
from planner_core.ports.generation_queue import StoredGeneration

FIRST_DAY = date(2026, 8, 17)  # Monday of 2026-W34
REQUEST = GenerationRequest(week=IsoWeek(2026, 34), mode=GenerationMode.MIX)


def test_submission_outcome_is_frozen() -> None:
    """docs/conventions.md: every new frozen dataclass gets this test."""
    outcome = SubmissionOutcome(
        idempotency_key="x", targets=GenerationTargets((), (), (), ()), stored=None, enqueued=True
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        outcome.__setattr__("enqueued", False)


def test_submission_derives_the_same_id_twice_for_the_same_input() -> None:
    weeks, rules, queue = FakeWeekRepository(), FakeRuleRepository(), FakeGenerationQueue()
    # R27 — the id equals the domain-derived key (empty fakes -> RuleSet(), no week);
    # asserting against the derivation defeats a hardcoded constant id.
    expected = build_plan(REQUEST, RuleSet(), FIRST_DAY, {}).idempotency_key

    first = submit_generation(REQUEST, FIRST_DAY, weeks=weeks, rules=rules, queue=queue)
    second = submit_generation(REQUEST, FIRST_DAY, weeks=weeks, rules=rules, queue=queue)

    assert first.idempotency_key == expected
    assert second.idempotency_key == expected


def test_submission_derives_a_different_id_for_a_materially_different_request() -> None:
    """R27 — a constant id would collide two distinct inputs."""
    weeks, rules, queue = FakeWeekRepository(), FakeRuleRepository(), FakeGenerationQueue()
    other = GenerationRequest(week=IsoWeek(2026, 35), mode=GenerationMode.MIX)

    first = submit_generation(REQUEST, FIRST_DAY, weeks=weeks, rules=rules, queue=queue)
    second = submit_generation(other, date(2026, 8, 24), weeks=weeks, rules=rules, queue=queue)

    assert first.idempotency_key != second.idempotency_key


def test_a_fresh_request_enqueues_exactly_once() -> None:
    weeks, rules, queue = FakeWeekRepository(), FakeRuleRepository(), FakeGenerationQueue()

    outcome = submit_generation(REQUEST, FIRST_DAY, weeks=weeks, rules=rules, queue=queue)

    assert outcome.enqueued is True and outcome.stored is None
    assert queue.submissions == [(outcome.idempotency_key, REQUEST)]


def test_an_idempotent_hit_returns_the_stored_result_without_enqueuing() -> None:
    weeks, rules, queue = FakeWeekRepository(), FakeRuleRepository(), FakeGenerationQueue()
    key = submit_generation(
        REQUEST, FIRST_DAY, weeks=weeks, rules=rules, queue=queue
    ).idempotency_key
    queue.submissions.clear()
    queue.stored[key] = StoredGeneration(idempotency_key=key, status="done", result="{}")

    outcome = submit_generation(REQUEST, FIRST_DAY, weeks=weeks, rules=rules, queue=queue)

    assert outcome.enqueued is False
    assert outcome.stored is not None and outcome.stored.result == "{}"
    assert queue.submissions == []
