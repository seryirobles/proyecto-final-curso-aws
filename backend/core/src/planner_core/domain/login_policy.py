"""Login failure (FR-AUTH-02). Brute-force lockout moved to infrastructure
(feature 21, G-87) — this module carries no attempt-counting state."""

from __future__ import annotations

from planner_core import messages
from planner_core.domain.errors import PlannerError


class InvalidCredentials(PlannerError):
    """R12 — raised identically for an unknown username or a wrong password;
    no argument distinguishes the cause (requirements.md revision note)."""

    def __init__(self) -> None:
        super().__init__(messages.INVALID_CREDENTIALS)
