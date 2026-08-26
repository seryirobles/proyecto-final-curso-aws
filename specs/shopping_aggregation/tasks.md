# shopping_aggregation — Tasks

> Execute in order. Tick `[x]` as each completes.
> Read `design.md` §5 before splitting work across the four functions, and §6
> before typing any signature.

## Domain — sources (`backend/core/src/planner_core/domain/shopping.py`)

- [x] T1 — Create the module with its docstring, importing `SlotRef`,
  `current_week`, `next_week`, `slots_from` from
  `planner_core.domain.calendar`; `SlotContents`, `definitive` from
  `planner_core.domain.candidate`; `Ingredient` from
  `planner_core.domain.recipe`; `normalize` from `planner_core.domain.text`;
  `Unit` from `planner_core.domain.units` (`design.md` §6). Covers: R1–R8.
- [x] T2 — Add `in_scope_slots(today: date) -> tuple[SlotRef, ...]`: return
  `slots_from(current_week(today), today) + slots_from(next_week(today),
  today)` (`design.md` §6). Covers: R1, R2.
- [x] T3 — Add `definitive_ingredients(plans: Mapping[SlotRef, SlotContents],
  slots: Iterable[SlotRef]) -> tuple[Ingredient, ...]`: for each slot in
  `slots`, in order, look up `plans.get(slot)`; if the slot is absent from
  `plans` or `definitive(plan)` returns `None`, contribute nothing; otherwise
  extend the result with `candidate.meal.ingredients` (`design.md` §6).
  Covers: R3, R4.
- [x] T4 — Add `aggregate_ingredients(ingredients: Iterable[Ingredient]) ->
  tuple[Ingredient, ...]`: iterate once, keyed on `(normalize(ingredient.
  name), ingredient.unit)`; on the first occurrence of a key record its raw
  `name` and start its running quantity at `0`; on every occurrence add
  `ingredient.quantity` to that key's running total; never construct a `Unit`
  value directly (`ingredient.unit` is carried through unchanged); return one
  `Ingredient` per key, in first-occurrence order, carrying the recorded name,
  the summed quantity, and the key's unit (`design.md` §6, §7). Covers: R5,
  R6, R8.
- [x] T5 — Add `required_shopping_items(plans: Mapping[SlotRef, SlotContents],
  today: date) -> tuple[Ingredient, ...]`: return
  `aggregate_ingredients(definitive_ingredients(plans, in_scope_slots
  (today)))` (`design.md` §6). Covers: R1–R8 (the composed entry point).

## Tests (`backend/core/tests/domain/test_shopping.py`)

- [x] T6 — `test_in_scope_slots_includes_current_week_from_today_onward` —
  pick a `today` mid-week (e.g. a Wednesday); assert every slot of `today`
  and every later day of the same ISO week appears in
  `in_scope_slots(today)`, and no slot of an earlier day of that week does.
  Covers: R1.
- [x] T7 — `test_in_scope_slots_includes_the_whole_next_week` — assert
  `in_scope_slots(today)` contains all 14 slots of `next_week(today)`,
  including days before `today`'s weekday position (e.g. `today` is
  Wednesday, next week's Monday and Tuesday are still included). Covers: R2.
- [x] T8 — `test_definitive_ingredients_includes_a_slots_definitive_meal` —
  build a `SlotContents` with one candidate holding a `MealSnapshot` with two
  `Ingredient`s, promoted to definitive; call `definitive_ingredients` with
  `plans={slot: plan}` and `slots=(slot,)`; assert the result equals that
  meal's `ingredients` tuple. Covers: R3.
- [x] T9 — `test_definitive_ingredients_ignores_a_slot_with_only_candidates`
  — a `SlotContents` with one or more candidates and `definitive_id=None`;
  assert `definitive_ingredients` returns `()` for that slot. Covers: R4.
- [x] T10 — `test_definitive_ingredients_ignores_a_slot_absent_from_plans` —
  call with a `slots` tuple containing a `SlotRef` that has no entry in
  `plans`; assert it contributes nothing and no `KeyError` is raised. Covers:
  R4.
- [x] T11 — `test_definitive_ingredients_preserves_slot_and_ingredient_order`
  — two slots, each with a definitive holding two ingredients; assert the
  result is the concatenation of both meals' `ingredients` tuples in the
  order `slots` was given, not merged and not reordered (`definitive_
  ingredients` performs no aggregation, `aggregate_ingredients` does).
  Covers: R3.
