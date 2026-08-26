# persistence_ports — Implementation report

Feature 14, tier 2, `sdd: true`. Covers `NFR-BKP-01` only. All 30 tasks in
`specs/persistence_ports/tasks.md` ticked. `./init.sh` green: **385 tests**
(up from 295 before this feature, 383 before this fix pass).

## Fix pass (reviewer CHANGES_REQUESTED, 2 findings)

1. **Lock-expiry boundary** (`fakes.py:206`'s `>=` vs `>`): added
   `test_acquire_lock_raises_at_the_exact_expiry_instant` to both
   `core/tests/ports/test_shopping_list.py` and
   `backend/tests/contract/test_shopping_list_repository_contract.py`.
   Verified by planting the `>=` → `>` mutant: both new tests failed;
   reverted after confirming.
2. **Storage-agnosticism scan allowlist hole**
   (`test_ports_are_storage_agnostic.py`): added `DENYLIST_STORAGE_MODULES`
   (`sqlite3`, `dbm`, `shelve`) checked independently of stdlib membership,
   and narrowed the `planner_core` allowance to `planner_core.domain.*` /
   `planner_core.ports.*` only (bare `planner_core` and
   `planner_core.application.*` now rejected) — required tracking full
   dotted import paths (`_imported_module_names`), not just the top-level
   segment, since `planner_core.application` and `planner_core.domain` share
   the same root. Verified with three planted mutants, all caught, all
   reverted: `import sqlite3` into `ports/rules.py`, `import
   planner_core.application` into `ports/rules.py`, and the regression
   check `import pytest` into `ports/weeks.py`.

## Traceability — R<n> → test

| R<n> | FR/NFR | Test(s) |
|---|---|---|
| R1 | NFR-BKP-01 | `core/tests/ports/test_accounts.py::test_account_record_is_frozen`, `::test_fake_account_repository_satisfies_the_account_repository_port`, `::test_create_then_get_by_id_and_get_by_username_round_trip_with_fold`, `::test_list_all_returns_every_account`, plus the contract mirror `tests/contract/test_account_repository_contract.py` (6 tests, parametrized over `IMPLEMENTATIONS`) |
| R2 | NFR-BKP-01 | `core/tests/ports/test_recipes.py::test_library_recipe_is_frozen`, `::test_fake_recipe_repository_satisfies_the_recipe_repository_port`, `::test_save_then_get_and_list_round_trip`, `::test_save_overwrites_by_id`; contract mirror `tests/contract/test_recipe_repository_contract.py` (3 tests) |
| R3 | NFR-BKP-01 | `core/tests/ports/test_weeks.py::test_fake_week_repository_satisfies_the_week_repository_port`, `::test_get_week_returns_an_empty_mapping_for_an_unwritten_week`, `::test_save_slot_round_trip`, `::test_save_week_overwrites_every_slot_at_once`; contract mirror `tests/contract/test_week_repository_contract.py` (3 tests) |
| R4 | NFR-BKP-01 | `core/tests/ports/test_rule_repository.py::test_fake_rule_repository_satisfies_the_rule_repository_port`, `::test_get_returns_an_empty_rule_set_before_any_save`, `::test_save_then_get_round_trip`; contract mirror `tests/contract/test_rule_repository_contract.py` (2 tests) |
| R5 | NFR-BKP-01 | `core/tests/ports/test_shopping_list.py` (9 tests: conformance, round trip, `delete_checked_items` no-op/removal, lock raise/expire/release); contract mirror `tests/contract/test_shopping_list_repository_contract.py` (4 tests) |
| R6 | NFR-BKP-01 | `core/tests/ports/test_archive.py::test_fake_archive_repository_satisfies_the_archive_repository_port`, `::test_get_returns_none_when_absent`, `::test_save_then_get_round_trip`, `::test_save_is_idempotent_when_re_saving_an_equal_archived_week`; contract mirror `tests/contract/test_archive_repository_contract.py` (2 tests) |
| R7 | NFR-BKP-01 | `core/tests/test_ports_are_storage_agnostic.py::test_port_signatures_use_only_domain_and_stdlib_types` (mechanical import-allowlist scan of all 6 port modules, now with a stdlib-storage denylist and a narrowed `planner_core.domain`/`planner_core.ports`-only allowance), plus its own self-check `::test_the_aws_sdk_pattern_detects_what_it_claims_to` for the sibling scan below |
| R8 | NFR-BKP-01 | All six `Fake*Repository` classes satisfy their `Protocol` via `isinstance(...)` in every `test_fake_*_satisfies_the_*_port` test above; composition proven end-to-end by `core/tests/application/test_persistence_fakes_compose.py::test_fakes_compose_from_account_through_recipe_week_and_shopping_list` |
| R9 | NFR-BKP-01 | All six `tests/contract/test_*_repository_contract.py` files: every test is `@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)`, executed once per registered implementation (today: the fake only) |
| R10 | NFR-BKP-01 | `core/tests/test_ports_are_storage_agnostic.py::test_no_aws_sdk_import` (scans the 6 port modules, `fakes.py`, and every file under `backend/tests/contract/`) |

## feature_list.json acceptance criteria

| Criterion | Satisfied by |
|---|---|
| "Ports are `typing.Protocol` definitions in `planner_core.ports` with no storage technology leaking into their signatures" | T1–T6 (ports), T21 (R7 mechanical scan) |
| "In-memory fakes in `core/tests/support` implement every port and are used by application-layer tests" | T7–T12 (fakes), T22 (`test_persistence_fakes_compose.py`) |
| "A contract suite in `backend/tests/contract` exercises each port and is parametrized to run against any implementation (fake now, real adapter later)" | T23 (conftest wiring), T24–T29 (6 contract suites) |
| "No AWS SDK import anywhere in this feature" | T21 (R10 mechanical scan) |

## What the spec did not anticipate

1. **Basename collision**: the task's file name `test_rules.py` (mirroring the
   `RuleRepository` port module) collides under pytest's prepend import mode
   with the pre-existing `core/tests/domain/test_rules.py` (feature 6). Ticked
   as `test_rule_repository.py` instead — `tasks.md` T18 annotated with the
   reason.
2. **mypy duplicate-module error**: adding a second `conftest.py`
   (`backend/tests/contract/conftest.py`) alongside the existing
   `backend/core/tests/conftest.py` made mypy report `Duplicate module named
   "conftest"` — neither tree had package structure to disambiguate them.
   Fixed with two empty package markers, `backend/tests/__init__.py` and
   `backend/tests/contract/__init__.py`, giving mypy a distinct dotted name
   for the new tree without touching `core/tests/` at all. No `pyproject.toml`
   change; no adapter or dependency added.
3. Removed the placeholder `backend/tests/contract/.gitkeep`, superseded by
   real content.

## Boundary checks

- No `pyproject.toml` touched anywhere; `planner-core` still `dependencies = []`.
- No `boto3`/AWS SDK import (T21 proves it mechanically).
- No frozen doc touched.
- No architecture §2 (P2–P6) decision made — `AccountRepository`'s shape was
  already accepted by the human at the design gate (design.md §11.1).
