"""Token validity: a flat 30-day expiry from issuance (FR-AUTH-16, amended
by G-87), and revocation via an account-level marker (FR-AUTH-11, -14)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Final

from planner_core import messages
from planner_core.domain.errors import PlannerError

ABSOLUTE_LIMIT: Final[timedelta] = timedelta(days=30)


def is_expired(issued_at: datetime, now: datetime) -> bool:
    """R25."""
    return now - issued_at > ABSOLUTE_LIMIT


def is_revoked(issued_at: datetime, credentials_valid_since: datetime) -> bool:
    """R26. A token issued before the account's marker was last advanced
    predates whatever event advanced it (an admin reset or a self logout,
    design.md section 9) and is no longer trusted."""
    return issued_at < credentials_valid_since


class SessionExpired(PlannerError):
    """R28 — raised uniformly whether the cause is a bad signature,
    expiry, revocation, or a removed account; the caller does not get to
    distinguish them (see application/authentication.authenticate)."""

    def __init__(self) -> None:
        super().__init__(messages.SESSION_EXPIRED)
