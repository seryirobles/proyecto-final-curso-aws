# rules_model — Tasks

> Execute in order. Tick `[x]` as each completes.
> Read `design.md` §5 before touching `RuleSet.__post_init__` — it is the
> single satisfiability gate every mutating function relies on — and §6
> before typing any signature.

## Domain — sources (`backend/core/src/planner_core/domain/rules.py`)

- [x] T1 — Create the module with its docstring, importing `MealSlot` from
  `planner_core.domain.calendar`, `PlannerError` from
  `planner_core.domain.errors`, and `IngredientCategory` from
  `planner_core.domain.ingredient_category`. Add `DAYS_PER_WEEK: Final[int]
  = 7`, `SLOTS_PER_DAY: Final[int] = len(MealSlot)`, `TOTAL_SLOTS: Final[int]
  = DAYS_PER_WEEK * SLOTS_PER_DAY`, `WEEKDAYS: Final[frozenset[int]] =
  frozenset(range(1, DAYS_PER_WEEK + 1))` (`design.md` §4, §8 rejected
  alternative C). Covers: R5, R6, R14, R15, R16.
- [x] T2 — Add `InvalidWeekday(PlannerError)` and `UnsatisfiableRuleSet
  (PlannerError)`, the first storing the offending value on
  `self.value` (mirroring `UnknownUnit`/`UnknownIngredientCategory`), the
  second carrying no extra state. Covers: R5, R6, R7.
- [x] T3 — Add `CategoryCountRule` (`@dataclass(frozen=True)`) with fields
  exactly `category: IngredientCategory`, `count: int`. Covers: R3.
- [x] T4 — Add `PinRule` (`@dataclass(frozen=True)`) with fields exactly
  `day: int`, `slot: MealSlot`, `recipe_id: str`. Covers: R4.
- [x] T5 — Add `RuleSet` (`@dataclass(frozen=True)`) with fields
  `category_counts: tuple[CategoryCountRule, ...] = ()`, `pins:
  tuple[PinRule, ...] = ()`, `disabled_days: tuple[int, ...] = ()`, plus
  `__post_init__` that: (1) raises `InvalidWeekday(day)` for the first `day`
  outside `WEEKDAYS` found in `disabled_days` or in any `pins` element's
  `day`; (2) raises `UnsatisfiableRuleSet` when `sum(r.count for r in
  category_counts)` exceeds `TOTAL_SLOTS - SLOTS_PER_DAY *
  len(disabled_days)`; (3) raises `UnsatisfiableRuleSet` when any `pins`
  element's `day` is a member of `disabled_days` (`design.md` §5). Covers:
  R1, R5, R6, R7.
- [x] T6 — Add `set_category_count(rule_set, category, count) -> RuleSet`:
  filter out any existing `CategoryCountRule` for `category` from
  `rule_set.category_counts`, append a new one carrying `count`, construct a
  new `RuleSet` with `pins` and `disabled_days` unchanged. Covers: R8.
- [x] T7 — Add `remove_category_count(rule_set, category) -> RuleSet`:
  filter out any `CategoryCountRule` for `category`; no error if absent.
  Covers: R9.
- [x] T8 — Add `set_pin(rule_set, day, slot, recipe_id) -> RuleSet`: filter
  out any existing `PinRule` matching `(day, slot)` from `rule_set.pins`,
  append a new one carrying `recipe_id`, construct a new `RuleSet` with
  `category_counts` and `disabled_days` unchanged. Covers: R10.
- [x] T9 — Add `remove_pin(rule_set, day, slot) -> RuleSet`: filter out any
  `PinRule` matching `(day, slot)`; no error if absent. Covers: R11.
- [x] T10 — Add `disable_day(rule_set, day) -> RuleSet`: construct a new
  `RuleSet` with `day` appended to `disabled_days` when not already present,
  otherwise `rule_set` unchanged (idempotent). Covers: R12.
- [x] T11 — Add `enable_day(rule_set, day) -> RuleSet`: construct a new
  `RuleSet` with `day` filtered out of `disabled_days`; no error if absent.
  Covers: R13.
- [x] T12 — Add `max_selectable_count(rule_set, category) -> int`: compute
  `available = TOTAL_SLOTS - SLOTS_PER_DAY * len(rule_set.disabled_days)`
  and `other = sum(r.count for r in rule_set.category_counts if r.category
  != category)`; return `max(0, available - other)`. Covers: R14.
- [x] T13 — Add `available_days_for_pin(rule_set) -> tuple[int, ...]`:
  return `tuple(sorted(WEEKDAYS - set(rule_set.disabled_days)))`. Covers:
  R15.
- [x] T14 — Add `available_days_to_disable(rule_set) -> tuple[int, ...]`:
  compute `pinned = {p.day for p in rule_set.pins}`; return
  `tuple(sorted(WEEKDAYS - set(rule_set.disabled_days) - pinned))`. Covers:
  R16.
