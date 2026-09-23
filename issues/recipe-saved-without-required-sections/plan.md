# recipe-saved-without-required-sections — plan

Triaged as `spec_gap` on 2026-09-22 and re-triaged the same day against the
requirement lift the owner then made: `docs/gaps_and_resolutions.md` **Part Y,
G-89**, amending `FR-LIB-03` (each of the three lists carries at least one
item, enforced at the write boundary, **utensilios included**) and `FR-AI-12`
(an empty section in AI output surfaces as the existing per-slot failure).
`analysis.md`'s root cause is unchanged; only its *Classification* moved to
`defect`.

## Expected behaviour

### E1
Implements: `FR-LIB-03` (as amended by `G-89`), `FR-UX-03`

WHEN a recipe write carries an empty or absent `ingredients` list, the API
SHALL reject the request with `422` and a detail taken from
`planner_core.messages`.

### E2
Implements: `FR-LIB-03` (as amended by `G-89`), `FR-UX-03`

WHEN a recipe write carries an empty or absent `tools` list, the API SHALL
reject the request with `422` and a detail taken from `planner_core.messages`.

### E3
Implements: `FR-LIB-03` (as amended by `G-89`), `FR-UX-03`

WHEN a recipe write carries an empty or absent `procedure` list, the API SHALL
reject the request with `422` and a detail taken from `planner_core.messages`.

### E4
Implements: `FR-LIB-03` (as amended by `G-89`), `FR-AI-12`

WHEN AI output carries an empty `ingredients`, `tools` or `procedure` list,
`validate_ai_recipe_output` SHALL raise a named domain exception instead of
returning a `Recipe`.

### E5
Implements: `FR-AI-12` (as amended by `G-89`; `G-48`, `G-66`)

WHEN `validate_and_preview` receives such output, it SHALL return
`GenerationFailure(INVALID_OUTPUT)` instead of propagating the exception.

### E6
Implements: `FR-LIB-03` (as amended by `G-89`), `FR-CAND-03`, `FR-UX-03`

WHILE the from-scratch authoring form holds no ingredient, no utensilio or no
paso de elaboración, the form SHALL NOT submit the recipe.

### E7
Implements: `FR-LIB-03`, `FR-LIB-02`

WHEN a recipe carries at least one item in each of the three lists, the system
SHALL keep today's outcome — decoded, previewed and submitted unchanged.

E7 holds the line: the rule is a minimum of **one**, and nothing else about a
complete recipe changes.

### E8
Implements: `FR-UX-03`, `FR-LIB-03` (as amended by `G-89`)

*Scope extension, 2026-09-23 — `analysis.md` § Scope extension.* WHILE the
from-scratch authoring form holds no ingredient, no utensilio or no paso de
elaboración, the form SHALL show, beside each empty section, an es-ES warning
from the messages module naming what is missing; a section with at least one
item SHALL show none.

## Fix design

One rule, expressed once in `core/domain` and applied at the two entry points
that admit a recipe from outside, plus the form. Layers per
`docs/architecture.md` §3. `Recipe` itself is untouched — `G-89`'s *Reasoning*
requires that recipes already persisted empty in the running dev environment
stay readable.

| File | Layer | Change |
|---|---|---|
| `backend/core/src/planner_core/domain/recipe.py` | core/domain | Three `PlannerError` subclasses — `MissingIngredients`, `MissingTools`, `MissingProcedure` — and one `require_recipe_sections(ingredients, tools, procedure)` that raises the matching one when a list is empty. Three classes, not one, so each carries its own static es-ES detail through the existing `_TABLE` without touching `build_problem_response` (which issue 5 will already be reworking). |
| `backend/core/src/planner_core/messages.py` | core | Three es-ES constants, e.g. `RECIPE_WITHOUT_INGREDIENTS = "La receta debe incluir al menos un ingrediente."`, `… un utensilio.`, `… un paso de elaboración.` (FR-UX-03). |
| `backend/lambda_api/src/planner_api/serialization.py` | lambda_api | `decode_recipe` calls `require_recipe_sections` on the three decoded tuples before constructing the `Recipe` (E1, E2, E3). |
| `backend/lambda_api/src/planner_api/errors.py` | lambda_api | Three `_TABLE` rows: `422`, codes `MISSING_INGREDIENTS` / `MISSING_TOOLS` / `MISSING_PROCEDURE`, each with its message. |
| `backend/core/src/planner_core/domain/ai_output.py` | core/domain | `validate_ai_recipe_output` calls `require_recipe_sections` (E4); `validate_and_preview` adds the three exceptions to its `except` tuple (E5). |
| `docs/rest_api_contract.md` §4 | doc | Three rows in the exception/status table, beside `UnknownUnit`. |
| `frontend/src/hooks/useRecipeAuthoring.js` | frontend hook | `canSubmit` for the `scratch` method requires `form.ingredients.length > 0 && form.tools.length > 0 && form.procedure.length > 0`; the `// no client validation - FR-LIB-03, G-85` comment goes with it — `G-85` governs servings/time, not section cardinality (E6). |

