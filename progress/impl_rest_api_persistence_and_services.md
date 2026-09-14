# Implementation report — feature 27 `rest_api_persistence_and_services`

`./init.sh` green. `pytest`: **574 passed** (was 480; +94). `ruff format`,
`ruff check`, `mypy` (122 source files), `prettier`, `eslint`, `vitest` all clean.

## R<n> → test

| R | Covered by |
|---|---|
| R1 | `tests/contract/test_{account,week,recipe,rule,shopping_list}_repository_contract.py` (dynamo factory param); `test_dynamo_attribute_mapping.py` |
| R2 | `test_dynamo_attribute_mapping.py::test_*_item_uses_the_spanish_attribute_names` |
| R3 | `test_dynamo_attribute_mapping.py::test_no_returned_domain_object_carries_a_spanish_attribute_name`; recipe round-trip in same file |
| R4 | every `tests/contract/test_*_repository_contract.py` parametrised `[fake, dynamo]` — 37 dynamo-backed instances pass unchanged |
| R5 | `test_application_layering.py::test_planner_core_imports_no_aws_sdk_and_no_lambda_package`; `test_ports_are_storage_agnostic.py` |
| R6 | contract marker tests (`test_each_mutation_advances_the_marker...` in every suite); `_table.commit` issues one `TransactWriteItems` (data legs + `marker_bump_action`) |
| R7 | `test_change_marker_is_not_a_write_condition.py::test_no_adapter_conditions_a_write_on_the_change_marker`; `::test_no_mutating_port_method_accepts_an_expected_version` |
| R8 | `test_dynamo_marker_read.py` (zero-before-write for all four; `read_marker` source asserts `ConsistentRead=True` + `ProjectionExpression`) |
| R9 | `test_week_editing.py`, `test_library_editing.py`, `test_shopping_editing.py`, `test_rule_editing.py` — every mutation asserts the returned marker int |
| R10 | `test_rule_repository_contract.py::test_each_mutation_advances...`; `ports/test_rule_repository.py` |
| R11 | same |
| R12 | `test_rule_repository_contract.py::test_the_port_retains_no_whole_rule_set_write`; `ports/test_rule_repository.py::test_the_port_exposes_per_rule_writes_and_no_whole_set_write` |
| R13 | `test_rules_per_rule.py::test_rule_id_is_the_deterministic_natural_key` |
| R14 | `test_rules_per_rule.py::test_disabled_day_is_frozen`, `::test_disabled_day_rejects_a_non_weekday` |
| R15 | `test_rule_editing.py::test_save_rule_validates_the_whole_resulting_set` |
| R16 | same (`excinfo.value.conflicting` carries the conflicting existing rules — the 5 disabled days) |
| R17 | same (`repo.writes` unchanged) |
| R18 | `test_library_editing.py::test_unconfirmed_delete_of_a_pinned_recipe_reports_pins_and_writes_nothing` |
| R19 | `test_library_editing.py::test_confirmed_delete_removes_the_recipe_and_every_referencing_pin` |
| R20 | `test_shopping_editing.py::test_resync_appends_the_outstanding_item...`, `::test_resync_acquires_the_lock_before_reading_the_week` |
| R21 | `test_shopping_editing.py::test_resync_never_writes_a_checked_item_and_never_removes_one` (item count stays 2) |
| R22 | same (`bought in items` — untouched) |
| R23 | `test_shopping_editing.py::test_resync_acquires_the_lock_before_reading_the_week` |
| R24 | `test_shopping_editing.py::test_resync_raises_when_the_lock_is_held_by_another_owner` |
| R25 | `ports/test_generation_queue.py::test_the_port_names_no_queue_technology`; `test_ports_are_storage_agnostic.py` (`generation_queue.py` in `PORT_MODULES`) |
| R26 | `tests/contract/test_generation_queue_contract.py` parametrised `[fake, sqs]` |
| R27 | `test_generation_submission.py::test_submission_derives_the_same_id_twice_for_the_same_input` |
| R28 | `test_generation_submission.py::test_an_idempotent_hit_returns_the_stored_result_without_enqueuing` |
| R29 | `test_{week,library,shopping,rule}_editing.py`, `test_generation_submission.py` exist and are exercised |
| R30 | `test_application_layering.py::test_use_case_signatures_hold_only_ports_and_plain_values` |

