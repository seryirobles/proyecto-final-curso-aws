# auth_flow — Design

> Feature 15 · tier 3 · `planner_core.domain` + `planner_core.ports` +
> `planner_core.application` + `backend/core/tests/support`
> Read `requirements.md` first. Depends on feature 9 `password_policy` (done)
> and feature 14 `persistence_ports` (done); unblocked by architecture P2
> (`docs/architecture.md` §1.2.3, decided 2026-08-27).

## Revision note (2026-08-27) — amended per `G-87`, in place

This is a revision of a rejected first pass. The human rejected the
`DatosSesion` item type, per-session tracking, and the app-level
brute-force lockout counter at the design gate;
`docs/gaps_and_resolutions.md` Part W / `G-87` records the full reasoning.
**§6, §7 and §8 are rewritten; §9 is rewritten; §10's three rejected
alternatives are replaced (the old ones are moot).** §0, §3, §4, §5 are
unchanged from the first pass — the human approved `Role` and the
authorization guards specifically; nothing here revisits them.

## 0. What this feature is, and is not

**Is:** the application-managed auth mechanism — login, logout,
authenticate-a-token, the mandatory set-password step, admin
create/rename/reset/remove-user operations, and role-based authorization
guards. All of it is `planner_core` domain/application/port code: pure
logic plus port interfaces and their stdlib-only default implementations,
exactly the shape `persistence_ports` (feature 14) already established.
Authentication is **stateless** (`G-87`): no session table, no per-request
database write for the expiry check.

**Is not:** an HTTP layer, and not a brute-force-protection mechanism.
No `handler.py`, no REST verbs, no cookie/bearer wiring — `docs/
architecture.md` §2 P5/P6, still pending and human-owned. Every use case
below takes and returns plain values (`user_id`, a token string, records) —
never an HTTP request/response shape, and never a decision about how a
token travels. `NFR-SEC-04` (brute-force lockout) is out of this feature
entirely — feature 21, Terraform, `G-87` point 4.

## 1. Layering

`docs/architecture.md` §3, §3.1:

| Piece | Layer | Why |
|---|---|---|
| `Role`, `Forbidden`, `require_admin`, `require_user` | `domain/` | Pure — unchanged from the first pass. |
| `is_expired`, `is_revoked`, `SessionExpired`, `ABSOLUTE_LIMIT` | `domain/session_policy.py` | Pure — takes plain `datetime`s, never a `Clock`. Rewritten: no more `SessionState`/`last_activity_at`. |
| `InvalidCredentials` | `domain/login_policy.py` | Pure. Rewritten: no more `LoginAttemptState`/lockout functions — those moved to feature 21's infrastructure, not `planner_core`. |
| `PasswordResetPending`, `SetPasswordNotPending` | `domain/authentication_guards.py` | Pure guard exceptions, same shape as `Forbidden`. Split out of `application/authentication.py` so a pure domain test can exercise them without any port. |
| `PasswordHasher` + default `Pbkdf2PasswordHasher` | `ports/` | Unchanged from the first pass — `docs/architecture.md` §1.2.2: one correct implementation, but a real 600k-iteration run would slow every test. |
| `TokenSigner` + default `HmacTokenSigner` | `ports/tokens.py` | Same §1.2.2 reasoning, for a different runtime-environment axis: the *secret key* differs by environment (a fixed test key vs. a real deployed secret), even though the signing algorithm itself does not. Replaces the first pass's `TokenGenerator`/`SystemTokenGenerator` (opaque random session ids) — there is no session id left to generate. |
| `login`, `authenticate`, `logout`, `set_password`, `require_password_set` | `application/authentication.py` | Orchestrates `AccountRepository`, `PasswordHasher`, `TokenSigner`, `Clock` through the domain guards. |
| `create_user`, `rename_user`, `admin_set_password`, `remove_user`, `list_accounts` | `application/account_admin.py` | Unchanged in shape from the first pass; `remove_user`'s body is simpler (§3 — no session-invalidation call left to make). |
| `FakePasswordHasher` | `backend/core/tests/support/fakes.py` | Unchanged — needed for test speed. |

**No `FakeTokenSigner`.** `HmacTokenSigner` has no internal randomness and
reads no ambient state (`issued_at` is a parameter, not read from a clock
inside it) — it is already fully deterministic given a fixed `secret_key`.
Tests construct `HmacTokenSigner(b"test-secret-key")` directly, the same
way a test might construct any other pure value — no fake earns its keep
here. **No `SessionRepository`, no contract suite for it** — nothing left
to persist.

