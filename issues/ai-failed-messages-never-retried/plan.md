# Issue 25 — plan

Redone 2026-11-08 under the owner's rulings (`analysis.md` § *Owner rulings*): only the first delivery may call the provider, a failure settles on the spot, and a run stops starting slots before the function times out.

## Expected behaviour

"Redelivered" or "a later delivery" means `ApproximateReceiveCount` above 1; an absent count reads as 1. "Settle" means: every slot still `pending` or `running` becomes `error`, finished slots stay, and the run status is recomputed — with no provider call and no candidate.

### E1
Implements: FR-AI-12, FR-AI-09

IF processing a claimed whole-week run raises, THEN the system SHALL settle the run in the same delivery, keeping every persisted candidate.

### E2
Implements: FR-AI-12, FR-UX-03

WHEN the system records a slot as `error` while settling or at the deadline, the entry SHALL carry a `GenerationFailureReason` `code` and an es-ES `message` from `planner_core.messages`.

### E3
Implements: FR-AI-12

WHEN a slot has been recorded as `error` under E1, E4, E6 or E16, the per-slot retry SHALL accept that slot.

### E4
Implements: FR-AI-12

WHEN a later delivery finds its whole-week run `running` with slot entries, the system SHALL settle it.

### E5
Implements: FR-AI-08

WHEN a later delivery arrives, whatever the run's state, the system SHALL NOT invoke the provider or add a candidate; it SHALL only settle.

### E6
Implements: FR-AI-12, FR-AI-08

IF a whole-week run has no slot entries when it is settled (the failure hit before or during `begin_slots`, or a later delivery finds it `pending` or `running` with none), THEN the system SHALL record as `error` every slot `resolve_targets` gives as open, re-reading the week, or from the rules alone when the week cannot be read, and settle the run (`failed`, or `completed` when nothing is open).

### E7
Implements: FR-AI-12

IF processing raises before the claim has applied, THEN `handle` SHALL report the message's id in `batchItemFailures`, and the next delivery SHALL settle the run under E5.

### E8
Implements: FR-AI-12

IF the system cannot record the settlement, THEN `handle` SHALL report the message's id in `batchItemFailures`.

### E9
Implements: FR-AI-12, FR-AI-08

IF a claimed single-recipe run raises, or a later delivery finds one `pending` or `running`, THEN the system SHALL record it `failed` with `{"error": {code, message}}` without a further provider call.

### E10
Implements: FR-AI-12, FR-AI-09

IF a claimed slot retry raises, or a later delivery finds its slot `pending` or `running`, THEN the system SHALL record that slot alone as `error` and recompute the run status.

### E11
Implements: FR-AI-08

WHEN a first receive finds its record behind the claim, or any delivery finds it terminal or absent, the system SHALL leave the record unchanged and acknowledge the message.

### E12
Implements: FR-AI-09, NFR-OBS-01

IF a message body cannot be parsed, THEN `handle` SHALL log it at ERROR and acknowledge it without claiming, invoking the provider or reporting it.

### E13
Implements: FR-AI-12

WHEN the local worker has polled a batch, it SHALL hand `handle` each message's receive count and delete only the messages `handle` did not report.

### E14
Implements: FR-AI-09

WHEN one record of a batch fails, the system SHALL still process the batch's other records and report only the failed one.

### E15
Implements: FR-AI-12

The Lambda entry point SHALL return `handle`'s partial batch response, letting a failure to build the dependencies propagate as a function error.

### E16
Implements: FR-AI-12

WHEN, before a slot starts, the time left in the invocation cannot cover one worst-case slot, the system SHALL record that slot and every later one as `error`, keep the finished ones, and settle the run in the same delivery.

### E17
Implements: FR-AI-12

The Bedrock client SHALL wait at most 5 s to connect and 60 s for a response, with at most 2 attempts in standard retry mode, so a response wait stays under one slot's share of the 900 s function (900 / 14 ≈ 64 s).

## Fix design

