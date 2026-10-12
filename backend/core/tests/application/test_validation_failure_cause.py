"""Cause text and log bounds for rejected AI output (issue 14 E1, E3)."""

from __future__ import annotations

import dataclasses
import logging
import re
from datetime import date

import pytest
from support.fakes import (
    FakeAiProvider,
    FakeGenerationGate,
    FakeGenerationQueue,
    FakeRecipeRepository,
    FakeWeekRepository,
)

from planner_core.application.week_generation import run_week_generation
from planner_core.domain.ai_output import (
    GenerationFailure,
    RawIngredient,
    RawRecipeOutput,
    validate_and_preview,
)
from planner_core.domain.calendar import IsoWeek
from planner_core.domain.generation import GenerationMode, GenerationRequest
from planner_core.domain.rules import RuleSet
from planner_core.ports.generation_queue import StoredGeneration

VALID = RawRecipeOutput(
    name="Lentejas guisadas",
    ingredients=(RawIngredient(name="lentejas", quantity=200.0, unit="g"),),
    tools=("olla",),
    procedure=("Cocer las lentejas.",),
    category="legume",
)


def test_cause_carries_the_value_even_when_the_snippet_would_not() -> None:
    raw = dataclasses.replace(VALID, category="postre")
    outcome = validate_and_preview(raw)
    assert isinstance(outcome, GenerationFailure)
    assert outcome.cause == "UnknownIngredientCategory postre"


def test_cause_value_is_capped_at_exactly_100_chars() -> None:
    outcome = validate_and_preview(dataclasses.replace(VALID, estimated_time="y" * 10_000))
    assert isinstance(outcome, GenerationFailure)
    assert outcome.cause is not None
    assert outcome.cause == "InvalidEstimatedTime " + "y" * 100


def test_week_path_snippet_is_capped_at_500(caplog: pytest.LogCaptureFixture) -> None:
    raw = dataclasses.replace(VALID, category="postre", procedure=("x" * 10_000,))
    queue = FakeGenerationQueue()
    queue.stored["k"] = StoredGeneration(idempotency_key="k", status="pending")
    with caplog.at_level(logging.WARNING):
        run_week_generation(
            "k",
            GenerationRequest(week=IsoWeek(2026, 34), mode=GenerationMode.MIX),
            RuleSet(),
            "v1",
            "u-1",
            date.fromisocalendar(2026, 34, 7),
            provider=FakeAiProvider(responses=[raw]),
            weeks=FakeWeekRepository(),
            recipes=FakeRecipeRepository(),
            queue=queue,
            gate=FakeGenerationGate(),
        )
    text = caplog.text
    assert "UnknownIngredientCategory" in text
    assert max(len(m) for m in re.findall(r"x+", text)) < 500
