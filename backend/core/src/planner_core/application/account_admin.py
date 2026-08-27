"""Admin account management: create, rename, reset, remove, list
(FR-AUTH-03, -05, -07, -12, -13, -18). Every operation requires the Admin
role; none accepts a role parameter for the account it targets, so an
Admin-role account can never be created or removed through the application
(R9, R31 — by construction, design.md section 5)."""

from __future__ import annotations

from planner_core.domain.authorization import Forbidden, require_admin
from planner_core.domain.role import Role
from planner_core.domain.username_policy import validate_username
from planner_core.ports.accounts import AccountRecord, AccountRepository
from planner_core.ports.clock import Clock


def create_user(
    actor_role: Role,
    user_id: str,
    username: str,
    password_hash: str,
    *,
    accounts: AccountRepository,
    clock: Clock,
) -> AccountRecord:
    """R6, R7, R8, R9, R11. password_hash is computed by the caller via
    PasswordHasher, the same shape admin_set_password's new_temp_password_hash
    uses — this function stores it, it never hashes it itself."""
    require_admin(actor_role)
    validate_username(username, (account.username for account in accounts.list_all()))
    account = AccountRecord(
        user_id=user_id,
        username=username,
        role=Role.USER,
        password_hash=password_hash,
        password_reset_required=True,
        credentials_valid_since=clock.now(),
    )
    accounts.create(account)
    return account


def rename_user(
    actor_role: Role, user_id: str, new_username: str, *, accounts: AccountRepository
) -> None:
    """R7, R8 — reuses AccountRepository.rename's own uniqueness handling
    (feature 14)."""
    require_admin(actor_role)
    accounts.rename(user_id, new_username)


def admin_set_password(
    actor_role: Role,
    actor_user_id: str,
    target: AccountRecord,
    new_temp_password_hash: str,
    *,
    accounts: AccountRepository,
    clock: Clock,
) -> None:
    """R18, R19, R29, R30 — one call sets the temporary-password flag and
    advances the revocation marker together (design.md section 9, G-51)."""
    require_admin(actor_role)
    if target.user_id == actor_user_id:
        raise Forbidden(actor_role)
    accounts.update_credentials(target.user_id, new_temp_password_hash, True, clock.now())


def remove_user(actor_role: Role, target: AccountRecord, *, accounts: AccountRepository) -> None:
    """R21, R22, R23, R31. No content-repository call: an Admin-role account
    cannot be removed (R31), and a User-role removal needs no separate
    invalidation write under the stateless design (design.md section 3)."""
    require_admin(actor_role)
    if target.role is Role.ADMIN:
        raise Forbidden(actor_role)
    accounts.delete(target.user_id)


def list_accounts(actor_role: Role, *, accounts: AccountRepository) -> tuple[AccountRecord, ...]:
    """R20."""
    require_admin(actor_role)
    return accounts.list_all()