- [x] T15 — Add `RemovePinsResult` (`@dataclass(frozen=True)`, fields
  `rule_set: RuleSet`, `removed_pins: tuple[PinRule, ...]`) and
  `remove_pins_referencing(rule_set, recipe_id) -> RemovePinsResult`:
  partition `rule_set.pins` into `removed` (matching `recipe_id`) and `kept`
  (not matching); return `RemovePinsResult(rule_set=RuleSet(category_counts
  =rule_set.category_counts, pins=kept, disabled_days=rule_set.
  disabled_days), removed_pins=removed)`. Covers: R17, R18.
- [x] T16 — Add `apply_override(shared, category_counts=None, pins=None,
  disabled_days=None) -> RuleSet`: return a new `RuleSet` using each
  argument when it is not `None`, else `shared`'s corresponding field; never
  write to any attribute of `shared` (`design.md` §8 rejected alternative
  B). Covers: R19, R20.

## Tests (`backend/core/tests/domain/test_rules.py`)

- [x] T17 — `test_rule_set_declares_exactly_the_three_fields` — introspect
  `{f.name for f in dataclasses.fields(RuleSet)}` equals exactly
  `{"category_counts", "pins", "disabled_days"}`. Covers: R1.
- [x] T18 — `test_no_rules_function_takes_a_week_identity_parameter` —
  `inspect.signature` on `RuleSet.__init__` and on every function in
  `planner_core.domain.rules`; assert no parameter is annotated `IsoWeek`,
  `SlotRef`, or `date` (`design.md` §1). Covers: R2.
- [x] T19 — `test_category_count_rule_fields_are_exactly_the_fixed_shape` —
  introspect `dataclasses.fields(CategoryCountRule)` equals `{"category",
  "count"}`. Covers: R3.
- [x] T20 — `test_pin_rule_fields_are_exactly_the_fixed_shape` — introspect
  `dataclasses.fields(PinRule)` equals `{"day", "slot", "recipe_id"}`.
  Covers: R4.
- [x] T21 — `test_rule_set_rejects_an_out_of_range_disabled_day` —
  `with pytest.raises(InvalidWeekday): RuleSet(disabled_days=(8,))` and the
  same for `(0,)`. Covers: R5.
- [x] T22 — `test_rule_set_rejects_an_out_of_range_pin_day` —
  `with pytest.raises(InvalidWeekday): RuleSet(pins=(PinRule(day=9,
  slot=MealSlot.LUNCH, recipe_id="r1"),))`. Covers: R5.
- [x] T23 — `test_rule_set_rejects_category_totals_exceeding_available_slots`
  — build `category_counts` summing to `15` with `disabled_days=()`
  (`14` available); assert `UnsatisfiableRuleSet`. Covers: R6.
- [x] T24 — `test_disabling_a_day_can_make_a_previously_valid_total_invalid`
  — a `RuleSet` with `category_counts` summing to `13` and no disabled days
  constructs cleanly; calling `disable_day` on it (available drops to `12`)
  raises `UnsatisfiableRuleSet` (`design.md` §5). Covers: R6.
- [x] T25 — `test_rule_set_rejects_a_pin_on_a_disabled_day` — `with
  pytest.raises(UnsatisfiableRuleSet): RuleSet(pins=(PinRule(day=3,
  slot=MealSlot.DINNER, recipe_id="r1"),), disabled_days=(3,))`. Covers: R7.
- [x] T26 — `test_set_category_count_replaces_the_existing_rule_for_that_
  category` — start from a `RuleSet` with a `MEAT` rule of `2`; call
  `set_category_count(rule_set, IngredientCategory.MEAT, 4)`; assert exactly
  one `MEAT` rule remains, carrying `4`, and any other category's rule is
  untouched. Covers: R8.
- [x] T27 — `test_set_category_count_adds_a_new_rule_when_none_existed` —
  from `RuleSet()`, set `FISH` to `3`; assert `category_counts == (
  CategoryCountRule(IngredientCategory.FISH, 3),)`. Covers: R8.
- [x] T28 — `test_remove_category_count_removes_the_matching_rule` — start
  with `MEAT` and `FISH` rules; remove `MEAT`; assert only `FISH` remains.
  Covers: R9.
- [x] T29 — `test_remove_category_count_is_a_no_op_when_absent` — call
  `remove_category_count` on a `RuleSet` with no rule for that category;
  assert the result equals the input, no exception raised (`design.md` §8
  rejected alternative D). Covers: R9.
- [x] T30 — `test_set_pin_replaces_the_existing_pin_for_that_slot` — start
  with a pin on `(2, MealSlot.LUNCH, "r1")`; call `set_pin(rule_set, 2,
  MealSlot.LUNCH, "r2")`; assert exactly one pin remains for `(2, LUNCH)`,
  carrying `"r2"`. Covers: R10.
- [x] T31 — `test_remove_pin_removes_the_matching_pin` — start with two
  pins on different slots; remove one; assert only the other remains.
  Covers: R11.
- [x] T32 — `test_remove_pin_is_a_no_op_when_absent` — call `remove_pin` on
  a slot with no pin; assert the result equals the input. Covers: R11.
