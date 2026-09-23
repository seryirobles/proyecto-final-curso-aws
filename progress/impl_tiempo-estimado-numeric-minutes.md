# tiempo-estimado-numeric-minutes — implementation report

## Summary

`G-90` (Part Z) amends `G-85`/`FR-LIB-03`/`FR-AI-13` for one field only:
`estimated_time` (`tiempo`) moves from a freeform string to a bounded integer
minute count, 0–6000 inclusive, or absent. `servings` is untouched (`G-90`
explicitly leaves it alone; issue 4's `parse_servings` stands). This is a
cross-cutting, design-authorized change — not a bug in the usual sense, the
shipped code correctly implemented the now-superseded `G-85`.

## Fix

One rule, defined once in `backend/core/src/planner_core/domain/recipe.py`,
applied at both write boundaries (client wire, AI output), matching
`plan.md` § *Fix design* exactly (rejected alternatives — widening the domain
to `int | str | None`; coercing at the wire instead of rejecting — are in
`plan.md`, not repeated here).

1. **`recipe.py`** — `MAX_ESTIMATED_MINUTES: Final[int] = 6000`;
   `InvalidEstimatedTime(PlannerError)`; `parse_estimated_minutes(value)`
   (`None` → `None`; a `bool` or non-`int` → raise; outside `[0, 6000]` →
   raise). `Recipe.estimated_time`/`MealSnapshot.estimated_time` →
   `int | None`. **No `__post_init__` check** — `dataclasses.replace(...,
   estimated_time="45 min")` still constructs without raising, so a row
   already persisted under `G-85` stays readable (`G-90`, `G-89`'s
   precedent). Lives in `recipe.py` because `test_no_recipe_metadata_logic.py`
   fully exempts that module by name; a new module naming `estimated_time`
   would fail the scan.
2. **`ai_output.py`** — `RawRecipeOutput.estimated_time: int | str | None`
   (raw, unvalidated, like `category: str`); `validate_ai_recipe_output`
   resolves it through `parse_estimated_minutes`; `validate_and_preview`
   catches `InvalidEstimatedTime` alongside `UnknownUnit`/
   `UnknownIngredientCategory` → the existing per-slot `INVALID_OUTPUT`
   failure (`G-66`), never a propagated raise.
3. **`ai_prompt.py`** — new prompt version **v3** (`RECIPE_METADATA_
   INSTRUCTION_V3`, `JSON_OUTPUT_INSTRUCTION_V3`), registered in
   `PROMPT_INSTRUCTION_VERSIONS["v3"]` reusing every other v2 field
   (`FR-AI-14`/`G-84` append-only — v1/v2 untouched, confirmed by the staged
   `test_the_earlier_prompt_versions_keep_the_wording_they_shipped_with`).
   Both new lines reworded so neither repeats v2's line verbatim (comma→
   semicolon on the schema-keys line; `str|null`→`int|null, whole minutes
   from 0 to 6000 inclusive` on the time line) — `test_no_recipe_metadata_
   logic.py`'s `AI_PROMPT_SANCTIONED_LINES` extended with exactly those two
   new literal lines.
4. **`messages.py`** — `INVALID_ESTIMATED_TIME` es-ES constant naming the
   range.
5. **`lambda_api/errors.py`** — one `_TABLE` row: `InvalidEstimatedTime` →
   `422` / `INVALID_ESTIMATED_TIME` / `messages.INVALID_ESTIMATED_TIME`.
6. **`serialization.py`** — new `parse_estimated_time(value)`: the wrong
   JSON type → `MalformedRequest` (400, same shape `parse_servings` gives);
   a well-formed integer then goes through the domain's
   `parse_estimated_minutes`, whose `InvalidEstimatedTime` surfaces as the
   422 above. Wired into `decode_recipe`.
7. **Both `adapters/dynamo/_meal.py` copies** (`lambda_api`, `lambda_ai`) —
   `content_attrs(estimated_time: int | None)`; `read_estimated_time` returns
   `int(_table.decode_number(value))`, catching `decimal.InvalidOperation`
   to return `None` for a legacy free-text `tiempo` instead of raising
   (`E5`). `weeks.py`/`recipes.py` in both Lambdas needed no change — types
   flow through by inference.
8. **`bedrock.py`** — `estimated_time` passed through raw (no more
   `str(...)` coercion), so a bad model value is rejected by the domain
   validator as an `INVALID_OUTPUT` slot failure, not swallowed into a
   provider parse error.
