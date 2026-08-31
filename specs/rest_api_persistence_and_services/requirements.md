# rest_api_persistence_and_services — Requirements

> Feature 27 · tier 3 · `sdd: true`
> `covers` in `feature_list.json`: **`NFR-BKP-01`, `FR-RT-01`, `FR-RULE-07`,
> `FR-SHOP-06`, `FR-AI-08`**.
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen id(s)
> it implements and is verifiable by at least one concrete test that asserts a
> value. **Exactly one `SHALL` / `SHALL NOT` per `R<n>`, counted mechanically.**

## Purpose in one sentence

Everything below the api Lambda's transport edge: the real DynamoDB adapters for
every `api`-side port, the `GenerationQueue` port and its SQS adapter, the
`planner_core.application` use cases the handlers call, and the `RuleRepository`
per-rule port change that `docs/rest_api_contract.md` §7 Q5 requires.

## Where this feature came from

Split out of feature 16 `rest_api_lambda` on 2026-08-31 (GQ4, owner ruling: the
original spec was too big for one feature). Feature 16 keeps the Lambda shell —
`handler.py`, `routing.py`, `errors.py`, `serialization.py`, `wiring.py`,
`authorizer.py`, `scheduled.py`, the SQS producer call site and `ETag` emission.
**Feature 16 `depends_on` this feature**: the shell calls what is built here.

The dividing line: a requirement lives in feature 16 if it is about **the shape
of what crosses the Lambda's edge**; it lives here if it is about **what a port,
an adapter or a use case guarantees**.

## Gate ruling folded in — GQ3 (owner, 2026-08-31)

`RuleRepository` gets `save_rule(rule) -> int` and `delete_rule(ruleId) -> int`
(both marker-bumping); `save(RuleSet)` is removed; `DisabledDay` becomes a frozen
value object in `domain/rules.py`; rule ids are deterministic natural keys
(`cat#<category>`, `pin#<day>#<slot>`, `day#<day>`). `R9`–`R13` and `design.md`
§3 carry it.

## Depends on

`feature_list.json` lists `depends_on: [14]` (`persistence_ports`, done). This
spec also builds on, as shipped code:

- feature 15 `auth_flow` — `AccountRepository`'s shape and the auth exceptions.
- feature 18 `realtime_channel_persistence` — `current_version` and the
  version-returning writes on the four pollable ports, plus their contract
  suites, which the real adapters must now also pass.
- feature 13 `rollover_job_logic` — `domain.rollover`, whose ports the scheduled
  entry resolves.
- feature 10 `generation_request` — `domain.generation`'s `idPeticionIA`
  derivation.
- features 4–12 — the domain models every use case orchestrates.

---

## Adapters

## R1
Implements: NFR-BKP-01

The system SHALL provide, under `planner_api/adapters/dynamo/`, a DynamoDB-backed
implementation of `AccountRepository`, `WeekRepository`, `RecipeRepository`,
`RuleRepository` and `ShoppingListRepository`.

## R2
Implements: NFR-BKP-01

WHEN a DynamoDB adapter reads or writes an item, it SHALL use the partition key,
sort key and Spanish attribute names that `docs/data_model.md` §1 and §3 assign
to that item type.

## R3
Implements: NFR-BKP-01

