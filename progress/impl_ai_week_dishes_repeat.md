# Impl — issue 18 `ai-week-dishes-repeat`

| E | Change | Test |
|---|---|---|
| E1 | `_fill_slots` accumulates names of dishes written in the run into `CategoryPrompt.avoid_names` | `test_week_generation_variety.py::..earlier_in_the_run` |
| E2 | Week occupancy candidates seed the avoid list | `..already_in_the_week` |
| E3 | Library-pick names added (mix) | `..library_picks..` |
| E4 | Retry goes through `_fill_slots` with the week occupancy | `..retried_slot..` |
| E5 | `bedrock._render` appends the v5 avoid line | `lambda_ai/tests/test_bedrock_week_variety.py` |
| E6 | `reduce_needs` after each written AI meal | `test_week_generation_needs.py` (written first, red `[1,1,1,1]`, green `[1,0,0,0]`) |

Red to green: the 5 staged tests plus the E6 test failed before the fix for the diagnosed reason (no names; needs never reduced).

Design: `CategoryPrompt.avoid_names` (default `()`); prompt v5 = v4 wording; the avoid line lives in a separate `AVOID_NAMES_TEMPLATES` registry, `PromptInstructions.avoid_names_template` (default `""`). `PromptInstructionsVersion` is unchanged, so v1-v4 digests and bytes are unchanged. Name dedup by `domain.text.normalize`. A slot where a definitive outranks the AI output writes nothing, so adds no name and reduces no need.

Unanticipated:
- Existing tests pinning shapes updated (extended, not loosened): `test_ai_prompt.py` registry set (+v5), `PromptInstructions` fields (+`avoid_names_template`), `CategoryPrompt` fields (+`avoid_names`).
- `docs/local_development.md` line 67 changed to `AI_PROMPT_VERSION_ID=v5`: `test_the_documented_local_env_selects_the_newest_version` pins it to the newest key.

Owner must set: `AI_PROMPT_VERSION_ID=v5` in every deployed config (worker/API enrichment source) and in his local env. Until then v4 is used and the fix has no effect.

Review fix: `test_avoid_names_list_a_dish_once_whatever_its_case_or_accents` (test_week_generation_needs.py) kills both `_distinct` mutants (setdefault(name, name); `_distinct` removed).