- [x] T12 — `test_aggregate_ingredients_sums_matching_name_and_unit` —
  `Ingredient("tomate", 200, Unit.GRAM)` and `Ingredient("tomate", 300,
  Unit.GRAM)`; assert the result is exactly one item, quantity `500`. Covers:
  R5.
- [x] T13 — `test_aggregate_ingredients_matches_on_normalized_name` —
  `Ingredient("Tomate", 200, Unit.GRAM)` and `Ingredient(" tomate ", 300,
  Unit.GRAM)`; assert they merge into one item (`text.normalize` folds case,
  accents and surrounding whitespace, feature 3). Covers: R5.
- [x] T14 — `test_aggregate_ingredients_keeps_different_units_separate` —
  `Ingredient("leche", 500, Unit.MILLILITRE)` and `Ingredient("leche", 1,
  Unit.UNIT)`; assert the result has two items, neither quantity summed with
  the other, no conversion attempted. Covers: R6.
- [x] T15 — `test_aggregate_ingredients_keeps_different_normalized_names_
  separate` — `Ingredient("tomate", 200, Unit.GRAM)` and `Ingredient
  ("tomates", 200, Unit.GRAM)`; assert two items remain (no stemming, no
  singular/plural fold — `G-56`). Covers: R5.
- [x] T16 — `test_aggregate_ingredients_keeps_the_first_occurrences_spelling`
  — `Ingredient("Tomate", 200, Unit.GRAM)` first, then `Ingredient("tomate",
  100, Unit.GRAM)`; assert the merged item's `name == "Tomate"` (`design.md`
  §6, §8 rejected alternative D). Covers: R5.
- [x] T17 — `test_aggregate_ingredients_result_items_are_ingredient_instances`
  — every element of `aggregate_ingredients(...)` is an instance of
  `planner_core.domain.recipe.Ingredient`; `{f.name for f in dataclasses.
  fields(Ingredient)} == {"name", "quantity", "unit"}` (`design.md` §7).
  Covers: R8.
- [x] T18 — `test_required_shopping_items_excludes_candidates_never_
  promoted` — a full `plans` mapping across both in-scope weeks where one
  slot has only candidates; assert none of that slot's ingredients appear in
  `required_shopping_items(plans, today)`. Covers: R3, R4.
- [x] T19 — `test_required_shopping_items_excludes_a_definitive_outside_
  scope` — a definitive meal placed on a day before `today` in the current
  week; assert its ingredients are absent from the result (`in_scope_slots`
  already excludes the slot, R1). Covers: R1, R3.
- [x] T20 — `test_required_shopping_items_merges_across_both_weeks` — the
  same normalized name + unit appears in a definitive meal of the current
  week and another of the next week; assert the result carries one item
  whose quantity is the sum of both. Covers: R1, R2, R5.
- [x] T21 — `test_required_shopping_items_is_deterministic_across_repeated_
  invocations` — call `required_shopping_items(plans, today)` twice with the
  same arguments; assert the two results are equal (`docs/verification.md`
  Level 2 property test shape). Covers: R7.
- [x] T22 — `test_required_shopping_items_is_idempotent_by_construction` —
  the acceptance-criterion-6 test: call `required_shopping_items` a third
  time after mutating a *copy* of `plans` back to an equal value; assert the
  result is still equal to the first call's, demonstrating convergence rather
  than mere object identity. Covers: R7.
- [x] T23 — `test_required_shopping_items_returns_empty_tuple_when_nothing_
  is_required` — an empty `plans` mapping; assert
  `required_shopping_items({}, today) == ()`, never `None`. Covers: R7, R8.

## Close-out

- [x] T24 — Record the `R<n> → test` map in
  `progress/impl_shopping_aggregation.md` (`docs/verification.md` Level 3).
  Covers: R1–R8.
- [x] T25 — Confirm `backend/core/pyproject.toml` still reads
  `dependencies = []`, and that `uv export --package planner-api --no-dev`
  and `uv export --package planner-ai --no-dev` both resolve with nothing
  added. Covers: R1–R8 (no dependency introduced).
- [x] T26 — Run `./init.sh` and confirm every gate is green: `ruff format`,
  `ruff check`, `mypy --strict`, `pytest` (including
  `test_shared_kernel_guards.py` and `test_no_ambient_time.py`, unmodified
  but re-run), plus the frontend gate. Covers: R1–R8.
