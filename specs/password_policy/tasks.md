# password_policy — Tasks

> Execute in order. Tick `[x]` as each completes.
> Read `design.md` §4 before touching `messages.py` — this is the first
> backend es-ES messages module, not a placeholder.
> The breached-password blocklist (`_COMMON_PASSWORDS`, `PasswordBlocklisted`)
> is out of scope — deferred by `G-83`, see `requirements.md`'s revision note
> and `design.md` §0. No task below builds it.

## Messages module (`backend/core/src/planner_core/messages.py`, new)

- [x] T1 — Create `messages.py` with `PASSWORD_TOO_SHORT`,
  `USERNAME_ALREADY_TAKEN`, `USERNAME_RESERVED` as the three literal es-ES
  strings in `design.md` §4. Covers: R1, R6, R7.

## Domain — password (`backend/core/src/planner_core/domain/password_policy.py`, new)

- [x] T2 — Add `MIN_LENGTH: Final[int] = 10` (`design.md` §5). Covers: R1.
- [x] T3 — Add `PasswordTooShort(PlannerError)` carrying `min_length` and
  `actual_length`, initialized with `messages.PASSWORD_TOO_SHORT`
  (`design.md` §5). Covers: R1.
- [x] T4 — Add `validate_password(password: str) -> None`: raise
  `PasswordTooShort` if `len(password) < MIN_LENGTH`; else return `None`. No
  parameter beyond `password` (`design.md` §5). Covers: R1, R2, R3, R4.

## Domain — username (`backend/core/src/planner_core/domain/username_policy.py`, new)

- [x] T5 — Add `UNKNOWN_USER_NAME: Final[str] = "usuario desconocido"`
  (`design.md` §5, sourced from `docs/data_model.md` §5.1 — do not alter the
  value). Covers: R7.
- [x] T6 — Add `UsernameReserved(PlannerError)` and
  `UsernameAlreadyTaken(PlannerError)`, each carrying `username` and
  initialized with `messages.USERNAME_RESERVED` /
  `messages.USERNAME_ALREADY_TAKEN` respectively (`design.md` §5). Covers:
  R6, R7.
- [x] T7 — Add `validate_username(username: str, active_usernames:
  Iterable[str]) -> None`: fold `username` through `normalize`; raise
  `UsernameReserved` if it matches `normalize(UNKNOWN_USER_NAME)`; else raise
  `UsernameAlreadyTaken` if it matches any folded entry in
  `active_usernames`; else return `None` (`design.md` §5–§6 order:
  reservation before uniqueness). Covers: R5, R6, R7.

## Tests (`backend/core/tests/domain/test_password_policy.py`, new)

- [x] T8 — `test_password_shorter_than_ten_raises_password_too_short` —
  a 9-character password; assert `PasswordTooShort` is raised with
  `min_length == 10` and `actual_length == 9`, and
  `str(exc) == messages.PASSWORD_TOO_SHORT`. Covers: R1.
- [x] T9 — `test_password_of_exactly_ten_characters_is_not_rejected_for_length`
  — a 10-character password; assert `validate_password` does not raise.
  Covers: R1 (boundary).
- [x] T10 — `test_password_of_two_hundred_characters_is_accepted` — a
  200-character password built from repeated characters; assert
  `validate_password` does not raise (proves no ceiling below at least 64,
  `design.md` §7 alternative A). Covers: R2.
- [x] T11 — `test_all_lowercase_password_is_not_rejected_for_composition` —
  a ≥10-character, all-lowercase-letter password; assert `validate_password`
  does not raise. Covers: R3.
- [x] T12 — `test_all_digit_password_is_not_rejected_for_composition` — same
  shape, all digits. Covers: R3.
- [x] T13 — `test_validate_password_signature_has_no_age_or_rotation_parameter`
  — `inspect.signature(validate_password).parameters.keys() == {"password"}`
  (mirrors `specs/shopping_list_state/tasks.md` T12's construction-check
  style). Covers: R4.

## Tests (`backend/core/tests/domain/test_username_policy.py`, new)

- [x] T14 — `test_username_matching_an_active_account_case_and_accent_insensitively_raises`
  — `active_usernames=("José",)`, candidate `"jose"`; assert
  `UsernameAlreadyTaken` is raised, `username == "jose"`, and
  `str(exc) == messages.USERNAME_ALREADY_TAKEN`. Covers: R5, R6.
- [x] T15 — `test_username_absent_from_active_usernames_is_not_rejected` —
  a candidate matching no entry; assert `validate_username` does not raise.
  Covers: R6 (negative case).
- [x] T16 — `test_username_matching_the_reserved_placeholder_name_raises_username_reserved`
  — candidate `"Usuario Desconocido"` (mixed case), `active_usernames=()`;
  assert `UsernameReserved` is raised and `str(exc) ==
  messages.USERNAME_RESERVED`. Covers: R5, R7.
- [x] T17 — `test_reserved_name_check_wins_over_a_stray_active_usernames_entry`
  — `active_usernames=("usuario desconocido",)`, candidate `"Usuario
  Desconocido"`; assert `UsernameReserved`, not `UsernameAlreadyTaken`, is
  raised (`design.md` §6 order). Covers: R7.
- [x] T18 — `test_removed_accounts_username_is_not_rejected_when_absent_from_active_usernames`
  — a candidate matching a name simply not present in `active_usernames`
  (the caller's job to have excluded it); assert `validate_username` does
  not raise — documents the `FR-AUTH-17` reuse-after-removal caller contract
  (`design.md` §5 docstring). Covers: R6 (negative case, caller contract).

## Close-out

- [x] T19 — Record the `R<n> → test` map in
  `progress/impl_password_policy.md` (`docs/verification.md` Level 3).
  Covers: R1–R7.
- [x] T20 — Confirm `backend/core/pyproject.toml` still reads
  `dependencies = []`, and that `uv export --package planner-api --no-dev`
  and `uv export --package planner-ai --no-dev` both resolve with nothing
  added. Covers: R1–R7 (no dependency introduced).
- [x] T21 — Run `./init.sh` and confirm every gate is green: `ruff format`,
  `ruff check`, `mypy --strict`, `pytest` (including
  `test_shared_kernel_guards.py` and `test_no_ambient_time.py`, unmodified
  but re-run), plus the frontend gate. Covers: R1–R7.
