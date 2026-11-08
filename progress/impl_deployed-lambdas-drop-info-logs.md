# Implementation report: issue 24 deployed-lambdas-drop-info-logs

## Traceability (E -> T -> code -> test)

| E | T | Code | Test |
|---|---|---|---|
| E1, E2, E9 | T5 (leader) | `terraform/lambda.tf`, `locals.tf` | `test_terraform_lambda_logging.py` (red until T5) |
| E3 | T3 | the four `lambda_handler`s | `test_lambda_log_levels.py` |
| E4, E6 | T2, T3 | `sdk_logging.py` (both packages), `quiet_sdk_loggers()` first line | `test_lambda_log_levels.py` |
| E5 | T2, T3 | same | `test_no_secret_reaches_the_log_at_root_debug` |
| E7 | T2 | the pin never sets the root level | `test_the_entry_point_leaves_the_root_level_alone` |
| E8 | none needed | no `extra=` change | `test_log_extra_keys.py` |
| E10 | T3 | app loggers untouched | `test_an_app_debug_line_still_reaches_the_log_at_root_debug` |
| E11 | T3b | `authorizer.py`: `logger.info("Allowing authorizer request")` | `lambda_api/tests/test_authorizer_allow_log.py` (new, red first) |

## Notes

- Four staged files copied (not moved) into `backend/tests/`; originals stay in `issues/`.
- Red check before the fix: 18 failed, 25 passed, all staged; includes
  `test_no_secret_reaches_the_log_at_root_debug` (3) and `test_every_function_logs_in_json`.
- `sdk_logging.py` is byte-identical in `planner_api` and `planner_ai`.
- T5 (Terraform) is the leader's; T7 (deploy, apply, dev check) is the owner's.

## Review round 1 additions

- `backend/lambda_api/tests/test_authorizer_allow_log.py`: two Deny-branch tests; the
  identity check now reads only the message and `extra`-added attributes.
- `backend/lambda_api/tests/test_api_sdk_logging.py` and
  `backend/lambda_ai/tests/test_ai_sdk_logging.py`: the pin touches only the four SDK
  loggers (package-specific names avoid a basename collision).
- `_lambda_log_probe.py` comment corrected in the live and staged copies, still byte-identical.
