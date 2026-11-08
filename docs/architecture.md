# Architecture — What "doing a good job" means here

> This document defines the quality bar. Reviewer agents evaluate code against
> this file. **If it is not in here, it is not a requirement.**
>
> **Architecture is owned by the human.** §1 lists what is decided. §2 lists what
> is not. An agent that needs something from §2 marks the feature `blocked` and
> stops — it never decides.

---

## 1. Decided

### 1.1 Frontend

- A **single-page application**, responsive, desktop + mobile (`FR-UX-02`).
- **React, written idiomatically: function components and hooks, with JSX.**
  Built with **Vite**, tested with **Vitest**, formatted and linted with
  **Prettier + ESLint**. Plain JavaScript, ESM — no TypeScript.
- **State and markup are separated like backend layers**: a **custom hook** owns
  state, handlers and API calls; the **component** is a pure function of its
  props. Full rules in `docs/conventions.md` § *Frontend conventions*.
- Styling is **inline `style` objects** referencing a shared tokens module. **No
  stylesheet, no CSS framework, no CSS-in-JS library** — see `conventions.md`.

#### Formerly P7 — decided by the human 2026-08-17

The frozen requirements never named a frontend framework; earlier drafts of this
section said "a **React-based DC framework**", pinned down from *"the human's
initial version of the frontend code"*.

**Both halves of that turned out to be unobtainable.** "DC" was Claude Design's
own authoring runtime (`.dc.html`, `<x-dc>`, a generated `support.js` marked *do
not edit*) — an Anthropic-internal format, not a framework anyone can install.
And the initial code drop **already happened**: it *is* the prototype now in
`prototypes/wireframe/`, which `docs/frontend_prototype.md` establishes is not
portable. So P7 could never have been resolved the way this document described.

The human decided it outright instead. **Idiomatic React was chosen over keeping
the prototype's class-and-`createElement` shape for one reason: reachable help.**
Every tutorial, answer and assistant assumes hooks and JSX; the alternative is a
legacy style whose answers all need translating first. Same reasoning that chose
Prettier + ESLint over Biome.

What this does **not** change: inline CSS with a tokens module, the single es-ES
messages module, no business logic in the client, and fluid-first layout with
`matchMedia`. Those were never DC-specific.
- **No business logic in the client.** Week boundaries, scoping, aggregation and
  rule satisfiability live in `backend/core` (`planner_core.domain`). The SPA
  displays results.
- All UI text in **Castilian Spanish** (`FR-UX-01`, `FR-UX-03`), centralised in
  one messages module, with `Intl` pinned to `es-ES`.
- Inline CSS cannot express `@media` queries, so layout is **fluid-first**
  (flex/grid, `clamp()`, `minmax()`); genuine breakpoints go through
  `matchMedia` and become state. See `docs/conventions.md`.
- ~~The human supplies the **initial version of the frontend code**. Until it
  exists, no agent writes frontend code (`frontend_spa` is `blocked`).~~
  **Superseded 2026-08-17** — the drop already happened and was the prototype.
  `frontend_spa` (feature 20) now depends only on **feature 16** (the REST
  contract, §1.2.5) and **feature 26** — no architecture decision blocks it.

### 1.2 Backend

Exactly **two Lambdas**, no more:

| Lambda | Responsibility |
|---|---|
| `api` | Regular backend operations, exposed as a **REST API** |
| `ai`  | AI generation only (single recipe + whole week) |

- Language: **Python**.
- **`api` hands AI work to `ai` over a standard SQS queue** (decided
  2026-08-30, §1.2.6 / `docs/rest_api_contract.md` Q12; previously only in
  `docs/decisiones_arquitectura.md`). `api` enqueues a generation request
  and the client polls for the result; `ai` is a queue-driven worker. This
  is the one queue the design has — a further one still needs an approved
  `design.md` (§6).
- Also on the `api` package: a **non-HTTP entry point for scheduled week
  rollover** (`FR-MENU-06`/`-08`), invoked by EventBridge Scheduler
  (`docs/rest_api_contract.md` Q8) — not a third Lambda.
- Splitting AI generation into its own Lambda is deliberate: AI calls are slow
  (seconds to a minute-plus, `G-19`), cost-capped (`NFR-AI-01`) and need their
  own concurrency and idempotency behaviour (`FR-AI-08`, `FR-AI-09`). Do not
  merge it into `api`, and do not add a third Lambda without human approval.
- The split is **real, not nominal**: each Lambda is its own package with its
  own dependency closure, so the `api` artifact never ships the AI provider SDK
  and never pays its cold-start cost. Packaging is covered in §3.2.

### 1.2.1 Datastore — DynamoDB, single table (was P1)

