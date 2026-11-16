"""Login costs one real PBKDF2 whether or not the username exists (NFR-SEC-04).
Counts calls to hashlib.pbkdf2_hmac under the real hasher."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import Any

import pytest
from support.fakes import FakeAccountRepository, FakeClock

from planner_core.application.authentication import login
from planner_core.domain.login_policy import InvalidCredentials
from planner_core.domain.role import Role
from planner_core.ports.accounts import AccountRecord
from planner_core.ports.password_hasher import Pbkdf2PasswordHasher
from planner_core.ports.tokens import HmacTokenSigner

PASSWORD = "correct horse battery staple"
CLOCK = FakeClock.at("2026-01-02T00:00:00+00:00")
SIGNER = HmacTokenSigner(b"test-secret-key")


@pytest.fixture(scope="module")
def stored_hash() -> str:
    return Pbkdf2PasswordHasher().hash(PASSWORD)


@pytest.fixture
def pbkdf2_calls(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, int]]:
    """Records (algorithm, iterations) of every PBKDF2 run; still runs it."""
    calls: list[tuple[str, int]] = []
    real: Callable[..., bytes] = hashlib.pbkdf2_hmac

    def spy(name: str, password: bytes, salt: bytes, iterations: int, *a: Any) -> bytes:
        calls.append((name, iterations))
        return real(name, password, salt, iterations, *a)

    monkeypatch.setattr(hashlib, "pbkdf2_hmac", spy)
    return calls


def _accounts(stored_hash: str) -> FakeAccountRepository:
    accounts = FakeAccountRepository()
    accounts.create(
        AccountRecord(
            user_id="u1",
            username="Ana",
            role=Role.USER,
            password_hash=stored_hash,
            password_reset_required=False,
            credentials_valid_since=CLOCK.now(),
        )
    )
    return accounts


def _attempt(username: str, password: str, stored_hash: str) -> None:
    login(
        username,
        password,
        accounts=_accounts(stored_hash),
        hasher=Pbkdf2PasswordHasher(),
        signer=SIGNER,
        clock=CLOCK,
    )


def _stored_params(stored_hash: str) -> tuple[str, int]:
    algorithm, iterations, _, _ = stored_hash.split("$")
    return algorithm, int(iterations)


def test_unknown_username_login_runs_one_pbkdf2_with_the_real_parameters(
    stored_hash: str, pbkdf2_calls: list[tuple[str, int]]
) -> None:
    """E1 — reproduction: today the unknown-username path runs none."""
    with pytest.raises(InvalidCredentials):
        _attempt("nadie", PASSWORD, stored_hash)
    assert pbkdf2_calls == [_stored_params(stored_hash)]


def test_unknown_username_costs_the_same_as_a_wrong_password(
    stored_hash: str, pbkdf2_calls: list[tuple[str, int]]
) -> None:
    """E1, E2."""
    with pytest.raises(InvalidCredentials):
        _attempt("Ana", "wrong password entirely", stored_hash)
    wrong_password = list(pbkdf2_calls)
    pbkdf2_calls.clear()
    for _ in range(2):  # no first-call warm-up cost either
        with pytest.raises(InvalidCredentials):
            _attempt("nadie", "wrong password entirely", stored_hash)
        assert pbkdf2_calls == wrong_password
        pbkdf2_calls.clear()


def test_unknown_username_is_denied_even_with_any_password(
    stored_hash: str, pbkdf2_calls: list[tuple[str, int]]
) -> None:
    """E2 — the dummy hash matches no password, the empty one included."""
    for password in ("", PASSWORD, "nadie"):
        with pytest.raises(InvalidCredentials):
            _attempt("nadie", password, stored_hash)


def test_correct_password_still_logs_in_with_one_pbkdf2(
    stored_hash: str, pbkdf2_calls: list[tuple[str, int]]
) -> None:
    """E3 — regression: the existing-account path is unchanged."""
    _attempt("Ana", PASSWORD, stored_hash)
    assert pbkdf2_calls == [_stored_params(stored_hash)]
