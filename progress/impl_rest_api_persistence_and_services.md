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
