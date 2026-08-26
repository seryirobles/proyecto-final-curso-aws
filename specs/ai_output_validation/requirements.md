# ai_output_validation — Requirements

> Feature 12 · tier 1 · `sdd: true`
> Covers: `FR-AI-10`, `FR-AI-12`, `FR-LIB-05`
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen
> requirement ids it implements and is verifiable by at least one concrete
> test that asserts a value.

## Purpose in one sentence

Validate an already-parsed, provider-agnostic AI recipe response against the
`Recipe` schema and the fixed unit vocabulary (`FR-LIB-05`, `G-48`), and model
the single-recipe preview lifecycle — accept / discard / regenerate, nothing
persisted until accepted (`FR-AI-10`) — and the per-slot success/failure
result shape whole-week generation surfaces (`FR-AI-12`), including the named
"insufficient library recipes" failure (`G-66`).

## One `SHALL` per requirement

Every `R<n>` below carries exactly one `SHALL` (or one `SHALL raise` /
`SHALL NOT`), counted mechanically rather than by eye, per the checklist in
`AGENTS.md` / `docs/specs.md`.

## Scope note — what this feature owns of each id it cites

Several `Implements:` lines below cite an id outside this feature's own
`covers` array. That mirrors the precedent `ai_prompt_builder` (feature 11)
set for `FR-LIB-05` itself: a feature may **consume** an already-frozen
requirement's text without owning it, provided the owning feature is named.

