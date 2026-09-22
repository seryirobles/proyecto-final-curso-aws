# analysis — servings-and-time-inputs-not-numeric (issue 4)

## Defect, one sentence

The from-scratch recipe form renders *Comensales* as a free-text input and
submits whatever was typed verbatim, so `servings` reaches the API as a
**string** — `""` when the field is left blank — instead of the integer the
contract and `numeroComensales` are typed for.

The report has a second half — *Tiempo estimado* should step numerically and be
labelled "in minutes". That half is **not a defect**: see *Classification*.

## Reproduction

**Servings wire type (backend chain, confirmed):**

```
cd backend && uv run python -c "
from planner_api.serialization import decode_recipe
from planner_api.adapters.dynamo import _meal
body = {'name':'Lentejas','category':'legume','servings':'','estimatedTime':'',
        'ingredients':[],'tools':[],'procedure':[]}   # what the blank form posts
r = decode_recipe(body)
attrs = _meal.content_attrs(name=r.name, ingredients=r.ingredients, tools=r.tools,
        procedure=r.procedure, category=r.category, servings=r.servings,
        estimated_time=r.estimated_time)
print(repr(attrs['numeroComensales'])); print(_meal.read_servings(attrs))"
```

Observed:

```
decoded servings = '' str
stored numeroComensales = ''
read_servings -> InvalidOperation [<class 'decimal.ConversionSyntax'>]
```

Expected: `servings` decodes to `None`, `numeroComensales` is absent/null, and
the item reads back. **A recipe saved with Comensales left empty cannot be read
again** — `read_servings` raises, i.e. every later `GET` of that library recipe
or week meal 500s.

With a number typed in, the same path stores `numeroComensales` as the string
`"4"`. `read_servings` survives that one (`Decimal("4")` parses), so the visible
damage is limited to a DynamoDB attribute typed `S` where `data_model.md` models
a count, plus the contract violation.

Run again at triage on 2026-09-22; output above is verbatim.

**UI half (staged tests, run at triage):** `RecipeAuthoringForm.servings.test.jsx`
-> `expected 'text' to be 'number'`; `useRecipeAuthoring.servings.test.js` ->
`expected '4' to be 4`, `expected '' to be null`, `expected '2' to be 2`.
Counts in `plan.md`, "Red result at triage". The staged copies were deleted
after each run; `frontend/` and `backend/` are unchanged.

## Root cause

1. `frontend/src/components/RecipeAuthoringForm.jsx:141` — the *Comensales*
   input is `type="text"`. No numeric keyboard, no stepper (the reported
   symptom), and nothing keeps the value numeric.
2. `frontend/src/hooks/useRecipeAuthoring.js:53` — `buildManualRecipe` passes
   `servings: form.servings` through unconverted, while the line just below it
   (`quantity: Number(ingredient.quantity)`) does convert. **This is the line
   that is wrong**: `rest_api_contract.md` §3.1 types the field
   `"servings": 4`, `planner_core.domain.recipe.Recipe.servings` is
   `int | None`, and `docs/data_model.md` §1 models `numeroComensales` as a
   count on `DatosPlatoBiblioteca`/`DatosPlatoSemana`. Violates **FR-LIB-03**
   ("a library recipe shall store … **number of servings**") for both authoring
   targets (**FR-CAND-03**, **FR-LIB-02**).
3. `backend/lambda_api/src/planner_api/serialization.py:141` —
   `servings=payload.get("servings")` is the only field in `decode_recipe`
   with no wire-type parse (`name` gets `str()`, `quantity` gets `float()`,
   `category`/`unit` get a parser). So the bad client value is *persisted*
   rather than rejected, which is what turns a client bug into an unreadable
   stored item. Contract §4 makes a body that does not match the documented
   shape a `400`, never a write.

The symptom the user sees (a text box without steppers) surfaces at (1); the
data damage originates at (2) and is let through at (3).

## Blast radius

- **Library authoring and editing** — `useLibrary.js:53` ->
  `useRecipeAuthoring`; both `POST /v1/library/recipes` and
  `PUT /v1/library/recipes/{id}` carry the string. Editing is the nastier path:
  `recipeToForm` stringifies a correctly stored integer, and the save downgrades
  it — so a recipe the AI wrote with `servings: 4` becomes `"4"` after the first
  human edit.
- **Candidate authoring** — `useWeekPlanner.js:61` holds an `authoringTarget`
  but no view renders `RecipeAuthoringForm` for it yet (that is **issue 3**,
  "Añadir plato does nothing"). The same hook serves it, so the defect arrives
  with the wiring unless fixed here.
- **AI generation** — unaffected: `planner_ai/adapters/bedrock.py:92` already
  does `int(payload["servings"])`.
- **Two live tests encode the buggy payload** and will turn red when the fix
  lands — they must be corrected, not the fix:
  `frontend/tests/hooks/useRecipeAuthoring.test.js:55` (`servings: '4'`, in a
  test that claims to assert "the exact manual body shape
  (rest_api_contract.md 3.1)") and
  `frontend/tests/hooks/useLibrary.test.js:187` (`servings: '2'`).
  `useLibrary.test.js:162` asserts *form state* `'2'` and stays valid — the
  controlled input keeps a string; only the built body changes.
- **Sibling issues on this form** (cross-reference, not duplicated here):
  **5** empty-field error messages, **7** negative ingredient quantity, **8**
  saving without ingredients/tools/procedure, **9** the *Cerrar* button style.
  Issue 7 owns value-range policing; this issue therefore adds **no `min`/`max`**
  to the servings control (see E4).

## Classification

**`defect`** for the servings half — the code violates `FR-LIB-03`
(+ `FR-CAND-03`, `FR-LIB-02`) as instantiated by `rest_api_contract.md` §3.1
and `docs/data_model.md` §1.

**`not_a_defect` for the *Tiempo estimado* half.** `FR-LIB-03`, as amended by
**G-85** (Part U) and **G-86** (Part V), states: "*Time and servings are set the
same way (manually or by AI) but are **freeform** and purely informational — no
validation, no dropdown constraint, no downstream logic*". The contract's own
example is the string `"45 min"` (§3.1), the domain type is
`estimated_time: str | None`, and G-85 records explicitly that `tiempo` "has no
`FR-*` or gap backing anywhere". So:

- a numeric stepper for *Tiempo estimado* would change its wire type from string
  to number and contradict `str | None`;
- "measured in minutes" fixes a **unit convention** that no requirement states —
  adopting it is a `spec_gap` needing a fresh human lift of the frozen docs (a
  new lettered Part amending `FR-LIB-03`), not a bug fix.

The staged tests therefore **lock the current free-text behaviour** of that
field (E5, E7), so the implementer cannot "fix" it in passing. If the human
wants minutes, that is a requirements lift plus a new triage.

**Severity:** reported `low`; the servings half reads **medium** — a blank
optional field silently produces a stored item that cannot be read back. Left as
reported in `issue_list.json` per that file's `severity` rule.
