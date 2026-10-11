# Plan — silent-failures-not-logged (issue 14)

Builds on issue 13 (in_progress, reviewed). That issue already logs the
`AiProviderError` swallows (`single_recipe_generation.py:84`,
`week_generation.py:99`) and the SSM fail-closed branch (`ssm.py:45`).

## Expected behaviour

- **E1** — WHEN the domain validator rejects a single-recipe AI output, the
  system SHALL log a WARNING carrying the generation key, the rejecting
  validator's class name, the offending value (if the validator carries one) and
  a snippet of the model output. Implements: FR-AI-01, FR-AI-02, NFR-OBS-01.
- **E2** — WHEN the validator rejects a whole-week slot's output, the system
  SHALL log the same WARNING. Implements: FR-AI-03, FR-AI-12, NFR-OBS-01.
- **E3** — The logged model-output snippet SHALL be at most 500 characters and
  the offending value at most 100. Implements: NFR-OBS-01.
- **E4** — IF the Bedrock response has no text block or its text cannot be
  parsed, THEN the raised `AiProviderError` SHALL carry the response's
  `stopReason` and at most 500 characters of the text. Implements: FR-AI-01,
  FR-AI-03, NFR-OBS-01. (Issue 13 logs that error, so this text is what reaches
  the log.)
- **E5** — WHEN a request is answered `422 UNKNOWN_PROMPT_VERSION`, the system
  SHALL log a WARNING naming the unresolved key or version id. Implements:
  FR-AI-14, NFR-OBS-01.
- **E6** — An ordinary client-error response (4xx other than E5) SHALL NOT log
  at WARNING. Implements: NFR-OBS-01. *Guard, green today.*
- **E7** — WHEN the SSM switch is read cleanly as disabled after any other state
  (first read, enabled, or a failed read), the gate SHALL log one INFO line
  naming the parameter. Repeated disabled reads, an enabled switch, and a
  failed read (which stays issue 13's WARNING) SHALL NOT log it. Implements:
  NFR-AI-01, NFR-OBS-01. (Owner B4 = yes.)
- **E8** — The per-invocation log lines SHALL carry their facts in the message
  text: `Handled request` gets method, resource template and status; the
  rollover line gets the week id; the worker's `Processed …` lines get the
  generation key. They SHALL never carry the cookie, the query string or
  path-parameter values. Implements: NFR-OBS-01, `specs/rest_api_lambda` R22.
  (Owner B5 = yes; the rollover and worker lines were found in the re-sweep with
  the same pattern.)

Why 500 characters: that is enough for the recipe name plus the first
ingredients or steps, which shows what the model did. It stays one CloudWatch
line, well inside Lambda's 256 KB event limit. Model output is recipe text, not
a secret. Its only user-derived content is the ingredient and tool names the
household typed in, which is not PII. The offending value is capped at 100
because a free-text `estimated_time` can be unbounded.

## Fix design

| # | File (layer) | Change |
|---|---|---|
| F1 | `core/.../domain/ai_output.py:145` (domain) | `validate_and_preview` stays pure. Its `GenerationFailure` gains a diagnostic `cause: str \| None` (`field(default=None, compare=False)`, so existing equality checks hold). Its value is the class name plus `exc.args[0]` capped at 100. It never reaches the wire: `_failed` and `SlotResult` keep using `code`/`message`. |
| F1 | `single_recipe_generation.py` (the `isinstance(outcome, GenerationFailure)` branch), `week_generation.py` (same branch) (application) | `logger.warning(key, outcome.cause, repr(raw)[:500])`, using stdlib `logging` as in issue 13. |
| F2 | `lambda_ai/.../adapters/bedrock.py:72, :98` (adapter) | `_extract_text` / `_parse_recipe` error messages include `response.get("stopReason")` and `text[:500]`. No new log call: issue 13's warning carries it. |
| F3 | `lambda_api/.../errors.py:141` (adapter) | A per-row opt-in (e.g. `_ErrorSpec.log_warning`), set **only** on `UnknownPromptVersion`. `build_problem_response` logs a WARNING with the type name and `exc.args` (key or version id). No other row changes. |
| F4 | `lambda_ai/.../adapters/ssm.py` (adapter) | Remember the last *read outcome* (enabled / disabled-by-switch / failed). Log INFO only on a transition into disabled-by-switch. This is per warm container, so a long "off" period costs one line per container, not one per 5 s TTL refresh. |
| F5 | `lambda_api/.../handler.py:104`, `scheduled.py:36`, `lambda_ai/.../handler.py:33, :61` (entry points) | Move the existing `extra` values into %-style message args, e.g. `"Handled request %s %s -> %s", method, resource, status`. Keep `extra` as it is, because `test_handler.py:342` reads it and a JSON log format prints it. `resource` is the route template (`/v1/generations/{generationId}`), so no ids, query string or cookie reach the text. No logging configuration is touched. |

**Why F5 is code-only, and what it cannot fix.** Nothing in the code configures
the Lambda log level or format; only the dev servers call `basicConfig`. The
Lambda runtime's default text format prints `%(message)s` and drops `extra`,
which is why the status code is invisible today. F5 fixes that for every format.
**However:** as far as I know (not verified against a deployed function), the
Python runtime leaves the root logger at WARNING unless the function's
`LoggingConfig.ApplicationLogLevel` is set. If so, **no INFO line reaches
CloudWatch** in production: not `Handled request`, not E7's switch line, not
the worker's `Processed` lines. That setting (with `LogFormat=JSON` if `extra`
fields are wanted) is Lambda configuration, which is human-owned IaC. See open
question Q2. I rejected `setLevel(INFO)` in code: it would override whatever
level an operator configures, which is logging config the code should not own.

