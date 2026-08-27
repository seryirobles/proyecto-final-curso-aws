# auth_flow — Requirements

> Feature 15 · tier 3 · `sdd: true`
> Covers: `FR-AUTH-01` … `FR-AUTH-14`, `FR-AUTH-16`, `FR-AUTH-18`
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen
> requirement ids it implements, carries exactly one `SHALL`/`SHALL NOT`
> (mechanically counted, not eyeballed), and is verifiable by at least one
> concrete test.

## Revision note (2026-08-27) — `G-87`: session tracking and app-level lockout dropped

This is a revision of a rejected first pass, amended in place per the
human's design-gate decision. `docs/gaps_and_resolutions.md` Part W /
`G-87` records the full reasoning; summary:

1. **No session persistence.** Authentication is stateless: a token carries
   `user_id` + `issued_at`; validity is computed, never looked up. The old
   `SessionRepository` port, `DatosSesion` item type, and every
   sliding-window/`last_activity_at` requirement are gone.
2. **`FR-AUTH-11`/`-14`'s "invalidate all sessions"** is now a
   **revocation-marker** check: one timestamp attribute on the existing
   `AccountRecord`/`DatosUsuario`, compared against the token's `issued_at`
   on every authenticated request. No per-session write, no new item type.
3. **`FR-AUTH-16` is amended** (frozen text, `docs/requirements.md`): the
   12-hour inactivity clause is struck, leaving a flat 30-day expiry
   computed from `issued_at` alone.
4. **`NFR-SEC-04` (brute-force lockout) moves to feature 21** (Terraform —
   API Gateway/WAF), out of this feature's `covers` entirely. It is **not**
   cited by any `R<n>` below. `InvalidCredentials` still exists for a
   wrong-password/unknown-username login failure — just not the
   attempt-counting state machine that used to sit around it.

## Scope note — one acceptance-cited id absent from `covers`

`feature_list.json`'s `covers` array does not list `FR-AUTH-15` (password
policy), but its acceptance criteria cite it as **reuse**, not
reimplementation — feature 9 `password_policy` (done) already owns it in
full. `R16` below cites it only for the one thing this feature does with
it: call `planner_core.domain.password_policy.validate_password` at the
set-password integration point, the identical precedent
`specs/password_policy/requirements.md` § *Scope note* set for `FR-UX-03`.
(`FR-AUTH-17`, similarly cited in the first pass, is likewise reused via
`username_policy.validate_username` — see `R8`.)

## Scope note — `FR-AUTH-09`'s HTTPS-only clause is infrastructure, not covered here

`FR-AUTH-09` bundles three clauses: HTTPS-only access, authenticated
sessions, and logout. TLS termination is deployment topology
(`docs/architecture.md` §2 P6, human-owned) — no Python domain or
application code can "enforce HTTPS" from inside a Lambda. `R23`, `R27`,
`R28` cover the "authenticated sessions" and "logout" clauses only.

## Depends on

Feature 9 `password_policy` (done) — `password_policy.py` and
`username_policy.py`, reused as-is. Feature 14 `persistence_ports` (done) —
`AccountRepository`/`AccountRecord`, extended here exactly where its own
`design.md` §7 flagged (the `Role` type), plus the `G-87` revocation-marker
attribute — see `design.md` §2.

---

## R1
Implements: FR-AUTH-01

The system SHALL support exactly two roles: Admin and User.

## R2
Implements: FR-AUTH-01, FR-AUTH-06

IF a User-role actor requests an Admin-only operation, THEN the system SHALL
deny it.

## R3
Implements: FR-AUTH-01, FR-AUTH-05

IF an Admin-role actor requests a meal-planning operation, THEN the system
SHALL deny it.

## R4
Implements: FR-AUTH-06

WHEN a User-role actor requests a meal-planning operation, the system SHALL
authorize it.

## R5
Implements: FR-AUTH-02

The system SHALL authenticate using a username and a password, and no other
credential.

## R6
Implements: FR-AUTH-03

The system SHALL NOT expose a self-registration operation for creating an
account.

## R7
Implements: FR-AUTH-03, FR-AUTH-05

WHEN an account is created, the system SHALL require the creating actor to
hold the Admin role.

## R8
Implements: FR-AUTH-05, FR-AUTH-17

WHEN an account is created, the system SHALL reject the username using the
existing `username_policy.validate_username` function against the active
account usernames.

## R9
Implements: FR-AUTH-07, FR-AUTH-18

The system SHALL NOT expose an application operation that creates an
Admin-role account.

## R10
Implements: FR-AUTH-07

WHERE more than one Admin-role account exists, the system SHALL authorize
each of them identically for Admin operations.

## R11
Implements: FR-AUTH-08, FR-AUTH-10, FR-AUTH-11

WHEN an account's pending-set-password flag is true, the system SHALL apply
identical set-password-forcing behavior regardless of whether the flag was
set by account creation, an admin password change or reset, or an IaC
bootstrap re-seed.

## R12
Implements: FR-AUTH-02

IF a presented username and password do not match a stored account's
credentials, THEN the system SHALL deny authentication.

## R13
Implements: FR-AUTH-04

The system SHALL NOT provide an operation for an authenticated account to
change its own password, other than the mandatory set-password step.

## R14
Implements: FR-AUTH-04

IF an account's pending-set-password flag is false, THEN the system SHALL
deny the set-password operation.

## R15
Implements: FR-AUTH-10

