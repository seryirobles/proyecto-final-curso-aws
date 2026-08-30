# impl — realtime_channel_persistence (feature 18)

`docs/verification.md` Level 3. Spec: `specs/realtime_channel_persistence/`.
All `R<n>` cite `FR-RT-01`.

## Quality gates (from `backend/`)

| Gate | Result |
|---|---|
| `uv run ruff format --check .` | 94 files formatted |
| `uv run ruff check .` | All checks passed |
| `uv run mypy .` | Success, 94 files, no new `# type: ignore` |
| `uv run pytest -q` | 480 passed (was 441; +39 tests) |
| `./init.sh` | `[OK] Environment ready` |

> Fix pass 2026-08-30 (reviewer `CHANGES_REQUESTED`, 2 surviving mutants):
> added a `widened_read` fixture to the R7 scan self-test, and a
> `test_the_<port>_repository_protocol_pins_the_marker_surface` to each of the
> four `tests/ports/test_*.py` (pins `current_version` and the `-> int` returns
> on the Protocol, not just the fake). Port docstrings trimmed to the 3-line
> ceiling. Both mutants now killed — see the Level 5 table.

## R → test (forward)

| R | Statement (short) | Test(s) |
|---|---|---|
| R1 | `current_version` exists on all four ports | `tests/ports/test_{weeks,recipes,rule_repository,shopping_list}.py::test_the_<port>_repository_protocol_pins_the_marker_surface` (asserts on the Protocol itself: `current_version` declared + every mutating method returns `int`); plus `::test_fake_*_satisfies_the_*_port` and the per-port `::test_save_*_advances_...` for the fake side |
| R2 | reads leave the marker unchanged | `tests/ports/test_weeks.py::test_reads_do_not_advance_the_marker`; `test_recipes.py::test_reads_do_not_advance_the_marker`; `test_rule_repository.py::test_get_does_not_advance_the_marker`; `test_shopping_list.py::test_reads_do_not_advance_the_marker`, `::test_lock_operations_do_not_advance_the_marker`; contract `test_*_repository_contract.py::test_reads_leave_the_marker_unchanged` (×4) |
| R3 | baseline `0` for a never-written resource | `tests/ports/test_weeks.py::test_current_version_is_zero_for_a_week_never_written`, `::test_two_weeks_carry_independent_markers`; `test_recipes.py::test_current_version_is_zero_before_any_write`; `test_rule_repository.py::test_current_version_is_zero_before_any_write`; `test_shopping_list.py::test_current_version_is_zero_before_any_write` |
| R4 | mutating op returns the marker as advanced by it (== next read) | `tests/ports/test_weeks.py::test_save_slot_advances_...`, `::test_save_week_advances_...`; `test_recipes.py::test_save_and_delete_advance_...`; `test_rule_repository.py::test_save_advances_...`; `test_shopping_list.py::test_save_item_and_delete_item_advance_...`; contract `::test_every_mutating_method_advances_the_marker_and_returns_the_new_value` (weeks/recipes/shopping) + `test_rule_repository_contract.py::test_save_advances_the_marker_and_returns_the_new_value` |
| R5 | mutating op advances the marker in the same operation | same tests as R4, plus `test_shopping_list.py::test_delete_checked_items_advances_the_marker_when_it_removes_an_item` |
| R6 | no operation advances the marker without the data write it marks | `test_shopping_list.py::test_delete_checked_items_with_nothing_checked_returns_the_marker_without_advancing` (a bump-capable op that performs no write does not bump); all four `test_reads_do_not_advance_the_marker` / `test_get_does_not_advance_the_marker` (`current_version` never bumps); port surface is closed — `test_fake_*_satisfies_the_*_port` |
| R7 | no mutating op accepts a caller-supplied expected marker | `tests/test_change_marker_is_not_a_write_condition.py::test_no_mutating_port_method_accepts_an_expected_version`, `::test_the_expected_version_scan_catches_a_planted_parameter` (planted-mutant self-test) |
| R8 | two successive writes to one resource — second applies, no conflict | contract `test_*_repository_contract.py::test_two_successive_writes_both_apply_and_advance_the_marker_twice` (×4); `tests/ports/test_weeks.py::test_two_weeks_carry_independent_markers` shows independence |
| R9 | `delete_checked_items` with nothing checked leaves the marker unchanged | `tests/ports/test_shopping_list.py::test_delete_checked_items_with_nothing_checked_returns_the_marker_without_advancing` (runs it twice — Level 4 idempotency); contract `test_shopping_list_repository_contract.py::test_delete_checked_items_with_nothing_checked_does_not_advance_the_marker` |
| R10 | in-memory impl of each port maintains the marker as an incrementing counter | `tests/ports/test_*` marker tests all run against `Fake*Repository`; `test_fake_*_satisfies_the_*_port` (×4); contract suites parametrized over `IMPLEMENTATIONS = [Fake*Repository]` |
| R11 | composed single-item ops advance the marker once per op | contract `::test_two_successive_writes_both_apply_and_advance_the_marker_twice` (×4, asserts `(1, 2)`); contract shopping `::test_every_mutating_method_advances_...` walks save→save→delete→delete_checked as `1,2,3,4` |
| R12 | marker not referenced outside `planner_core.ports` + test fakes | `tests/test_change_marker_is_not_a_write_condition.py::test_the_change_marker_stays_inside_the_four_port_modules`, `::test_the_marker_name_pattern_detects_what_it_claims_to` (pattern self-test) |

