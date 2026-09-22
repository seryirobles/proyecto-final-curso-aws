# debug-requires-aws-credentials — analysis

## Defect, one sentence

The `ai` local worker builds its DynamoDB Local / ElasticMQ clients from the
ambient AWS credential chain, so with only a Bedrock API key configured the
first emulator call fails to sign and the process exits — even though
`AWS_BEARER_TOKEN_BEDROCK` already authenticates the one call that leaves the
machine.

## Reproduction

Exactly the "Debug: full stack" `ai: local worker` environment
(`.vscode/launch.json`: the three local endpoint vars +
`AWS_BEARER_TOKEN_BEDROCK`, deliberately no `AWS_ACCESS_KEY_ID`/
`AWS_SECRET_ACCESS_KEY`), with no credential file reachable:

```bash
cd backend/lambda_ai
AWS_SHARED_CREDENTIALS_FILE=<nonexistent> AWS_CONFIG_FILE=<nonexistent> \
DYNAMODB_ENDPOINT_URL=http://localhost:8000 \
SQS_ENDPOINT_URL=http://localhost:9324 \
GENERATION_QUEUE_URL=http://localhost:9324/000000000000/generation-queue \
AWS_DEFAULT_REGION=eu-south-2 AI_MODEL_ID=global.openai.gpt-5.6-terra \
AWS_BEARER_TOKEN_BEDROCK=<key> ../.venv/Scripts/python.exe -m planner_ai.local_worker
```

Observed (exit code 1, both containers up and healthy):

```
ERROR:planner_ai.local_worker:No AWS credentials found. Configure real AWS
credentials (aws configure, environment variables, or SSO) before running the
local worker — Bedrock requires them regardless of local mode.
```

Expected: the worker starts polling `generation-queue`; AI generation works
end-to-end with the Bedrock API key as the only AWS credential.

The message's premise was checked directly (same empty-credential
environment, botocore 1.43.83): a `bedrock-runtime` request **signs** with
only `AWS_BEARER_TOKEN_BEDROCK` set (it reaches the connection stage), while
`sqs` and `dynamodb` requests raise `NoCredentialsError` at signing. And with
explicit placeholder keys (`local`/`local`) both emulators answer normally
(`sqs.receive_message` -> empty, `dynamodb.list_tables` -> `["data"]`). So
Bedrock does **not** require generic credentials; only the two local-emulator
clients do.

## Root cause

`backend/lambda_ai/src/planner_ai/local_worker.py:58` (`_sqs()`) and
`backend/lambda_ai/src/planner_ai/adapters/dynamo/_table.py:48-59`
(`resource()`, `client()`) override `endpoint_url` for local mode but leave
credential resolution to boto3's default chain. `main()` then calls
`create_data_table()` (`local_worker.py:95`), whose `CreateTable` is the first
request to be signed, and the `NoCredentialsError` branch at
`local_worker.py:96-105` turns that into `SystemExit(1)` with a message whose
justification — "Bedrock requires them regardless of local mode" — is false
once `AWS_BEARER_TOKEN_BEDROCK` is set. The symptom surfaces in that branch;
the cause is the two client factories signing local-emulator traffic with
credentials that only real AWS needs.

The same false premise is written into `docs/local_development.md` §3
(lines 101-113, 133-143), which is why the worker was built this way: the
Bedrock API key was added to the doc and to `.vscode/launch.json` without the
emulator clients being given credentials of their own.

## Blast radius

- **Same process, second path:** even if startup is survived (a developer with
  ambient credentials), every generation write goes through the same `_table`
  factories. A bearer-token-only developer would get a `NoCredentialsError`
  per record inside `handle()`, logged and skipped — a silently non-functional
  AI flow rather than a startup failure.
- **`lambda_api`** (`adapters/dynamo/_table.py`, `adapters/sqs.py`) shares the
  pattern but is not affected in practice: its documented local environment and
  its launch config both export `AWS_ACCESS_KEY_ID=local` /
  `AWS_SECRET_ACCESS_KEY=local`, which is exactly the placeholder this issue
  asks the `ai` side to stop demanding from the developer. Out of scope; no
  change proposed there.
- **Deployed Lambda:** `_table` is the real adapter, so the fix must be scoped
  to `_ENDPOINT_URL` being set. In real-AWS mode a missing credential must keep
  failing loudly rather than signing with a placeholder (regression test
  `test_the_real_aws_dynamodb_client_still_requires_real_credentials`).
- **Fast-fail behaviour:** removing the `NoCredentialsError` branch alone would
  lose the documented "one clear log line" for a developer who has configured
  *no* Bedrock auth at all (`docs/local_development.md` §3, last paragraph);
  that check has to be re-expressed against Bedrock auth rather than against
  the emulator clients (E4).
- Docker/moto test tiers are unaffected: the docker tier already exports
  placeholder credentials, and the moto tier runs with `_ENDPOINT_URL` unset.

## Classification

`defect`.

Caveat, stated plainly: the local dev tooling is not a product feature
(`docs/local_development.md`, first line) and no `FR-*` describes it. The
citable requirement is **`NFR-SEC-01` (least-privilege IAM)** — the reason the
repo itself already gives for preferring a Bedrock-scoped API key over an IAM
key pair, in `docs/local_development.md` §3 and in `.vscode/launch.json`'s
comments. The code defeats that preference by making a generic credential
mandatory anyway. Nothing here needs a new requirement or a lift of a frozen
doc, and no `G-xx` sanctions the current behaviour; the fix only makes the
tooling do what its own doc promises. If the human judges `NFR-SEC-01` not to
reach dev tooling, this is still a defect against `docs/local_development.md`
§3 — the go/no-go is theirs either way.
