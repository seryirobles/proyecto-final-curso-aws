# auth_flow — Tasks

> Revision (2026-08-27), amended in place per `G-87` — the first pass's
> session-port/lockout tasks are replaced, not appended. Execute in order.
> Tick `[x]` as each completes.
> Read `design.md` §2 before touching `ports/accounts.py` or
> `tests/support/fakes.py` — both are feature 14's shipped code; the ripple
> is named in full there, not open-ended.

## Messages module (`backend/core/src/planner_core/messages.py`, modified)

- [x] T1 — Add `FORBIDDEN`, `INVALID_CREDENTIALS`, `SESSION_EXPIRED`,
  `SET_PASSWORD_REQUIRED`, `SET_PASSWORD_NOT_ALLOWED` as es-ES string
  constants (`design.md` §11). Covers: R2, R3, R12, R14, R15, R28, R30, R31.

## Domain — role and authorization

- [x] T2 — Create `domain/role.py`: `Role(StrEnum)` with `ADMIN = "admin"`,
  `USER = "user"` (`design.md` §4 — corrected 2026-08-27 from `(str, Enum)`,
  `ruff` `UP042`, human-approved). Covers: R1.
- [x] T3 — Create `domain/authorization.py`: `Forbidden(PlannerError)`
  carrying `role`, initialized with `messages.FORBIDDEN`; `require_admin`;
  `require_user` (`design.md` §5). Covers: R2, R3, R4.

## Domain — token validity (`domain/session_policy.py`, new)

- [x] T4 — Add `ABSOLUTE_LIMIT = 30 days`, `is_expired(issued_at, now)`,
  `is_revoked(issued_at, credentials_valid_since)`,
  `SessionExpired(PlannerError)` initialized with `messages.SESSION_EXPIRED`
  (`design.md` §6). Covers: R25, R26, R28.

## Domain — login failure (`domain/login_policy.py`, new)

- [x] T5 — Add `InvalidCredentials(PlannerError)` initialized with
  `messages.INVALID_CREDENTIALS`. No attempt-counting state — that is
  feature 21's job, not this module's (`design.md` §7). Covers: R12.

## Domain — authentication guards (`domain/authentication_guards.py`, new)

- [x] T6 — Add `PasswordResetPending(PlannerError)` (message
  `SET_PASSWORD_REQUIRED`) and `SetPasswordNotPending(PlannerError)`
  (message `SET_PASSWORD_NOT_ALLOWED`) (`design.md` §1). Covers: R14, R15.

## Ports — password hashing (`ports/password_hasher.py`, new, unchanged from first pass)

- [x] T7 — Add `PasswordHasher` Protocol and `Pbkdf2PasswordHasher` default
  implementation: `hash`/`verify` over `hashlib.pbkdf2_hmac("sha256", ...)`,
  600,000 iterations, 16-byte salt, `hmac.compare_digest` for the comparison.
  Covers: R16 (integration point).

## Ports — tokens (`ports/tokens.py`, rewritten)

- [x] T8 — Add `AuthToken`, `InvalidToken(PlannerError)`, `TokenSigner`
  Protocol (`issue`, `verify`), and `HmacTokenSigner` default
  implementation: HMAC-SHA256 over `f"{user_id}|{issued_at.isoformat()}"`,
  base64url-encoded payload and signature joined by `.` (`design.md` §8).
  Covers: R5, R27.

## Ports — accounts (`ports/accounts.py`, modified)

- [x] T9 — Change `AccountRecord.role` from `str` to `Role`; add
  `credentials_valid_since: datetime` (no default) (`design.md` §2, §9).
  Covers: R18, R19, R23, R26.
- [x] T10 — Extend `AccountRepository.update_credentials` to take
  `credentials_valid_since` as a fourth parameter (`design.md` §6, §9).
  Covers: R19.
- [x] T11 — Add `AccountRepository.revoke_credentials(user_id, revoked_at)
  -> None`, raising `AccountNotFound` (`design.md` §9). Covers: R24.

## Application — authentication (`application/authentication.py`, new)

- [x] T12 — Add `login(username, password, *, accounts, hasher, signer,
  clock) -> LoginResult`: look up by username, verify password — raise
  `InvalidCredentials` (not `signer.issue`) for either an unknown username
  or a wrong password, identically; on success, `signer.issue(user_id, now)`
  and return `LoginResult(user_id, token, role, password_reset_required)`
  (`design.md` §7, §8). Covers: R5, R12.
- [x] T13 — Add `authenticate(token, *, accounts, signer, clock) ->
  AccountRecord`: `signer.verify` (catch `InvalidToken` → `SessionExpired`);
  `is_expired` → `SessionExpired`; `accounts.get_by_id` → `SessionExpired`
  if absent; `is_revoked` against the account's `credentials_valid_since`
  → `SessionExpired`; else return the account (`design.md` §6, §8).
  Covers: R23, R25, R26, R27, R28.
