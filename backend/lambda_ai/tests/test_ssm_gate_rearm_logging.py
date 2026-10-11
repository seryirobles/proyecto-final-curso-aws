"""A failed read re-arms the disabled INFO line (issue 14 E7)."""

from __future__ import annotations

import logging

import pytest
from botocore.exceptions import NoCredentialsError
from test_ssm_gate_disabled_logging import _gate


def test_a_failed_read_between_two_off_reads_logs_the_line_twice(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    gate = _gate("false", NoCredentialsError(), "false")

    for _ in range(3):
        gate.is_generation_enabled()

    infos = [r for r in caplog.records if r.levelno == logging.INFO]
    assert len(infos) == 2
