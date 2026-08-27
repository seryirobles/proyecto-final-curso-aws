"""Tests for the PasswordHasher port and its default implementation (FR-AUTH-15)."""

from __future__ import annotations

from planner_core.ports.password_hasher import PasswordHasher, Pbkdf2PasswordHasher


def test_pbkdf2_password_hasher_satisfies_the_password_hasher_port() -> None:
    assert isinstance(Pbkdf2PasswordHasher(), PasswordHasher)


def test_hash_then_verify_round_trips_true() -> None:
    """R16."""
    hasher = Pbkdf2PasswordHasher()
    password_hash = hasher.hash("correct horse battery staple")
    assert hasher.verify("correct horse battery staple", password_hash) is True


def test_verify_with_a_wrong_password_is_false() -> None:
    """R16."""
    hasher = Pbkdf2PasswordHasher()
    password_hash = hasher.hash("correct horse battery staple")
    assert hasher.verify("wrong password entirely", password_hash) is False


def test_two_hashes_of_the_same_password_are_different_salted() -> None:
    """R16."""
    hasher = Pbkdf2PasswordHasher()
    first = hasher.hash("correct horse battery staple")
    second = hasher.hash("correct horse battery staple")
    assert first != second
    assert hasher.verify("correct horse battery staple", first) is True
    assert hasher.verify("correct horse battery staple", second) is True
