# realtime_channel_transport — Requirements

> Feature 26 · tier 3 · the HTTP-facing half of real-time support (split from
> the original `realtime_channel` 2026-08-27, `G-88`, `architecture.md` §1.2.4):
> the `api` Lambda's conditional-GET short-circuit, the shopping-list re-sync
> marker-bump collapse, and the frontend's adaptive polling engine.
> `covers` = `{FR-RT-01, FR-RT-02, FR-RT-03}`.
>
> Frozen text: `docs/requirements.md` L167–169 (`FR-RT-01`/`-02`/`-03`), L238
> (US19 traceability). Decisions: `docs/architecture.md` §1.2.4 (P3, adaptive
> polling + conditional GET, decided 2026-08-27), `docs/gaps_and_resolutions.md`
> `G-88` (Part X). Contract: `docs/rest_api_contract.md` §6 ("Marker transport
> — `ETag`/`If-None-Match`") and §2 (Poll column). Data model:
> `docs/data_model.md` §1.1 (marker atomicity), §4.4 (re-sync's per-item-bump
> note), §4.7 (`AP29`), §5.3 (lock release), §5.5 (bump/read ordering).
>
> **Boundary.** Feature 18 `realtime_channel_persistence` (done) owns the
> `MarcaCambio` item type, `current_version()` reads and the version-returning
> writes on all four ports — this feature *consumes* those, it does not
> re-specify them. Feature 16 `rest_api_lambda` (done) owns emitting `ETag` on
> `200`/mutation responses and `Cache-Control: no-store` — this feature adds
> the missing half: parsing `If-None-Match` and mapping to `304`
> (`rest_api_lambda`'s design.md §0 names this explicitly as feature 26's job).
> Feature 27 (done) owns the re-sync composition this feature amends in place.
> Feature 20 `frontend_spa` (pending) is this feature's only consumer — it
> instantiates the polling hook per view; it does not change how the hook
> itself decides intervals or markers.

---

## R1
Implements: FR-RT-01

WHEN a `GET` request for a pollable resource carries a single quoted
`If-None-Match` value, the system SHALL read that resource's current
`marcaCambio` before computing the resource's payload.

## R2
Implements: FR-RT-01

IF the marker read for R1 equals the parsed `If-None-Match` value, THEN the
system SHALL return a `304` response with no body.

## R3
Implements: FR-RT-01

WHEN returning a `304` response, the system SHALL set the response's `ETag`
header to the same value the request's `If-None-Match` header carried.

## R4
Implements: FR-RT-01

IF the marker read for R1 does not equal the parsed `If-None-Match` value,
THEN the system SHALL compute and return the resource's full payload as a
`200` response.

## R5
Implements: FR-RT-01

The system SHALL NOT compute a pollable resource's full payload when it
returns a `304` response for that request.

## R6
Implements: FR-RT-01

WHEN a `GET` request for a pollable resource carries an absent, malformed,
wildcard (`*`), or multi-valued `If-None-Match` header, the system SHALL
compute and return the resource's full payload without attempting a `304`.

## R7
Implements: FR-RT-01

The system SHALL apply R1–R6's conditional-GET handling only to the `GET`
routes for a live week (and its summary), the library, the shopping list, and
the rules.

## R8
Implements: FR-RT-01

WHEN shopping-list re-sync finds one or more items that differ from what is
stored, the system SHALL write all of those items in a single transaction.

## R9
Implements: FR-RT-01

WHEN that single transaction commits, the system SHALL increment
`COMPRA#<idLista>`'s `marcaCambio` exactly once as part of it.

## R10
Implements: FR-RT-01

IF shopping-list re-sync finds no item that differs from what is stored, THEN
the system SHALL NOT increment `COMPRA#<idLista>`'s `marcaCambio`.

## R11
Implements: FR-RT-01

The system SHALL NOT reference `marcaCambio` in the `ConditionExpression` of
the re-sync transaction.

## R12
Implements: FR-RT-01

WHEN polling a resource, the system SHALL send that resource's held marker as
a quoted `If-None-Match` request header.

## R13
Implements: FR-RT-01

WHEN a poll response is `304`, the system SHALL leave the resource's held data
and held marker unchanged.

## R14
Implements: FR-RT-01

WHEN a poll response is `200`, the system SHALL replace the resource's held
data and held marker with the response's body and `ETag`.

## R15
Implements: FR-RT-01

The system SHALL maintain each polled resource's held marker,
consecutive-failure count, and connection-loss indication independently of
every other resource being polled.

## R16
Implements: FR-RT-03

WHILE the document is visible and the window is focused, the system SHALL
schedule each poll for a resource after the configured active interval.

## R17
Implements: FR-RT-03

WHILE the document is hidden or the window is not focused, the system SHALL
schedule each poll for a resource after the configured background interval.

## R18
Implements: FR-RT-03

WHEN the document regains visible-and-focused state, the system SHALL issue a
poll immediately rather than waiting for a delay already scheduled.

## R19
Implements: FR-RT-03

WHEN a poll fails, the system SHALL increase that resource's
consecutive-failure count by one.

## R20
Implements: FR-RT-03

WHEN a poll succeeds, the system SHALL reset that resource's
consecutive-failure count to zero.

## R21
Implements: FR-RT-03

WHEN scheduling a poll after one or more consecutive failures, the system
SHALL double the applicable interval once per consecutive failure, capped at
the configured maximum.

## R22
Implements: FR-RT-03

WHEN scheduling a poll after one or more consecutive failures, the system
SHALL apply random jitter within the configured ratio to the capped delay.

## R23
Implements: FR-RT-03

WHEN a resource's consecutive-failure count reaches the configured threshold,
the system SHALL indicate loss of the real-time connection for that resource.

## R24
Implements: FR-RT-03

WHEN a poll succeeds while connection loss is indicated for a resource, the
system SHALL clear that indication.

## R25
Implements: FR-RT-01, FR-RT-02

WHEN a mutation's response marker equals the resource's held marker plus one,
the system SHALL store that response marker as the new held marker.

## R26
Implements: FR-RT-01, FR-RT-02

IF a mutation's response marker does not equal the resource's held marker
plus one, THEN the system SHALL discard that response marker and refetch the
resource.
