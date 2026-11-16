"""The env-var gate never logs the variable's value."""

from __future__ import annotations

import logging
from collections.abc import Callable

import pytest
from _env_switch_fixtures import SWITCH
from _env_switch_fixtures import ssm_says as ssm_says  # re-exported fixture

from planner_ai import wiring

_VALUE = "distinctive-off-value-7f3a"


def test_the_off_line_does_not_carry_the_value(
    ssm_says: Callable[[str], None],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """E6 - the line names the variable, never what it was set to."""
    ssm_says("true")
    monkeypatch.setenv(SWITCH, _VALUE)
    caplog.set_level(logging.INFO)

    assert wiring.build_dependencies().gate.is_generation_enabled() is False

    lines = [r for r in caplog.records if r.name.startswith("planner_ai")]
    assert lines and all(_VALUE not in r.getMessage() for r in lines)
    assert _VALUE not in caplog.text
