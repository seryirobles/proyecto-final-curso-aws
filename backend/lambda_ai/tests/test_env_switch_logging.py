"""The env-var gate logs the off transition like the SSM gate does (issue 14 E7):
one INFO per transition into disabled, naming the variable; on stays silent."""

from __future__ import annotations

import logging
from collections.abc import Callable

import pytest
from _env_switch_fixtures import SWITCH
from _env_switch_fixtures import ssm_says as ssm_says  # re-exported fixture

from planner_ai import wiring

_SECRET = "bedrock-api-key-must-not-be-logged"


def _lines(caplog: pytest.LogCaptureFixture, level: int) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name.startswith("planner_ai") and r.levelno == level]


@pytest.mark.parametrize("value", ["false", "", "garbage"])
def test_the_off_state_logs_one_info_naming_the_variable(
    ssm_says: Callable[[str], None],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    value: str,
) -> None:
    """E6 - SSM says on throughout, so an SSM read can log no off line here."""
    ssm_says("true")
    monkeypatch.setenv(SWITCH, value)
    monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", _SECRET)
    caplog.set_level(logging.INFO)

    assert wiring.build_dependencies().gate.is_generation_enabled() is False

    infos = _lines(caplog, logging.INFO)
    assert len(infos) == 1 and SWITCH in infos[0].getMessage()
    assert _lines(caplog, logging.WARNING) == []
    assert _SECRET not in caplog.text


def test_repeated_off_reads_log_once(
    ssm_says: Callable[[str], None],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """E6 - a week run reads the gate once per slot."""
    ssm_says("true")
    monkeypatch.setenv(SWITCH, "false")
    caplog.set_level(logging.INFO)
    gate = wiring.build_dependencies().gate

    for _ in range(3):
        gate.is_generation_enabled()

    assert len(_lines(caplog, logging.INFO)) == 1


def test_each_transition_into_off_logs_again(
    ssm_says: Callable[[str], None],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """E6."""
    ssm_says("true")
    monkeypatch.setenv(SWITCH, "false")
    caplog.set_level(logging.INFO)
    gate = wiring.build_dependencies().gate

    for value in ("false", "true", "false"):
        monkeypatch.setenv(SWITCH, value)
        gate.is_generation_enabled()

    assert len(_lines(caplog, logging.INFO)) == 2


def test_the_on_state_logs_nothing(
    ssm_says: Callable[[str], None],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """E6 - SSM says off, so an SSM read would log and return False."""
    ssm_says("false")
    monkeypatch.setenv(SWITCH, "true")
    caplog.set_level(logging.INFO)

    assert wiring.build_dependencies().gate.is_generation_enabled() is True

    assert [r for r in caplog.records if r.name.startswith("planner_ai")] == []
