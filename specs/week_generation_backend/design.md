# week_generation_backend — Design

> Feature 36 · read `requirements.md` first. Builds on 17 (`ai_lambda`), 27, 28.
> Sources: `rest_api_contract.md` §2/§3.5/§4/§7 Q4, `data_model.md` §2/§4.6/§5,
> `specs/ai_lambda/design.md` §6/§8, `G-18`, `G-19`, `G-66`.
> No `architecture.md` §2 item needed. No frozen `FR-*` change. Contract and
> `data_model.md` lifts are listed in §8 (owner/leader edit; not done here).

## 1. Mode semantics (R1-R16)

New pure domain function in `domain/generation.py` (no I/O, takes data):

```python
def select_library_fill(
    open_slots: tuple[SlotRef, ...],          # chronological
    library: tuple[LibraryRecipe, ...],
    needs: tuple[CategoryCountRule, ...],     # remaining counts
    used_names: frozenset[str],               # casefolded names of meals already in the week
    seed: str,                                # the idempotency key
) -> dict[SlotRef, LibraryRecipe]
```

Algorithm: drop recipes whose casefolded name is in `used_names`; sort by id;
`random.Random(seed).shuffle`. For each slot in order: take the first recipe of
the first category (rule order) with a remaining count; if none, the first
remaining recipe; if the pool is empty the slot gets no pick. A pick removes the
recipe, adds its name to `used_names`, and decrements that category's need. A
second helper `reduce_needs(needs, picked_categories)` floors at 0 (R12).

`run_week_generation` flow (adds `recipes: RecipeRepository`, read-only):

1. claim; `occupancy`; `resolve_targets`; `begin_slots(open)` (R17).
2. `ai_only`: skip the library. Otherwise `list_all()` once, `select_library_fill`, then for
   each pick: re-read the slot, skip + `done` if definitive (R14), else
   `add_slot_candidate` (snapshot, `author` = submitter) and record `done`.
3. Slots without a pick: `library_only` records `error`/`insufficient_library_recipes`
   (message `AI_GENERATION_INSUFFICIENT_LIBRARY_RECIPES`; no gate, no provider, R1/R3).
   `mix`/`ai_only` run the existing AI path with `needs = reduce_needs(...)`; the
   gate check stays per AI slot (R15: library fill never reads it).
4. `settle_run` (§3).

Pinned slots remain feature 27's synchronous submit-time writes; they are not in
`slots[]` (the 202 `targets.pinnedSlots` reports them). Pinned names land in
`occupancy`, so they are excluded by R8 for free. Library picks are candidates,
so `resolve_targets`'s definitive-only counting is unchanged.

The worker needs the library: `planner_ai/adapters/dynamo/recipes.py`, a
read-only copy of the `planner_api` adapter (same precedent as `weeks.py`,
`ai_lambda` design §7), added to the `RecipeRepository` contract suite so drift
fails a test. IAM read on the library partition is feature 21's (deployment).

## 2. Persistence of progress (R17-R22, R34) — `data_model.md` §4.6 / §5

`PETICIONIA#<hash>/METADATA` gains two attributes (lift in §8):

- `franjas`: a map, one entry per open slot, key `"<day>-<slot>"` (e.g. `"3-1"`),
  value `{estado, codigo?, mensaje?}` with `estado` in `pending|running|done|error`.
  Initialised `{}` at submit (a nested `SET` needs the parent map to exist);
  absent on single-recipe records, which is how `GET` tells the two apart.
- `solicitud`: `{semana, modo, reglas, versionPrompt}` — the resolved effective
  rules, so a retry reproduces the run without a client override (§7 Q4).

Writes: `begin_slots` = one `UpdateItem` setting every `franjas.#k`; `record_slot`
= `SET franjas.#k = :v`, one slot, unconditional (the claim established
ownership). There is no read-modify-write, so concurrent per-slot tasks and
concurrent retries cannot lose each other's updates (`FR-AI-09`). `estado` stays
a run attribute. `resultado` is not written for week runs. The record keeps its
`ttl`; `AP27` stays one `DeleteItem`. `PETICIONIA#` has no `MarcaCambio`, so no
ETag rule is touched, and `put_pending` stays create-if-absent so idempotency is
unchanged. Legacy week records (7-day TTL) read as `slots: []`.

