# rest_api_lambda — Design

> Feature 16 · tier 3 · `planner_api` **shell only**: handler, routing, errors,
> serialization, authorizer, scheduled entry, wiring, and the SQS producer call
> site. Read `requirements.md` first.
> Primary source: `docs/rest_api_contract.md` (whole). Also `docs/architecture.md`
> §1.2 / §1.2.5 / §3–§3.2, `docs/data_model.md` §1.

## 0. Governing decisions already made elsewhere — not re-opened

- **The adapters and the application services are feature 27** — see
  `specs/rest_api_persistence_and_services/`. This feature codes against those
  ports and use cases and builds none of them.
- The contract is **decided** (`docs/rest_api_contract.md`, 2026-08-30, all 13
  gate questions resolved in §7). This feature implements it; it does not
  revisit resources, verbs, payloads, the error format, the cookie or the
  marker transport.
- No `docs/architecture.md` §2 item is open (all `P<n>` decided). Nothing here
  needs a human architecture decision.
- `Clock` is a port; domain code takes a `date`/instant, never a `Clock`
  (tier-1 ruling). The authorizer and the scheduled entry point read the clock
  in `wiring.py` and pass the instant down.
- `If-None-Match` parsing, the marker-first read and the `304` mapping are
  **feature 26** (GQ2, owner 2026-08-31). This feature only emits the marker.

## 1. Layering (`docs/architecture.md` §3, §3.1)

| Piece | Layer | Notes |
|---|---|---|
| `handler.py`, `authorizer.py`, `scheduled.py` | `planner_api/` (AWS entry points) | Thin: parse event → call one use case → map result or exception. No business logic (`conventions.md`). |
| `routing.py` | `planner_api/` | `(method, resource-template) → handler fn` dispatch table. Pure data + lookup. |
| `errors.py` | `planner_api/` | `PlannerError` → `(status, code, detail-key, details)` per `contract` §4. The one place that maps exceptions. |
| `serialization.py` | `planner_api/` | domain value objects ⇄ camelCase JSON. The wire ⇄ English-identifier boundary. |
| `wiring.py` | `planner_api/` | Composition root; selects adapters by environment; the only module naming a concrete adapter. Reads the clock. |
| `adapters/sqs.py` **call site** | `planner_api/` | This feature calls `GenerationQueue.send(...)`; the concrete SQS adapter is feature 27. |

`planner_api` gains no new runtime dependency in this feature. `boto3` arrives
with feature 27's adapters (`docs/architecture.md` §1.3).

## 2. Files created / modified

**`backend/lambda_api/src/planner_api/`** (all new):
`handler.py`, `authorizer.py`, `scheduled.py`, `routing.py`, `errors.py`,
`serialization.py`, `wiring.py`.

**`backend/lambda_api/tests/`** — routing, authorizer, error-mapping,
serialization, marker-emission, scheduled-entry tests.

Nothing under `backend/core/` is modified by this feature.

**Reopened 2026-09-06 (bundled with feature 27):**

- `routing.py` gains a `DELETE /v1/generations/{generationId}` route (`R42`):
  the handler calls `deps.queue.discard(path["generationId"])` directly — the
  same direct-port pattern as `_get_generation` for `AP26`, with no `application`
  use case and no `generation_submission` involvement — and returns `204` with
  no `ETag`. Closes spec-gap 4.
- `adapters/markers.py` (the spec-gap 2 forwarding shim) is **deleted**.
  Feature 27's four read use cases now return the `marcaCambio` in their result
  DTO (feature 27 `R34`); `routing.py` reads it from there. No name
  `current_version` then appears in `lambda_api/src` outside the real adapters,
  so the feature-18 guard passes without leaning on the directory exemption.

## 3. The authorizer (`R6`–`R13`, `contract` §5)

- `authorizer.py` is a separate Lambda handler function in the same package
  (same artifact, different entry point — `docs/architecture.md` §1.2 allows
  multiple entry points on `api`).
- Reads the `session` cookie from `event.headers.Cookie`, calls
  `authentication.authenticate(token, accounts=…, signer=…, clock=…)`.
- Success → allow policy + `context = {userId, role, passwordResetRequired}`
  (all strings; API Gateway context values are stringified — `role` is
  `Role.value`, `passwordResetRequired` is `"true"`/`"false"`).
- `SessionExpired` / missing cookie → explicit `Deny` (API Gateway renders its
  own 401/403 body; matching it to `problem+json` needs Gateway Response
  templates — **feature 21 IaC**, noted in `contract` §4).
- No result caching in the authorizer itself (`R10`); the API Gateway authorizer
  resource's `authorizer_result_ttl_in_seconds = 0` is **feature 21 IaC**.
- The handler trusts the context and never re-reads the account (`R11`–`R13`).

## 4. Error mapping (`errors.py`, `R14`–`R21`)

One table, `PlannerError` subclass → `(http_status, code, message_constant,
details_builder)`, transcribed from `contract` §4. Unmapped `PlannerError` →
`500 / INTERNAL_ERROR` (`R20`), logged with traceback (`R24`), no body detail
beyond the generic message. `400` is raised by `serialization.py` /
`routing.py` **before** a use case runs (bad JSON, missing field, client `id`,
bad path param); `422` and friends come from a use case raising a domain
exception. `InvalidIsoWeek` is `400` in a path segment, `422` in a body
(`contract` §4) — the path/body origin is known at the parse site.

## 5. Marker emission (`R28`–`R30`, `contract` §6)

