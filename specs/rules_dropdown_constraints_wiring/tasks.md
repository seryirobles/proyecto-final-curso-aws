# rules_dropdown_constraints_wiring — Tasks

> Prerequisite for T1 (not a task the implementer does): the owner has
> edited `docs/rest_api_contract.md` per `design.md` §1's proposed
> `availableOptions` shape. Do not start T1 before that edit lands.

Test-first inside each task, per `docs/conventions.md` § Tests.

## Backend

- [x] T1 — Add `encode_available_options(rule_set)` to
  `backend/lambda_api/src/planner_api/serialization.py`, importing
  `IngredientCategory` and `max_selectable_count` /
  `available_days_for_pin` / `available_days_to_disable` from
  `planner_core.domain.rules`. Covers: R1, R2, R3, R4.
- [x] T2 — Wire the new field into `_list_rules` in
  `backend/lambda_api/src/planner_api/routing.py`:
  `{"rules": rules, "availableOptions": ser.encode_available_options(rule_set)}`.
  Covers: R1.
- [x] T3 — Extend `backend/lambda_api/tests/test_rules_routes.py` with a test
  seeding a rule set that exercises all three fields non-trivially (a
  category near its cap, a disabled day, a pinned day) and asserts
  `availableOptions`' three fields equal the pure functions called directly
  on the same `RuleSet`. Covers: R2, R3, R4.
- [x] T4 — Add a regression test (or confirm an existing one still covers it)
  proving a `PUT`/`DELETE /v1/rules/{ruleId}` that would make the set
  unsatisfiable still answers `422 UNSATISFIABLE_RULE_SET` with `conflicts`,
  unchanged by this feature. Covers: R5. Confirmed: existing
  `test_an_unsatisfiable_rule_change_is_rejected_422_with_conflicts` and
  `test_unsatisfiable_conflicts_array_has_no_recipename_for_a_conflicting_pin`
  still pass unmodified (verified by test run below).

## Frontend

- [x] T5 — In `frontend/src/hooks/useRules.js`: derive
  `maxCountByCategory` / `daysAvailableForPin` / `daysAvailableToDisable`
  from `poll.data?.availableOptions`; add memoized `categoryCountOptions`,
  `pinDayOptions`, `disabledDayOptions`; change `setCategoryCountCategory` to
  clear an out-of-range `count` draft on category change; remove
  `RULE_COUNT_OPTIONS`. Covers: R6, R7, R8, R9, R10, R11.
- [x] T6 — Update `frontend/src/components/RulesView.jsx` to accept
  `categoryCountOptions`, `pinDayOptions`, `disabledDayOptions` props and
  render each of the three selects from them, replacing
  `RULE_COUNT_OPTIONS.map(...)` and the two `Object.entries(DAY_LABELS)
  .map(...)` call sites this feature targets. The category select and the
  pin's slot select are unchanged. Covers: R6, R7, R9, R10.
- [x] T7 — Extend `frontend/tests/hooks/useRules.test.js` asserting
  `categoryCountOptions`/`pinDayOptions`/`disabledDayOptions` come only from
  `poll.data.availableOptions` (never from `poll.data.rules`), that an empty
  `category` draft yields no count options, and that changing `category`
  clears a `count` draft the new category's max no longer covers. Covers:
  R6, R7, R8, R11.
- [x] T8 — Extend `frontend/tests/components/RulesView.test.jsx` asserting
  each of the three selects renders exactly the options its prop lists (and
  none when the list is empty). Covers: R6, R7, R9, R10.
- [x] T9 — Confirm (add a regression test if none exists) that a caught
  `UNSATISFIABLE_RULE_SET` `ApiError` from `putRule`/`remove` still renders
  via `toRuleErrorDetail` exactly as before this feature. Covers: R12.
  Confirmed: existing `useRules.test.js` test "an UNSATISFIABLE_RULE_SET
  ApiError renders details.conflicts as es-ES text" exercises the same
  `toRuleErrorDetail` path both `putRule` and `remove` share, unmodified by
  this feature, and still passes (verified by test run below).

## Close-out

- [x] T10 — Run `./init.sh`; write
  `progress/impl_rules_dropdown_constraints_wiring.md` with the R-to-test
  traceability table. Covers: R1–R12.
