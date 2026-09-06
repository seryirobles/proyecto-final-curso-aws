# rest_api_persistence_and_services — Tasks

> Feature 27 · ordered. Each step `[ ]` with the `R<n>` ids it covers.
> `implementer` ticks `[x]`. Feature 16 `rest_api_lambda` depends on this
> feature; build it first.

## Port and domain changes (`planner_core`)

- [x] T1 — Add `DisabledDay` frozen value object to `domain/rules.py`; add the
  `rule_id` helper deriving `cat#…` / `pin#…` / `day#…` from a rule
  (`design.md` §3). Covers: R13, R14.
- [x] T2 — Change `RuleRepository` (`ports/rules.py`): remove `save(RuleSet)`,
  add `save_rule(rule) -> int` and `delete_rule(rule_id) -> int` with feature
  18's marker contract in the docstrings. Covers: R10, R11, R12.
- [x] T3 — Add `ports/generation_queue.py`: a `GenerationQueue` `Protocol` with
  no queue technology in its signature. Covers: R25.
- [x] T4 — Update `core/tests/support/fakes.py`: `FakeRuleRepository` gains
  `save_rule`/`delete_rule` (natural-key storage, counter bump); add
  `FakeGenerationQueue`. Covers: R10, R11, R25.
- [x] T5 — Retarget `backend/tests/contract/test_rule_repository_contract.py` to
  `save_rule`/`delete_rule`; keep feature 18's marker assertions. Covers: R10,
  R11, R12.

## Application use cases (`planner_core/application/`)

- [x] T6 — `rule_editing.py`: `get()` → apply the change via the existing
  `domain/rules` mutators → `save_rule`/`delete_rule`; unsatisfiable result
  raises and never writes. Covers: R15, R16, R17, R29.
- [x] T7 — `week_editing.py` (`AP10`–`AP13`) and thin read services for `AP8`,
  `AP14`, `AP18`, `AP22`; every mutation returns the write's marker. Covers:
  R9, R29, R30.
- [x] T8 — `library_editing.py` (`AP15`–`AP17`) incl. the `contract` §3.4 pin
  cascade: unconfirmed delete reports the affected pins, confirmed delete
  removes recipe + pins. Covers: R18, R19, R29.
- [x] T9 — `shopping_editing.py` (`AP19`–`AP21`) + the re-sync composition:
  acquire the lock, read the week in-process (`AP9`), additive merge on
  normalized name + unit, release the lock. Covers: R20, R21, R22, R23, R24, R29.
- [x] T10 — `generation_submission.py`: derive `idPeticionIA` via
  `domain/generation`, check the stored result (`AP26`), enqueue through
  `GenerationQueue` only on a miss. Covers: R27, R28, R29.
- [x] T11 — Layer scan tests: `planner_core` imports no `boto3` / `planner_api`;
  no use-case signature holds an HTTP or AWS type. Covers: R5, R30.

## Adapters (`planner_api/adapters/`)

- [x] T12 — `pyproject.toml`: add `boto3` runtime dep, `moto` dev dep
  (`architecture.md` §1.3). Covers: R1.
- [x] T13 — `adapters/dynamo/_table.py`: `(PK, SK)` builders for every item type
  in `data_model.md` §1/§3, the Spanish⇄English attribute map, and the
  `TransactWriteItems` helper whose second leg is `ADD marcaCambio 1`. Covers:
  R2, R3, R6.
- [x] T14 — `adapters/dynamo/accounts.py`: `AccountRepository` incl. the `AP4`
  username-reservation second leg and `validoDesde` (`data_model.md` §5.1/§5.2).
  Covers: R1, R2, R3.
- [x] T15 — `adapters/dynamo/weeks.py`: `WeekRepository`, `begins_with` SK scopes
  per `data_model.md` §3; `get_week` carries the full ingredient snapshot
  (`AP9`). Covers: R1, R2, R3, R6.
- [x] T16 — `adapters/dynamo/recipes.py` and `adapters/dynamo/rules.py`
  (single-item `AP23`/`AP24` writes keyed by the derived rule id). Covers: R1,
  R2, R3, R6, R10, R11.
- [x] T17 — `adapters/dynamo/shopping_list.py`: items, `delete_checked_items`
  (no-op does not bump), and the lock comparing `ttl` itself
  (`data_model.md` §5.3). Covers: R1, R2, R3, R6, R23.
- [x] T18 — `current_version` on all four pollable adapters: `ConsistentRead`,
  `ProjectionExpression=marcaCambio`, `0` before any write. Covers: R8.
- [x] T19 — Marker-safety scan test extended to the adapters: no
  `ConditionExpression` references `marcaCambio`. Covers: R7.
- [x] T20 — `adapters/sqs.py`: `GenerationQueue` producer, `SendMessage` to the
  `api`→`ai` queue, queue URL from configuration. Covers: R26.
- [x] T21 — Register the DynamoDB adapters into every suite in
  `backend/tests/contract/` (moto-backed) so fake and real pass one suite
  (`architecture.md` §3.2). Covers: R4.

## Close

- [x] T22 — Full test pass per `design.md` §9. `./init.sh` green. Covers: all.
- [x] T23 — `progress/impl_rest_api_persistence_and_services.md`: traceability
  table (`R<n>` → test), test result, anything `data_model.md` did not
  anticipate.

## Reopened 2026-09-06 — AP27 discard + read markers

- [x] T24 — `ports/generation_queue.py`: add `discard(idempotency_key: str) ->
  None` to the `GenerationQueue` `Protocol` (no queue tech in the signature;
  absent-key discard is a no-op). Covers: R31, R33.
- [x] T25 — `adapters/sqs.py`: implement `discard` as an unconditional
  `DeleteItem PETICIONIA#<hash> / METADATA` — no `ConditionExpression`. Covers:
  R32, R33.
- [x] T26 — `backend/core/tests/support/fakes.py`: `FakeGenerationQueue` gains
  `discard` (drop the key; missing key = no-op). Covers: R31, R33.
- [x] T27 — `backend/tests/contract/test_generation_queue_contract.py`: submit →
  `discard` → `stored_generation` returns `None`; `discard` of a never-submitted
  key does not raise; scan asserts no `ConditionExpression` on the `discard`
  path (parametrized fake + moto adapter). Covers: R31, R32, R33.
- [x] T28 — `application/week_editing.load_week`: return a frozen result with the
  slot map and the week `marcaCambio`, marker read first; update callers/tests.
  Covers: R34, R35.
- [x] T29 — `application/library_editing.list_library`: return a frozen result
  with the entries and the library `marcaCambio`, marker first. Covers: R34, R35.
- [x] T30 — `application/rule_editing.read_rules`: return a frozen result with
  the `RuleSet` and the rules `marcaCambio`, marker first. Covers: R34, R35.
- [x] T31 — `application/shopping_editing.list_shopping`: return a frozen result
  with the items and the shopping-list `marcaCambio`, marker first. Covers: R34,
  R35.
- [x] T32 — Read-service tests: returned marker equals the port's
  `current_version()`; a spy fake asserts `current_version` runs before the
  payload read; a frozen-instance test per new result object. Covers: R34, R35.
- [x] T33 — Full test pass per `design.md` §9; `./init.sh` green; update
  `progress/impl_rest_api_persistence_and_services.md` traceability. Covers: all
  reopened `R<n>`.
