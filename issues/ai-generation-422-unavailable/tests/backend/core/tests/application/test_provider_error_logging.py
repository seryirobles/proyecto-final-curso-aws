"""A provider error the worker turns into a `failed` result is logged, not
swallowed silently (issues/ai-generation-422-unavailable E8)."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import date

import pytest
from support.fakes import (
    FakeAiProvider,
    FakeGenerationGate,
    FakeGenerationQueue,
    FakeWeekRepository,
)

from planner_core.application.single_recipe_generation import run_single_recipe_generation
from planner_core.application.week_generation import run_week_generation
from planner_core.domain.calendar import IsoWeek
from planner_core.domain.generation import (
    GenerationMode,
    GenerationRequest,
    SpecificationSource,
)
from planner_core.domain.recipe import Recipe
from planner_core.domain.rules import RuleSet
from planner_core.ports.ai_provider import AiProviderError
from planner_core.ports.generation_queue import StoredGeneration

KEY = "k-1"
CAUSE = "Bedrock invocation failed: AccessDeniedException"


def _pending_queue() -> FakeGenerationQueue:
    queue = FakeGenerationQueue()
    queue.stored[KEY] = StoredGeneration(idempotency_key=KEY, status="pending")
    return queue


def _encode(recipe: Recipe) -> Mapping[str, object]:
    return {"name": recipe.name}


def test_single_recipe_provider_error_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    """E8 - R26 still records failed; the cause reaches the log (FR-AI-01)."""
    queue = _pending_queue()

    with caplog.at_level(logging.WARNING):
        outcome = run_single_recipe_generation(
            KEY,
            SpecificationSource(("lentejas",), ("olla",)),
            "v1",
            provider=FakeAiProvider(responses=[AiProviderError(CAUSE)]),
            queue=queue,
            gate=FakeGenerationGate(),
            encode_recipe=_encode,
        )

    assert outcome.terminal_status == "failed"
    assert any(r.levelno >= logging.WARNING for r in caplog.records)
    assert CAUSE in caplog.text


def test_week_slot_provider_error_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    """E8 - same swallow, per slot (FR-AI-03; blast radius)."""
    with caplog.at_level(logging.WARNING):
        run_week_generation(
            KEY,
            GenerationRequest(week=IsoWeek(2026, 34), mode=GenerationMode.MIX),
            RuleSet(),
            "v1",
            "u-1",
            date.fromisocalendar(2026, 34, 7),
            provider=FakeAiProvider(responses=[AiProviderError(CAUSE)]),
            weeks=FakeWeekRepository(),
            queue=_pending_queue(),
            gate=FakeGenerationGate(),
        )

    assert any(r.levelno >= logging.WARNING for r in caplog.records)
    assert CAUSE in caplog.text
