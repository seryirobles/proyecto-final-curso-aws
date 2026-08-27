# Implementation report — feature 5 `week_plan_model`

## Files

### Created

- `backend/core/src/planner_core/domain/candidate.py` — `UNKNOWN_USER_ID`,
  `CandidateNotFound`, `Candidate`, `SlotContents` (with `__post_init__`
  raising on a dangling `definitive_id`), `AddCandidateResult`,
  `LibraryEntryResult`, `new_candidate`, `definitive`, `add_candidate`,
  `edit_candidate`, `remove_candidate`, `promote`, `clear_definitive`,
  `summary`, `to_library_entry`, `resolve_author`. Matches `design.md` §6
  signatures exactly, except one import fix (see *Deviations* below).
- `backend/core/tests/domain/test_candidate.py` — 25 tests covering R1–R24.

### Modified

None. `backend/core/pyproject.toml` still reads `dependencies = []`;
`SHARED_KERNEL_MODULES` in `test_shared_kernel_guards.py` intentionally left
unchanged per `design.md` §7.

## Deviations from the spec's literal text

`design.md` §6 shows `from collections.abc import AbstractSet, Iterable,
Mapping`. `collections.abc` has no `AbstractSet` member (it is `Set`;
`AbstractSet` is only in `typing`, deprecated). `mypy --strict` rejected the
literal import. Fixed with `from collections.abc import Set as AbstractSet`,
which keeps the exact parameter annotation `known_user_ids: AbstractSet[str]`
that R22/R23 specify — a stdlib import typo fix, not a design or architecture
decision.

Two tests (`test_definitive_resolves_by_id_lookup_not_by_cache`,
`test_promote_sets_the_definitive_and_replaces_any_previous`) needed an
explicit `is not None` narrowing before dereferencing `definitive(...)`'s
result, since it is typed `Candidate | None` under `mypy --strict`.

## Traceability

| R<n> (FR-*) | Test |
|---|---|
| R1 (FR-MENU-03) | `test_slot_contents_holds_candidates_and_at_most_one_definitive`, `test_slot_contents_is_frozen` |
| R2 (FR-MENU-03) | `test_slot_contents_rejects_a_dangling_definitive_id` |
| R3 (FR-MENU-03, FR-CAND-04) | `test_candidate_fields_are_exactly_the_fixed_shape`, `test_candidate_is_frozen` |
| R4 (FR-MENU-03) | `test_definitive_resolves_by_id_lookup_not_by_cache` |
| R5 (FR-CAND-02) | `test_new_candidate_is_the_only_construction_path` |
| R6 (FR-CAND-01) | `test_add_candidate_always_appends` |
| R7 (FR-CAND-01) | `test_add_candidate_warns_on_a_normalized_name_match`, `test_add_candidate_does_not_warn_on_distinct_names` |
| R8 (FR-CAND-01) | `test_add_candidate_warns_on_a_normalized_name_match` |
| R9 (FR-CAND-01) | `test_edit_candidate_replaces_meal_preserving_id_and_author` |
| R10 (FR-CAND-01) | `test_remove_candidate_removes_the_matching_one`, `test_removing_a_non_definitive_candidate_leaves_the_definitive_untouched` |
| R11 (FR-CAND-01) | `test_edit_and_remove_raise_on_an_unknown_id` |
| R12 (FR-CAND-05) | `test_promote_sets_the_definitive_and_replaces_any_previous` |
| R13 (FR-CAND-05) | `test_promote_raises_on_an_unknown_id` |
| R14 (FR-CAND-05, G-67) | `test_editing_the_definitive_candidate_propagates`, `test_definitive_resolves_by_id_lookup_not_by_cache` |
| R15 (FR-CAND-04) | `test_edit_candidate_replaces_meal_preserving_id_and_author`, `test_promote_takes_no_author_or_promoter_argument` |
| R16 (FR-CAND-08) | `test_clear_definitive_unsets_it_and_keeps_candidates` |
| R17 (FR-MENU-03) | `test_removing_the_definitive_candidate_clears_it`, `test_removing_a_non_definitive_candidate_leaves_the_definitive_untouched` |
| R18 (FR-CAND-06) | `test_to_library_entry_builds_a_new_recipe_from_the_snapshot` |
| R19 (FR-CAND-06) | `test_to_library_entry_warns_on_a_normalized_name_collision`, `test_to_library_entry_does_not_warn_without_a_collision` |
| R20 (FR-CAND-06) | `test_to_library_entry_warns_on_a_normalized_name_collision` |
| R21 (FR-SUM-01) | `test_summary_contains_exactly_the_definitive_holding_slots` |
| R22 (FR-SUM-03) | `test_resolve_author_returns_the_id_unchanged_when_known` |
| R23 (FR-SUM-03) | `test_resolve_author_substitutes_the_placeholder_when_unknown`, `test_resolve_author_is_idempotent_on_the_placeholder`, `test_unknown_user_id_matches_the_seeded_placeholder_account` |
| R24 (FR-AUTH-13) | `test_a_candidate_with_an_unknown_author_is_never_excluded` |

All ten `covers` ids (`FR-MENU-03`, `FR-CAND-01`, `FR-CAND-02`, `FR-CAND-04`,
`FR-CAND-05`, `FR-CAND-06`, `FR-CAND-08`, `FR-SUM-01`, `FR-SUM-03`,
`FR-AUTH-13`) trace through the R<n> column above to at least one test.

## Test output summary

```
uv run pytest -q
........................................................................ [ 75%]
........................                                                 [100%]
96 passed in 0.11s   # superseded: 100 passed after review rounds 1-2
```

96 backend tests total (71 pre-existing + 25 new in `test_candidate.py`).

> **Superseded 2026-08-24 (`O8` of `progress/review_week_plan_model_round3.md`).**
> The figures above are this report's original round. After review rounds 1
> and 2 the true totals are **100 passed**, **29 tests** in
> `test_candidate.py`. See `progress/impl_week_plan_model_review1.md` and
> `_review2.md`. The traceability table above was updated in place (`O5`);
> this section is left as the dated record of the first run.
`./init.sh` finished with `[OK] Environment ready` — ruff format, ruff check,
mypy --strict, pytest (96 passed), plus prettier/eslint/vitest on the
frontend, all green.

## `tasks.md`

All 41 tasks (T1–T41) ticked `[x]`.

## Anything the spec did not anticipate

Only the `collections.abc.AbstractSet` import typo above. No other gap: the
design's signatures, the four gate-approved decisions (`UNKNOWN_USER_ID`
literal, caller-supplied ids, no `Recipe.author`, silent `remove_candidate`
clear), and the pointer-not-flag shape for `definitive` all implemented as
written, with no propagation logic needed for R14 beyond `definitive()`
being a fresh lookup on every call, as `design.md` §5 predicted.

Feature left `in_progress`; not marked `done` (reviewer's decision).