- [x] T14 — Add `logout(user_id, *, accounts, clock) -> None`: calls
  `accounts.revoke_credentials(user_id, clock.now())` (`design.md` §9,
  §10 alternative C). Covers: R24.
- [x] T15 — Add `set_password(user_id, new_password, *, accounts, hasher) ->
  None`: raise `SetPasswordNotPending` if the account's
  `password_reset_required` is already false; else `validate_password`
  (reused from feature 9), `hasher.hash`, then
  `accounts.update_credentials(user_id, hash, False, <the account's
  existing credentials_valid_since, unchanged>)` — deliberately does not
  advance the marker (`design.md` §6, "why set_password does not"). Covers:
  R14, R16, R17.
- [x] T16 — Add `require_password_set(account) -> None`: raises
  `PasswordResetPending` if `account.password_reset_required` is true
  (`design.md` §1). Covers: R15.

## Application — account admin (`application/account_admin.py`, new)

- [x] T17 — Add `create_user(actor_role, username, *, accounts, clock) ->
  AccountRecord`: `require_admin`; `validate_username` against
  `accounts.list_all()` usernames; construct an `AccountRecord` with
  `role=Role.USER` (never accepts a role parameter — R9 by construction),
  `password_reset_required=True`, `credentials_valid_since=clock.now()`;
  `accounts.create(...)` (`design.md` §5, §9). Covers: R6, R7, R8, R9, R11.
