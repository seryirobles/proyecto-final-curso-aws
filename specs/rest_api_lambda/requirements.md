# rest_api_lambda — Requirements

> Feature 16 · tier 3 · `sdd: true`
> `covers` in `feature_list.json`: **`NFR-SEC-03`, `NFR-OBS-01`, `FR-AUTH-09`,
> `FR-UX-03`, `FR-RT-01`, `FR-MENU-08`, `FR-AI-08`** — ratified by the owner
> 2026-08-31 (GQ1).
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen id(s)
> it implements and is verifiable by at least one concrete test that asserts a
> value. **Exactly one `SHALL` / `SHALL NOT` per `R<n>`, counted mechanically.**

## Purpose in one sentence

The `planner_api` Lambda **shell**: the HTTP and event boundary shaped exactly as
`docs/rest_api_contract.md` specifies — routing, camelCase serialization, RFC
9457 errors, the `HttpOnly`-cookie REQUEST authorizer, `ETag`/`Cache-Control`
emission, the SQS producer call site and the EventBridge rollover entry point —
calling application services and adapters it does not itself build.

## Scope boundary — the substrate is feature 27

This feature was split on 2026-08-31 (GQ4, owner). Everything below the
transport boundary — the real DynamoDB adapters, the `GenerationQueue` port and
its SQS adapter, the new `planner_core.application` use cases, the
`RuleRepository` port change and the `DisabledDay` value object — is
**feature 27 `rest_api_persistence_and_services`**, spec'd in
`specs/rest_api_persistence_and_services/`. This feature `depends_on` it.

The dividing line: a requirement lives here if it is about **the shape of what
crosses the Lambda's edge** (an HTTP request/response, an authorizer event, a
scheduled event, an SQS send). It lives in feature 27 if it is about **what a
port or a use case guarantees**.

## Gate rulings folded in (2026-08-31)

- **GQ1** — `covers` ratified as the seven ids above. No id is invented; every
  one is frozen in `docs/requirements.md`.
- **GQ2** — this feature only **emits** the marker (`R28`–`R30`). The
  `If-None-Match` parse, the marker-first read (`docs/data_model.md` §5.5) and
  the `304` mapping are **feature 26 `realtime_channel_transport`**, whose
  acceptance item 1 already claims them. The former `R28`/`R29` are deleted
  here and are not restated in any form.
- **GQ3** — the `RuleRepository` port change and the deterministic rule-id
  scheme are resolved and moved to feature 27 (`specs/rest_api_persistence_and_services/design.md`
  §3). This feature keeps only the routing of `PUT`/`DELETE /v1/rules/{ruleId}`
  (`R31`) and the `422 UNSATISFIABLE_RULE_SET` error mapping (`R21`).
- **GQ4** — split, as described above.

## Depends on

`feature_list.json` lists `depends_on: [14, 27]` — `persistence_ports` (done)
and `rest_api_persistence_and_services` (the substrate this shell calls). This
spec also builds on, as shipped code: feature 15 `auth_flow`
(`application.authentication.authenticate`, `Role`, the auth exceptions),
feature 18 `realtime_channel_persistence` (the version-returning writes whose
value becomes the `ETag`), feature 13 `rollover_job_logic`
(`domain.rollover.roll_over`), feature 10 `generation_request`
(`domain.generation` — the `idPeticionIA` derivation), and `planner_core.messages`.

---

## R1
Implements: NFR-SEC-03, FR-AUTH-09

WHEN the api Lambda emits the session cookie, it SHALL set the cookie
attributes to `HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=2592000`
(`docs/rest_api_contract.md` §5).

## R2
Implements: NFR-SEC-03

The api Lambda SHALL NOT expose a route whose HTTP method is `GET` and whose
handler performs a write through any repository port
(`docs/rest_api_contract.md` §5 rule 3 — the `SameSite=Lax` CSRF invariant).

## R3
Implements: FR-AUTH-09

WHEN handling `DELETE /v1/session`, the api Lambda SHALL emit a `Set-Cookie`
header that expires the session cookie (`Max-Age=0`) on the same response that
advances `validoDesde` (`docs/rest_api_contract.md` §5, AP28).

