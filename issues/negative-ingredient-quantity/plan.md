# negative-ingredient-quantity — plan

## Expected behaviour

- **E1** — When a request body carries an ingredient whose `quantity` is not
  strictly greater than zero, the API **shall** reject the request with `422`
  and a `detail` taken from `planner_core.messages`.
  *Implements:* FR-SHOP-06, FR-SHOP-01, FR-LIB-03, FR-UX-03.
- **E2** — When AI output carries an ingredient whose quantity is not strictly
  greater than zero, `validate_ai_recipe_output` **shall** raise a named domain
  exception instead of returning a `Recipe`.
  *Implements:* FR-AI-04, FR-LIB-03, FR-SHOP-06.
- **E3** — When `validate_and_preview` receives such output, it **shall** return
  `GenerationFailure(INVALID_OUTPUT)` instead of propagating the exception.
  *Implements:* FR-AI-12 (G-48, G-66).
- **E4** — While an ingredient row of the authoring form holds a quantity that is
  not strictly greater than zero, the form **shall not** submit the recipe.
  *Implements:* FR-LIB-03, FR-CAND-03, FR-SHOP-06.
- **E5** — While an ingredient row's quantity field holds a non-blank value that
  is not strictly greater than zero, the form **shall** display the es-ES
  message `MESSAGES.RECIPE_AUTHORING_INVALID_QUANTITY` for that row.
  *Implements:* FR-UX-03, FR-LIB-03, FR-CAND-03.
- **E6** — While the authoring form is shown, the ingredient-quantity control
  **shall** be a numeric control whose minimum is zero, so its stepper never
  produces a negative value. *Implements:* FR-UX-02, FR-LIB-03.

The strictly-positive bound (not merely non-negative) is the triage ruling
recorded in `analysis.md`, "Triage ruling on zero"; the requirements delegate the
bound itself to implementation (`docs/gaps_and_resolutions.md` Part H).

E5 and E6 were added on 2026-09-22 on the owner's ruling: *"strictly positive,
with control in UI to warn the user if a quantity is 0 or negative. Avoid 1
up/1 down button controls to go below 0."* E1–E4 are unchanged — nothing in the
ruling contradicts them; it adds the user-facing half that this plan previously
left to issue 5.

## Fix design

Ingredient quantity gains the validating entry point its sibling field `unit`
already has, at the same two places that resolve `unit`, plus the form. Layers
per `docs/architecture.md` section 3: domain rule in `core/domain`, wire mapping
in `lambda_api`, form state in the frontend hook.

| File | Layer | Change |
|---|---|---|
| `backend/core/src/planner_core/domain/recipe.py` | core/domain | Add `InvalidIngredientQuantity(PlannerError)` carrying the rejected value, and `parse_quantity(value: float) -> float` beside `Ingredient`, mirroring `parse_unit` / `parse_category` (one entry point, exact rule, no coercion). |
| `backend/core/src/planner_core/messages.py` | core | Add one es-ES constant, e.g. `INVALID_INGREDIENT_QUANTITY = "La cantidad del ingrediente debe ser mayor que cero."` (FR-UX-03). |
| `backend/core/src/planner_core/domain/ai_output.py` | core/domain | `validate_ai_recipe_output` resolves the quantity through `parse_quantity` (E2); `validate_and_preview` adds the new exception to its `except` tuple (E3). |
| `backend/lambda_api/src/planner_api/serialization.py` | lambda_api | `decode_ingredient` resolves the quantity through `parse_quantity` (E1). |
| `backend/lambda_api/src/planner_api/errors.py` | lambda_api | One `_TABLE` row: `422`, code `INVALID_INGREDIENT_QUANTITY`, the new message. |
| `docs/rest_api_contract.md` section 4 | doc | One row in the exception/status table, beside `UnknownUnit`. |
| `frontend/src/hooks/useRecipeAuthoring.js` | frontend hook | `canSubmit` for the `scratch` method requires every ingredient row to satisfy `Number(quantity) > 0` (E4). |
| `frontend/src/messages/es-ES.js` | frontend messages | One constant, `RECIPE_AUTHORING_INVALID_QUANTITY`, with the same text as the backend's `INVALID_INGREDIENT_QUANTITY` — the two message modules are parallel by design (`docs/conventions.md`, *Castilian Spanish*). |
| `frontend/src/components/RecipeAuthoringForm.jsx` | frontend component | `min="0"` on the quantity input (E6), and inside each ingredient row an element rendering `MESSAGES.RECIPE_AUTHORING_INVALID_QUANTITY` while `ingredient.quantity !== '' && Number(ingredient.quantity) <= 0` (E5). No `role`, no `aria-*` — `frontend/tests/test_no_extra_accessibility.test.js` (R22) forbids them in `src/**/*.jsx`. |

**Do not** put the check in `Ingredient.__post_init__` — see the rejected
alternatives. **Do not** touch `ShoppingItem`: same class of hole, different
entry point, and outside this report (`analysis.md`, "Blast radius").

### Who owns which message on this field

Issue 5 (`empty-field-error-messages`, `pending`) owns the **empty**-field
message: a quantity box the user never filled in reads *"El campo Cantidad no
puede estar vacío."*, and that stays entirely issue 5's — which is why E5's
rule excludes the blank value and why the staged test asserts no warning for
`''`. This issue owns the **invalid-value** message for the same field: a
non-blank `0` or negative quantity. The two never fire together, and neither
fix needs the other to land first.