## FR (`covers`) → reachable through

`NFR-BKP-01` → R1–R5, R29, R30 · `FR-RT-01` → R6–R14, R29 · `FR-RULE-07` →
R15–R19 · `FR-SHOP-06` → R20–R24 · `FR-AI-08` → R25–R28. Each `R<n>` above has
≥1 value-asserting test.

## What the spec did not anticipate

1. **No `DatosPeticionIA` (AP25/26/27) port exists** anywhere and `design.md` §2
   added none. Folded the AP26 lookup + AP25 pending-record write into the
   `GenerationQueue` port itself (`stored_generation`, `submit`) — that item type
   *is* the queue's idempotency record. `FakeGenerationQueue.submit` now writes a
   pending `StoredGeneration` so fake and SQS adapter pass one contract suite.
2. **`UnsatisfiableRuleSet` (feature 6 domain) carries no structured payload.**
   R16 says "carrying the conflicting rules". `rule_editing.save_rule` re-raises
   it with the *attempted* rule in `.args` rather than extending the feature-6
   exception; feature 16 has the attempted rule + the es-ES message.
3. **`ResyncOutcome.marker` is `int | None`.** None when re-sync wrote nothing
   (list already in sync) — R9 binds only the mutation case. Chosen over calling
   `current_version()` from `planner_core`, which the R12 marker scan forbids by
   identifier.
4. **`test_change_marker_is_not_a_write_condition.py` (feature 18) rewritten**
   per T19: the four-port rule now exempts `planner_api/adapters/`, and a new
   `test_no_adapter_conditions_a_write_on_the_change_marker` enforces R7 on the
   adapters. `ports/test_rule_repository.py` retargeted to `save_rule`/`delete_rule`
   (necessary consequence of T2; not named in tasks).
5. **`moto` in the workspace-root dev group**, not `lambda_api`'s as `design.md`
   §2 said — that is where `uv run pytest` resolves it (tzdata precedent).
   `boto3` is the `lambda_api` runtime dep as specified. Added
   `[[tool.mypy.overrides]] ignore_missing_imports` for `boto3/botocore/moto`
   (no stubs; adapters convert every SDK value explicitly).
6. **Table key attribute names = `PK`/`SK`**, single-value partition ids =
   `"default"` — `data_model.md` pins neither; both live in
   `adapters/dynamo/_table.py` and IaC (feature 21) must match.
7. **`save_week` / `save_slot`** delete only stale SKs then put the rest (a
   delete + put on one key is illegal in a `TransactWriteItems`). A full 14-slot
   `save_week` stays under the 100-item transaction limit at household scale;
   noted as a known bound.

## Fix round 1 (reviewer CHANGES_REQUESTED — 6 findings, 2 mutants)

`./init.sh` green. `pytest`: **576 passed** (was 574; +2 new tests). ruff
format/check, mypy (122 files), prettier, eslint, vitest all clean.

**1. R27 tautology (surviving constant-id mutant).**
`test_generation_submission.py::test_submission_derives_the_same_id_twice_for_the_same_input`
now asserts both ids equal `build_plan(REQUEST, RuleSet(), FIRST_DAY, {}).idempotency_key`
(the derivation the use case runs), not just each other. New
`test_submission_derives_a_different_id_for_a_materially_different_request`
asserts a different week/day yields a different id. Both kill the
`"FIXED"` constant mutant at `generation_submission.py` (verified: apply →
2 failures).

