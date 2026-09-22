# empty-field-error-messages — analysis

## Defect, one sentence

No decoder on the recipe/shopping write path distinguishes *"this field is
empty"* from *"this value is wrong"*, so the wire boundary hands an empty field
to the value parser and the user is told the failure that parser knows about —
or nothing at all, or a 500.

## Reproduction

Backend, at the pair the handler runs for every authoring request (`decode_*`
then `build_problem_response`), 2026-09-22:

```
$ cd backend && uv run python -c "...decode_recipe / decode_shopping_item..."
empty unit               422 UNKNOWN_UNIT                 La unidad indicada no está permitida.
empty name               ACCEPTED
empty category           422 UNKNOWN_INGREDIENT_CATEGORY  La categoría de ingrediente indicada no está permitida.
empty ingredient name    ACCEPTED
blank quantity           500 INTERNAL_ERROR               Se ha producido un error inesperado. Inténtalo de nuevo más tarde.
null quantity            500 INTERNAL_ERROR               Se ha producido un error inesperado. Inténtalo de nuevo más tarde.
blank tool               ACCEPTED
blank step               ACCEPTED
shopping empty unit      422 UNKNOWN_UNIT                 La unidad indicada no está permitida.
```

The first line is the report, verbatim. Expected in every line: `422` with
`El campo <Campo> no puede estar vacío.`

The text the user sees is the API's: `apiFetch` copies `detail` into `ApiError`
(`frontend/src/api/client.js:44-49`), `useLibrary.js:16` surfaces it verbatim,
`LibraryView.jsx:108-118` renders it. No frontend string is involved, and no
frontend guard exists to stop the request.

Staged tests run the same nine cases through `decode_* + build_problem_response`
— see `plan.md`, "Red result at triage".

## Root cause

One missing distinction, three failure modes, all at
`backend/lambda_api/src/planner_api/serialization.py`:

| `file:line` | Field | What happens to an empty value |
|---|---|---|
| `:117` `decode_ingredient` | `unit` | `parse_unit("")` -> `UnknownUnit` -> the reported message. `units.py:40-47` is a membership test; `""` is simply not a member. |
| `:140` `decode_recipe` | `category` | `parse_category("")` -> `UnknownIngredientCategory`, same shape. |
| `:116` `decode_ingredient` | `quantity` | `float("")` / `float(None)` raises `ValueError`/`TypeError` — **not** a `PlannerError`, so `errors.py:121-124` falls through to the generic `500` and logs a traceback. Violates `docs/architecture.md` §4 invariant 12 ("errors are explicit"). |
| `:136` `decode_recipe` | `name` | `str(require_field(...))` — `require_field` (`:68`) only checks **presence**, so `""` is stored. |
| `:138-139` `decode_recipe` | `tools`, `procedure` entries | `str(t)` per entry; a blank row is stored. |
| `:181-183` `decode_shopping_item` | `name`, `unit` | Same two, same results. |

The parsers are not at fault: `parse_unit` and `parse_category` answer the
question they are asked ("is this one of the allowed values?"). The defect is
that nobody asks the prior question.

Requirement basis. `docs/gaps_and_resolutions.md` Part H, negative space,
rejects *field-level validation minutiae* as **requirement** material and
points at `FR-UX-03` for the messaging — "es-ES validation messaging is already
required (`FR-UX-03`)" — which presupposes the validation exists. `FR-UX-03`
covers "**all** texts — including validation, error, and system messages"; a
message that reports a value check the user never triggered is not the
validation message for an empty field, and `INTERNAL_ERROR` is not one either.
Accepting the empty value is the worse half: `FR-LIB-03` requires a library
recipe to store a name, ingredients, tools and procedure, and an unnamed recipe
also defeats name search (`FR-LIB-04`) and the duplicate-name warning
(`FR-CAND-06`). For the shopping item, `FR-SHOP-01`/`FR-SHOP-02` require every
item to show a name and quantity.

## Blast radius

Every write that reaches these two decoders shares the cause, so fixing them
covers all of it:

| Path | Decoder | Affected fields |
|---|---|---|
| `POST`/`PUT /v1/library/recipes` (`routing.py:356`, `:407`) | `decode_recipe` | name, category, ingredient name/quantity/unit, tool, step |
| `POST` candidate, manual source (`routing.py:523`) | `decode_recipe` | same |
| AI-preview accept (`routing.py:365`) | `decode_recipe` | same — server-side content, so it should never trip |
| `POST`/`PUT /v1/shopping-list/items` | `decode_shopping_item` | name, unit (`quantity` is issue 7's bound) |

Not affected: `decode_rule` (every field is an id or an enum chosen from a
dropdown, and `InvalidRuleId`/`InvalidWeekday` already name them), account
creation (`username`/`temporaryPassword` have their own policies), and the AI
output validator (`ai_output.py`, machine-generated content).

Scope boundaries with the siblings on this form — none of these is duplicated
here:

- **Issue 7** (`negative-ingredient-quantity`) owns the *value* rule for
  `quantity` (`> 0`) and the frontend submit block. This issue owns only the
  *empty* case, and only the API message. The two fixes meet in
  `decode_ingredient`; neither replaces the other.
- **Issue 8** (`recipe-saved-without-required-sections`) owns an **empty
  list** (no ingredient rows at all). This issue owns a **row present but
  blank**.
- **Issue 4** (`servings-and-time-inputs-not-numeric`) owns `servings` and
  `estimatedTime`, which are *not* required fields — freeform and purely
  informational (`G-85`). They are deliberately outside this issue's rule.

## Classification

`defect`. The empty-unit message contradicts `FR-UX-03`'s requirement that
validation messages be the es-ES text for the failure that occurred; the empty
`name`/tool/step cases store content `FR-LIB-03` says a recipe must have; and
the blank-quantity `500` violates `docs/architecture.md` §4 invariant 12. The
bound itself is implementation detail delegated by Part H, not an invented
requirement — the same reading already accepted for issue 7.

Severity as reported: `medium`. Not amended, though the blank-quantity `500` is
the part that deserves attention first.
