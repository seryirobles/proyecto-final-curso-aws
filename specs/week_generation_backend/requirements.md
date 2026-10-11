# week_generation_backend — Requirements

> Feature 36 · tier 3 · depends on 17, 27, 28. `covers` is empty by design
> (owner request 2026-10-11, prerequisite of feature 35): the `FR-*` below are
> **cited, not claimed**. No frozen requirement changes: `FR-AI-03` names the
> three modes but leaves `mix` unspecified, so R1-R15 define it (owner ruling
> 2026-10-11). `G-66` already says the week "fills as far as the library
> allows, with honest gaps". Decisions: `G-18`, `G-19`, `G-66`. Contract:
> `docs/rest_api_contract.md` §3.5, §7 Q4. Slot vocabulary: the contract wins
> (`done`, `error{code,message}`).
>
> Slot statuses: `pending | running | done | error`. Run statuses: `pending`,
> `running`, then `completed | partial | failed`.

## Mode semantics

## R1
Implements: FR-AI-03

WHEN a whole-week run has mode `library_only`, the system SHALL NOT invoke the AI provider.

## R2
Implements: FR-AI-03, FR-AI-11

WHEN a whole-week run has mode `library_only`, the system SHALL append a library recipe snapshot as a candidate to each open slot for which an eligible library recipe exists.

## R3
Implements: FR-AI-12

IF no eligible library recipe remains for an open slot of a `library_only` run, THEN the system SHALL record that slot as `error` with code `insufficient_library_recipes`.

## R4
Implements: FR-AI-03

WHEN a whole-week run has mode `ai_only`, the system SHALL NOT read the library.

## R5
Implements: FR-AI-03

WHEN a whole-week run has mode `mix`, the system SHALL complete the library fill of every open slot before invoking the AI provider for any slot.

## R6
Implements: FR-AI-03

WHEN a whole-week run has mode `mix`, the system SHALL invoke the AI provider only for open slots that received no library candidate.

## R7
Implements: FR-AI-11, FR-AI-03

The system SHALL consider only the open slots returned by target resolution (no pinned, disabled, past or definitive-held slot) for library fill.

## R8
Implements: FR-AI-03

The system SHALL exclude from library fill every recipe whose case-folded name equals that of a meal already in the week or already picked in the same run.

## R9
Implements: FR-AI-04

WHILE a category has a remaining count and an eligible recipe of that category exists, the system SHALL assign to each open slot, in chronological order, a recipe of a category with a remaining count.

## R10
Implements: FR-AI-04

WHEN no eligible recipe of a category with a remaining count exists for an open slot, the system SHALL assign to that slot any eligible recipe.

## R11
Implements: FR-AI-08

The system SHALL order eligible library recipes by a shuffle seeded with the generation's idempotency key, so equal inputs yield equal picks.

## R12
Implements: FR-AI-04

WHEN library candidates have been written in a `mix` run, the system SHALL reduce the category counts given to the AI by the categories of those candidates.

## R13
Implements: FR-AI-11

The system SHALL NOT remove or replace an existing candidate or definitive selection when writing a library candidate.

## R14
Implements: FR-AI-11

IF a slot holds a definitive selection when its library candidate is about to be written, THEN the system SHALL skip the write and record the slot as `done`.

## R15
Implements: NFR-AI-01

WHILE the generation kill-switch indicates that AI generation is disabled, the system SHALL still perform library fill.

## R16
Implements: FR-AI-03

The system SHALL read the library in the worker only through the `RecipeRepository` port.

## Live per-slot progress

## R17
Implements: FR-AI-12

WHEN a worker has claimed a whole-week message and resolved its targets, the system SHALL record every open slot as `pending` before processing any slot.

## R18
Implements: FR-AI-12

WHEN the worker begins an AI generation for a slot, the system SHALL record that slot as `running` before invoking the AI provider.

## R19
Implements: FR-AI-12

WHEN a slot's candidate has been persisted, the system SHALL record that slot as `done`.

## R20
Implements: FR-AI-12

IF a slot fails, THEN the system SHALL record that slot as `error` with a `code` (a `GenerationFailureReason` value) and an es-ES `message`.

## R21
Implements: FR-AI-09

The system SHALL write each slot's progress as an independent update of that slot's entry only.

## R22
Implements: FR-AI-12

The system SHALL NOT use the values `completed`, `failed` or a `message` field at slot level.