**No new dependency, port, adapter method, attribute or message constant. No frozen-doc lift. No Terraform change** (owner, Q3). Layers per `docs/architecture.md` §3: use cases in `application/`, mapping to the transport and the Lambda context in `handler.py`; core reads no clock and imports no AWS type — the deadline arrives as a `Callable[[], bool]`.

**The rule:** the first delivery runs; anything that goes wrong is settled at once while the worker can still write. A later delivery only settles. SQS gets a message back only when nothing was paid and nothing could be recorded.

### `backend/core/src/planner_core/application/week_generation.py`

`_Run` gains `has_time: Callable[[], bool]`; `run_week_generation` and `run_slot_retry` gain the keyword `has_time: Callable[[], bool] = _always` and pass it to `_Run`.

```python
def _always() -> bool:
    return True


def _interrupted(day: int, slot: int) -> SlotProgress:
    failure = build_generation_failure(GenerationFailureReason.GENERATION_UNAVAILABLE)
    error = SlotError(failure.reason.value, failure.message)
    return SlotProgress(day, slot, SlotStatus.ERROR, error)


def settle_week_run(
    key: str,
    request: GenerationRequest,
    effective_rules: RuleSet,
    first_day: date,
    *,
    occupancy: Callable[[], Mapping[SlotRef, SlotContents]],
    queue: GenerationResultSink,
) -> None:
    stored = queue.stored_generation(key)
    if stored is None or stored.status not in (RunStatus.PENDING, RunStatus.RUNNING):
        return
    slots = stored.slots or ()
    if not slots:  # never begun: record its targets as error (contract 3.5 needs a slot)
        targets = resolve_targets(request.week, effective_rules, first_day, dict(occupancy()))
        queue.begin_slots(
            key, tuple(_interrupted(s.day_number, int(s.slot.value)) for s in targets.open_slots)
        )
    for progress in slots:
        if progress.status in (SlotStatus.PENDING, SlotStatus.RUNNING):
            queue.record_slot(key, _interrupted(progress.day, progress.slot))
    settle_run(key, queue)


def settle_slot_retry(key: str, day: int, slot: int, sink: GenerationResultSink) -> None:
    stored = sink.stored_generation(key)
    slots = stored.slots or () if stored is not None else ()
    current = next((p for p in slots if (p.day, p.slot) == (day, slot)), None)
    if current is None:
        return
    if current.status in (SlotStatus.PENDING, SlotStatus.RUNNING):
        sink.record_slot(key, _interrupted(day, slot))
    settle_run(key, sink)
```

In `_fill_slots`, a sticky check before every slot, in both loops:

```python
    out_of_time = False

    def cut(slot: SlotRef) -> SlotProgress | None:
        nonlocal out_of_time
        out_of_time = out_of_time or not run.has_time()
        return _interrupted(slot.day_number, int(slot.slot.value)) if out_of_time else None
    ...
            progress = cut(slot) or _write_library_candidate(run, slot, picks[slot])  # library loop
    ...
        interrupted = cut(slot)                                                     # AI loop
        if interrupted is not None:
            progress = interrupted
        elif run.mode is GenerationMode.LIBRARY_ONLY:
```

`GENERATION_UNAVAILABLE` because its message is true here ("no está disponible en este momento. Puedes intentarlo más tarde."); `INVALID_OUTPUT` says the recipe is invalid. The tests accept any `GenerationFailureReason`.

**`slots: []` and contract §3.5.** `failed` needs at least one slot, all `error`, so a run with no entries cannot be failed as it stands. `settle_week_run` writes one `error` entry per open target through the existing `begin_slots`, then `settle_run` derives `failed`. The week is re-read for the targets; if that read fails too, an empty occupancy targets every slot the rules allow, so a slot that already holds a definitive also gets `error` and its retry answers 409 — a wrong slot on screen, not a stuck run. The alternatives — `failed` with `slots: []` — break §3.5 and are not taken.

### `backend/core/src/planner_core/application/single_recipe_generation.py`

