"""Tests for token validity: flat expiry and revocation (FR-AUTH-16, -11)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from planner_core.domain.session_policy import ABSOLUTE_LIMIT, is_expired, is_revoked

ISSUED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def test_is_expired_false_just_under_thirty_days() -> None:
    """R25."""
    now = ISSUED_AT + ABSOLUTE_LIMIT - timedelta(seconds=1)
    assert is_expired(ISSUED_AT, now) is False


def test_is_expired_false_at_exactly_thirty_days() -> None:
    """R25 — "more than 30 days": the exact boundary is still valid."""
    assert is_expired(ISSUED_AT, ISSUED_AT + ABSOLUTE_LIMIT) is False


def test_is_expired_true_just_past_thirty_days() -> None:
    """R25."""
    now = ISSUED_AT + ABSOLUTE_LIMIT + timedelta(seconds=1)
    assert is_expired(ISSUED_AT, now) is True


def test_is_revoked_false_when_issued_at_equals_the_marker() -> None:
    """R26."""
    assert is_revoked(ISSUED_AT, ISSUED_AT) is False


def test_is_revoked_true_when_issued_at_predates_the_marker() -> None:
    """R26."""
    marker = ISSUED_AT + timedelta(seconds=1)
    assert is_revoked(ISSUED_AT, marker) is True
