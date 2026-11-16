"""Every Lambda handler string Terraform deploys resolves to a callable with
AWS's `(event, context)` shape."""

from __future__ import annotations

import importlib
import inspect
import re
from collections.abc import Callable
from pathlib import Path

import pytest

# Repo root: tests/ -> backend/ -> root.
_TERRAFORM = Path(__file__).resolve().parents[2] / "terraform"
_HANDLER = re.compile(r'^\s*handler\s*=\s*"([\w.]+)"', re.MULTILINE)
_POSITIONAL = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)


def _handler_strings() -> list[str]:
    found = {
        match
        for tf in sorted(_TERRAFORM.glob("*.tf"))
        for match in _HANDLER.findall(tf.read_text(encoding="utf-8"))
    }
    return sorted(found)


def _resolve(dotted: str) -> Callable[..., object]:
    module_name, _, attribute = dotted.rpartition(".")
    entry: Callable[..., object] = getattr(importlib.import_module(module_name), attribute)
    assert callable(entry), f"{dotted} is not callable"
    return entry


def test_terraform_declares_the_four_known_entry_points() -> None:
    """E6 - guards the scan itself: a regex miss would make the next test vacuous."""
    assert _handler_strings() == [
        "planner_ai.handler.lambda_handler",
        "planner_api.authorizer.lambda_handler",
        "planner_api.handler.lambda_handler",
        "planner_api.scheduled.lambda_handler",
    ]


@pytest.mark.parametrize("dotted", _handler_strings())
def test_each_deployed_handler_takes_exactly_event_and_context(dotted: str) -> None:
    """E6 - AWS passes both positionally; a defaulted second slot is an injection seam."""
    params = list(inspect.signature(_resolve(dotted)).parameters.values())

    assert len(params) == 2, f"{dotted}: {params}"
    assert all(p.kind in _POSITIONAL for p in params), f"{dotted}: {params}"
    assert all(p.default is inspect.Parameter.empty for p in params), f"{dotted}: {params}"