Rejected alternatives:
- **Log inside `validate_and_preview`.** It is domain code: it gains a side
  effect, and it has no idempotency key to correlate the line with the record.
- **Log every mapped 4xx in `errors.py`.** Every 401, 404 and validation 422
  would become a WARNING. That is the flood E6 forbids, and the per-request
  `Handled request` INFO record already exists.

## Sweep (backend `src/`, tests and `.venv` excluded; lens: production harm)

Changed: F1–F5 above. Already fixed by issue 13: `single_recipe_generation.py:84`,
`week_generation.py:99`, `lambda_ai/adapters/ssm.py:45`.

Re-sweep 2026-10-11 under the owner's lens ("lack of logs that could harm
production"): it added the `extra`-only lines in `scheduled.py:36` and
`lambda_ai/handler.py:33, :61` to F5, since they are the same B5 pattern and
carry no secrets. `wiring.py:44` (archive discard, `weekId` in extra) is the
same pattern, but archive is parked for the MVP, so it is left out. Nothing else
that had been dismissed passes both the "harms production" test and the
"no flood / no secret" test.

Dev-only, out of scope (owner B3): `lambda_api/local_server.py:119, :123, :154`,
`lambda_api/seed_local_data.py:98, :126`, `lambda_ai/local_worker.py:147–167`.

Not changed, and why:

| Site | Swallowed into | Why not |
|---|---|---|
| `core/application/authentication.py:59` | `InvalidToken` → `SessionExpired` (401) | Expected; the token is a credential; the authorizer already logs INFO (`authorizer.py:58`) |
| `core/ports/tokens.py:61, :69` | bad cookie → `InvalidToken` | Expected; cookie content must not be logged |
| `core/application/rule_editing.py:92`, `domain/calendar.py:72`, `domain/rules.py:254`, `lambda_api/serialization.py:88, :133, :140, :150, :354` | named 4xx domain errors | Client validation; E6 flood |
| `core/domain/shopping.py:226` | re-raised `InsufficientNewIds` | Unmapped → 500, already logged with traceback (`errors.py:166`) |
| `lambda_api/adapters/dynamo/accounts.py:84, :136, :206`, `shopping_list.py:95, :111`, `lambda_api/adapters/sqs.py:149, :213`, `lambda_ai/adapters/dynamo/generations.py:41` | `ConditionalCheckFailed` → domain outcome | Expected concurrency outcome; every other code is re-raised and logged as a 500 |
| `lambda_api/serialization.py:433` | non-JSON result → returned as string | Intentional: the whole-week result is an opaque string |
| `lambda_*/adapters/dynamo/_table.py:79 / :98` | `ResourceInUse` | The table already exists; expected |
| `lambda_ai/handler.py:77`, `message.py:55–125` | per-record isolation | Already `logger.exception` with traceback |
| `lambda_api/…/_meal.py:85`, `lambda_ai/…/_meal.py:85` | legacy non-numeric `tiempo` read as absent | Owner B2 = no (intentional, G-90; it would repeat on every read) |
| `lambda_api/wiring.py:44` | archive discard, `weekId` in `extra` only | Archive parked for the MVP |

