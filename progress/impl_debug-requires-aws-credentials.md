# debug-requires-aws-credentials — implementation report

## Traceability

`NFR-SEC-01 → E<n> → T<n> → test`

| NFR-SEC-01 | E<n> | T<n> | Test |
|---|---|---|---|
| least-privilege IAM (no generic AWS key required for local emulator traffic) | E1 — SQS local client signs without ambient chain | T3 | `test_the_local_sqs_client_signs_without_ambient_aws_credentials`, `test_the_worker_polls_when_only_a_bedrock_api_key_is_configured` |
| " | E2 — DynamoDB local client/resource sign without ambient chain | T2 | `test_the_local_dynamodb_client_signs_without_ambient_aws_credentials` |
| " | E3 — real-AWS DynamoDB client still requires real credentials | T2 (guard: only inject placeholders when `_ENDPOINT_URL` is set) | `test_the_real_aws_dynamodb_client_still_requires_real_credentials` |
| " | E4 — fail fast with one log line when neither Bedrock auth exists | T4 | `test_the_worker_fails_fast_when_no_bedrock_credential_is_configured` |

All 4 `E<n>` covered; all 5 staged tests map to at least one `E<n>`.

## Root cause and fix

`_table.py`'s `resource()`/`client()` and `local_worker.py`'s `_sqs()` left
credential resolution to boto3's default chain even when `endpoint_url` was
overridden for the local emulators. Fixed by adding a `_local_credentials()`
helper to each module — returns static `local`/`local` placeholder
credentials **only when `_ENDPOINT_URL` is truthy**, read at call time (same
pattern as the existing `_ENDPOINT_URL`/`_CONFIG` module attributes, so tests
patching them via `monkeypatch.setattr` take effect) — and spreading its
result into the `boto3.resource`/`boto3.client` calls.

`main()`'s `NoCredentialsError` branch (whose premise — "Bedrock requires
[generic credentials] regardless of local mode" — `analysis.md` verified
false) is replaced by `_require_bedrock_auth()`, called before either
emulator client is built: passes if `AWS_BEARER_TOKEN_BEDROCK` is set: else
requires `boto3.Session().get_credentials()` to resolve, else one
`logger.error` line + `SystemExit(1)`. `ProfileNotFound`/`ClientError`
branches untouched, per plan.md.

`docs/local_development.md` §3 updated: the "Do NOT set
AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY" block and the closing fail-fast
paragraph now say a Bedrock API key alone is sufficient and that
DynamoDB/SQS traffic signs with built-in placeholders. `.vscode/launch.json`
untouched (gitignored, owner-owned, per plan.md).

## Test result — red before, green after

Reproduction command: `cd backend && uv run pytest lambda_ai/tests/test_local_worker.py -q`

- **Before the fix** (staged test moved verbatim to its destination,
  application code untouched): `4 failed, 1 passed` — the 4 failures matched
  `analysis.md`'s stated cause exactly: `NoCredentialsError` at
  `botocore/auth.py:429` for the two signing tests and the reproduction test
  (`main()`-level), `Failed: DID NOT RAISE SystemExit` for the fail-fast
  test. `test_the_real_aws_dynamodb_client_still_requires_real_credentials`
  was green already (regression guard, must stay green).
- **After the fix**: `5 passed`.

Full backend suite: `cd backend && uv run pytest -q -m "not aws and not
docker"` — **816 passed**, no regression. `uv run ruff format --check .` /
`uv run ruff check .` / `uv run mypy .` — all clean. `./init.sh` — fully
green (§4's guardrails report the expected `in_progress`/`approved` mix
across `issue_list.json`, unrelated to this fix).

## Scope check

Only `backend/lambda_ai/src/planner_ai/adapters/dynamo/_table.py`,
`backend/lambda_ai/src/planner_ai/local_worker.py`,
`backend/lambda_ai/tests/test_local_worker.py` (new, moved verbatim from
`issues/debug-requires-aws-credentials/tests/...`, byte-identical — verified
via `diff`) and `docs/local_development.md` changed. `lambda_api` untouched
per `analysis.md`'s blast-radius note (its local env already uses
`local`/`local` placeholder credentials). `issue_list.json`/
`feature_list.json` not touched by this session — the `issue_list.json` diff
present in the working tree pre-dates this session (status flips already in
place at session start, confirmed against the conversation's initial git
status snapshot).

`issues/debug-requires-aws-credentials/tasks.md` — all T1–T7 ticked.

## Round 2 — reviewer CHANGES_REQUESTED (4 findings), all fixed

1. **E2 coverage gap (mutant survivor)** — only `client()` had a test;
   `resource()` did not. Added
   `test_the_local_dynamodb_resource_signs_without_ambient_aws_credentials`
   (`backend/lambda_ai/tests/test_local_worker.py`): signs `_table.table().get_item(...)`
   (which calls `resource()`) through the `before-send` hook under
   `no_ambient_credentials` + `local_mode`. Additive; no existing assertion touched.
2. **E4 credential-chain fallback untested (mutant survivor)** — added
   `test_the_worker_polls_when_a_credential_chain_is_configured_without_a_bedrock_key`:
   no `AWS_BEARER_TOKEN_BEDROCK`, `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` set
   on top of `no_ambient_credentials`; asserts `main()` reaches `_poll_once`
   (no `SystemExit`). Additive.
3. **Stale comment**, `local_worker.py` (was lines 34-35) — removed the
   reference to the deleted `NoCredentialsError` branch; `_AUTH_ERROR_CODES`
   comment now states only what the constant is for.
4. **Comment ceiling** — trimmed the 4-line docstrings at `_table.py`
   `_local_credentials()`, `local_worker.py` `_require_bedrock_auth()` and
   `local_worker.py` `_local_credentials()` to 3 lines each; still point at
   `issues/debug-requires-aws-credentials/analysis.md` rather than reproducing it.

### Re-verification

- `cd backend && uv run pytest lambda_ai/tests/test_local_worker.py -q` → `7 passed` (5 staged + 2 new).
- `cd backend && uv run pytest -q -m "not aws and not docker"` → `818 passed, 8 deselected` (was 816; +2 new tests, no regression).
- `uv run ruff format --check .` / `uv run ruff check .` / `uv run mypy .` — all clean.
- `./init.sh` — fully green.

No staged test's existing assertions were edited, loosened or removed; only
new test functions were added.
