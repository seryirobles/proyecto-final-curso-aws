# week_generation_backend — Tasks

Test-first inside each task. Contract, data-model and gaps docs are lifted by the owner/leader (design §8); do not edit them.

- [x] T1 — Add `SlotStatus`, `RunStatus`, `SlotError`, `SlotProgress`, `GenerationSnapshot`, `run_status`, `select_library_fill`, `reduce_needs` in `domain/generation.py`, with domain tests. Covers: R7-R12, R23-R26.
- [x] T2 — Extend `GenerationResultSink` (`begin_slots`, `record_slot`, `claim_slot`, `record_status`, `stored_generation`) and `StoredGeneration` (`slots`, `snapshot`); update `FakeGenerationQueue`; add `settle_run`. Covers: R17-R21, R27, R47.
- [x] T3 — Rework `run_week_generation`: mode handling, library fill, per-slot progress, `settle_run`, `SlotProgress` vocabulary; extract the shared per-slot procedure. Update the tests listed in design §6. Covers: R1-R6, R13-R20, R22, R27.
- [x] T4 — Add `planner_ai/adapters/dynamo/recipes.py` (complete copy of the api adapter) and wire it in `wiring.py`; add it to the `RecipeRepository` contract suite. Covers: R16.
- [x] T5 — Implement `DynamoGenerationRecords` new methods and `SqsGenerationQueue` snapshot/`franjas` init at submit, `retry_slot`; extend the queue and sink contract suites over fake and moto. Covers: R21, R34, R36, R40, R45, R46.
- [x] T6 — Implement `generation_retry.retry_slot`, exceptions, es-ES messages, error-table rows. Covers: R36, R38-R42, R44.
- [x] T7 — Implement `run_slot_retry` and the `slot_retry` branch in `handler.py`/`message.py`. Covers: R47-R53.
- [x] T8 — Routing: slots shape in `_get_generation` and the `200` submit hit; retry route in `ROUTES` with day/slot parsing; update `test_routing_table.py`, `test_generation_route.py`, `test_request_log_line.py`. Covers: R28-R33, R35, R37, R43.
- [x] T9 — Run `./init.sh`; write `progress/impl_week_generation_backend.md` with the R-to-test traceability and the live-run checklist (design §9). Covers: R1-R53.
