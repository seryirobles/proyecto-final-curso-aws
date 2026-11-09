# Issue 25 — analysis

## Defect, one sentence

When a generation fails with anything but a provider error, the worker catches the exception and returns `None`, AWS reads that as success and deletes the message, and the run stays `pending` or `running` with no message, no retry option and no alarm; a redelivery could not rescue it anyway, because the claim turns every later delivery into a no-op that is acknowledged too.

**Classification: `defect`.** Severity: **agree with medium**, see *Severity*.

## Is it a defect? The catch is deliberate; the deletion is not

The comment at `handler.py:120` cites the wrong requirement. `R4` is about slots, not records:

> **`specs/ai_lambda/requirements.md` R4:** "IF processing one target slot fails, THEN the system SHALL continue processing the remaining target slots."

Record isolation does exist, but it asks only that the other records are processed:

> **`specs/single_recipe_generation/requirements.md` R27:** "WHEN one record in an SQS batch fails, the system SHALL still process the batch's other records."
> **`specs/ai_lambda/design.md` §12:** "a use-case raise on one record does not stop the other (R1, R4)."

No spec says a failed message is acknowledged. `specs/ai_lambda/design.md` §9 hands "the queue + DLQ" to feature 21 and says nothing about what the handler returns. The only statement of the deletion is a comment, `local_worker.py:135-137`: "a batch always completes without raising, so a real SQS trigger would delete the whole batch too". Partial batch responses satisfy R27 without deleting anything.

What the swallow violates:

> **`FR-AI-12`:** "Failures shall be surfaced **per slot** with a retry option and a friendly message in Castilian Spanish; partial results are kept"
> **`specs/week_generation_backend/requirements.md` R20:** "IF a slot fails, THEN the system SHALL record that slot as `error` with a `code` (a `GenerationFailureReason` value) and an es-ES `message`."
> **`specs/single_recipe_generation/requirements.md` R26:** "IF the provider raises or the output fails validation, THEN the system SHALL record status `failed`" (the provider half holds; a failure after the provider call does not reach it)
> **`docs/architecture.md` §4 invariant 5:** "AI generation (`FR-AI-08`) [...] must converge to one result under retry, double-click or partial failure."

`G-xx`: none makes this deliberate. `G-19` is the opposite: "Per-slot retry is the natural complement of per-slot independence: pay only for the failed slot, not the whole week again". `docs/requirements.md`, `docs/gaps_and_resolutions.md`, `docs/architecture.md`, `docs/data_model.md` and `docs/rest_api_contract.md` never mention a DLQ, a redrive policy or partial batch responses.

## AWS behaviour (official docs, fetched 2026-11-08, not asserted from memory)

[Handling errors for an SQS event source](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html), § *Success and failure conditions*:

> "Lambda treats a batch as a complete success if your function returns any of the following: An empty batchItemFailures list / A null batchItemFailures list / An empty EventResponse / A null EventResponse"

A Python `None` serialises to a null response, so the report's "if" holds. Same page:

> "If your function throws an exception, the entire batch is considered a complete failure."

[Lambda function metrics](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-metrics-types.html), so a function that returns normally adds nothing to `Errors`, with or without `batchItemFailures`:

> "Errors – The number of invocations that result in a function error. Function errors include exceptions that your code throws and exceptions that the Lambda runtime throws. The runtime returns errors for issues such as timeouts and configuration errors."

## Reproduction

**Not observed on AWS; no AWS call was made.** The AWS half (null means delete) rests on the quotes above. The record half is reproduced on a scratchpad copy of `HEAD`, with fakes and moto. Live tree untouched.

    cp -r issues/ai-failed-messages-never-retried/tests/backend/. <scratch copy>/backend/
    cd <scratch copy>/backend && pytest lambda_ai/tests/test_worker_failure_recovery.py lambda_ai/tests/test_local_worker_partial_batch.py tests/contract/test_generation_failure_recovery.py

| Scenario | Observed today | Expected |
|---|---|---|
| Save fails on slot 2 of 14 | Status `running`; 13 slots in flight (`(1,2)` `running`, 12 `pending`); handler returns `None` | Terminal, every slot `done` or `error` |
| `claim` throttled | Returns `None`, so deleted; record `pending` forever | `{"batchItemFailures": [{"itemIdentifier": "m-1"}]}` |
| Redelivery with `ApproximateReceiveCount` 2 behind a dead attempt's claim | `claim` returns `False`, no-op, acknowledged; `(1,2)` and `(2,1)` in flight for good | Terminal |

