# rules_model — Requirements

> Feature 6 · tier 1 · `sdd: true`
> Covers: `FR-RULE-01`, `FR-RULE-02`, `FR-RULE-03`, `FR-RULE-04`, `FR-RULE-05`,
> `FR-RULE-06`, `FR-RULE-07`
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen
> requirement ids it implements and is verifiable by at least one concrete
> test that asserts a value.

## Purpose in one sentence

Model the shared, predefined generation rule set — ingredient-category
counts, a pinned library meal per day/slot, and disabled days — as a single
immutable value whose own constructor is the one gate keeping the set
satisfiable (`FR-RULE-07`), plus the pure per-run override (`FR-RULE-05`)
that never touches the shared value.

## One `SHALL` per requirement

Every `R<n>` below carries exactly one `SHALL` or one `SHALL NOT`, counted
mechanically rather than by eye, per the checklist in `AGENTS.md` /
`docs/specs.md`.

## Scope note on the seven covered requirements

Several of the seven ids in `covers` are UI-facing, persistence-facing, or
straddle a feature not yet built (real-time broadcast, AI generation). This
spec claims only the half each one names below; the rest belongs elsewhere
and is not implemented here.

| Requirement | Owned **here** | Deferred to |
|---|---|---|
| `FR-RULE-01` | The `RuleSet` value type, and the guarantee that neither it nor any operation on it is parameterized by a week identity — the same rules apply to every week by construction. | Persisting exactly one shared instance, and "shared among all users" as a concurrency/storage fact — **feature 14** (`persistence_ports`). |
| `FR-RULE-02` | The three rule types as separately enumerable collections (`category_counts`, `pins`, `disabled_days`) — the data shape a "list in its own dedicated section" needs. | The actual section layout and rendering — **feature 20**. |
| `FR-RULE-03` | The pure functions that compute each dropdown's valid option set (`max_selectable_count`, `available_days_for_pin`, `available_days_to_disable`), and closed-vocabulary field types (`IngredientCategory`, `MealSlot`, a validated `1..7` day). | The dropdown widgets themselves, and rejecting free-text input at the UI layer — **feature 20**. |
| `FR-RULE-04` | The three rule shapes (`CategoryCountRule`, `PinRule`, disabled-day membership) and the pure operations that set/remove each, reusing the ingredient-category list feature 4 already shipped. | The authoring UI for each rule type — **feature 20**. |
| `FR-RULE-05` | `apply_override`'s pure composition of an effective `RuleSet` from a shared one plus per-axis overrides, and the guarantee that the shared value is never mutated. | Wiring an override into an actual generation run — **feature 12** (`ai_output_validation`, not yet built) and the `ai` Lambda. |
| `FR-RULE-06` | The absence of any author/editor/owner field on every rule type, and the absence of an acting-user parameter on every mutating function. | Real-time broadcast of edits (`FR-RT-02`) — blocked on `P3`. |
| `FR-RULE-07` | Satisfiability validation (category totals vs. available slots after disabled days; no pin on a disabled day) enforced at construction, plus the pure pin-removal cascade when a referenced library recipe is deleted. | The delete-recipe confirmation flow itself — **feature 20**; issuing the actual `DeleteItem` — **feature 14**. Runtime shortfalls caused by *occupied* slots during generation are `FR-AI-12`'s concern, not this feature's (`G-71`). |

---

## R1
Implements: FR-RULE-01, FR-RULE-02, FR-RULE-04

The system SHALL declare `RuleSet` as `@dataclass(frozen=True)` in
`planner_core.domain.rules` with fields exactly `category_counts:
tuple[CategoryCountRule, ...]`, `pins: tuple[PinRule, ...]` and
`disabled_days: tuple[int, ...]`.

## R2
Implements: FR-RULE-01

The system SHALL NOT accept a week identity (an `IsoWeek`, a `SlotRef`, or a
`date`) as a parameter of `RuleSet` or of any function in
`planner_core.domain.rules` that constructs or mutates one.

## R3
Implements: FR-RULE-04

The system SHALL declare `CategoryCountRule` as `@dataclass(frozen=True)`
with fields exactly `category: IngredientCategory` and `count: int`.

## R4
Implements: FR-RULE-04

The system SHALL declare `PinRule` as `@dataclass(frozen=True)` with fields
exactly `day: int`, `slot: MealSlot` and `recipe_id: str`.

## R5
Implements: FR-RULE-04

IF `RuleSet` is constructed with a `day` value outside `1..7` in
`disabled_days` or in any element of `pins`, THEN the system SHALL raise
`InvalidWeekday`.

## R6
Implements: FR-RULE-07

IF the sum of `count` across `category_counts` exceeds `14` minus twice the
number of `disabled_days`, THEN `RuleSet` construction SHALL raise
`UnsatisfiableRuleSet`.

## R7
Implements: FR-RULE-07

IF any element of `pins` has a `day` that is also a member of
`disabled_days`, THEN `RuleSet` construction SHALL raise
`UnsatisfiableRuleSet`.

## R8
Implements: FR-RULE-04

The system SHALL provide `set_category_count(rule_set: RuleSet, category:
IngredientCategory, count: int) -> RuleSet` whose result's `category_counts`
holds exactly one `CategoryCountRule` for `category`, carrying `count`, with
every other category's prior rule unchanged.

## R9
Implements: FR-RULE-04

