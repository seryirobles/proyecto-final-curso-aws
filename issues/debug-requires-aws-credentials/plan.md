# debug-requires-aws-credentials — plan

## Expected behaviour

- **E1** — WHEN `SQS_ENDPOINT_URL` is set, the `ai` local worker SHALL sign its
  SQS requests without resolving the ambient AWS credential chain.
  *Implements: NFR-SEC-01.*
- **E2** — WHEN `DYNAMODB_ENDPOINT_URL` is set, `planner_ai`'s DynamoDB client
  and resource SHALL sign their requests without resolving the ambient AWS
  credential chain. *Implements: NFR-SEC-01.*
- **E3** — WHERE `DYNAMODB_ENDPOINT_URL` is unset, `planner_ai`'s DynamoDB
  client SHALL resolve its credentials from the AWS credential chain and raise
  `NoCredentialsError` when that chain is empty. *Implements: NFR-SEC-01.*
- **E4** — WHEN neither `AWS_BEARER_TOKEN_BEDROCK` nor a resolvable AWS
  credential chain is configured, the `ai` local worker SHALL log one error
  line and exit with status 1 before polling. *Implements: NFR-SEC-01 — keeps
  the documented fast-fail (`docs/local_development.md` §3) that E1/E2 would
  otherwise silently remove.*

## Fix design

Layer: `lambda_ai` adapter + its dev-only entry point
(`docs/architecture.md` §3 — nothing in `core` changes, no new dependency).

1. `backend/lambda_ai/src/planner_ai/adapters/dynamo/_table.py` — `resource()`
   and `client()` pass static placeholder credentials
   (`aws_access_key_id="local"`, `aws_secret_access_key="local"`) **only when
   `_ENDPOINT_URL` is truthy**, alongside the `endpoint_url`/`config` override
   they already apply. Resolve them at call time from the module attribute,
   exactly as `_ENDPOINT_URL`/`_CONFIG` are read today — the tests patch those
   attributes, per `lambda_api/tests/_docker_fixtures.py`.
2. `backend/lambda_ai/src/planner_ai/local_worker.py` — `_sqs()` does the same
   for the ElasticMQ endpoint.
3. `backend/lambda_ai/src/planner_ai/local_worker.py` — replace the
   `NoCredentialsError` branch in `main()` (now unreachable from the emulator
   clients) with an explicit Bedrock-auth check that runs **before** the
   clients are built: no `AWS_BEARER_TOKEN_BEDROCK` **and**
   `boto3.Session().get_credentials() is None` -> one `logger.error` line
   naming both options, `raise SystemExit(1)`. Leave the `ProfileNotFound` and
   `ClientError` branches as they are.
4. `docs/local_development.md` §3 — correct the now-false claims: the "Do NOT
   set AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY" block and the closing
   paragraph's "if no AWS credentials are configured at all" must say that a
   Bedrock API key alone is sufficient and that DynamoDB/SQS traffic is signed
   with built-in placeholders. Do **not** touch `.vscode/launch.json` — it is
   gitignored and owner-owned.

Rejected alternatives:

- **Export placeholder `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` into
  `os.environ` at worker startup.** One line, but process-global: it shadows a
  developer's profile/SSO chain, so the documented fallback ("prefer your
  normal AWS credential chain instead") would break the Bedrock call with a
  signature error instead of working.
- **Document `AWS_ACCESS_KEY_ID=local` for the `ai` worker too and change no
  code.** Restores the fast path but re-introduces the shadowing above for the
  credential-chain fallback, and leaves the worker unable to run on a
  Bedrock-scoped key alone — the very thing `NFR-SEC-01` motivated.

## Test plan

| Staged file | Destination |
|---|---|
| `issues/debug-requires-aws-credentials/tests/backend/lambda_ai/tests/test_local_worker.py` | `backend/lambda_ai/tests/test_local_worker.py` |

Moved verbatim. No existing test file changes.

| Test | Covers | Result at triage |
|---|---|---|
| `test_the_local_sqs_client_signs_without_ambient_aws_credentials` | E1 | **RED** — `NoCredentialsError` at `botocore/auth.py:429` |
| `test_the_local_dynamodb_client_signs_without_ambient_aws_credentials` | E2 | **RED** — `NoCredentialsError` at `botocore/auth.py:429` |
| `test_the_worker_polls_when_only_a_bedrock_api_key_is_configured` | E1 (reproduction, `main()` level) | **RED** — the client `main()` built raises `NoCredentialsError` |
| `test_the_real_aws_dynamodb_client_still_requires_real_credentials` | E3 (blast-radius regression) | **GREEN** today, must stay green |
| `test_the_worker_fails_fast_when_no_bedrock_credential_is_configured` | E4 | **RED** — `DID NOT RAISE SystemExit` |

No test touches the network: a `before-send` hook raises a sentinel once the
request is signed, so signing success/failure is observed without a socket.
Ambient credentials are removed per test (env vars, a `tmp_path` credentials/
config file, metadata disabled, `boto3.DEFAULT_SESSION` reset), which is what
makes the tests meaningful under `core/tests/conftest.py`'s process-wide
`AWS_ACCESS_KEY_ID=testing`.

Command and observed result at triage (file copied to its destination, then
deleted again):

```
cd backend && uv run pytest core/tests lambda_ai/tests -q
4 failed, 560 passed
```

`ruff format --check`, `ruff check` and `mypy` all pass on the staged file at
its destination.

Manual check after the fix (not automatable — needs the containers and a real
key): the reproduction command in `analysis.md` logs
`planner_ai local worker polling http://localhost:9324/...` instead of exiting.
