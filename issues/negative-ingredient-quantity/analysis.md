# negative-ingredient-quantity — analysis

## Defect, one sentence

No entry point between the recipe form and storage constrains an ingredient
quantity or a servings count (*Comensales*), so a zero or negative value of
either is accepted and persisted — and a negative ingredient quantity is later
**subtracted** from what the shopping list says the week requires.

The servings half was added on 2026-09-23 (owner, via the leader); its
requirements lift, `G-91` (Part AA), landed the same day — see "Scope
extension: servings" below.
Everything above that section is the original ingredient-quantity triage,
unchanged.

## Reproduction

Backend, wire boundary (the path every manual recipe write takes):

```
$ cd backend && uv run python -c "
import sys; sys.path.insert(0, 'lambda_api/src')
from planner_api import serialization as ser
print(ser.decode_recipe({'name':'X','category':'legume',
  'ingredients':[{'name':'lentejas','quantity':-500,'unit':'g'}],
  'tools':['olla'],'procedure':['a']}).ingredients)"
(Ingredient(name='lentejas', quantity=-500.0, unit=<Unit.GRAM: 'g'>),)
```

Observed: accepted. Expected: rejected as a domain-rule violation (422,
`docs/rest_api_contract.md` section 4), the way `unit` already is.

AI path, same result:

```
validate_ai_recipe_output(RawRecipeOutput(..., RawIngredient('a', -3, 'g')))
-> Ingredient(name='a', quantity=-3, unit=Unit.GRAM)     # accepted
```

Consequence in the shopping list (`planner_core.domain.shopping`):

```
aggregate_ingredients(arroz 500 g, Arroz -200 g)  ->  (arroz, 300.0, g)
outstanding_amounts((), (arroz -200 g))           ->  ()        # item vanishes
```

Frontend: `useRecipeAuthoring.canSubmit` is `true` for the `scratch` method
regardless of the form's contents, so `submit()` posts `quantity: -300`
verbatim; the quantity `<input type="number">` carries no `min`.
Confirmed red by the staged tests — see `plan.md`, "Red result at triage".

## Root cause

Ingredient quantity has **no validating entry point**, where the sibling field
`unit` has one. The cause is distributed over the three places that admit an
ingredient from outside:

| `file:line` | What is missing |
|---|---|
| `backend/lambda_api/src/planner_api/serialization.py:113-118` | `decode_ingredient` resolves `unit` through `parse_unit` but takes `quantity` through a bare `float(...)` — no check. This is the wire entry for every manual recipe write (`routing.py:356`, `:407`, `:523`) and for accepting an AI preview (`routing.py:365`). |
| `backend/core/src/planner_core/domain/ai_output.py:48-51` | `validate_ai_recipe_output` resolves the unit and the category, carries `item.quantity` through untouched. |
| `frontend/src/hooks/useRecipeAuthoring.js:146-150` | `canSubmit` returns `true` unconditionally for `scratch`; `RecipeAuthoringForm.jsx:171-177` renders the number input with no `min`. |

