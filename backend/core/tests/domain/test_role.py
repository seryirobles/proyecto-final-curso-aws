"""Tests for the Role enum (FR-AUTH-01)."""

from __future__ import annotations

from planner_core.domain.role import Role


def test_exactly_two_roles_exist() -> None:
    """R1."""
    assert len(Role) == 2
    assert Role.ADMIN in Role
    assert Role.USER in Role
