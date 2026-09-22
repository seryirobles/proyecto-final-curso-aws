# servings-and-time-inputs-not-numeric — plan

## Expected behaviour

### E1
Implements: `FR-LIB-03`, `FR-LIB-02`, `FR-CAND-03`

WHEN the from-scratch authoring form is submitted with a value in *Comensales*,
the system SHALL send `servings` as a JSON integer.

### E2
Implements: `FR-LIB-03`

WHEN the from-scratch authoring form is submitted with *Comensales* left empty,
the system SHALL send `servings` as `null`.

### E3
Implements: `FR-LIB-03`, `FR-UX-02`

WHILE the from-scratch authoring form is shown, the form SHALL render
*Comensales* as a numeric control stepping by one.

### E4
Implements: `FR-LIB-03` (as amended by `G-85`)

WHILE the from-scratch authoring form is shown, the *Comensales* control SHALL
carry no minimum and no maximum.

### E5
Implements: `FR-LIB-03` (as amended by `G-85`)

WHILE the from-scratch authoring form is shown, the form SHALL render *Tiempo
estimado* as a free-text control.

### E6
Implements: `FR-LIB-03`

WHEN a recipe write carries a `servings` value that is not an integer and not
`null`, the API SHALL reject the request as malformed.

### E7
Implements: `FR-LIB-03` (as amended by `G-85`), `FR-AI-13`

WHEN a recipe write carries `estimatedTime`, the API SHALL store the client's
string unchanged.

E4, E5 and E7 exist to *hold the line*: they state what `G-85` already decided
and must pass before and after the fix. The report's "tiempo estimado in
minutes" is deliberately **not** an `E<n>` — see `analysis.md`,
*Classification*.

## Fix design

Layers per `docs/architecture.md` §3: the form control in the component, the
wire mapping in the hook, the wire-type parse at the `lambda_api` boundary.
No `core` change: `Recipe.servings` stays `int | None` and stays permissive
about the *value* (`G-85`), which is what
`backend/core/tests/domain/test_recipe.py:63` asserts — that test must stay
green.

| File | Layer | Change |
|---|---|---|
| `frontend/src/components/RecipeAuthoringForm.jsx` | component | *Comensales* input `type="number"` with `step="1"`; no `min`, no `max`. Leave *Tiempo estimado* as `type="text"`. |
| `frontend/src/hooks/useRecipeAuthoring.js` | hook | In `buildManualRecipe`, map `servings` to `null` when the field is blank and to an integer otherwise — the same transport cast the line below already applies to `quantity`. `estimatedTime` keeps passing through untouched. |
| `backend/lambda_api/src/planner_api/serialization.py` | lambda_api | `decode_recipe` parses `servings` like every other field: integer or `null`, anything else `MalformedRequest` (400, `docs/rest_api_contract.md` §4). `bool` is not an integer here. |

Two **live** frontend tests assert the buggy payload and will go red; they are
not staged tests, and the implementer corrects them to the contract shape
rather than weakening the fix:
`frontend/tests/hooks/useRecipeAuthoring.test.js:55` (`servings: '4'`) and
`frontend/tests/hooks/useLibrary.test.js:187` (`servings: '2'`).
`useLibrary.test.js:162` asserts *form state* and stays as it is — the
controlled input still holds a string.

No new dependency. No message string added. No change to `docs/`.

### Rejected alternatives

**Coerce on the backend (`int(payload["servings"])`) instead of rejecting.**
One line, and it would absorb any client. Rejected because it makes `"4"` and
`4` the same request, which `docs/rest_api_contract.md` §4 splits into
malformed-vs-accepted, and because it would hide the client defect this issue
exists to remove — `int("")` still raises, just later and as a 500.

**Fix only the frontend.** The SPA is the only writer today, so the string
would stop arriving. Rejected because the API is the contract boundary: the
blank-field payload currently persists a `numeroComensales` that
`read_servings` cannot parse, and nothing but the boundary check stops the next
client from doing it again.

## Test plan

| Staged | Destination |
|---|---|
| `issues/servings-and-time-inputs-not-numeric/tests/frontend/tests/hooks/useRecipeAuthoring.servings.test.js` | `frontend/tests/hooks/useRecipeAuthoring.servings.test.js` |
| `issues/servings-and-time-inputs-not-numeric/tests/frontend/tests/components/RecipeAuthoringForm.servings.test.jsx` | `frontend/tests/components/RecipeAuthoringForm.servings.test.jsx` |
| `issues/servings-and-time-inputs-not-numeric/tests/backend/lambda_api/tests/test_serialization_servings.py` | `backend/lambda_api/tests/test_serialization_servings.py` |

| `E<n>` | Test | At triage |
|---|---|---|
| E1 | `sends servings as a number, not the raw input string`; `re-sends an edited recipe servings as a number, not a string` | **RED** — `expected '4' to be 4`, `expected '2' to be 2` |
| E2 | `sends servings as null when the field is left empty` | **RED** — `expected '' to be null` |
| E3 | `renders Comensales as a numeric control stepping by one` (reproduction of the reported symptom) | **RED** — `expected 'text' to be 'number'` |
| E4 | `bounds Comensales with no min or max` | GREEN, must stay green |
| E5 | `keeps Tiempo estimado a free-text control`; `accepts a free-text Tiempo estimado value carrying its own unit` | GREEN, must stay green |
| E6 | `test_decode_recipe_rejects_an_empty_string_servings`; `test_decode_recipe_rejects_a_servings_that_is_not_an_integer[…]` | **RED** — `DID NOT RAISE MalformedRequest`, 6 cases |
| E7 | `test_decode_recipe_keeps_estimated_time_as_the_clients_free_text` | GREEN, must stay green |
| regression | `test_decode_recipe_keeps_an_integer_servings`, `…reads_an_absent_servings_as_none`, `…reads_a_null_servings_as_none`, `keeps Comensales a controlled field reporting its value` | GREEN, must stay green |

### Red result at triage (2026-09-22)

Copied to the destinations, run, deleted; the live tree was left as found
(`git status --porcelain` clean apart from `issue_list.json` and `issues/`).

- `frontend`: `npx vitest run tests/hooks/useRecipeAuthoring.servings.test.js
  tests/components/RecipeAuthoringForm.servings.test.jsx` -> **4 failed | 6
  passed (10)**. Every failure is the string-vs-number/text-vs-number mismatch
  of `analysis.md`; the six passes are the `G-85` lock and the controlled-input
  cases.
- `backend`: `uv run pytest lambda_api/tests/test_serialization_servings.py -q`
  -> **6 failed, 5 passed**, all six `Failed: DID NOT RAISE MalformedRequest`.

Suites the fix must leave green (beyond the two live tests it must correct):
`frontend/tests/components/RecipeAuthoringForm.test.jsx`,
`frontend/tests/hooks/useRecipeAuthoring.test.js`,
`backend/core/tests/domain/test_recipe.py`,
`backend/lambda_api/tests/test_serialization.py`.
