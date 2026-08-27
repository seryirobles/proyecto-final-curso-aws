"""Tests for the login-failure exception (FR-AUTH-02)."""

from __future__ import annotations

from planner_core import messages
from planner_core.domain.login_policy import InvalidCredentials


def test_invalid_credentials_carries_the_es_es_message() -> None:
    """R12."""
    assert str(InvalidCredentials()) == messages.INVALID_CREDENTIALS
