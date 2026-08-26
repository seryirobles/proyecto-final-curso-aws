"""Username uniqueness among active accounts, and the reservation of the
"unknown user" placeholder name (FR-AUTH-17, G-42, G-58)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

from planner_core import messages
from planner_core.domain.errors import PlannerError
from planner_core.domain.text import normalize

# Value settled at feature 5's gate (docs/data_model.md section 5.1);
# enforced, not chosen here.
UNKNOWN_USER_NAME: Final[str] = "usuario desconocido"


class UsernameReserved(PlannerError):
    """Raised when a candidate username folds to the placeholder's name (R7)."""

    username: str

    def __init__(self, username: str) -> None:
        super().__init__(messages.USERNAME_RESERVED)
        self.username = username


class UsernameAlreadyTaken(PlannerError):
    """Raised when a candidate username folds to an existing active one (R6)."""

    username: str

    def __init__(self, username: str) -> None:
        super().__init__(messages.USERNAME_ALREADY_TAKEN)
        self.username = username


def validate_username(username: str, active_usernames: Iterable[str]) -> None:
    """Raise on a case-/accent-insensitive collision; return None otherwise.

    Caller contract: active_usernames holds only ACTIVE accounts' current
    usernames (a removed account's name may be reused, FR-AUTH-17) and, on a
    rename, excludes the account's own current username first (self-rename
    to an unchanged name must not collide with itself).
    """
    folded = normalize(username)
    if folded == normalize(UNKNOWN_USER_NAME):
        raise UsernameReserved(username)
    if any(folded == normalize(existing) for existing in active_usernames):
        raise UsernameAlreadyTaken(username)
