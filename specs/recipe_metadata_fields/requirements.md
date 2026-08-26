# recipe_metadata_fields — Requirements

> Feature 25 · tier 1 · `sdd: true`
> Covers: `FR-LIB-03`, `FR-MENU-04`, `FR-AI-13` (amended by `G-85`, then
> re-amended by `G-86`, `docs/gaps_and_resolutions.md` Parts U and V)
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen
> requirement ids it implements and is verifiable by at least one concrete
> test that asserts a value.

## Purpose in one sentence

Give `Recipe`/`MealSnapshot` the two per-recipe, purely informational fields
`docs/data_model.md` §1 has always modelled (`numeroComensales` → `servings`,
`tiempo` → `estimated_time`), thread them unchanged through every place a
`Recipe` is built or copied, replace `CONFIGURED_SERVINGS`'s deployment-config
target with an instruction telling the model to state both values itself
(`G-86`), and remove `CONFIGURED_SERVINGS` outright.

## One `SHALL` per requirement

Every `R<n>` below carries exactly one `SHALL` (or one `SHALL NOT`), counted
mechanically rather than by eye, per the checklist in `AGENTS.md` /
`docs/specs.md`. Where a requirement needed both a positive claim and a
prohibition (e.g. "copy the value through" and "raise nothing when absent"),
they are two separate `R<n>`s.

## Scope note — what this feature owns of each id it cites