9. **Frontend** — `RecipeAuthoringForm.jsx`'s Tiempo estimado input:
   `type="number" step="1" min="0" max="6000"`. `useRecipeAuthoring.js`:
   `buildManualRecipe` casts `''`→`null`/`Number(...)`, `recipeToForm` casts
   present→`String(...)` (the same two lines `servings` already has).
   `test_all_strings_from_messages.test.js`'s `SAFE_ATTR_NAMES` gained
   `'min'`/`'max'` (HTML bounds, never copy — same class as issue 4's
   `'step'`).
10. **Labels** — `RECIPE_AUTHORING_ESTIMATED_TIME_LABEL` and
    `RECIPE_DETAIL_ESTIMATED_TIME` both become `'Tiempo estimado (minutos)'`.
    `RecipeDetailView.jsx` needed no code change — it already renders
    `{recipe.estimatedTime}` verbatim next to the label.
11. **`docs/rest_api_contract.md`** — §3.0 rule 8 (integer minute count,
    `[0, 6000]`), §3.1 worked example (`"estimatedTime": 45`), §4 exception
    table (`InvalidEstimatedTime` row).

## Two design points resolved beyond plan.md's literal text (disclosed, not silent)

**A live R17 guard shaped the `_meal.py`/errors design, same discipline as
issue 5.** No conflict this time — `plan.md`'s design (one `_TABLE` row,
static `messages.INVALID_ESTIMATED_TIME`) already respects R17; no deviation
needed here, unlike issue 5's `EmptyField`.

**Two guard false positives found and fixed without touching either guard:**
- `test_no_recipe_metadata_logic.py`'s `INFORMATIONAL_METADATA` scan flagged
  my own new comments in `ai_prompt.py` and `messages.py` for containing the
  literal word `estimated_time` in prose (not in a sanctioned schema line).
  Reworded both comments to say "prep/cook time" instead — no scan-logic
  change, no new exemption.
- `core/tests/domain/test_ai_prompt.py::
  test_resolve_prompt_version_registry_carries_every_expected_version`
  asserts `set(PROMPT_INSTRUCTION_VERSIONS) == {"v1", "v2"}` — a live test
  not named in `plan.md`'s supersession table, but necessarily broken by the
  append-only `v3` registration the design (and the staged
  `test_the_numeric_time_prompt_version_is_registered`) both require.
  Updated the literal set to `{"v1", "v2", "v3"}` — the exact same "correct
  an exact-membership assertion to the new correct state" move issue 4 used
  for `useRecipeAuthoring.test.js`/`useLibrary.test.js`.

## Traceability

| `E<n>` | `FR-*` | Test |
|---|---|---|
| E1 — a whole-minute count, 0–6000, or absent | FR-LIB-03 (G-90) | `test_estimated_time_minutes.py` (range/parser cases); `test_recipe_and_snapshot_declare_estimated_time_as_an_optional_integer` |
| E2 — non-integer/non-null write rejected as malformed | FR-LIB-03 (G-90), FR-CAND-03 | `test_estimated_time_wire.py::test_decode_recipe_rejects_an_estimated_time_of_the_wrong_type`; `useRecipeAuthoring.estimatedTime.test.js` (sends as number/null/re-sends) |
| E3 — numeric stepper control | FR-LIB-03 (G-90), FR-UX-02 | `RecipeAuthoringForm.estimatedTime.test.jsx` "renders … numeric control …", "bounds Tiempo estimado at 0 and 6000 …" |
| E4 — label names the unit, both places | FR-MENU-04, FR-UX-03 | `RecipeAuthoringForm.estimatedTime.test.jsx` "names the unit …"; `RecipeDetailView.estimatedTime.test.jsx` (both cases) |
| E5 — a legacy free-text row reads without raising | FR-LIB-03 (G-90) | `test_estimated_time_wire.py`/`test_estimated_time_legacy_read.py` "reads_a_legacy_free_text_tiempo…" |
| E6 — v3 prompt asks for an integer minute count | FR-AI-13 (G-90), FR-AI-14 | `test_ai_prompt_estimated_time.py` (all three) |
| E7 — bad AI output fails the slot, never persists | FR-AI-12, FR-LIB-03 (G-90) | `test_estimated_time_minutes.py` "…surfaces_as_an_invalid_output_failure" (both), "…still_previews" |
| E8 — out-of-range write is a 422 naming the range | FR-LIB-03 (G-90), FR-UX-03, FR-CAND-03 | `test_estimated_time_wire.py` "…outside_the_range", "…is_a_422_naming_the_permitted_range", "…accepts_both_bounds_exactly" |

