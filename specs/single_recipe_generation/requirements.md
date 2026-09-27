# single_recipe_generation — Requirements

> Feature 28 · tier 3 · the single-recipe AI submit-then-poll path, end to end:
> `POST /v1/generations` (`type:"recipe"`), the server-authoritative `attempt`,
> the `ai` worker branch, and the SPA authoring tab.
> `feature_list.json` `covers` is empty; the ids below are taken from the
> feature's description: `FR-AI-01`, `-02`, `-08`, `-09`, `-10`. Also cited:
> `FR-CAND-03` (library authoring reuses AI), `FR-LIB-04` (reference picker),
> `FR-UX-03` (es-ES), `NFR-AI-01` (cost gate, consumed from feature 17).
>
> EARS + approval gate: `docs/specs.md`. Contract: `docs/rest_api_contract.md`
> §3.5, §3.6, §4, §7 Q3 — reconciled by the leader with the owner's rulings
> (gaps Part AB, G-92); `design.md` §1 mirrors it. Decisions: `G-70`, `G-17` (no quota), `G-68`. Data: `docs/data_model.md`
> §2 (`idPeticionIA`), §4.6.

Terminology: a **record** is the `PETICIONIA#<key>/METADATA` item. A record is
**terminal** when its `estado` is neither `pending` nor `running`. The
**scope** of a request is its target slot, or `library` when the target is the
library. Concurrent generations for one scope are allowed (FR-AI-09).

---

## Submit (api)

## R1
Implements: FR-AI-01

WHEN `POST /v1/generations` carries `type: "recipe"` and a `source` of kind
`specification` with `ingredients` and `tools`, the system SHALL enqueue one
single-recipe generation and answer `202 Accepted` with `status: "pending"`
and a `Location` header for `/v1/generations/{generationId}`.

## R2
Implements: FR-AI-02

WHEN `POST /v1/generations` carries `type: "recipe"` and a `source` of kind
`reference` with a `recipeId` and `extraSpecifications`, the system SHALL
enqueue one single-recipe generation carrying the referenced library recipe's
snapshot and answer `202 Accepted` with `status: "pending"`.

## R3
Implements: FR-AI-02

IF the `recipeId` of a `reference` source names no library recipe, THEN the
system SHALL answer `404 RECIPE_NOT_FOUND` and enqueue nothing.

## R4
Implements: FR-AI-01, FR-AI-02

IF the body has an unknown `type`, `source.kind` or `target.kind`, a missing or
mistyped field, an invalid `weekId`, or a `day`/`slot` outside its range, THEN
the system SHALL answer `400` and enqueue nothing.

## R5
Implements: FR-AI-01, FR-CAND-03

WHEN the `target` is `{"kind":"library"}`, the system SHALL accept the request
without any week, day or slot.

## R6
Implements: FR-AI-10

IF the request body carries an `attempt` field, THEN the system SHALL answer
`400`.

## Attempt and idempotency key

## R7
Implements: FR-AI-08

The system SHALL derive the single-recipe idempotency key as a deterministic
hash of the scope, the source kind and content, and the attempt ordinal.

## R8
Implements: FR-AI-08

The single-recipe idempotency key SHALL be unaffected by the order of the
`ingredients`, `tools` or `extraSpecifications` lists.

## R9
Implements: FR-AI-08

Two single-recipe requests differing in scope, source kind or source content
SHALL derive different idempotency keys.

## R10
Implements: FR-AI-08

The whole-week idempotency key SHALL remain byte-identical to its value before
this feature for every whole-week request.

## R11
Implements: FR-AI-08, FR-AI-10

The system SHALL derive `attempt` as the count of consecutive terminal records
stored for the request, counted from attempt 0, and never from a client field.

## R12
Implements: FR-AI-08

WHEN the derived key already has a `pending` or `running` record, the system
SHALL answer `200 OK` with that record and enqueue nothing.

## R13
Implements: FR-AI-10

WHEN the request's attempt-0 record is terminal and the identical request is
submitted again, the system SHALL derive attempt 1, enqueue a fresh generation
and answer `202 Accepted`.

## R14
Implements: FR-AI-08

WHILE two identical submissions derive the same key concurrently, the system
SHALL invoke the AI provider at most once.

## R15
Implements: FR-AI-10

WHEN a terminal record is discarded through `DELETE /v1/generations/{id}`, the
next identical submission SHALL derive the discarded record's attempt.

