"""Tests for username uniqueness and placeholder reservation (R5-R7)."""

from __future__ import annotations

import pytest

from planner_core import messages
from planner_core.domain.username_policy import (
    UsernameAlreadyTaken,
    UsernameReserved,
    validate_username,
)


def test_username_matching_an_active_account_case_and_accent_insensitively_raises() -> None:
    """R5, R6: normalized equality catches case/accent variants."""
    with pytest.raises(UsernameAlreadyTaken) as excinfo:
        validate_username("jose", active_usernames=("José",))

    assert excinfo.value.username == "jose"
    assert str(excinfo.value) == messages.USERNAME_ALREADY_TAKEN


def test_username_absent_from_active_usernames_is_not_rejected() -> None:
    """R6 negative case: no collision, no raise."""
    validate_username("marta", active_usernames=("jose", "ana"))


def test_username_matching_the_reserved_placeholder_name_raises_username_reserved() -> None:
    """R5, R7: reservation folds the same way as uniqueness."""
    with pytest.raises(UsernameReserved) as excinfo:
        validate_username("Usuario Desconocido", active_usernames=())

    assert str(excinfo.value) == messages.USERNAME_RESERVED


def test_reserved_name_check_wins_over_a_stray_active_usernames_entry() -> None:
    """R7: reservation is checked before uniqueness (design.md section 6)."""
    with pytest.raises(UsernameReserved):
        validate_username("Usuario Desconocido", active_usernames=("usuario desconocido",))


def test_removed_accounts_username_is_not_rejected_when_absent_from_active_usernames() -> None:
    """R6 negative case: reuse-after-removal is the caller's contract, not this function's."""
    validate_username("jose", active_usernames=("ana",))
