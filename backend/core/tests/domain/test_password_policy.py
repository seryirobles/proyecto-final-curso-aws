"""Tests for password acceptability under NIST SP 800-63B (R1-R4)."""

from __future__ import annotations

import inspect

import pytest

from planner_core import messages
from planner_core.domain.password_policy import PasswordTooShort, validate_password


def test_password_shorter_than_ten_raises_password_too_short() -> None:
    """R1: a 9-character password is rejected with the es-ES message."""
    with pytest.raises(PasswordTooShort) as excinfo:
        validate_password("nine9char")

    assert excinfo.value.min_length == 10
    assert excinfo.value.actual_length == 9
    assert str(excinfo.value) == messages.PASSWORD_TOO_SHORT


def test_password_of_exactly_ten_characters_is_not_rejected_for_length() -> None:
    """R1 boundary: exactly MIN_LENGTH is acceptable."""
    validate_password("ten1234567")


def test_password_of_two_hundred_characters_is_accepted() -> None:
    """R2: no ceiling below at least 64 (design.md section 7 alternative A)."""
    validate_password("a" * 200)


def test_all_lowercase_password_is_not_rejected_for_composition() -> None:
    """R3: no character-class rule."""
    validate_password("alllowercase")


def test_all_digit_password_is_not_rejected_for_composition() -> None:
    """R3: no character-class rule, digits case."""
    validate_password("1234567890")


def test_validate_password_signature_has_no_age_or_rotation_parameter() -> None:
    """R4: no age/last-changed/rotation-count parameter exists to omit."""
    assert set(inspect.signature(validate_password).parameters.keys()) == {"password"}