## Root cause

Three links. Fixing only the first does not fix the report.

1. **`backend/lambda_ai/src/planner_ai/handler.py:117-121`, `:124-127`** catches every `Exception` and returns `None`, despite `function_response_types = ["ReportBatchItemFailures"]` at `terraform/lambda.tf:74`. Nothing retries; nothing reaches the DLQ. The symptom surfaces here.
2. **`backend/core/src/planner_core/application/week_generation.py:206`, `:248`; `single_recipe_generation.py:67`** read a `False` claim as "another delivery owns this". `claim` is a one-way latch (`backend/lambda_ai/src/planner_ai/adapters/dynamo/generations.py:86-101`, conditional on `estado = pending`), so a dead attempt's own redelivery cannot be told from a live duplicate and is acknowledged. **This also defeats retries that happen today:** a Lambda timeout or crash does redeliver, then the second delivery no-ops and deletes the message. So `terraform/monitoring.tf:11` ("A message reaching the DLQ means a generation run crashed or timed out 5 times") is false today: anything past the claim gets one redelivery and is gone.
3. **`week_generation.py:122`, `single_recipe_generation.py:84`** catch only `AiProviderError`. Everything else (`save_slot`, `get_week`, `record_slot`, `record_result`) propagates, so no code path turns such a failure into a terminal record. A realistic trigger is `save_slot`'s `TransactWriteItems` (`adapters/dynamo/_table.py`, `transact_write`) with its marker bump; contention with a concurrent week edit is plausible but not demonstrated.

Requirement violated: `FR-AI-12` (with `R20`, `R26`), `docs/architecture.md` §4 invariant 5.

## Settled questions

### 1. What the user sees today

The SPA polls every 2 s with no cap and stops only on a terminal status (`useWeekGeneration.js:141-175`, `useAiGeneration.js:47-65`).

| `_process_record` raises at | Record | Screen | Way out for that request |
|---|---|---|---|
| Parse (poison) or `claim` | `pending`, `slots: []` | Week panel: every slot "Generando…", "0 de N huecos listos". Recipe form: loading state | None |
| After `claim`, before `begin_slots` | `running`, `slots: []` | Same | None |
| Mid-run | `running`; earlier slots `done` with candidates kept, one slot `running`, the rest `pending` | "k de N", the rest "Generando…" | None: the retry button renders only on `error` rows and the API answers `409 SLOT_NOT_RETRYABLE` otherwise |
| Single-recipe, after `claim` | `running` | Loading state, no discard (the preview holds it) | None |

**For how long:** until the record's `ttl`, 7 days after submit (`backend/lambda_api/src/planner_api/adapters/sqs.py:37`, `:201`), plus TTL deletion lag "up to 48 hours" (`docs/data_model.md` §5.3); then `GET` returns 404. **Re-submitting does not help:** an identical `POST` returns the stuck record (`generation_submission.py:51-59`; contract §3.6 for recipes). A whole-week run only escapes with a request that hashes differently (another mode, an override, or a change in target slots, `domain/generation.py:178`). Closing the panel clears the browser's copy and leaves the record. A single-recipe result already paid for is lost.

### 2. What retries and what must not

Under the owner's policy (§ *Owner rulings*), **only the first delivery may call the provider; no failure is ever rerun.**

| Failure | Example | Treatment |
|---|---|---|
| Before the claim applied | `claim` throttled | **Reported.** Nothing spent or recorded; the next delivery (90 min) only settles it `failed` |
| Claimed, no slot recorded | `get_week` or `begin_slots` fails | **Settled on the spot.** Every open target written as `error`, run `failed` (E6) |
| Behind the claim, slots recorded | `save_slot`, `record_slot` | **Settled on the spot.** Unfinished slots `error`, finished kept; the user retries per slot (`FR-AI-12`, `G-19`) |
| Out of time | 3 slots left, 100 s left | **Settled on the spot.** Slots not started become `error` (E16) |
| Single-recipe behind the claim | `record_result` | **Settled on the spot.** `failed` with an es-ES error; a regenerate is the user's choice |
| The settlement cannot be written | Outage during settling | **Reported.** The next delivery only settles; else DLQ |
| Any later delivery (`ApproximateReceiveCount` > 1) | Dead attempt, throttled claim | **Settle only**: no provider call, no candidate (E5) |
| Poison | Unparseable JSON, non-object body, `MalformedMessage`, unknown `type` | **Never retried.** Logged at ERROR, acknowledged, record untouched (Q2 (a)) |

