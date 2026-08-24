# Review — feature 5 (`week_plan_model`), round 3

**Verdict:** APPROVED

`F7` is genuinely closed. I re-ran `M57` myself and it now dies on
`assert result.recipe.tools == meal.tools` — the exact assertion the
implementer claims kills it. The three new assertions were each audited for
the "cannot fail" defect by planting a mutation that only that assertion can
catch: **all three are independently killable**, `category` included. Both
`O6` removals were ruled sound and the ruling was *proved*, not reasoned: the
assertion immediately preceding each removed line catches the very defect the
removed line claimed to guard against. Six further probes on
`to_library_entry`'s two branches produced no survivor of `./init.sh`.

`./init.sh` green, 100 passed, run once. `candidate.py` unchanged since
round 1 — blob `fa4fa32404c0aeedb71f49a89fdf00b09c705c82`, independently
derived here. Working tree byte-identical to its pre-review state.

Round-3 totals: **10 mutations run, 9 killed, 1 equivalent (`M40`,
pre-existing `O2`), 0 genuine survivors.**

---

## Re-run register

House numbering continues: round 1 used `M20`–`M54`, round 2 `M55`–`M57`,
this round adds `M58`–`M66`. Every mutation was applied to
`backend/core/src/planner_core/domain/candidate.py` **only**, one live at a
time, restored from a byte-verified scratchpad backup and SHA-256-checked back
to `d4048ab5…` before the next was applied.
`PYTHONDONTWRITEBYTECODE=1` plus a `__pycache__` purge before **and** after
every run. The whole `core` suite (100 tests) was run for each unless the row
says otherwise.

### Part A — `F7`'s mutant, re-run independently

| # | `R<n>` | Mutation | Result |
|---|---|---|---|
| `M57` | R18 | `to_library_entry`, duplicate path only: `tools=()`, `procedure=()`; `name`, `ingredients`, `category` intact | **killed** — `test_to_library_entry_warns_on_a_normalized_name_collision`, on `test_candidate.py:280` `assert result.recipe.tools == meal.tools` (`AssertionError: assert () == ('olla',)`). `1 failed, 99 passed`. |

The kill matches `progress/impl_week_plan_model_review2.md`'s claim in test,
line and message. `F7` closed.

### Part B — independent-killability audit of the three new assertions

The instruction was that each new assertion must be killable *on its own*, and
`category` in particular must not be made redundant by a neighbour. Each row
below is a mutation crafted so that **exactly one** of the five field
assertions can notice it.

| # | Target assertion | Mutation | Result |
|---|---|---|---|
| `M60` | `result.recipe.tools == meal.tools` (`:280`) | duplicate path: `tools=()` **only** | **killed** on `:280`, and only there. `1 failed, 99 passed`. |
| `M59` | `result.recipe.procedure == meal.procedure` (`:281`) | duplicate path: `procedure=()` **only** | **killed** on `:281`, and only there. `1 failed, 99 passed`. |
| `M58` | `result.recipe.category == meal.category` (`:282`) | duplicate path: `category=IngredientCategory.VEGETABLE` **only** (fixture is `LEGUME`) | **killed** on `:282`, and only there (`assert <…VEGETABLE: 'vegetable'> == <…LEGUME: 'legume'>`). `1 failed, 99 passed`. |

**`category` is not redundant.** `M58` leaves `name`, `ingredients`, `tools`
and `procedure` correct; the four other assertions in the test pass and the
other 99 tests pass. The `category` assertion is the sole thing standing
between that defect and a green suite. Same for `tools` under `M60` and
`procedure` under `M59`. None of the three is decoration.

### Part C — ruling on the two `O6` removals

The brief required proof by mutation, not argument. For each removed
assertion I planted the defect it plausibly guarded and checked the assertion
that *remains* catches it.

| Removed assertion | Preceding assertion that survives | Probe | Result |
|---|---|---|---|
| `assert not isinstance(plan.definitive_id, (list, tuple, set))` | `:69` `assert plan.definitive_id == "c1"` | `M63` — `SlotContents.__post_init__` rewrites `definitive_id` to `(self.definitive_id,)` after its own check, i.e. makes it *literally a collection* | **killed** — `test_slot_contents_holds_candidates_and_at_most_one_definitive` fails at `:69`, `AssertionError: assert ('c1',) == 'c1'`. Suite-wide: **8 failed, 92 passed**. |
| `assert result.meal.name != "Original"` | `:227` `assert result.meal.name == "Editado"` | `M64` — `edit_candidate` returns each candidate unchanged, so the edit never lands and the name stays `"Original"` | **killed** — `test_editing_the_definitive_candidate_propagates` fails at `:227`, `AssertionError: assert 'Original' == 'Editado'`. Suite-wide: **2 failed, 98 passed** (also `test_edit_candidate_replaces_meal_preserving_id_and_author`). |

