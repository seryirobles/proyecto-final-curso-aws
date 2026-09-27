# Implementation: single_recipe_generation (feature 28)

Tests: backend 1029 passed, frontend vitest 465 passed; ruff, mypy, prettier, eslint green.
`./init.sh` gates (section 5) all OK; its only FAILs are the pre-existing
`issue_list.json` "done but issues/<name>/ missing" checks (issues 1-12, deleted by the
"remove stale issues" commit) - not this feature.

## Traceability (R -> T -> test)

| R | T | Test |
|---|---|---|
| R1-R2 | T4, T5, T6 | `lambda_api/tests/test_single_recipe_generation_route.py` (202, snapshot), `core/tests/application/test_single_recipe_submission.py`, `tests/contract/test_generation_queue_contract.py` (`submit_recipe`, message body) |
| R3 | T4, T6 | route 404 test; submission `test_unknown_reference_recipe...` |
| R4-R6 | T6 | route `test_malformed_bodies_are_400...` (14-row table incl. `attempt`), library target test |
| R7-R9 | T1 | `core/tests/domain/test_single_recipe_generation_key.py` |
| R10 | T2 | same file, golden hash |
| R11-R13, R15-R16 | T4, T6, T10 | submission probe tests; route in-flight/terminal/discard-resubmit tests |
| R14, R21 | T9 | `lambda_ai/tests/test_recipe_message.py::test_double_delivery_invokes_the_provider_once` |
| R17-R18 | T4, T6 | submission + route 422 tests |
| R19-R20 | T8, T9 | `core/tests/application/test_single_recipe_generation.py`; `test_recipe_message.py` |
| R22-R26 | T8 | same core test file (gate off, valid, provider error, invalid output, no WeekRepository param) |
| R23, R29 | T3, T5, T7 | contract `record_result` dict payload (fake, moto, ai adapter); `tests/contract/test_recipe_wire_parity.py` |
| R24-R25 | T8, T9 | signature test; `test_a_recipe_message_never_touches_the_week_repository` |
| R27 | T9 | `test_the_handler_dispatches_a_recipe_record_and_isolates_a_bad_one` |
| R28-R30 | T10 | route GET completed/failed, accept via `source:"generation"`, DELETE 204 |
| R31-R33, R37-R38 | T11, T12 | `frontend/tests/hooks/useAiGeneration.test.js`, `useRecipeAuthoring.ai.test.js` |
| R34-R36, R39-R40 | T12 | `frontend/tests/components/RecipeAuthoringForm.ai.test.jsx`, updated `RecipeAuthoringForm.test.jsx` |
| R41 | T11 | `useAiGeneration.test.js` unmount test |

FR reachability: FR-AI-01/-02/-08/-09/-10, FR-CAND-03, FR-LIB-04, FR-UX-03, NFR-AI-01 all
through the rows above.

## Not anticipated by the spec

- `run_single_recipe_generation` takes an extra `encode_recipe` callable: core owns no wire
  format, the `planner_ai` encoder is injected (design section 3 signature omitted it).
- `GET`/`200` decode a JSON-object `result` into an object (`decode_generation_result`); the
  whole-week per-slot list stays the string it was.
- The SPA polls with its own `setTimeout` loop, not `usePolling`: that engine is ETag/marker
  based and contract 3.6 says this GET is not conditional.
- Absent `ingredients`/`tools` in a specification source read as empty -> 422 (contract
  section 4 table); absent `extraSpecifications` on a reference source is 400.
- A worker crash other than `AiProviderError` leaves the record `running` (week-path
  precedent); an identical resubmit then dedupes until the TTL.
- Existing tests edited: `test_week_generation.py` (third-param rename/type),
  `test_generation_queue.py` (method list), `RecipeAuthoringForm.test.jsx` (two stub-notice
  tests replaced, R40).