**Decided by the human 2026-08-16.** Formerly P1.

**Amazon DynamoDB**, in a **single-table design**. One table named `data`, ten
item types, serving all 29 access patterns.

> **Where to read the model and the catalogue.** Both are in
> **`docs/data_model.md`** — the persistence source of truth. The owner authors
> the catalogue in `Desktop/lab-final-patrones-acceso.xlsx`, which is **outside
> the repo and not in git**; do not assume it is present. Work from
> `data_model.md` unless you have the spreadsheet in front of you, in which case
> it wins.

- **No secondary indexes anywhere.** Every access pattern resolves to a
  `GetItem`, a `Query` on a single partition, or a `TransactWriteItems`. No
  index storage, no duplicated writes, no eventual consistency on any path
  including login.
- The authoritative key design, item types and attribute names are
  `docs/data_model.md` **§1**.
- **The key *formats* are §2 of that document and exist nowhere else** —
  `idSemana`, `idPlato`, `numeroDia`, `numeroComida`, `idPeticionIA` and the
  username fold. Four carry a documented trap. Read §2 before writing any
  persistence code.
- Concurrency primitives already settled there and not to be re-derived (§5):
  the `FR-AUTH-17` uniqueness reservation, the rename-releases-its-reservation
  lookup, the `FR-SHOP-10` re-sync lock and its TTL trap, and read-time
  resolution of dangling references.

This closes P1 and unblocks `persistence_ports` (feature 14). DynamoDB TTL
configuration and table provisioning are IaC — feature 21 (§1.2.7);
cold-storage wiring stays parked (`data_model.md` §9).

### 1.2.2 A port's dependency-free default implementation ships with the port

**Decided by the human 2026-08-18.** Not one of the P1–P7 items; raised while
reviewing feature 2 `week_calendar`, where nothing said where a real
`SystemClock` should live.

**Rule.** An implementation of a port that imports **nothing outside the
standard library** lives in `planner_core/ports/`, in the same module as the
`Protocol` it satisfies. It is a **default implementation**, not an adapter.
Only implementations that pull in an external dependency — `boto3`, an AI SDK, an
HTTP client — are adapters, and those live in the Lambda package that owns the
dependency (§3.1 rule 3, unchanged).

**Why.** The ports-and-adapters boundary exists to isolate what **differs by
runtime environment**. Persistence genuinely differs — DynamoDB in production, a
fake in tests. *"What time is it now?"* does not: there is exactly one correct
implementation, identical in every environment, and it will never be swapped.
Java put `Clock` in `java.time` with `Clock.systemUTC()` beside it; .NET 8 put
`TimeProvider.System` in the base class library next to `TimeProvider`. Both had
the option to make the system clock an infrastructure concern and neither took
it. `core`'s **zero runtime dependencies** guarantee is untouched, because a
default implementation by definition adds none.

**The concrete cost this avoids.** Under Lambda ownership, `lambda_api` and
`lambda_ai` would each carry their own copy of a three-line class — two
independent chances to write `datetime.utcnow()`, which returns a **naive**
datetime and is deprecated from 3.12. `planner_core.domain.calendar.civil_date`
rejects naive instants with `NaiveInstant` precisely because that footgun is
real; duplicating the one class that must not trip it is backwards.

**The objection, and how it is answered.** A real clock inside `core` sits within
reach of every `core` test, which §3.1 rule 6 exists to prevent. That is a reason
for a **stronger control, not a different directory**: a directory boundary only
works until someone types the import. `backend/core/tests/test_no_ambient_time.py`
scans the sources mechanically and is **the authority** on both the sanctioned
ambient-time call and which modules may reach for `SystemClock`. Enforcement is
mechanical rather than geographic.

Deliberately not restated here: which call it allows, and which modules it
exempts. This document has already gone stale twice by paraphrasing that guard —
each paraphrase is a claim that must be re-verified whenever the guard changes,
and one of them overstated the very control this paragraph relies on. **Read the
module.**

**What would reverse this.** A `Clock` implementation that needs a real
dependency — time from an AWS service, a distributed clock. Then it is a true
adapter and moves to the Lambda that owns that dependency. Nothing in
`docs/requirements.md` points that way.

### 1.2.3 Auth mechanism — application-managed (was P2)

**Decided by the human 2026-08-27.** Formerly P2.

**Application-managed.** No external identity provider. Credentials
(password hashes), password-reset state and session tokens are owned,
validated and persisted by the application itself, through the
`AccountRepository` port (feature 14) — not delegated to Cognito or any
other managed IdP.

