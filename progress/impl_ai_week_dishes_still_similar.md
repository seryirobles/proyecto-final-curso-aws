# Impl — issue 19 `ai-week-dishes-still-similar`

| E | Test (`lambda_ai/tests/test_prompt_week_variety_v6.py`) | Change |
|---|---|---|
| E1 | `test_every_avoided_name_still_reaches_the_model` | `AVOID_NAMES_TEMPLATE_V6` keeps `${names}` |
| E2 | `test_the_avoid_instruction_covers_main_ingredient_and_style` | v6 avoid wording |
| E3 | `test_a_positive_variety_steer_follows_the_avoided_names` | "different cuisine" after the list |
| E4 | `test_empty_needs_render_no_dangling_line`, `test_needs_still_render_when_present` | v6 framing without needs; `NEEDS_TEMPLATES["v6"]`; `_render` emits it only if needs exist |
| E5 | `test_v6_is_the_newest_prompt_version`, `test_retired_versions_render_byte_identical` | v6 appended; v1-v5 untouched |

Red at T1: 5 failed, 7 passed (as expected). `./init.sh`: green, 1350 passed.

Unanticipated: a new `PromptInstructions.needs_template` field (default "") was needed to carry the needs sentence to `_render`; field-set test updated.
Edited: `ai_prompt.py`, `bedrock.py` `_render`, `core/tests/domain/test_ai_prompt.py`, `docs/local_development.md` (v6).
Owner: set `AI_PROMPT_VERSION_ID=v6` in every deployed config. No test checks the live model.
