"""Contract suite for the env-var GenerationGate: real adapter and in-memory fake
agree (architecture.md section 3.2 contract rule; NFR-AI-01)."""

from __future__ import annotations

import inspect

import pytest
from planner_ai.adapters.ssm import SsmGenerationGate
from planner_ai.wiring import build_dependencies
from planner_core.ports.generation_gate import GenerationGate
from support.fakes import FakeGenerationGate

from tests.contract.dynamo_contract import seed_ssm_parameter

_SWITCH = "AI_GENERATION_SWITCH"
_PARAM = "/planner/dev/ai-generation-enabled"


def _env_gate(monkeypatch: pytest.MonkeyPatch, value: str) -> GenerationGate:
    monkeypatch.setenv(_SWITCH, value)
    monkeypatch.setenv("PLANNER_ENV", "dev")
    return build_dependencies().gate


@pytest.mark.parametrize(("value", "enabled"), [("true", True), ("false", False)])
def test_the_env_gate_and_the_fake_agree(
    monkeypatch: pytest.MonkeyPatch, value: str, enabled: bool
) -> None:
    """E2 - SSM holds the opposite, so only the variable can give this answer."""
    seed_ssm_parameter(_PARAM, str(not enabled).lower())

    real = _env_gate(monkeypatch, value).is_generation_enabled()

    assert real is FakeGenerationGate(enabled=enabled).is_generation_enabled()


def test_the_env_gate_is_the_port_and_not_the_ssm_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E9 - R19: no user argument, one deployment-wide state."""
    gate = _env_gate(monkeypatch, "true")

    assert isinstance(gate, GenerationGate)
    assert not isinstance(gate, SsmGenerationGate)
    assert list(inspect.signature(gate.is_generation_enabled).parameters) == []