```python
def settle_recipe_run(idempotency_key: str, sink: GenerationResultSink) -> None:
    stored = sink.stored_generation(idempotency_key)
    if stored is not None and stored.status in ("pending", "running"):
        unavailable = build_generation_failure(GenerationFailureReason.GENERATION_UNAVAILABLE)
        _failed(sink, idempotency_key, unavailable)
```

### `backend/lambda_ai/src/planner_ai/adapters/bedrock.py`

```python
from botocore.config import Config

_CONFIG = Config(
    connect_timeout=5, read_timeout=60, retries={"mode": "standard", "total_max_attempts": 2}
)
WORST_CASE_SECONDS = 2 * (5 + 60) + 20  # two full attempts plus the standard-mode backoff cap
...
        return self._client or boto3.client("bedrock-runtime", region_name=_REGION, config=_CONFIG)
```

Why these values (`analysis.md` §7): botocore defaults are 60 s connect and 60 s read, and the boto3 default legacy mode makes 5 attempts, so one slot can take ~600 s today. `total_max_attempts` counts the first request; standard mode caps backoff at 20 s. 60 s read is under a slot's 64 s share and well above a 4,096-token Nova 2 Lite response.

### `backend/lambda_ai/src/planner_ai/wiring.py`

```python
from planner_ai.adapters.bedrock import WORST_CASE_SECONDS, BedrockAiProvider

SLOT_RESERVE_SECONDS = WORST_CASE_SECONDS + 30
"""Time a slot may need: a worst-case provider call plus its record writes."""
```

Here, not in `handler.py`, because a handler may not import an adapter (§3.1 rule 4).

### `backend/lambda_ai/src/planner_ai/handler.py`

Split `_process_record` into `_parse_record(record)` and `_run(message, deps, has_time)` (keep the log lines). The bare catches stay at the handler boundary (`docs/conventions.md`).

```python
HasTime = Callable[[], bool]


def _occupancy(deps: Dependencies, week: IsoWeek) -> Mapping[SlotRef, SlotContents]:
    try:
        return deps.weeks.get_week(week)
    except Exception:  # unreadable: settle every slot the rules target (plan.md E6)
        logger.exception("Week %s unreadable while settling a run", week.week_id)
        return {}


def _settle(message: _Message, deps: Dependencies) -> None:
    # recipe -> settle_recipe_run; slot retry -> settle_slot_retry;
    # week -> settle_week_run(..., civil_date(deps.clock.now()),
    #                         occupancy=lambda: _occupancy(deps, message.request.week), ...)


def _unclaimed(message: _Message, deps: Dependencies) -> bool:
    """Whether this delivery's claim never applied, so nothing was paid or recorded."""
    # slot retry: its own slot entry is still PENDING; otherwise: the record is "pending"


def _attempt(message: _Message, receives: int, deps: Dependencies, has_time: HasTime) -> bool:
    """One delivery of a parsed message; True when SQS must deliver it again."""
    if receives > 1:  # only the first delivery may call the provider (plan.md E5)
        _settle(message, deps)
        return False
    try:
        _run(message, deps, has_time)
    except Exception:  # the handler boundary (docs/conventions.md)
        logger.exception("Failed to process SQS record")
        if _unclaimed(message, deps):
            return True
        _settle(message, deps)
    return False


def handle(
    event: dict[str, Any], deps: Dependencies | None = None, has_time: HasTime = _always
) -> dict[str, Any]:
    resolved = deps if deps is not None else build_dependencies()
    failures: list[dict[str, str]] = []
    for record in event.get("Records", []):
        try:
            message = _parse_record(record)
        except _UNPARSEABLE:  # poison: no delivery can succeed, so none is asked for
            logger.exception("Dropped unparseable SQS record %s", record.get("messageId"))
            continue
        try:
            retry = _attempt(message, _receives(record), resolved, has_time)
        except Exception:  # nothing could be recorded; a later delivery settles it
            logger.exception("Could not settle SQS record %s", record.get("messageId"))
            retry = True
        if retry:
            failures.append({"itemIdentifier": record["messageId"]})
    return {"batchItemFailures": failures}


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    quiet_sdk_loggers()

    def has_time() -> bool:  # a worst-case slot must fit before the function times out
        return bool(context.get_remaining_time_in_millis() / 1000 > SLOT_RESERVE_SECONDS)

    return handle(event, has_time=has_time)
```