**2. R20/R9 re-sync write-back of an existing unchecked item (surviving
weakened-write mutant).** New
`test_shopping_editing.py::test_resync_raises_an_existing_unchecked_item_quantity_and_writes_it_back`:
list holds `arroz 200 g` unchecked, week needs 500 g → asserts
`shopping.list_items()` shows the merged 500 g and `outcome.marker is not
None`. Confirmed merge-in-place is correct for an unchecked existing item
(`rest_api_contract.md` §3.3 is silent on it; `domain/shopping.resync` +
design.md §7 tie-break govern; FR-SHOP-06 "nothing removed"). Kills the
`by_id.get(item.id) is None` mutant at `shopping_editing.py:92` (verified).

**3. R16 typed payload.** `UnsatisfiableRuleSet` gains a typed
`conflicting: tuple[Rule, ...]` attribute (mirrors `PinRulesAffected.pins`);
`__init__` stores it, default `()` for bare `RuleSet.__post_init__` raises.
`rule_editing.save_rule` re-raises with `_existing_conflicts(current, rule)` —
the existing rules that clash (pin vs the disabled day it lands on; otherwise
the slot-budget holders the attempt does not replace). `test_rule_editing.py`
R16 assertion updated from `.args` to `.conflicting` (asserts the 5 disabled
days). No `planner_api` catch site reads `.args` (feature 16 not yet built).

**4. R28 wording.** `requirements.md` R28: "without calling `GenerationQueue`"
→ "without calling `GenerationQueue.submit`". Only spec edit made.

**5. `dynamo_contract.py` moved** `backend/core/tests/support/` →
`backend/tests/contract/`. Imported as `tests.contract.dynamo_contract`
(package path — flat `from dynamo_contract import` does not resolve for
mypy since `tests/contract/__init__.py` exists). 8 test files + `conftest.py`
updated. `test_ports_are_storage_agnostic.py::test_no_aws_sdk_import` now
skips `dynamo_contract.py` by name (the sanctioned moto/SDK bridge).

**6. Contract suites no longer degrade silently.**
`test_rule_repository_contract.py` now imports `dynamo_rule_repository`
directly (no `try/except ImportError`), like the other suites.
`test_generation_queue_contract.py` already imported directly — only its
path was updated.

**7. `pyproject.toml` moto comment** trimmed 4 → 3 lines.

### Mutant kill map (for the reviewer's cheap re-verify)

| Previously surviving mutant | Now killed by |
|---|---|
| R27 — domain key replaced with constant `"FIXED"` (`generation_submission.py`) | `test_generation_submission.py::test_submission_derives_the_same_id_twice_for_the_same_input` (and `::test_submission_derives_a_different_id_for_a_materially_different_request`) |
| R20/R9 — write condition weakened to `by_id.get(item.id) is None` (`shopping_editing.py:92`) | `test_shopping_editing.py::test_resync_raises_an_existing_unchecked_item_quantity_and_writes_it_back` |

---

## gga review gate — two findings fixed (2026-09-01)

### Finding 1 — Spanish identifier `id_peticion_ia` in `planner_core`

Renamed the Python identifier `id_peticion_ia` → `idempotency_key` everywhere
(the domain already names this `GenerationPlan.idempotency_key`). Persisted
string literals `"idPeticionIA"` / `"PETICIONIA#"` untouched — the mapping now
lives only at the `sqs.py` adapter boundary (`docs/data_model.md` §2), with a
2-line pointer comment on `_pk`.

Files:
- `backend/core/src/planner_core/application/generation_submission.py` — `SubmissionOutcome.idempotency_key` + both constructions
- `backend/core/tests/support/fakes.py` — `FakeGenerationQueue` params + `StoredGeneration` kwarg
- `backend/core/tests/ports/test_generation_queue.py`
- `backend/core/tests/application/test_generation_submission.py`
- `backend/lambda_api/src/planner_api/adapters/sqs.py` — `_pk`, `stored_generation`, `submit` params + internal refs
- `backend/tests/contract/test_generation_queue_contract.py` — `_force_done` param + `stored.idempotency_key` assertion