### The stepper cannot go below zero

The quantity control is already a native `<input type="number">`
(`RecipeAuthoringForm.jsx:171-177`); adding `min="0"` is what stops the
browser's own up/down stepper from producing a negative value, which is the
owner's "avoid 1 up/1 down button controls to go below 0". Nothing in this
repository replaces it with a custom stepper — issue 4
(`servings-and-time-inputs-not-numeric`) makes *Comensales* a native
`type="number"` and leaves the ingredient rows untouched. If a custom stepper
is ever introduced for this field, the same clamp-at-zero obligation (E6)
carries over to it: the staged test asserts the control's numeric type and its
minimum, not a particular widget. `0` itself remains reachable by typing, and
is caught by E4 and E5.

### Rejected alternatives

1. **Validate in `Ingredient.__post_init__`.** One line, closes every path at
   once — including the DynamoDB read decoders (`adapters/dynamo/_meal.py`). A
   recipe already stored with a negative quantity would then raise on *read*,
   turning a bad row into a 500 on the library view, and the bug has been
   reachable in the running dev environment. It also contradicts the documented
   design that `Ingredient` takes already-resolved fields.
2. **Clamp the value to zero, or to its absolute value, at the boundary.**
   Rejected by `docs/architecture.md` section 4, invariants 2 and 12: it
   silently rewrites what the user typed and reports no failure.
3. **Frontend-only guard.** The API is the contract boundary and also accepts AI
   output; a client-side rule leaves `POST /v1/library/recipes` open.

## Test plan

Staged files and their destinations (moved verbatim):

| Staged | Destination |
|---|---|
| `issues/negative-ingredient-quantity/tests/backend/core/tests/domain/test_ingredient_quantity.py` | `backend/core/tests/domain/test_ingredient_quantity.py` |
| `issues/negative-ingredient-quantity/tests/backend/lambda_api/tests/test_ingredient_quantity_rejected.py` | `backend/lambda_api/tests/test_ingredient_quantity_rejected.py` |
| `issues/negative-ingredient-quantity/tests/frontend/tests/hooks/useRecipeAuthoring.quantity.test.js` | `frontend/tests/hooks/useRecipeAuthoring.quantity.test.js` |
| `issues/negative-ingredient-quantity/tests/frontend/tests/components/RecipeAuthoringForm.quantity.test.jsx` | `frontend/tests/components/RecipeAuthoringForm.quantity.test.jsx` |

| Expected behaviour | Test |
|---|---|
| E1 | `test_decode_recipe_rejects_a_non_positive_ingredient_quantity` (reproduction), `test_the_rejection_reaches_the_client_as_422_with_an_es_es_message` |
| E2 | `test_ai_output_validation_rejects_a_non_positive_quantity` |
| E3 | `test_a_non_positive_quantity_surfaces_as_a_generation_failure` |
| E4 | `does not submit the form with quantity %s` (reproduction) |
| E5 | `warns in es-ES while the quantity is %s` (reproduction, 3 cases), `shows no warning for a positive quantity`, `shows no warning while the quantity field is empty - issue 5 owns that message` |
| E6 | `bounds the quantity stepper at zero, so it never steps negative` |
| regression | `test_decode_recipe_accepts_a_positive_ingredient_quantity`, `test_ai_output_validation_accepts_a_positive_quantity`, `test_a_positive_quantity_still_previews`, `test_aggregation_of_positive_quantities_is_unchanged`, `submits the form with a positive quantity` |

The tests name no exception class of their own: they assert `PlannerError`, the
`422` status and an es-ES detail drawn from the messages module, so they
constrain the behaviour and not the shape of the fix.

### Red result at triage (2026-09-21)

Staged files copied to their destinations, run, then deleted; the live tree was
left as found.

Backend, `uv run pytest` on the two staged modules from `backend/`:
**9 failed, 4 passed.**

- Red, for the reason in `analysis.md` — every rejection test reports
  `Failed: DID NOT RAISE PlannerError` (E1, E2), and the two `GenerationFailure`
  cases fail because `validate_and_preview` returns `GenerationSuccess` (E3).
- Green already, as this plan expects: the four positive-quantity regressions.

Frontend, `npx vitest run tests/hooks/useRecipeAuthoring.quantity.test.js` from
`frontend/`: **3 failed, 1 passed.**

- Red: all three non-positive cases fail at
  `expect(result.current.canSubmit).toBe(false)` — `canSubmit` is `true` and
  `onSubmit` fires (E4).
- Green already: `submits the form with a positive quantity`.

### Red result for E5 and E6 (2026-09-22)

`npx vitest run tests/components/RecipeAuthoringForm.quantity.test.jsx` from
`frontend/`: **6 failed (6)**. Copied, run, deleted; the live tree was left as
found.

- E5, five cases: `expected 'undefined' to be 'string'` — the whole warning
  mechanism is absent, starting with `MESSAGES.RECIPE_AUTHORING_INVALID_QUANTITY`,
  which the test requires before it queries the DOM. Once the constant exists
  the three non-positive cases still fail on `toHaveLength(1)` until the
  element is rendered, so they constrain the behaviour, not the constant.
- E6: `expected null to be '0'` — the quantity input carries no `min`
  (`RecipeAuthoringForm.jsx:171-177`), so the native stepper walks below zero.

`frontend/tests/components/RecipeAuthoringForm.test.jsx` renders its ingredient
row with `quantity: '300'`, so the new warning does not appear there and that
suite stays green.
