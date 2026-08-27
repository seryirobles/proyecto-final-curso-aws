"""The mandatory set-password step's guard exceptions (FR-AUTH-04, -10)."""

from __future__ import annotations

from planner_core import messages
from planner_core.domain.errors import PlannerError


class PasswordResetPending(PlannerError):
    """R15 — raised for any operation but set-password while the account's
    pending-set-password flag is true."""

    def __init__(self) -> None:
        super().__init__(messages.SET_PASSWORD_REQUIRED)


class SetPasswordNotPending(PlannerError):
    """R14 — raised when set-password is invoked but the account's
    pending-set-password flag is already false."""

    def __init__(self) -> None:
        super().__init__(messages.SET_PASSWORD_NOT_ALLOWED)
