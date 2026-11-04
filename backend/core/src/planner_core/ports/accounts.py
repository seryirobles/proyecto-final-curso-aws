"""The account repository port: persistence for USUARIOS (docs/data_model.md section 1)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from planner_core.domain.errors import PlannerError
from planner_core.domain.role import Role


@dataclass(frozen=True)
class AccountRecord:
    """One persisted account (DatosUsuario). credentials_valid_since is the
    G-87 revocation marker (`validoDesde`): advanced whenever every token
    issued before it must stop working (feature 15 auth_flow design.md
    section 9)."""

    user_id: str
    username: str
    role: Role
    password_hash: str
    password_reset_required: bool
    credentials_valid_since: datetime


class AccountNotFound(PlannerError):
    """Raised when an operation targets a user_id absent from the repository."""

    user_id: str

    def __init__(self, user_id: str) -> None:
        super().__init__(user_id)
        self.user_id = user_id


class AccountAlreadyExists(PlannerError):
    """Raised by create() when an account with the same user_id exists (G-96)."""

    user_id: str

    def __init__(self, user_id: str) -> None:
        super().__init__(user_id)
        self.user_id = user_id


class NotAnAdmin(PlannerError):
    """Raised when an Admin-only operation targets a non-Admin account (G-96)."""

    username: str

    def __init__(self, username: str) -> None:
        super().__init__(username)
        self.username = username


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
        """Create-only. Raises UsernameAlreadyTaken if the folded username is
        reserved, AccountAlreadyExists if the user_id is taken; never overwrites."""
        ...

    def rename(self, user_id: str, new_username: str) -> None:
        """Raises AccountNotFound or UsernameAlreadyTaken. Releases the old
        reservation by looking it up, never by re-folding the old name
        (docs/data_model.md section 5.2 — the trap)."""
        ...

    def update_credentials(
        self,
        user_id: str,
        password_hash: str,
        password_reset_required: bool,
        credentials_valid_since: datetime,
    ) -> None:
        """Raises AccountNotFound. credentials_valid_since rides the same
        UpdateItem a password reset already makes (G-87, design.md section 9);
        set_password passes the account's existing value through unchanged."""
        ...

    def reset_admin_credentials(
        self, user_id: str, password_hash: str, credentials_valid_since: datetime
    ) -> None:
        """Raises AccountNotFound if the id is absent or not an Admin. Sets the
        hash, the pending flag and the revocation marker together (G-96)."""
        ...

    def delete(self, user_id: str) -> None:
        """Raises AccountNotFound. Releases the username reservation too (section 5.2)."""
        ...

    def revoke_credentials(self, user_id: str, revoked_at: datetime) -> None:
        """Raises AccountNotFound. The logout-only write (G-87, design.md
        section 9): advances credentials_valid_since with no other change."""
        ...