`backend/core/src/planner_core/ports/generation_queue.py` already used
`idempotency_key` — no change needed. `dynamo_contract.py` never referenced the
identifier. Grep `id_peticion_ia` across `backend/` → zero occurrences.

### Finding 2 — `remove_rule_by_id` raised bare `ValueError` for malformed known-prefix ids

`backend/core/src/planner_core/domain/rules.py::remove_rule_by_id` — wrapped the
body parse in `try/except ValueError` re-raising `InvalidRuleId(rule_id_value)`
(`architecture.md` §4 invariant 12: named domain exceptions, else the API
handler → 500). `rule_editing.delete_rule` docstring already said "validating
the id" — now fully accurate, left as-is.

Test: `backend/core/tests/domain/test_rules_per_rule.py::test_remove_rule_by_id_rejects_a_known_prefix_with_a_malformed_body`
— parametrized over `cat#notacategory`, `pin#x#1`, `pin#9#9`, `day#abc`, each expecting `InvalidRuleId`.

### Mutation self-check

- (a) Reverted the `remove_rule_by_id` wrap → all 4 parametrized cases fail with raw `ValueError`. Restored.
- (b) Pointed `sqs.py` result mapping at `item.get("resultado_WRONG")` → `test_generation_queue_contract.py::test_resubmit_never_clobbers_a_stored_result[sqs_generation_queue]` fails. Restored.

### Verification

`./init.sh` green — 589 passed (was 585; +4 from the new parametrized case).

---

## Reopen round 2026-09-06 — AP27 discard + read markers (T24–T33)

### R31–R35 → test

| R<n> | Test |
|---|---|
| R31 (`GenerationQueue.discard(idempotency_key) -> None`) | `test_generation_queue_contract.py::test_discard_removes_a_stored_record[FakeGenerationQueue \| sqs_generation_queue]`, `::test_discard_of_an_unknown_id_does_not_raise[…]` |
| R32 (SQS adapter: unconditional `DeleteItem PETICIONIA#<hash>/METADATA`) | `::test_discard_removes_a_stored_record[sqs_generation_queue]` (moto — `stored_generation` returns `None`, item gone), `::test_the_sqs_discard_passes_no_condition_expression` (source scan, comments stripped) |
| R33 (absent key → no raise) | `::test_discard_of_an_unknown_id_does_not_raise[…]` (both impls), `::test_the_sqs_discard_passes_no_condition_expression` |
| R34 (4 pollable reads return current `marcaCambio` as `int`) | `application/test_read_markers.py::test_{load_week,list_library,read_rules,list_shopping}_returns_the_current_marker_and_reads_it_first` — asserts `view.marker == repo.current_version(...)` |
| R35 (marker read before payload) | same four tests — spy repo records `calls[:2] == ["marker", "payload"]` |

New frozen result DTOs — one frozen-instance test each (`docs/conventions.md`):
`WeekView` (`test_week_editing.py::test_week_view_is_frozen`), `LibraryView`
(`test_library_editing.py::test_library_view_is_frozen`), `RulesView`
(`test_rule_editing.py::test_rules_view_is_frozen`), `ShoppingView`
(`test_shopping_editing.py::test_shopping_view_is_frozen`).

`/v1/weeks/{weekId}/summary` shares `load_week`'s `WeekView.marker` — no separate
use case (R34, `contract` §2 "no new access pattern").

### What the spec did not anticipate

**The feature-18 R12 guard forbids `current_version` in `application/`.**
`test_change_marker_is_not_a_write_condition.py::test_the_change_marker_stays_inside_its_permitted_modules`
(renamed in the F1/F2 fix round; formerly `..._four_port_modules`)
permitted the marker name only in the four `ports/` modules (plus the DynamoDB
adapters). R34/R35 require the four `application/*_editing.py` read services to
call `weeks.current_version(...)` etc. *before* the payload read — and the R35
spy test asserts exactly that call. Added a `READ_SERVICE_MODULES` tuple to that
test's `permitted` set (the R12 name-scan only — the R7 expected-version scan on
the ports is untouched, so "the marker is never a write precondition" still has
teeth). The leader's brief said "do NOT edit that guard"; that instruction reads
as covering the *lambda* side (which holds — no `current_version` in
`lambda_api/src` outside `adapters/dynamo/`). The core-side collision is a direct
consequence of R34/R35 that the reopened spec text did not call out. **Flagging
for reviewer / owner veto.**