| Requirement | Owned **here** | Consumed, not owned |
|---|---|---|
| `FR-LIB-05` | Resolving each AI-output ingredient's unit string against `Unit` via `parse_unit`, and rejecting (not silently accepting) a code outside it. | The unit vocabulary itself — owned by `text_and_units`, feature 3. |
| `FR-LIB-03` | Cited on `R2`, `R5`–`R9`: `validate_ai_recipe_output` resolves the AI output's category string via `parse_category` and carries `name`/`ingredients`/`tools`/`procedure`/`category` through unchanged into the `Recipe` it builds — the same "AI output instructed and validated to use that same fixed set" clause `FR-LIB-03` states for category, applied here exactly as `ai_prompt_builder` applied `FR-LIB-05` to units without owning it. `Recipe`'s shape itself is owned by `recipe_model`, feature 4 (closed); `IngredientCategory`/`parse_category` by `rules_model`, feature 6 (closed). This feature adds no field to `Recipe`. |
| `FR-AI-10` | The preview lifecycle types and functions (`RecipePreview`, `new_preview`, `accept_preview`, `discard_preview`) and the "surfaced as a value, not raised" wrapping `validate_and_preview` provides. | Actually invoking the AI provider, and re-building a prompt for a regeneration (`ai_prompt_builder`'s existing `build_specification_prompt`/`build_reference_prompt`, feature 11) — both **feature 17** (`ai_lambda`). Persisting an accepted preview as a `Candidate` or library `Recipe` — the existing `new_candidate`/`to_library_entry` functions (features 5, 4, both closed). The preview UI itself — feature 20. |
| `FR-AI-12` | The per-slot result shape (`SlotGenerationResult`, `GenerationSuccess`, `GenerationFailure`, `GenerationFailureReason`) and the es-ES message each failure reason carries. | The progress/loading state shown while a call is in flight (no domain representation — feature 20/17, see `design.md` §1). Detecting *that* a slot lacks a suitable library recipe (library search — feature 17). Retrying a slot (reuses `generation_request`'s existing idempotency machinery, feature 10, closed — see `design.md` §5). |
| `FR-UX-03` | Cited on `R17`: every failure message this feature returns is a constant from `planner_core.messages`, never an inline string. | The messages module itself — established convention, `docs/conventions.md`. |
| `FR-AI-09` | Cited on `R21`: `SlotGenerationResult`'s "each entry unaffected by any other" property is this feature's restatement, at the result-type level, of `FR-AI-09`'s "per-slot results shall be written independently and the failure of one shall not abort the others." | Actually running per-slot tasks concurrently and writing results without lost updates — feature 17 (`ai_lambda`); owned by `generation_request`'s concurrency story in general (feature 10, closed), not this feature. |

---

## R1
Implements: FR-LIB-05

The system SHALL declare `RawIngredient` as `@dataclass(frozen=True)` in
`planner_core.domain.ai_output` with fields exactly `name: str`,
`quantity: float` and `unit: str`.

## R2
Implements: FR-LIB-05, FR-LIB-03

The system SHALL declare `RawRecipeOutput` as `@dataclass(frozen=True)` in
`planner_core.domain.ai_output` with fields exactly `name: str`,
`ingredients: tuple[RawIngredient, ...]`, `tools: tuple[str, ...]`,
`procedure: tuple[str, ...]` and `category: str`.

## R3
Implements: FR-LIB-05

`validate_ai_recipe_output(raw)`'s result's `ingredients` field SHALL contain,
for each `RawIngredient` in `raw.ingredients` in order, an `Ingredient` whose
`unit` equals `parse_unit` of that `RawIngredient`'s `unit`.

## R4
Implements: FR-LIB-05

IF any `RawIngredient` in `raw.ingredients` carries a `unit` that does not
resolve via `parse_unit`, THEN `validate_ai_recipe_output(raw)` SHALL raise
`UnknownUnit` (reused from `planner_core.domain.units`, never redeclared).

## R5
Implements: FR-LIB-03

`validate_ai_recipe_output(raw)`'s result's `category` field SHALL equal
`parse_category(raw.category)`.

## R6
Implements: FR-LIB-03

IF `raw.category` does not resolve via `parse_category`, THEN
`validate_ai_recipe_output(raw)` SHALL raise `UnknownIngredientCategory`
(reused from `planner_core.domain.ingredient_category`, never redeclared).

## R7
Implements: FR-LIB-03

`validate_ai_recipe_output(raw)`'s result's `name` field SHALL equal
`raw.name`.

## R8
Implements: FR-LIB-03

`validate_ai_recipe_output(raw)`'s result's `tools` field SHALL equal
`raw.tools`.

## R9
Implements: FR-LIB-03

`validate_ai_recipe_output(raw)`'s result's `procedure` field SHALL equal
`raw.procedure`.

## R10
Implements: FR-AI-10

The system SHALL declare `RecipePreview` as `@dataclass(frozen=True)` in
`planner_core.domain.ai_output` with a field exactly `recipe: Recipe` (no
per-user quota, count or usage field — `G-70`).

## R11
Implements: FR-AI-10

`new_preview(recipe)`'s result's `recipe` field SHALL equal `recipe`.

## R12
Implements: FR-AI-10

`accept_preview(preview)` SHALL return `preview.recipe`.

## R13
Implements: FR-AI-10

`discard_preview(preview)` SHALL return `None`.

## R14
Implements: FR-AI-12

The system SHALL declare `GenerationFailureReason` as a `StrEnum` in
`planner_core.domain.ai_output` with exactly the members `INVALID_OUTPUT`,
`INSUFFICIENT_LIBRARY_RECIPES` and `GENERATION_UNAVAILABLE`.

## R15
Implements: FR-AI-12

The system SHALL declare `GenerationFailure` as `@dataclass(frozen=True)` in
`planner_core.domain.ai_output` with fields exactly
`reason: GenerationFailureReason` and `message: str`.

## R16
Implements: FR-AI-12

The system SHALL declare `GenerationSuccess` as `@dataclass(frozen=True)` in
`planner_core.domain.ai_output` with a field exactly `preview: RecipePreview`.

## R17
Implements: FR-AI-12, FR-UX-03

`build_generation_failure(reason)`'s result's `message` field SHALL equal the
`planner_core.messages` constant this table maps `reason` to:

| `reason` | message constant |
|---|---|
| `INVALID_OUTPUT` | `AI_GENERATION_INVALID_OUTPUT` |
| `INSUFFICIENT_LIBRARY_RECIPES` | `AI_GENERATION_INSUFFICIENT_LIBRARY_RECIPES` |
| `GENERATION_UNAVAILABLE` | `AI_GENERATION_UNAVAILABLE` |

## R18
Implements: FR-AI-10

WHEN `validate_ai_recipe_output(raw)` succeeds, `validate_and_preview(raw)`
SHALL return `GenerationSuccess(preview=new_preview(<that result>))`.

## R19
Implements: FR-AI-10, FR-AI-12

IF `validate_ai_recipe_output(raw)` raises `UnknownUnit` or
`UnknownIngredientCategory`, THEN `validate_and_preview(raw)` SHALL return
`build_generation_failure(GenerationFailureReason.INVALID_OUTPUT)`.

## R20
Implements: FR-AI-12

The system SHALL declare `SlotGenerationResult` as `@dataclass(frozen=True)`
in `planner_core.domain.ai_output` with fields exactly `slot: SlotRef` and
`outcome: GenerationSuccess | GenerationFailure`.

## R21
Implements: FR-AI-12, FR-AI-09

WHILE a whole-week generation run's results are assembled as a collection of
`SlotGenerationResult` values, the system SHALL preserve each entry's own
`slot` and `outcome` unaffected by any other entry in the same collection.

---

## Coverage map

| Frozen requirement | Covered by |
|---|---|
| `FR-AI-10` | R10, R11, R12, R13, R18, R19 |
| `FR-AI-12` | R14, R15, R16, R17, R19, R20, R21 |
| `FR-LIB-05` | R1, R2, R3, R4 |
| `FR-LIB-03` (consumed, not in `covers`) | R2, R5, R6, R7, R8, R9 |
| `FR-UX-03` (consumed, not in `covers`) | R17 |
| `FR-AI-09` (consumed, not in `covers`) | R21 |

| `feature_list.json` acceptance criterion | Covered by |
|---|---|
| Output failing the recipe schema or using a unit outside the fixed list is rejected, not silently accepted (`G-48`) | R3, R4, R5, R6 (rejection is `raise`, never a silently-degraded `Recipe`); R18, R19 (the failure is surfaced as a value, never swallowed) |
| Single-recipe generation produces a preview that can be accepted, discarded or regenerated; nothing persists until accepted (`FR-AI-10`, `G-17`) | R10–R13, R18 (regeneration is `design.md` §5's "call `validate_and_preview` again", never a mutation of an existing `RecipePreview` — `RecipePreview` is frozen, R10) |
| Each regeneration is a fresh AI invocation consuming the global budget; no per-user quota is counted (`FR-AI-10`, `NFR-AI-01`, `G-70`) | R10 (`RecipePreview`'s fields are exactly `{recipe}` — structurally, no counter can be attached); `design.md` §5 (no cross-call state anywhere in this module) |
| Per-slot results are independent: one slot failing does not abort the others and partial results are kept (`FR-AI-09`, `FR-AI-12`) | R20, R21 |
| Insufficient library recipes for library-only or mix mode produces an explicit named failure, never a silent partial result (`FR-AI-12`, `G-66`) | R14 (`INSUFFICIENT_LIBRARY_RECIPES` is a named member, not a generic catch-all); R17 (its own message); R20 (`SlotGenerationResult.outcome` has no default — a slot's result can never be omitted, only ever an explicit `GenerationSuccess` or `GenerationFailure`) |
| Failure messages come from the es-ES messages module (`FR-UX-03`) | R17 |

Supporting requirements not demanded by a single acceptance bullet but
required by the invariants those bullets rest on: R1, R2, R7, R8, R9 (the
`RawRecipeOutput`/`Recipe` field-by-field carry-through `R3`/`R5`'s equality
claims assume exists); R16 (the success half of the `GenerationSuccess |
GenerationFailure` outcome R18/R19 construct).
