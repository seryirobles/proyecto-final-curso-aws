"""Contract suite for GenerationGate: the in-memory fake and the SSM-backed
adapter agree — the parameter's "true"/"false" is the deployment-wide switch,
and a read failure fails closed (NFR-AI-01; specs/ai_lambda/design.md section 5)."""

from __future__ import annotations

import pytest
from planner_core.ports.generation_gate import GenerationGate
from support.fakes import FakeGenerationGate

from tests.contract.dynamo_contract import seed_ssm_parameter, ssm_generation_gate

_PARAM = "/planner/dev/ai-generation-enabled"


@pytest.mark.parametrize(
    "gate,expected",
    [
        (FakeGenerationGate(enabled=True), True),
        (FakeGenerationGate(enabled=False), False),
    ],
)
def test_the_fake_reports_its_configured_state(gate: GenerationGate, expected: bool) -> None:
    assert gate.is_generation_enabled() is expected


def test_the_ssm_gate_reads_the_parameter_value() -> None:
    seed_ssm_parameter(_PARAM, "true")
    assert ssm_generation_gate().is_generation_enabled() is True

    seed_ssm_parameter(_PARAM, "false")
    assert ssm_generation_gate().is_generation_enabled() is False


def test_the_ssm_gate_fails_closed_when_the_parameter_is_absent() -> None:
    assert ssm_generation_gate().is_generation_enabled() is False
