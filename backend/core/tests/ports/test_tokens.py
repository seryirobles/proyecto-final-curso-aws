"""Tests for the TokenSigner port and its default HMAC implementation (FR-AUTH-09)."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from planner_core.ports.tokens import AuthToken, HmacTokenSigner, InvalidToken, TokenSigner

ISSUED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def test_auth_token_is_frozen() -> None:
    """docs/conventions.md: every new frozen dataclass gets this test."""
    token = AuthToken(user_id="u1", issued_at=ISSUED_AT)
    with pytest.raises(dataclasses.FrozenInstanceError):
        token.__setattr__("user_id", "u2")


def test_hmac_token_signer_satisfies_the_token_signer_port() -> None:
    assert isinstance(HmacTokenSigner(b"test-secret-key"), TokenSigner)


def test_issue_then_verify_round_trips_the_same_user_id_and_issued_at() -> None:
    """R27."""
    signer = HmacTokenSigner(b"test-secret-key")
    token = signer.issue("u1", ISSUED_AT)

    assert signer.verify(token) == AuthToken(user_id="u1", issued_at=ISSUED_AT)


def test_a_tampered_payload_raises_invalid_token() -> None:
    """R27."""
    signer = HmacTokenSigner(b"test-secret-key")
    token = signer.issue("u1", ISSUED_AT)
    payload_b64, signature_b64 = token.split(".", 1)
    tampered = payload_b64 + "x" + "." + signature_b64

    with pytest.raises(InvalidToken):
        signer.verify(tampered)


def test_a_tampered_signature_raises_invalid_token() -> None:
    """R27."""
    signer = HmacTokenSigner(b"test-secret-key")
    token = signer.issue("u1", ISSUED_AT)
    payload_b64, signature_b64 = token.split(".", 1)
    tampered = payload_b64 + "." + signature_b64[:-1] + ("A" if signature_b64[-1] != "A" else "B")

    with pytest.raises(InvalidToken):
        signer.verify(tampered)


def test_a_malformed_token_raises_invalid_token() -> None:
    """R27."""
    signer = HmacTokenSigner(b"test-secret-key")

    with pytest.raises(InvalidToken):
        signer.verify("not-a-valid-token-at-all")


def test_a_token_signed_with_a_different_key_fails_verification() -> None:
    """R27."""
    signer = HmacTokenSigner(b"test-secret-key")
    other_signer = HmacTokenSigner(b"a-different-secret-key")
    token = signer.issue("u1", ISSUED_AT)

    with pytest.raises(InvalidToken):
        other_signer.verify(token)
