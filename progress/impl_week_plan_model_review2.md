# Round-2 review closure — feature 5 `week_plan_model`

Source: `progress/review_week_plan_model_round2.md`. Source untouched by this
session; `candidate.py` untouched by this session.

## F7 — kills M57

`backend/core/tests/domain/test_candidate.py`,
`test_to_library_entry_warns_on_a_normalized_name_collision`: added
`result.recipe.tools == meal.tools`, `result.recipe.procedure ==
meal.procedure`, `result.recipe.category == meal.category`, matching the five
fields already asserted on the non-duplicate path.

### M57 kill demonstration

Applied the mutant to `candidate.py` in place (duplicate-only branch, `tools`
and `procedure` hollowed to `()`), ran the single test, then reverted:

```
def to_library_entry(meal, existing_names):
    duplicate_warning = any(normalize(meal.name) == normalize(e) for e in existing_names)
    recipe = Recipe(
        name=meal.name,
        ingredients=meal.ingredients,
        tools=() if duplicate_warning else meal.tools,
        procedure=() if duplicate_warning else meal.procedure,
        category=meal.category,
    )
    return LibraryEntryResult(recipe=recipe, duplicate_warning=duplicate_warning)
```

Result: `test_to_library_entry_warns_on_a_normalized_name_collision` failed on
`assert result.recipe.tools == meal.tools` (`AssertionError: assert () ==
('olla',)`). Mutant killed by the new assertion. Reverted immediately.

Blob hash before mutation and after revert (`git hash-object
backend/core/src/planner_core/domain/candidate.py`): both
`fa4fa32404c0aeedb71f49a89fdf00b09c705c82` — identical to the round-1/round-2
baseline. `candidate.py` was not touched by this session; only the mutation
was applied and reverted in place, verified with `git hash-object`.

## O6 ruling

- `test_candidate.py` (pre-fix) `:70`,
  `assert not isinstance(plan.definitive_id, (list, tuple, set))` — cannot
  fail: the preceding line already asserts `plan.definitive_id == "c1"`, a
  str. Any value that satisfies that equality is a str, never a
  list/tuple/set. **Removed.**
- `test_candidate.py` (pre-fix) `:229`, `assert result.meal.name != "Original"`
  — cannot fail: the preceding line already asserts
  `result.meal.name == "Editado"`, and `"Editado" != "Original"` is always
  true given that. **Removed.**

Both confirmed genuinely incapable of failing before removal (no live
mutation could distinguish them from the assertion immediately before).

## O5 — traceability table updated

`progress/impl_week_plan_model.md`'s `R<n>` -> test table now also lists:
`R1` -> `test_slot_contents_is_frozen`; `R3` -> `test_candidate_is_frozen`;
`R10`/`R17` -> `test_removing_a_non_definitive_candidate_leaves_the_definitive_untouched`;
`R23` -> `test_unknown_user_id_matches_the_seeded_placeholder_account`.

## Verification

`./init.sh` (run twice: once after the test edits, once after the mutation
was applied and reverted) — all gates green both times:

```
ruff format: OK
ruff check: OK
mypy: OK
pytest: 100 passed in 0.11s
prettier --check: OK
eslint: OK
vitest: OK
Environment ready.
```

Test count: **100 passed** (unchanged from round 2's baseline — three
assertions added to one existing test, two dead assertions removed from two
existing tests; no test added or removed).

## No source file changed

`candidate.py` git blob hash after this session:
`fa4fa32404c0aeedb71f49a89fdf00b09c705c82`, verified with `git hash-object`,
identical to the value recorded at the top of round 2's review and to the
value recorded immediately before the M57 demonstration mutation in this
session.

## Files touched this session

- `backend/core/tests/domain/test_candidate.py` (F7 additions, O6 removals)
- `progress/impl_week_plan_model.md` (O5 traceability additions)

Feature 5 left `in_progress`; not marked `done` (reviewer's decision).