## test → R (reverse)

| Test module | Tests | R |
|---|---|---|
| `backend/core/tests/ports/test_weeks.py` | `test_the_week_repository_protocol_pins_the_marker_surface` | R1 |
| | `test_current_version_is_zero_for_a_week_never_written` | R3 |
| | `test_save_slot_advances_the_marker_and_returns_the_new_value` | R1, R4, R5 |
| | `test_save_week_advances_the_marker_and_returns_the_new_value` | R1, R4, R5 |
| | `test_reads_do_not_advance_the_marker` | R2, R6 |
| | `test_two_weeks_carry_independent_markers` | R3, R8 |
| | `test_fake_week_repository_satisfies_the_week_repository_port` (existing) | R1, R10 |
| `backend/core/tests/ports/test_recipes.py` | `test_the_recipe_repository_protocol_pins_the_marker_surface` | R1 |
| | `test_current_version_is_zero_before_any_write` | R3 |
| | `test_save_and_delete_advance_the_marker_and_return_the_new_value` | R1, R4, R5 |
| | `test_reads_do_not_advance_the_marker` | R2, R6 |
| | `test_delete_raises_recipe_not_found_for_a_missing_id` (existing) | failure path (CHECKPOINTS C4) |
| | `test_fake_recipe_repository_satisfies_the_recipe_repository_port` (existing) | R1, R10 |
| `backend/core/tests/ports/test_rule_repository.py` | `test_the_rule_repository_protocol_pins_the_marker_surface` | R1 |
| | `test_current_version_is_zero_before_any_write` | R3 |
| | `test_save_advances_the_marker_and_returns_the_new_value` | R1, R4, R5 |
| | `test_get_does_not_advance_the_marker` | R2, R6 |
| | `test_fake_rule_repository_satisfies_the_rule_repository_port` (existing) | R1, R10 |
| `backend/core/tests/ports/test_shopping_list.py` | `test_the_shopping_list_repository_protocol_pins_the_marker_surface` | R1 |
| | `test_current_version_is_zero_before_any_write` | R3 |
| | `test_save_item_and_delete_item_advance_the_marker_and_return_the_new_value` | R1, R4, R5 |
| | `test_reads_do_not_advance_the_marker` | R2, R6 |
| | `test_delete_checked_items_with_nothing_checked_returns_the_marker_without_advancing` | R6, R9, Level 4 idempotency |
| | `test_delete_checked_items_advances_the_marker_when_it_removes_an_item` | R5 |
| | `test_delete_checked_items_leaves_an_unchecked_item_byte_for_byte_untouched` | Level 4 "never undo the user's reality" |
| | `test_lock_operations_do_not_advance_the_marker` | R2 |
| | `test_delete_item_raises_shopping_item_not_found_for_a_missing_id` (existing) | failure path (CHECKPOINTS C4) |
| | `test_fake_shopping_list_repository_satisfies_the_port` (existing) | R1, R10 |
| `backend/core/tests/test_change_marker_is_not_a_write_condition.py` | `test_the_expected_version_scan_catches_a_planted_parameter` | R7 (self-test) |
| | `test_no_mutating_port_method_accepts_an_expected_version` | R7 |
| | `test_the_marker_name_pattern_detects_what_it_claims_to` | R12 (self-test) |
| | `test_the_change_marker_stays_inside_the_four_port_modules` | R12 |
| `backend/tests/contract/test_week_repository_contract.py` | `test_every_mutating_method_advances_the_marker_and_returns_the_new_value` | R4, R5 |
| | `test_reads_leave_the_marker_unchanged` | R2 |
| | `test_two_successive_writes_both_apply_and_advance_the_marker_twice` | R8, R11 |
| `backend/tests/contract/test_recipe_repository_contract.py` | `test_every_mutating_method_advances_the_marker_and_returns_the_new_value` | R4, R5 |
| | `test_reads_leave_the_marker_unchanged` | R2 |
| | `test_two_successive_writes_both_apply_and_advance_the_marker_twice` | R8, R11 |
| `backend/tests/contract/test_rule_repository_contract.py` | `test_save_advances_the_marker_and_returns_the_new_value` | R4, R5 |
| | `test_reads_leave_the_marker_unchanged` | R2 |
| | `test_two_successive_writes_both_apply_and_advance_the_marker_twice` | R8, R11 |
| `backend/tests/contract/test_shopping_list_repository_contract.py` | `test_every_mutating_method_advances_the_marker_and_returns_the_new_value` | R4, R5, R11 |
| | `test_reads_leave_the_marker_unchanged` | R2 |
| | `test_two_successive_writes_both_apply_and_advance_the_marker_twice` | R8, R11 |
| | `test_delete_checked_items_with_nothing_checked_does_not_advance_the_marker` | R9 |

