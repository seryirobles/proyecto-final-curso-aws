# recipe-saved-without-required-sections — analysis

## Defect, one sentence

A recipe with zero ingredients, zero utensilios and zero pasos is accepted by
the form, by the API and by the domain, which `FR-LIB-03` as amended by `G-89`
now forbids — at triage no requirement said so, and the lift recorded in
`docs/gaps_and_resolutions.md` Part Y supplied it.

## Reproduction

Confirmed at the wire boundary, 2026-09-22:

```
$ cd backend && uv run python -c "
from planner_api.serialization import decode_recipe
print(decode_recipe({'name':'Tortilla','category':'eggs',
                     'ingredients':[],'tools':[],'procedure':[]}))"
Recipe(name='Tortilla', ingredients=(), tools=(), procedure=(), category=<IngredientCategory.EGGS: 'eggs'>, servings=None, estimated_time=None)
```

The client side agrees: `useRecipeAuthoring.js:146-150` returns
`canSubmit === true` for the `scratch` method regardless of the form's
contents — with the comment `// no client validation - FR-LIB-03, G-85` — so
*Guardar receta* is enabled on a form where the three sections are empty.
Nothing rejects the write anywhere along the chain.

Observed and expected agree with the report: the recipe is saved. What is
missing is the requirement that says it should not be.

## Root cause

There is no defective line. Three places would each have to **gain** a rule
that does not exist today:

| `file:line` | Today |
|---|---|
| `frontend/src/hooks/useRecipeAuthoring.js:146-150` | `canSubmit` is unconditional for `scratch`. |
| `backend/lambda_api/src/planner_api/serialization.py:137-139` | `decode_recipe` maps `payload.get("ingredients", ())` and the two lists through, empty or not. |
| `backend/core/src/planner_core/domain/recipe.py:26-40` | `Recipe` holds plain tuples with no cardinality rule. |

`FR-LIB-03` says a library recipe "shall **store**: name, ingredients with
quantities, tools, procedure, exactly one ingredient category … and an
estimated preparation/cook time and number of servings". It enumerates the
fields a recipe carries; it states **no minimum count** for any of the three
lists, and `docs/gaps_and_resolutions.md` has no entry on the subject — neither
allowing empty lists nor forbidding them. Part H's negative space delegates
*field-level validation minutiae* ("name lengths, quantity bounds, item
ordering") to implementation; the **cardinality of a recipe's sections** is not
one of those, and is not mentioned anywhere.

The question has already been asked and answered once, in an approved spec —
`specs/recipe_model/design.md` §8, rejected alternative **G**:

> **G. Enforce a non-empty `ingredients` tuple, or a non-blank `name`.**
> Rejected as invention — no `FR-*` in this feature's `covers` array says a
> recipe must have at least one ingredient or a non-blank name. `docs/specs.md`
> forbids inventing a requirement no `FR-*` covers; if this is ever wanted, it
> is a finding for a future spec, not a default to assume now.

So the current behaviour is a **deliberate consequence of a documented
decision**, taken for want of a requirement. Reversing it is the human's call,
not an implementer's.

The *utensilios* half needs that call explicitly: requiring at least one tool
is a product judgement (an ensalada or a plate of fruit plausibly needs none),
not an implementation detail. The same applies, less obviously, to a
ready-to-eat dish with no elaboración.

## What the fix would cost, once the requirement exists

Recorded before the lift so the human could price it; `plan.md` now carries the
design and the staged tests, and follows all three points below:

- One rule, expressed once at the wire boundary
  (`serialization.decode_recipe`), mapped to `422` with es-ES messages from
  `planner_core.messages`, plus `canSubmit` in `useRecipeAuthoring`. Roughly
  the shape of issue 5's fix, and it lands cleanly on top of it.
- **Not** in `Recipe.__post_init__`: recipes already saved empty in the running
  dev environment must stay readable, the same reasoning as issue 7's rejected
  alternative 1.
- Tests: an empty-section rejection per section at the wire, the `canSubmit`
  block, plus regressions that a fully filled recipe still saves. All staged
  after the lift — see `plan.md` § *Test plan*.

## Blast radius

If the rule is adopted it reaches every recipe-writing path — library
create/edit, manual candidate create (once issue 3 wires it), and the
AI-preview accept — because all three decode through `decode_recipe`. The AI
path additionally needs a ruling: `validate_ai_recipe_output`
(`backend/core/src/planner_core/domain/ai_output.py:44-51`) accepts empty lists
too, and a model that returns an empty `utensilios` would have to surface as
`GenerationFailure(INVALID_OUTPUT)` (`G-48`, `FR-AI-12`) rather than a raise.

Sibling issues on the same form, cross-referenced not duplicated: **5**
(`empty-field-error-messages`) owns a row that exists but is blank — a
different case, already classified `defect` because Part H names *name lengths*
among the minutiae it delegates; **7** owns the quantity bound; **4** owns
`servings`/`estimatedTime`.

## Classification

`defect` (2026-09-22, after the lift). Triage first classified this `spec_gap`
-> **blocked**: no `FR-*` or `G-xx` backed the rule, and
`specs/recipe_model/design.md` §8 alternative **G** had declined it as
invention. The owner then lifted the frozen docs — `docs/gaps_and_resolutions.md`
**Part Y, G-89** — and the requirement now exists:

- `FR-LIB-03` (amended by `G-89`): "**The ingredients, tools and procedure
  lists shall each contain at least one item; a write with any of the three
  empty is rejected**", in every authoring flow, enforced at the write boundary
  with an es-ES message (`FR-UX-03`). **Utensilios is included** — the open
  question this analysis raised is closed by the owner's ruling.
- `FR-AI-12` (amended by `G-89`): AI output with any of the three lists empty
  surfaces as the existing per-slot failure (`G-66`), never persisted, never a
  raise.

So the three places named under *Root cause* now each violate a frozen
requirement, and the two constraints this analysis recorded survive into the
plan unchanged: the rule goes at the wire boundary (never
`Recipe.__post_init__`, which `G-89`'s *Reasoning* adopts explicitly so already
stored empty recipes stay readable), and the AI path returns a
`GenerationFailure`.

Severity as reported: `medium`. Not amended.

## Scope extension (2026-09-23)

**Gap, one sentence:** with a section empty, *Guardar receta* is disabled and
nothing on screen says why.

E6 required only that the form not submit. The landed fix satisfies it
silently: `useRecipeAuthoring.js:160-174` returns `canSubmit === false`, and
`RecipeAuthoringForm.jsx:261` renders `disabled={!canSubmit}` with no message.
The sibling rules on the same form do explain themselves — servings and
ingredient quantity (issue `negative-ingredient-quantity`, E5/E11) render an
inline `tokens.color.honey` `<span>` beside the field
(`RecipeAuthoringForm.jsx:149-155`, `:191-196`), text from `es-ES.js`. The
owner reported the empty-section case as still broken; `FR-UX-03` (errors and
validation messages in Castilian Spanish) and `FR-LIB-03` as amended by `G-89`
("rejected … with an es-ES message") cover it. No new requirement.

**Trigger.** Those warnings keep no touched or submit-attempted state: each is a
pure function of the current form value, shown whenever the value is invalid.
E8 follows the same rule, so a section warns whenever it is empty — including
on a freshly opened scratch form, where the three warnings are exactly the
explanation for the disabled button. A touched/attempted flag would be a new
state mechanism on this form; not proposed.

**Blast radius.** `ScratchFields` is shared by the library add/edit flow and
the week view's candidate flow (`CandidateAuthoring.jsx`), so one change covers
both. The library-pick and AI-stub methods do not render these sections.
