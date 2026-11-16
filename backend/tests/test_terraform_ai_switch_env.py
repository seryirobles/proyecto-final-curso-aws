"""Terraform hands the ai Lambda the variable the wiring reads; without it the
deployed gate stays the SSM one the shared role cannot read."""

from __future__ import annotations

import re
from pathlib import Path

# Repo root: tests/ -> backend/ -> root.
_TERRAFORM = Path(__file__).resolve().parents[2] / "terraform"
# The literal map only: merge() lets it win over var.ai_inference_settings.
_AI_ENV = re.compile(
    r"ai_env\s*=\s*merge\(var\.ai_inference_settings,\s*\{(.*?)\n\s*\}\)", re.DOTALL
)
_VARIABLE = re.compile(r'variable\s+"ai_generation_enabled"\s*\{(.*?)\n\}', re.DOTALL)


def _ai_env() -> str:
    match = _AI_ENV.search((_TERRAFORM / "locals.tf").read_text(encoding="utf-8"))
    assert match, "ai_env block not found in locals.tf"
    return match.group(1)


def test_the_scan_finds_the_ai_env_map() -> None:
    """E10 - guards the scan itself: a regex miss would make the next test vacuous."""
    assert "PLANNER_DATA_TABLE" in _ai_env()


def test_the_ai_env_carries_the_switch_from_the_variable() -> None:
    """E10."""
    assert re.search(r"^\s*AI_GENERATION_SWITCH\s*=.*var\.ai_generation_enabled", _ai_env(), re.M)


def test_the_switch_variable_is_a_bool() -> None:
    """E10 - a bool renders exactly "true" or "false", so a typo fails at plan time."""
    match = _VARIABLE.search((_TERRAFORM / "variables.tf").read_text(encoding="utf-8"))
    assert match, "variable ai_generation_enabled not found in variables.tf"
    assert re.search(r"^\s*type\s*=\s*bool\s*$", match.group(1), re.M)