`FR-RT-01` → all of R1–R12 (see `requirements.md` coverage map). Traceable
both directions with no gap.

## Acceptance criteria → tasks

| `feature_list.json` acceptance criterion | Tasks | R |
|---|---|---|
| `MarcaCambio` item type, one instance per pollable partition | T1–T4 (port amendments), T5–T8 (one counter per fake) | R1, R3 |
| Each port gains a `current_version` read (AP29 shape, cheap/strongly-consistent/marker-only) | T1–T4 (method + docstring contract), T9–T12, T15 | R1, R2 |
| Every mutating method returns the new version, bumps inside the same op, never before/separate | T1–T4 (`-> int` + docstrings), T5–T8 (bump in method body), T9–T12, T15 | R4, R5, R6 |
| Marker never a write precondition — scan test enforced | T13 | R7, R8 |
| Fakes implement the bump with an in-memory counter | T5–T8 | R10 |
| Contract suites: mutating changes it / reads don't / write's return == next read / `delete_checked_items` no-op doesn't bump | T15 | R2, R4, R5, R9 |
| No handler / wiring / HTTP — pure `planner_core` + contract tests | T14 | R12 |
| Bulk op bumping once per item write accepted; collapse out of scope | T15 (`::test_two_successive_writes...`) | R11 |

## Level 5 — planted mutant → killing test (`design.md` §8)