`_UNPARSEABLE = (MalformedMessage, ValueError, KeyError, AttributeError, TypeError)`; `_receives` is `int(record.get("attributes", {}).get("ApproximateReceiveCount", 1))`. `build_dependencies()` stays outside the loop so a wiring failure still fails the invocation (E15). Correct the docstring and comment that cite `R4`. Recipes get no deadline: one call fits.

### `backend/lambda_ai/src/planner_ai/local_worker.py`

```python
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=_WAIT_TIME_SECONDS,
        AttributeNames=["ApproximateReceiveCount"],
    )
    ...
                "body": m["Body"],
                "attributes": m.get("Attributes", {}),
    ...
    # Mirrors the SQS trigger: a reported message stays for redelivery, the rest go.
    reported = {f["itemIdentifier"] for f in handle(event, deps)["batchItemFailures"]}
    for message in messages:
        if message.get("MessageId") not in reported:
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])
```

The local worker passes no deadline (`has_time` defaults to always).

### Existing tests: two stubs, no assertion

`handle` now returns a value that `_poll_once` reads. Without these edits 4 tests fail with `TypeError`. Re-checked against `HEAD` on 2026-11-08: both one-line `lambda` stubs are still there unchanged.

`backend/lambda_ai/tests/test_local_worker.py`, in `test_poll_once_forwards_deps_to_handle`:

```python
    def fake_handle(event: Any, d: Any = None) -> dict[str, Any]:
        calls.append(d)
        return {"batchItemFailures": []}

    monkeypatch.setattr(local_worker, "handle", fake_handle)
```

`backend/lambda_ai/tests/test_local_worker_transient_sqs_errors.py`, in the `run_worker` fixture:

```python
    def fake_handle(event: Any, deps: Any = None) -> dict[str, Any]:
        handled.append(event)
        return {"batchItemFailures": []}

    monkeypatch.setattr(local_worker, "handle", fake_handle)
```

### Terraform

**None** (owner, Q3: no alarm). `function_response_types`, `visibility_timeout_seconds`, `redrive_policy` and `ai_timeout = 900` stay. One comment goes stale, `terraform/monitoring.tf:11`; it is human-owned and listed in `analysis.md` §6.

### Rejected alternatives

**Report or raise only, leaving the claim alone.** The smallest diff. A mid-run failure gets one redelivery 90 minutes later, finds `claim` false and is deleted, so the run stays stuck (mutant H4: 14 staged tests fail).

**Let a later delivery rerun a run that paid for nothing** (the first draft of this plan). Safe on spend, but the rerun comes 90 minutes after the click, and a redelivery can add up to 14 paid candidates to a week the user has since changed. Replaced by E5 on the owner's ruling.

**Resume unfinished slots on redelivery.** Same lateness, plus `needs` and `avoid` rebuilt from a changed week. `FR-AI-12` already names the mechanism: per-slot retry.

## Test plan

### Staged files

| Staged under `issues/ai-failed-messages-never-retried/tests/` | Destination |
|---|---|
| `backend/lambda_ai/tests/test_worker_failure_recovery.py` | `backend/lambda_ai/tests/test_worker_failure_recovery.py` |
| `backend/lambda_ai/tests/test_bedrock_client_limits.py` | `backend/lambda_ai/tests/test_bedrock_client_limits.py` |
| `backend/lambda_ai/tests/test_local_worker_partial_batch.py` | `backend/lambda_ai/tests/test_local_worker_partial_batch.py` |
| `backend/tests/contract/test_generation_failure_recovery.py` | `backend/tests/contract/test_generation_failure_recovery.py` |

