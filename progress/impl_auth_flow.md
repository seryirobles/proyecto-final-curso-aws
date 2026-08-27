# Implementation report — feature 15 `auth_flow`

`./init.sh` green: ruff format, ruff check, mypy --strict, pytest all pass
(441 tests, up from 385). `uv export --package planner-api --no-dev` and
`--package planner-ai --no-dev` both resolve with nothing added; `core`
still `dependencies = []`.

**Reviewer fix pass (this revision):** added the missing exact-boundary
`is_expired` case (mutant `>` → `>=` now killed — verified by hand: mutant
applied, new test failed, reverted), replaced the vacuous R22 test with a
pre-populated content repository asserted byte-for-byte unchanged, added
structural tests for R6/R10/R13, added the two missing frozen-instance
tests (`AuthToken`, `LoginResult`), and trimmed three docstrings
(`HmacTokenSigner`, `InvalidToken`, `InvalidCredentials`) to point at
`specs/auth_flow/design.md` §7/§8 instead of reproducing it. Skipped
per leader's own resolution: no `PasswordHasher`/`TokenSigner` contract
suite — both are §1.2.2 default-implementation ports, not persistence
ports with a real adapter to cross-check against.

## Traceability

| R<n> (FR-*) | Test |
|---|---|
| R1 (FR-AUTH-01) | `test_role.py::test_exactly_two_roles_exist` |
| R2 (FR-AUTH-01,-06) | `test_authorization.py::test_require_admin_raises_forbidden_for_a_user_role` |
| R3 (FR-AUTH-01,-05) | `test_authorization.py::test_require_user_raises_forbidden_for_an_admin_role` |
| R4 (FR-AUTH-06) | `test_authorization.py::test_require_user_passes_for_a_user_role` |
| R5 (FR-AUTH-02) | `test_authentication.py::test_successful_login_returns_a_token_carrying_role_and_pending_flag` |
| R6 (FR-AUTH-03) | `test_account_admin.py::test_account_admin_exposes_no_self_registration_operation` |
| R7 (FR-AUTH-03,-05) | `test_account_admin.py::test_create_user_by_non_admin_raises_forbidden`, `test_rename_user_by_non_admin_raises_forbidden` |
| R8 (FR-AUTH-05,-17) | `test_account_admin.py::test_create_user_rejects_a_taken_username` |
| R9 (FR-AUTH-07,-18) | `test_account_admin.py::test_create_user_never_accepts_an_admin_role` |
| R10 (FR-AUTH-07) | `test_account_admin.py::test_admin_set_password_authorizes_any_admin_actor_identically` |
| R11 (FR-AUTH-08,-10,-11) | `test_account_admin.py::test_create_user_sets_password_reset_required_true`, `test_authentication.py::test_successful_login_returns_a_token_carrying_role_and_pending_flag` |
| R12 (FR-AUTH-02) | `test_authentication.py::test_login_with_unknown_username_raises_invalid_credentials`, `test_login_with_wrong_password_raises_invalid_credentials`, `test_login_policy.py::test_invalid_credentials_carries_the_es_es_message` |
| R13 (FR-AUTH-04) | `test_account_admin.py::test_authentication_exposes_no_self_service_password_change_operation` |
| R14 (FR-AUTH-04) | `test_authentication.py::test_set_password_rejects_when_not_pending`, `test_authentication_guards.py::test_set_password_not_pending_carries_the_es_es_message` |
| R15 (FR-AUTH-10) | `test_authentication.py::test_require_password_set_raises_pending_when_flag_true`, `test_authentication_guards.py::test_password_reset_pending_carries_the_es_es_message` |
| R16 (FR-AUTH-10,-15) | `test_authentication.py::test_set_password_rejects_a_too_short_password`, `test_password_hasher.py::test_hash_then_verify_round_trips_true` |
| R17 (FR-AUTH-10) | `test_authentication.py::test_set_password_clears_the_pending_flag_without_advancing_the_marker` |
| R18 (FR-AUTH-11) | `test_account_admin.py::test_admin_set_password_sets_pending_flag_and_advances_the_marker` |
| R19 (FR-AUTH-11) | `test_account_admin.py::test_admin_set_password_sets_pending_flag_and_advances_the_marker` |
| R20 (FR-AUTH-12) | `test_account_admin.py::test_list_accounts_by_non_admin_raises_forbidden`, `test_list_accounts_returns_username_role_and_pending_status` |
| R21 (FR-AUTH-13) | `test_account_admin.py::test_remove_user_deletes_the_account_and_calls_no_content_repository` |
| R22 (FR-AUTH-13) | `test_account_admin.py::test_remove_user_deletes_the_account_and_calls_no_content_repository` (pre-populated fake, asserted byte-for-byte unchanged) |
| R23 (FR-AUTH-14) | `test_authentication.py::test_authenticate_denies_a_removed_accounts_token` |
| R24 (FR-AUTH-09) | `test_authentication.py::test_logout_advances_the_revocation_marker`, `test_accounts.py::test_revoke_credentials_advances_the_marker_and_touches_nothing_else` |
| R25 (FR-AUTH-16) | `test_session_policy.py::test_is_expired_false_at_exactly_thirty_days`, `test_is_expired_true_just_past_thirty_days`, `test_authentication.py::test_authenticate_with_a_31_day_old_token_raises_session_expired` |
| R26 (FR-AUTH-11) | `test_session_policy.py::test_is_revoked_true_when_issued_at_predates_the_marker`, `test_authentication.py::test_authenticate_with_token_issued_before_the_revocation_marker_raises_session_expired` |
| R27 (FR-AUTH-09) | `test_tokens.py::test_issue_then_verify_round_trips_the_same_user_id_and_issued_at`, `test_authentication.py::test_authenticate_succeeds_for_a_valid_recent_token` |
| R28 (FR-AUTH-09,-16) | `test_authentication.py::test_authenticate_with_tampered_token_raises_session_expired` |
| R29 (FR-AUTH-18) | `test_account_admin.py::test_admin_set_password_on_another_admin_is_permitted` |
| R30 (FR-AUTH-04,-18) | `test_account_admin.py::test_admin_set_password_on_self_raises_forbidden` |
| R31 (FR-AUTH-18) | `test_account_admin.py::test_remove_user_on_an_admin_account_raises_forbidden` |