No `handler.py`, no `wiring.py` change — both live in `lambda_api`, empty
until P5/P6.

## 2. Files

### Created

| Path | Contents |
|---|---|
| `backend/core/src/planner_core/domain/role.py` | `Role` enum. Unchanged from the first pass. |
| `backend/core/src/planner_core/domain/authorization.py` | `Forbidden`, `require_admin`, `require_user`. Unchanged. |
| `backend/core/src/planner_core/domain/session_policy.py` | `is_expired`, `is_revoked`, `SessionExpired`, `ABSOLUTE_LIMIT`. Rewritten (§6). |
| `backend/core/src/planner_core/domain/login_policy.py` | `InvalidCredentials` only. Rewritten (§7) — everything else cut. |
| `backend/core/src/planner_core/domain/authentication_guards.py` | `PasswordResetPending`, `SetPasswordNotPending`. |
| `backend/core/src/planner_core/ports/password_hasher.py` | `PasswordHasher`, `Pbkdf2PasswordHasher`. Unchanged from the first pass. |
| `backend/core/src/planner_core/ports/tokens.py` | `AuthToken`, `InvalidToken`, `TokenSigner`, `HmacTokenSigner`. Rewritten (§8). |
| `backend/core/src/planner_core/application/authentication.py` | `login`, `authenticate`, `logout`, `set_password`, `require_password_set`. |
| `backend/core/src/planner_core/application/account_admin.py` | `create_user`, `rename_user`, `admin_set_password`, `remove_user`, `list_accounts`. |
| `backend/core/tests/domain/test_role.py`, `test_authorization.py`, `test_session_policy.py`, `test_login_policy.py`, `test_authentication_guards.py` | R1–R4, R25–R28. |
| `backend/core/tests/ports/test_password_hasher.py`, `test_tokens.py` | Port conformance, mirroring `tests/ports/test_clock.py`. |
| `backend/core/tests/application/test_authentication.py`, `test_account_admin.py` | R5–R24, R29–R31. |

**Dropped from the first pass, entirely:** `ports/sessions.py`
(`SessionRecord`/`SessionNotFound`/`SessionRepository`), `ports/tokens.py`'s
old `TokenGenerator`/`SystemTokenGenerator` shape, `tests/ports/
test_sessions.py`, `backend/tests/contract/test_session_repository_
contract.py`, `FakeSessionRepository`/`FakeTokenGenerator`. `login_policy.py`
loses `LoginAttemptState`, `is_locked_out`, `record_failure`,
`record_success`, `MAX_CONSECUTIVE_FAILURES`, `LOCKOUT_DURATION`.

### Modified