Moto and fake values only, no network. Building the Bedrock client calls no AWS. The contract file needs `AWS_DEFAULT_REGION`, which `core/tests/conftest.py` sets when the whole suite is collected; alone, set a fake region. It names no AWS SDK (`test_no_aws_sdk_import`).

### Tests changed by the redo, and why

Each expected a later delivery to finish a run; E5 forbids that, so each now expects that delivery to settle with 0 provider calls.

| Old | New | Now expects |
|---|---|---|
| `test_a_run_claimed_before_any_slot_began_completes_on_redelivery` | `test_a_run_a_dead_attempt_left_with_no_slots_is_failed_on_redelivery` | `failed`, 14 `error`, 0 calls |
| `test_a_read_failure_right_after_the_claim_completes_on_redelivery` | `test_a_read_failure_right_after_the_claim_fails_the_run_on_the_spot` | settled in the first delivery (E6) |
| `test_a_failed_slot_setup_completes_on_redelivery` | `test_a_failed_slot_setup_fails_the_run_on_the_spot` | settled in the first delivery (E6) |
| `test_a_claim_throttled_once_completes_on_the_next_delivery` | `test_a_claim_throttled_once_is_failed_by_the_next_delivery_without_paying` | reported, then `failed`, 0 calls |
| `test_a_recipe_claim_throttled_once_completes_on_the_next_delivery` | `test_a_recipe_claim_throttled_once_is_failed_by_the_next_delivery` | reported, then `failed`, 0 calls |
| `test_a_slot_claim_throttled_once_completes_on_the_next_delivery` | `test_a_slot_claim_throttled_once_is_failed_by_the_next_delivery` | slot `error`, run `partial`, 0 calls |
| C `test_a_crash_behind_the_claim_is_settled_by_the_redelivery` | C `test_a_crash_before_any_slot_is_failed_by_the_redelivery_and_retryable` | `failed`, 14 `error` with messages on real DynamoDB, retry accepted |

`_FakeContext` gained `get_remaining_time_in_millis`.

### Traceability

`F` = `test_worker_failure_recovery.py`, `B` = `test_bedrock_client_limits.py`, `L` = `test_local_worker_partial_batch.py`, `C` = `test_generation_failure_recovery.py`. **Red** fails today; **green** is a guard that passes today.