Domain types (`domain/generation.py`): `SlotStatus`, `RunStatus`, `SlotError(code,
message)`, `SlotProgress(day, slot, status, error)`, and pure
`run_status(slots) -> RunStatus` (R23-R26). `StoredGeneration` gains
`slots: tuple[SlotProgress, ...] | None` and `snapshot: GenerationSnapshot | None`.

## 3. Ports

`GenerationResultSink` (worker side) adds: `begin_slots(key, slots)`,
`record_slot(key, progress)`, `claim_slot(key, day, slot) -> bool` (conditional
`pending -> running`, R47), `record_status(key, status)`, and `stored_generation`
(moved up from `GenerationQueue`; strongly consistent). `record_result` stays for
single-recipe runs. Application helper `settle_run(key, sink)`: read slots; if any
`pending|running` write nothing (run stays `running`), else
`record_status(key, run_status(slots))`. Two simultaneous finishers both compute
the same terminal value, so it is idempotent (R27, R51).

`GenerationQueue` (api side) adds `retry_slot(key, day, slot, *, author) -> None`:
a conditional `UpdateItem` (`franjas.#k.estado = error`) setting the slot `pending`
and `estado = running`; `ConditionalCheckFailed` -> `SlotNotRetryable`; then the SQS
send of a `type: "slot_retry"` message (`idPeticionIA`, `day`, `slot`, `weekId`,
`mode`, `effectiveRules`, `promptVersionId`, `authorUserId` = retrier); a send
failure restores the slot to `error` (R46).

## 4. Retry (R35-R53)

`application/generation_retry.py::retry_slot(generation_id, day, slot, first_day, *,
queue, weeks)`: load the record (`GenerationNotFound` 404); no `franjas` entry for
the slot -> `GenerationSlotNotFound` 404; resolve targets from the stored rules and
current occupancy; slot not open -> `SlotNotRetryable` 409 (R39); then
`queue.retry_slot`. New exceptions + es-ES strings in `messages.py`; the two codes
go in the `errors.py` table. Route `("POST", "/v1/generations/{generationId}/slots/{day}/{slot}/retry")`,
`requires_role=Role.USER`; day/slot parsed with `parse_day`/`parse_slot` (400).
Response `202` + `Location: /v1/generations/{id}`, body = the `GET` body.

Worker: `handler._process_record` dispatches `type == "slot_retry"` to
`run_slot_retry(...)`: `claim_slot` (lost -> return, R48), then the same per-slot
procedure as §1 for one slot (`library_only` -> library; `mix` -> library then AI;
`ai_only` -> AI, R49), kill-switch before the provider (R50), `record_slot`,
`settle_run`. The shared per-slot code is extracted from `run_week_generation`.
`local_worker.py` needs no change beyond reaching the new branch through `handle`.