## R16
Implements: FR-AI-09

WHEN a slot already has a `pending` or `running` single-recipe record and a
submission arrives whose derived key differs, the system SHALL accept it with
`202 Accepted` and enqueue it independently.

## R17
Implements: FR-AI-01

IF a `specification` source has an empty `ingredients` list, THEN the system
SHALL answer `422 MISSING_INGREDIENTS` and enqueue nothing.

## R18
Implements: FR-AI-01

IF a `specification` source has an empty `tools` list, THEN the system SHALL
answer `422 MISSING_TOOLS` and enqueue nothing.

## Worker (ai)

## R19
Implements: FR-AI-01

WHEN the worker claims a specification-source message, the system SHALL build
the prompt with `build_specification_prompt` from the message's ingredients,
tools and prompt-version id.

## R20
Implements: FR-AI-02

WHEN the worker claims a reference-source message, the system SHALL build the
prompt with `build_reference_prompt` from the message's recipe snapshot,
extra specifications and prompt-version id.

## R21
Implements: FR-AI-08, FR-AI-09

IF the message's record is not claimable, THEN the system SHALL NOT invoke the
AI provider.

## R22
Implements: NFR-AI-01, FR-UX-03

WHILE the generation gate is disabled, the system SHALL record a `failed`
result carrying the es-ES `AI_GENERATION_UNAVAILABLE` message without invoking
the AI provider.

## R23
Implements: FR-AI-10

WHEN the provider output passes `validate_and_preview`, the system SHALL record
status `completed` with the previewed recipe, in the wire recipe shape, as the
result.

## R24
Implements: FR-AI-10

The worker SHALL NOT call `WeekRepository` while running a single-recipe
generation.

## R25
Implements: FR-AI-10

The worker SHALL NOT bump any `marcaCambio` while running a single-recipe
generation.

## R26
Implements: FR-AI-09, FR-UX-03

IF the provider raises or the output fails validation, THEN the system SHALL
record status `failed` with the es-ES failure message as the result.

## R27
Implements: FR-AI-09

WHEN one record in an SQS batch fails, the system SHALL still process the
batch's other records.

## Read and discard (already built, verified here)

## R28
Implements: FR-AI-10

WHEN a single-recipe record is `completed`, `GET /v1/generations/{id}` SHALL
return its status and the previewed recipe in `result`.

## R29
Implements: FR-AI-10

The recipe in a `completed` result SHALL be accepted unchanged by the
`source: "generation"` candidate path.

## R30
Implements: FR-AI-10

WHEN `DELETE /v1/generations/{id}` is called, the system SHALL remove the
record and return `204`.

## Frontend

## R31
Implements: FR-AI-01, FR-UX-03

WHEN the user submits the from-scratch AI form, the SPA SHALL `POST` a
`specification` body built from the form's ingredients and tools.

## R32
Implements: FR-AI-02, FR-LIB-04

WHEN the user picks a library recipe and submits extra specifications, the SPA
SHALL `POST` a `reference` body with the picked `recipeId`.

## R33
Implements: FR-AI-10

WHILE a submitted generation is `pending` or `running`, the SPA SHALL poll
`GET /v1/generations/{id}` on a short interval and show a loading state.

## R34
Implements: FR-AI-10

WHEN the polled record is `completed`, the SPA SHALL show the previewed recipe
with accept, discard and regenerate actions.

## R35
Implements: FR-AI-10

WHEN the user accepts a preview, the SPA SHALL save it as a candidate or as a
library recipe according to the authoring target.

## R36
Implements: FR-AI-10

WHEN the user discards a preview, the SPA SHALL call
`DELETE /v1/generations/{id}` and clear the preview.

## R37
Implements: FR-AI-10

WHEN the user regenerates, the SPA SHALL re-`POST` the form's current
specifications, which the user may have adjusted.

## R38
Implements: FR-AI-10

The SPA SHALL NOT send an `attempt` field nor compute any idempotency key.

## R39
Implements: FR-AI-09, FR-UX-03

WHEN the polled record is `failed`, the SPA SHALL show the es-ES message from
`result`.

## R40
Implements: FR-UX-03

The SPA SHALL NOT show the "not available yet" notice once submit is wired.

## R41
Implements: FR-AI-10

WHEN the AI form unmounts, the SPA SHALL stop polling.
