# rules_dropdown_constraints_wiring — Requirements

> Feature 29 · tier 4 · `sdd: true` · `feature_list.json` `covers: []`
> Depends on feature 6 `rules_model` (done) and feature 20 `frontend_spa` (done).
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen
> requirement id it implements and is verifiable by at least one concrete test.

## Why `covers` is empty and what is cited instead

Like feature 28 (`specs/single_recipe_generation/requirements.md`), this
feature's `feature_list.json` entry carries an empty `covers` array — it is a
wiring gap found during feature 20's final review, not a fresh slice of a
tier-1 domain feature. The id every `R<n>` below cites is **`FR-RULE-07`**,
taken from the feature's own title and description: *"dropdown options shall
prevent contradictory combinations"* (`docs/requirements.md` line 141). No
other `FR-*` is touched — the requirement's warn-and-remove pin-cascade half
is feature 6's territory and is not reopened here.

## Purpose in one sentence

Wire the three pure constraint functions `rules_model` (feature 6) already
built — `max_selectable_count`, `available_days_for_pin`,
`available_days_to_disable` — through `GET /v1/rules` and into `RulesView`'s
three dropdowns, so a well-behaved client cannot compose a contradictory rule
set in the first place, without duplicating any of that arithmetic in
JavaScript (`docs/architecture.md` §1.1).

## Scope note

This feature adds **no new domain logic**. Every backend `R<n>` below is
wiring: read the already-computed `RuleSet`, call an existing
`planner_core.domain.rules` function, put the result on the wire. Every
frontend `R<n>` is rendering: read the wire field, render only those options.
The whole-set `422 UNSATISFIABLE_RULE_SET` check (feature 27) stays the last
line of defense for a race between two concurrent edits and is explicitly
**not** touched (R5, R12).

---

## Backend — `GET /v1/rules`

## R1
Implements: FR-RULE-07

The system SHALL include an `availableOptions` object in `GET /v1/rules`'s
`200` response body, alongside the existing `rules` array.

## R2
Implements: FR-RULE-07

The system SHALL populate `availableOptions.maxCountByCategory` with one
entry per `IngredientCategory` member, each value equal to
`planner_core.domain.rules.max_selectable_count` applied to the same shared
`RuleSet` the response's `rules` array was built from.

## R3
Implements: FR-RULE-07

The system SHALL populate `availableOptions.daysAvailableForPin` with the
value `planner_core.domain.rules.available_days_for_pin` returns for that
same shared `RuleSet`.

## R4
Implements: FR-RULE-07

The system SHALL populate `availableOptions.daysAvailableToDisable` with the
value `planner_core.domain.rules.available_days_to_disable` returns for that
same shared `RuleSet`.

## R5
Implements: FR-RULE-07

The system SHALL NOT alter the whole-set `UnsatisfiableRuleSet` validation
`rule_editing.py` performs before every per-rule `PUT`/`DELETE` write.

---

## Frontend — `RulesView`'s three dropdowns

## R6
Implements: FR-RULE-07

WHILE the category-count draft's `category` field is non-empty, the SPA
SHALL render the count `<select>`'s options as exactly the integers from `1`
through `availableOptions.maxCountByCategory[category]`.

## R7
Implements: FR-RULE-07

WHILE the category-count draft's `category` field is empty, the SPA SHALL
render the count `<select>` with no count options.

## R8
Implements: FR-RULE-07

IF the category-count draft's `category` changes to a value whose
`maxCountByCategory` entry no longer includes the current `count` draft
value, THEN the SPA SHALL clear the `count` draft to empty.

## R9
Implements: FR-RULE-07

The system SHALL render the pin section's day `<select>` options as exactly
the days listed in `availableOptions.daysAvailableForPin`.

## R10
Implements: FR-RULE-07

The system SHALL render the disabled-day section's day `<select>` options as
exactly the days listed in `availableOptions.daysAvailableToDisable`.

## R11
Implements: FR-RULE-07

The SPA SHALL NOT derive `maxCountByCategory`, `daysAvailableForPin` or
`daysAvailableToDisable` from any value besides the `availableOptions` field
of the polled `GET /v1/rules` response.

## R12
Implements: FR-RULE-07

The SPA SHALL NOT modify the existing handling of a `422
UNSATISFIABLE_RULE_SET` response from `PUT /v1/rules/{ruleId}` or
`DELETE /v1/rules/{ruleId}`.

---

## Coverage map

| Frozen requirement | Covered by |
|---|---|
| `FR-RULE-07` | R1–R12 |

| `feature_list.json` acceptance criterion | Covered by |
|---|---|
| OWNER-OWNED PRECURSOR: `rest_api_contract.md` needs an `availableOptions` shape | Not an `R<n>` — this is the human gate. `design.md` §1 proposes the shape; the owner edits `docs/rest_api_contract.md` before any task in `tasks.md` starts. |
| Backend: `_list_rules` computes and returns the available option sets using the existing pure functions, no new domain logic | R1, R2, R3, R4, R5 |
| Frontend: the three dropdowns render only the options the API reports as available, replacing today's full fixed-value lists | R6, R7, R8, R9, R10, R11 |
| The existing whole-set `422 UNSATISFIABLE_RULE_SET` check stays untouched, the last line of defense for a concurrent-edit race | R5, R12 |
