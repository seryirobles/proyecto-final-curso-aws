"""Smoke test proving the planner_core scaffold is importable (feature 1)."""

from __future__ import annotations

import planner_core
from planner_core import application, domain, ports


def test_planner_core_and_its_subpackages_are_importable() -> None:
    assert planner_core.__name__ == "planner_core"
    assert domain.__name__ == "planner_core.domain"
    assert application.__name__ == "planner_core.application"
    assert ports.__name__ == "planner_core.ports"
