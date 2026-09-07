# ai_lambda — Design

> Feature 17 · tier 3 · `planner_ai` **worker shell**: the SQS consumer entry
> point, the Bedrock provider adapter, the cost-cap kill-switch, per-slot
> concurrency, idempotent invocation, and the whole-week write-back through
> `WeekRepository`. Read `requirements.md` first.
> Structural template: `specs/rest_api_lambda/` (shell vs. core split) and
> `specs/rest_api_persistence_and_services/` (the `GenerationQueue` port + SQS
> adapter). Sources: `docs/architecture.md` §1.2 / §1.2.6 / §3–§3.2 / §4;
> `docs/data_model.md` §4.6 / §4.7; `docs/rest_api_contract.md` §3.5 / §7 Q3;
> `docs/gaps_and_resolutions.md` G-70 / G-81 / G-88.

## 0. Governing decisions already made elsewhere — not re-opened

- Provider is **AWS Bedrock + Anthropic Claude** (`architecture.md` §1.2.6,
  formerly P4). The Bedrock SDK path is `planner_ai`'s dependency closure only,
  never `planner_api`'s (`architecture.md` §1.2 rule).
- `api`→`ai` is the **one signed-off SQS queue** (`architecture.md` §1.2 /
  §1.2.5). No second queue, no third Lambda (`architecture.md` §6).
- The **generation domain logic exists** and is not rewritten here:
  `domain/generation.py` (`build_plan`, `resolve_targets`, `idempotency_key`),
  `domain/ai_prompt.py` (`build_category_prompt`, `build_instructions`),
  `domain/ai_output.py` (`validate_and_preview`, `SlotGenerationResult`,
  `build_generation_failure`), `application/generation_submission.py`.
- The **idempotency key** (`idPeticionIA`) is derived on the `api` side at
  submit (`generation_submission.submit_generation`, feature 27) and is opaque
  to this worker (`data_model.md` §2, `contract` §7 Q3). This feature does not
  compute it and does not compute the single-recipe `attempt` ordinal — that is
  **feature 28 `single_recipe_generation`** (owner, 2026-09-06).
- `G-88` constraint: whole-week candidates are written **through
  `WeekRepository`** so the `marcaCambio` bump rides inside `save_slot`'s
  transaction (`data_model.md` §4.7). Never a separate write path.
- No `docs/architecture.md` §2 item is open. The cost-cap **mechanism** §1.2.6
  defers to this spec gate was **ruled by the owner 2026-09-06**: a
  `GenerationGate` port read against an SSM parameter (§5). All eight spec-gate
  questions were ruled the same day — §5–§8 and §10 carry the outcomes.
- `Clock` is a port; domain takes a `date`, never a `Clock` (tier-1 ruling).
  `wiring.py` reads the clock and passes the civil date to `build_plan`.

## 1. Layering (`docs/architecture.md` §3, §3.1)

| Piece | Layer | Notes |
|---|---|---|
| `planner_ai/handler.py` | `planner_ai/` (AWS entry point) | Thin: parse the SQS `Records` event → call one use case per record → return. No business logic. |
| `planner_ai/wiring.py` | `planner_ai/` | Composition root; selects adapters by environment; the only module naming a concrete adapter; reads the clock. |
| `planner_ai/adapters/bedrock.py` | `planner_ai/adapters/` | `AiProvider` implementation. Owns the Bedrock SDK call and `BEDROCK_MODEL_ID`. |
| `planner_ai/adapters/ssm.py` | `planner_ai/adapters/` | `GenerationGate` implementation — reads the kill-switch parameter. |
| `planner_ai/adapters/dynamo/` | `planner_ai/adapters/` | `WeekRepository` + the `PETICIONIA#` claim/record adapter. Spanish attribute names ⇄ English domain here (`data_model.md` §1). |
| `application/week_generation.py` | `planner_core/application/` | New use case: orchestrates `domain/ai_prompt`, `domain/ai_output`, `domain/generation` through the `AiProvider`, `WeekRepository`, `GenerationGate` and `GenerationQueue` ports. Takes ports + plain values only. |
| `ports/ai_provider.py` | `planner_core/ports/` | New `Protocol`. No SDK in the signature. |
| `ports/generation_gate.py` | `planner_core/ports/` | New `Protocol`. `is_generation_enabled() -> bool`. |
| `ports/generation_queue.py` | `planner_core/ports/` | **Feature 27 reopen** (§6): `claim` and `record_result` land there — `specs/rest_api_persistence_and_services/` R36–R39. This feature builds the `planner_ai` adapter side and consumes the ported signature. |