**Scope extension (E8), frontend only:**

| File | Layer | Change |
|---|---|---|
| `frontend/src/messages/es-ES.js` | frontend messages | Three keys beside `RECIPE_AUTHORING_INVALID_*`, wording mirroring `planner_core.messages`: `RECIPE_AUTHORING_MISSING_INGREDIENTS: 'La receta debe incluir al menos un ingrediente.'`, `RECIPE_AUTHORING_MISSING_TOOLS: '… un utensilio.'`, `RECIPE_AUTHORING_MISSING_PROCEDURE: '… un paso de elaboración.'`. The key names are asserted by the staged test. |
| `frontend/src/components/RecipeAuthoringForm.jsx` (`ScratchFields`) | frontend component | After each section's rows and before its *Añadir …* button, `{form.<section>.length === 0 ? <span style={{ color: tokens.color.honey, fontSize: tokens.fontSize.xs }}>{MESSAGES.…}</span> : null}` — the idiom at `:149-155`. Pure function of `form`, no new state; the hook is untouched. |

**Do not** put the rule in `Recipe.__post_init__` and **do not** touch the
DynamoDB read decoders (`adapters/dynamo/_meal.py`): that is the read path
`G-89` deliberately leaves permissive.

### Live fixtures the fix makes red

Four live fixtures encode the permissive behaviour and must be corrected to the
new rule — they are **fixtures, not assertions**: add the missing item, change
no expectation. They are not staged tests, and none of them is evidence about
section cardinality.

| File | Today | Correction |
|---|---|---|
| `backend/core/tests/support/fakes.py:409-415` (`_default_ai_output`) | `tools=()` | one utensilio; it feeds every week-generation success test through `FakeAiProvider` |
| `backend/core/tests/application/test_week_generation.py:90-96` (`good`) | `tools=()` | one utensilio |
| `backend/lambda_api/tests/test_handler.py:244-250` (`_VALID_RECIPE`) | `"tools": [], "procedure": []` | one item each; used by the 201 path at `:470` |
| `backend/lambda_api/tests/test_markers.py:39-52` | `"tools": [], "procedure": []` | one item each; the test asserts `201` + `ETag` |

`test_handler.py:225-241` and `:287` keep their empty lists and their `400`:
`reject_keys` runs before the section check inside `decode_recipe`, so the
author guard is still what answers. The many `core` tests that build
`Recipe(ingredients=(), tools=(), procedure=())` directly are **unaffected** —
the rule is not a constructor invariant (`G-89`).

### Relationship to the sibling issues on this form

- **Issue 5** (`empty-field-error-messages`, `pending`) owns a row that exists
  but is **blank** — an added-then-untouched utensilio, a blank paso, an
  unselected unidad. This issue owns the row that does **not exist**. The two
  rules compose: `decode_recipe` first rejects a section with zero items
  (here), then issue 5's `require_non_empty` rejects a blank item inside a
  non-empty section. Neither fix needs the other to land first, and neither
  edits the other's lines.
- **Issue 7** (`negative-ingredient-quantity`, `pending`) adds its own clause to
  the same `canSubmit`. Whichever lands second ANDs its clause onto the
  expression; the staged tests of both stay green either way, because each
  fills every field the other checks.

### Rejected alternatives

1. **One `EmptyRecipeSection` exception carrying the section name.** Fewer
   classes, one `_TABLE` row. Rejected because `build_problem_response` takes
   its `detail` from the static `_ErrorSpec`, so a per-section message would
   need the error-mapping machinery changed here as well as in issue 5 — two
   issues editing the same mechanism for the same reason.
2. **Frontend-only guard (`canSubmit` alone).** The SPA is the only writer
   today, so the empty recipe would stop being sent. Rejected because the API
   is the contract boundary and also ingests AI output: `G-89` states the rule
   is enforced at the write boundary, and `FR-AI-12` needs the AI path covered.

## Test plan

