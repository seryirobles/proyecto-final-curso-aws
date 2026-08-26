# Implementation report — generation_request (feature 10)

## Files

Created:
- `backend/core/src/planner_core/domain/generation.py`
- `backend/core/tests/domain/test_generation.py`

Modified: none.

## R<n> -> test mapping

| R<n> | FR-* | Test(s) |
|---|---|---|
| R1 | FR-AI-03 | `test_generation_mode_has_exactly_the_three_members` |
| R2 | FR-AI-05, FR-RULE-05 | `test_rule_override_fields_are_exactly_the_fixed_shape`, `test_rule_override_is_frozen` |
| R3 | FR-AI-05, FR-RULE-05 | `test_effective_rules_returns_shared_unchanged_when_override_is_none` |
| R4 | FR-AI-05, FR-RULE-05 | `test_effective_rules_applies_the_override_when_given` |
| R5 | FR-RULE-05 | `test_effective_rules_never_mutates_shared` |
| R6 | FR-AI-11 | `test_pinned_target_fields_are_exactly_the_fixed_shape`, `test_pinned_target_is_frozen` |
| R7 | FR-AI-11 | `test_skipped_pin_fields_are_exactly_the_fixed_shape`, `test_skipped_pin_is_frozen` |
| R8 | FR-AI-11 | `test_generation_targets_fields_are_exactly_the_fixed_shape`, `test_generation_targets_is_frozen` |
| R9 | FR-AI-11 | `test_resolve_targets_excludes_disabled_days` |
| R10 | FR-AI-11 | `test_resolve_targets_excludes_days_before_first_day` |
| R11 | FR-AI-11 | `test_resolve_targets_resolves_pins_skips_and_category_remainder` |
| R12 | FR-AI-11 | `test_resolve_targets_resolves_pins_skips_and_category_remainder` |
| R13 | FR-AI-11 | `test_resolve_targets_resolves_pins_skips_and_category_remainder` |
| R14 | FR-AI-11 | `test_resolve_targets_resolves_pins_skips_and_category_remainder` |
| R15 | FR-AI-11 | `test_resolve_targets_resolves_pins_skips_and_category_remainder` |
| R16 | FR-AI-08 | `test_idempotency_key_is_deterministic_for_identical_inputs`, `test_idempotency_key_ignores_construction_order_of_every_sorted_collection` |
| R17 | FR-AI-08 | `test_idempotency_key_changes_when_rules_change` |
| R18 | FR-AI-08 | `test_idempotency_key_changes_when_targets_change`, `test_idempotency_key_changes_when_pinned_slots_change` |
| R19 | FR-AI-08 | `test_idempotency_key_changes_when_week_changes` |
| R20 | FR-AI-03, FR-AI-05 | `test_generation_request_fields_are_exactly_the_fixed_shape`, `test_generation_request_is_frozen` |
| R21 | FR-AI-05, FR-RULE-05 | `test_build_plan_composes_effective_rules_targets_mode_and_key` |
| R22 | FR-AI-11 | `test_build_plan_composes_effective_rules_targets_mode_and_key` |
| R23 | FR-AI-03 | `test_build_plan_composes_effective_rules_targets_mode_and_key` |
| R24 | FR-AI-08 | `test_build_plan_composes_effective_rules_targets_mode_and_key`, `test_build_plan_resubmitting_the_same_request_yields_the_same_key`, `test_build_plan_reflects_a_mode_change_in_the_idempotency_key` |
| R25 | FR-AI-08 | `test_idempotency_key_changes_when_mode_changes`, `test_build_plan_reflects_a_mode_change_in_the_idempotency_key` |

All four `covers` ids (`FR-AI-03`, `FR-AI-05`, `FR-AI-08`, `FR-AI-11`) are reachable through the R<n> rows above.

## Test result

`./init.sh`: PASS (ruff format, ruff check, mypy --strict, pytest, frontend gate all green).

Test count: 193 -> 218 (+25) -> 221 (+3, review round: reviewed-requested fixes below).

## Reviewer round (CHANGES_REQUESTED, 4 findings)

- Finding 1 (required): `pins` sort was untested — extended
  `test_idempotency_key_ignores_construction_order_of_every_sorted_collection`
  to use two `PinRule`s in reversed order. Re-applied the mutant (dropped
  the `pins` sort): caught, test fails.
- Finding 2 (required): `pinned_slots` could be silently absent from the
  hash payload — added `test_idempotency_key_changes_when_pinned_slots_change`,
  holding `open_slots`/`skipped_pins` constant. Re-applied the mutant
  (dropped `pinned_slots` from `slot_ids`): caught, test fails.
- Finding 3 (required): T12 ticked in `specs/generation_request/tasks.md`
  after re-confirming `./init.sh` green.
- Finding 4 (optional): added `test_pinned_target_is_frozen` and
  `test_skipped_pin_is_frozen`, matching R2/R8/R20's style.

Both mutants reverted; tree confirmed clean before finishing.
