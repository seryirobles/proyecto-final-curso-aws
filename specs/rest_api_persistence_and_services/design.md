# rest_api_persistence_and_services — Design

> Feature 27 · tier 3 · the `api` Lambda's **substrate**: `planner_api/adapters/`
> (DynamoDB + SQS), the new `planner_core/application/` use cases, and one
> `planner_core/ports/` change. Read `requirements.md` first.
> Sources: `docs/data_model.md` §1, §3–§5; `docs/rest_api_contract.md` §2, §3.3,
> §3.4, §7 (Q5, Q12, Q13); `docs/architecture.md` §1.2, §3–§3.2.

## 0. Governing decisions already made elsewhere — not re-opened

- **The Lambda shell is feature 16** — see `specs/rest_api_lambda/`. Nothing
  here parses an HTTP event, builds a response or maps an exception to a status.
- The datastore is decided: DynamoDB, single table `data`, no secondary indexes
  (`docs/architecture.md` §1.2.1, `docs/data_model.md` §1, §7).
- No `docs/architecture.md` §2 item is open (all `P<n>` decided).
- `Clock` is a port; domain code takes a `date`/instant, never a `Clock`
  (tier-1 ruling). An application use case that needs the time takes the instant
  as an argument; `wiring.py` (feature 16) reads the clock.

## 1. Layering (`docs/architecture.md` §3, §3.1)

| Piece | Layer | Notes |
|---|---|---|
| `adapters/dynamo/_table.py` | `planner_api/adapters/` | Shared key builders, `TransactWriteItems` helper, the marker-bump leg, attribute (de)serialisation. |
| `adapters/dynamo/{accounts,weeks,recipes,rules,shopping_list}.py` | `planner_api/adapters/` | Real `boto3` implementations. Spanish attribute names ⇄ English domain here (`data_model.md` §1). |
| `adapters/sqs.py` | `planner_api/adapters/` | `GenerationQueue` producer — `SendMessage` to the `api`→`ai` queue. |
| `ports/generation_queue.py` | `planner_core/ports/` | New `Protocol`. No queue technology in the signature (`R25`). |
| `ports/rules.py` | `planner_core/ports/` | Port change — `save_rule` / `delete_rule` replace `save(RuleSet)` (§3). |
| `domain/rules.py` | `planner_core/domain/` | New `DisabledDay` frozen value object + the rule-id derivation (§3). |
| `application/{week,library,shopping,rule}_editing.py`, `application/generation_submission.py` | `planner_core/application/` | Orchestrate domain + ports (§4). |

`planner_api` gains `boto3` as a runtime dependency (first time; justified here
per `docs/architecture.md` §1.3 — it is the `api` adapter closure) and `moto` as
a dev dependency for adapter tests.

## 2. Files created / modified

**`backend/lambda_api/src/planner_api/adapters/`** (all new):
`__init__.py`, `sqs.py`, `dynamo/__init__.py`, `dynamo/_table.py`,
`dynamo/accounts.py`, `dynamo/weeks.py`, `dynamo/recipes.py`,
`dynamo/rules.py`, `dynamo/shopping_list.py`.

**`backend/lambda_api/pyproject.toml`** — add `boto3` runtime dep, `moto` dev dep.

**`backend/core/src/planner_core/ports/rules.py`** — replace `save(RuleSet)`
with `save_rule` / `delete_rule` (§3).

**`backend/core/src/planner_core/ports/generation_queue.py`** — new port.
Reopened 2026-09-06: add `discard(idempotency_key: str) -> None` (`R31`, `R33`)
as a sibling of `stored_generation` / `submit` — absent-key discard is a no-op.
Reopened 2026-09-06 (feature 17 gate): add `claim(idempotency_key: str) -> bool`
and `record_result(idempotency_key: str, status: str, per_slot: list) -> None`
(`R36`–`R39`) — the `ai` worker's idempotent-consumer guard and result write-back
(§3b).

**`backend/core/src/planner_core/domain/rules.py`** — add `DisabledDay`; add the
`rule_id` derivation helper.

