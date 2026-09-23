# tiempo-estimado-numeric-minutes — plan

## Expected behaviour

### E1
Implements: `FR-LIB-03` (as amended by `G-90`)

WHERE a recipe carries an estimated prep/cook time, the system SHALL hold it as
a whole number of minutes from 0 to 6000 inclusive, or as absent.

### E2
Implements: `FR-LIB-03` (as amended by `G-90`), `FR-CAND-03`

WHEN a recipe write carries an `estimatedTime` that is neither a JSON integer
nor `null`, the API SHALL reject the request as malformed.

### E3
Implements: `FR-LIB-03` (as amended by `G-90`), `FR-UX-02`

WHILE the from-scratch authoring form is shown, the form SHALL render *Tiempo
estimado* as a numeric control stepping by one, with a minimum of 0 and a
maximum of 6000.

### E4
Implements: `FR-MENU-04`, `FR-UX-03`

WHERE an estimated prep/cook time is displayed or edited, the system SHALL name
its unit in the field's label.

### E5
Implements: `FR-LIB-03` (as amended by `G-90`)

WHILE a recipe persisted before `G-90` holds a free-text `tiempo`, the system
SHALL read it without raising.

### E6
Implements: `FR-AI-13` (as amended by `G-90`), `FR-AI-14`

WHEN a generation prompt is assembled from the numeric-time prompt version, it
SHALL instruct the model to state the estimated prep/cook time as an integer
number of minutes.

### E7
Implements: `FR-AI-12`, `FR-LIB-03` (as amended by `G-90`)

IF AI output carries an estimated prep/cook time that is not an integer from 0
to 6000 inclusive, THEN the system SHALL surface that slot as a failed
generation and SHALL NOT persist the recipe.

### E8
Implements: `FR-LIB-03` (as amended by `G-90`), `FR-UX-03`, `FR-CAND-03`

WHEN a recipe write carries an `estimatedTime` integer outside 0 to 6000
inclusive, the API SHALL reject it with a Castilian-Spanish message naming the
permitted range.

`E8` carries the whole range rule, both ends: the negative case that the first
draft folded into `E2`'s "non-negative" wording moved here when the owner
corrected the bound (2026-09-23). `G-90` still leaves servings alone; no
`E<n>` here touches `servings`, and
`backend/core/tests/test_no_recipe_metadata_logic.py` must stay green — the
field gains a shape and a range, never downstream logic.

## Fix design

One rule, defined once in the domain and applied at both write boundaries; no
new dependency, no frozen-doc change.