**Ruling: both removals are correct and neither lost coverage.**

- The first was unreachable-false: any value satisfying `== "c1"` is a `str`,
  so `not isinstance(..., (list, tuple, set))` could never be `False` at that
  point. `M63` shows the equality assertion fires first and fires harder on
  the only defect the isinstance check named. The test's docstring — *"R1:
  `definitive_id` is a single value, never a collection"* — is still
  truthfully earned by the assertion that remains.
- The second was unreachable-false for the same reason: `"Editado" !=
  "Original"` is a tautology once `== "Editado"` has passed. `M64` shows the
  equality assertion catches the propagation failure the `!=` claimed to
  catch.

One caveat recorded rather than held against the feature: `tasks.md` T14 asks
literally to *"assert `definitive_id` is a single value, never a collection"*.
The explicit isinstance line is gone, but `M63` demonstrates the property is
still verified. T14 is satisfied in substance; the task text is now slightly
ahead of the test's letter. Non-blocking — see `O9`.

### Part D — fresh probes on the paths this round touched

| # | `R<n>` | Mutation | Result |
|---|---|---|---|
| `M61` | R18 | `category=IngredientCategory.VEGETABLE` on **both** branches | **killed twice** — `test_to_library_entry_builds_a_new_recipe_from_the_snapshot` **and** `test_to_library_entry_warns_on_a_normalized_name_collision`. `2 failed, 98 passed`. Both input classes now cover `category`; this is the gap `F7` named, closed. |
| `M65` | R18 | duplicate path: `ingredients=()` only | **killed** on `:279` `assert result.recipe.ingredients == meal.ingredients`. |
| `M62` | R19 | `to_library_entry` compares raw names instead of normalized ones (`meal.name == existing`) | **killed** — `assert result.duplicate_warning is True` (`"Tomate "` vs `"tomate"`). Invariant 10 (normalised matching) still live on this path. |
| `M66` | R18 | duplicate path returns the **`MealSnapshot` itself** as `recipe`, all five field values therefore identical | **survives `pytest` (100 passed) — killed by `mypy --strict`**: `candidate.py:147: error: Argument "recipe" to "LibraryEntryResult" has incompatible type "MealSnapshot"; expected "Recipe"  [arg-type]`. `./init.sh` goes **red** on this mutant, so it does not survive the gate suite (`docs/verification.md` Level 1, mandatory). Recorded as `O7`, not as a finding. |
| `M40` | O2, R13 | `promote`'s guard clause dropped (re-run to keep the carried register verified rather than inherited) | **survives — equivalent mutant, confirmed, not a finding.** With the guard gone, `SlotContents.__post_init__` (`candidate.py:44-48`) raises the identical `CandidateNotFound` with the identical `.candidate_id` one line later. No test can distinguish the two. Round 2's ruling stands. |

Both branches of `to_library_entry` are now covered on all five `Recipe`
fields, verified field-by-field rather than asserted in bulk.

---

## Requirement coverage (FR → R)

Ten of ten `covers` ids cited by an `R<n>`, re-checked against the per-`R<n>`
`Implements:` lines in `specs/week_plan_model/requirements.md`. Unchanged
since round 1.

- `FR-MENU-03`: [x] R1, R2, R3, R4, R17
- `FR-CAND-01`: [x] R6, R7, R8, R9, R10, R11
- `FR-CAND-02`: [x] R5
- `FR-CAND-04`: [x] R3, R15
- `FR-CAND-05`: [x] R12, R13, R14
- `FR-CAND-06`: [x] R18, R19, R20
- `FR-CAND-08`: [x] R16
- `FR-SUM-01`: [x] R21
- `FR-SUM-03`: [x] R22, R23
- `FR-AUTH-13`: [x] R24

## Test traceability (R → test)

All 24 `R<n>` have at least one concrete value-asserting test. Deltas this
round, and the `O5` audit:

| `R<n>` | Round-3 state |
|---|---|
| R18 | **[x] strong on both branches now** — `test_to_library_entry_builds_a_new_recipe_from_the_snapshot` (non-duplicate, 5 fields) and `test_to_library_entry_warns_on_a_normalized_name_collision` (duplicate, same 5 fields). Killed `M57`, `M58`, `M59`, `M60`, `M61`, `M65`. |
| R1 | [x] `test_slot_contents_holds_candidates_and_at_most_one_definitive` (`M63`), `test_slot_contents_is_frozen` (`M47`, round 2) |
| R14 | [x] `test_editing_the_definitive_candidate_propagates` (`M64`), `test_definitive_resolves_by_id_lookup_not_by_cache` |
| R19, R20 | [x] `M62` and round 2's `M29`/`M56` |
| all others | [x] unchanged from round 2, which verified each by mutation |

**`O5` — closed and accurate.** `progress/impl_week_plan_model.md`'s
`R<n> → test` table now lists all four round-1 additions, each in the right
row: R1 → `test_slot_contents_is_frozen`; R3 →
`test_candidate_is_frozen`; R10 **and** R17 →
`test_removing_a_non_definitive_candidate_leaves_the_definitive_untouched`;
R23 → `test_unknown_user_id_matches_the_seeded_placeholder_account`. Checked
row by row against the test file, not by keyword.

## Tasks complete

T1–T41: all `[x]` in `specs/week_plan_model/tasks.md`; zero `[ ]` remain
(41 ticked lines, counted mechanically and then read). No new task was owed —
this round was three assertions added and two dead ones removed inside
existing tests, plus a document edit.

## Invariants exercised

| Invariant (`docs/architecture.md` §4) | State |
|---|---|
| 2 — Never silently undo the user's reality | [x] `test_removing_a_non_definitive_candidate_leaves_the_definitive_untouched` (`M23` round 2), `M55` for the opposite branch |
| 3 — Warn, do not block (`G-26` library recipe) | [x] the entry is created **and now proven complete** on the warning path: `M57`, `M58`, `M59`, `M60`, `M65` all die there. This is the invariant `F7` was quietly hollowing. |
| 3 — Warn, do not block (candidate duplicate, `G-59`) | [x] `test_add_candidate_warns_on_a_normalized_name_match` |
| 9 — Removed users leave content behind | [x] `test_a_candidate_with_an_unknown_author_is_never_excluded`, `test_unknown_user_id_matches_the_seeded_placeholder_account` (`M43`) |
| 10 — Text matching is normalised | [x] `M62` dies on `to_library_entry`; `add_candidate`'s side covered round 1 |
| 11 — Content freezes only at archival | [x] `test_editing_the_definitive_candidate_propagates` (`M64`) |
| 12 — Errors are explicit | [x] `CandidateNotFound` with a populated `.candidate_id`, three kills under `M53` |
| 1 — Snapshots, not references | [x] owned by feature 4; `to_library_entry` rebuilds rather than aliases, and `M66` shows the type gate holds that line |

## Boundaries

- No `*.tf`, `*.tfvars` or `.github/workflows/**` generated: **[x]** —
  `init.sh` §4 tripwire green.
- No architecture decision from §2 taken silently: **[x]** — nothing here
  touches P2–P6.
- Frozen requirement docs unmodified: **[x]** — none of the five appears in
  `git status --porcelain`.
- `feature_list.json`: the **only** diff against `HEAD` is
  `-"status": "pending"` / `+"status": "in_progress"` on feature 5. Nothing
  marked `done`. **[x]**
- `docs/data_model.md` (+9 lines at §5.1): legitimate, not a frozen doc,
  records the human's own gate ruling on `UNKNOWN_USER_ID`. **[x]**

## Layering, conventions, gates

- **Layering** (`docs/architecture.md` §3.1): `candidate.py` imports stdlib
  plus four sibling `domain` modules and nothing else. No import of
  `planner_core.application` or `planner_core.ports` anywhere under
  `domain/`; no `boto3`/`botocore`/`lambda_api`/`lambda_ai` anywhere under
  `core/src`. `backend/core/pyproject.toml:6` still `dependencies = []`.
  **[x]**
- **Ambient time**: `backend/core/tests/test_no_ambient_time.py` and
  `test_shared_kernel_guards.py` are both tracked and show **no diff against
  `HEAD`** — no exemption widened, no allowance loosened, no self-check
  deleted — and both pass in the green suite. **[x]**
- **Comment ceiling** (three lines, tests included): `candidate.py` and
  `test_candidate.py` contain **zero** `#` comments, and every docstring in
  both — 16 and 30 respectively — is **one line**. Measured, not eyeballed.
  Nothing reproduces a document; the one docstring that cites one
  (`test_candidate.py:322`) points at `docs/data_model.md` §5.1 and stops.
  **[x]**