Known limits (not fixed here): a worker crash leaves a slot `running` until the
7-day TTL (same as today's stuck run `running`); a retry accepted between a
finisher's read and write can show a terminal run status for a moment; the slot
list is self-healing because the retrying worker re-settles.

## 5. Wire shapes

```jsonc
// GET /v1/generations/{id}  (week)            // 200 on idempotent POST hit too
{ "generationId": "9f2c…", "status": "running",   // pending|running|completed|partial|failed
  "slots": [ { "day": 1, "slot": 1, "status": "done" },
             { "day": 1, "slot": 2, "status": "error",
               "error": { "code": "insufficient_library_recipes", "message": "…" } } ] }
```

Final-status table:

| Condition (all slots recorded) | Run status |
|---|---|
| nothing claimed yet | `pending` (`slots: []`) |
| any slot `pending`/`running` | `running` |
| no slots, or all `done` | `completed` |
| ≥1 `done` and ≥1 `error` | `partial` |
| ≥1 slot, all `error` | `failed` |

Error `code` values: `GenerationFailureReason` (`invalid_output`,
`insufficient_library_recipes`, `generation_unavailable`).

## 6. Vocabulary change — what must change (R22)

Source: `application/week_generation.py` (`SlotResult`, `_TERMINAL_STATUS`,
`_payload`, `message` field) is replaced by `SlotProgress`.
`application/single_recipe_generation.py` keeps `completed`/`failed` at **run**
level (unchanged). Tests: `core/tests/application/test_week_generation.py`
(L78-79, 104, 137, 167, 190, 224-227), `test_provider_error_logging.py`,
`test_validation_failure_logging.py`, `test_validation_failure_cause.py`,
`lambda_ai/tests/test_worker_handler.py` (L60), the per-slot payload in
`tests/contract/test_generation_queue_contract.py` (L118-156) and
`test_generation_result_sink_contract.py` (L23-78), `lambda_api/tests/test_generation_route.py`,
`test_request_log_line.py`, `test_routing_table.py` (new route). Single-recipe
`completed`/`failed` assertions stay.

## 7. Rejected alternatives

**Per-slot items (`SK = SLOT#d#s`) instead of a map on the one item.** Independent
writes and a trivial 409 condition, but `GET` becomes a `Query`, `AP27` must delete
many items, and a new SK format is needed. A nested map update gives the same
independence on one item.

**Do library fill synchronously in the `api` Lambda at submit (like pins).**
No new worker adapter, but mix needs the AI to know which slots were filled, the
retry route would need the same logic, and the logic splits across two Lambdas.
One use case in the worker is testable in one place.

**Re-derive the retry's rules from the shared `RuleSet`.** Needs no stored
snapshot, but silently drops the parent run's per-run override — the exact reason
§7 Q4 rejected a fresh `POST`.

## 8. Doc lifts (owner/leader; this spec edits none)

`rest_api_contract.md`: §2 add the retry row (and `200` on a stored week hit
returns the `GET` body); §3.5 example `"failed"` -> `"error"`, `AI_SLOT_FAILED` ->
the reason codes, add slot/run vocabulary, final-status table, mode semantics, the
retry subsection (202/404/409/400); §4 rows `SLOT_NOT_RETRYABLE` (409),
`GENERATION_SLOT_NOT_FOUND` (404), plus `GENERATION_NOT_FOUND` (404) which the
table omits today; §7 Q4 pointer. `data_model.md`: §2 slot-map key format
`"<day>-<slot>"`; §4.6 the `franjas`/`solicitud` attributes and the AP26 return
list; the L188 sentence ("override not persisted") becomes "the resolved effective
rules are stored on the record"; §5 a note that per-slot progress is a nested
update, never read-modify-write. `gaps_and_resolutions.md`: a lettered Part
recording `mix` semantics and that `G-63`'s "even library-only mode is the AI
selecting from the library" is superseded (`FR-AI-03` text unchanged).

## 9. Test strategy (feeds `tasks.md`)

Fakes-first, TDD, no AI spend: `select_library_fill` (category priority, name
exclusion, seeded determinism, empty pool), `run_status` table, worker flows per
mode with a counting fake provider (`library_only` = 0 calls, even with the gate
disabled), per-slot isolation, `ai_only` never touches the fake `RecipeRepository`,
definitive-at-write skip, progress ordering via a recording sink, retry use case
(404/409/400, concurrent acceptance, enqueue-failure restore), redelivery of the
retry message, `GET` body for week vs recipe, contract suites over fake and moto
for the new sink/queue methods, `RecipeRepository` adapter parity.

Only a live run shows (paid; proposed, not run): real `mix` fill quality and
latency per slot against a real library and Nova; `GET` polled mid-run actually
showing `running` slots; real DynamoDB nested-path and conditional semantics
beyond moto; SQS redelivery of a retry message; the kill-switch flipping
mid-run; a real `library_only` run leaving zero Bedrock invocations in the logs.