| File | Layer | Change |
|---|---|---|
| `backend/core/src/planner_core/domain/recipe.py` | domain | `estimated_time: int \| None` on `Recipe` and `MealSnapshot`; `MAX_ESTIMATED_MINUTES: Final[int] = 6000`; new `InvalidEstimatedTime(PlannerError)` and `parse_estimated_minutes(value) -> int \| None` (`None` stays `None`; a `bool`, a non-`int`, a negative or anything above `MAX_ESTIMATED_MINUTES` raises). It lives here because `test_no_recipe_metadata_logic.py` exempts this module by name - a new module naming `estimated_time` would fail that scan; the module-level int constant is safe, that scan's no-int-constant rule covers `ai_prompt.py` only. |
| `backend/core/src/planner_core/domain/ai_output.py` | domain | `RawRecipeOutput.estimated_time: int \| str \| None` (raw and unvalidated, exactly like `category: str`); `validate_ai_recipe_output` resolves it through `parse_estimated_minutes`; `validate_and_preview` catches `InvalidEstimatedTime` alongside `UnknownUnit` / `UnknownIngredientCategory`, giving the existing `INVALID_OUTPUT` per-slot failure (E7). |
| `backend/core/src/planner_core/domain/ai_prompt.py` | domain | Append **v3** to `PROMPT_INSTRUCTION_VERSIONS` (`G-84`: v1 and v2 are never edited): v2's wording, with a metadata instruction asking for whole minutes as an integer and a JSON-output line declaring `estimated_time` as `int|null`. Word the new lines so they do not repeat v2's verbatim - the scan below matches one line per pattern. |
| `backend/core/tests/test_no_recipe_metadata_logic.py` | test (live) | Add v3's two metadata-bearing prompt lines to `AI_PROMPT_SANCTIONED_LINES`; the scan flags them otherwise. Mechanical allowlist extension, the same move the v2 lines already record. |
| `backend/lambda_api/src/planner_api/serialization.py` | lambda_api | `parse_estimated_time(value)`, called from `decode_recipe`: a value that is neither `null` nor a JSON integer raises `MalformedRequest` (400 - the shape check, the same treatment `parse_servings` gives, E2); an integer is then handed to the domain's `parse_estimated_minutes`, whose `InvalidEstimatedTime` propagates as the 422 below (E8). |
| `backend/core/src/planner_core/messages.py` | messages | New `INVALID_ESTIMATED_TIME` es-ES constant naming the permitted range, e.g. *"El campo Tiempo estimado debe ser un número entero de minutos entre 0 y 6000."* (`FR-UX-03`; `detail` is always a constant, never composed). |
| `backend/lambda_api/src/planner_api/errors.py` | lambda_api | One `_TABLE` row: `InvalidEstimatedTime` -> `422`, code `INVALID_ESTIMATED_TIME`, `messages.INVALID_ESTIMATED_TIME`. |
| `backend/lambda_api/.../adapters/dynamo/_meal.py` and `backend/lambda_ai/.../adapters/dynamo/_meal.py` | adapters | `content_attrs(..., estimated_time: int \| None)`; `read_estimated_time(item) -> int \| None` returns the decoded number and returns `None` when the stored value is not numeric - the legacy free-text row (E5). |
| `backend/lambda_api/.../adapters/dynamo/{weeks,recipes}.py`, `backend/lambda_ai/.../adapters/dynamo/weeks.py` | adapters | Follow the annotation change; no logic. |
| `backend/lambda_ai/src/planner_ai/adapters/bedrock.py` | adapter | Stop coercing with `str(...)`: pass an `int` through as an `int` and anything else as a string, letting the domain validator reject it - so a bad value is an `INVALID_OUTPUT` slot failure, not a provider parse error. |
| `frontend/src/components/RecipeAuthoringForm.jsx` | component | The *Tiempo estimado* input becomes `type="number"` with `step="1"`, `min="0"` and `max="6000"` (E3, E8). No client-side validation logic is added: an out-of-range submit is rejected by the API and its `detail` is shown verbatim, the same path issue 5's empty-field messages take. |
| `frontend/tests/test_all_strings_from_messages.test.js` | test (live) | Add `'min'` **and** `'max'` to `SAFE_ATTR_NAMES` - HTML bounds, never copy; issue 4 added `'step'` there for the same reason. Without both, that scan flags `min="0"` / `max="6000"` as hardcoded prop text. |
| `frontend/src/hooks/useRecipeAuthoring.js` | hook | `buildManualRecipe`: `estimatedTime` becomes `null` when blank and `Number(...)` otherwise; `recipeToForm`: `String(...)` when present - the two lines `servings` already has. Update the `G-85` comment to cite `G-90`. |
| `frontend/src/messages/es-ES.js` | messages | `RECIPE_AUTHORING_ESTIMATED_TIME_LABEL` and `RECIPE_DETAIL_ESTIMATED_TIME` become `'Tiempo estimado (minutos)'` (E4). Changing the constants' values leaves every render site and the no-hardcoded-strings scan untouched. |
| `docs/rest_api_contract.md` | doc | §3.0 rule 8: both fields are integers, `estimatedTime` a minute count in `[0, 6000]` (`G-90`), still purely informational. §3.1 worked example: `"estimatedTime": 45`. §4 exception table: one row, `InvalidEstimatedTime` -> `422` / `INVALID_ESTIMATED_TIME`. |

**Why two rejection shapes.** `docs/rest_api_contract.md` §4 draws the line
itself: *400 = malformed request, 422 = well-formed but rejected by a domain
rule*. A `"45 min"` is the wrong JSON type, so it is malformed (and matches
`parse_servings`); `7000` is a well-formed integer the range rule refuses, so
it is a 422 carrying an es-ES `detail` — which is what `G-90`'s "rejected the
same way an empty required field is" asks for (issue 5's shape: 422 plus a
static `planner_core.messages` constant). Rejected alternative: one error for
both, which would return 422 for a malformed body and contradict §4.

