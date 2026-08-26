"""Password acceptability under NIST SP 800-63B for the mandatory
set-password step (FR-AUTH-15): a length floor, no composition rules, no
rotation (G-30)."""

from __future__ import annotations

from typing import Final

from planner_core import messages
from planner_core.domain.errors import PlannerError

MIN_LENGTH: Final[int] = 10


class PasswordTooShort(PlannerError):
    """Raised when a password is shorter than MIN_LENGTH (R1)."""

    min_length: int
    actual_length: int

    def __init__(self, min_length: int, actual_length: int) -> None:
        super().__init__(messages.PASSWORD_TOO_SHORT)
        self.min_length = min_length
        self.actual_length = actual_length


def validate_password(password: str) -> None:
    """Raise on the first rule violated; return None if password is acceptable.

    No parameter represents age, last-changed date or rotation count (R4) —
    there is nothing to omit, since none exists in this signature at all.
    """
    length = len(password)
    if length < MIN_LENGTH:
        raise PasswordTooShort(MIN_LENGTH, length)
