# Implementation report: feature 34 `ai_fallback_recipe`

Fallback sentence appended in place to `HEALTHY_BALANCED_INSTRUCTION_V4` (owner decision 2026-10-11: edit v4, no v5). `./init.sh` green, 1158 passed. Reviewer: all mutants killed.

F = `backend/core/tests/domain/test_ai_prompt_fallback.py`, W = `backend/lambda_ai/tests/test_prompt_fallback_wording.py`

| R | Test |
|---|---|
| R1, R16 | F `test_v4_instruction_ends_with_the_fallback_sentence` |
| R2–R4 | W `test_the_fallback_sentence_is_rendered[specification,reference,week_slot]` |
| R5–R7 | W `test_it_names_the_four_unusable_cases_and_the_keep_usable_clause[*]` |
| R8, R9 | W `test_the_guidelines_and_language_are_still_rendered[*]` |
| R10 | F `test_retained_versions_are_unchanged[v1,v2,v3]` (hashes dataclass fields, not rendered text) |
| R11 | F `test_v4_is_v3_with_only_the_healthy_balanced_instruction_replaced`; issue 17 guard |
| R12 | W `test_only_the_healthy_balanced_line_differs_from_v3[*]` |
| R13 | W `test_the_specification_strings_reach_the_prompt_unchanged` |
| R14, R15 | existing `lambda_api/tests/test_single_recipe_generation_route.py::test_empty_ingredients_or_tools_are_422` (no code change) |
| R17 | W `test_v4_never_asks_to_generate_a_menu[*]` |

## Open: T8 (owner-run live probe)

Paid Bedrock calls, so no agent ran it. Script (scratchpad, not in the repo): `C:/Users/Sergio/AppData/Local/Temp/claude/C--Users-Sergio-projects-proyecto-final-curso-aws/c4df60a7-e160-4cab-a73d-bae4970e0da1/scratchpad/fallback_probe.py`. Run from `backend/lambda_ai` with `uv run python <path>` and the Bedrock key set. Matrix and pass criteria: `specs/ai_fallback_recipe/design.md`.

Known gap (non-blocking): R10 does not pin v1/v2 rendered text, only their fields.