## R4
Implements: NFR-SEC-03, FR-AUTH-09

WHEN `POST /v1/session` authenticates a user, the api Lambda SHALL return the
session token in the `Set-Cookie` response header.

## R5
Implements: NFR-SEC-03

The api Lambda SHALL NOT place a session token in any response body.

## R6
Implements: FR-AUTH-09

The api Lambda SHALL provide a `REQUEST`-type API Gateway Lambda authorizer
whose identity source is the `Cookie` request header
(`docs/rest_api_contract.md` §5).

## R7
Implements: FR-AUTH-09

WHEN the authorizer evaluates a request, it SHALL determine the caller by
calling `planner_core.application.authentication.authenticate` with the token
read from the session cookie.

## R8
Implements: FR-AUTH-09

WHEN `authenticate` returns an account, the authorizer SHALL pass `userId`,
`role` and `passwordResetRequired` to the handler in the authorizer context
(`docs/rest_api_contract.md` §5).

## R9
Implements: FR-AUTH-09

IF the session cookie is absent, unparseable, or `authenticate` raises
`SessionExpired`, THEN the authorizer SHALL return a Deny result.

## R10
Implements: FR-AUTH-09

The authorizer SHALL evaluate `authenticate` on every request it is invoked for,
without reusing a decision computed for an earlier request
(`docs/rest_api_contract.md` §7 Q2 — TTL 0; the API Gateway cache-TTL value
itself is feature 21 IaC, `design.md` §6).

## R11
Implements: FR-AUTH-09

WHEN a route requires a role that the request's authorizer-context `role` does
not hold, the api Lambda SHALL respond `403` with `code` `FORBIDDEN`.

## R12
Implements: FR-AUTH-09

The api Lambda SHALL NOT read the account record to decide a role gate or a
`passwordResetRequired` gate, taking both from the authorizer context
(`docs/rest_api_contract.md` §5 — "without a second `AP2` read").

## R13
Implements: FR-AUTH-09

WHILE the request's authorizer-context `passwordResetRequired` is `true`, the
api Lambda SHALL respond `403` with `code` `PASSWORD_RESET_PENDING` to every
route other than `PUT /v1/session/password` and `DELETE /v1/session`
(`docs/rest_api_contract.md` §5).

## R14
Implements: FR-UX-03

WHEN the api Lambda returns any error response, it SHALL serialise the body as
an RFC 9457 `application/problem+json` document
(`docs/rest_api_contract.md` §4).

## R15
Implements: FR-UX-03

The api Lambda SHALL include in every error body a `code` extension member
holding the `SCREAMING_SNAKE` value that `docs/rest_api_contract.md` §4 assigns
to that condition.

## R16
Implements: FR-UX-03

WHEN the api Lambda builds an error body, it SHALL set the `detail` member to
the corresponding constant from `planner_core.messages`.

## R17
Implements: FR-UX-03

The api Lambda SHALL NOT construct a user-facing message string in the handler
or authorizer layer.

## R18
Implements: FR-UX-03

WHEN a request is syntactically malformed — unparseable JSON body, a missing
required field, a create body carrying a client-supplied `id`, or an unparseable
path parameter — the api Lambda SHALL respond with HTTP status `400`
(`docs/rest_api_contract.md` §3.0, §4).

## R19
Implements: FR-UX-03

WHEN a well-formed request is rejected by a domain rule, the api Lambda SHALL
respond with the HTTP status that `docs/rest_api_contract.md` §4 maps to the
raised domain exception.

## R20
Implements: FR-UX-03, NFR-OBS-01

WHEN a handler catches a `PlannerError` that `docs/rest_api_contract.md` §4 does
not map, the api Lambda SHALL respond `500` with `code` `INTERNAL_ERROR`.

## R21
Implements: FR-UX-03

WHEN a use case raises `UnsatisfiableRuleSet`, the api Lambda SHALL respond
`422` with `code` `UNSATISFIABLE_RULE_SET` and a `details.conflicts` member
(`docs/rest_api_contract.md` §4). *(The check that raises it is feature 27.)*