**Backward compatibility (the call `G-90` delegates).** Enforcement sits at the
two write boundaries - `decode_recipe` for clients, `validate_ai_recipe_output`
for the model - and nowhere else. `Recipe` and `MealSnapshot` keep plain
dataclass semantics with no `__post_init__` check, so building one from an old
row never raises; the adapter read maps a non-numeric `tiempo` to `None`, so
the old free text stops being displayed while the recipe stays readable and
re-saveable. That is `G-89`'s precedent applied verbatim.

### Rejected alternatives

1. **Widen the domain to `int | str | None` so legacy text keeps displaying.**
   Nothing would disappear from screen - but the union then travels through
   both `_meal` adapters, `encode_recipe`, the detail view and the authoring
   form, for rows that exist only in one dev environment, and it restates the
   freeform shape `G-90` just removed.
2. **Coerce at the wire instead of rejecting (`int(payload["estimatedTime"])`).**
   Absorbs `"45"` and any client - rejected for the reason issue 4 already
   recorded for `servings`: `"45"` and `45` are different requests under
   `docs/rest_api_contract.md` §4, and coercion hides the client defect instead
   of surfacing it.

## Live tests this fix supersedes

`G-90` supersedes the reasoning these encode, so they are **replaced or
inverted, never worked around**. All are issue 4 / issue 5 work, live today.

| File | Case | What the implementer does |
|---|---|---|
| `frontend/tests/components/RecipeAuthoringForm.servings.test.jsx` | `keeps Tiempo estimado a free-text control (E5, G-85)` | Delete - the staged `RecipeAuthoringForm.estimatedTime.test.jsx` states the opposite. |
| same | `accepts a free-text Tiempo estimado value carrying its own unit (E5, G-85)` | Delete; the staged file covers the controlled numeric field. Update the file header, which cites `G-85`. |
| `frontend/tests/hooks/useRecipeAuthoring.servings.test.js` | `sends estimatedTime as the typed free text, unit included (E7, G-85)` | Delete - superseded by the staged hook test. |
| same | `never parses estimatedTime into a number (E7, G-85)` | Delete - `G-90` requires exactly the parse this forbids. |
| same | `sends servings as null when the field is left empty (E2)` | Fixture only: `estimatedTime: '45 min'` becomes `'45'`. |
| `backend/lambda_api/tests/test_serialization_servings.py` | `test_decode_recipe_keeps_estimated_time_as_the_clients_free_text` | Delete - the staged `test_estimated_time_wire.py` states the opposite. Update the module docstring's `G-85` sentence. |
| `backend/lambda_api/tests/test_empty_field_errors.py` | `valid_recipe()` fixture, line 32 | `"estimatedTime": "45 min"` becomes `45`; otherwise every case in the file starts failing on the wrong field. |
| `backend/lambda_api/tests/test_serialization.py` | round-trip fixture, lines 60 and 68 | `"45 min"` becomes `45`. |
| `backend/core/tests/domain/test_recipe.py` | `test_recipe_accepts_any_servings_and_estimated_time_value` (line 63) and the snapshot fixture (line 136) | Keep the "no constructor validation" claim, with an integer value; mypy `strict` rejects the string otherwise. |
| `backend/core/tests/domain/test_candidate.py` | line 296 fixture | `estimated_time="45 min"` becomes `45`. |
| `backend/core/tests/domain/test_ai_output.py` | line 163 fixture | `estimated_time="30 min"` becomes `30`. |
| `backend/tests/contract/test_ai_provider_contract.py` | lines 27 and 38 | `"estimated_time": "30 min"` becomes `30`, in the JSON and in `_EXPECTED`. |
| `backend/core/tests/test_no_recipe_metadata_logic.py` | `AI_PROMPT_SANCTIONED_LINES` | Extend with v3's lines (see *Fix design*). |
| `frontend/tests/test_all_strings_from_messages.test.js` | `SAFE_ATTR_NAMES` | Add `'min'`. |
| `frontend/tests/hooks/useRecipeAuthoring.test.js` | `submitting the scratch method posts the exact manual body shape` (lines 38, 56) | `'45 min'` becomes `'45'` / `45`. |
| `frontend/tests/hooks/useLibrary.test.js` | `fullRecipe` fixture (line 23) and its two assertions (163, 188) | `'30 min'` becomes `30`; seeded form `'30'`, PUT body `30`. |

