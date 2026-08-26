# ai_output_validation — Tasks

> Feature 12 · tier 1. Read `requirements.md` and `design.md` first. The
> `implementer` ticks `[x]` as each completes; the `reviewer` rejects if any
> `[ ]` remains without a documented justification.

- [x] T1 — Create `backend/core/src/planner_core/domain/ai_output.py` with its
  module docstring and imports (`planner_core.domain.recipe.{Recipe,
  Ingredient}`, `planner_core.domain.units.{Unit, UnknownUnit, parse_unit}`,
  `planner_core.domain.ingredient_category.{UnknownIngredientCategory,
  parse_category}`, `planner_core.domain.calendar.SlotRef`,
  `planner_core.messages`). Covers: R1–R21 (scaffolding).

- [x] T2 — Add `RawIngredient` and `RawRecipeOutput`
  (`@dataclass(frozen=True)` each). Covers: R1, R2.

- [x] T3 — Add `validate_ai_recipe_output(raw: RawRecipeOutput) -> Recipe`,
  resolving each ingredient's unit via `parse_unit` (never `Unit(...)`
  directly — `test_planner_core_never_constructs_unit_directly` enforces
  this) and the category via `parse_category`, carrying `name`, `tools` and
  `procedure` through unchanged. Covers: R3, R4, R5, R6, R7, R8, R9.

- [x] T4 — Add `RecipePreview` (`@dataclass(frozen=True)`, field `recipe:
  Recipe` only). Covers: R10.

- [x] T5 — Add `new_preview(recipe)`, `accept_preview(preview)` and
  `discard_preview(preview)`. Covers: R11, R12, R13.

- [x] T6 — Add `GenerationFailureReason` (`StrEnum`: `INVALID_OUTPUT`,
  `INSUFFICIENT_LIBRARY_RECIPES`, `GENERATION_UNAVAILABLE`). Covers: R14.

- [x] T7 — Add `GenerationFailure` and `GenerationSuccess`
  (`@dataclass(frozen=True)` each), and the `GenerationOutcome` type alias
  (`GenerationSuccess | GenerationFailure`). Covers: R15, R16.

- [x] T8 — Add the three new es-ES constants to
  `backend/core/src/planner_core/messages.py`
  (`AI_GENERATION_INVALID_OUTPUT`, `AI_GENERATION_INSUFFICIENT_LIBRARY_RECIPES`,
  `AI_GENERATION_UNAVAILABLE`, exact wording per `design.md` §4), then add
  `build_generation_failure(reason: GenerationFailureReason) ->
  GenerationFailure` in `ai_output.py`, mapping each reason to its constant
  per `design.md`/`requirements.md`'s table. Covers: R17.

- [x] T9 — Add `validate_and_preview(raw: RawRecipeOutput) ->
  GenerationOutcome`, calling `validate_ai_recipe_output` and wrapping a
  success in `GenerationSuccess(preview=new_preview(...))`, catching
  `UnknownUnit`/`UnknownIngredientCategory` and returning
  `build_generation_failure(GenerationFailureReason.INVALID_OUTPUT)` instead
  of propagating. Covers: R18, R19.

- [x] T10 — Add `SlotGenerationResult` (`@dataclass(frozen=True)`, fields
  `slot: SlotRef`, `outcome: GenerationOutcome`). Covers: R20, R21.

- [x] T11 — Create `backend/core/tests/domain/test_ai_output.py` covering
  every `R<n>`, including: `RawIngredient`/`RawRecipeOutput` field-shape and
  frozen-ness checks; `validate_ai_recipe_output` cases for a valid input, an
  unknown unit (`pytest.raises(UnknownUnit)`), and an unknown category
  (`pytest.raises(UnknownIngredientCategory)`); `RecipePreview` field-shape,
  frozen-ness and `{"recipe"}`-only field-set assertion; `new_preview` /
  `accept_preview` / `discard_preview` behaviour; `GenerationFailureReason`
  membership; `GenerationFailure`/`GenerationSuccess` field-shape;
  `build_generation_failure` parametrized over all three reasons, asserting
  the message equals the matching `planner_core.messages` constant;
  `validate_and_preview` success and failure paths; `SlotGenerationResult`
  field-shape and a case building three entries (two success, one failure)
  asserting each preserves its own `slot`/`outcome` independently of the
  others. Covers: R1–R21.

- [x] T12 — Run `./init.sh`; confirm `ruff format`, `ruff check`, `mypy
  --strict` and `pytest` (deselecting `-m 'not aws'`) all pass, and that
  `test_shared_kernel_guards.py` and `test_no_ambient_time.py` still pass
  unmodified. Covers: R1–R21.
