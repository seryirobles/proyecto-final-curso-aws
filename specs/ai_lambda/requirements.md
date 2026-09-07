# ai_lambda — Requirements

> Feature 17 · tier 3 · the `ai` Lambda worker shell: an SQS consumer that runs
> whole-week AI generation and writes results back.
> `covers` = `{FR-AI-09, NFR-AI-01}`. `FR-AI-08` (idempotency key + record —
> features 10/27), `FR-AI-10`/`FR-AI-11`/`FR-AI-12` (features 10/12), `FR-RT-01`
> (the `marcaCambio` bump inside `WeekRepository`, feature 18) and `FR-UX-03`
> are **cited for context only**. `FR-CAND-04` is cited by **R21** as
> consumed-not-owned (candidate authorship — feature 5 `week_plan_model`), the
> same convention feature 27 uses for `FR-AI-10`/`FR-AI-11`; `covers` is
> unchanged.
>
> EARS notation and the approval gate: `docs/specs.md`. Frozen text:
> `docs/requirements.md` FR-AI-09 (L108), NFR-AI-01 (L205). Decisions:
> `docs/architecture.md` §1.2 / §1.2.6, `docs/gaps_and_resolutions.md` G-70,
> G-81, G-88. Contract: `docs/rest_api_contract.md` "AI generation — HTTP
> shape" (~L167), §3.5, §7 Q3. Data model: `docs/data_model.md` §4.6, §4.7.

Scope note: only **whole-week** generation requests are enqueued today
(`_submit_generation` rejects `type != "week"`). Single-recipe generation —
its submit/enqueue path, the server-authoritative `attempt` ordinal, the true
per-slot `409`, and the `contract` body shape — is **feature 28
`single_recipe_generation`** (owner, 2026-09-06), not this feature.
Requirements are phrased per **target slot** so feature 28 reuses them; the
`WeekRepository` write requirements (R6–R10) are explicitly whole-week only.

---

## R1
Implements: FR-AI-09

WHEN a message is received from the `api`→`ai` queue, the system SHALL process
it as one generation request identified by the `idPeticionIA` the message
carries.

## R2
Implements: FR-AI-09

WHEN a generation request resolves to more than one target slot, the system
SHALL invoke the AI provider separately for each target slot.

## R3
Implements: FR-AI-09

WHEN a whole-week generation request resolves to more than one target slot, the
system SHALL persist each successful slot's candidate in its own
`WeekRepository` write.

## R4
Implements: FR-AI-09

IF processing one target slot fails, THEN the system SHALL continue processing
the remaining target slots.

## R5
Implements: FR-AI-09

IF processing one target slot fails, THEN the system SHALL keep every candidate
already persisted for the target slots that succeeded.

## R6
Implements: FR-AI-09

WHEN a whole-week target slot's AI output passes validation, the system SHALL
append the resulting candidate to that slot through the `WeekRepository` port.

## R7
Implements: FR-AI-09

The system SHALL NOT persist a generated whole-week candidate through any code
path other than the `WeekRepository` port.

## R8
Implements: FR-AI-09

WHEN appending a generated candidate to a slot, the system SHALL derive the new
slot contents from a read of that slot taken during the same processing step.

## R9
Implements: FR-AI-09

The system SHALL NOT remove or replace an existing candidate or the definitive
selection of a target slot.

## R10
Implements: FR-AI-09

IF a target slot holds a definitive selection at the moment its candidate is
about to be written, THEN the system SHALL skip that slot.

## R11
Implements: FR-AI-09

BEFORE invoking the AI provider for a received message, the system SHALL
atomically transition that message's stored generation record from `pending` to
`running`.

## R12
Implements: FR-AI-09

IF the atomic transition to `running` does not succeed, THEN the system SHALL
NOT invoke the AI provider for that message.

## R13
Implements: FR-AI-09

WHEN a received message's stored generation record is already `running` or
`completed`, the system SHALL NOT invoke the AI provider for that message.

## R14
Implements: FR-AI-09

WHEN every target slot of a message has been processed, the system SHALL record
the run's terminal status and each target slot's outcome in the stored
generation record.

## R15
Implements: FR-AI-09

The system SHALL record the run's terminal status only after every successful
slot's candidate has been persisted.

## R16
Implements: NFR-AI-01

BEFORE each AI provider invocation, the system SHALL read the deployment-managed
generation kill-switch.

## R17
Implements: NFR-AI-01

WHILE the kill-switch indicates that AI generation is disabled, the system SHALL
NOT invoke the AI provider.

## R18
Implements: NFR-AI-01

WHILE the kill-switch indicates that AI generation is disabled, the system SHALL
record each target slot not yet processed with the es-ES message
`AI_GENERATION_UNAVAILABLE`.

## R19
Implements: NFR-AI-01

The system SHALL evaluate the generation kill-switch as a single deployment-wide
state.

## R20
Implements: NFR-AI-01

The system SHALL NOT read, maintain, or increment any per-user generation
counter or quota.

## R21
Implements: FR-CAND-04

WHEN the worker appends a generated candidate to a slot, it SHALL attribute that
candidate to the submitting user identified on the received message.
*(`FR-CAND-04` is owned by feature 5 `week_plan_model`; cited here, not added to
`covers`. The submitter's id reaches the worker on the enriched SQS message —
`specs/rest_api_persistence_and_services/` R40.)*
