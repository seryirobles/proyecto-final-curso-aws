# Local development

This is dev tooling, not a product feature — there is no `feature_list.json`
entry or spec for it. Everything runs on your own machine except AWS
Bedrock itself, which can't be emulated locally: DynamoDB, the `api` Lambda,
the SQS queue between `api` and `ai`, the `ai` Lambda, and the SPA are all
local. Only the actual Bedrock `InvokeModel` call reaches real AWS.

## Two DynamoDB modes

| Mode | `DYNAMODB_ENDPOINT_URL` |
|---|---|
| **Local emulator** | Set to the local DynamoDB Local endpoint |
| **Real AWS table** | Unset |

Unset (or empty) `DYNAMODB_ENDPOINT_URL` is a true no-op — the DynamoDB
adapter in both `lambda_api` and `lambda_ai` falls back to boto3's normal
AWS resolution, identical to the real deployment. `SQS_ENDPOINT_URL` on
`lambda_api`'s SQS adapter works the same way. The AI generation flow works
end-to-end in local-emulator mode now (it didn't in an earlier version of
this doc) — the only piece that ever leaves your machine is the Bedrock
call itself.

## 1. DynamoDB Local + SQS Local

```bash
docker compose up -d
```

Starts two containers:
- `amazon/dynamodb-local` on `localhost:8000`, **in-memory** — data does not
  survive a container restart (the image's non-root user can't write into a
  Docker Desktop named volume on Windows; `-inMemory` sidesteps that
  entirely). The local server/worker below auto-provision the table on every
  startup when `DYNAMODB_ENDPOINT_URL` is set.
- `softwaremill/elasticmq-native` (SQS-compatible) on `localhost:9324`,
  configured by `elasticmq.conf` at the repo root, which **declaratively**
  pre-creates the `generation-queue` — it exists the instant the container
  starts, no bootstrapping call needed.

