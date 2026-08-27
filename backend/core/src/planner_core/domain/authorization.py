"""Role-based access guards (FR-AUTH-01, -05, -06, -18)."""

from __future__ import annotations

from planner_core import messages
from planner_core.domain.errors import PlannerError
from planner_core.domain.role import Role


class Forbidden(PlannerError):
    """Raised when an actor's role does not permit the requested operation."""

    role: Role

    def __init__(self, role: Role) -> None:
        super().__init__(messages.FORBIDDEN)
        self.role = role


def require_admin(role: Role) -> None:
    """Raise Forbidden unless role is Role.ADMIN (R2)."""
    if role is not Role.ADMIN:
        raise Forbidden(role)


def require_user(role: Role) -> None:
    """Raise Forbidden unless role is Role.USER (R3)."""
    if role is not Role.USER:
        raise Forbidden(role)