Display-only fixtures elsewhere (`RecipeDetailView.test.jsx`, `DaySlot.test.jsx`,
`SummaryView.test.jsx`, `WeekPlannerView.test.jsx`, `useWeekPlanner.test.js`,
`useSummary.test.js`, `useRecipeDetail.test.js`, `LibraryRecipePicker.test.jsx`)
render whatever they are handed and stay green either way; they are not
required edits.

## Test plan

| Staged file (under `issues/tiempo-estimado-numeric-minutes/tests/`) | Destination |
|---|---|
| `backend/core/tests/domain/test_estimated_time_minutes.py` | `backend/core/tests/domain/test_estimated_time_minutes.py` |
| `backend/core/tests/domain/test_ai_prompt_estimated_time.py` | `backend/core/tests/domain/test_ai_prompt_estimated_time.py` |
| `backend/lambda_api/tests/test_estimated_time_wire.py` | `backend/lambda_api/tests/test_estimated_time_wire.py` |
| `backend/lambda_ai/tests/test_estimated_time_legacy_read.py` | `backend/lambda_ai/tests/test_estimated_time_legacy_read.py` |
| `frontend/tests/components/RecipeAuthoringForm.estimatedTime.test.jsx` | `frontend/tests/components/RecipeAuthoringForm.estimatedTime.test.jsx` |
| `frontend/tests/components/RecipeDetailView.estimatedTime.test.jsx` | `frontend/tests/components/RecipeDetailView.estimatedTime.test.jsx` |
| `frontend/tests/hooks/useRecipeAuthoring.estimatedTime.test.js` | `frontend/tests/hooks/useRecipeAuthoring.estimatedTime.test.js` |

| `E<n>` | Test | At triage |
|---|---|---|
| E1 | `parse_estimated_minutes` accepts 0/1/45/5999/6000, reads `None` as `None`, rejects `"45 min"`, `"hora y media"`, `"45"`, `""`, `45.5`, `True`, `[]`; `MAX_ESTIMATED_MINUTES == 6000`; `Recipe`/`MealSnapshot` declare `int \| None`; `snapshot` copies it | **RED** - the module does not import: `cannot import name 'MAX_ESTIMATED_MINUTES'` |
| E2 | `test_decode_recipe_rejects_an_estimated_time_of_the_wrong_type` (7 cases) | **RED** (module import), then must pass; the pre-range draft of this file, which collected, showed the same cases as `Failed: DID NOT RAISE MalformedRequest` |
| E2 | `…keeps_an_integer_estimated_time`, `…absent…`, `…null…`, `test_encode_recipe_emits_the_integer_minute_count` | **RED** (module import), then must pass; they passed on the broken code when the module still collected, and must stay green after |
| E2 | `sends estimatedTime as a number, not the raw input string`; `sends estimatedTime as null when the field is left empty`; `seeds the edit form with the minute count as text` | **RED** - `expected '45' to be 45`, `expected '' to be null`, `expected 30 to be '30'` |
| E2 | `re-sends an edited recipe estimatedTime as a number, not a string` | GREEN, must stay green (guards the edit path across the type change) |
| E3 | `renders Tiempo estimado as a numeric control stepping by one`; `bounds Tiempo estimado at 0 and 6000 minutes` | **RED** - `expected 'text' to be 'number'`, `expected null to be '0'` |
| E3 | `keeps Tiempo estimado a controlled field reporting its value` | GREEN, must stay green |
| E4 | `names the unit in the Tiempo estimado label…` (asserts both the authoring and the detail constant) | **RED** - `expected 'tiempo estimado' to contain 'minutos'` |
| E4 | `RecipeDetailView` renders the minute count next to its label; shows the label with no value when absent | GREEN, must stay green |
| E5 | `test_constructing_a_recipe_with_a_legacy_free_text_value_does_not_raise` | **RED** (module import), then must pass |
| E5 | `test_reading_a_legacy_free_text_tiempo_reads_as_absent_and_never_raises`, `test_reading_a_numeric_tiempo_gives_the_minute_count`, in both `_meal` suites | **RED** - `assert '30 min' is None`, `assert '30' == 30` in `lambda_ai`; the `lambda_api` pair rides the same module import |
| E5 | `test_reading_an_absent_tiempo_is_still_none` (both) | GREEN, must stay green |
| E6 | `test_the_numeric_time_prompt_version_is_registered`; `…declares_estimated_time_as_an_integer`; `…asks_the_model_for_minutes` | **RED** - `assert 'v3' in {...}` / `UnknownPromptVersion: v3` |
| E6 | `test_the_earlier_prompt_versions_keep_the_wording_they_shipped_with` (`G-84`) | GREEN, must stay green |
| E7 | `test_validate_ai_recipe_output_rejects_a_free_text_estimated_time`; `test_a_free_text_estimated_time_surfaces_as_an_invalid_output_failure`; `test_an_out_of_range_estimated_time_surfaces_as_an_invalid_output_failure`; `test_an_integer_estimated_time_still_previews` | **RED** (module import), then must pass |
| E8 | `test_parse_estimated_minutes_rejects_a_count_outside_the_range` (-1, 6001, 100000); `test_decode_recipe_rejects_an_estimated_time_outside_the_range`; `test_an_out_of_range_estimated_time_is_a_422_naming_the_permitted_range` | **RED** (module import), then must pass |
| E8 | `test_parse_estimated_minutes_accepts_both_bounds_exactly`; `test_decode_recipe_accepts_both_bounds_exactly` (0 and 6000 in, boundary regression) | **RED** (module import), then must pass |

