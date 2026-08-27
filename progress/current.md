# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

- **Feature in progress:** 15 — `auth_flow`
- **Started:** 2026-08-27
- **Agent:** spec_author (launching)

## Plan

Human decided **P2 (auth mechanism) = application-managed**, no external
IdP — 2026-08-27. Recorded in `docs/architecture.md` §1.2.3 (closes P2) and
the §2 table. `feature_list.json` feature 15 unblocked: `blocked` →
`pending`, `blocked_reason` removed, 15 acceptance criteria written from
`FR-AUTH-01`–`-18` and `NFR-SEC-04`. `./init.sh` confirms feature 15 as
next actionable (385 tests still green).

Covers the whole `FR-AUTH-*` family + `NFR-SEC-04`. Depends on 9
(`password_policy`, done — reuse `password_policy.py`/`username_policy.py`
as-is, do not re-implement) and 14 (`persistence_ports`, done — auth state
persists through `AccountRepository`).

Per SDD flow: spec_author writes
`specs/auth_flow/{requirements,design,tasks}.md`, sets status to
`spec_ready`, then STOP for human approval gate.

- spec_author: `spec_ready -> specs/auth_flow/`. 34 EARS requirements
  (R1-R34, one SHALL/SHALL NOT each), new domain modules (`role.py`,
  `authorization.py`, `session_policy.py`, `login_policy.py`), three new
  ports (`sessions.py`, `password_hasher.py`, `tokens.py`, each with a
  stdlib-only default per the §1.2.2 pattern), two application modules
  (`authentication.py`, `account_admin.py`), and a named 5-file ripple onto
  feature 14's `AccountRepository`/`AccountRecord` (`role: str -> Role`,
  lockout fields, `record_login_attempt`). 59 tasks (T1-T59). FR-AUTH-13's
  reattribution needs no new code — `candidate.resolve_author` (feature 5)
  already resolves a deleted account to "unknown user" at read time.
  Sessions modeled as an opaque `(user_id, session_id)` pair, deliberately
  leaving cookie-vs-bearer transport to P5. 3 rejected alternatives (§10).
  Proposes closing `docs/data_model.md` §9's parked Sessions row with a new
  `DatosSesion` item type (PK on `idUsuario` for the invalidate-all query)
  plus two attributes on `DatosUsuario` — not applied yet, leader merges
  post-approval. `feature_list.json` diff verified: only feature 15's
  status (`pending` -> `spec_ready`).

## Gate questions for the human (specs/auth_flow/design.md §12)

1. **`DatosSesion` item type + 5 access patterns** — PK on `idUsuario`
   (required for the invalidate-all-sessions query without a secondary
   index), `ttl` reused as storage hygiene only (`is_expired` does the real
   12h-inactivity enforcement, not TTL). spec_author recommends accepting.