**`backend/core/src/planner_core/application/`** — new modules:
`week_editing.py` (candidates CRUD, definitive select/clear — `AP10`–`AP13`),
`library_editing.py` (`AP15`–`AP17` + the §3.4 pin cascade),
`shopping_editing.py` (`AP19`–`AP21` + the re-sync composition, §5),
`rule_editing.py` (get → domain mutate → `save_rule`/`delete_rule`),
`generation_submission.py` (derive `idPeticionIA`, check `AP26`, enqueue).
Reads (`AP8`, `AP14`, `AP18`, `AP22`, live-weeks) reuse the existing
`application.live_weeks` and add thin read services as needed.
Reopened 2026-09-06 (feature 17 gate, `R40`–`R43`): `generation_submission`
grows `recipes: RecipeRepository`, `author: str` and `config: ConfigPort`
parameters; on the fresh-submit path it resolves the active prompt version
through `resolve_active_prompt_version(config)` (feature 24's guard — fix round 1
finding 2), writes the resolved pinned-slot candidates and puts the resolved
`effective_rules` + prompt-version id into the `GenerationQueue.submit` payload —
see §3b, §3c.

Reopened 2026-09-06 (`R34`, `R35`): the four pollable read services —
`week_editing.load_week`, `library_editing.list_library`,
`rule_editing.read_rules`, `shopping_editing.list_shopping` — each return a
small frozen result object carrying the resource data **and** `marker: int`
(same domain as `current_version`), read marker-first. This deletes feature
16's `adapters/markers.py` workaround (that feature's `routing.py` reads the
marker off the DTO instead). `GET /v1/weeks/{weekId}/summary` is a
definitive-only serialization projection of `load_week`'s result (`contract`
§2 — "no new access pattern"), so it needs no separate use case and shares the
week marker.

**`backend/core/tests/support/fakes.py`** — `FakeRuleRepository` gains
`save_rule`/`delete_rule`; add `FakeGenerationQueue` (reopened 2026-09-06: it
also gains the discard op — drop the key, missing key = no-op; and 2026-09-06
feature 17 gate: `claim` — first call per key returns `True` and flips an
in-memory `estado`, later calls return `False`; `record_result` — stores
`status` + `per_slot`).