Owner answers (2026-10-11): B2 no, B3 no (dev-only), B4 yes (F4/E7), B5 yes
(F5/E8). **B1 is awaiting the owner's decision** and is not in the fix (see the
optional block below).

### Optional block B1 — awaiting owner (not in T1–T8)

`core/ports/password_hasher.py:40-50`: a stored hash has the shape
`algo$iterations$salt_hex$digest_hex`. If the `split` or `fromhex` call raises
`ValueError`, `verify()` returns `False`. So a corrupt stored hash looks exactly
like a wrong password: the user gets a plain 401 and nothing is logged. If the
owner says yes:
- **EB1:** IF the stored hash is malformed, THEN `verify()` SHALL return `False`
  and log one WARNING "malformed stored password hash", with no hash, password
  or username (the port has no user id).
- **TB1:** add a test in `core/tests/ports/` asserting the WARNING is logged, the
  return is `False`, and the hash text is absent from the log; then implement it.
- **Risk:** low. It fires only on data corruption, never on a wrong password.

## Test plan

| Staged (`issues/silent-failures-not-logged/tests/…`) | Destination |
|---|---|
| `backend/core/tests/application/test_validation_failure_logging.py` | same path under repo root |
| `backend/lambda_ai/tests/test_bedrock_failure_diagnostics.py` | same |
| `backend/lambda_api/tests/test_config_fault_logging.py` | same |
| `backend/lambda_ai/tests/test_ssm_gate_disabled_logging.py` | same |
| `backend/lambda_api/tests/test_request_log_line.py` | same |
| `backend/lambda_ai/tests/test_worker_log_line.py` | same |

| Test | E | Red at triage (2026-10-11) |
|---|---|---|
| `test_single_recipe_rejection_logs_validator_value_and_snippet` ×6 (UnknownUnit, UnknownIngredientCategory, InvalidEstimatedTime, InvalidIngredientQuantity, InvalidServings, MissingTools) — **reproduction** | E1 | red: `failed` recorded, zero WARNING records |
| `test_week_slot_rejection_logs_validator_value_and_snippet` | E2 | red: zero warnings |
| `test_a_huge_rejected_output_is_logged_bounded` | E3 | red: zero warnings |
| `test_unparseable_output_error_carries_stop_reason_and_snippet` | E4 | red: message is `unparseable model output: substring not found` |
| `test_the_snippet_in_the_error_is_bounded` | E4 | red: no stop reason |
| `test_a_response_with_no_text_block_names_the_stop_reason` | E4 | red |
| `test_an_unresolvable_prompt_version_is_logged[unset,unknown]` | E5 | red: 422 with zero warnings |
| `test_an_ordinary_client_error_logs_no_warning` | E6 | green (guard) |
| `test_a_clean_false_logs_one_info_and_no_warning` | E7 | red: no INFO |
| `test_repeated_disabled_reads_log_once` | E7 | red: 0 lines, expected 1 |
| `test_each_transition_into_disabled_logs_again` | E7 | red: 0 lines, expected 2 |
| `test_an_enabled_switch_logs_nothing` | E7 | green (guard) |
| `test_a_failed_read_is_the_warning_not_the_disabled_info` | E7 | green (guard; issue 13 WARNING) |
| `test_the_request_line_shows_method_resource_and_status` | E8 | red: message is the bare `Handled request` |
| `test_the_request_line_omits_cookie_query_and_path_values` | E8 | red: the template is not in the text yet (its no-leak half holds today) |
| `test_the_rollover_line_shows_the_archived_week` | E8 | red: week id only in `extra` |
| `test_the_processed_line_names_the_generation[recipe,week]` | E8 | red: key only in `extra` |

Totals: **21 failed, 3 passed**, run against the current tree with issue 13
applied. The 3 passes are the E6/E7 guards. `ruff check` and `ruff format` are
clean; mypy reports only the `support.fakes`/`_helpers` path noise that the
existing suites also hit. `git status` is unchanged after the copies were
removed.
