"""The AiProvider and GenerationGate ports and their fakes (FR-AI-09, NFR-AI-01)."""

from __future__ import annotations

import inspect

from support.fakes import FakeAiProvider, FakeGenerationGate

from planner_core.ports.ai_provider import AiProvider
from planner_core.ports.generation_gate import GenerationGate


def test_the_fakes_satisfy_their_ports() -> None:
    assert isinstance(FakeAiProvider(), AiProvider)
    assert isinstance(FakeGenerationGate(), GenerationGate)


def test_the_generation_gate_takes_no_user_argument() -> None:
    """R19, R20 — one deployment-wide state, never a per-user check."""
    params = list(inspect.signature(GenerationGate.is_generation_enabled).parameters)
    assert params == ["self"]