`FR-AUTH-15` (cited, reuse-only) → R16 → `password_policy.validate_password`
called from `set_password`, itself covered above.
`FR-AUTH-17` (cited, reuse-only) → R8 → `username_policy.validate_username`
called from `create_user`, covered above.

## Deviations from the literal spec text (mechanical, non-design)

- `Role(str, Enum)` (design.md §4) became `Role(StrEnum)` — ruff UP042
  flags the former; verified by direct test against this project's
  `target-version = "py313"` config, not a style preference. **Correction
  (2026-08-27):** the two forms are identical for every comparison and
  `.value` access this feature performs, but NOT for `str()`/f-string
  formatting — `StrEnum` gives `"admin"`, `(str, Enum)` gives the
  Enum-default `"Role.ADMIN"`. Nothing in the shipped code currently
  formats a `Role` that way, so this was not a live bug, but "behaviourally
  identical" overstated it. `design.md` §4 and `tasks.md` T2 corrected to
  match, human-approved.
- `create_user`'s signature includes `user_id: str` and `password_hash: str`
  positional parameters not spelled out in tasks.md's abbreviated T17 —
  `AccountRecord` has no default for either field, and every other
  id-bearing constructor in this codebase (`LibraryRecipe`, `new_candidate`)
  takes the id from its caller rather than generating one internally.
  `password_hash` mirrors `admin_set_password`'s own
  `new_temp_password_hash` parameter: the caller computes the hash via
  `PasswordHasher`, this function only stores it.