## R22
Implements: NFR-OBS-01

WHEN the api Lambda handles an HTTP request, an authorizer invocation or a
scheduled invocation, it SHALL emit one structured log record through the
standard-library `logging` module.

## R23
Implements: NFR-OBS-01

The api Lambda SHALL NOT write to standard output or standard error with
`print` (`docs/architecture.md` §6).

## R24
Implements: NFR-OBS-01

WHEN the api Lambda maps a fault to a `500` response, it SHALL log the causing
exception with its traceback.

## R25
Implements: NFR-OBS-01

The api Lambda SHALL NOT place a traceback or stack frame in any response body
(`docs/conventions.md` § *Error handling*).

## R26
Implements: NFR-SEC-03, NFR-OBS-01

The api Lambda SHALL route each access pattern in `docs/data_model.md` §4 —
except `AP3`, `AP9` and `AP29`, which `docs/rest_api_contract.md` §2 marks
internal-only — and the computed `GET /v1/live-weeks` endpoint to the HTTP
method and path template that `docs/rest_api_contract.md` §1–§2 assigns it.

## R27
Implements: NFR-SEC-03

The api Lambda SHALL NOT expose an HTTP route for `AP9` (Obtener semana +
ingredientes) or an `?include=ingredients` query parameter on
`GET /v1/weeks/{weekId}` (`docs/rest_api_contract.md` §1, §7 Q13).

## R28
Implements: FR-RT-01

WHEN the api Lambda returns a `200` response for `GET /v1/weeks/{weekId}`,
`GET /v1/weeks/{weekId}/summary`, `GET /v1/library/recipes`,
`GET /v1/shopping-list` or `GET /v1/rules`, it SHALL set the `ETag` response
header to the resource's `marcaCambio` value as a strong validator
(`docs/rest_api_contract.md` §6).

## R29
Implements: FR-RT-01

WHEN the api Lambda returns a success response for a mutation of a week, the
library, the shopping list or the rules, it SHALL set the `ETag` response
header to the `marcaCambio` value returned by that repository write
(`docs/rest_api_contract.md` §6).

## R30
Implements: FR-RT-01

The api Lambda SHALL set `Cache-Control: no-store` on every response
(`docs/rest_api_contract.md` §6).

## R31
Implements: FR-RT-01

The api Lambda SHALL map `PUT /v1/rules/{ruleId}` to the single-rule write
operation (`AP23`) and `DELETE /v1/rules/{ruleId}` to the single-rule delete
operation (`AP24`) of `planner_core.application.rule_editing`
(`docs/rest_api_contract.md` §2, §7 Q5).

## R32
Implements: FR-MENU-08

The api package SHALL provide a non-HTTP entry point, invoked by EventBridge
Scheduler, that runs week rollover by delegating to
`planner_core.domain.rollover` (`docs/rest_api_contract.md` §7 Q8,
`docs/architecture.md` §1.2).

## R33
Implements: FR-MENU-08, NFR-SEC-03

The api Lambda SHALL NOT expose any HTTP route that triggers week rollover
(`docs/rest_api_contract.md` §1 — "a job, not a request").

## R34
Implements: FR-MENU-08

WHEN the scheduled rollover entry point is invoked more than once for the same
rollover boundary, the api Lambda SHALL leave the persisted state identical to a
single invocation (`FR-MENU-08`, `G-61`; delegates to feature 13's idempotent
transition).

## R35
Implements: FR-AI-08

WHEN handling `POST /v1/generations`, the api Lambda SHALL place the generation
request on the `api`→`ai` SQS queue through the `GenerationQueue` port
(`docs/architecture.md` §1.2, `docs/rest_api_contract.md` §7 Q12).

## R36
Implements: FR-AI-08

The `planner_api` distribution SHALL NOT import an AWS Bedrock or other AI
provider SDK module (`docs/architecture.md` §1.2 — the split is real).

## R37
Implements: FR-AI-08