| Path | Change |
|---|---|
| `backend/core/src/planner_core/ports/accounts.py` | `AccountRecord.role` becomes `Role` (unchanged decision from the first pass). Add `credentials_valid_since: datetime` (no default — every account has one from creation; `G-87`'s revocation marker). **Drop** the first pass's `failed_login_attempts`/`locked_until` fields and `record_login_attempt` method — cut with the lockout machinery. Extend `AccountRepository.update_credentials` to take `credentials_valid_since` as a fourth parameter (§6, §9 — rides on the same `UpdateItem` a password reset already makes). Add `AccountRepository.revoke_credentials(user_id, revoked_at) -> None` (raises `AccountNotFound`) — the lightweight logout-only write (§9). |
| `backend/core/tests/support/fakes.py` | Update `FakeAccountRepository` for the `Role` type, `credentials_valid_since`, the extended `update_credentials` signature, and the new `revoke_credentials` method. Keep `FakePasswordHasher`; **drop** `FakeSessionRepository`/`FakeTokenGenerator` from the first pass's plan (never implemented — this is still `spec_ready`). |
| `backend/core/tests/ports/test_accounts.py` | Update literal `role="..."` construction to `Role.USER`/`Role.ADMIN`; add `credentials_valid_since`; add cases for the extended `update_credentials` and for `revoke_credentials`. |
| `backend/core/tests/application/test_persistence_fakes_compose.py` | Update its one `AccountRecord(role="user", ...)` literal to `Role.USER` plus a `credentials_valid_since` value. |
| `backend/tests/contract/test_account_repository_contract.py` | Same `Role`/`credentials_valid_since` update. |

Same five-file ripple as the first pass, content changed. No `pyproject.toml`
change: every new module imports only stdlib (`hashlib`, `hmac`, `secrets`,
`base64`, `datetime`, `enum`, `dataclasses`) plus sibling `planner_core`
code. `planner-core` keeps `dependencies = []`.

## 3. FR-AUTH-13's reattribution is free — no new write path (unchanged)

`docs/architecture.md` §4 invariant 9 and `docs/data_model.md` §5.4 already
settled this: `añadidoPor` pointing at a removed account resolves to the
"unknown user" placeholder **at read time**. `planner_core.domain.
candidate.resolve_author` (feature 5, done) already does exactly this.
`remove_user`'s job for R21/R22 is: delete the account record, and touch
nothing else. Under the stateless design this is now *also* the entirety
of `remove_user`'s job for R23 (`FR-AUTH-14`) — see §6: there is no
separate "invalidate sessions" call left to make, because a token whose
`user_id` no longer resolves to an account fails R27 automatically.

## 4. Roles — concrete values proposed (human-approved; base class corrected post-implementation)

```python
# backend/core/src/planner_core/domain/role.py
"""The two roles FR-AUTH-01 names."""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    USER = "user"
```

**Correction (2026-08-27, human-approved):** the first pass specified
`class Role(str, Enum)`. `ruff check` (`UP042`, this project's configured
`target-version = "py313"`) rejects that shape outright — verified
directly, not a style preference. `StrEnum` is also the technically better
choice here regardless of the lint: `str(Role.ADMIN)` gives the plain
`"admin"` that actually gets persisted (`docs/data_model.md`'s `tipo`
attribute), where `(str, Enum)`'s `str()` gives the unhelpful
`"Role.ADMIN"` — a well-known footgun `StrEnum` (3.11+) exists specifically
to fix. The two forms are identical for every comparison and `.value`
access this feature performs; nothing in the shipped code relied on the
difference. `Role`'s literal values (`"admin"`/`"user"`) are unchanged and
remain human-approved.

## 5. Authorization guards (unchanged)

```python
# backend/core/src/planner_core/domain/authorization.py
"""Role-based access guards (FR-AUTH-01, -05, -06, -18)."""

from __future__ import annotations

from planner_core import messages
from planner_core.domain.errors import PlannerError
from planner_core.domain.role import Role


class Forbidden(PlannerError):
    def __init__(self, role: Role) -> None:
        super().__init__(messages.FORBIDDEN)
        self.role = role


def require_admin(role: Role) -> None:
    if role is not Role.ADMIN:
        raise Forbidden(role)


def require_user(role: Role) -> None:
    if role is not Role.USER:
        raise Forbidden(role)
```

## 6. Token validity — flat expiry and revocation (rewritten per G-87)

No session record exists to look up. A token is self-contained
(`user_id` + `issued_at`, §8) and its validity is two independent pure
predicates plus an account lookup — no `last_activity_at`, no `touch`, no
per-request write.

```python
# backend/core/src/planner_core/domain/session_policy.py
"""Token validity: a flat 30-day expiry from issuance (FR-AUTH-16, amended
by G-87), and revocation via an account-level marker (FR-AUTH-11, -14)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Final

from planner_core import messages
from planner_core.domain.errors import PlannerError

ABSOLUTE_LIMIT: Final[timedelta] = timedelta(days=30)


def is_expired(issued_at: datetime, now: datetime) -> bool:
    """R25."""
    return now - issued_at > ABSOLUTE_LIMIT


def is_revoked(issued_at: datetime, credentials_valid_since: datetime) -> bool:
    """R26. A token issued before the account's marker was last advanced
    predates whatever event advanced it (an admin reset or a self logout,
    §9) and is no longer trusted."""
    return issued_at < credentials_valid_since


class SessionExpired(PlannerError):
    """R28 — raised uniformly whether the cause is a bad signature,
    expiry, revocation, or a removed account; the caller does not get to
    distinguish them (see application/authentication.authenticate, §8)."""

    def __init__(self) -> None:
        super().__init__(messages.SESSION_EXPIRED)
```

**Why `set_password` (R17) does not advance the marker.** The account
holder completes the set-password step using the very token they logged in
with (the temporary-password login). If `set_password` bumped
`credentials_valid_since` to "now," it would immediately invalidate the
token the caller is using to make that same request, logging them out the
instant they finish setting their password — not required by any `FR-*`
and actively hostile UX. `set_password` passes the account's existing
`credentials_valid_since` through unchanged when it calls
`update_credentials` (§9).

## 7. Login failure (R12) — brute-force protection moved to infrastructure

```python
# backend/core/src/planner_core/domain/login_policy.py
"""Login failure (FR-AUTH-02). Brute-force lockout moved to infrastructure
(feature 21, G-87) — this module carries no attempt-counting state."""

from __future__ import annotations

from planner_core import messages
from planner_core.domain.errors import PlannerError


class InvalidCredentials(PlannerError):
    """R12 — raised identically whether the username is unknown or the
    password is wrong; no argument distinguishes the cause. This is a
    leftover good practice from NFR-SEC-04's spirit, not a claim that this
    feature implements NFR-SEC-04 — it does not (requirements.md revision
    note)."""

    def __init__(self) -> None:
        super().__init__(messages.INVALID_CREDENTIALS)
```

## 8. The token — a minimal signed `(user_id, issued_at)` pair

```python
# backend/core/src/planner_core/ports/tokens.py
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
    """Raised by verify() when the signature does not match or the token
    is malformed. No message — mapped to the same SessionExpired/
    INVALID_CREDENTIALS text by whichever caller catches it, never shown
    on its own (docs/conventions.md: persistence/parsing-layer exceptions
    carry no user-facing text)."""


@runtime_checkable
class TokenSigner(Protocol):
    def issue(self, user_id: str, issued_at: datetime) -> str: ...

    def verify(self, token: str) -> AuthToken:
        """Raises InvalidToken."""
        ...


class HmacTokenSigner:
    """Default implementation: HMAC-SHA256 over the payload, stdlib-only
    (hashlib, hmac, base64) — ships beside its Protocol per architecture.md
    section 1.2.2. secret_key is an injected constructor parameter: core
    never reads an environment variable or secret store (the zero-IO rule);
    supplying the real key from a deployed secret is wiring.py's job (a
    Lambda concern, out of core), the same "configuration is explicit
    values passed in" shape as every other port (docs/architecture.md
    section 6)."""

    def __init__(self, secret_key: bytes) -> None:
        self._secret_key = secret_key

    def issue(self, user_id: str, issued_at: datetime) -> str:
        payload = f"{user_id}{_FIELD_SEP}{issued_at.isoformat()}".encode("utf-8")
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
```

`login` (application layer) calls `signer.issue(record.user_id, now)` and
returns the resulting string as the whole "session" the caller gets back —
no separate `session_id`, because there is nothing left to key a lookup by.
`authenticate` calls `signer.verify(token)`, then applies R25/R26 from §6,
then confirms the account still exists (R27's third clause) — see §0's
sketch in `application/authentication.py` below.

## 9. Data-model change — one attribute, one extended write, one new write

`docs/data_model.md` §9 records this as resolved by `G-87`: no new item
type. This feature proposes exactly:

- **One new attribute on the existing `DatosUsuario` item**: a
  timestamp, proposed name `validoDesde` (persisted, Spanish, matching
  `docs/data_model.md`'s naming convention) / `credentials_valid_since`
  (the `AccountRecord` field). Set at account creation to the creation
  instant, and advanced to "now" whenever the account's active tokens must
  all stop working (an admin password change/reset, or a self logout).
- **AP4/AP7's existing write is extended, not replaced.** A password reset
  already issues an `UpdateItem` on `DatosUsuario` for the new `passHash`;
  `validoDesde` is set in the **same** call (`update_credentials`'s new
  fourth parameter). No new access pattern for the reset case.
- **One genuinely new, but minimal, access pattern: "Cerrar sesión"
  (logout)** — `UpdateItem PK=USUARIOS SK=ID#<idUsuario>`, setting only
  `validoDesde = now`. This is the one write `G-87` did not already
  authorize by name (it discusses reset and removal, not voluntary
  logout) — flagged as gate question 1, because it exists only if the
  human accepts logout advancing the marker (§10, alternative C) rather
  than being a pure client-side no-op. It is a single-attribute update on
  an item already read on every authenticated request, not a new item
  type and not a per-request cost — the same order of magnitude `G-87`
  found acceptable for the reset case, just triggered by a different
  event.
- **Removal needs no write at all**, beyond the existing account-record
  delete (AP5). `G-87` point 2: "removal is free because deleting the
  account row already fails every lookup for its tokens" — R27's
  "account exists" clause is what makes this true; §3 above.

## 10. Rejected alternatives

The first pass's three alternatives (the `DatosSesion` PK debate, the
lockout-item-type debate, progressive lockout) are moot — none of that
persistence exists anymore. Replaced:

**A. A per-token revocation list** (a blocklist of individually-revoked
token ids) instead of a single account-wide `credentials_valid_since`
marker. Rejected: this reintroduces exactly the per-token persistence
`G-87` rejected — a blocklist is a session table by another name, and
checking "is this token in a large deny-list" costs a lookup per request,
the same cost the owner ruled out.

**B. A JWT-shaped token** (JSON claims, a header field naming the
algorithm, base64url of three segments) instead of the minimal custom
two-field HMAC token built here. Rejected: no JSON/JWT library is
available in `core` (`dependencies = []`), and JWT's extensibility —
multiple claims, multiple algorithms, a negotiable header — serves no need
this feature has, which is exactly two fixed fields. Same fixed-vocabulary
reasoning already used for units (`G-39`) and ingredient categories
(`G-63`): don't build a general mechanism for a single concrete need.

**C. Logout as a pure client-side token discard**, with no server-side
call at all — the cheapest option, since a stateless token needs nothing
server-side to stop being *sent*. Rejected as this design's default
because it leaves `FR-AUTH-09`'s "users shall be able to log out" merely
nominal: a copied or intercepted token would remain valid for up to 30
days after the user believes they logged out. Chosen instead: logout
advances the same revocation marker an admin reset uses (§9), at the cost
of also logging out every other device signed into that account — a
reasonable trade at the household scale `G-35` already established. This
is a genuine, either-way-defensible fork the human should confirm — gate
question 1.

## 11. Boundary checks

- **`docs/architecture.md` §2 (pending, human-owned):** P5 (REST contract)
  and P6 (deployment topology, including where `HmacTokenSigner`'s secret
  key is sourced from) are not decided here — §0 states every use case is
  transport-agnostic. `R23`, `R27`, `R28` cover only the "authenticated
  sessions"/"logout" clauses of `FR-AUTH-09`; its HTTPS-only clause is
  P6's.
- **§2.1 decide-in-a-spec items:** none of the named ones. This feature's
  own analogous concrete values — `Role`'s literals (§4, human-approved),
  the 30-day flat expiry (§6, fixed by `FR-AUTH-16`'s frozen text, not a
  free choice), the token's field-separator/encoding and the
  `validoDesde` attribute name (§8–§9) — are flagged as gate questions
  below.
- **Frozen docs:** none modified. `docs/data_model.md`'s addition (§9) is
  a proposal, for the leader to merge post-approval — the human has
  already updated `docs/data_model.md` §9's *header* to record `G-87`'s
  decision; the concrete attribute name is still this feature's proposal
  per that same section's text.
- **Runtime dependencies:** none added. `core` stays `dependencies = []`.
- **Requirements invented:** none. Every `R<n>` cites a real `FR-*` id
  (`requirements.md`'s coverage map). `NFR-SEC-04` is cited by none —
  deliberately, per the revision note.
- **User-facing strings:** the same five `messages.py` entries as the
  first pass — `FORBIDDEN`, `INVALID_CREDENTIALS`, `SESSION_EXPIRED`,
  `SET_PASSWORD_REQUIRED`, `SET_PASSWORD_NOT_ALLOWED` — no new ones and
  none removed; the redesign changed *what raises them*, not the message
  set.

## 12. Gate questions for the human

Superseded from the first pass: questions 1–3 there (the `DatosSesion`
shape, the lockout-item-type amendment, the lockout numeric values) are
moot — resolved by `G-87` itself, not re-asked here.

1. **Logout advances the account-wide revocation marker (§9, §10
   alternative C)**, logging the account out of every device, rather than
   being a pure client-side no-op. This is a real behavioral fork `G-87`
   does not itself resolve (it discusses reset/removal, not voluntary
   logout). Recommendation: accept — it is the only way to give
   `FR-AUTH-09`'s logout clause real, testable, server-enforced effect
   without reintroducing per-token tracking, and the "every device" cost
   is reasonable at household scale (`G-35`).
2. **A minimal custom HMAC-SHA256 token, built and verified inside
   `core`** (§8), rather than deferring token construction/signing
   entirely to whatever P5/P6 eventually wires up (e.g. an API Gateway
   JWT authorizer). Recommendation: accept — it needs no P5/P6 decision to
   exist, keeps `core` fully testable today, and a future P5-owned
   authorizer can call the same `TokenSigner.verify` regardless of which
   transport wraps it.
3. **The `credentials_valid_since`/`validoDesde` attribute name and shape**
   (§9) — a plain timestamp on `DatosUsuario`, set at creation and
   advanced on admin reset/change and on logout. Recommendation: accept —
   matches `G-87`'s explicit shape and the existing `DatosUsuario` naming
   style.
4. **The `AccountRepository`/`AccountRecord` ripple** (§2): `role: str →
   Role` (unchanged from the first pass, already approved), the new
   `credentials_valid_since` field, the extended `update_credentials`
   signature, and the new `revoke_credentials` method. Recommendation:
   accept — the `Role` half was already approved; the rest is `G-87`'s
   direct, minimal consequence.
