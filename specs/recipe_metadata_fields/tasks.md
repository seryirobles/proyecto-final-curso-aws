# recipe_metadata_fields — Tasks

> Feature 25 · tier 1. Read `requirements.md` and `design.md` first. The
> `implementer` ticks `[x]` as each completes; the `reviewer` rejects if any
> `[ ]` remains without a documented justification.

- [x] T1 — In `backend/core/src/planner_core/domain/recipe.py`, add
  `servings: int | None = None` and `estimated_time: str | None = None` to
  `Recipe` and to `MealSnapshot` (after `category` — the only legal position,
  `design.md` §5), and update `snapshot()` to copy both fields unchanged.
  Covers: R1, R2, R3, R4, R5, R6.

- [x] T2 — In `backend/core/src/planner_core/domain/ai_output.py`, add the
  same two optional fields to `RawRecipeOutput`, and update
  `validate_ai_recipe_output()` to pass both straight through into the
  `Recipe(...)` it builds — no `parse_*` call, no new exception path.
  Covers: R10, R11, R12, R13, R14, R15.

- [x] T3 — In `backend/core/src/planner_core/domain/candidate.py`, add
  `servings=meal.servings` and `estimated_time=meal.estimated_time` to the
  existing `Recipe(...)` construction inside `to_library_entry()` — the two
  lines `design.md` §7's mechanical scan sanctions by exact text. Covers:
  R16, R17.

- [x] T4 — In `backend/core/src/planner_core/domain/ai_prompt.py`: remove
  `CONFIGURED_SERVINGS`; remove `servings` from `PromptInstructions` and
  from `PromptInstructionsVersion`; add `RECIPE_METADATA_INSTRUCTION` (exact
  wording per `design.md` §6, `G-86`) and a `recipe_metadata_instruction:
  str` field on both `PromptInstructions` and `PromptInstructionsVersion`;
  update `PROMPT_INSTRUCTION_VERSIONS`'s `"v1"` construction and
  `build_instructions()` accordingly (`design.md` §6). Covers: R18, R19,
  R20, R23, R24, R25.

- [x] T5 — Amend `specs/ai_prompt_builder/requirements.md` (feature 11,
  `done`) — the `R<n>`s pinning `CONFIGURED_SERVINGS` and
  `PromptInstructions.servings` — to the shape T4 ships (`servings` gone,
  `recipe_metadata_instruction` added). Amend
  `specs/ai_prompt_versioning/requirements.md` and `design.md` (feature 24,
  `done`) the same way for every `PromptInstructionsVersion.servings`
  reference, including the `v1` construction example. Mirrors the precedent
  `ai_prompt_versioning`'s own T5 set when it amended `ai_prompt_builder`.
  Covers: R18, R19, R20, R23, R24, R25.

- [x] T6 — Create `backend/core/tests/test_no_recipe_metadata_logic.py`: the
  mechanical scan (`design.md` §7) proving no `planner_core` source module
  outside `domain/recipe.py`, `domain/ai_output.py`, and the two sanctioned
  lines of `domain/candidate.py` mentions `servings` or `estimated_time`;
  plus the `dataclasses.fields()` introspection proving neither
  `PromptInstructions` nor `PromptInstructionsVersion` declares a `servings`
  field; plus a text-scan proving `CONFIGURED_SERVINGS` no longer appears
  anywhere in `planner_core`. Include the self-tests
  `test_no_ambient_time.py` established as mandatory: the pattern actually
  matches what it claims to, the sanctioned lines actually exist verbatim in
  `candidate.py`, and the scanned-file list is non-empty and contains named
  modules. Do **not** extend the scan pattern to `recipe_metadata_instruction`
  — `design.md` §7 explains why it is out of this guard's scope. Covers:
  R18, R19, R20, R21, R22.

- [x] T7 — Add tests to `backend/core/tests/domain/test_recipe.py` for R1–R9:
  field shape and `None` defaults on `Recipe` and `MealSnapshot`;
  `snapshot()` copies both fields (a case with values set, a case with both
  `None`); arbitrary values accepted for both fields (zero, a negative
  `servings`, an arbitrary `estimated_time` string) with no exception.
  Covers: R1, R2, R3, R4, R5, R6, R7, R8, R9.

- [x] T8 — Add tests to `backend/core/tests/domain/test_ai_output.py` for
  R10–R15: `RawRecipeOutput` field shape and `None` defaults;
  `validate_ai_recipe_output` with both fields present (copy-through
  asserted field-by-field); with both fields absent (`None`, no exception
  raised); with one present and one absent. Covers: R10, R11, R12, R13, R14,
  R15.

- [x] T9 — Add a test to `backend/core/tests/domain/test_candidate.py` for
  R16, R17: `to_library_entry` on a `MealSnapshot` carrying non-`None`
  `servings`/`estimated_time` produces a `Recipe` whose own fields equal
  them; a second case with both `None` on the input produces both `None` on
  the result. Covers: R16, R17.

- [x] T10 — Update `backend/core/tests/domain/test_ai_prompt.py`: remove the
  two assertions naming `CONFIGURED_SERVINGS`; remove every `.servings ==`
  assertion on `PromptInstructions`/`PromptInstructionsVersion`; update every
  `build_instructions`/`build_specification_prompt`/`build_reference_prompt`/
  `build_category_prompt` call site and its field-shape assertion to the
  shape T4 ships; add assertions that `recipe_metadata_instruction` equals
  `RECIPE_METADATA_INSTRUCTION` (via `resolve_prompt_version("v1")`) in the
  result of `build_instructions` and in `.instructions.recipe_metadata_
  instruction` for all three of `build_specification_prompt`,
  `build_reference_prompt` and `build_category_prompt`. Covers: R18, R19,
  R20, R23, R24, R25.

- [x] T11 — Run `./init.sh`; confirm `ruff format --check`, `ruff check`,
  `mypy` and `pytest` (default tier) all pass, and that
  `test_shared_kernel_guards.py` and `test_no_ambient_time.py` still pass
  unmodified (neither is touched by this feature). Covers: R1–R25.

- [x] T12 — Record the `R<n>` → test traceability map in
  `progress/impl_recipe_metadata_fields.md`, per `docs/verification.md`
  Level 3. Covers: R1–R25.
