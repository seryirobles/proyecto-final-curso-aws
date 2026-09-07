# ai_lambda — Tasks

> Ordered. Each `[ ]` names the `R<n>` it covers. Ports/use case in
> `planner_core`; adapters, wiring and the handler in `planner_ai`. Read
> `design.md` first. All eight spec-gate questions were ruled by the owner
> 2026-09-06 (`design.md` §5–§10). T3 depends on the feature 27 reopen landing
> `GenerationQueue.claim` / `record_result` first
> (`specs/rest_api_persistence_and_services/` R36–R39).

## Ports and fakes (`planner_core`)

- [x] T1 — Add `AiProvider` Protocol in `planner_core/ports/ai_provider.py`
  (prompt value object in, `RawRecipeOutput` out; no SDK import). Covers: R2.
- [x] T2 — Add `GenerationGate` Protocol in
  `planner_core/ports/generation_gate.py` (`is_generation_enabled() -> bool`,
  no user argument). Covers: R16, R19, R20.
- [x] T3 — Consume `GenerationQueue.claim` / `record_result` from the feature 27
  reopen (`specs/rest_api_persistence_and_services/` R36–R39); do not edit the
  port here. If the reopen has not landed, this feature is blocked on it.
  Covers: R11, R12, R13, R14, R15.
- [x] T4 — Add `FakeAiProvider`, `FakeGenerationGate` and extend
  `FakeGenerationQueue` (`claim` counter, `record_result` capture) in
  `backend/core/tests/support/fakes.py`. Covers: R2, R11–R18.

## Orchestration use case (`planner_core/application`)

- [x] T5 — Add `week_generation.py` with `run_week_generation(..., author, ...)`
  and the `WeekGenerationOutcome` frozen dataclass (+ its frozen-instance test):
  claim → read occupancy → `resolve_targets` → per-slot loop (candidate authored
  by `author`) → `record_result`.
  Covers: R1, R2, R3, R4, R5, R6, R8, R10, R11, R12, R13, R14, R15, R21.
- [x] T6 — In the per-slot loop, read `gate.is_generation_enabled()` before each
  provider call; on disabled, invoke nothing and record
  `AI_GENERATION_UNAVAILABLE` per unprocessed slot. Covers: R16, R17, R18.
- [x] T7 — Enforce the write path: candidates only via
  `week_editing.add_slot_candidate`; skip a slot that is definitive at write
  time. Covers: R6, R7, R8, R9, R10.

## Use-case tests (`backend/core/tests`)

- [x] T8 — `test_week_generation.py`: per-slot failure isolation (provider raises
  on one slot), partial results kept, one `save_slot` per success, each written
  candidate authored by the passed `author`. Covers: R2, R3, R4, R5, R21.
- [x] T9 — Additive/invariant test: pre-set candidate + definitive, generate,
  assert nothing removed and definitive slot skipped. Covers: R8, R9, R10.
- [x] T10 — Idempotent-invocation tests: `claim` False → zero provider calls;
  already-terminal record → zero calls; `record_result` ordered after the last
  `save_slot`. Covers: R11, R12, R13, R14, R15.
- [x] T11 — Cost-cap tests: gate disabled → zero provider calls, every slot
  result is `AI_GENERATION_UNAVAILABLE`. Covers: R16, R17, R18.
- [x] T12 — Scan test (mirrors `test_no_ambient_time.py`): no per-user
  generation counter / quota read or attribute in `application/week_generation.py`
  or `planner_ai/`. Covers: R19, R20.

## Adapters (`planner_ai`)

- [x] T13 — Copy `dynamo/_table.py`, `dynamo/_meal.py`, `dynamo/weeks.py` (and
  whatever else the `WeekRepository` adapter needs) into
  `planner_ai/adapters/dynamo/`. No shared workspace member (owner, 2026-09-06).
  Covers: R6.
- [x] T14 — Add `dynamo/generations.py`: conditional `claim` update and the
  `record_result` write on `PETICIONIA#<hash>/METADATA`. Covers: R11, R14, R15.
- [x] T15 — Add `adapters/bedrock.py`: `BedrockAiProvider`, `BEDROCK_MODEL_ID`
  constant + `AI_MODEL_ID` env override, prompt→messages rendering,
  response→`RawRecipeOutput` parsing, named parse exception. Covers: R2.
- [x] T16 — Add `adapters/ssm.py`: `SsmGenerationGate` reading
  `/planner/<env>/ai-generation-enabled` with a ~5 s in-process TTL cache.
  Covers: R16, R19.
- [x] T17 — Add `boto3` runtime dep + `moto` dev dep to
  `backend/lambda_ai/pyproject.toml`. Covers: R2, R6, R16.

## Wiring and entry point (`planner_ai`)

- [x] T18 — Add `wiring.py`: build the real stack (Bedrock, SSM, DynamoDB week +
  generations adapters), read the clock, pass the civil date down. Covers: R1.
- [x] T19 — Add `handler.py`: iterate the SQS `Records`, parse each body
  (`idPeticionIA`, `weekId`, `mode`, `ruleOverride`, enriched `effectiveRules`,
  `promptVersionId`, `authorUserId`), call `run_week_generation` per record,
  isolate per-record failures. Covers: R1, R4, R21.

## Contract tests and gate

- [x] T20 — New contract suites: `AiProvider`, `GenerationGate`,
  `GenerationQueue.claim`/`record_result` — fake + `moto`. Covers: R2, R11–R18.
- [x] T21 — Parametrize `backend/tests/contract/test_week_repository_contract.py`
  over **both** the `planner_api` and `planner_ai` DynamoDB adapters (plus the
  fake), so a drift between the two copies fails the suite (owner-mandated
  2026-09-06). Covers: R6.
- [x] T22 — Extend the `planner_core` layer scan: no `boto3` / Bedrock import in
  `planner_core`. Covers: R7.
- [x] T23 — Handler test: two-record SQS event → two use-case runs, one failing
  record does not abort the other. Covers: R1, R4.
- [x] T24 — `./init.sh` green (ruff, mypy, pytest unit + contract, frontend gate
  untouched); update `progress/current.md`.
