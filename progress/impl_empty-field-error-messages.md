# empty-field-error-messages — implementation report

## Summary

Root cause per `issues/empty-field-error-messages/analysis.md`: no decoder on
the recipe/shopping write path distinguished "this field is empty" from "this
value is wrong". An empty `unit`/`category` fell through to `parse_unit`/
`parse_category` and reported that value's own rejection message; empty
`name`/tool/step rows were silently stored; a blank `quantity` raised an
uncaught `ValueError`/`TypeError` that escaped to a generic `500`.

## Fix

One layer, per `plan.md` § *Fix design* (`lambda_api` wire boundary + the
`core` message text); no `parse_unit`/`parse_category` change (E9), no
`quantity > 0` rule (issue 7's bound, left untouched), no empty-list rule
(issue 8), no `servings`/`estimatedTime` change (issue 4, `G-85`).

**Real design deviation from `plan.md`, disclosed here — not an authority
overreach, no architecture decision, no frozen doc touched:** the plan called
for "one `_TABLE` row … detail from the exception" (a single `EmptyField`
exception with a per-instance dynamic detail resolved via a new callable on
`_ErrorSpec.message`). Implementing that literally broke a live, pre-existing
guard test the plan didn't examine — `lambda_api/tests/
test_error_mapping.py::test_every_mapped_detail_is_a_messages_module_constant`
(R17: "the table never composes its own string; every `message` value is one
of `planner_core.messages`' own constants", also stated in
`docs/rest_api_contract.md` §4: "`detail` is copied from `planner_core.
messages`, never composed in the handler"). I did not edit or weaken that
test. Instead I used **one exception subclass per field** — the same shape
this codebase already uses for `RecipeNotFound`/`CandidateNotFound`/
`ShoppingItemNotFound` — each mapped to its own static `messages.py`
constant. External contract (status, `code`, `detail` text per field) is
identical to what `plan.md`/the staged tests specify; only the internal
Python shape differs (7 `_TABLE` rows instead of 1, no `_ErrorSpec`/
`build_problem_response` mechanism change at all).

**Second, smaller deviation, same reason:** the natural name `EmptyUnit`
trips `core/tests/test_shared_kernel_guards.py::
test_planner_core_has_one_unit_vocabulary` (R16, a real anti-second-vocabulary
scan matching `class\s+\w*Unit\w*\b`) — a false positive, not a vocabulary
class, but I did not touch that guard either. Renamed to `EmptyMeasure`,
documented inline why.

| File | Layer | Change |
|---|---|---|
| `backend/core/src/planner_core/messages.py` | core | 7 new es-ES constants: `EMPTY_NAME`, `EMPTY_CATEGORY`, `EMPTY_INGREDIENT_NAME`, `EMPTY_QUANTITY`, `EMPTY_UNIT`, `EMPTY_TOOL`, `EMPTY_PROCEDURE_STEP`. |
| `backend/core/src/planner_core/domain/errors.py` | core/domain | `EmptyField(PlannerError)` base + 7 subclasses (`EmptyName`, `EmptyCategory`, `EmptyIngredientName`, `EmptyQuantity`, `EmptyMeasure`, `EmptyTool`, `EmptyProcedureStep`), no constructor args — the field is encoded in the type, not carried as data. |
| `backend/lambda_api/src/planner_api/serialization.py` | lambda_api | New `require_non_empty(value, field)`: `None` or a whitespace-only string raises the matching `Empty*` exception; anything else passes through unchanged. Applied in `decode_recipe` (name, category, each tool, each procedure entry — **before** `parse_category`), `decode_ingredient` (name, quantity, unit — **before** `float`/`parse_unit`), and `decode_shopping_item` (name, unit only — `quantity`'s bound stays issue 7's, untouched, commented). |
| `backend/lambda_api/src/planner_api/errors.py` | lambda_api | 7 new `_TABLE` rows, one per `Empty*` type, all `422`/`EMPTY_FIELD`, each `message` a literal `messages.py` constant (R17-compliant). `_ErrorSpec`/`build_problem_response` untouched. |
| `docs/rest_api_contract.md` §4 | doc | New row: `EmptyField` → 422 → `EMPTY_FIELD`, beside `UnknownUnit`. |

## Traceability

| `E<n>` | `FR-*` | Test |
|---|---|---|
| E1 — empty ingredient `unit` (reproduction) | FR-UX-03, FR-LIB-05 | `test_an_unselected_unit_reports_the_empty_unit_message` |
| E2 — empty/whitespace recipe `name` | FR-UX-03, FR-LIB-03, FR-LIB-04 | `test_an_empty_recipe_name_…`, `test_a_whitespace_only_recipe_name_is_empty_too` |
| E3 — empty `category` | FR-UX-03, FR-LIB-03 | `test_an_unselected_category_…` |
| E4 — empty ingredient `name` | FR-UX-03, FR-LIB-03 | `test_an_empty_ingredient_name_…` |
| E5 — blank ingredient `quantity` (no more 500) | FR-UX-03, FR-LIB-03, architecture.md §4 invariant 12 | `test_a_blank_ingredient_quantity_…[None/""/"  "]` |
| E6 — blank `tools` entry | FR-UX-03, FR-LIB-03 | `test_a_blank_tool_entry_…` |
| E7 — blank `procedure` entry | FR-UX-03, FR-LIB-03 | `test_a_blank_procedure_step_…` |
| E8 — empty shopping-item `name`/`unit` | FR-UX-03, FR-SHOP-01, FR-SHOP-02 | `test_an_unselected_unit_on_a_shopping_item_…`, `test_an_empty_shopping_item_name_…` |
| E9 — filled/valid values, and outside-list rejections, unchanged | FR-LIB-05, FR-LIB-03 | `test_a_fully_filled_recipe_still_decodes`, `test_an_absent_estimated_time_is_still_accepted`, `test_a_filled_in_unit_outside_the_list_still_reports_unknown_unit`, `test_a_filled_in_category_outside_the_list_…`, `test_a_filled_in_shopping_item_still_decodes` — all green before and after, held |

`issue_list.json`'s `covers` for issue 5 (`FR-UX-03`, `FR-LIB-03`, `FR-LIB-05`,
`FR-LIB-04`, `FR-CAND-03`, `FR-SHOP-01`, `FR-SHOP-02`) are all reachable
through E1–E9 above.

## Test move and red→green evidence

Staged file moved verbatim (`diff` against the staged copy: empty):
`issues/empty-field-error-messages/tests/backend/lambda_api/tests/
test_empty_field_errors.py` → `backend/lambda_api/tests/
test_empty_field_errors.py`.

**Red**, before any code change (`uv run pytest lambda_api/tests/
test_empty_field_errors.py -q`): `12 failed, 5 passed` — matching
`plan.md` § *Red result at triage* (wrong `UNKNOWN_UNIT`/
`UNKNOWN_INGREDIENT_CATEGORY` code (2), silently accepted (7), uncaught
`ValueError`/`TypeError` escaping as a 500 (3)).

**Green**, after the fix (same command): `17 passed`.

Suites `plan.md` requires to stay green, confirmed together (`uv run pytest
lambda_api/tests/test_empty_field_errors.py lambda_api/tests/
test_serialization.py lambda_api/tests/test_error_mapping.py core/tests/
domain/test_units.py core/tests/domain/test_ingredient_category.py -q`):
**59 passed** — includes the R17 invariant test that caught the first design
attempt.

Two more live guards, not named in `plan.md` but caught by the fix's own
naming (both real, both fixed without touching the guard): `core/tests/
test_shared_kernel_guards.py::test_planner_core_has_one_unit_vocabulary`
(`EmptyUnit` → renamed `EmptyMeasure`) and `core/tests/
test_no_ambient_time.py::test_calendar_modules_contain_no_user_facing_text`
(one em dash in a new docstring in `domain/errors.py`, one of the four
ASCII-only `FEATURE_MODULES` → replaced with a hyphen).

Full backend suite (`uv run pytest -q -m "not aws and not docker"`): **846
passed, 8 deselected** (was 829 after issue 4 — +17, the new staged file).
`uv run ruff format --check .` / `uv run ruff check .` / `uv run mypy .` all
clean. `./init.sh`: fully green. No frontend file touched by this issue.

No staged test was edited, loosened, skipped or xfailed. `tasks.md` T1–T7
all ticked. `issue_list.json`: no edit made by this implementer for issue 5
(status was already `in_progress` at session start, per the batch dispatch).
