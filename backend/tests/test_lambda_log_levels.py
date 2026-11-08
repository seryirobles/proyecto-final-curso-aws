"""What reaches the log from each deployed entry point, one fresh process per case
(issues/deployed-lambdas-drop-info-logs). Moto and fake values; see _lambda_log_probe.py."""

from __future__ import annotations

import functools
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

_PROBE = Path(__file__).with_name("_lambda_log_probe.py")
# Moto is this harness's own logger; it does not ship.
_NOT_THIRD_PARTY = ("planner_api", "planner_ai", "planner_core", "moto")
_SDK_PATHS = ("api", "authorizer", "rollover", "ai")
_ROOT_CASES = (
    ("api", "DEBUG"),
    ("api", "INFO"),
    ("authorizer", "DEBUG"),
    ("authorizer", "INFO"),
    ("authorizer-deny", "INFO"),
    ("rollover", "DEBUG"),
    ("rollover", "INFO"),
    ("ai", "DEBUG"),
    ("ai", "INFO"),
)


@functools.cache
def _run(scenario: str, level: str) -> dict[str, Any]:
    done = subprocess.run(
        [sys.executable, str(_PROBE), scenario, level],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    report: dict[str, Any] = json.loads(done.stdout)
    return report


def _texts(report: dict[str, Any]) -> list[str]:
    return [str(record["text"]) for record in report["records"]]


def test_the_probe_reaches_the_sensitive_calls() -> None:
    """E5 - guards the probe: a run that stopped early would make the leak tests vacuous."""
    assert _run("api", "DEBUG")["result"]["statusCode"] == 200
    allow = _run("authorizer", "DEBUG")["result"]
    assert allow["policyDocument"]["Statement"][0]["Effect"] == "Allow"
    assert _run("rollover", "DEBUG")["result"]["status"] == "ok"
    assert any("AI provider failed" in text for text in _texts(_run("ai", "DEBUG")))


@pytest.mark.parametrize(
    ("scenario", "secrets"), [("api", 2), ("authorizer", 2), ("ai", 1)], ids=["api", "auth", "ai"]
)
def test_no_secret_reaches_the_log_at_root_debug(scenario: str, secrets: int) -> None:
    """E5 - reproduction: the session key, a passHash and the Bedrock bearer token."""
    report = _run(scenario, "DEBUG")

    assert len(report["secrets"]) == secrets
    leaked = [s for s in report["secrets"] if any(s in text for text in _texts(report))]
    assert leaked == []


@pytest.mark.parametrize("scenario", _SDK_PATHS)
def test_each_entry_point_leaves_the_sdk_loggers_at_warning(scenario: str) -> None:
    """E4 - all four names, children included, whichever of them this path exercises."""
    levels = _run(scenario, "DEBUG")["sdk_levels"]

    assert {name.split(".")[0] for name in levels} == {"boto3", "botocore", "urllib3", "s3transfer"}
    assert {name: level for name, level in levels.items() if level != logging.WARNING} == {}


@pytest.mark.parametrize("level", ["DEBUG", "INFO"])
@pytest.mark.parametrize("scenario", _SDK_PATHS)
def test_no_third_party_record_below_warning_reaches_the_log(scenario: str, level: str) -> None:
    """E6 - also the guard on the list: a logger outside the four names fails here."""
    noisy = {
        str(record["logger"])
        for record in _run(scenario, level)["records"]
        if int(record["level"]) < logging.WARNING
        and not str(record["logger"]).startswith(_NOT_THIRD_PARTY)
    }

    assert noisy == set()


@pytest.mark.parametrize("scenario", _SDK_PATHS)
def test_an_app_debug_line_still_reaches_the_log_at_root_debug(scenario: str) -> None:
    """E10 - the dev level stays useful: only the SDK loggers are quieted."""
    assert any("app-debug-line" in text for text in _texts(_run(scenario, "DEBUG")))


@pytest.mark.parametrize(
    ("scenario", "line"),
    [
        ("api", "Handled request POST /v1/session -> 200"),
        ("authorizer-deny", "Denying authorizer request with no session cookie"),
        ("rollover", "Rollover completed for week"),
        ("ai", "Processed single-recipe generation"),
    ],
    ids=["api", "authorizer-deny", "rollover", "ai"],
)
def test_the_per_invocation_record_reaches_the_log_at_root_info(scenario: str, line: str) -> None:
    """E3 - R22: INFO is enough; the record does not depend on the dev level."""
    report = _run(scenario, "INFO")

    assert any(
        line in str(record["text"]) and int(record["level"]) == logging.INFO
        for record in report["records"]
    )
    assert not any("app-debug-line" in text for text in _texts(report))


@pytest.mark.parametrize(("scenario", "level"), _ROOT_CASES)
def test_the_entry_point_leaves_the_root_level_alone(scenario: str, level: str) -> None:
    """E7 - Terraform owns the root level; AWS gives code precedence over it."""
    assert _run(scenario, level)["root_level_after"] == logging.getLevelName(level)