2. **`intentosFallidos`/`bloqueadoHasta` as two new attributes on the
   existing `DatosUsuario`** (piggybacked on AP6's existing read) rather
   than an 11th item type. spec_author recommends accepting.
3. **Concrete values**: 5 consecutive failures / 15-minute flat lockout,
   `Role` literals `"admin"`/`"user"`, PBKDF2-HMAC-SHA256 at 600,000
   iterations. spec_author recommends accepting.
4. **`AccountRecord.role: str -> Role`** plus two new fields and
   `record_login_attempt` on `AccountRepository` (feature 14, done) — named
   ripple, already anticipated by feature 14's own design.md §7. spec_author
   recommends accepting.

- Human: rejected gate questions 1, 2, 3 (partial — enum piece of 4
  accepted). Leader verified against docs before agreeing (data_model.md §9
  parks Sessions pending P2, not stripped; three live gaps G-10/G-29/G-31
  establish session behavior; FR-AUTH-09/-11/-14/-16 un-struck) and asked
  for clarification. Human confirmed: **strip session tracking from the
  MVP entirely** (no `DatosSesion`, no per-session persistence). Three
  follow-up questions resolved: (1) `NFR-SEC-04` brute-force lockout moves
  to **infrastructure** (API Gateway/WAF rate limiting, feature 21) rather
  than app-level DB writes; (2) `FR-AUTH-11`/`-14` invalidation satisfied
  by a **lightweight revocation marker** (one attribute on `DatosUsuario`,
  piggybacked on the reset write, free on removal) instead of session
  records; (3) `FR-AUTH-16` simplified to a **flat 30-day expiry** only,
  inactivity clause dropped (a sliding window needs a write per request).
- Leader: lifted the freeze — new **Part W / G-87** in
  `docs/gaps_and_resolutions.md`, amended `FR-AUTH-16` in
  `docs/requirements.md` (struck the inactivity clause; `FR-AUTH-09/-11/-14`
  reviewed, left unchanged — mechanism-agnostic text still holds).
  Backfilled `docs/coverage_analysis.md` (gap-index row, closing counter,
  US2 note). Resolved `docs/data_model.md` §9's stale "blocked on P2"
  Sessions row to reflect G-87. `feature_list.json`: feature 15 loses
  `NFR-SEC-04` from `covers`, acceptance criteria rewritten for the
  stateless/revocation-marker/flat-expiry shape; feature 21 gains
  `NFR-SEC-04` in `covers`. `./init.sh` green (385 tests, 104/104 FR/NFR
  coverage intact). Sending the correction back to spec_author (same
  agent, resumed with full context) to revise `specs/auth_flow/` — drop
  `DatosSesion`/`SessionRepository`/`session_policy.py`'s tracking half and
  the lockout port/fields, add the revocation-marker + flat-expiry design.
- spec_author (revision): `spec_ready -> specs/auth_flow/` (amended in
  place). Dropped entirely: `SessionRepository`/`SessionRecord` port,
  `DatosSesion`, `SessionState.last_activity_at`, the lockout state machine
  and its two `AccountRecord` fields. `TokenGenerator` (opaque random id)
  replaced by `TokenSigner`/`HmacTokenSigner`, issuing a self-contained
  HMAC-signed `(user_id, issued_at)` token — no lookup table. New
  mechanism: `credentials_valid_since`/`validoDesde` on `AccountRecord`/
  `DatosUsuario`, advanced by admin reset (rides the existing
  `update_credentials` write) and by a new minimal `revoke_credentials`
  write for logout; removal needs no write at all. `FR-AUTH-16` rewritten
  to flat 30-day expiry. R1-R34 -> R1-R31, `NFR-SEC-04` cited by none.
  Leader verified: `feature_list.json` diff unchanged by this round (still
  just the leader's own prior edit), no `backend/`/`frontend/` files
  touched, `./init.sh` green (385 tests).

## Gate questions for the human (specs/auth_flow/design.md §12, revised — supersedes the first-pass §12)

1. **Logout advances the account-wide revocation marker**, logging the
   account out of every device rather than being a client-side no-op —
   the one behavioral fork `G-87` doesn't itself resolve. spec_author
   recommends accepting: it's the only way to give `FR-AUTH-09`'s logout
   clause real server-enforced effect without reintroducing per-token
   tracking; "every device" is reasonable at household scale (`G-35`).
2. **A minimal custom HMAC-SHA256 token, signed inside `core`** rather
   than deferring token construction to P5/P6. spec_author recommends
   accepting — needs no P5/P6 decision to exist yet, keeps `core` testable
   today.
3. **`credentials_valid_since`/`validoDesde` attribute name and shape** —
   a plain timestamp on `DatosUsuario`, set at creation, advanced on
   admin reset/change and on logout. spec_author recommends accepting.
4. **`AccountRepository`/`AccountRecord` ripple**: `role: str -> Role`
   (already approved), new `credentials_valid_since` field, extended
   `update_credentials` signature, new `revoke_credentials` method.
   spec_author recommends accepting.

- Human: asked for an explanation of gate question 1 (logout logs out
  every device — the only lever that exists given no per-token state).
  Explained the mechanism and the rejected client-side-only alternative.
  Human accepted all 4 gate questions.
- Leader: merged the approved data-model proposal into
  `docs/data_model.md` — `validoDesde` added to `DatosUsuario` (§1),
  attribute note added (§1.1), AP4 extended (sets `validoDesde` on
  create/admin-reset) and AP7 explicitly annotated as NOT touching it
  (§6's set_password reasoning), new **AP28** "Cerrar sesión" added (§4.1),
  §9's Sessions row finalized as resolved. Swept the access-pattern count
  (27 -> 28) across `data_model.md` (3 places), `docs/architecture.md`
  §1.2.1, and `AGENTS.md`'s repository map. `feature_list.json` feature 15
  flipped `spec_ready -> in_progress`. `./init.sh` green (385 tests).
  Launching implementer.

## Implementer session

- **Feature in progress:** 15 — `auth_flow`
- **Plan:** tasks T1..T60 from `specs/auth_flow/tasks.md`.
- implementer: all 60 tasks complete, ticked in `specs/auth_flow/tasks.md`.
  New modules: `domain/role.py`, `domain/authorization.py`,
  `domain/session_policy.py`, `domain/login_policy.py`,
  `domain/authentication_guards.py`, `ports/password_hasher.py`,
  `ports/tokens.py` (rewritten), `application/authentication.py`,
  `application/account_admin.py`. `ports/accounts.py` extended
  (`role: str -> Role`, `credentials_valid_since`, extended
  `update_credentials`, new `revoke_credentials`) with the named 5-file
  ripple. `Role(str, Enum)` implemented as `Role(StrEnum)` — ruff UP042,
  behaviourally identical, noted in the impl report. `./init.sh` green
  (435 tests, up from 385). `uv export` closures unaffected; `core` still
  `dependencies = []`. Report: `progress/impl_auth_flow.md`. Stopped for
  reviewer — not marking `done`, not committing.
- reviewer: CHANGES_REQUESTED, 6 findings, 1 mutant survived
  (`session_policy.py`'s `is_expired` boundary, `>` weakened to `>=`,
  R25/`FR-AUTH-16` — token issued exactly 30 days ago must still be valid,
  untested exact-equality case). Other findings: R22's test is vacuous
  (empty fake, true by construction); R6/R10/R13 claimed "structural"
  with no test backing it; two new frozen dataclasses (`AuthToken`,
  `LoginResult`) missing the mandatory frozen-instance test; three
  docstrings over the 3-line ceiling, reproducing design.md prose instead
  of pointing at it. Mutation testing otherwise clean — both
  `admin_set_password`/`set_password` revocation-marker call sites pinned
  correctly, `hmac.compare_digest` confirmed (not `==`), 7 other named
  mutants killed. Finding 5 (whether `PasswordHasher` needs a contract
  suite) flagged explicitly as the leader's call, not the implementer's.
- Leader: decided finding 5 — no contract suite. `PasswordHasher`/
  `TokenSigner` are both `docs/architecture.md` §1.2.2 "default
  implementation" ports (stdlib-only, ships beside its `Protocol`), same
  category as `Clock`/`SystemClock`, which never got one either. Contract
  suites are for the six persistence ports where a fake and a real
  adapter must behave identically across genuinely different backends —
  not this case, and never in the approved `design.md`/`tasks.md` scope.
  Sent the other 5 findings back to the implementer (same agent, resumed)
  for a fix pass.
- implementer (fix pass): killed the surviving mutant (added
  `test_is_expired_false_at_exactly_thirty_days`, verified by hand — mutant
  applied, new test failed, reverted); replaced the vacuous R22 test with a
  pre-populated content repository asserted byte-for-byte unchanged; added
  structural tests for R6 (`test_account_admin_exposes_no_self_registration_operation`),
  R10 (`test_admin_set_password_authorizes_any_admin_actor_identically`), R13
  (`test_authentication_exposes_no_self_service_password_change_operation`);
  added the two missing frozen-instance tests (`AuthToken`, `LoginResult`);
  trimmed the three over-length docstrings to point at `design.md` §7/§8.
  `./init.sh` green (441 tests, up from 435). Traceability table in
  `progress/impl_auth_flow.md` updated for R6/R10/R13/R22/R25. Still not
  marked `done`, not committed.
- Leader: sent a cheap-verification request to the same reviewer agent
  (resumed, not a second full review) — re-apply the named mutant, spot
  check the 5 fixes, confirm `./init.sh` green. Awaiting result.
- reviewer (cheap verification, same agent resumed): re-applied the named
  mutant (`session_policy.py`'s `is_expired`, `>` -> `>=`) — killed by the
  new boundary test. Spot-checked all 5 fixes: R22's test now asserts real
  content is unchanged (not `{} == {}`); R6/R10/R13 each exercise a real
  assertion (public-surface pins, two-distinct-admin-actors check); both
  frozen-instance tests raise `FrozenInstanceError`; all three docstrings
  within the 3-line ceiling, pointing at source docs. `./init.sh` green
  (441 tests), tree restored exactly to its pre-review state.

```
APPROVED — 0 findings, 0 mutants survived
```

## Next step

Ready for human sign-off: `specs/auth_flow/`,
`backend/core/src/planner_core/domain/{role,authorization,session_policy,
login_policy,authentication_guards}.py`,
`backend/core/src/planner_core/ports/{password_hasher,tokens,accounts}.py`,
`backend/core/src/planner_core/application/{authentication,account_admin}.py`,
`backend/core/tests/{domain,ports,application}/` (new + ripple files),
`backend/core/tests/support/fakes.py`,
`backend/tests/contract/test_account_repository_contract.py`,
`docs/architecture.md` (§1.2.3, §2 P2 row, access-pattern count),
`docs/requirements.md` (`FR-AUTH-16` amended by `G-87`),
`docs/gaps_and_resolutions.md` (Part W / `G-87`),
`docs/coverage_analysis.md` (backfilled), `docs/data_model.md` (`validoDesde`,
AP4/AP7/AP28, §9 resolved), `AGENTS.md` (access-pattern count),
`feature_list.json` (feature 15 `in_progress`, feature 21 `covers` gains
`NFR-SEC-04`), and `progress/impl_auth_flow.md`. Marking `done` and
committing are human-only. This closes the whole `FR-AUTH-*` family except
`NFR-SEC-04`, which now belongs to feature 21 (Terraform).

- Human: ran an external automated review, `STATUS: FAILED`, 1 violation +
  1 doc-drift observation. Leader verified both directly before acting
  (this project's convention — automated reviewers have been wrong
  before). Violation 2 (architecture.md §1.2.3 still describing the
  pre-`G-87` 12h-inactivity session model) confirmed as leader's own
  oversight from the `G-87` sweep — fixed directly, no decision needed.
  Violation 1 (`Role(StrEnum)` vs. the design-approved `Role(str, Enum)`)
  verified with a direct test: `ruff check` (`UP042`, `target-version =
  "py313"`) genuinely rejects `(str, Enum)` — the implementer had no
  choice — but the report's technical claim was also correct: `str()`/
  f-string output genuinely differs between the two forms (confirmed by
  direct Python test), so the impl report's "behaviourally identical"
  phrasing overstated it, even though no current code relies on the
  difference (grep confirmed). Presented findings, recommended keeping
  `StrEnum` (also the technically better choice — matches the persisted
  literal value). Human: **correct it.**
- Leader: corrected `specs/auth_flow/design.md` §4 (code block + human-
  approval note) and `tasks.md` T2 to show `Role(StrEnum)` with the ruff-
  forced reasoning; corrected `progress/impl_auth_flow.md`'s "behaviourally
  identical" claim to the precise version. No code changed either way.
  `./init.sh` green (441 tests, unchanged).

## Log

- Leader: confirmed features 14/25 done and committed, archived prior
  session to `history.md`, ran `./init.sh` (green, 385 tests) — confirmed
  no actionable feature remained; all 9 blocked features trace to
  undecided architecture items.
- Human: asked to start with the first blocker (P2, auth mechanism).
  Presented the Cognito-vs-application-managed tradeoffs specific to this
  project (feature 9's existing domain password/username policy, the
  12h-inactivity session model, NFR-SEC-04 brute-force protection) via
  `AskUserQuestion`. Decision: **application-managed**.
- Leader: recorded the decision in `docs/architecture.md` (new §1.2.3,
  closed the §2 P2 row), unblocked feature 15 in `feature_list.json` with
  full acceptance criteria, re-ran `./init.sh` green — feature 15 confirmed
  next actionable. Launching spec_author.
