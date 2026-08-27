"""Tests for login, token authentication, logout and set-password
(FR-AUTH-02, -04, -09, -10, -11, -16)."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta

import pytest
from support.fakes import FakeAccountRepository, FakeClock, FakePasswordHasher

from planner_core.application.authentication import (
    LoginResult,
    authenticate,
    login,
    logout,
    require_password_set,
    set_password,
)
from planner_core.domain.authentication_guards import PasswordResetPending, SetPasswordNotPending
from planner_core.domain.login_policy import InvalidCredentials
from planner_core.domain.password_policy import PasswordTooShort
from planner_core.domain.role import Role
from planner_core.domain.session_policy import SessionExpired
from planner_core.ports.accounts import AccountRecord
from planner_core.ports.tokens import HmacTokenSigner

SECRET_KEY = b"test-secret-key"
CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def _account(
    *,
    user_id: str = "u1",
    username: str = "Ana",
    role: Role = Role.USER,
    password: str = "correct horse battery staple",
    password_reset_required: bool = False,
    credentials_valid_since: datetime = CREATED_AT,
) -> tuple[AccountRecord, FakeAccountRepository, FakePasswordHasher]:
    hasher = FakePasswordHasher()
    accounts = FakeAccountRepository()
    account = AccountRecord(
        user_id=user_id,
        username=username,
        role=role,
        password_hash=hasher.hash(password),
        password_reset_required=password_reset_required,
        credentials_valid_since=credentials_valid_since,
    )
    accounts.create(account)
    return account, accounts, hasher


def test_login_result_is_frozen() -> None:
    """docs/conventions.md: every new frozen dataclass gets this test."""
    result = LoginResult(user_id="u1", token="t", role=Role.USER, password_reset_required=False)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.__setattr__("user_id", "u2")


def test_login_with_unknown_username_raises_invalid_credentials() -> None:
    """R12."""
    _, accounts, hasher = _account()
    signer = HmacTokenSigner(SECRET_KEY)
    clock = FakeClock.at("2026-01-02T00:00:00+00:00")

    with pytest.raises(InvalidCredentials):
        login("nadie", "whatever", accounts=accounts, hasher=hasher, signer=signer, clock=clock)


def test_login_with_wrong_password_raises_invalid_credentials() -> None:
    """R12."""
    account, accounts, hasher = _account()
    signer = HmacTokenSigner(SECRET_KEY)
    clock = FakeClock.at("2026-01-02T00:00:00+00:00")

    with pytest.raises(InvalidCredentials):
        login(
            account.username,
            "wrong password entirely",
            accounts=accounts,
            hasher=hasher,
            signer=signer,
            clock=clock,
        )


def test_successful_login_returns_a_token_carrying_role_and_pending_flag() -> None:
    """R5, R11."""
    account, accounts, hasher = _account(role=Role.ADMIN, password_reset_required=True)
    signer = HmacTokenSigner(SECRET_KEY)
    clock = FakeClock.at("2026-01-02T00:00:00+00:00")

    result = login(
        account.username,
        "correct horse battery staple",
        accounts=accounts,
        hasher=hasher,
        signer=signer,
        clock=clock,
    )

    assert result == LoginResult(
        user_id=account.user_id,
        token=result.token,
        role=Role.ADMIN,
        password_reset_required=True,
    )
    assert signer.verify(result.token).user_id == account.user_id


def test_authenticate_with_tampered_token_raises_session_expired() -> None:
    """R27, R28."""
    account, accounts, _ = _account()
    signer = HmacTokenSigner(SECRET_KEY)
    clock = FakeClock.at("2026-01-02T00:00:00+00:00")
    token = signer.issue(account.user_id, clock.now())
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")

    with pytest.raises(SessionExpired):
        authenticate(tampered, accounts=accounts, signer=signer, clock=clock)


def test_authenticate_with_a_31_day_old_token_raises_session_expired() -> None:
    """R25, R28."""
    account, accounts, _ = _account()
    signer = HmacTokenSigner(SECRET_KEY)
    issued_at = datetime(2026, 1, 1, tzinfo=UTC)
    token = signer.issue(account.user_id, issued_at)
    clock = FakeClock(issued_at + timedelta(days=31))

    with pytest.raises(SessionExpired):
        authenticate(token, accounts=accounts, signer=signer, clock=clock)


def test_authenticate_with_token_issued_before_the_revocation_marker_raises_session_expired() -> (
    None
):
    """R26, R28."""
    marker = datetime(2026, 1, 5, tzinfo=UTC)
    account, accounts, _ = _account(credentials_valid_since=marker)
    signer = HmacTokenSigner(SECRET_KEY)
    token = signer.issue(account.user_id, marker - timedelta(seconds=1))
    clock = FakeClock(marker)

    with pytest.raises(SessionExpired):
        authenticate(token, accounts=accounts, signer=signer, clock=clock)


def test_authenticate_denies_a_removed_accounts_token() -> None:
    """R23, R27."""
    account, accounts, _ = _account()
    signer = HmacTokenSigner(SECRET_KEY)
    clock = FakeClock.at("2026-01-02T00:00:00+00:00")
    token = signer.issue(account.user_id, clock.now())
    accounts.delete(account.user_id)

    with pytest.raises(SessionExpired):
        authenticate(token, accounts=accounts, signer=signer, clock=clock)


def test_authenticate_succeeds_for_a_valid_recent_token() -> None:
    """R27."""
    account, accounts, _ = _account()
    signer = HmacTokenSigner(SECRET_KEY)
    clock = FakeClock.at("2026-01-02T00:00:00+00:00")
    token = signer.issue(account.user_id, clock.now())

    resolved = authenticate(token, accounts=accounts, signer=signer, clock=clock)

    assert resolved == account


def test_logout_advances_the_revocation_marker() -> None:
    """R24."""
    account, accounts, _ = _account()
    signer = HmacTokenSigner(SECRET_KEY)
    issue_clock = FakeClock.at("2026-01-02T00:00:00+00:00")
    token = signer.issue(account.user_id, issue_clock.now())
    logout_clock = FakeClock.at("2026-01-03T00:00:00+00:00")

    logout(account.user_id, accounts=accounts, clock=logout_clock)

    with pytest.raises(SessionExpired):
        authenticate(token, accounts=accounts, signer=signer, clock=logout_clock)


def test_set_password_rejects_when_not_pending() -> None:
    """R14."""
    account, accounts, hasher = _account(password_reset_required=False)

    with pytest.raises(SetPasswordNotPending):
        set_password(
            account.user_id, "a new long enough password", accounts=accounts, hasher=hasher
        )


def test_set_password_rejects_a_too_short_password() -> None:
    """R16."""
    account, accounts, hasher = _account(password_reset_required=True)

    with pytest.raises(PasswordTooShort):
        set_password(account.user_id, "short", accounts=accounts, hasher=hasher)


def test_set_password_clears_the_pending_flag_without_advancing_the_marker() -> None:
    """R17."""
    marker = datetime(2026, 1, 1, tzinfo=UTC)
    account, accounts, hasher = _account(
        password_reset_required=True, credentials_valid_since=marker
    )
    signer = HmacTokenSigner(SECRET_KEY)
    clock = FakeClock(marker + timedelta(seconds=1))
    token = signer.issue(account.user_id, clock.now())

    set_password(account.user_id, "a new long enough password", accounts=accounts, hasher=hasher)

    updated = accounts.get_by_id(account.user_id)
    assert updated is not None
    assert updated.password_reset_required is False
    assert updated.credentials_valid_since == marker
    assert authenticate(token, accounts=accounts, signer=signer, clock=clock) == updated


def test_require_password_set_raises_pending_when_flag_true() -> None:
    """R15."""
    account, _, _ = _account(password_reset_required=True)

    with pytest.raises(PasswordResetPending):
        require_password_set(account)