### Red result at triage (2026-09-22, range corrected 2026-09-23)

Copied to the destinations, run, deleted; the live tree was left as found
(`git status --porcelain` unchanged apart from `issue_list.json`, `issues/` and
the owner's own doc edits).

The owner's bound correction (`G-90`: 0 to 6000 inclusive, out-of-range
rejected like an empty required field) landed after the first red run. Both
runs are recorded, since the first one exercised assertions the second folds
into a module that no longer imports.

**First run (2026-09-22, pre-range file):**

- backend `-q` over the four modules -> **15 failed, 8 passed**, plus
  `core/tests/domain/test_estimated_time_minutes.py` not collecting
  (`ImportError: cannot import name 'InvalidEstimatedTime'`). The eight wire
  rejection cases each failed `Failed: DID NOT RAISE MalformedRequest`.
- frontend -> **Tests 6 failed | 4 passed (10)**.
- `uv run mypy .` -> **14 errors**, every one an `estimated_time`
  `str | None` mismatch.

**Second run (2026-09-23, with the range):**

- `cd backend && uv run pytest core/tests/domain/test_ai_prompt_estimated_time.py lambda_ai/tests/test_estimated_time_legacy_read.py -q`
  -> **5 failed, 2 passed** (no v3 prompt version; `tiempo` read back as a
  string).
- `core/tests/domain/test_estimated_time_minutes.py` and
  `lambda_api/tests/test_estimated_time_wire.py` do not collect:
  `ImportError: cannot import name 'MAX_ESTIMATED_MINUTES' from
  'planner_core.domain.recipe'` — the range constant this issue introduces.
- `cd frontend && npx vitest run tests/components/RecipeAuthoringForm.estimatedTime.test.jsx`
  -> **3 failed | 1 passed**: `expected 'text' to be 'number'`,
  `expected null to be '0'` (the `min`/`max` assertion fails on the first
  missing bound), `expected 'tiempo estimado' to contain 'minutos'`.

**Green-after check (2026-09-23).** Because two modules now fail at import, a
red run alone would not prove the assertions are right. The three `src/` trees
were copied to a scratch directory outside the repo, the minimal fix applied
there (range constant + parser + error row + message + `decode_recipe` +
both `_meal` readers + AI validation + prompt v3), and the staged suites run
against it with `PYTHONPATH` pointing at the copy: **54 passed**. The repository
was not touched; `git status --porcelain` is unchanged.

- `ruff format --check`, `ruff check`, `eslint` and `prettier --check` on the
  seven staged files: clean.