| E | Tests | Today |
|---|---|---|
| E1 | F `test_a_write_failure_mid_run_leaves_no_slot_in_flight` **(reproduction)** | Red: 13 slots in flight |
| | F `test_a_write_failure_mid_run_settles_the_run_status`, `test_a_write_failure_on_the_first_slot_settles_the_run_as_failed` | Red: `running` |
| | C `test_a_mid_run_failure_ends_terminal_and_the_api_can_retry_the_slot` | Red: 13 in flight |
| | F `test_the_candidates_written_before_the_failure_are_kept`, `test_a_failure_the_run_could_record_is_not_handed_back_for_redelivery`, `test_a_failure_behind_the_claim_is_logged_as_an_error` | Green |
| E2 | F `test_each_interrupted_slot_carries_a_named_reason_and_a_spanish_message` | Red: 0 errors |
| E3 | F `test_an_interrupted_slot_accepts_the_per_slot_retry`; C both week tests | Red: no `error` slot |
| E4 | F `test_a_redelivery_settles_a_run_its_dead_attempt_left_running` **(reproduction)** | Red: in flight |
| | F `test_a_redelivery_of_a_run_that_never_started_a_slot_settles_it_as_failed`, `test_a_redelivery_finishes_a_run_that_only_lost_its_final_status` | Red: `running` |
| | F `test_a_redelivery_keeps_a_finished_slot_finished` | Green |
| E5 | F `test_a_late_delivery_of_a_run_never_claimed_settles_it_without_paying` | Red: `completed` with 14 calls |
| | F `test_a_redelivery_never_invokes_the_provider[2]`, `test_replaying_a_failed_run_through_the_queue_pays_for_nothing_extra`, `test_a_redelivery_never_adds_a_candidate` | Green: the claim holds today |
| E6 | F `test_a_read_failure_right_after_the_claim_fails_the_run_on_the_spot`, `test_a_failed_slot_setup_fails_the_run_on_the_spot`, `test_a_week_still_unreadable_while_settling_is_settled_from_the_rules`, `test_a_run_a_dead_attempt_left_with_no_slots_is_failed_on_redelivery`, `test_a_redelivered_run_with_no_open_slots_still_completes`; C `test_a_crash_before_any_slot_is_failed_by_the_redelivery_and_retryable` | Red: `running` |
| | F `test_settling_an_unstarted_run_leaves_a_definitive_slot_out` | Red: 0 errors |
| E7 | F `test_a_throttled_claim_is_reported_for_redelivery` **(reproduction of the report)** | Red: `[] != ['m-1']` |
| | F `test_a_claim_throttled_once_is_failed_by_the_next_delivery_without_paying` | Red: `pending` |
| | F `test_a_message_that_keeps_failing_reaches_the_dead_letter_queue` | Red: deleted |
| | F `test_a_parser_shaped_error_behind_the_parse_is_not_taken_for_poison[4]` | Red: not reported |
| E8 | F `test_a_failure_during_an_outage_is_reported_and_settled_on_redelivery` | Red: not reported |
| | F `test_a_lost_final_status_write_still_settles_the_run` | Red: `running` |
| E9 | F `test_a_lost_recipe_result_fails_the_run_instead_of_stranding_it`, `test_a_redelivered_recipe_behind_its_claim_fails_without_paying_again`, `test_a_recipe_claim_throttled_once_is_failed_by_the_next_delivery`; C `test_a_redelivered_recipe_behind_its_claim_is_recorded_as_failed` | Red: `running` / `pending` |
| | F `test_a_failed_recipe_run_carries_a_reason_and_a_spanish_message` | Red: no result (`KeyError`) |
| E10 | F `test_a_redelivered_slot_retry_fails_its_own_slot_only`, `test_a_slot_retry_that_cannot_write_its_candidate_settles_the_run` | Red: slot `running` |
| | F `test_a_redelivered_slot_retry_settles_a_run_with_nothing_else_in_flight` | Red: `running` |
| | F `test_a_slot_claim_throttled_once_is_failed_by_the_next_delivery` | Red: slot `pending` |
| E11 | F `test_a_first_receive_behind_the_claim_is_a_duplicate_of_a_live_attempt`, `test_a_record_without_a_receive_count_is_taken_for_a_first_receive`, `test_a_first_receive_of_a_recipe_behind_the_claim_is_a_duplicate_too`, `test_a_redelivery_of_a_finished_run_changes_nothing[3]`, `test_a_redelivery_of_a_discarded_run_is_acknowledged[3]`; C `test_a_first_receive_behind_the_claim_leaves_the_record_alone` | Green |
| E12 | F `test_a_poison_message_is_never_handed_back[6]`, `test_a_poison_message_claims_nothing_and_pays_nothing[6]`, `test_a_poison_message_is_logged_as_an_error[6]`; L `test_a_poison_message_is_deleted_rather_than_looping` | Green |
| E13 | L `test_a_reported_message_stays_on_the_queue`, `test_only_the_reported_message_of_a_batch_stays_on_the_queue` | Red: deleted |
| | L `test_a_redelivered_message_reaches_the_handler_with_its_receive_count` | Red: `running` |
| | L `test_a_processed_message_is_deleted` | Green |
| E14 | F `test_only_the_failing_record_of_a_batch_is_reported` | Red: not reported |
| | F `test_a_poison_record_does_not_stop_the_next` | Green |
| E15 | F `test_the_lambda_entry_point_returns_the_partial_batch_response` | Red: `None` |
| | F `test_a_wiring_failure_fails_the_invocation_so_sqs_redelivers` | Green |
| E16 | F `test_a_run_short_of_time_stops_after_the_slots_it_could_finish`, `test_the_last_slot_is_cut_when_only_it_does_not_fit`, `test_slots_finished_before_the_deadline_keep_their_candidates`, `test_no_slot_starts_when_only_a_worst_case_provider_call_is_left`, `test_a_slot_retry_short_of_time_fails_its_slot_without_paying` | Red: every slot runs (14 calls) |
| | F `test_a_library_run_short_of_time_writes_no_candidate` | Red: 3 candidates |
| | F `test_a_run_with_ten_minutes_left_finishes_every_slot` | Green |
| E17 | B `test_a_connection_attempt_gives_up_within_seconds`, `test_retries_use_the_standard_mode`, `test_a_call_makes_at_most_two_attempts` | Red: 60 s, `legacy`, 5 |
| | B `test_a_response_wait_fits_in_one_slots_share_of_the_function` | Green: botocore's 60 s default already fits; guards a raise |

