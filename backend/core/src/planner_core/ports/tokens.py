"""Self-contained authentication tokens: user_id + issued_at, tamper-evident
via a server-side HMAC signature. No session table (G-87) — verifying a
token plus the two domain/session_policy.py predicates is the whole
"is this request authenticated" check."""

from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from planner_core.domain.errors import PlannerError

_FIELD_SEP = "|"  # user_id and issued_at.isoformat() never contain this


@dataclass(frozen=True)
class AuthToken:
    user_id: str
    issued_at: datetime


class InvalidToken(PlannerError):
    """Raised by verify() on a bad signature or a malformed token. No
    message — the caller maps it to a user-facing exception (design.md
    section 8)."""


@runtime_checkable
class TokenSigner(Protocol):
    def issue(self, user_id: str, issued_at: datetime) -> str: ...

    def verify(self, token: str) -> AuthToken:
        """Raises InvalidToken."""
        ...


class HmacTokenSigner:
    """Default implementation: HMAC-SHA256, stdlib-only — ships beside its
    Protocol per architecture.md section 1.2.2. secret_key is an injected
    constructor parameter; wiring.py sources the real one (design.md section 8)."""

    def __init__(self, secret_key: bytes) -> None:
        self._secret_key = secret_key

    def issue(self, user_id: str, issued_at: datetime) -> str:
        payload = f"{user_id}{_FIELD_SEP}{issued_at.isoformat()}".encode()
        signature = hmac.new(self._secret_key, payload, hashlib.sha256).digest()
        payload_b64 = base64.urlsafe_b64encode(payload).decode("ascii")
        signature_b64 = base64.urlsafe_b64encode(signature).decode("ascii")
        return f"{payload_b64}.{signature_b64}"

    def verify(self, token: str) -> AuthToken:
        try:
            payload_b64, signature_b64 = token.split(".", 1)
            payload = base64.urlsafe_b64decode(payload_b64)
            signature = base64.urlsafe_b64decode(signature_b64)
        except (ValueError, TypeError):
            raise InvalidToken from None
        expected = hmac.new(self._secret_key, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            raise InvalidToken
        try:
            user_id, issued_at_iso = payload.decode("utf-8").split(_FIELD_SEP, 1)
            return AuthToken(user_id=user_id, issued_at=datetime.fromisoformat(issued_at_iso))
        except ValueError:
            raise InvalidToken from None