The system SHALL provide `remove_category_count(rule_set: RuleSet, category:
IngredientCategory) -> RuleSet` whose result's `category_counts` contains no
rule for `category`.

## R10
Implements: FR-RULE-04

The system SHALL provide `set_pin(rule_set: RuleSet, day: int, slot:
MealSlot, recipe_id: str) -> RuleSet` whose result's `pins` holds exactly one
`PinRule` for `(day, slot)`, carrying `recipe_id`.

## R11
Implements: FR-RULE-04

The system SHALL provide `remove_pin(rule_set: RuleSet, day: int, slot:
MealSlot) -> RuleSet` whose result's `pins` contains no `PinRule` for
`(day, slot)`.

## R12
Implements: FR-RULE-04

The system SHALL provide `disable_day(rule_set: RuleSet, day: int) ->
RuleSet` whose result's `disabled_days` contains `day`.

## R13
Implements: FR-RULE-04

The system SHALL provide `enable_day(rule_set: RuleSet, day: int) ->
RuleSet` whose result's `disabled_days` does not contain `day`.

## R14
Implements: FR-RULE-07, FR-RULE-03

The system SHALL provide `max_selectable_count(rule_set: RuleSet, category:
IngredientCategory) -> int` returning `max(0, available - other)`, where
`available` is `14` minus twice the number of `rule_set.disabled_days` and
`other` is the sum of `count` across every `category_counts` rule not for
`category`.

## R15
Implements: FR-RULE-07, FR-RULE-03

The system SHALL provide `available_days_for_pin(rule_set: RuleSet) ->
tuple[int, ...]` returning exactly the weekdays `1..7` absent from
`rule_set.disabled_days`.

## R16
Implements: FR-RULE-07, FR-RULE-03

The system SHALL provide `available_days_to_disable(rule_set: RuleSet) ->
tuple[int, ...]` returning exactly the weekdays `1..7` that are neither in
`rule_set.disabled_days` nor the `day` of any element of `rule_set.pins`.

## R17
Implements: FR-RULE-07

The system SHALL provide `remove_pins_referencing(rule_set: RuleSet,
recipe_id: str) -> RemovePinsResult` whose `rule_set` field's `pins` excludes
every element whose `recipe_id` equals the given `recipe_id`.

## R18
Implements: FR-RULE-07

`remove_pins_referencing`'s `removed_pins` field SHALL contain exactly the
elements of the input `rule_set.pins` whose `recipe_id` equals the given
`recipe_id`.

## R19
Implements: FR-RULE-05

The system SHALL provide `apply_override(shared: RuleSet, category_counts:
tuple[CategoryCountRule, ...] | None = None, pins: tuple[PinRule, ...] |
None = None, disabled_days: tuple[int, ...] | None = None) -> RuleSet` whose
result uses each argument's value when it is not `None`, and `shared`'s
corresponding field otherwise.

## R20
Implements: FR-RULE-05

The system SHALL NOT modify any field of the `shared` argument passed to
`apply_override`.

## R21
Implements: FR-RULE-06

The system SHALL NOT declare an author, editor or owner field on `RuleSet`,
`CategoryCountRule`, `PinRule` or `RemovePinsResult`.

## R22
Implements: FR-RULE-06

The system SHALL NOT accept a parameter identifying the acting user in the
signature of `set_category_count`, `remove_category_count`, `set_pin`,
`remove_pin`, `disable_day`, `enable_day`, or `apply_override`.

---

## Coverage map

| Frozen requirement | Covered by |
|---|---|
| `FR-RULE-01` | R1, R2 |
| `FR-RULE-02` | R1 |
| `FR-RULE-03` | R14, R15, R16 |
| `FR-RULE-04` | R1, R3, R4, R5, R8, R9, R10, R11, R12, R13 |
| `FR-RULE-05` | R19, R20 |
| `FR-RULE-06` | R21, R22 |
| `FR-RULE-07` | R6, R7, R14, R15, R16, R17, R18 |

| `feature_list.json` acceptance criterion | Covered by |
|---|---|
| The three rule types are modelled: category counts, pinned meal per day/slot, disabled days (`FR-RULE-04`) | R1, R3, R4 |
| The ingredient-category list is a fixed predefined set (concrete values proposed in `design.md` per `G-63`) | Already satisfied by feature 4's `IngredientCategory` (`G-69`, `G-82`), reused via R3 — see `design.md` §4 |
| Available options are constrained so contradictory rule sets cannot be composed: category totals exceeding available slots after disabled days, or a pin on a disabled day (`FR-RULE-07`) | R5, R6, R7, R14, R15, R16 |
| Deleting a library recipe referenced by a pin rule surfaces a warning and removes the rule on confirmation (`FR-RULE-07`, `G-20`) | R17, R18 |
| A per-run override produces an effective rule set without mutating the shared rules (`FR-RULE-05`, `G-06`) | R19, R20 |
| Any user may edit the shared rules; a rule stores NO author — rule attribution was removed from the MVP (`FR-RULE-06`, `G-76`, completed by `G-78` for `FR-RT-02`) | R21, R22 |

Supporting requirements not demanded by a single acceptance bullet but
required by the invariants those bullets rest on: R2 (`FR-RULE-01`'s
"apply to every week" clause — a week-scoped `RuleSet` would silently
contradict it), R8–R13 (the individual set/remove operations `FR-RULE-04`'s
"editable" clause requires for each of the three rule types, mirroring
`FR-CAND-01`'s add/edit/remove split in `week_plan_model`).