**`backend/tests/contract/test_rule_repository_contract.py`** — retarget to the
new methods (feature 18's marker assertions carry over unchanged); register the
DynamoDB adapters into every contract suite alongside the fakes.

**`backend/lambda_api/src/planner_api/routing.py`** (reopened 2026-09-06,
feature 17 gate) — `_submit_generation` passes `recipes=deps.recipes` and
`author=auth.user_id` to `submit_generation` (§3c). One-line caller change; the
call site is feature 16's, the signature change is this feature's.

## 3. `RuleRepository` port change + rule-id scheme (GQ3, `R10`–`R17`)

**Port**, `planner_core/ports/rules.py`:

```python
def current_version(self) -> int: ...
def get(self) -> RuleSet: ...
def save_rule(self, rule: CategoryCountRule | PinRule | DisabledDay) -> int: ...
def delete_rule(self, rule_id: str) -> int: ...
```

`save(RuleSet)` is removed (`R12`). `DisabledDay` is a tiny new frozen value
object in `domain/rules.py` (`R14`) — a disabled day is currently just an `int`
in a tuple; a per-rule endpoint needs it as an addressable item. `save_rule` /
`delete_rule` return the advanced `marcaCambio` and bump it in the same write
(feature 18's rule, unchanged).

**Rule ids are deterministic, derived from the rule's natural key** (`R13`) — no
stored id↔key map:

| Rule kind | `ruleId` (`= idRegla`) |
|---|---|
| category count | `cat#<IngredientCategory.value>` |
| pin | `pin#<day>#<slot>` |
| disabled day | `day#<day>` |

The domain already replaces by natural key (`set_pin` drops any existing pin for
`(day, slot)` — `domain/rules.py`), so per-rule last-write-wins falls straight
out: two users editing different rules never collide; two users editing the same
rule are last-write-wins, which is `FR-RT-02` / `G-07`.

**Satisfiability on write** (`R15`–`R17`): `rule_editing` loads `get()`, applies
the change with the existing `domain/rules` mutators (`set_category_count`,
`set_pin`, `disable_day`, …). Those raise `UnsatisfiableRuleSet` /
`InvalidWeekday` from `RuleSet.__post_init__` — so the "load full set, apply in
memory, check" the contract describes is already the domain's behaviour; the
service lets the exception out (`R16`) and never reaches the write (`R17`). Only
after the in-memory `RuleSet` validates does it call `save_rule` for the single
item.

The small TOCTOU window between two concurrent per-rule edits is accepted
(`contract` §7 Q5 consequence i — "acceptable at 2–10 users").

### 3a. Generation discard (`R31`–`R33`, reopened 2026-09-06)

`AP27` (`DELETE /v1/generations/{generationId}`) had no port method — feature
16's implementer flagged it as feature 27's territory (spec-gap 4). The
`{generationId}` path segment **is** the `idPeticionIA` (the contract keys
`AP26`'s `GET` on the same segment), so it maps straight to the port's
idempotency-key argument with no id translation. `discard(idempotency_key: str)
-> None` is a sibling of `stored_generation` / `submit`; it is idempotent —
discarding an absent record is a no-op, matching `HTTP DELETE` semantics and
DynamoDB `DeleteItem`'s natural behaviour. No `application` use case wraps it:
feature 16's handler calls `deps.queue.discard(...)` directly, exactly as the
`AP26` `GET` side already calls `stored_generation` (`routing.py:_get_generation`).
`generation_submission` is not involved.

### 3b. Generation claim / record_result + message enrichment (`R36`–`R40`, reopened 2026-09-06, feature 17 spec gate)

The `ai` worker (feature 17) consumes a `PETICIONIA#<hash>` record that
`submit` created `pending` but nothing can advance. Three additions, all on
`GenerationQueue` because it already owns that item's `submit` / `stored_generation`
/ `discard` lifecycle (same reasoning as §3a):

- `claim(idempotency_key) -> bool` (`R36`): conditional `UpdateItem`,
  `ConditionExpression: estado = :pending`, `SET estado = :running`. `False` on
  `ConditionalCheckFailedException` (`R37`) — a redelivered SQS message finds
  the record already `running`/`completed` and does **not** re-invoke the model.
  The one write-precondition here is on `estado`, never on `marcaCambio`
  (`PETICIONIA#` carries no marker — `contract` §2, §6).
- `record_result(idempotency_key, status, per_slot) -> None` (`R38`):
  unconditional `UpdateItem` `SET estado = :status, resultado = :payload`
  (`R39`); the `claim` already established ownership. `per_slot` is a list of
  `{day, slot, status, message}` dicts — the shape `GET /v1/generations/{id}`
  passes through verbatim (feature 16, done). `status` is `completed` once every
  target slot is terminal, regardless of per-slot failures (partial success is
  per-slot — `FR-AI-09`, feature 17).
- `submit` message enrichment (`R40`): the JSON body
  `SqsGenerationQueue.submit` sends gains `effectiveRules`, `promptVersionId`
  and `authorUserId` (the submitting user — feature 17 attributes the
  open-slot candidates it writes, `FR-CAND-04`). `generation_submission`
  already resolves the rules / version for the `202` `targets` body and now
  takes `author` (§3c), so this is a serialisation change, not new computation.
  It lets feature 17's worker hold no `RuleRepository` / `ConfigPort` and
  generate against exactly the rule set `idPeticionIA` was hashed from —
  closing the window where a shared-rule edit between submit and processing
  would change the run.

`SqsGenerationQueue` and `FakeGenerationQueue` both implement `claim` /
`record_result`; feature 17 adds a second real adapter under `planner_ai/` (it
cannot import `planner_api`), and the `GenerationQueue` contract suite runs over
all three. The whole-week `409` "slot already pending/running" of `contract`
§3.5 is downgraded to exact-hash-resubmit dedupe (owner, 2026-09-06 — recorded
in `specs/ai_lambda/design.md` §9.1); the true per-slot `409` is feature 28.

### 3c. Pinned-slot candidate persistence at submit (`R41`–`R43`, reopened 2026-09-06, feature 17 gate)

`resolve_targets` already partitions a whole-week plan into `open_slots` (the
AI-generated ones), `pinned_slots` (`PinnedTarget(slot, recipe_id)` — a rule
pins a library meal to an unoccupied slot) and `skipped_pins`. The AI worker
(feature 17) processes only `open_slots`. The **pinned-slot candidates are
deterministic — a library-recipe snapshot copy, no model call** (`FR-AI-11`,
`contract` §3.5) — so they are written **synchronously at submit**, not sent
through the queue (owner ruling, 2026-09-06).

`generation_submission.submit_generation` gains two parameters:

```python
def submit_generation(
    request: GenerationRequest,
    first_day: date,
    *,
    weeks: WeekRepository,
    rules: RuleRepository,
    queue: GenerationQueue,
    recipes: RecipeRepository,   # new — the pinned library-recipe read
    author: str,                 # new — the submitting user's id, R42
    config: ConfigPort,          # new — active prompt version, via feature 24's guard (finding 2)
) -> SubmissionOutcome: ...
```

The prompt version is resolved here through
`resolve_active_prompt_version(config)`: an unset or unknown `AI_PROMPT_VERSION_ID`
raises `UnknownPromptVersion` before anything is enqueued (feature 16 maps it to
`422`), instead of `routing.py` reading the raw key and handing `null` to the
worker.

On the **fresh-submit path only** (`stored is None`), **before**
`queue.submit(...)`: for each `plan.targets.pinned_slots` entry — fetch the
library recipe via `recipes`, `snapshot(entry.recipe)`,
`new_candidate(uuid4().hex, snapshot, author)`,
`week_editing.add_slot_candidate(request.week, pinned.slot, candidate,
weeks=weeks)`. This is the same deterministic copy feature 16's
`_resolve_meal_source(source="library")` + `_add_candidate` already perform
(`R41`, `R42`). The idempotent-hit path (`stored is not None`) writes nothing
(`R43`).

"Before `queue.submit`" is deliberate: the pinned candidates must land whether
or not the queue accepts the message, and if `submit`'s `attribute_not_exists`
dedup fires on a concurrent resubmit the pinned writes are harmlessly additive.

**Accepted edge (not designed around, flagged for the implementer/reviewer):** a
partial failure between the pinned-candidate writes and `queue.submit` lets a
resubmit re-resolve and double-write the pinned candidates — additive, rare at
2–10 users, and consistent with the §3b / Q3 concurrent-different-runs ruling.

**Caller adjustment (feature 16, `routing.py:_submit_generation`):** pass
`recipes=deps.recipes`, `author=auth.user_id` and `config=deps.config` — all
already in scope. One-line change; noted here because the call site lives in
feature 16's shell.

## 4. New application use cases — why they belong in `core`, not the handler

`conventions.md`: the handler is thin, "call **one** application use case".
Today only `authentication`, `account_admin`, `live_weeks`, `prompt_version`
exist. The candidate/library/shopping/rule/generation flows have domain models
(features 4–12, done) but no orchestration tying them to ports. Putting that
orchestration in the handler would be business logic in the transport layer.
So each flow gets an `application/` function taking ports + plain values (`R30`),
returning domain objects or raising domain exceptions — feature 16 only
serialises. These functions carry no HTTP knowledge and are unit-tested with
fakes, exactly as feature 15's `authentication` is.

## 5. AP9 stays internal (`R20`, `contract` §7 Q13)

`GET /v1/weeks/{weekId}?include=ingredients` has no route and no query param
(feature 16 `R27`). `WeekRepository.get_week` already returns `SlotContents`
carrying the full ingredient snapshot — that read *is* `AP9`. The
`shopping_editing` re-sync use case calls it directly, in-process, as one step
of the `FR-SHOP-06` composition: acquire the lock (`R23`), read the in-scope
definitive meals, compute the outstanding quantity per normalized name + unit
with feature 8's domain function, write only matching unchecked items, release
the lock. Nothing is removed (`R21`); no checked item is touched (`R22`).

**Not collapsed here.** Re-sync bumps `COMPRA#<idLista>`'s `marcaCambio` once per
differing item today. Collapsing it to one bump per re-sync is explicitly
**feature 26**'s acceptance item 3 (`data_model.md` §4.4 / §5.3); this feature
keeps the per-item bump feature 18 accepted as correct-but-not-optimal.

## 6. Adapter shape (`R1`–`R8`)

- One `_table.py` builds every `(PK, SK)` from `data_model.md` §1/§3 and owns the
  Spanish⇄English attribute map, so no individual adapter repeats it (`R2`,
  `R3`).
- Every mutating method issues a `TransactWriteItems` whose second leg is
  `ADD marcaCambio 1` on that partition's `MARCA` item, and returns the resulting
  value (`R6`) — the same shape `AP4` already uses for the username reservation
  (`data_model.md` §5.1/§5.2). No `ConditionExpression` ever names `marcaCambio`
  (`R7`); the existing feature-18 scan test extends to the adapters. Its R12
  guard (`test_change_marker_is_not_a_write_condition.py`,
  `test_the_change_marker_stays_inside_its_permitted_modules`) is also relaxed:
  the permitted set adds the four `application/*_editing.py` read-service modules,
  which must call `current_version()` in the use case to satisfy `R34`/`R35`.
  The R7 write-precondition scans (`_expected_version_offenders`, the adapter
  `ConditionExpression` scan, their self-checks) are untouched — the relaxation
  is narrow and read-only. Owner-approved 2026-09-06 (reviewer finding F4).
- `current_version` is a `GetItem` with `ConsistentRead=True` and
  `ProjectionExpression=marcaCambio`, returning `0` before any write (`R8`).
- `ShoppingListRepository.acquire_lock` compares `ttl` itself rather than relying
  on DynamoDB TTL deletion, which is not prompt (`data_model.md` §5.3).
- `delete_checked_items` with nothing checked stays a no-op and does **not** bump
  (feature 18's contract assertion carries over to the real adapter, `R4`).
- `SqsGenerationQueue.discard` (`R32`, `R33`) issues an **unconditional**
  `DeleteItem` on `PETICIONIA#<hash> / METADATA` — no `ConditionExpression`
  (`attribute_exists`), so an absent key succeeds silently. `FakeGenerationQueue`
  drops the key from its dict and treats a missing key as a no-op.
- `SqsGenerationQueue.claim` (`R37`) is a conditional `UpdateItem` on
  `PETICIONIA#<hash> / METADATA`, `ConditionExpression: estado = :pending`,
  `False` on `ConditionalCheckFailedException`. `record_result` (`R39`) is an
  unconditional `UpdateItem` setting `estado` + `resultado`. `submit` (`R40`)
  adds `effectiveRules` / `promptVersionId` to the JSON message body. See §3b.

## 7. Items raised at the spec gate

### 7.1 The `NFR-BKP-01` anchor — accepted as written (owner, 2026-08-31)

`docs/requirements.md` has no frozen id for "the adapter maps storage names to
domain names"; that rule lives in `docs/data_model.md` §1 and
`docs/conventions.md`. Rather than invent one, `R1`–`R5` and `R29`/`R30` cite
`NFR-BKP-01` — the one frozen id that enumerates the persistent datastores, and
the id feature 14 already used for the ports. The owner may prefer a different
anchor (e.g. adding `FR-ARCH-01` for the week adapter) or a narrower `covers`;
either way the `R<n>` are rescoped, not deleted.

### 7.2 `ArchiveRepository` — decided: **archive is parked for the MVP**

Owner ruling, 2026-08-31. This feature builds **no** DynamoDB
`ArchiveRepository` adapter: `docs/data_model.md` §9 parks the `FR-ARCH-02`
shopping-list snapshot with **no item type**, and archiving a week is otherwise
a no-op (past weeks already sit under older keys). Its absence from §2's file
list is deliberate, not an omission.

The port call `domain.rollover.roll_over` makes is satisfied in the MVP by a
no-op `ArchiveRepository` that feature 16's `wiring.py` injects — it retains
nothing and logs the discarded `ArchivedWeek` through the standard-library
`logging` module (`specs/rest_api_lambda/` `R40`/`R41`, `NFR-OBS-01`).

The real adapter and the `FR-ARCH-02` shopping-list-snapshot item type are
**post-MVP**; unparking them is the explicit owner decision `docs/data_model.md`
§9 describes, and would arrive as its own feature.

## 8. Rejected alternatives

*Three from the original design (the `RuleRepository` change); one from the
first 2026-09-06 reopening (the read-marker plumbing); one from the feature-17
gate reopening (the generation write-back).*

**Keep `save(RuleSet)`; the api adapter does load-modify-write-whole-set.**
Matches today's port with no `core` change. Rejected: `contract` §7 Q5 already
ruled per-rule endpoints, and a whole-set write makes `FR-RT-02` last-write-wins
apply to the *entire* set — one user's pin edit silently discards another's
concurrent category-count edit. Per-rule single-item writes are the whole point.

**Random ULID rule ids with a stored `idRegla → naturalKey` map.** Lets the wire
id be fully opaque. Rejected: it adds a persistence concern (the map is another
item to write transactionally and keep consistent) and a rebuild hazard, to buy
nothing the deterministic natural-key id (§3) does not already give — the id is
server-minted and stable either way, and the natural-key form matches how the
domain already de-duplicates rules.

**Put the orchestration in `planner_api` (adapters + use cases together in the
Lambda package).** Would make this feature a single package and remove the
`core` churn entirely. Rejected: `architecture.md` §3.1 rule 2 puts use cases in
`application/`, and orchestration in the Lambda package would be untestable
without the transport and unreachable from `lambda_ai`, which needs the same
week-writing path (`FR-AI-09` constraint, feature 17 acceptance item 5).

**Keep feature 16's `adapters/markers.py` forwarding shim; leave the read use
cases marker-free.** Smaller diff — no read-DTO change, no feature-16 caller
churn. Rejected: the shim puts a marker-read concern in the Lambda package that
the feature-18 guard (`test_change_marker_is_not_a_write_condition.py`) tolerates
only by a directory accident, and the `contract` §6 "read the marker first"
ordering has to live wherever the two reads are composed — which is the use
case, not the transport. Returning the marker from the read service is where it
belongs. Accepted cost (owner-approved 2026-09-06, reviewer finding F4): the
feature-18 R12 guard's permitted set gains the four `application/*_editing.py`
read modules; the R7 write-precondition scans stay as-is. (The parallel choice
for the discard — handler calls the port directly,
no `generation_discard` use case — is covered in §3a: the `AP26` `GET` side
already does exactly that, and there is no orchestration to wrap.)

**A separate write-only `GenerationResultStore` port for `claim` /
`record_result` instead of extending `GenerationQueue`.** Keeps the port
untouched and its "queue" name honest. Rejected: two ports would then write the
single `PETICIONIA#` item whose creation (`submit`), read (`stored_generation`)
and delete (`discard`) `GenerationQueue` already owns — splitting one item's
lifecycle across modules for a naming quibble. The `claim`/`record_result` pair
is the same call the `discard` reopening already made.

## 9. Test strategy (feeds `tasks.md`)

- **Contract suites**: every existing suite in `backend/tests/contract/` is
  parametrized over fake **and** `moto`-backed adapter; both pass unchanged
  (`R1`, `R4`). `moto` runs in the default gate; anything needing real creds is
  `@pytest.mark.aws`.
- **Attribute mapping**: round-trip a domain object through the adapter and
  assert the raw item's keys are exactly `data_model.md` §1's Spanish names; a
  scan test asserts no Spanish attribute name appears in a returned value
  (`R2`, `R3`).
- **Layer scan**: extend the existing storage-agnostic scan — `planner_core`
  imports no `boto3`/`planner_api` (`R5`); no use-case signature holds an HTTP
  or AWS type (`R30`).
- **Markers**: every mutating adapter method changes the version and returns
  what the next `current_version()` reports; a scan asserts no
  `ConditionExpression` names `marcaCambio` (`R6`–`R8`); each use case returns
  the write's marker (`R9`).
- **Rules**: `save_rule`/`delete_rule` contract tests; `save` is gone; ids derive
  from natural keys; unsatisfiable change raises and the fake records **zero**
  writes (`R10`–`R17`).
- **Library cascade**: unconfirmed delete of a pinned recipe reports the pins and
  deletes nothing; confirmed delete removes recipe + pins (`R18`, `R19`).
- **Re-sync**: fake week + list; asserts additive-only, checked untouched, item
  count never decreases, lock acquired before the week read, second holder
  raises `ShoppingListLockHeld` (`R20`–`R24`).
- **Generation**: `generation_submission` derives the same `idPeticionIA` twice
  for the same input; stored-result hit calls `FakeGenerationQueue` zero times;
  fresh request calls it once (`R25`–`R28`).
- **Generation discard** (`R31`–`R33`): contract-suite case parametrized over
  fake + `moto` adapter — `submit` then discard then `stored_generation` returns
  `None`; discard of a never-submitted key does not raise; a scan confirms the
  adapter's discard carries no `ConditionExpression`.
- **Generation claim / record_result** (`R36`–`R39`): contract-suite cases,
  fake + `moto` — first `claim` after `submit` returns `True`, a second returns
  `False` (and `claim` of an absent key returns `False`); `record_result` writes
  `estado` + `resultado` and a following `stored_generation` reports them; a
  scan confirms `record_result` carries no `ConditionExpression` and `claim`'s
  only condition is on `estado`, never `marcaCambio`.
- **Message enrichment** (`R40`): `generation_submission` on a fresh request →
  the payload handed to `FakeGenerationQueue.submit` carries `effectiveRules`
  matching `build_plan`'s `effective_rules` and the configured `promptVersionId`.
- **Pinned-slot persistence** (`R41`–`R43`): fake week + `FakeRecipeRepository`
  seeded with a pinned recipe + a rule pinning it to an unoccupied slot → a
  fresh `submit_generation` leaves a candidate in that slot, authored by the
  passed `author`, snapshot-decoupled from the library entry; an idempotent hit
  (`FakeGenerationQueue` pre-seeded with the stored result) makes **zero**
  `save_slot` calls.
- **Read markers** (`R34`, `R35`): each read service returns `marker` equal to
  the port's `current_version()`; a spy fake asserts `current_version` is
  invoked before the payload read; each new frozen result object has its own
  frozen-instance test (`docs/conventions.md`).
