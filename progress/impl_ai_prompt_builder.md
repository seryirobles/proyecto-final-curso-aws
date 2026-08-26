# Implementation report — ai_prompt_builder (feature 11)

## Tasks completed

T1–T10, all ticked in `specs/ai_prompt_builder/tasks.md`.

## Files

- `backend/core/src/planner_core/domain/ai_prompt.py` (new)
- `backend/core/tests/domain/test_ai_prompt.py` (new)

## Traceability

- R1 (FR-AI-13) → `test_configured_servings_is_four`
- R2 (FR-AI-07) → `test_output_language_is_es_es`
- R3 (FR-AI-06) → `test_healthy_balanced_instruction_is_non_empty`
- R4 (FR-LIB-05) → `test_allowed_units_contains_every_unit_member`
- R5 (FR-AI-06, FR-AI-07, FR-AI-13, FR-LIB-05) →
  `test_prompt_instructions_fields_are_exactly_the_fixed_shape`,
  `test_prompt_instructions_is_frozen`
- R6 (FR-AI-13) → `test_build_instructions_matches_the_module_constants`
- R7 (FR-AI-07) → `test_build_instructions_matches_the_module_constants`
- R8 (FR-AI-06) → `test_build_instructions_matches_the_module_constants`
- R9 (FR-LIB-05) → `test_build_instructions_matches_the_module_constants`
- R10 (FR-AI-01) → `test_specification_prompt_fields_are_exactly_the_fixed_shape`
- R11 (FR-AI-02) → `test_reference_prompt_fields_are_exactly_the_fixed_shape`
- R12 (FR-AI-04) → `test_category_prompt_fields_are_exactly_the_fixed_shape`
- R13 (FR-AI-01) → `test_build_specification_prompt_carries_its_inputs`
- R14 (FR-AI-01) → `test_build_specification_prompt_carries_its_inputs`
- R15 (FR-AI-01) → `test_build_specification_prompt_carries_its_inputs`
- R16 (FR-AI-02) → `test_build_reference_prompt_carries_its_inputs`
- R17 (FR-AI-02) → `test_build_reference_prompt_carries_its_inputs`
- R18 (FR-AI-02) → `test_build_reference_prompt_carries_its_inputs`
- R19 (FR-AI-04) → `test_build_category_prompt_carries_its_input`
- R20 (FR-AI-04) → `test_build_category_prompt_carries_its_input`

Every `FR-*` in the feature's `covers` array (`FR-AI-01`, `FR-AI-02`,
`FR-AI-04`, `FR-AI-06`, `FR-AI-07`, `FR-AI-13`) is reachable through the R<n>
map above; `FR-LIB-05` is consumed (not owned) per `requirements.md`'s scope
note and is likewise covered (R4, R5, R9).

## Test result

`./init.sh` green: ruff format, ruff check, mypy --strict, pytest all pass.
234 tests total (221 baseline → 234, +13 new for this feature).

## Anything the spec didn't anticipate

Two lines in the design's §6 literal signatures exceeded ruff's 100-char line
length once transcribed verbatim (`CONFIGURED_SERVINGS`'s docstring and
`ReferencePrompt`'s docstring). Shortened both without changing meaning —
`CONFIGURED_SERVINGS`'s dropped "proposed value, " (redundant with "approved
at this spec's human gate" right after it); `ReferencePrompt`'s dropped
"extra " before "specifications" in the docstring prose only, the field name
itself (`extra_specifications`) is untouched. No other deviation from
`design.md` §6.