- **ASCII**: byte scan, not visual. `candidate.py` 5 738 bytes,
  `test_candidate.py` 12 570 bytes, **zero bytes above `0x7F`** in either.
  **[x]**
- **Language rule**: Spanish appears in `test_candidate.py` only as fixture
  data (`"Lentejas con chorizo"`, `"Cocer las lentejas."`, `"olla"`,
  `"Tomate "`, `"Editado"`), matching `test_recipe.py`'s precedent. No
  user-facing application string anywhere in the feature. **[x]**
- **One test module per source module**: `domain/` has 7 source modules
  (excl. `__init__.py`) and `tests/domain/` has 7 matching `test_*.py`.
  **[x]**
- **`./init.sh`**: green end to end, **exit 0** — harness files, four docs,
  five frozen docs, `feature_list.json` valid (`blocked: 9, done: 4,
  in_progress: 1, pending: 9`), coverage check 103/103 ids, `ruff format`,
  `ruff check`, `mypy`, `pytest 100 passed`, `prettier --check`, `eslint`,
  `vitest`. **Run once.** **[x]**

## No source file changed — hash algorithm stated

**Algorithm: SHA-256 over the raw file bytes (`sha256sum`), cross-checked
against Git's own blob identity — SHA-1 over `blob <bytelen>\0` + content, via
`git hash-object`.** Both were computed before the first mutation and again
after the last revert; both agree, and each individual mutation additionally
re-verified the SHA-256 immediately on restore (printed by the harness, `ok=True`
on all ten).

| File | SHA-256 | `git hash-object` | vs. previous round |
|---|---|---|---|
| `candidate.py` | `d4048ab5ae990d721e420266ea55d2599aca01a22129998ef3463e9d84f596d9` | `fa4fa32404c0aeedb71f49a89fdf00b09c705c82` | **identical to rounds 1 and 2** |
| `test_candidate.py` | `ee7c43e69550c35354f4d844e99ce4aa638585766128e6b7d14430a6eae65828` | `083b64be49837cd0ad34399e3cad74082d7c4b97` | changed from round 2's `81d8d83d` — the expected test-only edit |

`candidate.py`'s blob `fa4fa324` is independently derived here and matches the
leader's confirmation and the implementer's claim. **No source file in the
repository was modified by the implementer this round or by me at any point.**
`git diff --name-only HEAD -- backend frontend` is **empty**.

## Checkpoints

- **C1** — harness base files, four docs, five frozen docs unmodified,
  `./init.sh` exit 0: **[x]**
- **C2** — exactly one `in_progress` (feature 5); all 9 `blocked` features
  carry a `blocked_reason`; `progress/current.md` describes this session:
  **[x]**
- **C3** — domain imports no `application`/`ports`/adapter/handler/AWS SDK;
  `core` has zero runtime dependencies; ambient-time guard green and
  unmodified; exactly two Lambda packages; no stray `print()`, no
  context-free TODO (zero `#` comments at all): **[x]**
- **C4** — `ruff format --check`, `ruff check`, `mypy --strict` (no new
  `# type: ignore`), `pytest -q` 100 passed; `core` tests need no clock,
  network or filesystem; one test module per source module: **[x]**, with the
  standing `Clock` contract-suite deferral to feature 14 left unticked by the
  human's own recorded decision (`CHECKPOINTS.md` C4 note).
- **C5** — no stray artefacts, no `__pycache__` left behind (purged and
  re-checked after the last revert); `progress/history.md` carries the feature
  4 entry; feature 5 correctly left `in_progress`: **[x]**
- **C6** — spec folder complete, strict EARS, every `R<n>` cites an `FR-*`,
  every `covers` id appears in an `R<n>`, every `R<n>` covered by a concrete
  test, all 41 tasks `[x]`, `init.sh` coverage check green (103/103): **[x]**
- **C7** — no `*.tf`, no `.github/workflows/**`, no §2 decision taken
  silently, no requirement invented, frozen docs unedited: **[x]**

## Tree state

**Tree restored: [x]** `git status --porcelain` after the last revert is
**character-identical** to the snapshot taken at step 2 of this review — the
same 4 modified paths (`docs/data_model.md`, `feature_list.json`,
`progress/current.md`, `progress/history.md`) and the same 10 untracked
entries, in the same order. Both feature files hash-verified above. No
`__pycache__` directory remains under `backend/`. `pytest -q` re-run after the
final revert: **100 passed**.

