# impl: ai_inference_config (feature 33)

Result: `./init.sh` green (1216 passed).

| R | Test (`backend/lambda_ai/tests/`) |
|---|---|
| R1 | test_inference_config: settings_are_read_on_every_call |
| R2, R14 | unset_env_sends_exactly_...; converse_kwargs_never_carry_the_fixed_fields |
| R3 | unset_env_... ; test_bedrock default/override model tests |
| R4-R7, R9 | each_variable_maps_to_its_converse_field; flex_is_sent_and_standard_is_omitted |
| R8, R10, R11 | flex_is_sent...; reasoning_defaults_to_low_effort_and_off_omits_the_field |
| R12, R13 | effort_high_with_temperature_or_top_p_raises_before_the_client; reasoning_off_with_effort_high_keeps_temperature |
| R15-R17 | an_invalid_value_raises_before_the_client_and_names_the_variable (17 cases, sentinel token) |
| R18 | a_blank_value_is_treated_as_unset; whitespace_around... |
| R19 | a_reasoning_block_before_the_tool_use_parses (toolUse, per issue 15) |
| R20 | single_recipe_and_week_jobs_send_identical_inference_kwargs |
| R21, R22 | test_inference_docs.py |
| R23 | effort_high_omits_max_tokens_even_when_set |

covers is empty, so no FR-* reachability beyond the R-level Implements lines.

Not anticipated by the spec:
- `backend/tests/contract/test_ai_provider_contract.py` imported `_MAX_TOKENS`; it now imports `DEFAULT_MAX_TOKENS` (one-line edit).
- R19 is tested against `toolUse` (issue 15 superseded the `text` block).
- Error messages name the variable and domain but never echo the offending value.
- `docs/architecture.md` and the Marketplace/`AI_MODEL_ID` paragraphs were left to the leader as specified.
