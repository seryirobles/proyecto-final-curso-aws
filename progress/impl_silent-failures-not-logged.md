# impl — silent-failures-not-logged (issue 14)

T1-T8 done; TB1 skipped (owner B1 = no). `./init.sh` green: 1095 passed, ruff, mypy.

| E | Test | Change |
|---|---|---|
| E1, E3 | test_validation_failure_logging (single x6, huge) | `GenerationFailure.cause`, WARNING in single_recipe_generation |
| E2 | test_week_slot_rejection_logs_... | WARNING in week_generation |
| E4 | test_bedrock_failure_diagnostics x3 | stopReason + text[:500] in bedrock.py |
| E5, E6 | test_config_fault_logging | `_ErrorSpec.log_warning` on UnknownPromptVersion |
| E7 | test_ssm_gate_disabled_logging x5 | transition flag in ssm.py |
| E8 | test_request_log_line, test_worker_log_line | message args in 4 log calls, `extra` kept |

Unanticipated: existing `core/tests/domain/test_ai_output.py`
`test_generation_failure_fields_are_exactly_the_fixed_shape` (R15) pinned the
field set; updated to include `cause` (plan F1 requires the field). Red state
(21/3) was not re-run separately before implementing.

## Reviewer mutants (new tests, staged files untouched)
- E7 re-arm: `lambda_ai/tests/test_ssm_gate_rearm_logging.py`
- E1 cause value, E3 cause cap 100, E3 week snippet 500:
  `core/tests/application/test_validation_failure_cause.py`
- E4 snippet 500: `lambda_ai/tests/test_bedrock_snippet_bound.py`
