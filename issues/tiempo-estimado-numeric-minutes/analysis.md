# tiempo-estimado-numeric-minutes — analysis

## Defect, one sentence

`tiempo` / `estimatedTime` is still the freeform string `G-85` specified — a
free-text form control, a `str | None` domain field, an unvalidated wire value
and a prompt asking the model for free text — while `G-90` now requires an
integer count of minutes from 0 to 6000 inclusive.

## Reproduction

Not a fault to reproduce: the shipped behaviour is correct under the superseded
resolution and wrong under the new one. The current shape is visible directly —
`decode_recipe({... "estimatedTime": "45 min"}).estimated_time` returns the
string `'45 min'` unchanged (`backend/lambda_api/src/planner_api/serialization.py:186`),
and `frontend/src/components/RecipeAuthoringForm.jsx:149-157` renders *Tiempo
estimado* as `type="text"`. Both are locked by live tests this fix must invert —
see `plan.md` § *Live tests this fix supersedes*.

## Root cause

The decision, not a bug. `G-85` (Part U, 2026-08-26) made servings and
prep/cook time *freeform, purely informational* metadata; every layer
implemented exactly that:

| Layer | Site | Today |
|---|---|---|
| domain | `core/.../domain/recipe.py:39,57` | `estimated_time: str \| None` on `Recipe` and `MealSnapshot` |
| domain | `core/.../domain/ai_output.py:38,59` | `RawRecipeOutput.estimated_time: str \| None`, copied through unvalidated |
| domain | `core/.../domain/ai_prompt.py:23-31,36-41,63-73` | v1/v2 ask the model for `estimated_time (str|null)` |
| lambda_api | `serialization.py:186` | `estimated_time=payload.get("estimatedTime")` — no parse, unlike `parse_servings` right above it |
| lambda_ai | `adapters/bedrock.py:93-95` | `str(payload["estimated_time"])` |
| both | `adapters/dynamo/_meal.py:24,29,76-78` | `tiempo` written and read as `str \| None` |
| frontend | `RecipeAuthoringForm.jsx:149-157`, `useRecipeAuthoring.js:48,54` | free-text input, value passed through verbatim |
| doc | `docs/rest_api_contract.md:207,225` | "freeform and purely informational (`G-85`)", `"estimatedTime": "45 min"` |

`G-90` (Part Z) amends `G-85`, `FR-LIB-03` and `FR-AI-13` for this one field:
an integer number of minutes from **0 to 6000 inclusive** or absent/`null`,
still optional, still no downstream logic, with a value outside the range
"rejected the same way an empty required field is". Servings is explicitly
*not* reopened (`G-90`: issue 4's `parse_servings` stands untouched).

## Blast radius

- **Every recipe-authoring path** shares this field: library recipes, week
  candidates, AI previews. There is one `Recipe` type and one `decode_recipe`,
  so the change is narrow in code and wide in reach.
- **AI generation** needs both halves: the prompt must ask for an integer
  (`FR-AI-13` as amended) and the validator must refuse a string, surfacing it
  through the existing per-slot `INVALID_OUTPUT` failure (`FR-AI-12`, `G-66`) —
  never a raise. The prompt-version registry is append-only (`FR-AI-14`,
  `G-84`), so the wording lands as **v3**; *which* version is active is
  deployment configuration (`AI_PROMPT_VERSION_ID`), human-owned, not this fix.
- **Already-persisted data.** The dev environment holds `tiempo` strings
  written under `G-85`. `G-90` makes backward compatibility the implementer's
  design call and rules out a constructor invariant that would raise on read —
  see `plan.md` § *Fix design*, decision and rejected alternative 1.
- **Live tests.** Obsolete cases in three suites deliberately lock the
  free-text behaviour (issue 4's approved work), and mypy `strict` covers the
  test tree, so every `estimated_time="45 min"` fixture becomes a type error.
  All of them are enumerated in `plan.md` § *Live tests this fix supersedes*;
  none may be silently worked around.
- **Not affected:** `numeroComensales`/`servings` (unchanged by `G-90`), the
  shopping list (no aggregation reads either field — the scan
  `backend/core/tests/test_no_recipe_metadata_logic.py` proves it and must stay
  green), and the `tiempo` attribute name itself (`docs/data_model.md` §1/§4.2
  names the attribute, never its type).

## Owner rulings (2026-09-23) and the one design read left

Both open questions from the first pass are now settled in the frozen docs, and
`plan.md` / `tasks.md` / the staged tests follow them:

1. **The range is 0 to 6000 inclusive** — not the unbounded "non-negative" the
   first pass read into `G-90`. Out of range is rejected the way an empty
   required field is. `E1`, `E3` and the new `E8` carry it; the control gets
   `min="0"` **and** `max="6000"`.
2. **The label names the unit**, confirmed as proposed:
   `RECIPE_AUTHORING_ESTIMATED_TIME_LABEL` (authoring form) and
   `RECIPE_DETAIL_ESTIMATED_TIME` (recipe detail) both become *Tiempo estimado
   (minutos)* — `E4`, tasks `T9`/`T10`.

The one reading still worth a glance at the gate: **which rejection is which.**
`docs/rest_api_contract.md` §4 splits *400 = malformed* from *422 = well-formed
but refused by a domain rule*, so `"45 min"` (wrong JSON type) is a 400 like a
bad `servings`, while `7000` (a well-formed integer outside the range) is a 422
carrying the new es-ES `INVALID_ESTIMATED_TIME` message — the empty-field shape
`G-90` points at. See `plan.md` § *Why two rejection shapes*.

`docs/requirements.md`'s `FR-LIB-03` and `FR-AI-13` rows now carry the amended
`G-90` wording (owner, 2026-09-23); the earlier note about that drift no longer
applies.

## Classification

`defect` — design-authorized. The built code contradicts `FR-LIB-03` and
`FR-AI-13` **as amended by `G-90`**, an owner ruling already recorded in the
frozen docs, so this is not a `spec_gap`: the requirement exists and the code
does not meet it. The design itself (domain type, backward compatibility,
prompt version) still wants the human's eye at the go/no-go gate.

Severity: reported **low**; confirmed low — the field is informational and
nothing downstream reads it. Breadth, not urgency, is what makes it work.
