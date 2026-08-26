# Implementation report — recipe_metadata_fields (feature 25)

Tasks T1–T12 of `specs/recipe_metadata_fields/tasks.md` complete, all ticked.

## What changed

- `backend/core/src/planner_core/domain/recipe.py`: `Recipe`/`MealSnapshot`
  gain `servings: int | None = None`, `estimated_time: str | None = None`;
  `snapshot()` copies both.
- `backend/core/src/planner_core/domain/ai_output.py`: `RawRecipeOutput`
  mirrors both fields; `validate_ai_recipe_output` copies them through
  unchanged, no new branch, no new exception.
- `backend/core/src/planner_core/domain/candidate.py`: `to_library_entry`'s
  `Recipe(...)` construction gains `servings=meal.servings`,
  `estimated_time=meal.estimated_time` — the two sanctioned lines.
- `backend/core/src/planner_core/domain/ai_prompt.py`: `CONFIGURED_SERVINGS`
  removed; `servings` removed from `PromptInstructions` and
  `PromptInstructionsVersion`; `RECIPE_METADATA_INSTRUCTION` constant and
  `recipe_metadata_instruction: str` field added to both, threaded through
  `build_instructions()`.
- New `backend/core/tests/test_no_recipe_metadata_logic.py`: mechanical scan
  mirroring `test_no_ambient_time.py`, proving R18–R22.
- Updated tests: `test_recipe.py`, `test_ai_output.py`, `test_candidate.py`,
  `test_ai_prompt.py` (full rewrite of the `CONFIGURED_SERVINGS`/`.servings`
  assertions).
- Cross-feature spec maintenance (T5): amended
  `specs/ai_prompt_builder/requirements.md` (feature 11, R1/R5/R6 and their
  coverage map) and `specs/ai_prompt_versioning/requirements.md` +
  `design.md` (feature 24, R1/R5 and the `v1` construction example) with
  amendment blockquotes — original text kept as historical record, not
  deleted, following the precedent feature 24 itself set for feature 11.

Comments in `ai_prompt.py`/`recipe.py` were kept to the 3-line ceiling
(`docs/conventions.md`) and, outside the two sanctioned copy-through sites,
avoid the literal words "servings"/"estimated_time" so they do not trip the
mechanical scan — this only affected docstring wording, not any design
decision.

## Traceability

| R<n> | FR-* | Test |
|---|---|---|
| R1 | FR-LIB-03 | `test_recipe_fields_are_exactly_the_fixed_shape`, `test_recipe_servings_and_estimated_time_default_to_none` |
| R2 | FR-LIB-03 | `test_recipe_fields_are_exactly_the_fixed_shape`, `test_recipe_servings_and_estimated_time_default_to_none` |
| R3 | FR-LIB-03 | `test_meal_snapshot_is_a_distinct_frozen_type`, `test_meal_snapshot_servings_and_estimated_time_default_to_none` |
| R4 | FR-LIB-03 | `test_meal_snapshot_is_a_distinct_frozen_type`, `test_meal_snapshot_servings_and_estimated_time_default_to_none` |
| R5 | FR-LIB-03 | `test_snapshot_copies_servings_and_estimated_time_when_set`, `test_snapshot_copies_servings_and_estimated_time_when_absent` |
| R6 | FR-LIB-03 | `test_snapshot_copies_servings_and_estimated_time_when_set`, `test_snapshot_copies_servings_and_estimated_time_when_absent` |
| R7 | FR-LIB-03 | `test_recipe_accepts_any_servings_and_estimated_time_value` |
| R8 | FR-LIB-03 | `test_recipe_accepts_any_servings_and_estimated_time_value` |
| R9 | FR-MENU-04 | `test_recipe_fields_are_exactly_the_fixed_shape` (structural: one dataclass) |
| R10 | FR-AI-13 | `test_raw_recipe_output_fields_are_exactly_the_fixed_shape`, `test_raw_recipe_output_servings_and_estimated_time_default_to_none` |
| R11 | FR-AI-13 | `test_raw_recipe_output_fields_are_exactly_the_fixed_shape`, `test_raw_recipe_output_servings_and_estimated_time_default_to_none` |
| R12 | FR-AI-13 | `test_validate_ai_recipe_output_does_not_raise_when_both_fields_are_absent` |
| R13 | FR-AI-13 | `test_validate_ai_recipe_output_does_not_raise_when_both_fields_are_absent` |
| R14 | FR-AI-13, FR-LIB-03 | `test_validate_ai_recipe_output_copies_servings_and_estimated_time_when_present`, `test_validate_ai_recipe_output_copies_one_field_present_one_absent` |
| R15 | FR-AI-13, FR-LIB-03 | `test_validate_ai_recipe_output_copies_servings_and_estimated_time_when_present`, `test_validate_ai_recipe_output_copies_one_field_present_one_absent` |
| R16 | FR-LIB-03 | `test_to_library_entry_copies_servings_and_estimated_time_when_set`, `test_to_library_entry_copies_servings_and_estimated_time_when_absent` |
| R17 | FR-LIB-03 | `test_to_library_entry_copies_servings_and_estimated_time_when_set`, `test_to_library_entry_copies_servings_and_estimated_time_when_absent` |
| R18 | FR-AI-13 | `test_ai_prompt_declares_no_top_level_int_constant` (structural, catches any rename), `test_configured_servings_no_longer_appears_anywhere_in_ai_prompt` (narrow, the literal old name) |
| R19 | FR-AI-13 | `test_prompt_instructions_declares_no_servings_field`, `test_prompt_instructions_fields_are_exactly_the_fixed_shape` |
| R20 | FR-AI-13 | `test_prompt_instructions_version_declares_no_servings_field`, `test_prompt_instructions_version_fields_are_exactly_the_fixed_shape` |
| R21 | FR-LIB-03 | `test_no_planner_core_module_reads_servings_or_estimated_time_outside_the_sanctioned_sites` |
| R22 | FR-LIB-03 | `test_no_planner_core_module_reads_servings_or_estimated_time_outside_the_sanctioned_sites` |
| R23 | FR-AI-13, FR-AI-14 | `test_prompt_instructions_version_fields_are_exactly_the_fixed_shape`, `test_recipe_metadata_instruction_is_the_approved_wording` |
| R24 | FR-AI-13 | `test_prompt_instructions_fields_are_exactly_the_fixed_shape` |
| R25 | FR-AI-13 | `test_build_instructions_matches_the_module_constants`, `test_build_instructions_sources_content_from_the_named_version`, `test_build_specification_prompt_carries_the_recipe_metadata_instruction`, `test_build_reference_prompt_carries_the_recipe_metadata_instruction`, `test_build_category_prompt_carries_the_recipe_metadata_instruction` |

