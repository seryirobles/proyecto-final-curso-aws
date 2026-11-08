"""The AI switch variable defaults to on, so a plain apply never silently stops AI
(issues/ai-kill-switch-unreadable-under-shared-role E10)."""

from __future__ import annotations

import re
from pathlib import Path

# Repo root: tests/ -> backend/ -> root.
_TERRAFORM = Path(__file__).resolve().parents[2] / "terraform"
_VARIABLE = re.compile(r'variable\s+"ai_generation_enabled"\s*\{(.*?)\n\}', re.DOTALL)


def test_the_switch_variable_defaults_to_true() -> None:
    """E10 - the owner confirmed `default = true`."""
    match = _VARIABLE.search((_TERRAFORM / "variables.tf").read_text(encoding="utf-8"))
    assert match, "variable ai_generation_enabled not found in variables.tf"
    assert re.search(r"^\s*default\s*=\s*true\s*$", match.group(1), re.M)
