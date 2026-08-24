# recipe_model — Tasks

> Execute in order. Tick `[x]` as each completes.
> Read `design.md` §4 before choosing the category values, §5 before writing
> `snapshot()`, and §6 before typing `Ingredient.unit` — do not accept a raw
> string there.

## Domain — sources

- [x] T1 — Add `IngredientCategory(StrEnum)` with exactly `MEAT = "meat"`,
  `FISH = "fish"`, `CARBOHYDRATE = "carbohydrate"`, `LEGUME = "legume"`,
  `VEGETABLE = "vegetable"`, `EGGS = "eggs"` in
  `backend/core/src/planner_core/domain/ingredient_category.py`. Covers: R4.
- [x] T2 — In the same module, add `UnknownIngredientCategory(PlannerError)`
  — importing `PlannerError` from `planner_core.domain.errors` — storing the
  rejected value on `self.value`, and `parse_category(value: str) ->
  IngredientCategory` matching a member's code **exactly**: no case folding,
  no `strip()`, no call to `normalize` (`design.md` §6, mirrors
  `parse_unit`). Covers: R5, R6, R7.
- [x] T3 — Add `Ingredient` (`@dataclass(frozen=True)`) with fields exactly
  `name: str`, `quantity: float`, `unit: Unit` in
  `backend/core/src/planner_core/domain/recipe.py`, importing `Unit` from
  `planner_core.domain.units`. No unit-resolution logic in this module — a
  caller must pass an already-`parse_unit`-resolved value (`design.md` §6,
  rejected alternative B). Covers: R3, R9.
- [x] T4 — In the same module, add `Recipe` (`@dataclass(frozen=True)`) with
  fields exactly `name: str`, `ingredients: tuple[Ingredient, ...]`,
  `tools: tuple[str, ...]`, `procedure: tuple[str, ...]`,
  `category: IngredientCategory`. No cuisine, difficulty or kcal field.
  Covers: R1, R2.
- [x] T5 — In the same module, add `MealSnapshot` (`@dataclass(frozen=True)`),
  a type distinct from `Recipe` (not a subclass, not an alias), with the
  identical field shape: `name`, `ingredients`, `tools`, `procedure`,
  `category`. Covers: R10.
- [x] T6 — In the same module, add `snapshot(recipe: Recipe) -> MealSnapshot`,
  constructing a new `MealSnapshot` from `recipe`'s field values. No field on
  `MealSnapshot` or local state inside `snapshot()` retains a reference to
  `recipe` itself (`design.md` §5). Covers: R11, R12, R13, R14.

## Tests — ingredient category (`backend/core/tests/domain/test_ingredient_category.py`)

- [x] T7 — `test_the_ingredient_category_vocabulary_is_closed` —
  `[c.value for c in IngredientCategory]` equals `["meat", "fish",
  "carbohydrate", "legume", "vegetable", "eggs"]` exactly, and the member names
  are exactly `MEAT`, `FISH`, `CARBOHYDRATE`, `LEGUME`, `VEGETABLE`, `EGGS`.
  Covers: R4.
- [x] T8 — `test_parse_category_resolves_every_code` — each of the six codes
  resolves to its matching member. Covers: R5.
- [x] T9 — `test_parse_category_rejects_a_value_outside_the_list` —
  `"MEAT"` (wrong case), `" meat"`, `"dairy"` and `""` each raise
  `UnknownIngredientCategory`. Covers: R6.
- [x] T10 — `test_unknown_ingredient_category_is_a_planner_error` — assert
  `issubclass(UnknownIngredientCategory, PlannerError)` **and** that a real
  `parse_category("dairy")` raise is caught by `except PlannerError`. Covers:
  R7.

## Tests — recipe and snapshot (`backend/core/tests/domain/test_recipe.py`)

- [x] T11 — `test_recipe_is_frozen` — constructing a `Recipe` then attempting
  to set an attribute on it raises `dataclasses.FrozenInstanceError`. Covers:
  R1.
- [x] T12 — `test_recipe_fields_are_exactly_the_fixed_shape` — introspect
  `{f.name for f in dataclasses.fields(Recipe)}`, assert it equals exactly
  `{"name", "ingredients", "tools", "procedure", "category"}` — no `cuisine`,
  `difficulty` or `kcal` field. Covers: R2.
- [x] T13 — `test_ingredient_fields_are_exactly_the_fixed_shape` — same
  introspection for `Ingredient`: exactly `{"name", "quantity", "unit"}`.
  Covers: R3.
- [x] T14 — `test_ingredient_unit_is_the_shared_unit_enum` — construct an
  `Ingredient` using `unit=parse_unit("g")`; assert
  `isinstance(ingredient.unit, Unit)` and `ingredient.unit is Unit.GRAM`.
  Covers: R3.
