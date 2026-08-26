"""The account repository port: persistence for USUARIOS (docs/data_model.md section 1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from planner_core.domain.errors import PlannerError


@dataclass(frozen=True)
class AccountRecord:
    """One persisted account (DatosUsuario). role is an opaque string here —
    no domain Role model exists yet; feature 15 auth_flow owns that (design.md section 7)."""

    user_id: str
    username: str
    role: str
    password_hash: str
    password_reset_required: bool


class AccountNotFound(PlannerError):
    """Raised when an operation targets a user_id absent from the repository."""

    user_id: str

    def __init__(self, user_id: str) -> None:
        super().__init__(user_id)
        self.user_id = user_id


@runtime_checkable
class AccountRepository(Protocol):
    """Persistence for user accounts and the username reservation (FR-AUTH-17,
    docs/data_model.md section 5.1, section 5.2). Username uniqueness and the
    rename-releases-its-reservation lookup are the implementation's job, not
    the caller's: create() and rename() are each one atomic operation from
    the caller's point of view."""

    def get_by_id(self, user_id: str) -> AccountRecord | None: ...

    def get_by_username(self, username: str) -> AccountRecord | None:
        """Case-/accent-/whitespace-insensitive match (docs/data_model.md section 2, the fold)."""
        ...

    def list_all(self) -> tuple[AccountRecord, ...]: ...

    def create(self, account: AccountRecord) -> None:
        """Raises UsernameAlreadyTaken if the folded username is already reserved."""
        ...

    def rename(self, user_id: str, new_username: str) -> None:
        """Raises AccountNotFound or UsernameAlreadyTaken. Releases the old
        reservation by looking it up, never by re-folding the old name
        (docs/data_model.md section 5.2 — the trap)."""
        ...

    def update_credentials(
        self, user_id: str, password_hash: str, password_reset_required: bool
    ) -> None:
        """Raises AccountNotFound."""
        ...

    def delete(self, user_id: str) -> None:
        """Raises AccountNotFound. Releases the username reservation too (section 5.2)."""
        ...