| Staged | Destination |
|---|---|
| `issues/recipe-saved-without-required-sections/tests/backend/lambda_api/tests/test_serialization_required_sections.py` | `backend/lambda_api/tests/test_serialization_required_sections.py` |
| `issues/recipe-saved-without-required-sections/tests/backend/core/tests/domain/test_ai_output_required_sections.py` | `backend/core/tests/domain/test_ai_output_required_sections.py` |
| `issues/recipe-saved-without-required-sections/tests/frontend/tests/hooks/useRecipeAuthoring.requiredSections.test.js` | `frontend/tests/hooks/useRecipeAuthoring.requiredSections.test.js` |

The backend tests assert `PlannerError`, the `422` status and a detail drawn
from the messages module — never an exception class or a literal string — so
they constrain the behaviour and not the shape of the fix.

| `E<n>` | Test | At triage |
|---|---|---|
| E1, E2, E3 | `test_decode_recipe_rejects_an_empty_section[…]` (reproduction), `test_decode_recipe_rejects_an_absent_section[…]`, `test_an_empty_section_reaches_the_client_as_422_with_an_es_es_message[…]` | **RED** — 9 cases, `Failed: DID NOT RAISE PlannerError` |
| E4 | `test_ai_output_validation_rejects_an_empty_section[…]` | **RED** — 3 cases, `Failed: DID NOT RAISE PlannerError` |
| E5 | `test_an_empty_section_surfaces_as_a_generation_failure[…]` | **RED** — 3 cases, `validate_and_preview` returns `GenerationSuccess` |
| E6 | `does not submit a recipe with no ingredients / tools / procedure` (reproduction), `does not submit a recipe whose three sections are all empty` | **RED** — 4 cases, `canSubmit` is `true` and `submit()` fires |
| E7 | `test_a_recipe_with_one_item_in_each_section_still_decodes`, `test_a_complete_ai_recipe_still_validates`, `test_a_complete_ai_recipe_still_previews`, `submits a recipe carrying one item in each section` | GREEN, must stay green |

### Red result at triage (2026-09-22)

Staged files copied to their destinations, run, then deleted; the live tree was
left as found (`git status --porcelain` identical before and after).

```
cd backend && uv run pytest lambda_api/tests/test_serialization_required_sections.py \
                            core/tests/domain/test_ai_output_required_sections.py -q
15 failed, 3 passed
```

Twelve of the fifteen are `DID NOT RAISE PlannerError` — the empty list is
accepted at both entry points, exactly the chain `analysis.md` traces — and the
other three are `validate_and_preview` returning
`GenerationSuccess(... procedure=() ...)`. The three passes are E7's backend
regressions.

```
cd frontend && npx vitest run tests/hooks/useRecipeAuthoring.requiredSections.test.js
4 failed | 1 passed (5)
```

All four failures are `expect(result.current.canSubmit).toBe(false)` →
`expected true to be false`, the unconditional `canSubmit` of
`useRecipeAuthoring.js:146-150`. The pass is E7's frontend regression.

### Scope extension (E8, 2026-09-23)

| Staged | Destination |
|---|---|
| `issues/recipe-saved-without-required-sections/tests/frontend/tests/components/RecipeAuthoringForm.requiredSections.test.jsx` | `frontend/tests/components/RecipeAuthoringForm.requiredSections.test.jsx` |

| Test | Covers | Kind |
|---|---|---|
| `warns in es-ES beside an empty {ingredients,tools,procedure} section` | E8 | **reproduction** — one warning, placed after that section's heading and before the next; the other two absent |
| `warns once per section when all three are empty` | E8 | reproduction |
| `shows no section warning on a recipe with one item in each section` | E8, E7 | regression |
| `shows no section warning on the library-pick method` | E8 | regression |

Red at triage (copied, run, deleted; prettier and eslint clean):
`Tests 6 failed (6)`. All six fail at `expect(typeof MESSAGES[key]).toBe('string')`
— the warning keys do not exist, and the form renders no warning for an empty
section, the gap in `analysis.md` § Scope extension. The two regressions are
red only through that key check (same pattern as issue 7's quantity test);
they turn green with the keys and guard against over-warning after.

A throwaway probe (deleted) ran the staged file against a copy of the form
with the idiom above applied and the three keys added: `6 passed`. So the
assertions — placement included — are red for the stated reason, not a
technique artefact.

Suites the fix must leave green: `backend/lambda_api/tests/test_serialization.py`,
`backend/lambda_api/tests/test_error_mapping.py`,
`backend/core/tests/domain/test_ai_output.py`,
`backend/core/tests/domain/test_recipe.py`,
`frontend/tests/hooks/useRecipeAuthoring.test.js`,
`frontend/tests/components/RecipeAuthoringForm.test.jsx`.