- Keeps `planner_core/domain/{password_policy,username_policy}.py`
  (feature 9, done) as the live validation path. Routing through Cognito
  would have left that domain logic dead or duplicated.
- The application builds, and owns testing, the admin-assigned
  temporary-password force-change flow (`FR-AUTH-10`, `-11`). **Amended by
  `G-87` (2026-08-27):** session tracking was dropped from the MVP —
  `FR-AUTH-16` is a flat 30-day expiry computed from the token alone, no
  sliding inactivity window, no database access for the check itself; and
  login brute-force protection (`NFR-SEC-04`) moved to infrastructure (an
  API Gateway/WAF rate-based rule, feature 21), not application code. See
  `docs/gaps_and_resolutions.md` Part W for the full reasoning.

This closes P2 and unblocks `auth_flow` (feature 15). How the session
token travels (an `HttpOnly` cookie) and how the Lambda authorizer is
wired were settled by P5 — §1.2.5.

### 1.2.4 Real-time transport — adaptive polling with conditional GET (was P3)

**Decided by the human 2026-08-27.** Formerly P3. See
`docs/gaps_and_resolutions.md` Part X / `G-88` for the full analysis and
rejected alternatives.

**Adaptive client-side polling, short-circuited by a conditional GET.**
No WebSocket API, no AppSync, no long polling.

- The frontend re-fetches each pollable resource on an interval that backs
  off when the tab is hidden/blurred and resumes immediately on
  `visibilitychange` back to visible, and backs off further (capped,
  jittered) on repeated failures.
- Every poll carries the last version marker the client holds for that
  resource. The `api` Lambda does a **cheap, strongly-consistent read of
  just the marker** before deciding whether to compute and return the full
  payload — unchanged returns `304 Not Modified` with no body.
- The marker itself, its storage shape (a new `MarcaCambio` item per
  pollable partition), and the amended access patterns are
  `docs/data_model.md` §1/§3/§4 — read those before touching persistence
  for weeks, the library, the shopping list, or the rules.

**Why not WebSocket API Gateway, AppSync, or long polling.** All three were
considered; discussed at length before this decision and recorded in full
in `G-88`. Long polling in particular is a poor fit for this architecture
specifically: API Gateway's integration timeout caps any held-open request
at 29 seconds, and Lambda bills by compute-time, so a connection held open
"waiting" for a change pays for idle compute the whole time it waits — a
worse cost profile than either short polling or a real WebSocket, which
bills by idle connection-*time*, not compute-*time*.

**`FR-RT-03`'s reconnect/resync language maps onto polling almost for
free**, because polling has no connection state to restore in the first
place: "indicate loss" is N consecutive failed polls, "reconnect
automatically" is the timer never stopping, and "re-synchronize state" is
simply the next successful poll — `docs/data_model.md` §9 already noted
this before P3 was decided ("reconnect resynchronisation is re-calling
existing reads").

This closes P3 and unblocks the persistence half of `realtime_channel`
(feature 18). How the marker travels over HTTP was settled by P5
(**`ETag` / `If-None-Match`**, §1.2.5); API Gateway throttling/caching of
poll traffic is a feature 21 infra detail.

### 1.2.5 REST API contract — decided (was P5)

**Decided by the human 2026-08-30.** Formerly P5. The full contract —
resources, verbs, payload shapes, error format, all 29 access patterns
mapped — is **`docs/rest_api_contract.md`**, authoritative for the `api`
Lambda. This section records only the load-bearing shape:

- **Base path `/v1`.** JSON in and out, English `camelCase` keys (Spanish
  is reserved for user-facing strings, mapped at the persistence adapter).
- **Auth transport: `HttpOnly` cookie** (`Secure; SameSite=Lax;
  Max-Age=2592000`), not a bearer header — no per-token revocation exists,
  so XSS token theft dominates. Requires the SPA and API to be
  **same-site**: `/v1/*` routes through the same CloudFront distribution
  that serves the SPA (§1.2.7). A `REQUEST`-type Lambda authorizer runs
  `authenticate()` and passes `userId`/`role`/`passwordResetRequired` in
  its context; authorizer result caching is **TTL 0** (`FR-AUTH-14` says
  "immediately"). Every authenticated request costs one `AP2` `GetItem`
  for the revocation check — that is `G-87` working as designed, not a
  regression.
- **Marker transport: `ETag` / `If-None-Match`**, value = `marcaCambio`
  verbatim, strong ETag, `Cache-Control: no-store`. Unchanged poll →
  `304`, no body. Mutations return the new marker as their `ETag`. A
  client keeps a mutation's returned marker **only if it equals held + 1**
  (`data_model.md` §4.7); otherwise it refetches. The four pollable
  resources are exactly `FR-RT-01`'s four — weeks, library, shopping
  list, rules.
- **Error format: RFC 9457 `application/problem+json`.** Machine-readable
  `code` as an extension member; `detail` copied verbatim from
  `planner_core.messages` (es-ES, never composed in the handler); `400`
  malformed vs. `422` domain-rejected. API Gateway's own
  authorizer/throttle responses need Gateway Response templates to match
  this shape — a feature 21 infra detail.
- **Rules use per-rule endpoints** (`PUT`/`DELETE /v1/rules/{ruleId}`),
  matching `AP23`/`AP24`'s per-item writes — genuine per-rule
  last-write-wins. Satisfiability (`FR-RULE-07`) is still validated
  whole-set in the adapter on each write.
- **`api` → `ai` is a standard SQS queue** (§1.2.6). The AI HTTP surface
  is submit-then-poll and is provider-agnostic.

The 13 gate questions and their rulings are recorded in
`docs/rest_api_contract.md` §7.

### 1.2.6 AI provider — AWS Bedrock + Amazon Nova 2 Lite (was P4)

**Decided by the human 2026-08-30; model changed 2026-09-16 and again
2026-10-11.** Formerly P4. Originally Anthropic Claude, then OpenAI GPT-5.6
Terra. The owner's account has no Bedrock model access for either (GPT-5.6
Terra returned `AccessDeniedException`, agreement `NOT_AVAILABLE`); the only
models enabled are Amazon Nova and Kimi K3. The provider stays Bedrock and the
model is now **Amazon Nova 2 Lite**.

