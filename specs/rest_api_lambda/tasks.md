# rest_api_lambda — Tasks

> Feature 16 · ordered. Each step `[ ]` with the `R<n>` ids it covers.
> `implementer` ticks `[x]`.
> **Feature 27 `rest_api_persistence_and_services` must be done first** — every
> task below calls its ports and use cases.

## Transport skeleton

- [ ] T1 — `errors.py`: the `PlannerError → (status, code, message-constant,
  details)` table from `contract` §4; `detail` pulled from `planner_core.messages`;
  unmapped → 500/`INTERNAL_ERROR`; `UnsatisfiableRuleSet` → 422 +
  `details.conflicts`. Covers: R14, R15, R16, R17, R19, R20, R21.
- [ ] T2 — `serialization.py`: camelCase encode/decode; reject a request body
  carrying `id` or `author`/`añadidoPor` (→ 400); path-param parsers
  (`weekId` ISO-week, `day`, `slot`) raising a 400-tagged error. Covers: R18, R38, R39.
- [ ] T3 — `routing.py`: `(method, resourceTemplate) → handler` table for every
  `contract` §2 row + `GET /v1/live-weeks`; no entry for `AP3`/`AP9`/`AP29`/
  rollover; assert no `GET` handler writes. Covers: R2, R26, R27, R33.
- [ ] T4 — `handler.py`: parse event → route → call one use case → serialise or
  map exception; one structured `logging` record per invocation; `Cache-Control:
  no-store` on every response; no `print`; no traceback in body. Covers: R22,
  R23, R24, R25, R30.

## Auth

- [ ] T5 — `authorizer.py`: REQUEST-type entry, `Cookie` identity source, calls
  `authentication.authenticate`, emits allow + `{userId, role,
  passwordResetRequired}` context or `Deny`; re-evaluates every call. Covers: R6,
  R7, R8, R9, R10.
- [ ] T6 — Session routes in `handler.py`: `POST /v1/session` sets the cookie
  (`HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=2592000`) and returns the
  token only there; `DELETE /v1/session` clears the cookie + advances
  `validoDesde`. Covers: R1, R3, R4, R5.
- [ ] T7 — Context gating: role gate → 403 `FORBIDDEN`; `passwordResetRequired`
  → 403 `PASSWORD_RESET_PENDING` except `PUT /v1/session/password` and
  `DELETE /v1/session`; no account read on either path. Covers: R11, R12, R13.

## Marker emission

- [ ] T8 — Pollable read handlers set `ETag` = the read service's marker
  (strong validator) on 200; mutation handlers set `ETag` = the write's returned
  marker. Covers: R28, R29.

## Rules routes

- [ ] T9 — `PUT`/`DELETE /v1/rules/{ruleId}` handlers → feature 27's
  `rule_editing`; decode `ruleId` to the natural key; `GET /v1/rules` returns
  the service's resolved payload. Covers: R31.

## Scheduled rollover + AI hop

- [ ] T10 — `scheduled.py`: EventBridge entry → `wiring` reads the clock →
  `domain.rollover.roll_over` → persist via ports; idempotent on re-invocation;
  no route. Covers: R32, R33, R34.
- [ ] T10b — No-op `ArchiveRepository` (archive parked for the MVP, owner
  2026-08-31, `design.md` §7): accepts the `ArchivedWeek`, retains nothing, logs
  the discarded record via `logging`; `wiring.py` injects it. Covers: R40, R41.
- [ ] T11 — `POST /v1/generations` handler → feature 27's
  `generation_submission`; enqueue via the `GenerationQueue` port; stored
  `idPeticionIA` returns 200 with the stored result. Covers: R35, R37.
- [ ] T12 — Import-scan test asserting `planner_api` imports no Bedrock/AI SDK
  module; confirm `uv export --package planner-api --no-dev` shows none. Covers: R36.

## Wiring + close

- [ ] T13 — `wiring.py`: composition root; selects feature 27's adapters by
  environment (fake stack for `pytest`, real for deployed); reads the clock for
  the authorizer and the scheduled entry; the only module naming a concrete
  adapter. Covers: R10, R32, R35.
- [ ] T14 — Full test pass per `design.md` §9: routing, authorizer, context
  gating, error mapping, marker emission, session cookie, scheduled entry,
  no-AI-SDK scan, serialization. `./init.sh` green. Covers: all.
- [ ] T15 — `progress/impl_rest_api_lambda.md`: traceability table
  (`R<n>` → test), test result, anything the contract did not anticipate.