- [x] T33 — `test_disable_day_adds_the_day` — from `RuleSet()`, call
  `disable_day(rule_set, 5)`; assert `disabled_days == (5,)`. Covers: R12.
- [x] T34 — `test_disable_day_is_idempotent` — call `disable_day` twice on
  the same day; assert `disabled_days` still contains `5` exactly once.
  Covers: R12.
- [x] T35 — `test_enable_day_removes_the_day` — from a `RuleSet` with
  `disabled_days=(5,)`, call `enable_day(rule_set, 5)`; assert
  `disabled_days == ()`. Covers: R13.
- [x] T36 — `test_enable_day_is_a_no_op_when_absent` — call `enable_day` on
  a day that is not disabled; assert the result equals the input. Covers:
  R13.
- [x] T37 — `test_max_selectable_count_subtracts_other_categories_and_
  disabled_days` — `category_counts=(MEAT:3, FISH:2)`, `disabled_days=(1,)`
  (available `12`); assert `max_selectable_count(rule_set,
  IngredientCategory.MEAT) == 10` (`12 - 2`, `MEAT`'s own count excluded).
  Covers: R14.
- [x] T38 — `test_max_selectable_count_floors_at_zero` — construct a
  `rule_set` where every other category already sums to the full available
  budget; assert `max_selectable_count(rule_set, category) == 0`, never
  negative. Covers: R14.
- [x] T39 — `test_available_days_for_pin_excludes_disabled_days` —
  `disabled_days=(1, 7)`; assert `available_days_for_pin(rule_set) == (2,
  3, 4, 5, 6)`. Covers: R15.
- [x] T40 — `test_available_days_to_disable_excludes_disabled_and_pinned_
  days` — `disabled_days=(1,)`, a pin on day `3`; assert
  `available_days_to_disable(rule_set) == (2, 4, 5, 6, 7)`. Covers: R16.
- [x] T41 — `test_remove_pins_referencing_removes_every_matching_pin` — a
  `rule_set` with two pins on `"recipe-a"` (different slots) and one on
  `"recipe-b"`; call `remove_pins_referencing(rule_set, "recipe-a")`; assert
  `result.rule_set.pins == (the "recipe-b" pin,)`. Covers: R17.
- [x] T42 — `test_remove_pins_referencing_reports_exactly_what_it_removed`
  — same setup as T41; assert `result.removed_pins` equals exactly the two
  `"recipe-a"` pins, in their original order. Covers: R18.
- [x] T43 — `test_remove_pins_referencing_is_a_no_op_when_nothing_matches`
  — call with a `recipe_id` no pin carries; assert `result.rule_set ==
  rule_set` and `result.removed_pins == ()`. Covers: R17, R18 (negative
  case).
- [x] T44 — `test_apply_override_uses_the_override_value_when_given` — a
  `shared` `RuleSet` with non-empty `category_counts`; call `apply_override
  (shared, category_counts=(different rules,))`; assert the result's
  `category_counts` is the override, and `pins`/`disabled_days` equal
  `shared`'s. Covers: R19.
- [x] T45 — `test_apply_override_inherits_the_shared_value_when_none_given`
  — `apply_override(shared)` with every argument left `None`; assert the
  result equals `shared` field-for-field. Covers: R19.
- [x] T46 — `test_apply_override_never_mutates_shared` — capture `shared`'s
  field values before calling `apply_override(shared, disabled_days=(2,))`;
  assert `shared.disabled_days` is unchanged after the call (`design.md` §8
  rejected alternative B). Covers: R20.
- [x] T47 — `test_no_rule_type_declares_an_author_field` — introspect
  `dataclasses.fields` of `RuleSet`, `CategoryCountRule`, `PinRule`, and
  `RemovePinsResult`; assert no field name contains `"author"`, `"editor"`
  or `"owner"` (`G-76`, `G-78`). Covers: R21.
- [x] T48 — `test_no_mutating_function_takes_an_actor_parameter` —
  `inspect.signature` on `set_category_count`, `remove_category_count`,
  `set_pin`, `remove_pin`, `disable_day`, `enable_day`, `apply_override`;
  assert no parameter name contains `"user"`, `"author"` or `"actor"`
  (`G-76`, mirrors `week_plan_model`'s `test_promote_takes_no_author_or_
  promoter_argument`). Covers: R22.

## Close-out

- [x] T49 — Record the `R<n> → test` map in
  `progress/impl_rules_model.md` (`docs/verification.md` Level 3). Covers:
  R1–R22.
- [x] T50 — Confirm `backend/core/pyproject.toml` still reads
  `dependencies = []`, and that `uv export --package planner-api --no-dev`
  and `uv export --package planner-ai --no-dev` both resolve with nothing
  added. Covers: R1–R22 (no dependency introduced).
- [x] T51 — Run `./init.sh` and confirm every gate is green: `ruff format`,
  `ruff check`, `mypy --strict`, `pytest` (including
  `test_shared_kernel_guards.py`, unmodified but re-run), plus the frontend
  gate. Covers: R1–R22.
