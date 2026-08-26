# Implementation report — feature 9 `password_policy`

## Files touched (all new; nothing modified)

- `backend/core/src/planner_core/messages.py`
- `backend/core/src/planner_core/domain/password_policy.py`
- `backend/core/src/planner_core/domain/username_policy.py`
- `backend/core/tests/domain/test_password_policy.py`
- `backend/core/tests/domain/test_username_policy.py`

## R<n> -> test map

| R<n> | FR-* | Test(s) |
|---|---|---|
| R1 | FR-AUTH-15, FR-UX-03 | `test_password_shorter_than_ten_raises_password_too_short`, `test_password_of_exactly_ten_characters_is_not_rejected_for_length` |
| R2 | FR-AUTH-15 | `test_password_of_two_hundred_characters_is_accepted` |
| R3 | FR-AUTH-15 | `test_all_lowercase_password_is_not_rejected_for_composition`, `test_all_digit_password_is_not_rejected_for_composition` |
| R4 | FR-AUTH-15 | `test_validate_password_signature_has_no_age_or_rotation_parameter` |
| R5 | FR-AUTH-17 | `test_username_matching_an_active_account_case_and_accent_insensitively_raises`, `test_username_matching_the_reserved_placeholder_name_raises_username_reserved` |
| R6 | FR-AUTH-17, FR-UX-03 | `test_username_matching_an_active_account_case_and_accent_insensitively_raises`, `test_username_absent_from_active_usernames_is_not_rejected`, `test_removed_accounts_username_is_not_rejected_when_absent_from_active_usernames` |
| R7 | FR-AUTH-17, FR-UX-03 | `test_username_matching_the_reserved_placeholder_name_raises_username_reserved`, `test_reserved_name_check_wins_over_a_stray_active_usernames_entry` |

All `FR-*` ids in the feature's `covers` (`FR-AUTH-15`, `FR-AUTH-17`) and the
pre-anticipated `FR-UX-03` are reachable through the R<n> rows above.

## Dependency check (T20)

`backend/core/pyproject.toml` still reads `dependencies = []`.
`uv export --package planner-api --no-dev` and `uv export --package
planner-ai --no-dev` both resolve unchanged (only `-e ./core` plus each
Lambda's own path) — no runtime dependency added.

## Test count

Before: 182. After: 193 (+11: 6 in `test_password_policy.py`, 5 in
`test_username_policy.py`).

## `./init.sh` (T21)

All gates green: ruff format, ruff check, mypy --strict, pytest (193 passed),
prettier, eslint, vitest.
