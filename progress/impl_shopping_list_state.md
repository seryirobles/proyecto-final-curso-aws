# Implementation report — shopping_list_state (feature 8)

## Files

- `backend/core/src/planner_core/domain/shopping.py` — extended with
  `ShoppingItem`, `ShoppingItemNotFound`, `InsufficientNewIds`, `add_item`,
  `edit_item`, `remove_item`, `check_item`, `uncheck_item`, `unchecked_items`,
  `checked_items`, `outstanding_amounts`, `resync`. Feature 7's functions
  (`in_scope_slots` through `required_shopping_items`) untouched.
- `backend/core/tests/domain/test_shopping.py` — extended with 24 new tests
  (feature 7's 21 tests untouched); 45 total in the module. Three of the 24
  (`test_outstanding_amounts_omits_the_exact_zero_boundary`,
  `test_resync_writes_to_the_first_of_two_matching_unchecked_items`,
  `test_resync_preserves_the_matched_items_own_name_and_unit`) were added
  after reviewer mutation testing (M3, M5, M6) — see below.
- `specs/shopping_list_state/requirements.md` — added R20 (first-occurrence
  tie-break) and R21 (matched-write touches quantity only), both
  human-approved gate decisions from `design.md` §9 that lacked a stated
  requirement.

## Traceability — R<n> -> test

| R<n> | FR-* | Test |
|---|---|---|
| R1 | FR-SHOP-01, FR-SHOP-04, FR-SHOP-08 | `test_shopping_item_has_exactly_the_fixed_fields` |
| R2 | FR-SHOP-02 | `test_add_item_appends_unconditionally` |
| R3 | FR-SHOP-02 | `test_edit_item_replaces_name_and_quantity` |
| R4 | FR-SHOP-02 | `test_edit_item_preserves_unit_and_check_state` |
| R5 | FR-SHOP-02 | `test_remove_item_deletes_the_matching_item` |
| R6 | FR-SHOP-02, FR-SHOP-07 | `test_edit_item_on_unknown_id_raises_shopping_item_not_found`, `test_remove_item_on_unknown_id_raises_shopping_item_not_found`, `test_check_and_uncheck_on_unknown_id_raise` |
| R7 | FR-SHOP-07 | `test_check_item_sets_checked_true` |
| R8 | FR-SHOP-07, FR-SHOP-08 | `test_uncheck_item_sets_checked_false` |
| R9 | FR-SHOP-07, FR-SHOP-08 | `test_unchecked_items_and_checked_items_partition_the_list` |
| R10 | FR-SHOP-06 | `test_outstanding_amounts_computes_required_minus_checked`, `test_resync_new_item_carries_the_remainder_not_the_gross_amount` |
| R11 | FR-SHOP-06 | `test_resync_writes_outstanding_to_the_matching_unchecked_item` |
| R12 | FR-SHOP-06, FR-SHOP-08 | `test_resync_creates_a_new_unchecked_item_when_none_matches`, `test_resync_raises_insufficient_new_ids_when_supply_is_exhausted` |
| R13 | FR-SHOP-06 | `test_outstanding_amounts_omits_zero_or_negative` |
| R14 | FR-SHOP-04, FR-SHOP-06 | `test_resync_never_removes_a_stale_or_manual_item` |
| R15 | FR-SHOP-08 | `test_resync_never_modifies_a_checked_items_quantity_or_state`, `test_resync_new_item_carries_the_remainder_not_the_gross_amount` |
| R16 | FR-SHOP-06 | `test_resync_never_removes_a_stale_or_manual_item`, `test_resync_leaves_a_manual_item_absent_from_the_computed_set_untouched` |
| R17 | FR-SHOP-06, FR-SHOP-10 | `test_resync_is_idempotent_across_two_consecutive_presses` |
| R18 | FR-SHOP-06, FR-SHOP-08, FR-SHOP-10 | `test_resync_retains_checked_and_new_unchecked_item_sharing_a_key` |
| R19 | FR-SHOP-02 | `test_add_item_does_not_reject_a_matching_normalized_name_and_unit` |
| R20 | FR-SHOP-06 | `test_resync_writes_to_the_first_of_two_matching_unchecked_items` |
| R21 | FR-SHOP-06 | `test_resync_preserves_the_matched_items_own_name_and_unit` |

Also added: `test_outstanding_amounts_omits_the_exact_zero_boundary` — the
exact-zero boundary of R13 (checked quantity equals required exactly),
distinct from the negative-only case `test_outstanding_amounts_omits_zero_or_negative`
already asserted.

All `FR-SHOP-01/02/04/06/07/08` from the feature's `covers` array are reached
through the R<n> map above; `FR-SHOP-10` is cited per `requirements.md`'s
scope note (R17, R18).

## G-77 scenario (Level 4 invariant)

`test_resync_new_item_carries_the_remainder_not_the_gross_amount`: checked
`arroz 500 g`, required raised to `800 g` — asserts the checked item is
present unchanged in the result and a new unchecked item with a different id
carries `300 g`, not `800 g`. `resync`'s write loop (`matched_index`) is built
only over unchecked items, via an `if item.checked: continue` guard in the
index-building loop — a tested invariant (mutation-tested, M1: deleting that
line is caught by a failing test), not a structural impossibility. The write
itself hardcodes `checked=False`, so removing the guard would silently
uncheck a purchase rather than raise.

## Test result

`./init.sh`: all gates green — ruff format, ruff check, mypy (strict, 0
errors), pytest 182 passed (45 in `test_shopping.py`), prettier, eslint,
vitest.

## Reviewer round 1 — mutation testing fixes

CHANGES_REQUESTED on M3 (write-scope guard untested), M5 (first-occurrence
tie-break untested), M6 (exact-zero boundary untested), plus one
documentation overstatement. All three mutants were re-planted individually
against the fixed suite and killed, then reverted:

| Mutant | Plant | Killed by |
|---|---|---|
| M3 | `resync`'s write overwrites `name`/`unit` from `ing` instead of `existing` | `test_resync_preserves_the_matched_items_own_name_and_unit` |
| M5 | `matched_index.setdefault(key, idx)` -> `matched_index[key] = idx` (last-occurrence) | `test_resync_writes_to_the_first_of_two_matching_unchecked_items` |
| M6 | `outstanding > 0` -> `outstanding >= 0` (zero boundary) | `test_outstanding_amounts_omits_the_exact_zero_boundary` |

`git diff --stat` on `shopping.py` after the last revert showed only the
originally-intended addition (no stray mutant lines). R20 and R21 were added
to `requirements.md` for the two previously-untraced gate decisions (tie-break,
write-scope), wired into `tasks.md` (T33a, T33b, T24a) and the traceability
table above.

## Deviations from spec

None. `design.md` §6 code was used near-verbatim; the only changes were a
line-length fix on `InsufficientNewIds`'s docstring and renaming a local
`idx` to `match_idx` in `resync` to satisfy mypy strict (shadowing the
enumerate loop variable's inferred type in the same function scope — not a
design decision, a Python/mypy scoping detail). Test fixtures use
`Unit.MILLILITRE` instead of a nonexistent `Unit.LITRE` (the fixed unit
vocabulary from feature 3 has no litre unit).