`planner_ai` gains **`boto3`** as its first runtime dependency (Bedrock-runtime,
DynamoDB and SSM are all boto3 clients — no separate package; `anthropic[bedrock]`
rejected in §11). `moto` as a dev dependency for adapter contract tests. Both
justified here per `architecture.md` §1.3 — this is the `ai` adapter closure.
`planner_core` stays stdlib-only.

## 2. Files created / modified

**`backend/core/src/planner_core/`**
- `ports/ai_provider.py` — new.
- `ports/generation_gate.py` — new.
- `ports/generation_queue.py` — `claim(idempotency_key) -> bool` and
  `record_result(idempotency_key, status, per_slot) -> None` are added by the
  **feature 27 reopen** (`specs/rest_api_persistence_and_services/` R36–R39,
  2026-09-06). This feature consumes them; it does not edit the port.
- `application/week_generation.py` — new use case (§3).

**`backend/core/tests/support/fakes.py`** — `FakeAiProvider`,
`FakeGenerationGate`; extend `FakeGenerationQueue` with `claim` / `record_result`.

**`backend/lambda_ai/`** (all new except `pyproject.toml`)
- `pyproject.toml` — add `boto3` runtime dep, `moto` dev dep.
- `src/planner_ai/handler.py`, `src/planner_ai/wiring.py`.
- `src/planner_ai/adapters/__init__.py`, `adapters/bedrock.py`, `adapters/ssm.py`.
- `src/planner_ai/adapters/dynamo/__init__.py`, `dynamo/_table.py`,
  `dynamo/_meal.py`, `dynamo/weeks.py`, `dynamo/generations.py`.
- `tests/` — use-case unit tests, adapter tests, scan tests.

**`backend/tests/contract/`** — parametrize the existing `WeekRepository`
contract suite over the `planner_ai` DynamoDB adapter; new contract suites for
`AiProvider`, `GenerationGate`, and the `GenerationQueue` `claim`/`record_result`
methods (fake + `moto`).

Nothing under `backend/frontend/` is touched.

## 3. The orchestration use case

`application/week_generation.py`:

```python
def run_week_generation(
    idempotency_key: str,
    request: GenerationRequest,
    effective_rules: RuleSet,
    prompt_version_id: str,
    author: str,
    first_day: date,
    *,
    provider: AiProvider,
    weeks: WeekRepository,
    queue: GenerationQueue,
    gate: GenerationGate,
) -> WeekGenerationOutcome: ...
```

- `effective_rules`, `prompt_version_id` and `author` (the submitting user)
  arrive **enriched on the SQS message** (§8) — the worker does not read
  `RuleRepository` or `ConfigPort`.
- Step 1 — `queue.claim(idempotency_key)`. `False` → return early, no provider
  call (R11–R13).
- Step 2 — read current occupancy: `weeks.get_week(request.week)`; re-run
  `resolve_targets(request.week, effective_rules, first_day, occupancy)` so a
  definitive promoted since submit is honoured (R8, R10).
- Step 3 — per open slot, independently (R2–R5): build the prompt
  (`build_category_prompt(targets.remaining_category_counts, prompt_version_id)`),
  check `gate.is_generation_enabled()` (R16, R17), call `provider.generate(...)`,
  `validate_and_preview(...)`, on `GenerationSuccess` re-read the slot, skip if
  now definitive (R10), else `week_editing.add_slot_candidate(...)` (R6, R8, R21)
  with `author` as the candidate's author. Each slot's exception is caught and
  turned into a `SlotGenerationResult` (R4); a raised gate-off produces an
  `AI_GENERATION_UNAVAILABLE` result (R18).
- Step 4 — `queue.record_result(idempotency_key, terminal_status, per_slot)`
  after all writes (R14, R15). `terminal_status` is `completed` (all slots
  terminal) regardless of per-slot failures — partial success is per-slot
  (`FR-AI-09`).