| Mutant | Killed by |
|---|---|
| Drop the bump in a mutating method (e.g. `save_item` no longer `+= 1`) | `tests/ports/test_shopping_list.py::test_save_item_and_delete_item_advance_the_marker_and_return_the_new_value` (asserts `== 1`); per-port equivalents for weeks/recipes/rules; contract `::test_every_mutating_method_advances_the_marker_and_returns_the_new_value` |
| Bump on a `delete_checked_items` no-op (bump unconditionally) | `tests/ports/test_shopping_list.py::test_delete_checked_items_with_nothing_checked_returns_the_marker_without_advancing`; contract `test_shopping_list_repository_contract.py::test_delete_checked_items_with_nothing_checked_does_not_advance_the_marker` |
| Make `current_version` bump (read advances the marker) | `tests/ports/test_weeks.py::test_reads_do_not_advance_the_marker` and the three other ports' read-no-advance tests; contract `::test_reads_leave_the_marker_unchanged` |
| Return a stale value from a write (`return self.version - 1`, or return before the bump) | `test_save_*_advances_...` assert both the exact returned value and `returned == current_version()`; contract `::test_every_mutating_method_advances_the_marker_and_returns_the_new_value` asserts exact equality |
| Widen the R7 scan's own `current_version` exemption (`- {"week"}` → `- {"week", "expected_version"}`) | `tests/test_change_marker_is_not_a_write_condition.py::test_the_expected_version_scan_catches_a_planted_parameter` — the `widened_read` fixture (`current_version(self, week, expected_version)`) must be flagged (fix pass, 2026-08-30) |
| Widen the R7 denylist / drop a real port's expected-version guard | `tests/test_change_marker_is_not_a_write_condition.py::test_no_mutating_port_method_accepts_an_expected_version` + the `mutant` fixture in `::test_the_expected_version_scan_catches_a_planted_parameter` |
| Delete `current_version` from a port Protocol (fake keeps it — `pytest` and `mypy` both stay green otherwise) | `tests/ports/test_<port>.py::test_the_<port>_repository_protocol_pins_the_marker_surface` — asserts `"current_version" in <Protocol>.__dict__` (fix pass, 2026-08-30) |
| Revert a mutating method's `-> int` to `-> None` on a port Protocol | same `::test_the_<port>_repository_protocol_pins_the_marker_surface` — asserts `get_type_hints(<Protocol>.<method>)["return"] is int` (fix pass, 2026-08-30) |
| Reference the marker outside the four port modules | `tests/test_change_marker_is_not_a_write_condition.py::test_the_change_marker_stays_inside_the_four_port_modules` |

## Notes — what the spec did not anticipate

1. **`feature_list.json` was still `spec_ready`, not `in_progress`.** The
   leader launched implementation after explicit owner approval
   (`progress/current.md` log, 2026-08-30) but did not flip the status.
   Set it to `in_progress` per the SDD lifecycle; recorded in
   `progress/current.md`. No spec deviation.
2. **`_marker_hits` returns `(Path, detail)` tuples, not `"path:line"`
   strings** (unlike `test_no_ambient_time.py::_offenders`). A Windows drive
   letter (`C:`) makes `str.split(":")` unsafe for path recovery; carrying
   the `Path` object avoids it. Same discipline, safer plumbing.
3. **`delete_checked_items` no-op detection uses a length comparison**
   (`len(survivors) != len(self.items)`) rather than re-scanning for checked
   items — one pass, and it is exactly "removed ≥ 1 item" (R9, `design.md`
   §4).
4. **Protocol pinning uses `<Protocol>.__dict__`, not `__protocol_attrs__`.**
   `typing.Protocol` sets `__protocol_attrs__` at runtime but mypy does not
   know it (`attr-defined`), and `getattr(P, "__protocol_attrs__")` trips
   ruff `B009`. `"current_version" in P.__dict__` is both clean and exact —
   a member deleted from the Protocol body leaves `__dict__`.
5. **The design's scan (`design.md` §6) needed a `current_version`-widening
   self-test the spec did not list.** The original self-test only planted a
   bad mutating-method parameter, so loosening the scan's own
   `set(params) - {"week"}` exemption survived. `widened_read` closes it.