The split must be structural, not by exception type: `_process_record` mixes parsing and running, so a `KeyError` from a use case would pass for poison. Parsing moves to its own step (a staged test pins this).

### 3. Is a retry safe?

**Double spend today: no.** `claim` is conditional on `estado = pending`, and `claim_slot` on the slot's `estado`; `provider.generate` is unreachable behind them.

**Stuck behind its own claim: yes, and this decides the fix.** A handler-only fix reports a mid-run failure, gets one redelivery 90 minutes later, finds `claim` false, returns normally and is deleted: same stuck run, later, and the DLQ still unreachable. Mutant H4 is that fix: 14 staged tests fail.

**Removing the wall naively is worse.** Re-running a claimed run pays again: up to 14 calls per delivery (`terraform/lambda.tf:69`), so up to 70 across `maxReceiveCount` 5, and `add_slot_candidate` mints a new candidate id each time, so finished slots gain duplicates. That breaks `FR-AI-08`: "shall **not** produce duplicate candidates nor duplicate AI invocations/charges".

**Even a rerun that pays for nothing is wrong for the user** (owner, 2026-11-08): it lands 90 minutes after the click, and a redelivery can add up to 14 paid candidates to a week the user has changed since. "A late retry must therefore never be the way a user learns of a failure."

**So:** only the first delivery runs; any later one settles. Telling a dead attempt from a live duplicate uses `ApproximateReceiveCount`, present in the [event](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html): at 1 a `False` claim is a duplicate, unchanged behaviour; above 1 the 5400 s visibility outlasts the 900 s function timeout, so the earlier attempt has ended.

**A run with `slots: []` cannot simply be marked `failed`:** contract §3.5 defines `failed` as "at least one slot and every slot `error`". The plan writes one `error` entry per open target through the existing `begin_slots` (targets from a re-read of the week, or from the rules alone if it cannot be read), so `settle_run` derives `failed` and every row gets a retry button. With the rules-only fallback a slot that already holds a definitive also shows `error` and its retry answers 409; that is the only imprecision, and only when the week is unreadable twice. No clean alternative exists without a contract change.

### 4. Queue settings

`terraform/sqs.tf`, `terraform/locals.tf:23`. **All correct; no Terraform change is needed for the fix.**

| Setting | Value | Against [AWS guidance](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html) |
|---|---|---|
| `visibility_timeout_seconds` | `6 * 900` = 5400 s | "at least six times the configuration timeout on your function" |
| `maxReceiveCount` | 5 | "We recommend setting the maxReceiveCount [...] to at least 5" |
| `message_retention_seconds` | 4 days | Outlasts 5 receives |
| `batch_size` | 1 | A report covers exactly one run |

Consequences: a reported message returns only after the visibility timeout ("After the visibility timeout, the messages become visible to Lambda again"), so **a redelivery is 90 minutes away** and the **DLQ is at least 7.5 hours away** (5 × 90 min). This is why the plan settles at once whenever it can write, and reports only what it could not record. `ai_timeout = 900` stays (owner).

**Once in the DLQ:** nothing consumes it (`generation_dlq` has no mapping). The alarm fires while a message is visible and stays in alarm; the body is kept up to 14 days ("the expiration of a message is always based on its original enqueue timestamp", [SQS DLQ docs](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)). Redriving is manual. The record stays non-terminal until then or until TTL.

### 5. Other callers of `handle`

`local_worker._poll_once` (`:134-139`) deletes the whole batch regardless. It must honour the report and pass the receive count, or it would diverge from the deployed path. Locally a reported message returns after 30 s (`elasticmq.conf`) with no DLQ; that second delivery only settles, so nothing is spent. The local worker passes no deadline.

**Existing tests pinning today's swallow: none pins the swallow of a non-poison failure.** No existing test sends one through `handle`; the overlay's full suite shows it.

- **Poison isolation, stays green unchanged:** `test_worker_handler.py::test_a_two_record_batch_runs_both_and_isolates_a_failure`, `::test_a_malformed_slot_retry_is_isolated_and_touches_nothing`; `test_recipe_message.py::test_the_handler_dispatches_a_recipe_record_and_isolates_a_bad_one`, `::test_an_unknown_message_type_is_isolated`.
- **Stubs of `handle` returning `None`, break and need a one-line stub change (no assertion changes):** `test_local_worker.py::test_poll_once_forwards_deps_to_handle`; the `run_worker` fixture in `test_local_worker_transient_sqs_errors.py`, which fails `test_a_receive_read_timeout_is_logged_and_polling_continues`, `test_an_unreachable_emulator_is_logged_and_polling_continues` and `test_a_delete_read_timeout_is_logged_and_polling_continues`. Exact edits in `plan.md`.

