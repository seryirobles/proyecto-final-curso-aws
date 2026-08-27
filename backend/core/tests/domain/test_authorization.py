"""Tests for the role-based authorization guards (FR-AUTH-01, -05, -06)."""

from __future__ import annotations

import pytest

from planner_core.domain.authorization import Forbidden, require_admin, require_user
from planner_core.domain.role import Role


def test_require_admin_raises_forbidden_for_a_user_role() -> None:
    """R2."""
    with pytest.raises(Forbidden):
        require_admin(Role.USER)


def test_require_admin_passes_for_an_admin_role() -> None:
    """R2 (negative check)."""
    require_admin(Role.ADMIN)


def test_require_user_raises_forbidden_for_an_admin_role() -> None:
    """R3."""
    with pytest.raises(Forbidden):
        require_user(Role.ADMIN)


def test_require_user_passes_for_a_user_role() -> None:
    """R4."""
    require_user(Role.USER)