Read handlers for the four pollable resources take the marker the read service
returns and set it as a strong `ETag`; mutation handlers set the `ETag` to the
value the write returned (feature 18's version-returning writes, surfaced
through feature 27's services). `Cache-Control: no-store` is set once, in
`handler.py`'s response builder, on every response including errors.

Reopened 2026-09-06: the read-service marker is now a field of feature 27's
read-use-case result DTO (feature 27 `R34`, marker read first) — the
first-round `adapters/markers.py` shim is deleted. Generation routes
(`GET`/`DELETE /v1/generations/{generationId}`) carry **no** `ETag`:
`PETICIONIA#` has no `MarcaCambio` (`contract` §2, §6). `DELETE` there returns
`204 No Content` (`R42`).

## 6. What is feature 21 (IaC), not here

API Gateway REST API + stage + routes, the CloudFront same-origin behaviour,
the authorizer resource and its `ttl = 0`, Gateway Response templates for the
authorizer/throttle 401/403, the SQS queue + its DLQ + the event-source
mapping, the EventBridge schedule, DynamoDB table provisioning + TTL +
backups, and all IAM. This feature assumes they exist and codes to their
contract shape; `wiring.py` selects a fake stack for `pytest`.

## 7. The rollover archive step — decided: **archive is parked for the MVP**

Owner ruling, 2026-08-31, consistent with `docs/data_model.md` §9 parking
`FR-ARCH-02`: the shopping-list snapshot has **no item type**, and archiving a
week is otherwise a no-op (past weeks already sit under older keys).

`domain.rollover.roll_over` still writes an `ArchivedWeek` through
`planner_core.ports.archive.ArchiveRepository`, so the port call must be
satisfied. **`wiring.py` injects a no-op `ArchiveRepository`** (`R40`): it
accepts the `ArchivedWeek`, retains nothing, and logs the discarded record
through the standard-library `logging` module (`R41`). No week menu and no
shopping-list snapshot is retained in the MVP.

The real DynamoDB `ArchiveRepository` adapter and the `FR-ARCH-02`
shopping-list-snapshot item type are **post-MVP**; unparking them is the owner
decision `docs/data_model.md` §9 describes. Feature 27 therefore builds no
archive adapter (`specs/rest_api_persistence_and_services/design.md` §7).

## 8. Rejected alternatives

**A routing/validation framework (AWS Lambda Powertools event handler, or
FastAPI-in-Lambda).** Gives declarative routes, parsing and OpenAPI. Rejected:
it is a new runtime dependency on `planner_api` (`architecture.md` §1.3 — "no
dependency outside this list without an approved `design.md`"), and ~40 routes
with no content negotiation, no pagination and a fixed locale need only a `dict`
dispatch over `(method, resourcePath)` plus explicit per-route body parsing.

**Re-read the account in the handler to gate role and `passwordResetRequired`.**
Would let the handler work identically under a future non-authorizer deployment
and removes any trust in a stringified context. Rejected: `contract` §5 states
the gate is decided "without a second `AP2` read", and with authorizer TTL 0
(§7 Q2) the authorizer has already made exactly that read on this request — a
second one doubles the per-request cost to re-derive a value it was handed.

**A third Lambda for scheduled rollover.** Cleanly separates the request path
from the job path and lets them scale and fail independently. Rejected:
`contract` §7 Q8 decided (a), a non-HTTP entry point on the `api` Lambda, and
`architecture.md` §6 forbids adding a Lambda without sign-off.

## 9. Test strategy (feeds `tasks.md`)

- **Routing**: table-driven — every `contract` §2 row has a route; `AP3`/`AP9`/
  `AP29`/rollover have none; no `GET` route writes (`R2`, `R26`, `R27`, `R33`).
- **Authorizer**: fake `AccountRepository` + `HmacTokenSigner` + `FakeClock`;
  allow/deny/context cases, no-cache behaviour (`R6`–`R10`).
- **Context gating**: role mismatch → 403 `FORBIDDEN`; `passwordResetRequired`
  → 403 `PASSWORD_RESET_PENDING` except the two allowed routes; the fake
  `AccountRepository` records zero reads during gating (`R11`–`R13`).
- **Errors**: each `contract` §4 row → status + `code` + `detail` is the
  `messages` constant verbatim; malformed → 400; unmapped → 500 no traceback
  (`R14`–`R21`, `R24`, `R25`).
- **Markers**: pollable `200` carries `ETag` = the marker on the read-use-case
  result DTO (feature 27 `R34`); mutation response carries the write's returned
  marker; `no-store` always (`R28`–`R30`). A source scan asserts no
  `current_version` literal in `lambda_api/src` outside the real adapters
  (`markers.py` is gone).
- **Session**: cookie attribute string exact match; token absent from every
  response body; logout emits `Max-Age=0` (`R1`, `R3`, `R4`, `R5`).
- **Scheduled entry**: invoking twice = one effect against fakes; not in the
  route table (`R32`–`R34`). The no-op `ArchiveRepository` returns without
  retaining the `ArchivedWeek` and emits one `logging` record for it, asserted
  with `caplog` (`R40`, `R41`).
- **Generation**: `POST /v1/generations` calls `FakeGenerationQueue.send`;
  stored-`idPeticionIA` hit returns 200 without a send; import-scan test —
  `planner_api` imports no `bedrock`/AI SDK module (`R35`–`R37`).
  `DELETE /v1/generations/{generationId}` calls `GenerationQueue.discard` with
  the path segment as the key and returns `204` with no `ETag`; the route table
  test now lists `AP27` as routed (`R42`).
- **Serialization**: camelCase round-trips; `author`/`id` in a request body →
  400 (`R38`, `R39`).
