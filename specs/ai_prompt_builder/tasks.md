# ai_prompt_builder — Tasks

> Feature 11 · tier 1. Read `requirements.md` and `design.md` first. The
> `implementer` ticks `[x]` as each completes; the `reviewer` rejects if any
> `[ ]` remains without a documented justification.

- [x] T1 — Create `backend/core/src/planner_core/domain/ai_prompt.py` with its
  module docstring and imports (`recipe.Recipe`, `rules.CategoryCountRule`,
  `units.Unit`). Covers: R1–R20 (scaffolding).

- [x] T2 — Add `CONFIGURED_SERVINGS: Final[int] = 4`, `OUTPUT_LANGUAGE:
  Final[str] = "es-ES"`, `HEALTHY_BALANCED_INSTRUCTION: Final[str] = ...`
  (exact wording per `design.md` §4) and `ALLOWED_UNITS: Final[tuple[Unit,
  ...]] = tuple(Unit)`. Covers: R1, R2, R3, R4.

- [x] T3 — Add `PromptInstructions` (`@dataclass(frozen=True)`). Covers: R5.

- [x] T4 — Add `build_instructions()` composing the four constants above into
  a `PromptInstructions`. Covers: R6, R7, R8, R9.

- [x] T5 — Add `SpecificationPrompt`, `ReferencePrompt` and `CategoryPrompt`
  (`@dataclass(frozen=True)` each). Covers: R10, R11, R12.

- [x] T6 — Add `build_specification_prompt(ingredients, tools)`. Covers:
  R13, R14, R15.

- [x] T7 — Add `build_reference_prompt(reference_recipe,
  extra_specifications)`. Covers: R16, R17, R18.

- [x] T8 — Add `build_category_prompt(category_counts)`. Covers: R19, R20.

- [x] T9 — Create `backend/core/tests/domain/test_ai_prompt.py` covering
  every `R<n>`, including: a `build_instructions` case asserting all four
  field equalities; a `build_specification_prompt` case asserting its
  `instructions`/`ingredients`/`tools` fields; a `build_reference_prompt`
  case asserting its `instructions`/`reference_recipe`/`extra_specifications`
  fields, constructing a `Recipe` fixture per `recipe_model`'s existing test
  support; and a `build_category_prompt` case asserting its
  `instructions`/`category_counts` fields, using a `CategoryCountRule`
  fixture per `rules_model`'s existing test support. Covers: R1–R20.

- [x] T10 — Run `./init.sh`; confirm `ruff format`, `ruff check`, `mypy
  --strict` and `pytest` (deselecting `-m 'not aws'`) all pass, and that
  `test_shared_kernel_guards.py` and `test_no_ambient_time.py` still pass
  unmodified. Covers: R1–R20.