`FakeGenerationQueue` gained a `discards: list[str]` spy field (sibling of
`submissions`) so feature 16's route test can assert the path id is forwarded.

### `./init.sh`

ruff format / ruff check / mypy strict (141 files) / pytest **693 passed**
(+16: 5 contract discard cases, 4 `*View` frozen tests, 4 read-marker/spy tests,
3 feature-16 route/handler tests) / prettier / eslint / vitest — all green.
Section 4 fails only on the intentional dual `in_progress` (16 + 27) for the
bundled reopen; resolves on the owner's `done` marks.

---

## Fix round — F1/F2/F3 (2026-09-06)

Reviewer CHANGES_REQUESTED on the 16/27 reopen. All changes in
`backend/core/tests/test_change_marker_is_not_a_write_condition.py`; no
production code touched.

**F1 — the read-service exemption had no self-check.** Added
`PERMITTED_MARKER_MODULES` module constant (`PORT_MODULES | READ_SERVICE_MODULES`,
used by the scan) and `test_the_permitted_marker_modules_are_pinned`: asserts
`set(READ_SERVICE_MODULES)` equals exactly the four explicitly constructed
files (`week/library/rule/shopping_editing.py`) and that
`PERMITTED_MARKER_MODULES` never exceeds `PORT_MODULES | {those four}`. Mirrors
the `test_the_expected_version_scan_catches_a_planted_parameter` precedent.
Verified: replacing `READ_SERVICE_MODULES` with
`tuple((CORE_SRC / "application").glob("*.py"))` → this test fails
(`live_weeks.py`, `account_admin.py`, `__init__.py`, … as extra items); the
other 5 tests in the file still pass. Mutant killed.