A DynamoDB adapter SHALL NOT return a Spanish persisted attribute name in any
value it hands to `planner_core` (`docs/data_model.md` §1 — "map at the adapter
boundary, not in the domain").

## R4
Implements: NFR-BKP-01

The DynamoDB adapters SHALL pass the existing per-port contract suites in
`backend/tests/contract/` unchanged, alongside the in-memory fakes
(`docs/architecture.md` §3.2).

## R5
Implements: NFR-BKP-01

`planner_core` SHALL NOT import `boto3`, any other AWS SDK module, or any
`planner_api` module (`docs/architecture.md` §3.1 rule 3).

## Change markers

## R6
Implements: FR-RT-01

WHEN a DynamoDB adapter performs a mutating operation, it SHALL bump the
resource's `marcaCambio` inside the same `TransactWriteItems` as the data write
it marks (`docs/data_model.md` §1.1, §5.5).

## R7
Implements: FR-RT-01

A DynamoDB adapter SHALL NOT reference `marcaCambio` in a write's
`ConditionExpression` (`docs/data_model.md` §1.1 — it is read-only client
metadata, never a write precondition).

## R8
Implements: FR-RT-01

WHEN a DynamoDB adapter serves `current_version`, it SHALL issue a
strongly-consistent read projecting only `marcaCambio` (`AP29`,
`docs/data_model.md` §4.7).

## R9
Implements: FR-RT-01

WHEN an application use case mutates a week, the library, the shopping list or
the rules, it SHALL return the `marcaCambio` value that the repository write
returned (`docs/rest_api_contract.md` §6 — feature 16 surfaces it as the `ETag`).

## The `RuleRepository` port change (GQ3)

## R10
Implements: FR-RT-01

The system SHALL expose on `RuleRepository` a per-rule write operation returning
the rule set's `marcaCambio` as advanced by that operation
(`docs/rest_api_contract.md` §7 Q5 consequence ii, `AP23`).

## R11
Implements: FR-RT-01

The system SHALL expose on `RuleRepository` a per-rule delete operation
returning the rule set's `marcaCambio` as advanced by that operation
(`docs/rest_api_contract.md` §7 Q5 consequence ii, `AP24`).

## R12
Implements: FR-RT-01

The system SHALL NOT retain on `RuleRepository` a whole-`RuleSet` blob write
operation (`docs/rest_api_contract.md` §7 Q5 — `AP23`/`AP24` are single-item
writes, and a whole-set write makes `FR-RT-02` last-write-wins apply to the
entire set).

## R13
Implements: FR-RT-01

The system SHALL derive a rule's identifier deterministically from that rule's
natural key, as `design.md` §3 tabulates (`cat#<category>`, `pin#<day>#<slot>`,
`day#<day>`).

## R14
Implements: FR-RULE-04, FR-RT-01

The system SHALL represent a disabled day as a frozen value object in
`planner_core.domain.rules`, so a disabled day is an individually addressable
rule item (`docs/data_model.md` §4.5 — one `REGLA#<idRegla>` item per rule).

## Rule-set consistency

## R15
Implements: FR-RULE-07

WHEN a per-rule write or delete is requested, the rule-editing use case SHALL
evaluate the satisfiability of the whole rule set that results from applying the
change in memory, before committing the single-item write
(`docs/rest_api_contract.md` §7 Q5 consequence i).

## R16
Implements: FR-RULE-07

IF the rule set resulting from a per-rule write or delete is unsatisfiable, THEN
the rule-editing use case SHALL raise `UnsatisfiableRuleSet` carrying the
conflicting rules (feature 16 maps it to `422 UNSATISFIABLE_RULE_SET`).

## R17
Implements: FR-RULE-07

IF the rule set resulting from a per-rule write or delete is unsatisfiable, THEN
the rule-editing use case SHALL NOT call the repository write.

## R18
Implements: FR-RULE-07

WHEN an unconfirmed delete of a library recipe referenced by at least one pin
rule is requested, the library-editing use case SHALL report the affected pin
rules instead of deleting the recipe (`docs/rest_api_contract.md` §3.4).

## R19
Implements: FR-RULE-07

WHEN a delete of a library recipe referenced by pin rules is confirmed, the
library-editing use case SHALL delete every pin rule referencing that recipe
(`FR-RULE-07` — "remove the affected rule upon confirmation").

## Shopping-list re-sync

## R20
Implements: FR-SHOP-06

WHEN the re-sync use case runs, it SHALL obtain the in-scope definitive meals'
ingredients by calling `WeekRepository` in-process (`AP9`,
`docs/rest_api_contract.md` §7 Q13 — the composition is `AP9`'s only consumer).

## R21
Implements: FR-SHOP-06

The re-sync use case SHALL NOT delete any shopping-list item (`FR-SHOP-06` —
"Nothing is ever removed").

## R22
Implements: FR-SHOP-06

The re-sync use case SHALL NOT modify a checked item (`FR-SHOP-06` — "Checked
items are never modified", `FR-SHOP-08`).

## R23
Implements: FR-SHOP-10, FR-SHOP-06

WHEN the re-sync use case starts, it SHALL acquire the shopping-list lock
through `ShoppingListRepository.acquire_lock` before reading the week
(`docs/data_model.md` §5.3, `docs/rest_api_contract.md` §3.3).

## R24
Implements: FR-SHOP-10, FR-SHOP-06

IF the shopping-list lock is held by another owner and not expired, THEN the
re-sync use case SHALL raise `ShoppingListLockHeld` (feature 16 maps it to
`409 SHOPPING_LIST_LOCK_HELD`).

## Generation hand-off

## R25
Implements: FR-AI-08

The system SHALL define a `GenerationQueue` port in `planner_core.ports` whose
signature names no queue technology (`docs/architecture.md` §3.1 —
storage/transport-agnostic ports).

## R26
Implements: FR-AI-08

The system SHALL provide an SQS-backed implementation of `GenerationQueue` under
`planner_api/adapters/` (`docs/architecture.md` §1.2, `contract` §7 Q12).

## R27
Implements: FR-AI-08

WHEN the generation-submission use case handles a request, it SHALL derive the
`idPeticionIA` using `planner_core.domain.generation`
(`docs/data_model.md` §2 — the key format is not re-derived here).

## R28
Implements: FR-AI-08

IF a stored result already exists for the derived `idPeticionIA` (`AP26`), THEN
the generation-submission use case SHALL return that stored result without
calling `GenerationQueue.submit`.

## Application layer

## R29
Implements: NFR-BKP-01, FR-RT-01

The system SHALL provide a `planner_core.application` use case for each mutating
flow the api Lambda routes — week editing, library editing, shopping editing,
rule editing and generation submission (`docs/conventions.md` — a handler calls
one use case).

## R30
Implements: NFR-BKP-01

A `planner_core.application` use case SHALL accept only ports and plain values
as arguments, holding no HTTP, event or AWS type in its signature
(`docs/architecture.md` §3.1 rule 2).

---

## Coverage map

### Frozen requirement → `R<n>`

| Requirement | Covered by |
|---|---|
| `NFR-BKP-01` | R1, R2, R3, R4, R5, R29, R30 |
| `FR-RT-01` | R6, R7, R8, R9, R10, R11, R12, R13, R14, R29 |
| `FR-RULE-07` | R15, R16, R17, R18, R19 |
| `FR-SHOP-06` | R20, R21, R22, R23, R24 |
| `FR-AI-08` | R25, R26, R27, R28 |

**Cited but owned elsewhere** (`Implements:` may name a frozen id this feature
does not `cover`, the way `realtime_channel_persistence` cited `FR-RT-02`):

- `FR-RULE-04` (R14) — the rule-type catalogue is feature 6 `rules_model`. R14
  only makes an existing rule type individually addressable.
- `FR-SHOP-10` (R23, R24) — the lock is feature 8 `shopping_list_state`. R23/R24
  only preserve its serialization guarantee at the new use-case boundary.
- `NFR-BKP-01` is used here the way feature 14 `persistence_ports` used it: it
  is the one frozen id that names the persistent datastores as a set ("users,
  recipes, menus, past weeks, the shopping list and its archived snapshots,
  rules"). Feature 14 built the ports against it; this feature builds the real
  adapters against the same id. Flagged for the gate — see `design.md` §7.

### `feature_list.json` acceptance criterion → `R<n>`

| Acceptance item | Covered by |
|---|---|
| 1 — real DynamoDB adapter per `api`-side port, Spanish attributes mapped at the boundary | R1, R2, R3, R5 |
| 2 — the adapters pass the existing contract suites alongside the fakes | R4 |
| 3 — `marcaCambio` bumped inside the write's transaction, never a `ConditionExpression`, `current_version` strongly consistent and marker-only | R6, R7, R8, R9 |
| 4 — `RuleRepository` gains `save_rule`/`delete_rule`, loses `save(RuleSet)`; deterministic natural-key rule ids; `DisabledDay` value object | R10, R11, R12, R13, R14 |
| 5 — whole-set satisfiability on each per-rule write; unsatisfiable never commits; the pin cascade on library delete | R15, R16, R17, R18, R19 |
| 6 — re-sync composition calls `AP9` internally, is purely additive and never touches a checked item, serialized by the `FR-SHOP-10` lock | R20, R21, R22, R23, R24 |
| 7 — `GenerationQueue` port + SQS adapter; idempotent submission returns the stored result without enqueuing | R25, R26, R27, R28 |
| 8 — the new use cases live in `planner_core/application/`, ports and plain values only | R29, R30 |
