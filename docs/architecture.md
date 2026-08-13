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
- Markup is **HTML with inline CSS**, driven by a **JS logic class**, on a
  **React-based DC framework**. **No separate templating language** — markup is
  produced from JavaScript.
- Logic class and markup are separated like backend layers: the class owns state
  and handlers, the markup is a pure function of that state. Full rules in
  `docs/conventions.md` § *Frontend conventions*.
- **No business logic in the client.** Week boundaries, scoping, aggregation and
  rule satisfiability live in `backend/core` (`planner_core.domain`). The SPA
  displays results.
- All UI text in **Castilian Spanish** (`FR-UX-01`, `FR-UX-03`), centralised in
  one messages module, with `Intl` pinned to `es-ES`.
- Inline CSS cannot express `@media` queries, so layout is **fluid-first**
  (flex/grid, `clamp()`, `minmax()`); genuine breakpoints go through
  `matchMedia` and become state. See `docs/conventions.md`.
- The human supplies the **initial version of the frontend code**. Until it
  exists, no agent writes frontend code (`frontend_spa` is `blocked`).

### 1.2 Backend

Exactly **two Lambdas**, no more:

| Lambda | Responsibility |
|---|---|
| `api` | Regular backend operations, exposed as a **REST API** |
| `ai`  | AI generation only (single recipe + whole week) |

- Language: **Python**.
- Splitting AI generation into its own Lambda is deliberate: AI calls are slow
  (seconds to a minute-plus, `G-19`), cost-capped (`NFR-AI-01`) and need their
  own concurrency and idempotency behaviour (`FR-AI-08`, `FR-AI-09`). Do not
  merge it into `api`, and do not add a third Lambda without human approval.
- The split is **real, not nominal**: each Lambda is its own package with its
  own dependency closure, so the `api` artifact never ships the AI provider SDK
  and never pays its cold-start cost. Packaging is covered in §3.2.

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

---

## 2. Pending — human-owned, agents must NOT decide

Hitting any of these means: mark the feature `blocked`, write the reason in
`progress/current.md`, stop.

| # | Undecided | Blocks |
|---|---|---|
| P1 | **Datastore** (DynamoDB? Aurora/RDS? something else) | persistence adapters, all reads/writes |
| P2 | **Auth mechanism** (Cognito? application-managed?) | the whole `FR-AUTH-*` family |
| P3 | **Real-time transport** (WebSocket API? AppSync? polling?) | `FR-RT-01`–`-03` |
| P4 | **AI provider and model** (Bedrock? external API?) | `ai` Lambda, and the enforcing path for the €50/month **global** cap (`G-70`, supersedes `G-38`) |
| P5 | **REST API contract** (resources, verbs, payload shapes, error format) | `api` Lambda handlers |
| P6 | **Deployment topology** (API Gateway config, VPC, cold-storage wiring) | anything touching AWS |
| P7 | **Frontend framework identity, bootstrap idiom and test runner** — the stack is specified (§1.1); only these are pinned down from the human's initial code drop | `frontend_spa` |

### 2.1 Not pending — decide these in a spec, not in chat

These read like open questions but the requirements explicitly classify them as
**implementation details**. A `spec_author` may propose concrete values in
`design.md`; the human approves them at the normal spec gate:

- The literal **unit list** for ingredients/shopping (`G-39`, `FR-SHOP-03`).
- The literal **ingredient-category list** for the rules (`G-69`, supersedes `G-63`; `FR-RULE-04`). It is the same set stored per recipe as `tipoAlimento` (`FR-LIB-03`).
- The configured **servings count** for AI prompts (`G-64`, `FR-AI-13`).
- ~~The **per-user daily generation cap** figure, once P4 is decided (`G-38`).~~ **Removed** by `G-70`: the cap is **global** for the whole deployment, enforced through AWS cost tooling. The application stores and enforces **no per-user quota**. What remains open is the *enforcing path* (a Budget action or equivalent), since Budgets alert but do not stop spend — an infrastructure question, not an access pattern.

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
    tests/                   Tier 1 lives here (features 2–13).
      support/               Fakes implementing the ports. Never mocks of our own code.
  lambda_api/                Distribution: planner-api. Depends: planner-core (+ AWS deps at P1).
    pyproject.toml
    src/planner_api/
      handler.py             AWS entry point. Thin: parse event, call a use case, map result.
      wiring.py              Composition root: picks adapters by environment.
      adapters/              Real port implementations this Lambda owns. Empty until §2 resolves.
    tests/
  lambda_ai/                 Distribution: planner-ai. Depends: planner-core (+ AI SDK at P4).
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
   Lambda package that uses it.
4. Adapters implement `ports/`. Nothing imports an adapter except its Lambda's
   `wiring.py`.
5. Dependencies point **inward**. Nothing outside `domain/` is imported by it.
6. Time is a **port**, never `datetime.now()` inside `core` — week rollover and
   "today onward" scoping (`FR-MENU-02`, `FR-AI-11`, `FR-SHOP-05`) must be
   deterministically testable.

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
  P6 (deployment topology) — human-owned.** This layout supports both unchanged;
  the choice only changes how the (human-written) CI pipeline assembles the
  final artifact.

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
- ❌ Do not call `datetime.now()` inside `core`. Inject a clock port.
- ❌ Do not mix IO with domain logic.
- ❌ Do not add a runtime dependency to `core`. It stays stdlib-only.
- ❌ Do not add a third Lambda, a queue, a cache, or any service without an
  approved `design.md` and human sign-off.
- ❌ Do not build a configuration framework. Configuration is explicit values
  passed in, or a single documented constants module.
- ❌ Do not add accessibility work — it is an explicit **scope exclusion**
  (`FR-UX-07`, `G-62`). Browser defaults only.
- ❌ Do not implement anything from the "examined and rejected" list at the end
  of `docs/gaps_and_resolutions.md` (offline support, presence indicators,
  export/print, per-recipe category attribute, GDPR formalities…).