`WeekGenerationOutcome` is a new `@dataclass(frozen=True)` (gets its own
frozen-instance test, `conventions.md`).

This worker acts only on `targets.open_slots` — the AI-generated ones — **by
design**. The pinned-slot candidates (`targets.pinned_slots`) are a
deterministic library-snapshot copy with no model call, so feature 27's
`generation_submission` writes them **synchronously at submit**, not through the
queue (owner, 2026-09-06; `specs/rest_api_persistence_and_services/` R41–R43,
design §3c). `targets.skipped_pins` is already reported in the submit `202`
body.

## 4. `AiProvider` port + Bedrock adapter

`ports/ai_provider.py` — one method, prompt value object in, parsed
provider-agnostic `RawRecipeOutput` out (the shape `domain/ai_output` already
consumes):

```python
class AiProvider(Protocol):
    def generate(self, prompt: CategoryPrompt | SpecificationPrompt | ReferencePrompt) -> RawRecipeOutput: ...
```

`BedrockAiProvider` (`planner_ai/adapters/bedrock.py`) renders the prompt value
object to the Anthropic messages JSON, calls `bedrock-runtime:InvokeModel`,
parses the JSON block the model returns into `RawRecipeOutput`. A parse failure
raises a named adapter exception the use case catches as a per-slot failure
(`GenerationFailureReason.INVALID_OUTPUT`, R4).

