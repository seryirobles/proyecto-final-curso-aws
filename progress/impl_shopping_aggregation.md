# Implementation report — shopping_aggregation (feature 7)

Status: implemented, `./init.sh` green, awaiting reviewer.

## Files

- `backend/core/src/planner_core/domain/shopping.py` (new) — `in_scope_slots`,
  `definitive_ingredients`, `aggregate_ingredients`, `required_shopping_items`.
- `backend/core/tests/domain/test_shopping.py` (new) — 19 tests.
- No modified files; no dependency added (`planner-core` keeps `dependencies = []`).

## Traceability: `R<n>` -> test (`docs/verification.md` Level 3)

| Requirement | FR-* | Test(s) |
|---|---|---|
| R1 | FR-SHOP-05 | `test_in_scope_slots_includes_current_week_from_today_onward`, `test_required_shopping_items_excludes_a_definitive_outside_scope`, `test_required_shopping_items_merges_across_both_weeks` |
| R2 | FR-SHOP-05 | `test_in_scope_slots_includes_the_whole_next_week`, `test_required_shopping_items_merges_across_both_weeks` |
| R3 | FR-SHOP-05 | `test_definitive_ingredients_includes_a_slots_definitive_meal`, `test_definitive_ingredients_preserves_slot_and_ingredient_order`, `test_required_shopping_items_excludes_a_definitive_outside_scope` |
| R4 | FR-SHOP-05 | `test_definitive_ingredients_ignores_a_slot_with_only_candidates`, `test_definitive_ingredients_ignores_a_slot_absent_from_plans`, `test_required_shopping_items_excludes_candidates_never_promoted` |
| R5 | FR-SHOP-03 | `test_aggregate_ingredients_sums_matching_name_and_unit`, `test_aggregate_ingredients_matches_on_normalized_name`, `test_aggregate_ingredients_keeps_different_normalized_names_separate`, `test_aggregate_ingredients_keeps_the_first_occurrences_spelling`, `test_required_shopping_items_merges_across_both_weeks` |
| R6 | FR-SHOP-03 | `test_aggregate_ingredients_keeps_different_units_separate` |
| R7 | FR-SHOP-10 | `test_required_shopping_items_is_deterministic_across_repeated_invocations`, `test_required_shopping_items_is_idempotent_by_construction`, `test_required_shopping_items_returns_empty_tuple_when_nothing_is_required` |
| R8 | FR-SHOP-03, FR-SHOP-10 | `test_aggregate_ingredients_result_items_are_ingredient_instances`, `test_required_shopping_items_returns_empty_tuple_when_nothing_is_required` |

## Coverage map: `feature_list.json` acceptance -> `R<n>`

| Acceptance criterion | R<n> |
|---|---|
| Aggregation derives only from definitive meals; candidates never contribute (FR-SHOP-05, G-04) | R3, R4 — proved directly by `test_required_shopping_items_excludes_candidates_never_promoted` |
| Scope is the current week from today onward plus the whole next week (FR-SHOP-05) | R1, R2 |
| Items merge only on matching normalized name + unit; no cross-unit conversion (FR-SHOP-03) | R5, R6 |
| The function is pure and deterministic (FR-SHOP-10, G-54) | R7 — proved by two-call and third-call-on-a-copy tests (Level 4 idempotency shape, `docs/verification.md`) |
| Items carry no provenance (G-72, G-73) | R8 |
| Test proves running the aggregation twice yields an identical result | R7 |

## FR-* -> covers array check

`covers`: `FR-SHOP-03`, `FR-SHOP-05`, `FR-SHOP-10` — all three appear in the
`Implements:` line of at least one `R<n>` above (R1-R8), and every `R<n>`
maps to at least one concrete test. Both directions of Level 3 close.

## Test result

```
uv run pytest -q core/tests/domain/test_shopping.py
19 passed
```

Full suite via `./init.sh`: 156 passed, ruff format/check, mypy strict,
prettier, eslint, vitest all green.

## Notes for the reviewer

- Followed all three approved gate answers verbatim: `Ingredient` reused as
  the result type (no `RequiredItem`), first-occurrence-wins on display name,
  module named `domain/shopping.py`.
- `aggregate_ingredients` never constructs `Unit` directly — it carries
  `ingredient.unit` through unchanged, satisfying
  `test_planner_core_never_constructs_unit_directly` (shared-kernel guard, unmodified).
- No exception type added; every function is total over its declared
  parameter types (design.md section 6) — empty input maps to `()`, never
  `None` (docs/architecture.md section 4 invariant 12).
