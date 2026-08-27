"""The password hashing port: verifying and storing credentials (FR-AUTH-15)."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Protocol, runtime_checkable

_ITERATIONS = 600_000
_SALT_BYTES = 16
_ALGORITHM = "sha256"
_FIELD_SEP = "$"


@runtime_checkable
class PasswordHasher(Protocol):
    def hash(self, password: str) -> str:
        """Return an opaque, self-contained hash suitable for storage."""
        ...

    def verify(self, password: str, password_hash: str) -> bool:
        """Return whether password matches the stored password_hash."""
        ...


class Pbkdf2PasswordHasher:
    """Default implementation: PBKDF2-HMAC-SHA256, stdlib-only (hashlib, hmac,
    secrets) — ships beside its Protocol per architecture.md section 1.2.2.
    One correct algorithm exists for this axis; only the salt differs per call.
    """

    def hash(self, password: str) -> str:
        salt = secrets.token_bytes(_SALT_BYTES)
        digest = hashlib.pbkdf2_hmac(_ALGORITHM, password.encode("utf-8"), salt, _ITERATIONS)
        return _FIELD_SEP.join(
            (_ALGORITHM, str(_ITERATIONS), salt.hex(), digest.hex()),
        )

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            algorithm, iterations_raw, salt_hex, digest_hex = password_hash.split(_FIELD_SEP)
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(digest_hex)
        except ValueError:
            return False
        candidate = hashlib.pbkdf2_hmac(
            algorithm, password.encode("utf-8"), salt, int(iterations_raw)
        )
        return hmac.compare_digest(candidate, expected)