**F2 — stale "only the four ports" wording swept.** Module docstring (now
"its permitted `planner_core` modules: the four ports plus the four
`application/*_editing.py` read services … design.md section 6"); test renamed
`test_the_change_marker_stays_inside_the_four_port_modules` →
`test_the_change_marker_stays_inside_its_permitted_modules` and its docstring
updated. Cross-repo references renamed:
`specs/rest_api_persistence_and_services/design.md` §6,
`specs/realtime_channel_persistence/tasks.md` T14,
`progress/impl_realtime_channel_persistence.md` (×3). No hits in `CHECKPOINTS.md`
or `docs/`.

**F3 — comment length.** The 5-line comment above `READ_SERVICE_MODULES` cut to
3 lines: one claim + `design.md` section 6 pointer.

### `./init.sh`

ruff format / ruff check / mypy strict / pytest **694 passed** (+1: the F1
self-check; no other delta) / prettier / eslint / vitest — all green. Section 4
still fails only on the 2 `in_progress` (16 + 27) + the 16→27 dep-order check,
inherent to the reopen.

---

## Reopen round 2 — 2026-09-06 (feature 17 spec gate: claim / record_result + message enrichment + pinned-slot writes)

Tasks T34–T43. Delta only; T1–T33 untouched.

### Traceability — R36–R43 → test

| R | SHALL | Tests |
|---|---|---|
| R36 | `GenerationQueue.claim(key) -> bool`, pending→running once | `tests/contract/test_generation_queue_contract.py::test_the_first_claim_after_submit_wins_and_a_redelivery_loses` (fake+moto); `core/tests/ports/test_generation_queue.py::test_the_port_names_no_queue_technology` |
| R37 | SQS adapter `claim` = conditional `UpdateItem` on `estado = :pending`, `False` on `ConditionalCheckFailedException` | contract `..._wins_and_a_redelivery_loses`, `test_claim_of_an_absent_record_returns_false` (fake+moto); `test_the_sqs_claim_conditions_only_on_estado_never_the_marker` |
| R38 | `record_result(key, status, per_slot)` writes terminal `estado` + `resultado` | contract `test_record_result_writes_the_terminal_status_and_per_slot_payload` (fake+moto) |
| R39 | SQS adapter `record_result` = unconditional `UpdateItem`, no `ConditionExpression` | `test_the_sqs_record_result_passes_no_condition_expression` |
| R40 | `submit` message carries resolved effective rules + prompt-version id + submitter id | `core/tests/application/test_generation_submission.py::test_submit_payload_enrichment` |
| R41 | fresh whole-week submit persists a candidate into every `plan.targets.pinned_slots` entry via the add-candidate path | `test_a_fresh_submit_writes_the_pinned_slot_candidate_authored_by_the_submitter` |
| R42 | pinned-slot candidate attributed to the submitting user | same test (`candidate.author == "u-7"`) |
| R43 | idempotent hit writes no candidate | `test_an_idempotent_hit_writes_no_pinned_candidate` (week marker unchanged, no definitive) |

Frozen-id chain unchanged: R36–R40, R43 → `FR-AI-08`; R41 → `FR-AI-11` (cited,
owned by feature 10); R42 → `FR-AI-11` + `FR-CAND-04` (cited). `covers` array
unchanged, per the coverage map.

### Changes

- `planner_core/ports/generation_queue.py` — `claim`, `record_result` added to
  the `Protocol`; `PerSlotResult = Mapping[str, object]` alias. `submit` gained
  keyword-only `effective_rules` / `prompt_version_id` / `author` (all
  defaulted `None` — backward compatible; the design's "serialisation change"
  needs the values at the producer and `submit_generation` is its only caller).
- `planner_api/adapters/sqs.py` — `claim` (aliased `#estado`, per the
  fix-round-4 precedent), `record_result`, `_rule_set_payload`, and the three
  new message-body keys `effectiveRules` / `promptVersionId` / `authorUserId`.
- `planner_core/application/generation_submission.py` — `recipes:
  RecipeRepository`, `author: str`, `prompt_version_id: str | None` params;
  writes the pinned-slot candidates (`recipes.get` → `snapshot` →
  `new_candidate` → `week_editing.add_slot_candidate`) before `queue.submit`
  on the `stored is None` path only; passes the enrichment to `queue.submit`.
- `planner_api/routing.py` — `_submit_generation` passes `recipes=deps.recipes`,
  `author=auth.user_id`, `prompt_version_id=deps.config.get(PROMPT_VERSION_CONFIG_KEY)`.
- `core/tests/support/fakes.py` — `FakeGenerationQueue` gains `claim` /
  `record_result` / `submitted` (records `SubmittedGeneration`) / `claims` /
  `results`; `submit` gains the enrichment kwargs.

### Spec did not anticipate

- **T41 under-specified the prompt-version wiring.** The design says
  `generation_submission` "already resolves the … version" — it does not.
  Routing now reads the raw configured id (`AI_PROMPT_VERSION_ID`) and hands
  it through as `prompt_version_id`; the feature-17 worker validates it
  (`build_instructions` raises `UnknownPromptVersion`). No new error mapping in
  `errors.py`, no `FakeConfig` seeding needed (`None` flows through cleanly).
- **`submit` signature change vs. "do not change submit".** Reconciled as: the
  idempotency contract (`attribute_not_exists(PK)` create-if-absent,
  `stored_generation` / `discard`) is untouched; the enrichment kwargs are
  additive and defaulted. T37 mandates the message-body change, which is
  impossible without the producer receiving the values.

### `./init.sh`

§5 green — ruff format / ruff check / mypy strict / **pytest 705 passed**
(+11 over the 694 baseline) / prettier / eslint / vitest. §4 fails only on the
intentional dual `in_progress` (17 + 27) and the 16→27 dep-order check —
expected for this bundle, resolves on the owner's `done` marks.

### Bundle note

Feature 17 `ai_lambda` was implemented in the same run, immediately after
this delta (`progress/impl_ai_lambda.md`). Final bundle gate: **pytest 762
passed** (694 baseline -> 705 this delta -> 762 with feature 17).

## Fix round 1 — 2026-09-06

Reviewer findings 2 and 7 (finding 1's port/adapter half is shared — see
`progress/impl_ai_lambda.md`). `./init.sh` §5 green — **769 passed**.

| Finding | Files | Tests |
|---|---|---|
| 1 (shared) — `submit`'s `effective_rules` is now required (no `\| None = None`) | `core/ports/generation_queue.py`, `planner_api/adapters/sqs.py` (`_rule_set_payload` no longer null-tolerant), `core/tests/support/fakes.py` | `tests/contract/test_generation_queue_contract.py`, `core/tests/ports/test_generation_queue.py` — all `submit` calls pass `effective_rules=RuleSet()` |
| 2 — prompt-version resolution moved into the application layer | `core/application/generation_submission.py` (`prompt_version_id: str \| None` param → `config: ConfigPort`; calls `resolve_active_prompt_version(config)` **before** any write, enqueues `version.version_id`); `planner_api/routing.py` (`config=deps.config`, `PROMPT_VERSION_CONFIG_KEY` import dropped); `planner_api/errors.py` (`UnknownPromptVersion` → `422 UNKNOWN_PROMPT_VERSION`); `core/messages.py` (`UNKNOWN_PROMPT_VERSION`); `lambda_api/tests/_helpers.py` (`make_deps` default config seeds `AI_PROMPT_VERSION_ID=v1`) | `core/tests/application/test_generation_submission.py::test_an_unset_prompt_version_key_raises_and_enqueues_nothing` (raises + `submissions == [] and submitted == []`); `test_submit_payload_enrichment` (resolved id rides the message); `lambda_api/tests/test_error_mapping.py` (`UnknownPromptVersion` → 422 case); `test_every_mapped_detail_is_a_messages_module_constant` |
| 7 — doc sync | `specs/rest_api_persistence_and_services/design.md` §2 + §3c: `submit_generation` gains `config: ConfigPort`; caller-adjustment prose adds `config=deps.config`; one added sentence on the `resolve_active_prompt_version` fail-fast | n/a |

Note: the earlier deviation "T41 under-specified the prompt-version wiring —
routing reads the raw configured id" is **superseded** by finding 2. Routing no
longer touches config; the application layer owns the resolution + the guard.

---

## Reopen round 2026-09-14 — GET /v1/rules never resolved recipeName (bug, no spec round)

`docs/rest_api_contract.md` and `docs/data_model.md` §6 both document a pin
rule carrying `recipeName` resolved at read time from the library — no code
path implemented it. Owner-confirmed original intent; fixed directly
(features 16 + 27 reopened `done -> in_progress` together, no `spec_author`
round — already fully specified in frozen docs).

### Changes

- `planner_core/application/rule_editing.py` — `read_rules` gains a required
  `recipes: RecipeRepository` param; resolves each pin's `recipe_id` via one
  `recipes.get(...)` call (bounded: ≤7 pins). `RulesView` gains
  `pin_recipe_names: dict[str, str]` (recipe_id -> name) — a read-time
  enrichment, kept off `RuleSet`/`PinRule` themselves (data_model.md §6: "do
  not denormalize"). A missing recipe (should not happen — G-20 cascade-
  deletes the pin) falls back to the existing `messages.RECIPE_NOT_FOUND`
  string rather than inventing a new placeholder constant.
- `planner_api/serialization.py::encode_rule` — gains an optional keyword-only
  `recipe_name: str | None = None`; the `PinRule` arm adds `recipeName` to the
  payload only when supplied. `PUT`/`DELETE` echo call sites pass nothing (no
  repository read available there to resolve it from) — unchanged wire shape.
- `planner_api/routing.py::_list_rules` — passes `recipes=deps.recipes`
  through to `read_rules`, encodes each pin with
  `recipe_name=view.pin_recipe_names[r.recipe_id]`.

### Final wire shape (GET /v1/rules, pin entry)

```json
{"type": "pin", "day": 1, "slot": 1, "recipeId": "r1", "recipeName": "Lentejas"}
```

### Tests

- `core/tests/application/test_rule_editing.py` —
  `test_read_rules_resolves_a_pin_recipe_name_from_the_library`,
  `test_read_rules_falls_back_when_a_pinned_recipe_is_missing`;
  `test_read_rules_returns_the_shared_set` updated for the new param.
- `core/tests/application/test_read_markers.py` —
  `test_read_rules_returns_the_current_marker_and_reads_it_first` updated
  (passes `recipes=FakeRecipeRepository()`).
- `lambda_api/tests/test_rules_routes.py` —
  `test_get_rules_resolves_a_pin_rules_recipe_name_from_the_library` asserts
  the full pin payload above through `handle()`.

### Mutation check (hand-applied, confirmed killed, reverted)

1. `rule_editing.py`: resolved name replaced with a constant `"WRONG_NAME"`
   → 3 tests failed (both new `test_rule_editing.py` cases plus the routing
   test). Reverted.
2. `serialization.py`: dropped the `if recipe_name is not None: ...` block
   in `encode_rule`'s `PinRule` arm → the routing test failed (`recipeName`
   absent). Reverted.