WHEN an account's pending-set-password flag is true, the system SHALL deny
every operation other than the set-password operation.

## R16
Implements: FR-AUTH-10, FR-AUTH-15

WHEN the set-password operation is invoked, the system SHALL validate the
new password using the existing `password_policy.validate_password`
function before accepting it.

## R17
Implements: FR-AUTH-10

WHEN the set-password operation succeeds, the system SHALL clear the
account's pending-set-password flag.

## R18
Implements: FR-AUTH-11

WHEN an Admin changes or resets a user's password, the system SHALL set
that account's pending-set-password flag to true.

## R19
Implements: FR-AUTH-11

WHEN an Admin changes or resets a user's password, the system SHALL advance
that account's revocation marker to the current time.

## R20
Implements: FR-AUTH-12

WHEN an Admin requests the account list, the system SHALL return every
account's username, role, and pending-set-password status.

## R21
Implements: FR-AUTH-13

WHEN an Admin removes a User-role account, the system SHALL delete that
account's repository record.

## R22
Implements: FR-AUTH-13

WHEN an Admin removes a User-role account, the system SHALL NOT delete any
content that account authored.

## R23
Implements: FR-AUTH-14

WHEN an Admin removes a user account, the system SHALL deny authentication
for every token previously issued to that account.

## R24
Implements: FR-AUTH-09

WHEN a user logs out, the system SHALL advance that account's revocation
marker to the current time.

## R25
Implements: FR-AUTH-16

The system SHALL treat a token as expired when more than 30 days have
elapsed since it was issued.

## R26
Implements: FR-AUTH-11

The system SHALL treat a token as revoked when its issued-at instant is
earlier than its account's revocation-marker instant.

## R27
Implements: FR-AUTH-09

WHEN authenticating a token, the system SHALL grant access only if the
token's signature verifies, its account exists, it is not expired (R25),
and it is not revoked (R26).

## R28
Implements: FR-AUTH-09, FR-AUTH-16

IF a token fails the authentication check in R27, THEN the system SHALL
deny the request, requiring re-authentication.

## R29
Implements: FR-AUTH-18

WHEN an Admin resets another Admin's password, the system SHALL permit it
through the same operation used for a User account.

## R30
Implements: FR-AUTH-04, FR-AUTH-18

IF an Admin targets their own account for a password change or reset, THEN
the system SHALL deny the operation.

## R31
Implements: FR-AUTH-18

The system SHALL NOT expose an operation to remove an Admin-role account.

---

## Coverage map

| Frozen requirement | Covered by |
|---|---|
| `FR-AUTH-01` | R1, R2, R3 |
| `FR-AUTH-02` | R5, R12 |
| `FR-AUTH-03` | R6, R7 |
| `FR-AUTH-04` | R13, R14, R30 |
| `FR-AUTH-05` | R3, R7, R8 |
| `FR-AUTH-06` | R2, R4 |
| `FR-AUTH-07` | R9, R10 |
| `FR-AUTH-08` | R11 |
| `FR-AUTH-09` (HTTPS clause excluded, see scope note) | R23, R27, R28 |
| `FR-AUTH-10` | R11, R15, R16, R17 |
| `FR-AUTH-11` (see G-51, G-87) | R18, R19, R26 |
| `FR-AUTH-12` | R20 |
| `FR-AUTH-13` | R21, R22 |
| `FR-AUTH-14` (see G-87) | R23 |
| `FR-AUTH-16` (amended, see G-87) | R25, R28 |
| `FR-AUTH-18` | R9, R29, R30, R31 |
| `FR-AUTH-15` (cited, see scope note) | R16 |
| `FR-AUTH-17` (cited, see scope note) | R8 |

| `feature_list.json` acceptance criterion | Covered by |
|---|---|
| Exactly two roles, strict view separation | R1, R2, R3, R4 |
| Username + password only, no self-registration, admin-only creation | R5, R6, R7, R12 |
| Neither role changes its own password except at set-password | R13, R14, R30 |
| Exactly one bootstrap admin via IaC; multiple supported; never created/removed via app | R9, R10, R31 |
| Admin recovery by IaC re-seed, same forced set-password step | R11 |
| Authenticated sessions and logout, stateless — no session table | R23, R24, R27, R28 |
| First login / admin-issued password is temporary, forces set-password | R11, R15, R16, R17, R18 |
| Admin reset or user removal invalidates all sessions via the revocation marker, no session table | R19, R23, R26 |
| Revocation marker rides on the same write a password reset already makes; removal needs no separate invalidation write | R19 (rides on `update_credentials`), R21+R27 (removal alone denies every token via account non-existence) — see `design.md` §3, §6 |
| Admin view lists accounts (username, role, pending status) | R20 |
| Removal retains and reattributes authored content to "unknown user" | R21, R22 (reattribution is free at read time — `planner_core.domain.candidate.resolve_author`, feature 5, done — see `design.md` §3) |
| Password policy reused, not reimplemented | R16 |
| Flat 30-day expiry from issuance, no database access, no inactivity clause | R25, R28 |
| Username uniqueness reused; placeholder reserved | R8 |
| `NFR-SEC-04` NOT implemented here — moved to feature 21 | Structural — no `R<n>` cites it; `R12`'s `InvalidCredentials` exists for `FR-AUTH-02` alone |
| No external identity provider; app-owned via `AccountRepository` | Structural — every R above is implemented through `AccountRepository`/`TokenSigner`, never a managed IdP or a session table |
