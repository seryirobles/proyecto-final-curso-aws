# Implementation: week_generation_backend (feature 36)

`./init.sh` green: 1324 backend tests, ruff, mypy, frontend gates. Not marked done.

## Traceability (R -> test)

| R | Test |
|---|---|
| R1-R3 | `core/tests/application/test_week_generation.py` (library_only: zero provider/gate reads, insufficient code/message) |
| R4 | `test_ai_only_never_reads_the_library` |
| R5-R6, R12 | `test_mix_fills_from_the_library_before_any_provider_call`, `test_mix_sends_the_ai_only_the_needs...` |
| R7 | resolve_targets unchanged; library fill takes `targets.open_slots` only (week_generation tests) |
| R8-R11 | `core/tests/domain/test_library_fill.py`; `test_library_fill_excludes_a_name_already_in_the_week`; `test_equal_inputs_give_equal_library_picks` |
| R13-R14 | `test_a_library_pick_is_a_candidate_and_never_replaces_a_definitive` |
| R15 | `test_library_only_never_invokes_the_provider_even_with_the_gate_disabled` |
| R16 | `lambda_ai/tests/test_write_path.py`; `ai_dynamo_recipe_repository` in `test_recipe_repository_contract.py` |
| R17-R20, R27 | `test_progress_is_pending_first_...`, `test_begin_slots_records_...`, `test_a_failed_slot_carries_a_code...` |
| R21, R52 | sink contract: `test_record_slot_changes_only_that_slot...`, `test_the_dynamo_slot_writes_name_only_their_own_slot_path` |
| R22 | vocabulary replaced everywhere; old assertions rewritten |
| R23-R26 | `test_library_fill.py::test_run_status_table`; week_generation outcome tests |
| R28-R31, R33 | `lambda_api/tests/test_generation_route.py` (slots shape, empty list, single-recipe unchanged) |
| R32 | `test_a_stored_week_hit_on_post_returns_the_get_shape` |
| R34 | queue contract `test_submit_stores_the_run_and_an_empty_slot_map`, snapshot round trip |
| R35, R37, R43 | `test_the_retry_route_requires_the_user_role`, `test_retrying_an_error_slot_returns_202...`, `..._400` |
| R36, R40, R45, R46 | queue contract (retry pending/running, concurrent, single message, restore on failed enqueue, one conditional write) |
| R38-R39, R41-R42, R44 | `core/tests/application/test_generation_retry.py`, route tests (409/404) |
| R47-R51, R53 | `test_generation_retry.py` worker tests, `lambda_ai/tests/test_worker_handler.py`, `test_message.py` |

FR traceability: `covers` is empty by design (cited, not claimed).

## Not anticipated by the spec

- `GenerationNotFound` moved from `planner_api.serialization` to `ports/generation_queue.py` (core use case raises it); added `GenerationSlotNotFound`, `SlotNotRetryable` there.
- `retry_slot` use case and `GenerationQueue.retry_slot` take `author` (R53 needs it).
- Name exclusion uses `domain.text.normalize` (case, accent, trim fold), not bare `casefold()`: `test_shared_kernel_guards` forbids a second name fold.
- The ai `DynamoRecipeRepository` is a full copy (save/delete included), not stripped: the contract suite needs the whole protocol; read-only is an IAM matter (feature 21).
- Worker retry of a slot no longer open (definitive appeared after acceptance) records `done` with no write; no error code fits.
- Legacy in-flight week records without `franjas` would fail the nested SET (`begin_slots`); only pending pre-deploy records are affected.
- `select_library_fill` is generic over a structural `id`/`recipe` protocol so `domain/` imports nothing from `ports/`.
- Live-run checklist: design.md section 9 (paid, not run).

## Review fixes (round 1)

- Defect: `SqsGenerationQueue.retry_slot` now uses `ReturnValues=ALL_OLD`; a failed enqueue restores the slot's previous entry, so `codigo`/`mensaje` survive (queue contract test asserts it).
- R34: `submit` test with non-default rules, mode and prompt version, on fake and sqs.
- R44/R49: use-case tests (stored rules disable or pin the day), sqs message test (non-empty `effectiveRules`, mode), handler test (`library_only` retry makes zero provider calls).
- Worker branch for a retried slot no longer open: test records `done`, writes nothing.
- Sink contract `_PER_SLOT` replaced by a single-recipe error dict.
- `./init.sh` green (1331 backend tests).