`Ingredient` itself (`backend/core/src/planner_core/domain/recipe.py:11-22`) is
**not** the cause: its docstring records the deliberate design that the caller
resolves a field before constructing (`parse_unit`, "design.md section 6,
rejected alternative B"). The missing caller-side check is the defect.

## Requirement basis (read this before the go/no-go)

There is **no `FR-*` stating a quantity bound**, and that is deliberate:
`docs/gaps_and_resolutions.md` Part H, negative space, line 551 —

> **Field-level validation minutiae** (name lengths, **quantity bounds**, item
> ordering within shopping sections) — implementation details below requirement
> granularity; es-ES validation messaging is already required (FR-UX-03).

That entry rejects quantity bounds as *requirement* material, not as
*behaviour*: it delegates the bound to implementation and points at `FR-UX-03`
for the message, which only makes sense if the validation exists. So this is
**not** a `spec_gap` — a human lift would have to contradict Part H. What the
requirements do fix is the arithmetic the value feeds:

- `FR-SHOP-06`: re-sync "computes the **outstanding** quantity — the amount
  **required by the in-scope definitive meals** minus the amount already carried
  by checked items". A negative ingredient cancels part of another meal's
  requirement (500 - 200 = 300 g above) or removes the line entirely, so the
  list no longer states the amount required. Same for `FR-SHOP-01`'s displayed
  quantity and `FR-SHOP-03`'s per-name+unit aggregation.
- `FR-LIB-03`: a library recipe stores "ingredients **with quantities**".
- `FR-UX-03`: the rejection text must be es-ES, from the messages module.

**Triage ruling on zero — confirmed by the owner, 2026-09-22:** *"strictly
positive, with control in UI to warn the user if a quantity is 0 or negative.
Avoid 1 up/1 down button controls to go below 0."* The second half added `E5`
(an inline es-ES warning on the field) and `E6` (the numeric control's minimum
is zero) to `plan.md`; `E1`–`E4` are unchanged. The report says
"negative"; the staged tests require **strictly positive**. Two reasons: an
ingredient contributing `0` states nothing about what the dish needs
(`FR-LIB-03`) and nothing about what to buy (`FR-SHOP-06` already discards a
zero-or-less outstanding amount); and `buildManualRecipe` casts with
`Number(ingredient.quantity)`, so an **empty** quantity box becomes `0` — a
`>= 0` rule would leave that hole open under a different symptom. Narrowing the
rule to `< 0` only would need the staged tests re-cut, i.e. a new triage.

## Blast radius

Every construction site of `Ingredient` was checked:

| Site | Status under the planned fix |
|---|---|
| `serialization.py:113` `decode_ingredient` | **Fixed** — covers library create/update, candidate create/update, AI-preview accept. |
| `ai_output.py:49` `validate_ai_recipe_output` | **Fixed** — and its failure must arrive as a `GenerationFailure`, not a raise (below). |
| `shopping.py:63` `aggregate_ingredients` | Sums validated inputs; positive in, positive out. Regression-tested, unchanged. |
| `shopping.py:182` `outstanding_amounts` | Already emits only `> 0`. Regression-tested, unchanged. |
| `lambda_api/adapters/dynamo/_meal.py:49`, `lambda_ai/adapters/dynamo/_meal.py:49` | **Read** path, deliberately left permissive: a recipe already stored with a negative quantity (this bug has been reachable in the running dev environment) must stay readable and editable, not 500 the library view. This is why the fix goes at the entry points and **not** in `Ingredient.__post_init__` — see `plan.md`, "Rejected alternatives". |
| `lambda_ai/adapters/bedrock.py:82` `RawIngredient` | Raw provider parse; validation is `validate_ai_recipe_output`'s job, already covered. |

Second path sharing the cause: `validate_and_preview` (`ai_output.py:124-130`)
catches only `UnknownUnit` and `UnknownIngredientCategory`, so a new quantity
exception would propagate out of a function whose contract is "surface the
result as a value, never a propagated raise" (G-48, `FR-AI-12`). Covered by
`E3`.

Adjacent but **out of scope**: `ShoppingItem.quantity`
(`serialization.py:177-184`, `shopping.py:87-99`) is equally unconstrained — a
manual `-1 g` shopping item is accepted. Different type, different entry point,
and outside this report ("Unidad in ingredientes"). Recorded here so it is not
lost; it needs its own report.

## Scope extension: servings (2026-09-23)

### Reproduction

```
decode_recipe({... 'servings': -4})          -> Recipe(..., servings=-4)   # accepted
decode_recipe({... 'servings': 0})           -> Recipe(..., servings=0)    # accepted
validate_ai_recipe_output(RawRecipeOutput(..., servings=0))  -> servings=0 # accepted
```

Frontend: the *Comensales* input (`RecipeAuthoringForm.jsx:140-147`) is
`type="number" step="1"` with no `min`, so its stepper walks below zero, and
`canSubmit` is `true` for `scratch` regardless of the form. Confirmed red by
the staged servings tests — `plan.md`, "Red result for E7–E12".

### `parse_servings` does not validate the value

`serialization.py:167-175` checks the **JSON type only** (`int` or `null`,
`bool` excluded -> `MalformedRequest`, 400) and returns any integer unchanged.
That is by design: issue 4 built it to exactly what `FR-LIB-03` allows.

### Root cause

Same shape as the ingredient half — no value check at the entry points — but
here the absence is **required by the frozen text**, not an oversight:

| `file:line` | What is missing |
|---|---|
| `backend/lambda_api/src/planner_api/serialization.py:167-175` | `parse_servings` accepts any integer. It is the only servings entry for manual library create/update (`routing.py:530`), manual candidate create/update (`routing.py:356`, `:413`) and single-recipe AI-preview accept (`routing.py:365`, which re-decodes the stored preview through `decode_recipe`). |
| `backend/core/src/planner_core/domain/ai_output.py:65` | `validate_ai_recipe_output` carries `raw.servings` through untouched (its docstring cites G-85). This is the only check on the **whole-week** AI path (`application/week_generation.py:101` -> `validate_and_preview`), which never passes `decode_recipe`. |
| `frontend/src/components/RecipeAuthoringForm.jsx:140-147`, `frontend/src/hooks/useRecipeAuthoring.js` `canSubmit` | No `min`, no warning, no submit guard. |

### Requirement basis — `G-91` (Part AA), landed 2026-09-23

**No longer a `spec_gap`.** `G-91` amends `G-85`/`FR-LIB-03` (and `FR-AI-13`):
"`servings` becomes a strictly positive integer (`>= 1`) or absent/`null`",
enforced "at the write boundary and in AI-output validation, not as a
domain-level invariant", with a UI control whose "minimum is 0 and shows an
inline warning if the user reaches 0 or a negative value". The staged `E7`–`E12`
tests assume exactly this (reject `-4`/`-1`/`0`; accept `1`, `4`, absent;
`min="0"`; es-ES warning; `Recipe` constructor left permissive) — no re-cut.
Live `RecipeAuthoringForm.servings.test.jsx` (`no min or max`, G-85) is now
superseded by `G-91` and is replaced per `plan.md`.

Before the lift, the frozen requirement **forbade** the bound (kept for the
record):

- `FR-LIB-03`: "Servings ... remain freeform and purely informational — **no
  validation beyond a numeric wire type**, no dropdown constraint, no
  downstream logic (G-85)."
- `G-85`: both fields purely informational, "**no validation**".
- `G-90` (Part Z) lifted this for `tiempo` only and says so: "Scoping the
  reopening to `tiempo` alone, leaving servings' already-implemented
  numeric-but-unbounded shape untouched, avoids re-litigating a decision
  (servings) nobody asked to reopen." `rest_api_contract.md` section 3,
  item 8 repeats it: "`servings` is a freeform integer (`G-85`)".
- Part H's "quantity bounds are implementation minutiae" — the argument the
  ingredient half rests on — does **not** carry over: for servings a
  requirement states the opposite explicitly.
- Live tests lock the current behaviour: `RecipeAuthoringForm.servings.test.jsx`
  `bounds Comensales with no min or max (E4, G-85 - no validation)`.

That lift is `G-91`, as proposed. Nothing in `docs/data_model.md` bounds
`numeroComensales` either way.

### Blast radius — servings

| Site | Status under the planned fix |
|---|---|
| `serialization.py:167` `parse_servings` | **Fixed** (E7) — covers library create/update, candidate create/update, AI-preview accept. Wrong JSON type stays 400; a well-formed non-positive integer becomes 422, the same split `parse_estimated_time` uses. |
| `ai_output.py:65` `validate_ai_recipe_output` | **Fixed** (E8), and `validate_and_preview` must catch the new exception (E9, G-48) — otherwise one bad AI servings count raises out of whole-week generation. |
| `lambda_ai/adapters/bedrock.py:92` | Raw `int(...)` parse; validation is `validate_ai_recipe_output`'s job. |
| `adapters/dynamo/_meal.py:72` `read_servings` (both lambdas) | **Read** path, left permissive — a stored `numeroComensales` of 0 or less must stay readable and editable. Same reasoning as G-89/G-90 and the ingredient half. |
| `Recipe`/`MealSnapshot` constructors | Unchanged: `test_recipe.py::test_recipe_accepts_any_servings_and_estimated_time_value` (servings `-3`, `0`) stays green by design. |
| `test_no_recipe_metadata_logic.py` | Unaffected if the check lives in `recipe.py` / `ai_output.py` (fully exempt) and `lambda_api` (not scanned). A check anywhere else in `planner_core` fails that guard. |

## Classification

`defect` — the code admits a value that breaks `FR-SHOP-06`'s and
`FR-SHOP-01`'s meaning of a required quantity and `FR-LIB-03`'s "ingredients
with quantities". The bound itself is an implementation detail delegated by
Part H, not an invented requirement; the zero ruling above is the only part the
human needs to confirm.

Severity as reported: `medium`. Not amended — it corrupts the shopping list
silently, but only when someone types a negative number.
