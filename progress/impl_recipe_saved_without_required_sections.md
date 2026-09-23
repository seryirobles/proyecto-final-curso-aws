# impl_recipe_saved_without_required_sections

Issue 8. `G-89` (Part Y) requires each of `ingredients`/`tools`/`procedure`
to carry at least one item.

## Red at T1

```
cd backend && uv run pytest lambda_api/tests/test_serialization_required_sections.py \
  core/tests/domain/test_ai_output_required_sections.py -q
15 failed, 3 passed

cd frontend && npx vitest run tests/hooks/useRecipeAuthoring.requiredSections.test.js
Test Files  1 failed (1)   Tests  4 failed | 1 passed (5)
```
Both match `plan.md`'s recorded red exactly.

## Fix

`backend/core/src/planner_core/domain/recipe.py`: `MissingIngredients`/
`MissingTools`/`MissingProcedure` (three classes, per `plan.md`'s rejected-
alternative reasoning — keeps each with its own static `_TABLE` message) and
`require_recipe_sections(ingredients, tools, procedure)`. Called at both
entry points (`serialization.decode_recipe` before `Recipe` is built;
`ai_output.validate_ai_recipe_output`, both new exceptions added to
`validate_and_preview`'s catch tuple). `Recipe.__post_init__` untouched
(G-89's stated reasoning — already-persisted empty recipes stay readable).
Three `messages.py` constants, three `errors.py` `_TABLE` rows,
`docs/rest_api_contract.md` §4 gained three rows.

Frontend: `useRecipeAuthoring.js`'s `canSubmit` for `scratch` now also
requires `ingredients.length > 0 && tools.length > 0 && procedure.length > 0`
before the quantity/servings checks (issue 7's clauses AND on top, as
`plan.md` anticipated — neither fix needed the other to land first).

## Blast radius was wider than `plan.md`'s four named fixtures (disclosed)

`plan.md` named 4 live fixtures. The actual `./init.sh` run surfaced **11**:
the 4 named (`fakes.py::_default_ai_output`, `test_week_generation.py`'s
`good`, `test_handler.py::_VALID_RECIPE`, `test_markers.py`'s inline payload)
plus 7 more that build a `decode_recipe`/scratch-form payload with empty
`tools`/`procedure` incidentally, unrelated to what each file is actually
testing: `test_estimated_time_wire.py::_body`,
`test_serialization_servings.py::_body` (backend); `useRecipeAuthoring.
estimatedTime.test.js`, `useRecipeAuthoring.servings.test.js` (both
`submitScratch` + one `initialRecipe` each), `useLibrary.test.js` (3 submit
tests), `useLibraryMutationVisibility.test.js` (issue 6's own staged test,
E1-E3 mutation cases), and issue 3's approved
`WeekPlannerView.candidateAuthoring.test.jsx` (E2) /
`WeekPlannerView.candidateEditRemove.test.jsx` (`CANDIDATE` fixture, 3 cases)
(frontend). Every correction adds a missing ingredient/tool/procedure item to
a fixture or fills the form via the same `add`/`update` actions the hook
already exposes — **no assertion changed** in any of the 11 files; verified
via `git diff` showing only fixture data and new `fillRequiredSections`-style
helper additions.

## Traceability

| E<n> | FR-* | T<n> | Test |
|---|---|---|---|
| E1 | FR-LIB-03 (G-89), FR-UX-03 | T3/T4 | `test_serialization_required_sections.py` |
| E2 | FR-LIB-03 (G-89), FR-UX-03 | T3/T4 | same file |
| E3 | FR-LIB-03 (G-89), FR-UX-03 | T3/T4 | same file |
| E4 | FR-LIB-03 (G-89), FR-AI-12 | T5 | `test_ai_output_required_sections.py::test_ai_output_validation_rejects_an_empty_section` |
| E5 | FR-AI-12 (G-89, G-48, G-66) | T5 | same file `::test_an_empty_section_surfaces_as_a_generation_failure` |
| E6 | FR-LIB-03 (G-89), FR-CAND-03, FR-UX-03 | T6 | `useRecipeAuthoring.requiredSections.test.js` |
| E7 | FR-LIB-03, FR-LIB-02 | T2-T6 (guard, unchanged) | both backend files' `test_a_recipe_with_one_item...`/`test_a_complete_ai_recipe...`; frontend `submits a recipe carrying one item in each section` |

## Result

Backend: `uv run pytest -q -m "not aws and not docker"` — **949 passed**
(931 → 949: +18 new). `ruff format --check` / `ruff check` / `mypy` clean.
Frontend: `npx vitest run` — **428/428**. `npx eslint .` / `npx prettier
--check .` clean. `./init.sh` green.

`issue_list.json`/`feature_list.json` untouched by this implementer. Not
`done` — reviewer next (batched with the other five issues in this run).

## Fix round 1 — reviewer finding (false comment)

`frontend/src/hooks/useRecipeAuthoring.js:164`'s comment claimed "still no
client validation - FR-LIB-03, G-85" directly above the quantity/servings
checks (`canSubmit`, lines 168-171) that issue 7's fix added — `plan.md` T6
had flagged this comment for removal and it was missed. Removed; no logic
changed. `./init.sh` green (949 backend / 436 frontend).

## Scope extension (2026-09-23): warning text beside empty sections (E8)

Resumed session (prior implementer run stalled on infra timeout, not a logic
error). Red confirmed at T9: 6 failed, each at
`expect(typeof MESSAGES[key]).toBe('string')` — the three
`RECIPE_AUTHORING_MISSING_*` keys did not exist.

`frontend/src/messages/es-ES.js`: three keys added beside
`RECIPE_AUTHORING_INVALID_*`, wording mirrors `planner_core.messages`'
`RECIPE_WITHOUT_INGREDIENTS`/`RECIPE_WITHOUT_TOOLS`/`RECIPE_WITHOUT_PROCEDURE`.
`frontend/src/components/RecipeAuthoringForm.jsx` (`ScratchFields`): a
`tokens.color.honey` span per section, same idiom as the servings/quantity
warnings, placed after that section's row list and before its *Añadir …*
button, shown whenever `form.<section>.length === 0`. No hook change.

| E<n> | FR-* | T<n> | Test |
|---|---|---|---|
| E8 | FR-UX-03, FR-LIB-03 (G-89) | T10 | `RecipeAuthoringForm.requiredSections.test.jsx`, all four cases |
| E7 (regression guard) | FR-LIB-03, FR-LIB-02 | T10 (unchanged) | same file, "shows no section warning on a recipe with one item in each section" |

Moved file confirmed byte-identical to the staged copy (`diff -q`, no
output). `cd frontend && npx vitest run
tests/components/RecipeAuthoringForm.requiredSections.test.jsx
tests/components/RecipeAuthoringForm.test.jsx
tests/components/RecipeAuthoringForm.quantity.test.jsx
tests/components/RecipeAuthoringForm.servingsBound.test.jsx
tests/components/WeekPlannerView.candidateAuthoring.test.jsx` — 36/36 green.