Every `FR-*` in `covers` (`FR-LIB-03`, `FR-MENU-04`, `FR-AI-13`) is reached
by at least one `R<n>` above; `FR-AI-14` is consumed (R23) but not owned, per
`requirements.md`'s scope note.

## Verification

- `./init.sh`: green — ruff format, ruff check, mypy, pytest (319 passed,
  up from 295 before this feature), prettier, eslint, vitest all `[OK]`.
- `test_shared_kernel_guards.py` and `test_no_ambient_time.py` pass
  **unmodified** (confirmed via `git diff --stat`, no output).
- Mutation testing is the reviewer's job, not run here (`docs/verification.md`
  Level 5).

## Post-review fix (reviewer finding, CHANGES_REQUESTED)

R18's guard checked only the literal string `"CONFIGURED_SERVINGS"`; a
rename (e.g. `DEFAULT_SERVINGS: Final[int] = 4`) defeated it — 1 mutant
survived. Fixed by adding an AST-based structural scan,
`test_ai_prompt_declares_no_top_level_int_constant`, asserting no top-level
`int`/`Final[int]` constant of any name exists in `ai_prompt.py` (the
module's only legitimate top-level constants — `OUTPUT_LANGUAGE`,
`HEALTHY_BALANCED_INSTRUCTION`, `RECIPE_METADATA_INSTRUCTION`,
`ALLOWED_UNITS`, `PROMPT_INSTRUCTION_VERSIONS` — are all non-`int`).

Scoped to `ai_prompt.py` rather than all of `planner_core`: `password_policy.py`
(`MIN_LENGTH`) and `rules.py` (`DAYS_PER_WEEK`, `SLOTS_PER_DAY`,
`TOTAL_SLOTS`) declare legitimate, unrelated `Final[int]` constants — a
package-wide ban would false-positive on them.

Added `test_the_int_constant_scan_catches_a_renamed_deployment_config_constant`
(plants the reviewer's mutant shape in a `tmp_path` file, asserts it's
caught; also asserts a non-`int` constant is not a false positive). Verified
directly against the real reviewer mutant: temporarily renamed
`CONFIGURED_SERVINGS` to `DEFAULT_SERVINGS` in `ai_prompt.py` itself,
confirmed the new test fails, then reverted (`git diff --stat` clean
afterward).

Corrected `specs/recipe_metadata_fields/requirements.md`'s coverage-map
claim that R21 alone "rules out a renamed replacement constant" — that was
false (R21 only confines the per-recipe field name `servings`, unrelated to
a differently-named deployment-config constant). Now attributes the
rename-proof claim to R18's structural test.

`./init.sh` re-run after the fix: still green, 318 tests (up from 316 before
this fix — net +2: `test_ai_prompt_declares_no_top_level_int_constant` and
`test_the_int_constant_scan_catches_a_renamed_deployment_config_constant`).
`test_shared_kernel_guards.py` and `test_no_ambient_time.py` re-confirmed
unmodified.
