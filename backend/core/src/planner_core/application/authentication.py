"""Login, token authentication, logout and the mandatory set-password step
(FR-AUTH-02, -04, -09, -10, -11, -16). Orchestrates AccountRepository,
PasswordHasher and TokenSigner through the domain guards — no HTTP shape,
no transport decision (design.md section 0)."""

from __future__ import annotations

from dataclasses import dataclass

from planner_core.domain.authentication_guards import PasswordResetPending, SetPasswordNotPending
from planner_core.domain.login_policy import InvalidCredentials
from planner_core.domain.password_policy import validate_password
from planner_core.domain.role import Role
from planner_core.domain.session_policy import SessionExpired, is_expired, is_revoked
from planner_core.ports.accounts import AccountNotFound, AccountRecord, AccountRepository
from planner_core.ports.clock import Clock
from planner_core.ports.password_hasher import PasswordHasher
from planner_core.ports.tokens import InvalidToken, TokenSigner


@dataclass(frozen=True)
class LoginResult:
    """What a successful login returns to its caller (design.md section 8)."""

    user_id: str
    token: str
    role: Role
    password_reset_required: bool


def login(
    username: str,
    password: str,
    *,
    accounts: AccountRepository,
    hasher: PasswordHasher,
    signer: TokenSigner,
    clock: Clock,
) -> LoginResult:
    """R5, R12."""
    account = accounts.get_by_username(username)
    if account is None or not hasher.verify(password, account.password_hash):
        raise InvalidCredentials
    token = signer.issue(account.user_id, clock.now())
    return LoginResult(
        user_id=account.user_id,
        token=token,
        role=account.role,
        password_reset_required=account.password_reset_required,
    )


def authenticate(
    token: str, *, accounts: AccountRepository, signer: TokenSigner, clock: Clock
) -> AccountRecord:
    """R23, R25, R26, R27, R28."""
    try:
        auth_token = signer.verify(token)
    except InvalidToken:
        raise SessionExpired from None
    if is_expired(auth_token.issued_at, clock.now()):
        raise SessionExpired
    account = accounts.get_by_id(auth_token.user_id)
    if account is None:
        raise SessionExpired
    if is_revoked(auth_token.issued_at, account.credentials_valid_since):
        raise SessionExpired
    return account


def logout(user_id: str, *, accounts: AccountRepository, clock: Clock) -> None:
    """R24 — advances the revocation marker (design.md section 10, alternative C)."""
    accounts.revoke_credentials(user_id, clock.now())


def set_password(
    user_id: str, new_password: str, *, accounts: AccountRepository, hasher: PasswordHasher
) -> None:
    """R14, R16, R17. Does not advance credentials_valid_since — see
    design.md section 6, "Why set_password does not"."""
    account = accounts.get_by_id(user_id)
    if account is None:
        raise AccountNotFound(user_id)
    if not account.password_reset_required:
        raise SetPasswordNotPending
    validate_password(new_password)
    password_hash = hasher.hash(new_password)
    accounts.update_credentials(user_id, password_hash, False, account.credentials_valid_since)


def require_password_set(account: AccountRecord) -> None:
    """R15."""
    if account.password_reset_required:
        raise PasswordResetPending
