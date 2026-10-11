# Plan — ai-generation-422-unavailable (issue 13, re-scoped 2026-10-07)

Owner decisions 2026-10-07: (1) local kill-switch override via env var
`AI_GENERATION_ENABLED`, read by the worker; unset = today's behaviour (SSM,
fail closed), deployed Lambda unaffected; (2) real Bedrock stays the one call
leaving the machine; (3) this issue is re-scoped, not split.

## Expected behaviour

- **E1** — WHEN the local `api` server runs with the env documented in
  `docs/local_development.md` §2, the system SHALL accept a single-recipe
  submit (`202`) with an explicitly selected, registered prompt version.
  Implements: FR-AI-01, FR-AI-14.
- **E2** — WHEN the local `api` server runs with that env, the system SHALL
  accept a whole-week submit (`202`). Implements: FR-AI-03, FR-AI-14.
- **E3** — IF `AI_PROMPT_VERSION_ID` is unset, THEN the system SHALL answer
  `422 UNKNOWN_PROMPT_VERSION` rather than default a version. Implements:
  FR-AI-14 (G-84). *Guard, green today.*
- **E4** — The local worker's documented env (`docs/local_development.md` §3)
  SHALL set `AI_GENERATION_ENABLED=true`. Implements: FR-AI-01, FR-AI-03
  (dev tooling, owner decision 1).
- **E5** — WHILE `AI_GENERATION_ENABLED` is exactly `true` or exactly `false`,
  the local worker SHALL use that value as the generation gate without reading
  SSM. Implements: NFR-AI-01 (owner decision 1).
- **E6** — IF `AI_GENERATION_ENABLED` is unset or any other value, or the
  deployed handler builds its own dependencies, THEN the gate SHALL be the SSM
  switch exactly as today. Implements: NFR-AI-01, `specs/ai_lambda` R16–R19.
  *Deployed-path guard green today.*
- **E7** — WHEN the SSM switch read fails and the gate fails closed, the system
  SHALL log a warning naming the parameter and no credential. Implements:
  NFR-AI-01, NFR-OBS-01 (+ `docs/architecture.md` §6 "use logging").
- **E8** — WHEN an `AiProviderError` is turned into a `failed` result (single
  recipe or week slot), the system SHALL log a warning carrying the error
  text. Implements: FR-AI-01, FR-AI-03, NFR-OBS-01.

## Fix design

| # | File (layer) | Change |
|---|---|---|
| 1 | `docs/local_development.md` §2 / §3 | §2 api block: `export AI_PROMPT_VERSION_ID=v3`. §3 worker block: `export AI_GENERATION_ENABLED=true`, plus one sentence each (FR-AI-14 no default; override is local-only, SSM unread). Line 20's "works end-to-end" claim then holds. |
| 2 | `backend/lambda_ai/src/planner_ai/local_worker.py` (dev-only entry point) | New `build_local_dependencies() -> Dependencies`: `wiring.build_dependencies()` with `gate` replaced by a fixed-value gate **only** when the env value is exactly `"true"`/`"false"`; otherwise returned unchanged. `main()` builds it once and `_poll_once` passes it to `handle(event, deps)`. |
| 3 | `backend/lambda_ai/src/planner_ai/adapters/ssm.py` (adapter) | In the `except` that fails closed, `logger.warning(...)` with the parameter name and the exception type/code. No credential values. |
| 4 | `backend/core/src/planner_core/application/single_recipe_generation.py:79`, `week_generation.py:96` (application) | `logger.warning(...)` with the idempotency key and `str(exc)` in the `except AiProviderError` branches. stdlib `logging` only: no new dependency, `core` stays stdlib-only (`architecture.md` §6). |
| 5 | `.vscode/launch.json` (the owner's gitignored file) | **Owner edit:** "ai: local worker" `env` gets `"AI_GENERATION_ENABLED": "true"` (the api entry already has `AI_PROMPT_VERSION_ID`). |

Why it can't weaken the deployed kill-switch: the Lambda entry point
(`handler.handle` -> `wiring.build_dependencies()`) never reads the variable. Only
`local_worker.py` reads it, and that file already refuses to start outside
local-emulator mode (`_require_local_env`). Only exact strings count, so a typo
falls back to SSM rather than enabling generation.

Rejected alternatives:

- **Override inside `wiring.build_dependencies()` or `SsmGenerationGate`.** That
  is the deployed path: setting the variable on the Lambda would bypass the
  NFR-AI-01 enforcing path (G-70) that infra flips through SSM. E6's deployed
  guard forbids it.
- **Log only in `BedrockAiProvider` before raising.** That keeps `core`
  logging-free, but it misses the idempotency key and any other provider. If the
  human rules that `core` must not log, E8 needs a re-triage (open question 2).

## Test plan

| Staged (`issues/ai-generation-422-unavailable/tests/…`) | Destination |
|---|---|
| `backend/lambda_api/tests/test_local_development_env.py` | same path under repo root |
| `backend/lambda_ai/tests/test_local_worker_gate.py` | same |
| `backend/lambda_ai/tests/test_ssm_gate_logging.py` | same |
| `backend/core/tests/application/test_provider_error_logging.py` | same |

| Test | E | Red at triage (2026-10-07) |
|---|---|---|
| `test_documented_api_env_selects_a_registered_prompt_version` | E1 | red: §2 has no export |
| `test_single_recipe_generation_is_accepted_under_the_documented_env` | E1 | red: 422 UNKNOWN_PROMPT_VERSION |
| `test_week_generation_is_accepted_under_the_documented_env` | E2 | red: same 422 |
| `test_an_unset_prompt_version_still_fails_without_a_silent_default[recipe,week]` | E3 | green (guard) |
| `test_documented_worker_env_enables_generation_locally` | E4 | red: §3 has no `AI_GENERATION_ENABLED` |
| `test_override_true_enables_the_local_worker_whatever_ssm_says` (**reproduction** of `generation_unavailable`) | E5 | red: no override exists (`build_local_dependencies` missing) |
| `test_override_false_disables_the_local_worker_whatever_ssm_says` | E5 | red: same |
| `test_anything_but_exact_true_or_false_leaves_the_ssm_switch_in_charge` ×12 | E6 | red: same seam missing |
| `test_the_deployed_wiring_ignores_the_override` | E6 | green (guard) |
| `test_a_failed_switch_read_fails_closed_with_a_warning[no-creds,denied]` | E7 | red: returns False, no warning logged |
| `test_single_recipe_provider_error_is_logged` | E8 | red: `failed` recorded, no warning |
| `test_week_slot_provider_error_is_logged` | E8 | red: no warning |

Totals: **22 failed, 3 passed**. The 22 failures are the missing behaviour and
the 3 passes are the guards. The api test file was also checked against a
simulated doc fix: all its tests passed. `ruff check`/`format` clean; mypy flags
only the not-yet-existing `build_local_dependencies`. SSM is moto-backed, so
nothing goes over the network.