**I edited no file in the repository.** Every mutation was applied to
`candidate.py` alone, one at a time, and restored by byte copy from a
scratchpad backup whose own SHA-256 was asserted equal to the baseline before
each application. No test file was ever touched. **No git write command was
run at any point** — no `add`, no `commit`, no `stash`, no `checkout`. The
harness and the backups live in the session scratchpad, outside the
repository. `candidate.py`, `prototypes/`, `frontend/` and all five frozen
requirement docs are exactly as I found them.

---

## Carried observations (open register for feature 6's reviewer)

- **O2 — `promote`'s guard is an equivalent mutant. Not a finding.**
  Re-verified this round (`M40` above), not merely inherited. Dropping the
  explicit `if not any(...): raise CandidateNotFound(candidate_id)` from
  `promote` leaves the suite green, because `SlotContents.__post_init__`
  raises the identical exception with the identical `.candidate_id` one line
  later. No test can distinguish them. The guard is dead code in the strict
  sense and **should stay** — it is where a reader looks for R13's
  precondition. Do not "fix" this by weakening `__post_init__`.
- **O3 — `candidate.py` is not in `SHARED_KERNEL_MODULES`, correctly.**
  `test_shared_kernel_guards.py`'s self-check pins that set to exactly
  `text.py`, `units.py`, `recipe.py`, `ingredient_category.py`.
  `candidate.py` declares no vocabulary of its own, and
  `test_planner_core_has_one_name_fold` scans all of `src/planner_core`
  except `text.py`, so a second fold planted in `candidate.py` would be
  caught today. Its ASCII-only property is true in fact (byte-verified
  above) but not mechanically pinned — as `design.md` §7 states.
- **O4 — no user-facing Spanish literal outside fixture data.** Unchanged.
  The es-ES messages module still owns nothing from this feature, correctly:
  `CandidateNotFound` carries an id, not a sentence.
- **O7 (new, non-blocking) — R18's "a `Recipe`, not a `MealSnapshot`" rests
  on `mypy` for the duplicate path.** `M66` returns the `MealSnapshot` itself
  from the warning branch; all five field values are then trivially equal and
  **no test fails**. `mypy --strict` rejects it outright, so `./init.sh` goes
  red and the mutant does not survive the mandatory Level-1 gate — this is
  *not* a coverage finding, and I am not requiring a test. It is worth
  knowing that the `assert not isinstance(result.recipe, MealSnapshot)` line
  exists on the non-duplicate path only (`test_candidate.py:268`), so if a
  future feature ever relaxes the annotation, the type gate is the only thing
  holding that half of R18.
- **O8 (new, non-blocking) — `progress/impl_week_plan_model.md`'s "Test
  output summary" section is two rounds stale.** It still reports
  `96 passed` and *"25 new in `test_candidate.py`"*; the true figures are
  **100 passed** and **29 tests** in that module. `O5` asked only for the
  traceability table, which was updated correctly; this adjacent section was
  not. Document drift in a progress report, not a coverage gap.
- **O9 (new, non-blocking) — `tasks.md` T14's wording now runs slightly ahead
  of its test.** T14 says *"assert `definitive_id` is a single value, never a
  collection"*; after the sanctioned `O6` removal the test asserts
  `== "c1"`, which `M63` proves catches exactly that defect. Substantively
  satisfied. Flagged only so a later reader does not mistake the mismatch for
  a dropped requirement.

**`O1`, `O5` and `O6` are closed.** `F1`–`F7` are all closed.

---

## What remains for the human

Nothing is required of the implementer or of any agent. Feature 5 is code
complete, spec complete, traceable in both directions, and mutation-tested
across three rounds with no surviving mutant.

Two acts remain, and **both are the human's alone — no agent may perform
either**:

1. **Mark feature 5 `done`** in `feature_list.json` (change
   `"status": "in_progress"` to `"status": "done"` on the feature with
   `"id": 5`). I have deliberately left it `in_progress`.
2. **Commit** the feature. The working tree currently carries feature 5's two
   new files (`backend/core/src/planner_core/domain/candidate.py`,
   `backend/core/tests/domain/test_candidate.py`), its `specs/week_plan_model/`
   folder, the five `progress/` reports from the three review rounds, and the
   `docs/data_model.md` §5.1 addition. Nothing is staged; no agent has touched
   git.

After that, `init.sh` will report feature 6 `rules_model` as next actionable
(it already does — `depends_on: [2, 4]`, both `done`).
