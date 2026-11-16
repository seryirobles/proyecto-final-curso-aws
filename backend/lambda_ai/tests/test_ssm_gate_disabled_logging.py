"""A cleanly read 'disabled' switch is logged at INFO once per transition into
the disabled state, distinct from the fail-closed WARNING."""

from __future__ import annotations

import logging
from typing import Any

import pytest
from botocore.exceptions import NoCredentialsError

from planner_ai.adapters.ssm import SsmGenerationGate

PARAMETER = "/planner/dev/ai-generation-enabled"


class _ScriptedSsm:
    """Returns each scripted value in turn; an exception entry is raised."""

    def __init__(self, *values: str | Exception) -> None:
        self._values = list(values)

    def get_parameter(self, **kwargs: Any) -> Any:
        value = self._values.pop(0)
        if isinstance(value, Exception):
            raise value
        return {"Parameter": {"Value": value}}


def _gate(*values: str | Exception) -> SsmGenerationGate:
    return SsmGenerationGate(env="dev", client=_ScriptedSsm(*values), ttl_seconds=0.0)


def _at(caplog: pytest.LogCaptureFixture, level: int) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.levelno == level]


def test_a_clean_false_logs_one_info_and_no_warning(caplog: pytest.LogCaptureFixture) -> None:
    """E7 - NFR-AI-01's deliberate off state is visible."""
    caplog.set_level(logging.INFO)

    assert _gate("false").is_generation_enabled() is False

    infos = _at(caplog, logging.INFO)
    assert len(infos) == 1 and PARAMETER in infos[0].getMessage()
    assert _at(caplog, logging.WARNING) == []


def test_repeated_disabled_reads_log_once(caplog: pytest.LogCaptureFixture) -> None:
    """E7 - one line per transition, not per 5 s cache refresh."""
    caplog.set_level(logging.INFO)
    gate = _gate("false", "false", "false")

    for _ in range(3):
        gate.is_generation_enabled()

    assert len(_at(caplog, logging.INFO)) == 1


def test_each_transition_into_disabled_logs_again(caplog: pytest.LogCaptureFixture) -> None:
    """E7."""
    caplog.set_level(logging.INFO)
    gate = _gate("false", "true", "false")

    for _ in range(3):
        gate.is_generation_enabled()

    assert len(_at(caplog, logging.INFO)) == 2


def test_an_enabled_switch_logs_nothing(caplog: pytest.LogCaptureFixture) -> None:
    """E7 - the normal state is silent."""
    caplog.set_level(logging.INFO)

    assert _gate("true").is_generation_enabled() is True

    assert [r for r in caplog.records if r.levelno >= logging.INFO] == []


def test_a_failed_read_is_the_warning_not_the_disabled_info(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """E7 - fail-closed (issue 13) stays a WARNING, never this INFO."""
    caplog.set_level(logging.INFO)

    assert _gate(NoCredentialsError()).is_generation_enabled() is False

    assert _at(caplog, logging.INFO) == []
    assert len(_at(caplog, logging.WARNING)) == 1