The deadline tests drive `lambda_handler` with a fake context whose remaining time is a function of the provider calls made; the worst-case test derives the time from the real client's `meta.config`, so it names no constant.

### Results at triage (scratchpad copies only, live tree unchanged)

- **Today's code + staged tests: 49 failed, 42 passed**, each for the reason above. Every failure is an assertion about the record, the response or the client config; none is a collection, import or fixture error.
- **Design overlay + staged tests: 91 passed.**
- **Whole backend suite on the overlay: 1,610 passed** (1,519 on untouched `HEAD`; the 91 extra are the staged tests). Ruff check and format clean on the 12 touched files. Mypy clean on the 8 touched sources and new test files in a scoped run; `uv run mypy .` was not run on the overlay.
- **Mutants: 34 tried, 34 killed**, against the staged tests plus `test_worker_handler.py` and `test_recipe_message.py`.

| Mutant | Tests failing |
|---|---|
| H1 nothing is ever reported (today's swallow) | 15 |
| H2 a later delivery still runs the provider | 17 |
| H3 an unclaimed failure is not reported | 10 |
| H4 no settle on the spot: every claimed failure reported | 14 |
| H5 a failed settle is acknowledged | 2 |
| H6 poison reported | 12 |
| H7 a record with no count reads as a redelivery | 7 |
| H8 `lambda_handler` passes no deadline | 6 |
| H9 reserve ignored: any time left starts a slot | 6 |
| H10 an unreadable week while settling escapes | 1 |
| H11 the settle never re-reads the week | 1 |
| W1 deadline ignored in the core | 6 |
| W2 last slot never cut | 5 |
| W3 finished slots overwritten at the deadline | 3 |
| W4 library slots not cut | 1 |
| W5 week run gets an always-true deadline | 5 |
| W6 slot retry gets an always-true deadline | 1 |
| W7 settling an unstarted run writes nothing | 8 |
| W8 the settle overwrites finished slots | 8 |
| W9 the settle touches terminal runs | 2 |
| W10 the week settle skips `settle_run` | 17 |
| W11 the slot settle leaves its slot | 4 |
| W12 the slot settle skips `settle_run` | 3 |
| R1 the recipe settle does nothing | 5 |
| R2 the recipe settle ignores `pending` | 1 |
| B1 client built without limits | 4 |
| B2 read timeout 120 s | 2 |
| B3 legacy retry mode | 1 |
| B4 three attempts | 2 |
| B5 worst case understated | 6 |
| WI1 no slot reserve | 6 |
| L1 local worker deletes reported messages | 3 |
| L2 local worker drops the attributes | 1 |
| L3 local worker asks for no receive count | 1 |

Not tried: making the deadline non-sticky — equivalent, since remaining time only falls.

**Not run:** any AWS call (Bedrock timeouts were not measured against the live model), any `terraform` command, Docker (so ElasticMQ and DynamoDB Local), `./init.sh`, `uv run mypy .`.