- **AWS Bedrock**, **Amazon Nova 2 Lite** (`amazon.nova-2-lite-v1:0`) — an
  Amazon first-party model: no AWS Marketplace subscription step. Reasoning is
  optional and off by default; effort, token cap, sampling and service tier are
  configured through environment variables (table below, feature 33).
- **Invocation: Bedrock's `Converse` API, plain `boto3`, no new
  dependency.** Nova 2 Lite supports `Converse` on the `bedrock-runtime`
  endpoint. `Converse` is provider-agnostic and already part of `boto3`
  (`bedrock-runtime` client, already this Lambda's dependency), so the
  same boto3-only reasoning `specs/ai_lambda/design.md` §3 already gave
  for rejecting `anthropic[bedrock]` applies equally here.
- **Structured output: a forced tool, not `outputConfig`.** Nova 2 Lite has no
  `outputConfig` structured output; the documented pattern is a `toolConfig`
  whose single tool's input schema is the recipe, with `toolChoice` forced to
  it (constrained decoding), reading the result from the `toolUse` block's
  `input`. The schema is built in `core` from the frozen enums and carries the
  field descriptions; the domain validators remain the backstop (issue 15).
- **Region: `eu-south-2` (Spain). Model id: `eu.amazon.nova-2-lite-v1:0`.**
  The `bedrock-runtime` endpoint takes an inference-profile id, not the bare
  model id. The `eu.` prefix is the EU **Geo** profile, which lists
  `eu-south-2` as a source region, so the call is made from the account's
  home region. The `us.`/`in.` prefixes in AWS's examples do not work from
  here. IAM needs `bedrock:InvokeModel` on the inference profile and on the
  foundation models it routes to.
- **EU data residency.** The Geo profile routes inference only between EU
  regions, so the earlier accepted tradeoff (the Global GPT-5.6 Terra
  profile could leave the EU) no longer applies. The profile, not the region
  alone, is what keeps traffic in the EU; do not switch to a `global.` id.
- The `ai` Lambda's provider client is a Bedrock adapter — the Bedrock
  path is **its** dependency closure, never `api`'s (§1.2 rule).
- **Cost cap: a real kill-switch**, resolving `G-81` / `NFR-AI-01` — an
  alert alone is not acceptable. The mechanism (reserved concurrency 0,
  event-source-mapping disable, or a flag the `ai` worker reads before
  invoking the provider) is a feature 17 spec-gate detail, unaffected by
  the model change.
- The `ai` worker consumes from the `api` → `ai` SQS queue (§1.2.5). It
  writes whole-week results through `WeekRepository` — never a separate
  write path (`G-88`, recorded on feature 17).
- **AI worker environment** (feature 33, `specs/ai_inference_config/`). The `ai`
  Lambda reads these on every Bedrock call; unset means the default. An
  out-of-domain value, or `AI_TEMPERATURE`/`AI_TOP_P` set while reasoning is on
  with effort `high`, fails the generation (logged, never silently defaulted).
  Reasoning tokens bill as output and count against `AI_MAX_TOKENS`.

  | Variable | Accepted values | Default | Effect |
  |---|---|---|---|
  | `AI_MODEL_ID` | non-empty string | `eu.amazon.nova-2-lite-v1:0` | Bedrock model / inference-profile id |
  | `AI_REASONING_ENABLED` | `true` / `false` | `false` | Reasoning on or off |
  | `AI_REASONING_EFFORT` | `low` / `medium` / `high` | `low` | Reasoning effort; used only when reasoning is on |
  | `AI_MAX_TOKENS` | integer 1-65000 | `4096` | Output token cap |
  | `AI_TEMPERATURE` | number 0-1 | unset (model default) | Sampling temperature |
  | `AI_TOP_P` | number 0-1 | unset (model default) | Nucleus sampling |
  | `AI_SERVICE_TIER` | `standard` / `priority` / `flex` | `standard` | Bedrock service tier |

### 1.2.7 Deployment topology — decided to the level code needs (was P6)

**Decided by the human 2026-08-30.** Formerly P6. Decided only as far as
application code depends on it:

- **API Gateway → Lambda**, reachable from the SPA. The Lambdas sit in a
  **VPC**, but that is transparent to application code — no handler
  touches networking.
- **`/v1/*` routes through the same CloudFront distribution** that serves
  the SPA, making them same-origin (required by §1.2.5's cookie auth, and
  it removes the CORS preflight on every poll).
- **Detailed network configuration** (subnets, security groups, VPC
  endpoints), the API Gateway stage/throttling config, and all IaC remain
  **human-owned, feature 21** — not a blocker for feature 16.
- **Cold storage / archive lifecycle stays parked** (`data_model.md` §9),
  MVP scope. No endpoint, no `restoring` state.

### 1.3 Toolchain

| Concern | Tool |
|---|---|
| Package / env manager | **uv** |
| Tests | **pytest** |
| Lint + format | **ruff** |
| Type checking | **mypy** |
| Static analysis / quality gate | **SonarQube** |
| Pre-commit enforcement | **pre-commit** hooks |

No dependency outside this list enters the project without being justified in an
approved `design.md`.

### 1.4 Cloud constraints (from `docs/requirements.md` §12)

These are fixed by the requirements, not open to reinterpretation:

- AWS deployment (`NFR-ARCH-01`); **Terraform** for IaC (`NFR-IAC-01`).
- ≥ 2 availability zones for production traffic (`NFR-HA-01`).
- Automated backups on every persistent datastore (`NFR-BKP-01`).
- CI/CD deploying on push to `main` (`NFR-CICD-01`).
- Least-privilege IAM (`NFR-SEC-01`); secrets never in source (`NFR-SEC-02`);
  HTTPS only (`NFR-SEC-03`); login brute-force protection (`NFR-SEC-04`).
- Centralised logs (`NFR-OBS-01`) and ≥ 1 active alarm (`NFR-OBS-02`).
- `Project` / `Environment` / `Owner` tags (`NFR-FIN-01`); AWS Budgets
  (`NFR-FIN-02`); €50/month AI sub-cap (`NFR-AI-01`).

### 1.5 Lambda logging (owner ruling 2026-11-07, issue 24)

Every Lambda logs in JSON through `logging_config` (`terraform/lambda.tf`). In
plain text, Python Lambdas default to WARN and drop every INFO line, including
the per-invocation record of `specs/rest_api_lambda` R22 (`NFR-OBS-01`).

- **Level per environment:** `DEBUG` on `dev`, `INFO` everywhere else. It is
  derived from the environment (`lambda_log_level`, `terraform/locals.tf`), not
  a variable, so a copied `terraform.tfvars` cannot put `DEBUG` in production.
- **The AWS SDK stays at WARNING:** at `DEBUG`, `botocore` logs full requests
  and responses, which hold the session signing key, password hashes and the
  Bedrock API token. So each deployed `lambda_handler` first calls
  `quiet_sdk_loggers()` (`sdk_logging.py`, one byte-identical copy per Lambda
  package), which sets `boto3`, `botocore`, `urllib3` and `s3transfer` to
  WARNING. Do not remove it. A new dependency that logs below WARNING on a
  tested path fails `test_no_third_party_record_below_warning_reaches_the_log`;
  add its logger to the list.
- **Code never sets the root level:** a level set in code overrides Terraform's.
- **Code before Terraform:** the code with `quiet_sdk_loggers()` must be running
  before `logging_config` is applied, and no build older than it may run on
  `dev` while `dev` is at `DEBUG`. Either mistake can put those secrets in
  CloudWatch.
- **Not covered:** `logger.debug` lines in application code. The backend has
  none today; any added later must not carry a secret.

Local runs use `basicConfig(level=logging.INFO)` in `local_server.py` and
`local_worker.py`, and do not call `quiet_sdk_loggers()`.

---

## 2. Pending — human-owned, agents must NOT decide

Hitting any of these means: mark the feature `blocked`, write the reason in
`progress/current.md`, stop.

| # | Undecided | Blocks |
|---|---|---|
| ~~P1~~ | ~~**Datastore**~~ — **DECIDED 2026-08-16: DynamoDB, single table. See §1.2.1.** | — |
| ~~P2~~ | ~~**Auth mechanism**~~ — **DECIDED 2026-08-27: application-managed. See §1.2.3.** | — |
| ~~P3~~ | ~~**Real-time transport**~~ — **DECIDED 2026-08-27: adaptive polling with conditional GET. See §1.2.4.** | — |
| ~~P4~~ | ~~**AI provider and model**~~ — **DECIDED 2026-08-30: AWS Bedrock + Anthropic Claude, real cost kill-switch. See §1.2.6.** | — |
| ~~P5~~ | ~~**REST API contract**~~ — **DECIDED 2026-08-30: see §1.2.5 and `docs/rest_api_contract.md`.** | — |
| ~~P6~~ | ~~**Deployment topology**~~ — **DECIDED 2026-08-30 to the level application code needs (§1.2.7); detailed network config and IaC remain feature 21, cold storage stays parked (`data_model.md` §9).** | — |
| ~~P7~~ | ~~**Frontend framework identity, bootstrap idiom and test runner**~~ — **DECIDED 2026-08-17: idiomatic React (function components, hooks, JSX), Vite, Vitest. See §1.1.** | — |

**No pending architecture items remain.** Every `P<n>` is decided. A feature
that still reads `blocked` on one of these is stale — check its `blocked_reason`
against §1.2.

### 2.1 Not pending — decide these in a spec, not in chat

These read like open questions but the requirements explicitly classify them as
**implementation details**. A `spec_author` may propose concrete values in
`design.md`; the human approves them at the normal spec gate:

- The literal **unit list** for ingredients/shopping (`G-39`, `FR-SHOP-03`).
- The literal **ingredient-category list** for the rules (`G-69`, supersedes `G-63`; `FR-RULE-04`). It is the same set stored per recipe as `tipoAlimento` (`FR-LIB-03`).
- The configured **servings count** for AI prompts (`G-64`, `FR-AI-13`).
- ~~The **per-user daily generation cap** figure, once P4 is decided (`G-38`).~~ **Removed** by `G-70`: the cap is **global** for the whole deployment, enforced through AWS cost tooling. The application stores and enforces **no per-user quota**. The *enforcing path* — `G-81`'s open question — was **decided 2026-08-30: a real kill-switch, not an alert alone** (§1.2.6). Its mechanism (reserved concurrency, event-source disable, or a flag the `ai` worker reads) is a feature 17 spec-gate detail, not an access pattern.

---

## 3. Repository layout

The repository has two toolchain roots — a Python **backend** and a JS
**frontend** — which never share tooling.

```
backend/                     uv workspace root; shared ruff/mypy/pytest config
  pyproject.toml             [tool.uv.workspace] members = core, lambda_api, lambda_ai
  core/                      Distribution: planner-core. ZERO runtime dependencies.
    pyproject.toml
    src/planner_core/
      domain/                Pure logic. No IO, no AWS SDK, no framework, no clock.
      application/           Use cases. Orchestrate domain objects through ports.
      ports/                 Interfaces (typing.Protocol): persistence, ai, clock, ids.
                             Also holds a port's DEFAULT implementation when that
                             implementation imports nothing outside the standard
                             library (e.g. SystemClock). See §1.2.2.
    tests/                   Tier 1 lives here (features 2–13).
      support/               Fakes implementing the ports. Never mocks of our own code.
  lambda_api/                Distribution: planner-api. Depends: planner-core (+ AWS deps at P1).
    pyproject.toml
    src/planner_api/
      handler.py             AWS entry point. Thin: parse event, call a use case, map result.
      wiring.py              Composition root: picks adapters by environment.
      adapters/              Real port implementations this Lambda owns (DynamoDB; §1.2.5/§1.2.7 decided).
    tests/
  lambda_ai/                 Distribution: planner-ai. Depends: planner-core (+ Bedrock SDK, §1.2.6).
    pyproject.toml
    src/planner_ai/
      handler.py
      wiring.py
      adapters/
    tests/
  tests/
    contract/                One suite per port, run against BOTH the fake and the real adapter.
frontend/                    Own toolchain root (see docs/conventions.md § Frontend).
  src/
  tests/
prototypes/                  Read-only reference material. NOT a toolchain root; no
                             linter, bundler or test runner may reach it, and nothing
                             here ships.
  wireframe/                 The Claude design prototype. Analysed in
                             docs/frontend_prototype.md — read it, mine it, do not port it.
```

`core` is the settled part of §2: it holds pure domain, application services and
port interfaces — everything with no idea it runs in a Lambda. It is chosen so
**domain logic can be built and fully tested today with none of §2 decided**.
Tier 1 of the backlog (features 2–13) is exactly `core`.

### 3.1 Layer rules (the reviewer enforces these)

1. `planner_core/domain/` imports **nothing** from `application/`, `ports/`, any
   adapter, any handler, `boto3`, or any AWS SDK. Standard library only.
2. `planner_core/application/` imports `domain/` and `ports/`. Never an adapter,
   never a handler.
3. **`core` never imports a Lambda package, and never imports an AWS SDK.**
   `core` defines the *port*; the *adapter* that imports `boto3` lives in the
   Lambda package that uses it. The test is the **dependency**, not the fact of
   being an implementation: a default implementation importing nothing beyond
   the standard library stays in `ports/` beside its `Protocol` (§1.2.2).
4. Adapters implement `ports/`. Nothing imports an adapter except its Lambda's
   `wiring.py`.
5. Dependencies point **inward**. Nothing outside `domain/` is imported by it.
6. Time is a **port**, never `datetime.now()` inside `core` — week rollover and
   "today onward" scoping (`FR-MENU-02`, `FR-AI-11`, `FR-SHOP-05`) must be
   deterministically testable. **One sanctioned exception (§1.2.2, added
   2026-08-19):** the port's default implementation, `SystemClock.now` in
   `planner_core/ports/clock.py`, is the single ambient-time call permitted in
   `core`. Nothing in `domain/` or `application/` may construct it — selecting a
   `Clock` is `wiring.py`'s job — and
   `backend/core/tests/test_no_ambient_time.py` enforces both halves
   mechanically. That module is **the authority** on exactly which call is
   allowed and which modules may reach for `SystemClock`; it is deliberately not
   paraphrased here (see §1.2.2).

A feature is "architecture-independent" exactly when it lives in
`planner_core/domain/` and its tests need no fake beyond a fixed clock. Those
are the features to build first.

### 3.2 Packaging and independent deployment

Each Lambda is a workspace member with its **own dependency closure**. `core` is
a **local path dependency**, resolved into each artifact — it is shared *source*,
not a shared runtime component. So building one Lambda pulls in `core` plus only
that Lambda's own dependencies:

```
build lambda_api  →  [ handler + wiring + adapters + planner_core + its AWS deps ]   ← no AI SDK
build lambda_ai   →  [ handler + wiring + adapters + planner_core + the AI SDK ]
```

```bash
uv export --package planner-api --no-dev   # exactly the api closure
uv export --package planner-ai  --no-dev   # exactly the ai closure
```

- **Independent testing** (your question, answered): each Lambda's `wiring.py`
  selects adapters **by environment** — fakes/local for `pytest`, real AWS for a
  deployed function. Never select an adapter by import-time side effect.
- **The contract-test rule** is what makes "mock locally, real in AWS"
  trustworthy: for every port, one suite in `backend/tests/contract/` runs
  against both the in-memory fake and the real adapter. If both pass the same
  suite, the local fake is a faithful stand-in. Without this, local mocking is a
  story you tell yourself until production disagrees.
- **Whether `core` ships vendored into each zip or as a shared Lambda layer is
  an IaC choice — feature 21, human-owned.** This layout supports both
  unchanged; the choice only changes how the (human-written) CI pipeline
  assembles the final artifact.

---

## 4. Domain invariants

These come from the requirements and their resolutions. Violating one is a
review rejection, regardless of whether a test catches it.

1. **Snapshots, not references.** A recipe added to a menu stores a *copy* of
   the recipe content. Later library edits or deletes must never retroactively
   mutate a live or archived week. (`FR-CAND-07`, `G-05`)

2. **Never silently undo the user's reality.** This is the single most repeated
   principle in the requirements — it decided `G-04`, `G-32`, `G-73` and `G-77`.
   A recompute must never un-check an item someone bought or discard a manual
   entry. When new data conflicts with a user action, **keep both** — as two
   rows, not as one row plus a marker.

   The MVP draws the line more sharply than earlier drafts did, and in two
   directions. **Stricter on purchases:** a checked shopping item is not merely
   preserved, it is **never written to at all**; a later shortfall arrives as
   its own new unchecked item carrying the remainder (`G-77`, supersedes
   `G-44`). **Looser on edits:** the principle no longer protects a deliberate
   edit to an *unchecked* quantity — `G-72` accepted that a later re-sync press
   may overwrite it, and made manual delete the remedy, because the alternative
   was a three-state provenance model on every row (`G-21`, superseded).
   Do not reintroduce a "flag it" marker to bridge the two: every flag proposed
   so far turned out to need an attribute recording state at a past moment,
   which is the provenance the shopping list deliberately does not carry.

3. **Warn, do not block, on duplicates.** Same-name library recipe (`G-26`),
   same-name candidate in a slot (`G-59`): surface it, allow it, never reject
   it. ~~manual/auto shopping item collision (`G-55`)~~ — the shopping list is
   the **exception** and carries no duplicate handling at all: `G-74` removed
   `FR-SHOP-11`, and under `G-77` a checked and an unchecked item may share a
   normalized name + unit **by design**. They are a purchase and a remainder,
   not a duplicate, and `FR-SHOP-08`'s two-section display already tells them
   apart. Do not warn on them.

4. **Bulk operations are additive.** Whole-week AI generation *adds* candidates.
   It never removes existing candidates or definitive selections. (`FR-AI-11`, `G-18`)

5. **Compound operations are idempotent.** AI generation (`FR-AI-08`), shopping
   re-sync (`FR-SHOP-10`, `G-54`) and week rollover (`FR-MENU-08`, `G-61`) must
   converge to one result under retry, double-click or partial failure.
   Recompute-from-source beats diff-and-patch.

6. **Definitive meals derive the shopping list. Candidates never do.**
   (`FR-SHOP-05`, `G-04`)

7. **Weeks are ISO weeks in `Europe/Madrid`.** Monday–Sunday. Every user must
   agree on which week is current. (`FR-MENU-02`, `G-02`)

8. **Admin-assigned passwords are always temporary** — creation, change, reset
   or IaC re-seed alike. They only ever reach the mandatory set-password step.
   (`FR-AUTH-11`, `G-10`, `G-51`, `G-65`)

9. **Removed users leave their content behind**, reattributed to a reserved
   "unknown user" placeholder. Never cascade-delete authored content.
   (`FR-AUTH-13`, `FR-SUM-03`, `G-29`, `G-58`)

10. **Text matching is normalised.** Case-, accent- and trim-insensitive for
    ingredient aggregation. No fuzzy matching beyond that —
    no stemming, no synonyms. (`FR-SHOP-03`, `G-56`, `G-68`)

11. **Content freezes only at archival.** A definitive meal stays editable like
    any candidate until its week is archived. (`FR-CAND-05`, `G-67`)

12. **Errors are explicit.** Functions that can fail raise named domain
    exceptions. They do not return `None` to mean failure.

---

## 5. Human-owned, never agent-generated

| Area | Why |
|---|---|
| `**/*.tf`, `**/*.tfvars`, Terraform modules | The human writes the infrastructure. |
| `.github/workflows/**`, any CI/CD pipeline | Same. |
| Architecture decisions listed in §2 | Same. |

`init.sh` fails if these files appear while their `feature_list.json` entry is
still `blocked`. That tripwire is intentional — do not work around it, and do
not "helpfully" scaffold a `main.tf`.

---

## 6. What NOT to do

- ❌ Do not use `print()` for errors. Use logging; return proper API errors.
- ❌ Do not import `boto3` (or any AWS SDK) inside `core` — not in `domain/`,
  `application/`, or `ports/`. Adapters live in the Lambda packages.
- ❌ Do not import a Lambda package (`planner_api`, `planner_ai`) from `core`.
- ❌ Do not call `datetime.now()` inside `core`. Inject a clock port. The lone
  exception is `SystemClock.now` in `planner_core/ports/clock.py`, the port's
  default implementation (§1.2.2, §3.1 rule 6) — do not add a second.
- ❌ Do not mix IO with domain logic.
- ❌ Do not add a runtime dependency to `core`. It stays stdlib-only.
- ❌ Do not add a third Lambda, a **second** queue, a cache, or any service
  without an approved `design.md` and human sign-off. (The `api` → `ai` SQS
  queue is signed off — §1.2, decided 2026-08-30.)
- ❌ Do not build a configuration framework. Configuration is explicit values
  passed in, or a single documented constants module.
- ❌ Do not add accessibility work beyond the WCAG 2.2 AA subset of `FR-UX-07`
  (amended by `G-93`; was ~~an explicit scope exclusion, browser defaults only~~, `G-62`).
- ❌ Do not implement anything from the "examined and rejected" list at the end
  of `docs/gaps_and_resolutions.md` (offline support, presence indicators,
  export/print, per-recipe category attribute, GDPR formalities…).