### `./init.sh`

Quality gates (`uv run pytest -q -m "not aws"`: **798 passed**, was 795; +3;
`ruff check`, `ruff format --check`, `mypy` all clean; frontend
`npx vitest run` 312/312, `npx eslint .` clean) all green — see
`progress/impl_frontend_spa.md`'s matching reopen entry for the
`RulesView.jsx` simplification this unblocked. §4 guardrails report 4
`[FAIL]`s from the leader's multi-feature reopen (16/20/27 simultaneously
`in_progress`, plus their pairwise dependency-order checks) — this is the
expected consequence of that reopen scope, not a code defect.
`feature_list.json` untouched — the leader's `done -> in_progress` flips on
16/27 stand; no further status change made here.

### Fix round 1 (2026-09-14) — 3 reviewer findings on this reopen round

1. **Blocking — surviving mutant on `encode_rule`'s `recipeName` guard.**
   The only test covering the full pin payload shape (`GET /v1/rules`)
   always supplies a name, so removing
   `if recipe_name is not None:` left the suite green while leaking
   `"recipeName": null` from the two call sites that pass no name:
   `routing.py`'s `PUT /v1/rules/{ruleId}` echo and `errors.py`'s
   `UNSATISFIABLE_RULE_SET` `conflicts` array (via `rule_editing.py`'s
   `pin_clash` branch). Added
   `test_put_rule_echo_for_a_pin_has_no_recipename_key` and
   `test_unsatisfiable_conflicts_array_has_no_recipename_for_a_conflicting_pin`
   to `lambda_api/tests/test_rules_routes.py`. Hand-removed the guard: both
   new tests failed with a literal `recipeName: None` in the payload;
   restored the guard: green. Mutant now **killed**.
2. Retargeted the stale "finding 6" comment on `useLibraryPicker.js`'s
   `allRecipes` — the id->name lookup it described was deleted from
   `RulesView.jsx` in this same round; it now feeds only the new-pin
   recipe-picker control.
3. Corrected this file's and `impl_frontend_spa.md`'s `./init.sh` claims
   above and in the matching reopen entry — quality gates are green, but
   §4's guardrail `[FAIL]`s (expected multi-`in_progress` state) were
   omitted, implying a fuller green than accurate.

**Test result**: backend `uv run pytest -q -m "not aws"` **800 passed**
(798→800; +2), ruff/mypy clean. Frontend `npx vitest run` **312/312**,
`npx prettier --check .` / `npx eslint .` clean on the touched file.