## R23
Implements: FR-AI-12

WHILE any slot of a run is `pending` or `running`, the system SHALL report the run as `running`.

## R24
Implements: FR-AI-12

WHEN every slot of a run is `done` or the run has no slot, the system SHALL record the run as `completed`.

## R25
Implements: FR-AI-12, FR-AI-09

WHEN every slot of a run is `done` or `error` and at least one is each, the system SHALL record the run as `partial`.

## R26
Implements: FR-AI-12

WHEN every slot of a run is `error`, the system SHALL record the run as `failed`.

## R27
Implements: FR-AI-09

The system SHALL record a terminal run status only after the last slot outcome has been recorded.

## R28
Implements: FR-AI-12

WHEN `GET /v1/generations/{generationId}` addresses a whole-week run, the system SHALL return `generationId`, `status` and `slots` ordered by day then slot.

## R29
Implements: FR-AI-12

The system SHALL include `error{code,message}` in a slot entry only when that slot's status is `error`.

## R30
Implements: FR-AI-12

The system SHALL NOT include `result` in the `GET` body of a whole-week run.

## R31
Implements: FR-AI-12

WHILE a whole-week run has no recorded slots, the system SHALL return `slots` as an empty list.

## R32
Implements: FR-AI-08

WHEN `POST /v1/generations` of type `week` hits a stored record, the system SHALL return the same body shape as the `GET`.

## R33
Implements: FR-AI-10

The system SHALL keep the `GET` body of a single-recipe run unchanged.

## R34
Implements: FR-AI-05

WHEN a whole-week run is submitted, the system SHALL store with its record the week, mode, effective rules and prompt version id.

## Per-slot retry

## R35
Implements: FR-AI-12

The system SHALL dispatch `POST /v1/generations/{generationId}/slots/{day}/{slot}/retry` for role `user`.

## R36
Implements: FR-AI-12

WHEN a retry targets a slot with status `error` that is still an open slot, the system SHALL set that slot `pending` and the run `running` in one conditional write.

## R37
Implements: FR-AI-12

WHEN a retry is accepted, the system SHALL respond `202 Accepted` with `Location` and the `GET` body.

## R38
Implements: FR-AI-09

IF the targeted slot's status is `pending`, `running` or `done`, THEN the system SHALL respond `409` with code `SLOT_NOT_RETRYABLE`.

## R39
Implements: FR-AI-11

IF the targeted slot is no longer an open slot (definitive present, past day, disabled day), THEN the system SHALL respond `409` with code `SLOT_NOT_RETRYABLE`.

## R40
Implements: FR-AI-09

WHEN two retries target the same slot concurrently, the system SHALL accept exactly one.

## R41
Implements: FR-AI-12

IF the generation does not exist, THEN the system SHALL respond `404` with code `GENERATION_NOT_FOUND`.

## R42
Implements: FR-AI-12

IF the run has no entry for the slot, THEN the system SHALL respond `404` with code `GENERATION_SLOT_NOT_FOUND`.

## R43
Implements: FR-AI-12

IF `{day}` is outside 1-7 or `{slot}` is not 1 or 2, THEN the system SHALL respond `400`.

## R44
Implements: FR-AI-05

The system SHALL generate a retry against the effective rules stored with the parent run.

## R45
Implements: FR-AI-08

The system SHALL enqueue exactly one message per accepted retry.

## R46
Implements: FR-AI-08

IF enqueuing an accepted retry fails, THEN the system SHALL restore the slot to `error`.

## R47
Implements: FR-AI-08

WHEN the worker receives a retry message, the system SHALL transition that slot from `pending` to `running` atomically before any provider invocation.

## R48
Implements: FR-AI-08

IF the transition to `running` does not succeed, THEN the system SHALL NOT process the retry message.

## R49
Implements: FR-AI-03

WHEN the worker processes a retry, the system SHALL apply the parent run's mode to that slot alone.

## R50
Implements: NFR-AI-01

BEFORE each AI provider invocation of a retry, the system SHALL read the generation kill-switch.

## R51
Implements: FR-AI-09

WHEN a retry's slot outcome has been recorded, the system SHALL recompute the run status from all slot entries.

## R52
Implements: FR-AI-09

The system SHALL NOT modify the entries of slots other than the retried slot.

## R53
Implements: FR-CAND-04

WHEN a retry writes a candidate, the system SHALL attribute it to the user who requested the retry.