`issue_list.json`'s `covers` for issue 11 is reachable through E1–E8 above.

## Test moves and red→green evidence

All 7 staged files moved verbatim (`diff` against staged copies: empty) to
their named destinations (`backend/core/tests/domain/
test_estimated_time_minutes.py`, `…/test_ai_prompt_estimated_time.py`,
`backend/lambda_api/tests/test_estimated_time_wire.py`, `backend/lambda_ai/
tests/test_estimated_time_legacy_read.py`, `frontend/tests/components/
RecipeAuthoringForm.estimatedTime.test.jsx`, `…/RecipeDetailView.
estimatedTime.test.jsx`, `frontend/tests/hooks/
useRecipeAuthoring.estimatedTime.test.js`).

**Red**, before any code change, matching `plan.md` § *Red result at triage*
"Second run (2026-09-23, with the range)" exactly:
- `test_ai_prompt_estimated_time.py` + `test_estimated_time_legacy_read.py`:
  `5 failed, 2 passed`.
- `test_estimated_time_minutes.py` / `test_estimated_time_wire.py`: collection
  error, `ImportError: cannot import name 'MAX_ESTIMATED_MINUTES'`.
- Frontend (3 staged files): `2 files failed | 1 passed`, `6 failed | 4
  passed (10)`.

**Green**, after the fix: all 4 backend staged files together — `54 passed`;
all 3 frontend staged files — `10 passed`. Matches `plan.md`'s own
"Green-after check" count (54) for the backend side.

**Live tests corrected** (`plan.md` § *Live tests this fix supersedes*, plus
the two additions noted above) — deleted 4 obsolete `G-85` cases, updated the
rest at the fixture level, per file:
- `frontend/tests/components/RecipeAuthoringForm.servings.test.jsx` — 2 cases deleted, header updated.
- `frontend/tests/hooks/useRecipeAuthoring.servings.test.js` — 2 cases deleted, 1 fixture (`'45 min'`→`'45'`), header updated.
- `backend/lambda_api/tests/test_serialization_servings.py` — 1 case deleted, docstring updated.
- `backend/lambda_api/tests/test_empty_field_errors.py` — `valid_recipe()` fixture (`"45 min"`→`45`).
- `backend/lambda_api/tests/test_serialization.py` — round-trip fixture (`"45 min"`→`45`, both sides).
- `backend/core/tests/domain/test_recipe.py` — 2 fixtures (`estimated_time=9999`/`30`, both ints).
- `backend/core/tests/domain/test_candidate.py` — 1 fixture.
- `backend/core/tests/domain/test_ai_output.py` — 1 fixture.
- `backend/tests/contract/test_ai_provider_contract.py` — JSON payload + `_EXPECTED`.
- `backend/core/tests/test_no_recipe_metadata_logic.py` — `AI_PROMPT_SANCTIONED_LINES` +2.
- `frontend/tests/test_all_strings_from_messages.test.js` — `SAFE_ATTR_NAMES` +`'min'`/+`'max'`.
- `frontend/tests/hooks/useRecipeAuthoring.test.js` — 2 fixture lines.
- `frontend/tests/hooks/useLibrary.test.js` — base fixture + 2 assertions.
- `backend/core/tests/domain/test_ai_prompt.py` — version-set assertion (found beyond `plan.md`'s table, disclosed above).

No staged test was edited, loosened, skipped or xfailed anywhere.

Full suites: backend `uv run pytest -q -m "not aws and not docker"` — **903
passed, 8 deselected** (was 850 after issue 3's extension — +53: 54 new
staged minus 1 deleted obsolete). Frontend `npx vitest run` — **60 files
passed, 384 passed** (was 57/378 — +3 files/+6 net tests: 10 new staged minus
4 deleted obsolete). `uv run ruff format --check .` / `ruff check .` / `mypy
.` and `npx eslint .` / `npx prettier --check .` all clean. `./init.sh`:
fully green.

`tasks.md` T1–T13 all ticked. `issue_list.json`: no edit made by this
implementer (status was already `in_progress` at session start, per the
batch dispatch). `feature_list.json` and issues 1/2/4/5's already-approved
work untouched.
