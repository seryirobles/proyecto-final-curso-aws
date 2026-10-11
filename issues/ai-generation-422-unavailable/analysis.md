# Analysis — ai-generation-422-unavailable (issue 13, re-scoped 2026-10-07)

## Defect, one sentence
The documented local setup never turns AI generation on. Without `AI_PROMPT_VERSION_ID` the `api` answers the submit with a 422. Once that is set, the worker reads the SSM kill-switch with no AWS credentials, the read fails closed, and it records `generation_unavailable` without logging why.

## Reproduction
1. **Submit stage:** the real handler with `EnvConfig()` and the frontend's own request body. Unset: `422 UNKNOWN_PROMPT_VERSION`, with the reported message word for word. Set to `v3`: `202`. The payload is identical in both runs.
2. **Worker stage** (owner's evidence after setting the variable): the local DynamoDB record holds `estado=failed`, code `generation_unavailable`. The worker log has no line about it.
3. **Staged tests:** `test_override_true_enables_the_local_worker_whatever_ssm_says` fails before the fix, and `test_a_failed_switch_read_fails_closed_with_a_warning` shows the fail-closed happens with no log.

## Root cause
- **Submit:** `planner_core/application/prompt_version.py:22` raises, and `errors.py:141` turns it into a 422. That behaviour is specified (FR-AI-14, G-84, ai_prompt_versioning R4). The cause is configuration: `docs/local_development.md` §2 and the owner's `.vscode/launch.json` both left the variable out.
- **Worker:** `planner_ai/adapters/ssm.py` (`SsmGenerationGate.is_generation_enabled`) reads `/planner/dev/ai-generation-enabled` from real SSM in eu-south-2. The local worker carries only `AWS_BEARER_TOKEN_BEDROCK`, so boto3 raises `NoCredentialsError`, a `BotoCoreError`. The `except` sets `enabled = False` and logs nothing. `single_recipe_generation.py:67` then records GENERATION_UNAVAILABLE (ai_lambda R22). Failing closed is itself specified (NFR-AI-01, ai_lambda R16–R19, design §5). The problem is that the local tooling never gives the worker a switch it can read, which contradicts the doc's "everything local except Bedrock" principle.
- **No log of the cause:** the fail-closed branch in `ssm.py` and the `except AiProviderError` blocks in `single_recipe_generation.py` and `week_generation.py` turn errors into `failed` results without logging them.
- **The frontend hides nothing:** it shows the server's `detail` / `result.error.message` as-is.

## Blast radius
- **Whole-week generation** has the same 422 at submit (`generation_submission.py:60`), the same gate and the same unlogged provider errors. Included (E2, E8) by owner decision.
- **Deployed `ai` Lambda:** the override cannot affect it; only `local_worker.py` reads the variable. The deployed paths gain the E7/E8 warnings (owner accepted).
- **Deployed `api` Lambda:** nothing in the repo sets `AI_PROMPT_VERSION_ID`. Owner: it will be set; out of scope for now.

## Classification
`not_a_defect` against FR-AI-* and NFR-AI-01: the 422 is FR-AI-14 working as designed, and failing closed on an unreadable switch is NFR-AI-01 working as designed. The fix is dev tooling plus logging (NFR-OBS-01, `architecture.md` §6).