WHEN `POST /v1/generations` names an `idPeticionIA` whose result is already
stored (`AP26`), the api Lambda SHALL return `200` with that stored result
(`FR-AI-08`; the server-authoritative `attempt` ordinal and the per-slot
in-flight `409` are feature 17's spec, `docs/rest_api_contract.md` §3.5).

## R38
Implements: FR-UX-03

WHEN the api Lambda serialises a JSON response body, it SHALL use English
`camelCase` member names under the `/v1` base path
(`docs/rest_api_contract.md` §1, §3.0, §7 Q6).

## R39
Implements: FR-AUTH-09

The api Lambda SHALL NOT accept an `author` / `añadidoPor` value from any
request body, taking it from the authenticated caller instead
(`docs/rest_api_contract.md` §3.0 rule 3).

## R40
Implements: FR-MENU-08

WHEN the scheduled rollover entry point runs, the api Lambda SHALL satisfy the
`ArchiveRepository` port call with an implementation that retains no archived
week (owner ruling 2026-08-31 — archive is parked for the MVP;
`docs/data_model.md` §9 parks `FR-ARCH-02`, which has no item type).

## R41
Implements: FR-MENU-08, NFR-OBS-01

WHEN the no-op `ArchiveRepository` receives an `ArchivedWeek`, it SHALL log the
discarded record through the standard-library `logging` module.

---

## Coverage map

### Frozen requirement → `R<n>`

| Requirement | Covered by |
|---|---|
| `NFR-SEC-03` | R1, R2, R4, R5, R26, R27, R33 |
| `NFR-OBS-01` | R20, R22, R23, R24, R25, R26, R41 |
| `FR-AUTH-09` | R1, R3, R4, R6, R7, R8, R9, R10, R11, R12, R13, R39 |
| `FR-UX-03` | R14, R15, R16, R17, R18, R19, R20, R21, R38 |
| `FR-RT-01` | R28, R29, R30, R31 |
| `FR-MENU-08` | R32, R33, R34, R40, R41 |
| `FR-AI-08` | R35, R36, R37 |

Two citation notes:

- **`R38` (camelCase) cites `FR-UX-03`, not `FR-AUTH-09`.** `FR-UX-03` reserves
  es-ES for user-facing *strings*; English identifiers on the wire are the
  complement of that rule (`docs/conventions.md`, `contract` §7 Q6). An earlier
  draft cited `FR-AUTH-09` here, which was wrong.
- **`FR-RULE-07` is no longer cited by this feature.** The whole-set
  satisfiability check moved to feature 27; what remains here (`R21`) is the
  error-format mapping, which is `FR-UX-03`.

### `feature_list.json` acceptance criterion → `R<n>`

| Acceptance item | Covered by |
|---|---|
| 1 — `/v1` base path, camelCase JSON, RFC 9457 with `code` + verbatim `detail`, 400 vs 422 | R14, R15, R16, R17, R18, R19, R38 |
| 2 — every `contract` §2 pattern routed; `AP3`/`AP9`/`AP29`/rollover have none; no `GET` route writes | R2, R26, R27, R33 |
| 3 — `ETag` emission on pollable `200` and on mutations; `Cache-Control: no-store`; `If-None-Match`/`304` is feature 26 | R28, R29, R30 |
| 4 — REQUEST authorizer on the cookie, TTL 0, `userId`/`role`/`passwordResetRequired` in context, gated without a second `AP2` read | R6, R7, R8, R9, R10, R11, R12, R13 |
| 5 — `PUT`/`DELETE /v1/rules/{ruleId}` routed to the single-rule ops; `422 UNSATISFIABLE_RULE_SET` mapping | R31, R21 |
| 6 — `?include=ingredients` (AP9) not public | R27 |
| 7 — non-HTTP scheduled rollover entry point in this package, idempotent, archiving through a no-op `ArchiveRepository` that logs and retains nothing | R32, R33, R34, R40, R41 |
| 8 — api never ships the Bedrock SDK; api→ai is an SQS enqueue | R35, R36, R37 |
| 9 — structured logging, no `print`, no traceback in a body | R22, R23, R24, R25 |
| 10 — session cookie shape and logout | R1, R3, R4, R5, R39 |
| 11 — adapters / application services / port change are feature 27 | — (scope statement; see `design.md` §0) |
