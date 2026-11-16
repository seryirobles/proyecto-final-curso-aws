"""AI_GENERATION_SWITCH picks the kill-switch adapter in the real wiring: set, it
alone decides and fails closed; unset, SSM as designed."""

from __future__ import annotations

import logging
from collections.abc import Callable

import pytest
from _env_switch_fixtures import LOCAL_OVERRIDE, SWITCH, DeniedSsm
from _env_switch_fixtures import shared_role as shared_role  # re-exported fixture
from _env_switch_fixtures import ssm_says as ssm_says  # re-exported fixture
from planner_core.ports.generation_gate import GenerationGate

from planner_ai import local_worker, wiring
from planner_ai.adapters.ssm import SsmGenerationGate

_ENABLED = ["true", "TRUE", "True", " true ", "true\n"]
_DISABLED = [
    "false",
    "FALSE",
    "",
    "   ",
    "0",
    "1",
    "yes",
    "on",
    "enabled",
    "tru",
    "truee",
    "true false",
    "null",
]


def _gate() -> GenerationGate:
    return wiring.build_dependencies().gate


@pytest.mark.parametrize("value", _ENABLED)
def test_the_switch_on_enables_generation_under_the_shared_role(
    shared_role: DeniedSsm, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    """E1 - reproduction: today the denied SSM read wins whatever the variable says."""
    monkeypatch.setenv(SWITCH, value)

    assert _gate().is_generation_enabled() is True


@pytest.mark.parametrize("value", _DISABLED)
def test_anything_but_true_disables_generation_even_with_ssm_on(
    ssm_says: Callable[[str], None], monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    """E2 - NFR-AI-01: SSM says on, so only the variable can make this False."""
    ssm_says("true")
    monkeypatch.setenv(SWITCH, value)

    assert _gate().is_generation_enabled() is False


@pytest.mark.parametrize("value", ["true", "false", "", "garbage"])
def test_a_set_switch_never_reads_ssm(
    shared_role: DeniedSsm, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    """E3 - presence selects the adapter, an empty value included."""
    monkeypatch.setenv(SWITCH, value)
    gate = _gate()

    gate.is_generation_enabled()

    assert not isinstance(gate, SsmGenerationGate)
    assert shared_role.reads == 0


@pytest.mark.parametrize("value", ["true", "false"])
def test_an_unset_switch_leaves_ssm_in_charge(ssm_says: Callable[[str], None], value: str) -> None:
    """E4 - the swap back: delete the variable and SSM decides again."""
    ssm_says(value)
    gate = _gate()

    assert isinstance(gate, SsmGenerationGate)
    assert gate.is_generation_enabled() is (value == "true")


def test_an_unset_switch_under_the_shared_role_stays_closed(
    shared_role: DeniedSsm, caplog: pytest.LogCaptureFixture
) -> None:
    """E4 - absence never opens generation; this is the reported CloudWatch line."""
    with caplog.at_level(logging.WARNING):
        assert _gate().is_generation_enabled() is False

    assert shared_role.reads == 1
    assert "(AccessDeniedException AccessDeniedException)" in caplog.text


def test_the_gate_reads_the_variable_on_every_call(
    ssm_says: Callable[[str], None], monkeypatch: pytest.MonkeyPatch
) -> None:
    """E5 - R16; gone at read time it stays closed instead of raising."""
    ssm_says("true")
    monkeypatch.setenv(SWITCH, "true")
    gate = _gate()

    assert gate.is_generation_enabled() is True
    monkeypatch.setenv(SWITCH, "false")
    assert gate.is_generation_enabled() is False
    monkeypatch.setenv(SWITCH, "true")
    assert gate.is_generation_enabled() is True
    monkeypatch.delenv(SWITCH)
    assert gate.is_generation_enabled() is False


@pytest.mark.parametrize(("switch", "override"), [("false", "true"), ("true", "false")])
def test_the_deployed_wiring_ignores_the_local_override(
    ssm_says: Callable[[str], None], monkeypatch: pytest.MonkeyPatch, switch: str, override: str
) -> None:
    """E8 - SSM agrees with the override, so only the switch can give this answer."""
    ssm_says(override)
    monkeypatch.setenv(SWITCH, switch)
    monkeypatch.setenv(LOCAL_OVERRIDE, override)

    assert _gate().is_generation_enabled() is (switch == "true")


@pytest.mark.parametrize(("switch", "override"), [("false", "true"), ("true", "false")])
def test_the_local_override_still_wins_in_the_local_worker(
    ssm_says: Callable[[str], None], monkeypatch: pytest.MonkeyPatch, switch: str, override: str
) -> None:
    """E8 - docs/local_development.md section 3 keeps working as documented."""
    ssm_says(switch)
    monkeypatch.setenv(SWITCH, switch)
    monkeypatch.setenv(LOCAL_OVERRIDE, override)

    gate = local_worker.build_local_dependencies().gate

    assert gate.is_generation_enabled() is (override == "true")
