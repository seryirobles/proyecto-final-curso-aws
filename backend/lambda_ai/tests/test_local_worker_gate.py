"""The local worker's AI_GENERATION_ENABLED override of the SSM kill-switch, and
the deployed path that must ignore it (issues/ai-generation-422-unavailable E5-E6)."""

from __future__ import annotations

from collections.abc import Callable, Iterator

import boto3
import pytest
from moto import mock_aws

from planner_ai import local_worker, wiring
from planner_ai.adapters import ssm

_OVERRIDE = "AI_GENERATION_ENABLED"
_PARAMETER = "/planner/dev/ai-generation-enabled"


@pytest.fixture
def ssm_says(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[[str], None]]:
    """Sets the moto-backed SSM switch to the given value."""
    monkeypatch.setenv("PLANNER_ENV", "dev")
    with mock_aws():
        client = boto3.client("ssm", region_name=ssm._REGION)

        def put(value: str) -> None:
            client.put_parameter(Name=_PARAMETER, Value=value, Type="String", Overwrite=True)

        yield put


def test_override_true_enables_the_local_worker_whatever_ssm_says(
    ssm_says: Callable[[str], None], monkeypatch: pytest.MonkeyPatch
) -> None:
    """E5 - the reported generation_unavailable: local opt-in needs no SSM."""
    ssm_says("false")
    monkeypatch.setenv(_OVERRIDE, "true")

    assert local_worker.build_local_dependencies().gate.is_generation_enabled() is True


def test_override_false_disables_the_local_worker_whatever_ssm_says(
    ssm_says: Callable[[str], None], monkeypatch: pytest.MonkeyPatch
) -> None:
    """E5."""
    ssm_says("true")
    monkeypatch.setenv(_OVERRIDE, "false")

    assert local_worker.build_local_dependencies().gate.is_generation_enabled() is False


@pytest.mark.parametrize("override", [None, "", "TRUE", "1", "yes", " true"])
@pytest.mark.parametrize("switch", ["true", "false"])
def test_anything_but_exact_true_or_false_leaves_the_ssm_switch_in_charge(
    ssm_says: Callable[[str], None],
    monkeypatch: pytest.MonkeyPatch,
    override: str | None,
    switch: str,
) -> None:
    """E6 - unset or unrecognised behaves exactly as today."""
    ssm_says(switch)
    if override is None:
        monkeypatch.delenv(_OVERRIDE, raising=False)
    else:
        monkeypatch.setenv(_OVERRIDE, override)

    gate = local_worker.build_local_dependencies().gate

    assert gate.is_generation_enabled() is (switch == "true")


def test_the_deployed_wiring_ignores_the_override(
    ssm_says: Callable[[str], None], monkeypatch: pytest.MonkeyPatch
) -> None:
    """E6 - NFR-AI-01: the local override cannot bypass the deployed switch (SSM or env)."""
    ssm_says("false")
    monkeypatch.setenv(_OVERRIDE, "true")

    assert wiring.build_dependencies().gate.is_generation_enabled() is False
