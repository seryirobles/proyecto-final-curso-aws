# Implementation report — rollover_job_logic (feature 13)

`backend/core/src/planner_core/domain/rollover.py` (new): `ArchivedWeek`,
`RolloverResult` (both `@dataclass(frozen=True)`), `archive_week`,
`promote_next_to_current`, `init_empty_next_week`, `roll_over` — matches
`specs/rollover_job_logic/design.md` §4 signatures verbatim. No `application/`
piece, no new exception, no new string, no change to `shopping.py` /
`candidate.py` / `calendar.py`. Cleanup calls `shopping.unchecked_items`
directly (design §6 alternative C).

`backend/core/tests/domain/test_rollover.py` (new, 18 tests).

## Traceability

| R<n> | FR-* | Test |
|---|---|---|
| R1 | FR-ARCH-01 | `test_archived_week_has_exactly_the_fixed_fields` |
| R2 | FR-ARCH-02 | `test_archived_week_is_frozen` |
| R3 | FR-MENU-06, FR-MENU-08 | `test_rollover_result_has_exactly_the_fixed_fields`, `test_rollover_result_is_frozen` |
| R4 | FR-MENU-06, FR-ARCH-01 | `test_roll_over_archives_the_former_current_week_identity` |
| R5 | FR-MENU-06, FR-ARCH-01 | `test_roll_over_archives_the_former_current_plans_unchanged` |
| R6 | FR-ARCH-02 | `test_roll_over_archives_the_shopping_list_before_cleanup` |
| R7 | FR-MENU-06 | `test_promote_next_to_current_returns_next_plans_unchanged`, `test_roll_over_new_current_plans_equals_former_next_plans_with_candidates_and_definitive` |
| R8 | FR-MENU-06 | `test_init_empty_next_week_returns_an_empty_mapping`, `test_roll_over_new_next_plans_is_always_empty_regardless_of_inputs` |
| R9 | FR-MENU-06, FR-SHOP-09 | `test_roll_over_shopping_items_equals_the_unchecked_subset_in_order` |
| R10 | FR-MENU-06 | `test_init_empty_next_week_takes_no_parameters` |
| R11 | FR-MENU-08 | `test_step_is_deterministic_on_identical_arguments` (parametrized ×3: `archive_week`, `promote_next_to_current`, `init_empty_next_week`) |
| R12 | FR-MENU-08, FR-SHOP-09 | `test_unchecked_items_of_an_already_clean_list_is_unchanged` |
| R13 | FR-MENU-08 | `test_roll_over_is_deterministic_on_identical_arguments` |

`covers` (FR-MENU-06, FR-MENU-08, FR-ARCH-01, FR-ARCH-02, FR-SHOP-09) — all
five reached via the R<n> map above.

## Test result

`./init.sh` green: `ruff format`, `ruff check`, `mypy --strict`, pytest
295 passed (was 277; +18), prettier, eslint, vitest all green.
`test_shared_kernel_guards.py` and `test_no_ambient_time.py` pass unmodified.

## Deviations from spec

None. `tasks.md` T1-T9 all ticked as done.

## Reviewer follow-up (round 2)

Reviewer found one surviving mutant: `@dataclass(frozen=True)` → `@dataclass`
on `RolloverResult` (`rollover.py:26`) survived because, unlike `ArchivedWeek`,
`RolloverResult` had only a field-shape test, no frozen-instance test. Added
`test_rollover_result_is_frozen`, mirroring `test_archived_week_is_frozen`.
Confirmed by hand: applied the named mutant, reran
`test_rollover.py::test_rollover_result_is_frozen` — failed with
`DID NOT RAISE FrozenInstanceError`, confirming the kill; reverted
`rollover.py` (`git diff` shows no change against HEAD); reran `./init.sh`
green, 295 passed.
