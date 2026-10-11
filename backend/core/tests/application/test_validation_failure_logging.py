"""An AI recipe the domain validator rejects is logged with the rejecting
validator, the value and a bounded model-output snippet
(issues/silent-failures-not-logged E1-E3)."""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Mapping
from datetime import date
from typing import Any

import pytest
from support.fakes import (
    FakeAiProvider,
    FakeGenerationGate,
    FakeGenerationQueue,
    FakeWeekRepository,
)

from planner_core.application.single_recipe_generation import run_single_recipe_generation
from planner_core.application.week_generation import run_week_generation
from planner_core.domain.ai_output import RawIngredient, RawRecipeOutput
from planner_core.domain.calendar import IsoWeek
from planner_core.domain.generation import (
    GenerationMode,
    GenerationRequest,
    SpecificationSource,
)
from planner_core.domain.recipe import Recipe
from planner_core.domain.rules import RuleSet
from planner_core.ports.generation_queue import StoredGeneration

KEY = "k-invalid-1"
VALID = RawRecipeOutput(
    name="Lentejas guisadas",
    ingredients=(RawIngredient(name="lentejas", quantity=200.0, unit="g"),),
    tools=("olla",),
    procedure=("Cocer las lentejas.",),
    category="legume",
)
# (validator class name, offending value or None, field overrides)
REJECTIONS: list[tuple[str, str | None, dict[str, Any]]] = [
    (
        "UnknownUnit",
        "puñado",
        {"ingredients": (RawIngredient(name="lentejas", quantity=1.0, unit="puñado"),)},
    ),
    ("UnknownIngredientCategory", "postre", {"category": "postre"}),
    ("InvalidEstimatedTime", "unos 30 minutos", {"estimated_time": "unos 30 minutos"}),
    (
        "InvalidIngredientQuantity",
        "-2.0",
        {"ingredients": (RawIngredient(name="lentejas", quantity=-2.0, unit="g"),)},
    ),
    ("InvalidServings", "0", {"servings": 0}),
    ("MissingTools", None, {"tools": ()}),
]


def _pending_queue() -> FakeGenerationQueue:
    queue = FakeGenerationQueue()
    queue.stored[KEY] = StoredGeneration(idempotency_key=KEY, status="pending")
    return queue


def _encode(recipe: Recipe) -> Mapping[str, object]:
    return {"name": recipe.name}


def _run_single(raw: RawRecipeOutput) -> str | None:
    outcome = run_single_recipe_generation(
        KEY,
        SpecificationSource(("lentejas",), ("olla",)),
        "v1",
        provider=FakeAiProvider(responses=[raw]),
        queue=_pending_queue(),
        gate=FakeGenerationGate(),
        encode_recipe=_encode,
    )
    return outcome.terminal_status


def _run_week(raw: RawRecipeOutput) -> None:
    run_week_generation(
        KEY,
        GenerationRequest(week=IsoWeek(2026, 34), mode=GenerationMode.MIX),
        RuleSet(),
        "v1",
        "u-1",
        date.fromisocalendar(2026, 34, 7),
        provider=FakeAiProvider(responses=[raw]),
        weeks=FakeWeekRepository(),
        queue=_pending_queue(),
        gate=FakeGenerationGate(),
    )


def _warnings(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.levelno >= logging.WARNING]


@pytest.mark.parametrize(("validator", "value", "overrides"), REJECTIONS)
def test_single_recipe_rejection_logs_validator_value_and_snippet(
    caplog: pytest.LogCaptureFixture,
    validator: str,
    value: str | None,
    overrides: dict[str, Any],
) -> None:
    """E1 - the reported invalid_output with nothing in the log (FR-AI-01, R26)."""
    with caplog.at_level(logging.WARNING):
        status = _run_single(dataclasses.replace(VALID, **overrides))

    assert status == "failed"
    assert _warnings(caplog)
    assert KEY in caplog.text
    assert validator in caplog.text
    if value is not None:
        assert value in caplog.text
    assert "Lentejas guisadas" in caplog.text  # the model-output snippet


def test_week_slot_rejection_logs_validator_value_and_snippet(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """E2 - same swallow on the whole-week path (FR-AI-03, FR-AI-12)."""
    raw = dataclasses.replace(VALID, category="postre")

    with caplog.at_level(logging.WARNING):
        _run_week(raw)

    assert _warnings(caplog)
    assert "UnknownIngredientCategory" in caplog.text
    assert "postre" in caplog.text
    assert "Lentejas guisadas" in caplog.text


def test_a_huge_rejected_output_is_logged_bounded(caplog: pytest.LogCaptureFixture) -> None:
    """E3 - snippet capped at 500 chars, offending value capped too."""
    raw = dataclasses.replace(VALID, estimated_time="y" * 10_000, procedure=("x" * 10_000,))

    with caplog.at_level(logging.WARNING):
        _run_single(raw)

    warnings = _warnings(caplog)
    assert warnings
    assert "InvalidEstimatedTime" in caplog.text
    assert all(len(r.getMessage()) <= 1_000 for r in warnings)
