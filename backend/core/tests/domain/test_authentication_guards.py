"""Tests for the set-password guard exceptions (FR-AUTH-04, -10)."""

from __future__ import annotations

from planner_core import messages
from planner_core.domain.authentication_guards import PasswordResetPending, SetPasswordNotPending


def test_password_reset_pending_carries_the_es_es_message() -> None:
    """R15."""
    assert str(PasswordResetPending()) == messages.SET_PASSWORD_REQUIRED


def test_set_password_not_pending_carries_the_es_es_message() -> None:
    """R14."""
    assert str(SetPasswordNotPending()) == messages.SET_PASSWORD_NOT_ALLOWED