`BEDROCK_MODEL_ID` — a module constant, `"anthropic.claude-sonnet-5"`
(`architecture.md` §1.2.6, Bedrock's `anthropic.` prefix), overridable by the
`AI_MODEL_ID` env var so the Haiku evaluation §1.2.6 anticipates needs no code
change. See §10.

## 5. Cost-cap kill-switch (`NFR-AI-01`, resolves `G-81` — owner ruled 2026-09-06)

`ports/generation_gate.py`:

```python
class GenerationGate(Protocol):
    def is_generation_enabled(self) -> bool: ...
```

- `is_generation_enabled()` takes **no user argument** (R19, R20) — one global
  boolean for the deployment.
- `SsmGenerationGate` (`planner_ai/adapters/ssm.py`) reads the **SSM Parameter
  Store** `String` parameter `/planner/<env>/ai-generation-enabled` (§10), with
  a ~5 s in-process TTL cache so a hot Lambda does not call SSM per slot.
- On the disabled state the use case invokes no provider (R17) and records
  `GenerationFailureReason.GENERATION_UNAVAILABLE` + the `AI_GENERATION_UNAVAILABLE`
  es-ES message per unprocessed slot (R18) — the friendly message `NFR-AI-01`
  requires, already in `planner_core.messages` and already wired in
  `domain/ai_output.py` (feature 12 `R17`). No new message constant.

**What is feature 21 (IaC), not here:** the AWS Budget + its alarm, the Budget
**action** and the SNS→Lambda flipper that sets the SSM parameter to disabled,
plus the belt-and-suspenders `reserved_concurrent_executions = 0` /
event-source-mapping disable on the `ai` function. The application layer owns
only the *read* and the *behaviour when disabled*; the enforcing trigger is
infra. This split is stated so the reviewer does not expect a Budget resource in
this feature.

## 6. Idempotent invocation + result recording (feature 27 reopen)

The `PETICIONIA#<hash>/METADATA` item (`data_model.md` §4.6) is created
`pending` by `SqsGenerationQueue.submit` (feature 27) and read by
`stored_generation`. It has no write-back method today. The **feature 27 reopen**
(`specs/rest_api_persistence_and_services/` R36–R39, 2026-09-06 — the same path
the `discard` reopen took, `specs/rest_api_lambda/design.md` §2) adds two:

- `claim(idempotency_key) -> bool` — a conditional update `estado pending →
  running`. `False` when another delivery already owns it or it is terminal
  (this feature's R11–R13). The idempotent-consumer guard that stops a
  double-delivered SQS message paying the model twice.
- `record_result(idempotency_key, status, per_slot) -> None` — writes
  `estado = status` and `resultado = <per-slot payload>` (this feature's
  R14, R15). Unconditional; the claim already established ownership.

`resultado` payload shape (a `contract` §2 "feature 17 spec input", ruled
2026-09-06): a JSON array of `{ "day": int, "slot": int, "status": "completed" |
"failed", "message": str | null }`, surfaced verbatim by `GET
/v1/generations/{id}` (`AP26`, feature 16 `_get_generation`, done). Per-slot
retry (`FR-AI-12`) is the client re-submitting — feature 28 / frontend.

Both adapters implement the two methods: `SqsGenerationQueue` (feature 27, for
the `api` contract suite) and this feature's `planner_ai/adapters/dynamo/generations.py`.
The shared `GenerationQueue` contract suite keeps them honest.

## 7. `WeekRepository` in `planner_ai`

`G-88` forces the write through `WeekRepository`, whose only real adapter is
DynamoDB and lives in `planner_api/adapters/dynamo/` — unreachable from
`planner_ai` (`architecture.md` §6: no cross-Lambda import). So `planner_ai`
gets its **own** copy of `weeks.py` + `_table.py` + `_meal.py` (whatever the
`WeekRepository` adapter actually needs). Owner ruled 2026-09-06: the copy — no
`architecture.md` edit, no shared workspace member. **Mandatory:**
`backend/tests/contract/test_week_repository_contract.py` is parametrized over
**both** the `planner_api` and `planner_ai` adapters, so drift between the two
copies is a test failure.

## 8. SQS message enrichment (feature 27 reopen)

`SqsGenerationQueue.submit` sends `{idPeticionIA, weekId, mode, ruleOverride}`
today. Owner ruled 2026-09-06: the message body gains the already-resolved
**effective rules**, the **active prompt version id** and the **submitting
user's id** (`authorUserId` — the worker attributes the open-slot candidates it
writes, R21). The `api` already computes `effective_rules` / `GenerationTargets`
for the `202` body, so this is free at submit. The worker then reads its
generation inputs from the message: no `RuleRepository` copy in `planner_ai`, no
`ConfigPort`, and it generates against exactly what the user confirmed at submit
(`FR-AI-05`), closing the mid-generation shared-rules TOCTOU. The message-body
contract change is `specs/rest_api_persistence_and_services/` R40 (feature 27
reopen).

## 9. What is NOT here

- Feature 21: the Budget, Budget action, SNS→flipper, ESM, reserved concurrency,
  the queue + DLQ, SSM parameter provisioning, DynamoDB table/TTL, all IAM.
- Feature 27 (reopen): the `GenerationQueue` `claim` / `record_result` port
  additions (R36–R39); the `submit` message-body enrichment (R40); the
  synchronous pinned-slot candidate writes at submit (R41–R43); the
  `SqsGenerationQueue` adapter side.
- Feature 28 `single_recipe_generation`: the single-recipe submit/enqueue path,
  the server-authoritative `attempt` ordinal, the true per-slot `409`, per-slot
  retry UX, and the `contract` single-recipe body shape.
- Feature 12: single-recipe preview lifecycle domain (done — reused via
  `domain/ai_output`).
- Feature 10: target resolution semantics (`FR-AI-11`, `G-71`) — reused via
  `resolve_targets`, not re-specified.

### 9.1 Deliberate deviation from `docs/rest_api_contract.md` §3.5 / L171 (owner, 2026-09-06)

The whole-week `POST /v1/generations` `409` "slot already has a
pending/running generation" is **downgraded to exact-hash-resubmit dedupe
only** — delivered by feature 27's `attribute_not_exists(PK)` conditional write
on `PETICIONIA#<hash>` (a genuine identical double-submit returns the stored
record, never a second Bedrock call). Concurrent *different* whole-week runs for
one week are allowed and safe: `FR-AI-11` additive writes plus this feature's
at-write definitive re-check (R8, R10) mean neither run corrupts the other. The
true per-slot `409` (one slot busy) — and any per-slot in-progress marker item
type it needs — is **feature 28**; no `data_model.md` change here. The owner
reconciles `rest_api_contract.md` §3.5 / L171.

## 10. Values fixed at the spec gate (owner, 2026-09-06)

| Item | Value | Rationale |
|---|---|---|
| Bedrock model id | `anthropic.claude-sonnet-5`, `AI_MODEL_ID` env override | `architecture.md` §1.2.6 Sonnet-to-start; env override so the Haiku evaluation needs no code change |
| Kill-switch store | SSM Parameter Store, `String` | `NFR-SEC-02` already names SSM; live-mutable by a feature-21 Lambda without a redeploy (env vars are not); one datastore concern kept out of the `data` table |
| Kill-switch parameter name | `/planner/<env>/ai-generation-enabled` (`"true"` / `"false"`) | matches the `Project`/`Environment` tagging convention (`NFR-FIN-01`) |
| Kill-switch cache TTL | ~5 s in-process | bounds SSM calls on a hot Lambda without making "disabled" take minutes to take effect |
| `resultado` per-slot payload | `[{day, slot, status, message}]` JSON | smallest shape `GET /v1/generations/{id}` needs for per-slot display (`FR-AI-12`) |

## 11. Rejected alternatives

**Cost cap as reserved-concurrency-0 / event-source-mapping disable only (no
application code).** Cleanest kill — the worker never runs. Rejected as the
*primary* path: both are feature-21 IaC the implementer cannot build, and a
worker that is simply switched off leaves every in-flight request stuck at
`pending` with no way to emit `NFR-AI-01`'s required es-ES "unavailable"
message. The flag-read path produces that message; the IaC controls stay as a
belt-and-suspenders second layer in feature 21.

**Worker re-reads `RuleRepository` + `ConfigPort` instead of enriching the
message.** No feature-27 message change. Rejected: it forces a second DynamoDB
adapter copy (rules) into `planner_ai`, and re-resolving the rules minutes after
submit can yield a different effective set than the one the user confirmed in
the `FR-AI-05` prompt — the run would silently not match its own confirmation.

**A new write-only `GenerationResultStore` port instead of extending
`GenerationQueue`.** Keeps feature 27 untouched. Rejected: two ports would then
write the single `PETICIONIA#` item, splitting its lifecycle across modules.
`GenerationQueue` already owns that item's creation (`submit`) and read
(`stored_generation`); `claim` / `record_result` belong beside them — the same
call the `discard` reopening already made.

## 12. Test strategy (feeds `tasks.md`)

- **Use case, per-slot independence**: `FakeAiProvider` raising on slot 2 of 3 →
  slots 1 and 3 persisted, `record_result` shows slot 2 `failed` (R2–R5).
- **Write path**: assert every candidate lands via `FakeWeekRepository.save_slot`
  (one call per successful slot); a scan test asserts `planner_ai` has no
  DynamoDB `put_item`/`update_item` on `SEMANA#` outside the `WeekRepository`
  adapter (R3, R6, R7).
- **Additive**: pre-populate a slot with a candidate + a definitive, generate,
  assert both survive and the definitive slot is skipped (R8, R9, R10) — the
  `architecture.md` §4 invariant-4 check.
- **Idempotent invocation**: `FakeGenerationQueue.claim` returns `False` →
  `FakeAiProvider` called zero times; redeliver a `completed` record → zero
  calls; `record_result` asserted to run after the last `save_slot` via an
  ordered spy (R11–R15).
- **Cost cap**: `FakeGenerationGate` disabled → zero provider calls, every slot
  result carries `AI_GENERATION_UNAVAILABLE` (R16–R18). A scan test asserts no
  per-user counter attribute or read anywhere in `planner_ai` /
  `application/week_generation.py`, mirroring `test_no_ambient_time.py`'s
  technique (R19, R20).
- **Bedrock adapter**: a recorded Anthropic-messages response fixture →
  `RawRecipeOutput`; a malformed block → the named adapter exception. No live
  call in the default gate; any real call is `@pytest.mark.aws`.
- **Contract suites**: `WeekRepository` suite green against the `planner_ai`
  adapter (`moto`); `AiProvider`, `GenerationGate`, `claim`/`record_result`
  suites green against fake + real.
- **Handler**: an SQS `Records` event with two records → two use-case
  invocations; a use-case raise on one record does not stop the other (R1, R4).
- **Layer scan**: `planner_core` imports no `boto3` and no Bedrock module
  (existing guard extended).
