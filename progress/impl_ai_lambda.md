# impl — ai_lambda (feature 17)

Bundled implementer run, 2026-09-06 (Part 2, after the feature 27 delta landed
`GenerationQueue.claim` / `record_result` / message enrichment / pinned-slot
writes). Tasks T1–T24, all ticked.

## Traceability — R1–R21 → test

| R | SHALL | Tests |
|---|---|---|
| R1 | process one message as one request keyed by `idPeticionIA` | `lambda_ai/tests/test_worker_handler.py::test_each_record_is_one_use_case_run`; `lambda_ai/tests/test_message.py` (whole suite) |
| R2 | invoke the provider separately per target slot | `core/tests/application/test_week_generation.py::test_a_provider_failure_on_one_slot_leaves_the_others_persisted`, `::test_the_gate_is_read_before_every_slot` |
| R3 | each success is its own `WeekRepository` write | `test_each_success_is_its_own_week_write` (marker == 2 for 2 slots) |
| R4 | one slot fails → keep processing the rest | `test_a_provider_failure_on_one_slot_leaves_the_others_persisted`; `test_worker_handler.py::test_a_two_record_batch_runs_both_and_isolates_a_failure` |
| R5 | one slot fails → keep the succeeded slots' candidates | `test_a_provider_failure_on_one_slot_leaves_the_others_persisted` (3 persisted, 1 failed) |
| R6 | validated output → append via `WeekRepository` | same test + `test_generation_is_additive_and_skips_a_slot_that_is_definitive_now` |
| R7 | no other persistence path | `lambda_ai/tests/test_write_path.py` (worker use case has no DynamoDB verb / `SEMANA#`; only `adapters/dynamo/` issues raw writes) |
| R8 | derive from a read taken in the same step | `test_generation_is_additive_and_skips_a_slot_that_is_definitive_now` (re-read + `add_slot_candidate`'s own read) |
| R9 | never remove/replace an existing candidate or definitive | `test_generation_is_additive_and_skips_a_slot_that_is_definitive_now` |
| R10 | definitive at write time → skip the slot | same test (lunch keeps its definitive, no new candidate) |
| R11 | claim pending→running before invoking the provider | `test_a_lost_claim_invokes_no_provider_and_records_nothing`; `tests/contract/test_generation_result_sink_contract.py` (fake + sqs + planner_ai) |
| R12 | failed claim → no provider invocation | `test_a_lost_claim_invokes_no_provider_and_records_nothing` (`provider.calls == 0`) |
| R13 | already running/completed → no provider invocation | `test_a_redelivery_after_completion_invokes_no_provider` |
| R14 | record terminal status + each slot's outcome after all slots processed | `test_the_terminal_status_and_per_slot_payload_reach_the_record` |
| R15 | record only after every success is persisted | `test_record_result_runs_after_the_last_week_write` (`events == ["save","save","record"]`) |
| R16 | read the kill-switch before each provider invocation | `test_the_gate_is_read_before_every_slot` (`gate.reads == 2`) |
| R17 | disabled → no provider invocation | `test_a_disabled_gate_invokes_no_provider_and_marks_every_slot_unavailable` |
| R18 | disabled → record `AI_GENERATION_UNAVAILABLE` per unprocessed slot | same test (`[msg] * 2`, status `failed`) |
| R19 | kill-switch is one deployment-wide state | `core/tests/ports/test_ai_ports.py::test_the_generation_gate_takes_no_user_argument`; `tests/contract/test_generation_gate_contract.py` |
| R20 | no per-user generation counter/quota | `core/tests/test_no_generation_quota.py` (scans `week_generation.py` + `planner_ai/`) |
| R21 | attribute the candidate to the submitting user on the message | `test_a_provider_failure_on_one_slot_leaves_the_others_persisted` (`all(c.author == "u-1")`) |

Frozen-id chain: R1–R18 → `FR-AI-09` (`covers`); R16–R20 → `NFR-AI-01` (`covers`);
R21 → `FR-CAND-04` (cited, owned by feature 5). `covers` array unchanged.

## Files

**`planner_core`** (new)
- `ports/ai_provider.py` — `AiProvider` Protocol + `AiPrompt` alias + `AiProviderError`.
- `ports/generation_gate.py` — `GenerationGate` Protocol (`is_generation_enabled() -> bool`).
- `ports/generation_queue.py` — split out `GenerationResultSink` (claim +
  record_result); `GenerationQueue` now inherits it. The worker depends on the
  narrower `GenerationResultSink` so `planner_ai`'s adapter need not implement
  `submit` / `stored_generation` / `discard` (ISP; design says `queue:
  GenerationQueue`, this is a refinement).
- `application/week_generation.py` — `run_week_generation(...)` + frozen
  `WeekGenerationOutcome` / `SlotResult`.

**`planner_ai`** (all new except `pyproject.toml`, `__init__.py`)
- `adapters/dynamo/{_table,_meal,weeks}.py` — verbatim copy of the `planner_api`
  versions with imports retargeted (T13; drift caught by T21).
- `adapters/dynamo/generations.py` — `DynamoGenerationRecords` (`claim` /
  `record_result` on `PETICIONIA#<hash>/METADATA`).
- `adapters/bedrock.py` — `BedrockAiProvider`, `BEDROCK_MODEL_ID =
  "anthropic.claude-sonnet-5"`, `AI_MODEL_ID` env override, prompt→messages
  render, response→`RawRecipeOutput` parse, `AiProviderError` on failure.
- `adapters/ssm.py` — `SsmGenerationGate`, `/planner/<env>/ai-generation-enabled`,
  5 s in-process TTL cache, **fails closed** on a read error.
- `message.py` — `parse_message` (SQS body → `GenerationMessage`).
- `wiring.py` (frozen `Dependencies`), `handler.py` (per-record isolation).
- `pyproject.toml` — `boto3` runtime dep, `moto` dev group.

**Tests / scans**
- `core/tests/support/fakes.py` — `FakeAiProvider`, `FakeGenerationGate`;
  `FakeGenerationQueue` already had `claim` / `record_result` from Part 1.
- `core/tests/test_application_layering.py` — `BANNED_IMPORT` gains
  `bedrock` / `anthropic`; `week_generation` added to `USE_CASE_MODULES`.
- `core/tests/test_change_marker_is_not_a_write_condition.py` — the adapter
  exemption widens from one dir to `ADAPTERS_ROOTS` (api + ai), since the
  `planner_ai` week-adapter copy legitimately names `marcaCambio`.
- `core/tests/test_ports_are_storage_agnostic.py` — `ai_provider.py` /
  `generation_gate.py` added to `PORT_MODULES`.
- `core/tests/test_no_generation_quota.py` — new scan (R19, R20).
- `backend/tests/contract/` — `test_ai_provider_contract.py`,
  `test_generation_gate_contract.py`, `test_generation_result_sink_contract.py`;
  `test_week_repository_contract.py` parametrized over the `planner_ai` adapter
  too (T21); `dynamo_contract.py` gains the three planner_ai factories +
  `seed_ssm_parameter`.
- `lambda_ai/tests/` — `test_worker_handler.py`, `test_message.py`,
  `test_bedrock.py`, `test_wiring.py`, `test_write_path.py`.

## Mutation probes planted (and the test that kills each)

- `run_week_generation`: drop the `if not queue.claim(...)` guard → `test_a_lost_claim_invokes_no_provider_and_records_nothing`.
- Move `queue.record_result(...)` before the slot loop → `test_record_result_runs_after_the_last_week_write`.
- `not gate.is_generation_enabled()` → `gate.is_generation_enabled()` (invert) → `test_a_disabled_gate_invokes_no_provider...` + `test_the_gate_is_read_before_every_slot`.
- Skip the `definitive(current) is not None` check → `test_generation_is_additive_and_skips_a_slot_that_is_definitive_now`.
- `claim` `ConditionExpression` `estado = :pending` → drop it → `test_generation_result_sink_contract.py::test_the_first_claim_transitions_pending_and_a_second_fails` (moto).
- `SsmGenerationGate` fail-open (`enabled = True` in the `except`) → `test_generation_gate_contract.py::test_the_ssm_gate_fails_closed_when_the_parameter_is_absent`.

## Spec did not anticipate / deviations

- **`GenerationResultSink` split.** Design §3 types the worker param `queue:
  GenerationQueue`. `planner_ai` must not implement `submit` (it is the
  consumer, not a producer), so the port grew a `GenerationResultSink` base
  Protocol (claim + record_result) and the worker depends on that. `SsmGenerationGate`
  contract / drift tests use it.
- **`prompt_version_id` not decremented per slot.** The worker builds one
  `build_category_prompt(targets.remaining_category_counts, ...)` and reuses it
  for every open slot, exactly as design §3 states. It does not lower the
  remaining counts as slots fill — a known simplification carried from the
  design.
- **AiProvider contract "fake + moto" → "fake + stubbed client".** moto does not
  meaningfully mock `bedrock-runtime:InvokeModel`; the Bedrock adapter is tested
  with an injected stub client (recorded Anthropic-messages response), per
  design §12's "recorded fixture" wording. No live call in the gate.
- **Handler swallows per-record exceptions** (logs + continues). SQS
  retry / DLQ / partial-batch-response semantics are feature 21 (IaC); flagged
  for the reviewer.
- **`init.sh` §4** still red on the intentional dual `in_progress` (17 + 27) and
  the 16→27 dep order — expected for this bundle, clears on the owner's `done`
  marks.

## `./init.sh`

§5 green — ruff format / ruff check / mypy strict / **pytest 762 passed**
(694 baseline → 705 after the feature 27 delta → 762 after feature 17) /
prettier / eslint / vitest.

## Fix round 1 — 2026-09-06

Reviewer findings 1, 3, 5, 6 (+ shared 2/7). `./init.sh` §5 green — **769 passed**
(+7 net over 762). §4 still red only on the intentional dual `in_progress` (17 + 27).

| Finding | Files | Tests (all planted-mutant-killed) |
|---|---|---|
| 1 — un-enriched SQS message rejected, not silently emptied | `planner_ai/message.py` (`effectiveRules` via `_require`, `_parse_rules` no longer null-tolerant); `core/ports/generation_queue.py`, `planner_api/adapters/sqs.py`, `core/tests/support/fakes.py` (`submit`'s `effective_rules` now required, no default) | `lambda_ai/tests/test_message.py::test_a_message_with_no_effective_rules_key_is_rejected`, `::test_a_malformed_field_raises` (new `{"effectiveRules": None}` case); contract/port `submit` callers pass `effective_rules=RuleSet()` |
| 3 — R8/R10 real at-write re-check test | (test only) | `core/tests/application/test_week_generation.py::test_a_definitive_appearing_after_target_resolution_is_not_overwritten` — kills both `week_generation.py:106-107` mutants (stale-occupancy swap + neutered `definitive()` check) |
| 5 — `_render` covered | (test only) | `lambda_ai/tests/test_bedrock.py::test_render_carries_the_versioned_instructions_and_the_category_counts` — `_render` → `""` now fails |
| 6 — render template folded into the versioned block | `core/domain/ai_prompt.py` (`PromptInstructionsVersion` / `PromptInstructions` gain `json_output_instruction` + 5 `*_template` fields; `v1` populated with the **verbatim** current strings; `build_instructions` copies them); `planner_ai/adapters/bedrock.py` (`_render` a pure `string.Template` assembler, zero Spanish literals; `_JSON_INSTRUCTION` deleted) | `test_ai_prompt.py` field-shape + `build_instructions` tests extended (feature 24, green); `test_bedrock.py::test_render_carries_...`; `test_no_recipe_metadata_logic.py` — narrow sanctioned-line exemption for `JSON_OUTPUT_INSTRUCTION` (mirrors `CANDIDATE_SANCTIONED_LINES`) + `test_the_ai_prompt_sanctioned_lines_exist_verbatim` so a reword still forces a version bump |

**FR-AI-14 consumed-not-owned** (feature 24 `ai_prompt_versioning`): finding 6
edits `core/domain/ai_prompt.py`'s versioned model. `FR-AI-14` is **not** added
to feature 17's `covers` — the registry and its append-only rule stay feature
24's. `v1` gained fields, not a new key (relocation, not a wording change).

### Deviations / notes

- **Feature 25 metadata scan.** `JSON_OUTPUT_INSTRUCTION` names the model's
  output-schema keys (`servings`, `estimated_time`) as versioned prompt text.
  `test_no_recipe_metadata_logic.py` is a line-text scan of `planner_core`; it
  gained a two-line sanctioned exemption + a verbatim-existence guard. The
  scan's intent (no domain *logic* touches those fields) is intact. Flagged for
  the reviewer / owner in case the feature 25 spec doc should record it.
- **`string.Template`** (stdlib) is used in `bedrock.py::_render` for the
  versioned templates — `.format()`/`%` are banned by `conventions.md`, and a
  stored template needs *some* substitution mechanism; `${…}` also tolerates the
  literal `{…}` braces inside `JSON_OUTPUT_INSTRUCTION`.
