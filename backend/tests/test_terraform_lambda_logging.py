"""Terraform sets the JSON log format and an environment-derived application level
on every function (issues/deployed-lambdas-drop-info-logs E1, E2, E9)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# Repo root: tests/ -> backend/ -> root.
_TERRAFORM = Path(__file__).resolve().parents[2] / "terraform"
_FUNCTION = re.compile(r'resource\s+"aws_lambda_function"\s+"this"\s*\{(.*?)^\}', re.DOTALL | re.M)
_LOGGING_CONFIG = re.compile(r"logging_config\s*\{(.*?)\}", re.DOTALL)
_LEVEL_LOCAL = re.compile(r"^\s*lambda_log_level\s*=\s*(.+?)\s*$", re.M)
_ENVIRONMENTS = re.compile(r"contains\(\[([^\]]+)\],\s*var\.environment\)")
_CONDITIONAL = re.compile(
    r'var\.environment\s*(==|!=)\s*"(\w+)"\s*\?\s*"(\w+)"\s*:\s*"(\w+)"(?:\s*#.*)?'
)


def _read(name: str) -> str:
    return (_TERRAFORM / name).read_text(encoding="utf-8")


def _function_block() -> str:
    match = _FUNCTION.search(_read("lambda.tf"))
    assert match, 'resource "aws_lambda_function" "this" not found in lambda.tf'
    return match.group(1)


def _logging_attribute(name: str) -> str:
    match = _LOGGING_CONFIG.search(_function_block())
    assert match, "no logging_config block on aws_lambda_function.this"
    found = re.search(rf"^\s*{name}\s*=\s*(\S+)", match.group(1), re.M)
    assert found, f"{name} not set in logging_config"
    return found.group(1)


def _environments() -> list[str]:
    match = _ENVIRONMENTS.search(_read("variables.tf"))
    assert match, "the environment validation list was not found in variables.tf"
    return re.findall(r'"(\w+)"', match.group(1))


def _level_for(environment: str) -> str:
    match = _LEVEL_LOCAL.search(_read("locals.tf"))
    assert match, "lambda_log_level not found in locals.tf"
    conditional = _CONDITIONAL.fullmatch(match.group(1))
    assert conditional, f"lambda_log_level must derive from var.environment: {match.group(1)}"
    operator, compared, when_true, when_false = conditional.groups()
    holds = (environment == compared) if operator == "==" else (environment != compared)
    return when_true if holds else when_false


def test_the_scan_finds_the_function_and_the_environments() -> None:
    """E1, E2 - guards the scan itself: a regex miss would make the next tests vacuous."""
    assert "function_name" in _function_block()
    assert {"dev", "prod"} <= set(_environments())


def test_every_function_logs_in_json() -> None:
    """E1 - reproduction: without it the runtime stays at WARN and drops R22's record."""
    assert _logging_attribute("log_format") == '"JSON"'


def test_the_application_level_comes_from_the_local() -> None:
    """E1 - no literal on the function, so the environment rule has one home."""
    assert _logging_attribute("application_log_level") == "local.lambda_log_level"


def test_the_system_level_is_info() -> None:
    """E1 - the platform's own records, on every environment."""
    assert _logging_attribute("system_log_level") == '"INFO"'


def test_dev_logs_at_debug() -> None:
    """E2."""
    assert _level_for("dev") == "DEBUG"


@pytest.mark.parametrize("environment", [e for e in _environments() if e != "dev"])
def test_every_other_environment_logs_at_info(environment: str) -> None:
    """E2 - stg and prod alike."""
    assert _level_for(environment) == "INFO"


def test_no_variable_can_set_the_level() -> None:
    """E9 - a copied tfvars must not be able to put DEBUG in production."""
    assert not re.search(r'variable\s+"\w*log_level\w*"', _read("variables.tf"))
    assert "AWS_LAMBDA_LOG_LEVEL" not in _read("locals.tf")
