# Implementation report — rules_dropdown_constraints_wiring (feature 29)

## Traceability

| R<n> | FR-* | Task | Test |
|---|---|---|---|
| R1 | FR-RULE-07 | T1, T2 | `backend/lambda_api/tests/test_rules_routes.py::test_get_rules_available_options_matches_the_pure_functions_on_the_same_rule_set` |
| R2 | FR-RULE-07 | T1, T3 | same test (`maxCountByCategory` equality) |
| R3 | FR-RULE-07 | T1, T3 | same test (`daysAvailableForPin` equality) |
| R4 | FR-RULE-07 | T1, T3 | same test (`daysAvailableToDisable` equality) |
| R5 | FR-RULE-07 | T4 | existing `test_an_unsatisfiable_rule_change_is_rejected_422_with_conflicts`, `test_unsatisfiable_conflicts_array_has_no_recipename_for_a_conflicting_pin` — unmodified, still pass |
| R6 | FR-RULE-07 | T5, T6 | `frontend/tests/hooks/useRules.test.js::the three option lists come only from availableOptions...`; `frontend/tests/components/RulesView.test.jsx::the count select renders exactly the options categoryCountOptions lists` |
| R7 | FR-RULE-07 | T5, T6 | `useRules.test.js::an empty category draft yields no count options`; `RulesView.test.jsx::the count select renders no options when categoryCountOptions is empty` |
| R8 | FR-RULE-07 | T5 | `useRules.test.js::changing category clears a count draft the new category no longer covers` |
| R9 | FR-RULE-07 | T5, T6 | `useRules.test.js` (pinDayOptions assertion); `RulesView.test.jsx::the pin-day select renders exactly the options pinDayOptions lists` |
| R10 | FR-RULE-07 | T5, T6 | `useRules.test.js` (disabledDayOptions assertion); `RulesView.test.jsx::the disabled-day select renders exactly the options disabledDayOptions lists` |
| R11 | FR-RULE-07 | T5, T7 | `useRules.test.js::the three option lists come only from availableOptions, never from rules` (a `categoryCount` rule of count 99 is present but ignored; options derive solely from `availableOptions`) |
| R12 | FR-RULE-07 | T9 | existing `useRules.test.js::an UNSATISFIABLE_RULE_SET ApiError renders details.conflicts as es-ES text` — unmodified, still passes |

`FR-RULE-07` (the feature's only cited id) → R1–R12 → the tests above.

## What changed

Backend:
- `backend/lambda_api/src/planner_api/serialization.py` — new `encode_available_options(rule_set)`, calling `max_selectable_count`, `available_days_for_pin`, `available_days_to_disable` from `planner_core.domain.rules` (no new domain/application code).
- `backend/lambda_api/src/planner_api/routing.py` — `_list_rules` now returns `{"rules": rules, "availableOptions": ser.encode_available_options(rule_set)}`.
- `backend/lambda_api/tests/test_rules_routes.py` — new test asserting the three `availableOptions` fields equal the pure functions called directly on the same `RuleSet`, using a non-trivial scenario (two category counts, a disabled day, a pin).

Frontend:
- `frontend/src/hooks/useRules.js` — derives `maxCountByCategory`/`daysAvailableForPin`/`daysAvailableToDisable` from `poll.data?.availableOptions` (memoized); adds memoized `categoryCountOptions`, `pinDayOptions`, `disabledDayOptions`; `setCategoryCountCategory` now clears an out-of-range `count` draft on category change; removed the stale `RULE_COUNT_OPTIONS` constant (confirmed via grep its only two call sites were this file and `RulesView.jsx`).
- `frontend/src/components/RulesView.jsx` — takes three new props (`categoryCountOptions`, `pinDayOptions`, `disabledDayOptions`), rendering the count select, pin-day select, and disabled-day select from them; dropped the now-unused `DAY_LABELS`/`RULE_COUNT_OPTIONS` imports. Category select and pin's slot select unchanged (unconstrained, per design.md §4 — no corresponding pure function).
- `frontend/tests/hooks/useRules.test.js` — extended `mockPolling` to accept `availableOptions`; three new tests (R6/R7/R8/R9/R10/R11).
- `frontend/tests/components/RulesView.test.jsx` — `baseProps` extended with the three new props; four new tests asserting exact rendered `<option>`s per prop, including the empty case.
- `frontend/tests/components/LibraryRecipePicker.test.jsx` — its own inline `RulesView` prop fixture (the "3rd of 3 sites" test) updated with the same three new props, since it doesn't go through `useRules`.

## Test results

- `./init.sh`: green end to end — `ruff format`, `ruff check`, `mypy`, `pytest` (1036 passed, 8 deselected), `prettier --check`, `eslint`, `vitest` (472 passed).
- Backend rules-route suite in isolation: `uv run pytest -q lambda_api/tests/test_rules_routes.py` → 8 passed (was 7; +1 new).
- Frontend hook/component suites in isolation: `useRules.test.js` → 11 passed (was 8; +3 new); `RulesView.test.jsx` → 19 passed (was 15; +4 new).

## Deviations from the spec

None. `docs/rest_api_contract.md` §3.7 and the `GET /v1/rules` row in §2 were already landed by the owner and match `design.md` §1.1 verbatim, so no shape decision was made here. All ten tasks in `tasks.md` are checked off.