- [x] T15 — `test_an_unlisted_unit_can_never_reach_an_ingredient` —
  `with pytest.raises(UnknownUnit): parse_unit("kg")`, demonstrating the only
  path into `Ingredient.unit` rejects a value outside the fixed list before
  an `Ingredient` can be built with it. Covers: R9.
- [x] T16 — `test_meal_snapshot_is_a_distinct_frozen_type` — assert
  `MealSnapshot is not Recipe`; assert
  `{f.name for f in dataclasses.fields(MealSnapshot)}` equals `Recipe`'s field
  names; attempting to set an attribute on a `MealSnapshot` instance raises
  `dataclasses.FrozenInstanceError`. Covers: R10.
- [x] T17 — `test_snapshot_copies_the_recipes_content` — build a `Recipe` with
  a non-trivial ingredient list, tools and procedure; call `snapshot()`;
  assert the result's `name`, `ingredients`, `tools`, `procedure` and
  `category` all equal the source recipe's values. Covers: R11, R14.
- [x] T18 — `test_meal_snapshot_holds_no_reference_to_the_recipe` — introspect
  `dataclasses.fields(MealSnapshot)`; assert no field's declared type is
  `Recipe`, and assert `MealSnapshot` declares no `id`/`recipe`/`source`
  field. Covers: R12.
- [x] T19 — `test_editing_or_deleting_the_library_recipe_leaves_an_existing_snapshot_unchanged`
  — the `docs/verification.md` Level 4 scenario for G-05. Build
  `library: dict[str, Recipe] = {"r1": original}`; take
  `taken = snapshot(library["r1"])`; replace `library["r1"]` with a
  differently-named, differently-categorised `Recipe` (the "edit"); assert
  `taken.name` and `taken.category` still equal the **original** recipe's
  values. Then `del library["r1"]` (the "delete"); assert `taken`'s fields are
  still exactly the original values. Covers: R13.

## Tests — mechanical guards (extend `backend/core/tests/test_shared_kernel_guards.py`)

> Build to the same self-testing discipline the existing three guards use:
> each scan asserts its own pattern matches inside the module it exempts, and
> asserts the scanned file list is non-empty. `design.md` §7 gives the
> patterns and the exemptions.

- [x] T20 — Add `test_planner_core_has_one_ingredient_category_vocabulary` —
  no `.py` under `src/planner_core` other than `domain/ingredient_category.py`
  contains a class definition whose name includes `IngredientCategory`, or an
  assignment to `MEAT`, `FISH`, `CARBOHYDRATE`, `LEGUME`, `VEGETABLE` or
  `EGGS`.
  Self-test: the pattern matches inside `domain/ingredient_category.py`; the
  scanned file list is non-empty and includes `domain/recipe.py`. Covers: R8.
- [x] T21 — Add `test_planner_core_never_constructs_unit_directly` — no `.py`
  under `src/planner_core` contains the literal substring `Unit(` (a direct
  call to the enum's constructor, as opposed to `parse_unit(...)` or
  `Unit.GRAM`-style member access). Self-test: assert the pattern matches a
  local string `"Unit(\"g\")"` so the regex itself is proven live, and assert
  it does **not** match `"parse_unit(value)"` or `"Unit.GRAM"`. Covers: R9.

  Implementation note: the literal-substring reading as specced would flag
  `raise UnknownUnit(value)` in `units.py` (contains `Unit(` as a
  sub-sequence of `UnknownUnit(`) and `class Unit(StrEnum):` (its own
  declaration) — both false positives, neither a construction call. The scan
  uses `\bUnit\(` (a word boundary before `Unit`, so `UnknownUnit(` — no
  boundary before `Unit` there — never matches) plus a class-header
  exclusion for `class Unit(StrEnum):`'s base-list parens. Still exactly the
  literal pattern `Unit(` per the design description; unmentioned in
  `design.md` §7 and `tasks.md`'s two counter-examples, so recorded here
  rather than silently patched.
- [x] T22 — Extend `test_the_shared_kernel_modules_are_ascii_only`'s asserted
  module set from `{domain/text.py, domain/units.py}` to also include
  `domain/recipe.py` and `domain/ingredient_category.py`; assert all four are
  ASCII-only. Covers: R15.

## Close-out

- [x] T23 — Record the `R<n> → test` map in
  `progress/impl_recipe_model.md` (`docs/verification.md` Level 3). Covers:
  R1–R15.
- [x] T24 — Confirm `backend/core/pyproject.toml` still reads
  `dependencies = []`, and that `uv export --package planner-api --no-dev`
  and `uv export --package planner-ai --no-dev` both resolve with nothing
  added. Covers: R1–R15 (no dependency introduced).
- [x] T25 — Run `./init.sh` and confirm every gate is green: `ruff format`,
  `ruff check`, `mypy --strict`, `pytest`, plus the frontend gate. Covers:
  R1–R15.
