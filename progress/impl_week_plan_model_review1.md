# Feature 5 (`week_plan_model`) — review round 1 fixes

Reviewer verdict addressed: `progress/review_week_plan_model.md` (CHANGES_REQUESTED).
All required changes were test-only, in
`backend/core/tests/domain/test_candidate.py`.
`backend/core/src/planner_core/domain/candidate.py` was never edited — hash
before and after this session: `fa4fa32404c0aeedb71f49a89fdf00b09c705c82`
(matches the reviewer's own baseline).

## What was added

- **F1** — `test_removing_a_non_definitive_candidate_leaves_the_definitive_untouched`:
  removes a non-definitive candidate from a plan that has a definitive,
  asserts both `result.definitive_id` and `definitive(result)` survive.
- **F2** — `test_to_library_entry_warns_on_a_normalized_name_collision` now
  asserts `result.recipe.name == meal.name` and
  `result.recipe.ingredients == meal.ingredients` instead of the tautological
  `is not None`.
- **F3** — `test_new_candidate_is_the_only_construction_path` now asserts the
  returned `Candidate.id`, `.meal` and `.author` equal what was passed, for
  all three authoring sources, with distinct authors so a cross-source mix-up
  is detectable.
- **F4** — new `test_unknown_user_id_matches_the_seeded_placeholder_account`
  pins `UNKNOWN_USER_ID == "unknown-user"`, comment points at
  `docs/data_model.md` section 5.1.
- **F5** — new `test_candidate_is_frozen` and `test_slot_contents_is_frozen`,
  following `test_recipe_is_frozen`'s idiom in `test_recipe.py`.
- **O1** — `excinfo.value.candidate_id` asserted in all three existing
  `pytest.raises(CandidateNotFound)` blocks (R2, R11 x2, R13).
- **F6** — already closed by the leader before this session; `design.md`
  section 6 untouched here, per instructions.

Test count: 96 -> 100 (4 new test functions; existing tests only gained
assertions, no new functions for F2/F3/F4/O1).

## Mutant-kill table

| # | Mutation | Test that kills it | Result |
|---|---|---|---|
| M23 | `remove_candidate`: `definitive_id = None` unconditionally | `test_removing_a_non_definitive_candidate_leaves_the_definitive_untouched` | killed |
| M29 | `to_library_entry`: hollow `Recipe` on duplicate path | `test_to_library_entry_warns_on_a_normalized_name_collision` | killed |
| M43 | `UNKNOWN_USER_ID` changed to `"usuario-desconocido"` | `test_unknown_user_id_matches_the_seeded_placeholder_account` | killed |
| M46 | `Candidate`: `@dataclass(frozen=True)` -> `@dataclass()` | `test_candidate_is_frozen` | killed |
| M47 | `SlotContents`: `@dataclass(frozen=True)` -> `@dataclass()` | `test_slot_contents_is_frozen` | killed |
| M48 | `new_candidate` branches on `meal.name`, substitutes author for one source | `test_new_candidate_is_the_only_construction_path` | killed |
| M49 | `new_candidate` discards `author`, always writes `UNKNOWN_USER_ID` | `test_new_candidate_is_the_only_construction_path` | killed |

Each mutation was applied to `candidate.py` alone, verified to make the named
test fail (full traceback captured during the session), then reverted from
the scratchpad backup and hash-checked back to `fa4fa324` before the next
mutation. `PYTHONDONTWRITEBYTECODE=1` was used throughout per the reviewer's
own harness note on stale `__pycache__` producing false survivors.

## Verification

`./init.sh` — all gates green, **100 passed** (`pytest -q`, backend `core`
suite). `ruff format --check`, `ruff check`, `mypy` all green; frontend gates
(`prettier`, `eslint`, `vitest`) unaffected and green.

Tree restored byte-identically apart from the test-file edits:
`git status --porcelain` shows the same modified/untracked set as before this
session (4 modified docs/config files, `candidate.py` + `test_candidate.py`
untracked as they were pre-review, plus the spec/progress files already
present). No source file, spec file or `feature_list.json` status was
touched.

## Not done here (per instructions)

- `candidate.py` was not edited.
- `feature_list.json` was not touched; feature 5 remains `in_progress`.
- No git commit, stage or push was performed.