Run the Docker-backed live tests with `cd backend && uv run pytest -m docker`
(they skip cleanly if the containers aren't running).

The `docker_dynamodb` fixture (`lambda_api/tests/_docker_fixtures.py`) is
function-scoped: it patches `_table`'s module-level endpoint/config directly,
and only `monkeypatch`'s per-test auto-revert guarantees that patch doesn't
leak into whichever moto-backed contract test runs next in the same process.
Session scope would leave that state bleeding across tests.

## 2. The local `api` Lambda server

`backend/lambda_api/src/planner_api/local_server.py` wraps the real
`handler.py`/`authorizer.py` in a stdlib HTTP server — same routing, same
auth gate, same responses a real deployment would give, just without API
Gateway/a VPC in front.

```bash
cd backend/lambda_api

export DYNAMODB_ENDPOINT_URL=http://localhost:8000
export SQS_ENDPOINT_URL=http://localhost:9324
export GENERATION_QUEUE_URL=http://localhost:9324/000000000000/generation-queue
export AWS_ACCESS_KEY_ID=local
export AWS_SECRET_ACCESS_KEY=local
export AWS_DEFAULT_REGION=us-east-1
export SESSION_SECRET_KEY=<any string — signs the session cookie's HMAC>

uv run python -m planner_api.local_server
```

`build_dependencies()` constructs the whole dependency graph eagerly, so
`SESSION_SECRET_KEY` and `GENERATION_QUEUE_URL` are both required for
**every** request, not just login or AI generation respectively. `AWS_*`
here can be any placeholder — nothing this process touches leaves your
machine.

Real-AWS-table mode instead: leave `DYNAMODB_ENDPOINT_URL`/`SQS_ENDPOINT_URL`
unset, export real AWS credentials, set `PLANNER_DATA_TABLE`/
`GENERATION_QUEUE_URL` to the real resources' names.

Listens on `localhost:8080` by default (`LOCAL_SERVER_PORT` to change it).

## 3. The local `ai` worker

`backend/lambda_ai/src/planner_ai/local_worker.py` stands in for the real
SQS→Lambda trigger — there's no real Lambda runtime here to deliver batches
automatically, so it long-polls the local queue itself, builds the same
`{"Records": [...]}` event shape a real trigger would, and calls the real
`handler.py`'s `handle()`. Same per-record exception isolation as
production: one bad message is logged and skipped, the poller keeps running.

```bash
cd backend/lambda_ai

export DYNAMODB_ENDPOINT_URL=http://localhost:8000
export SQS_ENDPOINT_URL=http://localhost:9324
export GENERATION_QUEUE_URL=http://localhost:9324/000000000000/generation-queue
export AWS_DEFAULT_REGION=eu-south-2
export AI_MODEL_ID=global.openai.gpt-5.6-terra

# Do NOT set AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY here to fake values —
# this process's Bedrock client needs real AWS auth. Prefer a scoped
# Bedrock API key over full IAM access keys (NFR-SEC-01, least privilege):
# generate one in the Bedrock console, then:
export AWS_BEARER_TOKEN_BEDROCK=<your Bedrock API key>
# `boto3` reads this env var natively — no code change, works with
# `.converse()`. It authorizes Bedrock/Bedrock Runtime actions only,
# unlike an IAM access key pair which may carry whatever else that
# identity has. If you'd rather use your normal AWS credential chain
# instead (`aws configure` / SSO / a named profile), that still works —
# just don't hardcode IAM access keys here for this process specifically.
# DynamoDB/SQS still route locally via the endpoint overrides above either
# way; only the Bedrock call itself reaches real AWS.

uv run python -m planner_ai.local_worker
```

**One-time AWS Marketplace activation, before the first real invocation.**
GPT-5.6 Terra is AWS-Marketplace-listed (it carries a Marketplace product
id on its model card), not one of Amazon's own auto-enabled serverless
models — Bedrock's retired "Model access" page's replacement text is
explicit about the distinction: *"For models served from AWS Marketplace,
a user with AWS Marketplace permissions must invoke the model once to
enable it account-wide for all users."* Someone with Marketplace
permissions on the account needs to invoke it once (the Bedrock console
playground is the easiest way) before `local_worker.py`'s own `Converse`
calls will succeed — skip this and the first real invocation fails with a
subscription/access error, not the credentials error covered above.

See `docs/architecture.md` §1.2.6 for the full provider decision (why
`Converse`/`eu-south-2`/no EU data-residency guarantee for this model).

Fails with one clear log line (not a raw traceback) if no AWS credentials
are configured at all, if your AWS profile/token is invalid, **or if
`DYNAMODB_ENDPOINT_URL`/`SQS_ENDPOINT_URL`/`GENERATION_QUEUE_URL` aren't all
set** — this script only ever supports local-emulator mode, deliberately,
with no override. Since it carries real AWS credentials (for Bedrock),
letting it silently fall through to real AWS DynamoDB/SQS on a missing env
var would be a real hazard, unlike the `api` side's fake `local`/`local`
credentials, which AWS itself would reject. A generation request that
reaches the Bedrock call without real Bedrock access will fail there
specifically, logged and skipped, same as any other per-record failure —
the rest of the app keeps working regardless.

## 4. Seed test accounts

`backend/lambda_api/src/planner_api/seed_local_data.py` seeds 4 accounts for
manual testing — one of each role with a real password already set, one of
each with password-reset still pending (to exercise the mandatory
set-password prompt):

```bash
cd backend/lambda_api
export DYNAMODB_ENDPOINT_URL=http://localhost:8000   # same env as the local server above
uv run python -m planner_api.seed_local_data
```

| Username | Role | Password state | Password |
|---|---|---|---|
| `user1` | user | set | `UserActive1234` |
| `user2` | user | pending | `TempPass1234` |
| `admin1` | admin | set | `AdminActive1234` |
| `admin2` | admin | pending | `TempPass1234` |

Runs automatically as part of the VS Code "Debug: full stack" launch (§6) —
you don't need the command above unless you're running outside VS Code.

Safe to re-run — already-seeded accounts are reported and skipped (an
"active" account still gets its `set_password` step retried if a prior run
was interrupted before completing it). Since DynamoDB Local is in-memory
(§1), you'll re-run this after every container restart.

**Real AWS table mode is more restricted here than for the API server above.**
`DYNAMODB_ENDPOINT_URL` unset means "real AWS" — `--force`/`SEED_FORCE=1`
lets the two *User* accounts seed there (for testing that flow against a
real table), but the two *Admin* accounts are **always skipped** in that
mode, no override exists. Nobody should be able to one-flag their way into
creating a real Admin account with a password printed in this file.

The two admin accounts are written directly via the repository, not through
the app's own account-creation code — the real app has no code path to
create an Admin account at all, by design (`backend/core/src/planner_core/
application/account_admin.py`'s `create_user` is hardcoded to the `User`
role; admin accounts are meant to be provisioned outside the app, same as a
real deployment would via IaC re-seed). This script fills that role for
local dev only.

## 5. The SPA

```bash
cd frontend
npm run dev
```

`vite.config.js` proxies `/v1/*` to `http://localhost:8080`, so the browser
sees the SPA and the API as the same origin — required for the session
cookie's `SameSite=Lax`/`Secure` attributes to work (see
`docs/rest_api_contract.md`). Note: browsers only special-case `Secure`
cookies over plain HTTP for the literal hostname `localhost` — open the dev
server at `http://localhost:5173`, not `http://127.0.0.1:5173`, or login
won't persist a session.

## 6. All of the above in one go — VS Code

`.vscode/launch.json`'s **"Debug: full stack (DynamoDB + SQS + api + ai +
SPA)"** compound runs everything above from one Run & Debug entry: `docker
compose up -d` (§1) → seed the 4 test accounts (§4) → debug
`local_server.py` and `local_worker.py` with breakpoints in the real
handler/authorizer/generation code → launch the SPA in a debuggable Chrome
instance proxied to it. `.vscode/` is gitignored, so its env values are
yours to edit freely — see the comments in `launch.json` for switching to
real-AWS-table mode, and note the "ai: local worker" config deliberately
carries no fake AWS credentials (§3) — configure your real ones on your
machine before launching it, or that one process will fail fast and loud
until you do; everything else in the compound works regardless.
