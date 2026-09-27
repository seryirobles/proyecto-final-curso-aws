# single_recipe_generation — Tasks

Test-first inside each task. The contract, gaps and data-model docs are already reconciled; do not edit them.

- [x] T1 — Add `SpecificationSource`, `ReferenceSource`, `SingleRecipeRequest` and `single_recipe_key` in `domain/generation.py`, with frozen-instance tests. Covers: R7, R8, R9.
- [x] T2 — Add a golden-hash test pinning the whole-week `idempotency_key`; leave the function untouched. Covers: R10.
- [x] T3 — Add `submit_recipe` to `GenerationQueue`; widen `record_result`'s payload type; update `FakeGenerationQueue`. Covers: R2, R23, R26.
- [x] T4 — Implement `application/single_recipe_submission.py` (probe loop, reference snapshot, prompt-version guard, empty `ingredients`/`tools` rejection). Covers: R2, R3, R11, R12, R13, R15, R16, R17, R18.
- [x] T5 — Implement `SqsGenerationQueue.submit_recipe` and the widened `record_result`; extend the queue contract suite over fake and moto. Covers: R1, R2, R23, R26.
- [x] T6 — Add the `type:"recipe"` branch, body parsing and `attempt` rejection in `_submit_generation` and `serialization.py`; add the routing validation table tests. Covers: R1, R2, R3, R4, R5, R6, R12, R13, R17, R18.
- [x] T7 — Add `planner_ai/serialization.py` recipe encoder and the parity test against `planner_api` `encode_recipe`. Covers: R23, R29.
- [x] T8 — Implement `application/single_recipe_generation.py` (claim, prompt, gate, provider, `validate_and_preview`, `record_result`) and its fakes-based tests. Covers: R19, R20, R21, R22, R23, R24, R25, R26.
- [x] T9 — Extend `planner_ai/message.py` and `handler.py` to dispatch on message `type`; test batch isolation and double delivery invoking the provider once. Covers: R14, R27.
- [x] T10 — Add routing tests for `GET` completed/failed, discard-then-resubmit, and accepting the result through `source:"generation"`. Covers: R15, R28, R29, R30.
- [x] T11 — Add es-ES messages and the `useAiGeneration` hook (submit, poll, stop on unmount) with Vitest tests. Covers: R31, R32, R33, R38, R41.
- [x] T12 — Replace `AiStubFields` and the `useRecipeAuthoring` AI stub with the real form, reference picker and preview (accept, discard, regenerate, failure); remove the unavailable notice. Covers: R32, R34, R35, R36, R37, R39, R40.
- [x] T13 — Run `./init.sh`; write `progress/impl_single_recipe_generation.md` with the R-to-test traceability. Covers: R1-R41.