`FR-CAND-07` (`MealSnapshot`'s shape) is not in this feature's `covers`
array — it belongs to `recipe_model`, feature 4, already closed. This spec
still extends `MealSnapshot`, under the explicit mandate `G-85` gives: *"Both
`numeroComensales` ... and `tiempo` ... become per-recipe attributes, stored
on `Recipe`/`MealSnapshot` like any other content field."* Every `R<n>` about
`MealSnapshot` below cites `FR-LIB-03` (the id `G-85` amended to add the
fields), not `FR-CAND-07`, following the same "consume an existing id without
claiming it" pattern `ai_output_validation`'s `requirements.md` used for
`FR-LIB-03` itself (feature 12, consumed but not owned there either).

| Requirement | Owned **here** | Consumed, not owned |
|---|---|---|
| `FR-LIB-03` | The two new fields on `Recipe`, their copy-through on `MealSnapshot`/`snapshot()`/`to_library_entry()`, and the absence of any validation on either. | `Recipe`'s pre-existing shape (`name`, `ingredients`, `tools`, `procedure`, `category`) — `recipe_model`, feature 4. `MealSnapshot`'s status as a distinct, decoupled type — also feature 4 (`FR-CAND-07`). `to_library_entry`'s duplicate-warning behaviour and `Candidate`'s own shape — `week_plan_model`, feature 5. |
| `FR-MENU-04` | That `servings`/`estimated_time` live on the same value object a detail view already renders `ingredients`/`tools`/`procedure` from, so no second lookup is needed. | The detail view itself, and the click-to-open navigation — feature 20 (`frontend_spa`), still `blocked`. |
| `FR-AI-13` | `RawRecipeOutput`'s two new optional fields, their no-raise-on-absence and copy-through behaviour; the removal of `CONFIGURED_SERVINGS` and the `servings` field from `PromptInstructions`/`PromptInstructionsVersion`; and the new `recipe_metadata_instruction` wording instructing the model to state both values itself (`G-86`, corrects `G-85`). | Actually invoking an AI provider or defining its response schema — feature 17 (`ai_lambda`), still `blocked` on `P4`. `ConfigPort` and prompt-version selection themselves — `ai_prompt_versioning`, feature 24, already closed; this feature narrows what a version's wording contains, it does not touch `ConfigPort`. |
| `FR-AI-14` | Nothing new claimed. `recipe_metadata_instruction` is added as one more field of the existing, already-versioned `PromptInstructionsVersion` (feature 24's append-only registry) — it reuses that shape, it does not add new versioning machinery. | The versioning mechanism itself: `ConfigPort`, `resolve_active_prompt_version`, the append-only-registry discipline, `UnknownPromptVersion` — all `ai_prompt_versioning`, feature 24, already closed. |

---

## R1
Implements: FR-LIB-03

The system SHALL declare `Recipe` with an optional `servings: int | None`
field, defaulting to `None`.

## R2
Implements: FR-LIB-03

The system SHALL declare `Recipe` with an optional `estimated_time: str |
None` field, defaulting to `None`.

## R3
Implements: FR-LIB-03

The system SHALL declare `MealSnapshot` with an optional `servings: int |
None` field, defaulting to `None`.

## R4
Implements: FR-LIB-03

The system SHALL declare `MealSnapshot` with an optional `estimated_time:
str | None` field, defaulting to `None`.

## R5
Implements: FR-LIB-03

WHEN `snapshot(recipe)` is called, the resulting `MealSnapshot`'s `servings`
field SHALL equal `recipe.servings`.

## R6
Implements: FR-LIB-03

WHEN `snapshot(recipe)` is called, the resulting `MealSnapshot`'s
`estimated_time` field SHALL equal `recipe.estimated_time`.

## R7
Implements: FR-LIB-03

The system SHALL accept any integer value for `Recipe.servings` and
`MealSnapshot.servings`, including zero or negative, applying no validation.

## R8
Implements: FR-LIB-03

The system SHALL accept any string value for `Recipe.estimated_time` and
`MealSnapshot.estimated_time`, applying no format validation.

## R9
Implements: FR-MENU-04

The system SHALL expose `servings` and `estimated_time` as fields of the
same `Recipe`/`MealSnapshot` value that already carries `name`,
`ingredients`, `tools`, `procedure` and `category`, so one object supplies a
detail view's entire content.

## R10
Implements: FR-AI-13

The system SHALL declare `RawRecipeOutput` with an optional `servings: int |
None` field, defaulting to `None`.

## R11
Implements: FR-AI-13

The system SHALL declare `RawRecipeOutput` with an optional
`estimated_time: str | None` field, defaulting to `None`.

## R12
Implements: FR-AI-13

IF `RawRecipeOutput.servings` is `None`, THEN `validate_ai_recipe_output`
SHALL NOT raise on that account.

## R13
Implements: FR-AI-13

IF `RawRecipeOutput.estimated_time` is `None`, THEN
`validate_ai_recipe_output` SHALL NOT raise on that account.

## R14
Implements: FR-AI-13, FR-LIB-03

`validate_ai_recipe_output(raw)`'s result's `servings` field SHALL equal
`raw.servings`.

## R15
Implements: FR-AI-13, FR-LIB-03

`validate_ai_recipe_output(raw)`'s result's `estimated_time` field SHALL
equal `raw.estimated_time`.

## R16
Implements: FR-LIB-03

WHEN `to_library_entry(meal, existing_names)` builds a `Recipe` from `meal`,
the result's `servings` field SHALL equal `meal.servings`.

## R17
Implements: FR-LIB-03

WHEN `to_library_entry(meal, existing_names)` builds a `Recipe` from `meal`,
the result's `estimated_time` field SHALL equal `meal.estimated_time`.

## R18
Implements: FR-AI-13

The system SHALL NOT declare, anywhere in `planner_core`, a module-level
constant representing one deployment-wide servings target.

## R19
Implements: FR-AI-13

The system SHALL NOT declare a `servings` field on `PromptInstructions`.

## R20
Implements: FR-AI-13

The system SHALL NOT declare a `servings` field on
`PromptInstructionsVersion`.

## R21
Implements: FR-LIB-03

The system SHALL confine every source-code reference to the `servings`
field name, within `backend/core/src/planner_core`, to `domain/recipe.py`,
`domain/ai_output.py`, and the one sanctioned line of `domain/candidate.py`
that copies it from a `MealSnapshot` into a `Recipe`.

## R22
Implements: FR-LIB-03

The system SHALL confine every source-code reference to the
`estimated_time` field name, within `backend/core/src/planner_core`, to
`domain/recipe.py`, `domain/ai_output.py`, and the one sanctioned line of
`domain/candidate.py` that copies it from a `MealSnapshot` into a `Recipe`.

## R23
Implements: FR-AI-13, FR-AI-14

The system SHALL declare `PromptInstructionsVersion` with a
`recipe_metadata_instruction: str` field, versioned alongside
`output_language` and `healthy_balanced_instruction` (`G-86`).

## R24
Implements: FR-AI-13

The system SHALL declare `PromptInstructions` with a
`recipe_metadata_instruction: str` field.

## R25
Implements: FR-AI-13

`build_instructions(version_id)`'s result's `recipe_metadata_instruction`
field SHALL equal `resolve_prompt_version(version_id).recipe_metadata_instruction`.

---

## Coverage map

| Frozen requirement | Covered by |
|---|---|
| `FR-LIB-03` | R1–R9, R14–R17, R21, R22 |
| `FR-MENU-04` | R9 |
| `FR-AI-13` | R10–R15, R18–R20, R23–R25 |
| `FR-AI-14` (consumed, not in `covers`) | R23 |

| `feature_list.json` acceptance criterion | Covered by |
|---|---|
| `Recipe` and `MealSnapshot` carry an optional servings count and an optional estimated prep/cook time (`FR-LIB-03`) | R1–R4 |
| Both fields are freeform — no validation, no dropdown constraint, no format enforcement | R7, R8 |
| Both fields can be set in every recipe-authoring flow, manually or by AI generation, with no cross-recipe consistency requirement (`FR-AI-13`, `G-85`, corrected by `G-86`) | R1–R4 (manual, any constructor call), R10, R11, R14, R15 (AI-generated, via `RawRecipeOutput` → `validate_ai_recipe_output`), R16, R17 (library-save flow), R23–R25 (the model is now actually *instructed* to attempt both fields, rather than left to volunteer them unprompted) — no requirement anywhere compares one recipe's values against another's |
| Neither field is read by shopping-list aggregation or any other domain logic — proven by a mechanical scan, mirroring `test_no_ambient_time.py`'s technique (`G-85`) | R21, R22 |
| The detail-view content model includes both fields alongside ingredients, tools and procedure (`FR-MENU-04`) | R9 |
| AI output validation accepts the fields as optional and freeform, with no new failure mode when either is absent | R10–R15 |
| The AI prompt builder's `CONFIGURED_SERVINGS` deployment-config constant (feature 11) is removed; no code path still treats servings as global config | R18, R19, R20. R18 is enforced structurally (no top-level `int` constant of any name in `ai_prompt.py`, `test_no_recipe_metadata_logic.py`'s `test_ai_prompt_declares_no_top_level_int_constant`), not by matching the literal name `CONFIGURED_SERVINGS` alone — a rename cannot defeat it (reviewer finding, feature 25). R21 is a **separate** claim: it confines the *per-recipe field name* `servings` to its three sanctioned sites; it says nothing about a differently-named deployment-config constant, so it does not by itself rule one out. R23–R25 add a differently-named, differently-shaped field (an instruction string, not a target value) — they do not reopen R18–R20's prohibition. |

Supporting requirements not demanded by a single acceptance bullet but
required by the invariants those bullets rest on: R5, R6 (the copy-through
`snapshot()` must perform for R1–R4's fields to survive a recipe entering a
week, mirroring `FR-CAND-07`'s existing "snapshot, don't reference"
discipline for every other field); R16, R17 (the same copy-through
`to_library_entry()` must perform, or saving a candidate back to the library
would silently drop both fields the moment they exist on `MealSnapshot`);
R25 (the equality claim `build_specification_prompt`/`build_reference_prompt`/
`build_category_prompt`'s existing, unmodified `instructions=build_instructions(version_id)`
assertions transitively depend on to carry `recipe_metadata_instruction`
into all three prompt modes).