- [x] T18 — Add `rename_user(actor_role, user_id, new_username, *,
  accounts) -> None`: `require_admin`; `accounts.rename(...)` (reuses
  feature 14's uniqueness handling). Covers: R7, R8.
- [x] T19 — Add `admin_set_password(actor_role, actor_user_id, target,
  new_temp_password_hash, *, accounts, clock) -> None`: `require_admin`;
  raise `Forbidden` if `target.user_id == actor_user_id` (R30); else
  `accounts.update_credentials(target.user_id, new_temp_password_hash,
  True, clock.now())` — one call setting the temporary-password flag and
  advancing the revocation marker together (`design.md` §9, G-51). Covers:
  R18, R19, R29, R30.
- [x] T20 — Add `remove_user(actor_role, target, *, accounts) -> None`:
  `require_admin`; raise `Forbidden` if `target.role is Role.ADMIN` (R31);
  else `accounts.delete(target.user_id)` — no other call (`design.md` §3;
  no session-invalidation call exists to make under the stateless design).
  Covers: R21, R22, R23, R31.
- [x] T21 — Add `list_accounts(actor_role, *, accounts) ->
  tuple[AccountRecord, ...]`: `require_admin`; `accounts.list_all()`.
  Covers: R20.

## Test fakes (`backend/core/tests/support/fakes.py`, modified)

- [x] T22 — Update `FakeAccountRepository` for the `Role` type,
  `credentials_valid_since`, the extended `update_credentials` signature,
  and the new `revoke_credentials` method (`rename`'s internal
  `AccountRecord(...)` reconstruction passes `credentials_valid_since`
  through unchanged). Covers: R18, R19, R23, R24, R26.
- [x] T23 — Add `FakePasswordHasher`: a deterministic, fast stand-in (e.g.
  `hash(p) = "fake:" + p`, `verify` compares equality after the prefix) —
  never the real PBKDF2 loop. Covers: R16 (via application tests).

## Existing-file ripple from the `AccountRecord` shape change

- [x] T24 — `backend/core/tests/ports/test_accounts.py`: update literal
  `role="..."` construction to `Role.USER`/`Role.ADMIN`, add
  `credentials_valid_since`; add cases for the extended `update_credentials`
  and for `revoke_credentials`. Covers: R18, R19, R23, R24, R26.
- [x] T25 — `backend/core/tests/application/test_persistence_fakes_compose.py`:
  update its one `AccountRecord(role="user", ...)` literal to `Role.USER`
  plus a `credentials_valid_since` value. Covers: — (ripple only).
- [x] T26 — `backend/tests/contract/test_account_repository_contract.py`:
  same `Role`/`credentials_valid_since` update. Covers: — (ripple only).

## Tests — domain

- [x] T27 — `test_role.py`: `test_exactly_two_roles_exist` (`len(Role) ==
  2`, membership check). Covers: R1.
- [x] T28 — `test_authorization.py`: `require_admin` raises `Forbidden` for
  `Role.USER`, passes for `Role.ADMIN`; `require_user` the mirror. Covers:
  R2, R3, R4.
- [x] T29 — `test_session_policy.py`: `is_expired` false at exactly 30 days
  minus a second, true just past 30 days; `is_revoked` false when
  `issued_at == credentials_valid_since`, true when `issued_at` is one
  second earlier. Covers: R25, R26.
- [x] T30 — `test_login_policy.py`: `str(InvalidCredentials()) ==
  messages.INVALID_CREDENTIALS`. Covers: R12.
- [x] T31 — `test_authentication_guards.py`: both exceptions carry their
  respective messages. Covers: R14, R15.

## Tests — ports

- [x] T32 — `test_password_hasher.py`: `hash` then `verify` round-trips
  true; `verify` with a wrong password is false; two `hash` calls on the
  same password produce different output (salted). Covers: R16.
- [x] T33 — `test_tokens.py`: `issue` then `verify` round-trips the same
  `user_id`/`issued_at`; a tampered payload or signature raises
  `InvalidToken`; a malformed (non-two-part) token raises `InvalidToken`;
  a token signed with a different key fails verification. Covers: R27.

## Tests — application (`test_authentication.py`)

- [x] T34 — `test_login_with_unknown_username_raises_invalid_credentials`.
  Covers: R12.
- [x] T35 — `test_login_with_wrong_password_raises_invalid_credentials`.
  Covers: R12.
- [x] T36 — `test_successful_login_returns_a_token_carrying_role_and_pending_flag`.
  Covers: R5, R11.
- [x] T37 — `test_authenticate_with_tampered_token_raises_session_expired`.
  Covers: R27, R28.
- [x] T38 — `test_authenticate_with_a_31_day_old_token_raises_session_expired`.
  Covers: R25, R28.
- [x] T39 — `test_authenticate_with_token_issued_before_the_revocation_marker_raises_session_expired`.
  Covers: R26, R28.
- [x] T40 — `test_authenticate_denies_a_removed_accounts_token` — issue a
  token, delete the account, assert `authenticate` raises `SessionExpired`.
  Covers: R23, R27.
- [x] T41 — `test_authenticate_succeeds_for_a_valid_recent_token`. Covers: R27.
- [x] T42 — `test_logout_advances_the_revocation_marker` — assert a token
  issued before `logout()` fails `authenticate` afterward. Covers: R24.
- [x] T43 — `test_set_password_rejects_when_not_pending`. Covers: R14.
- [x] T44 — `test_set_password_rejects_a_too_short_password` (via the
  reused `password_policy.validate_password`). Covers: R16.
- [x] T45 — `test_set_password_clears_the_pending_flag_without_advancing_the_marker`
  — assert `password_reset_required` becomes false and
  `credentials_valid_since` is unchanged, and a token issued just before
  the call still authenticates just after. Covers: R17.
- [x] T46 — `test_require_password_set_raises_pending_when_flag_true`.
  Covers: R15.

## Tests — application (`test_account_admin.py`)

- [x] T47 — `test_create_user_by_non_admin_raises_forbidden`. Covers: R7.
- [x] T48 — `test_create_user_never_accepts_an_admin_role` — inspect
  `create_user`'s signature to confirm no `role` parameter exists. Covers: R9.
- [x] T49 — `test_create_user_rejects_a_taken_username` (via the reused
  `username_policy.validate_username`). Covers: R8.
- [x] T50 — `test_create_user_sets_password_reset_required_true`. Covers: R11.
- [x] T51 — `test_admin_set_password_sets_pending_flag_and_advances_the_marker`.
  Covers: R18, R19.
- [x] T52 — `test_admin_set_password_on_another_admin_is_permitted`. Covers: R29.
- [x] T53 — `test_admin_set_password_on_self_raises_forbidden`. Covers: R30.
- [x] T54 — `test_remove_user_deletes_the_account_and_calls_no_content_repository`
  — a fake account repository and a fake content repository (e.g.
  `FakeRecipeRepository`) both present; assert the content repository
  received zero calls. Covers: R21, R22.
- [x] T55 — `test_remove_user_on_an_admin_account_raises_forbidden`. Covers: R31.
- [x] T56 — `test_list_accounts_by_non_admin_raises_forbidden`. Covers: R20.
- [x] T57 — `test_list_accounts_returns_username_role_and_pending_status`.
  Covers: R20.

## Close-out

- [x] T58 — Record the `R<n> → test` map in `progress/impl_auth_flow.md`
  (`docs/verification.md` Level 3).
- [x] T59 — Confirm `backend/core/pyproject.toml` still reads
  `dependencies = []`; `uv export --package planner-api --no-dev` and
  `uv export --package planner-ai --no-dev` both resolve with nothing added.
- [x] T60 — Run `./init.sh` green: `ruff format`, `ruff check`, `mypy
  --strict`, `pytest` (including `test_no_ambient_time.py`, unmodified but
  re-run), plus the frontend gate.