### 6. Requirements

**No frozen-doc lift is needed.** The fix restores `FR-AI-08`, `FR-AI-09` (partial results) and `FR-AI-12`; no `FR-*` text changes. `NFR-OBS-02` ("At least **one active alarm** shall notify an email or channel") is met today and after the fix: it asks for an alarm, not for coverage; the owner declined a new one (Q3). The deadline and the Bedrock limits invent no behaviour: they are how `FR-AI-12`'s per-slot `error` is reached before the function is killed.

**Statements the fix falsifies or that are already false:**

- `terraform/monitoring.tf:11` — "A message reaching the DLQ means a generation run crashed or timed out 5 times." False today. After the fix a message reaches it only when the record could not be read or written across 5 deliveries, or the invocation failed each time before handling (wiring, import). A timeout is now settled by its second delivery, not dead-lettered.
- `specs/ai_lambda/design.md:47` — handler row: "call one use case per record → return." It now returns a partial batch response.
- `specs/ai_lambda/design.md:125-126` — "Each slot's exception is caught and turned into a `SlotGenerationResult` (R4)". False today; stays false under the specific fix (Q1).
- `specs/ai_lambda/design.md:203-205` — `claim` "`False` when another delivery already owns it or it is terminal". Now incomplete: above receive 1 it means the earlier attempt died.
- `specs/ai_lambda/design.md:342-343` and `specs/ai_lambda/tasks.md:78-79` — per-record isolation cited as `R4`. Wrong requirement.
- `specs/ai_lambda/requirements.md` R13 — "already `running` [...] SHALL NOT invoke". Still true, and now stronger: no later delivery invokes, whatever the status (E5). Re-checked: no longer falsified (the first draft's no-slot rerun is gone).
- `backend/lambda_ai/src/planner_ai/adapters/bedrock.py:146` — "production reads the default Bedrock-runtime client". It gains explicit timeouts and retries (E17); no spec states the client's limits.
- `backend/lambda_ai/src/planner_ai/handler.py:3`, `:120` and `local_worker.py:135-137` — fixed by the change itself (T6–T8).

Line numbers re-checked against `HEAD` on 2026-11-08.

## Owner rulings (2026-11-08)

- **Q1: specific.** Slots after a failed one become `error`; the user retries them. The general fix is issue 28.
- **Q2: (a).** Poison is logged at ERROR and acknowledged, never reported; its record is untouched.
- **Q3: no alarm.** No Terraform change at all.
- **Q4:** filed as issue 29, out of scope.
- **New retry policy:** only the first delivery may call the provider; settle on the spot whenever the worker can write; report only when nothing was paid and nothing could be recorded; a per-slot deadline from `context.get_remaining_time_in_millis`; a Bedrock client timeout. The plan implements exactly this.

## Blast radius and the questions as they were put

Same chain, all three paths: whole-week, per-slot retry and single-recipe (all in the plan). `api`, the SPA, ports and DynamoDB adapters are unchanged; the Bedrock adapter gains a client config. The questions below are answered above and kept for the record.

**Q1. General or specific fix for slot isolation?** The narrow catch at `week_generation.py:122` also breaks an operation the report never mentions: `FR-AI-09` "the failure of one shall not abort the others". A `save_slot` failure on slot 3 abandons slots 4–14 unattempted.
- **Specific (planned):** those slots become `error`; the user retries each. `FR-AI-09` stays violated for non-provider failures; file it separately.
- **General:** remaining slots keep going. Costs a per-slot catch that `docs/conventions.md` forbids in `core` ("Never catch bare `Exception` outside the handler boundary"), so it needs a port-level error type or a convention exception, and during an outage it pays Bedrock for candidates that then cannot be written (up to 14 calls). Needs a new `E` and tests.
- *Recommendation:* specific now, general as its own issue.

**Q2. Poison after the fix.** As planned, poison is acknowledged and logged, and its record stays `pending`, so that user keeps the spinner until TTL. Only version skew between `api` and `ai`, or a hand-sent message, produces poison; `api` builds every body.
- **(a) Planned.** Three existing tests pin the record as untouched.
- **(b) Report poison.** It would reach the DLQ after 5 receives (7.5 h, no spend, body kept, alarm fires), at the price of 4 redeliveries that cannot succeed, which the triage brief ruled out ("A poison message must not loop").
- **(c) Also write `failed`.** For a week run that is `failed` with `slots: []`, which contradicts contract §3.5 ("at least one slot and every slot `error`"), leaves rows reading "Generando…" under a finished panel, and returns the same record on re-submit.
- *Recommendation:* (a), with Q3 covering visibility.

**Q3. Alarm coverage.** After the fix `lambda_errors` fires on timeouts, crashes and wiring failures only (see the `Errors` quote), and `generation_dlq` on sustained failures. **A failure settled on the spot and a poison message trip neither**; they leave only an ERROR log line. `NFR-OBS-02` does not require more, so this is optional. Answered: no alarm, and the snippet was removed from `plan.md`.

**Q4. Unbounded polling.** After the fix a spinner remains possible for poison and for runs parked in the DLQ. A client-side poll deadline would cover those and any future cause, but it is a frontend change with its own wording. Separate issue, or leave it?

## 7. Deadline and Bedrock limits

`lambda_handler` builds `has_time()` from `context.get_remaining_time_in_millis()` ("Returns the number of milliseconds left before the execution times out", [Python context](https://docs.aws.amazon.com/lambda/latest/dg/python-context.html)) and passes it down; core sees only a `Callable[[], bool]`, no clock and no AWS type. Before each slot, if the time left does not exceed `SLOT_RESERVE_SECONDS`, that slot and the rest become `error` and the run settles in the same delivery.

The reserve needs a bounded provider call. Today `bedrock.py:154` builds the client with no `Config`, so [botocore defaults](https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html) apply: `connect_timeout` and `read_timeout` 60 s, and boto3's default legacy [retry mode](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/retries.html) allows 5 attempts — about 600 s for one slot. Recommended: `connect_timeout=5`, `read_timeout=60`, `retries={"mode": "standard", "total_max_attempts": 2}` ("total_max_attempts" counts the initial request; standard mode caps backoff at 20 s). Worst case 2 × (5 + 60) + 20 = 150 s; reserve 150 + 30 s for the record writes = 180 s. The 60 s read is under a slot's equal share (900 / 14 ≈ 64 s) and generous for one Nova 2 Lite response at the default 4,096 output tokens. **Not measured against the live model**: if real responses approach 60 s, `read_timeout` is the value to revisit, and every timeout becomes a slot `error` the user can retry.

## What remains slow after the fix

The owner asked for this plainly. A user still waits long only when the worker cannot write or does not survive to write:

- **A worker that dies without warning** (out of memory, runtime crash, a hang the deadline does not cover). Nothing is written; the run is settled by the next delivery, **90 minutes later**.
- **A database that cannot be read or written.** The settlement fails, the message is reported, and the next delivery settles it in 90 minutes; if the outage outlasts 5 deliveries the message reaches the DLQ after **7.5 hours** with the record still `pending` or `running`, until TTL. The DynamoDB clients keep botocore's defaults (60 s timeouts, legacy retries), so a slow table can also eat the deadline's margin.
- **A throttled claim.** Nothing was paid, but the run is only settled `failed` by the delivery 90 minutes later; it is never run.
- **Poison.** Acknowledged with its record untouched, so its spinner lasts until TTL (Q2 (a); the polling cap is issue 29).

**Other residuals, not addressed:**
- A claim applied server-side whose response was lost and retried by botocore reads as `False` at receive 1: acknowledged, stuck `running` until a later delivery that never comes. Pre-existing and narrow.
- How SQS numbers a true duplicate is not stated in the docs. If one arrives above 1 during a live attempt, it settles slots that attempt then overwrites with `done`; `settle_run` recomputes, so the run still ends terminal.

## Severity

**Medium stands.** Against raising: nothing has been observed on AWS, DynamoDB failures that survive botocore's retries should be rare, persisted candidates are kept, the claim prevents a double spend, and the kill-switch is unaffected. Against lowering: no recovery for days on an identical request, and the operator is told nothing. Issue 22's reproduction test records the same blindness: "every record fails inside the per-record catch, so nothing is claimed". Timeouts are the likeliest trigger: 14 slots share 900 s, and the Bedrock client sets no timeout of its own (`adapters/bedrock.py:154`); §7 bounds both.

## Not run

No AWS call (so the Bedrock timeouts are unmeasured), no `terraform` command of any kind (`validate`, `plan`, `fmt`), no Docker, so ElasticMQ and DynamoDB Local were not exercised (moto stood in), no `./init.sh`, no full `uv run mypy .`. The whole pipeline from SQS through the event source mapping is unproven on real AWS and is worth one manual check after deployment.
