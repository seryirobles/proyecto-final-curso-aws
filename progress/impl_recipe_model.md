# Implementation report — feature 4 `recipe_model`

> Implementer session, 2026-08-23. Spec: `specs/recipe_model/`, all three §9
> gate questions approved by the human on 2026-08-23, all as recommended.
> Status left as `in_progress` — the reviewer closes it, not this agent.

---

## 1. Result

`./init.sh` → **exit 0**, every gate green:

| Gate | Result |
|---|---|
| `ruff format --check` | OK (30 files) |
| `ruff check` | OK |
| `mypy` (strict) | OK — no issues in 30 source files |
| `pytest` (unit, no AWS) | **70 passed** (55 before this feature, **+15**) |
| `prettier --check` / `eslint` / `vitest` (frontend) | OK, untouched |

All 25 tasks of `tasks.md` are ticked. No task was skipped.

---

## 2. Files

### Created — sources

| Path | Contents |
|---|---|
| `backend/core/src/planner_core/domain/ingredient_category.py` | `IngredientCategory(StrEnum)`, `UnknownIngredientCategory(PlannerError)`, `parse_category`. ASCII-only. |
| `backend/core/src/planner_core/domain/recipe.py` | `Ingredient`, `Recipe`, `MealSnapshot`, `snapshot`. ASCII-only. |

### Created — tests

| Path | Tests |
|---|---|
| `backend/core/tests/domain/test_ingredient_category.py` | 4 (T7–T10) |
| `backend/core/tests/domain/test_recipe.py` | 9 (T11–T19) |

### Modified

| Path | Change |
|---|---|
| `backend/core/tests/test_shared_kernel_guards.py` | Added `INGREDIENT_CATEGORY_SOURCE`, `RECIPE_SOURCE`, extended `SHARED_KERNEL_MODULES`; added `INGREDIENT_CATEGORY_VOCABULARY` and `UNIT_DIRECT_CONSTRUCTION` patterns plus `_matches_excluding_class_headers`; added `test_planner_core_has_one_ingredient_category_vocabulary` (T20) and `test_planner_core_never_constructs_unit_directly` (T21); extended `test_the_shared_kernel_modules_are_ascii_only`'s asserted set (T22). |

**Nothing else changes.** `planner_core/domain/errors.py` was reused unchanged
(`UnknownIngredientCategory` subclasses the `PlannerError` feature 2 declared).
`backend/core/pyproject.toml` still reads `dependencies = []`. No frozen doc,
no `feature_list.json` entry and no IaC/CI file was written. No git write
command was run at any point.

---

## 3. Traceability — every `R<n>` proved by a test that asserts a value

| `R<n>` | Task | Test | Module |
|---|---|---|---|
| R1 | T4, T11 | `test_recipe_is_frozen` | test_recipe |
| R2 | T4, T12 | `test_recipe_fields_are_exactly_the_fixed_shape` | test_recipe |
| R3 | T3, T13, T14 | `test_ingredient_fields_are_exactly_the_fixed_shape`, `test_ingredient_unit_is_the_shared_unit_enum` | test_recipe |
| R4 | T1, T7 | `test_the_ingredient_category_vocabulary_is_closed` | test_ingredient_category |
| R5 | T2, T8 | `test_parse_category_resolves_every_code` | test_ingredient_category |
| R6 | T2, T9 | `test_parse_category_rejects_a_value_outside_the_list` | test_ingredient_category |
| R7 | T2, T10 | `test_unknown_ingredient_category_is_a_planner_error` | test_ingredient_category |
| R8 | T20 | `test_planner_core_has_one_ingredient_category_vocabulary` | test_shared_kernel_guards |
| R9 | T3, T15, T21 | `test_an_unlisted_unit_can_never_reach_an_ingredient`, `test_planner_core_never_constructs_unit_directly` | test_recipe / test_shared_kernel_guards |
| R10 | T5, T16 | `test_meal_snapshot_is_a_distinct_frozen_type` | test_recipe |
| R11 | T6, T17 | `test_snapshot_copies_the_recipes_content` | test_recipe |
| R12 | T6, T18 | `test_meal_snapshot_holds_no_reference_to_the_recipe` | test_recipe |
| R13 | T6, T19 | `test_editing_or_deleting_the_library_recipe_leaves_an_existing_snapshot_unchanged` | test_recipe |
| R14 | T6, T17 | `test_snapshot_copies_the_recipes_content` | test_recipe |
| R15 | T22 | `test_the_shared_kernel_modules_are_ascii_only` | test_shared_kernel_guards |

### `FR-*` reachability (the `covers` array)

| Frozen requirement | Reached through | Proved by |
|---|---|---|
| `FR-LIB-03` | R1–R8, R15 | all `test_recipe`/`test_ingredient_category` tests above, plus the two guard tests |
| `FR-LIB-05` | R3, R9, R15 | `test_ingredient_fields_are_exactly_the_fixed_shape`, `test_ingredient_unit_is_the_shared_unit_enum`, `test_an_unlisted_unit_can_never_reach_an_ingredient`, `test_planner_core_never_constructs_unit_directly`, `test_the_shared_kernel_modules_are_ascii_only` |
| `FR-CAND-07` | R10–R13 | `test_meal_snapshot_is_a_distinct_frozen_type`, `test_snapshot_copies_the_recipes_content`, `test_meal_snapshot_holds_no_reference_to_the_recipe`, `test_editing_or_deleting_the_library_recipe_leaves_an_existing_snapshot_unchanged` |
| `FR-MENU-04` | R14 | `test_snapshot_copies_the_recipes_content` |

Both directions hold: every `R<n>` (R1–R15) has at least one test asserting a
concrete value, and neither `FR-*` in the `covers` array is left without a
reachable `R<n>`.

---

## 4. A spec-text gap found and fixed while implementing T21 (recorded, not silently patched)

`tasks.md` T21 and `design.md` §7 specify the R9 guard as "the literal pattern
`Unit(` across the whole `planner_core` package", asserted to match nothing
today. Taken literally against the **existing, already-`done`** `units.py`
(feature 3), this fails immediately on two lines neither counter-example in
the spec anticipates:

- `class Unit(StrEnum):` — the enum's own declaration; the substring `Unit(`
  is its base-list parens, not a call.
- `raise UnknownUnit(value)` — `UnknownUnit(` contains `Unit(` as a
  sub-sequence, but it is calling the *exception's* constructor, unrelated to
  R9 (which targets the *enum's* constructor).

Fixed by scanning with `\bUnit\(` (a word boundary is required immediately
before `Unit`, so `UnknownUnit(` — no boundary there, it is one continuous
identifier — never matches) plus a class-header exclusion,
`_matches_excluding_class_headers`, for `class Unit(StrEnum):`'s base-list
parens specifically. This still satisfies every case the spec's own self-test
requires (matches `Unit("g")`, does not match `parse_unit(value)` or
`Unit.GRAM`) while also not flagging feature 3's already-approved code. No
source file outside the test module was changed to make this pass — the fix
is entirely in the guard's regex and its exclusion helper, recorded inline in
`tasks.md` T21 and here per the "record the blocker with evidence" instruction.

---

## 5. mypy note

`mypy --strict` rejected the literal `assert MealSnapshot is not Recipe`
(T16/R10) as a "non-overlapping identity check" between two statically
distinct class-literal types. Fixed by assigning both to `type[object]`-typed
locals before comparing — the runtime check is unchanged, only the static type
of the compared expressions widened. No `# type: ignore` was used here.

**Correction, 2026-08-24 (review round 2, F3):** this statement was false for
T11/T16's frozen-instance checks. `mypy --strict` rejects a direct attribute
assignment on a frozen dataclass (`recipe.name = "Otro"`) as a read-only
property, and the original code carried `# type: ignore[misc]` on both
occurrences to work around that. Both are now removed — see the dated section
at the end of this file.

---

## 6. Boundary checks

| Check | Result |
|---|---|
| Runtime dependencies (T24) | `backend/core/pyproject.toml` still `dependencies = []`. `uv export --package planner-api --no-dev` and `--package planner-ai --no-dev` both resolve 27 packages with nothing added. |
| Layering (`architecture.md` §3) | Both new modules are pure values/functions in `domain/`. No port, no clock, no IO, no AWS SDK, no `application/` piece. |
| Architecture §2 decisions | None taken. The one §2.1 *decide-in-a-spec* item touched (the ingredient-category list) was decided by the human at the gate on 2026-08-23, not here. |
| User-facing strings | None. `UnknownIngredientCategory` carries only the rejected value; no backend messages module was created. |
| Frozen docs | Untouched. `docs/data_model.md` untouched — a category code is an attribute value, not one of the §2 key formats. |
| `feature_list.json` | Untouched; feature 4 left `in_progress` for the reviewer. |
| Terraform / CI | None written. |
| `# type: ignore` | **Correction, 2026-08-24:** two `# type: ignore[misc]` were present (`test_recipe.py:32`, `:74`), suppressing mypy's frozen-dataclass read-only check. Both removed in review round 2 (F3) — see the dated section below. |
| `tiempo` (prep time) | Deliberately absent, per the leader's instruction — no `FR-*` requires it; not treated as a bug. |

---

## 7. Handover notes for the features that consume this model

- **Feature 5** (`week_plan_model`) constructs `Candidate` wrapping a
  `MealSnapshot`, adding `anadidoPor` and persistence identity — not this
  feature's fields.
- **Feature 6** (`rules_model`) must import `IngredientCategory` from
  `planner_core.domain.ingredient_category`; `test_planner_core_has_one_ingredient_category_vocabulary`
  fails the build if it redeclares the enum or its member codes.
- **Feature 11** (`ai_prompt_builder`) owns `numeroComensales`
  (`FR-AI-13`, `G-64`) — not added here.
- **Feature 12** (`ai_output_validation`) validates AI output against
  `IngredientCategory`/`Unit` and owns the es-ES rejection text for both
  `UnknownIngredientCategory` and `UnknownUnit`.

---

## Review round 2 — 2026-08-24, fixing CHANGES_REQUESTED

`progress/review_recipe_model.md` raised three blocking findings. All three
are test-only changes; no source file (`recipe.py`, `ingredient_category.py`)
was touched.

**F1 (R9) — `CLASS_HEADER_LINE` exempted every class header, not just the
enum's own declaration.** Narrowed `backend/core/tests/test_shared_kernel_guards.py`'s
`CLASS_HEADER_LINE` from `^\s*class\s+\w+\(` to `^\s*class\s+Unit\(`, so only
`class Unit(StrEnum):` is exempt. Added
`test_the_class_header_exclusion_only_hides_units_own_declaration`, which
proves (via `tmp_path`) that `class _Sneaky(_Base, unit=Unit("g")):` is still
reported while the genuine declaration stays exempt. Verified live: planting
`class _Sneaky(dict, unit=Unit("g")):` in `recipe.py` now fails
`test_planner_core_never_constructs_unit_directly`; reverted, hash-confirmed
identical to baseline.

**F2 (R3) — `Ingredient.unit`'s declared type was unverified.** Added
`typing.get_type_hints(Ingredient)["unit"] is Unit` to
`test_ingredient_unit_is_the_shared_unit_enum`, keeping the existing runtime
assertions. Verified live: mutating `unit: Unit` to `unit: str` now fails this
test; reverted, hash-confirmed identical to baseline.

**F3 — two `# type: ignore[misc]` in `test_recipe.py`.** Removed both. The
reviewer's suggested replacement, `setattr(recipe, "name", "Otro")`, type-checks
clean under `mypy --strict` but is flagged by ruff's bugbear rule `B010`
("do not call setattr with a constant attribute value"), which recommends the
direct assignment `mypy` was rejecting in the first place — a genuine conflict
between the two gates the leader's fix did not anticipate. Resolved with
`recipe.__setattr__("name", "Otro")` (and the `taken` equivalent): it calls the
frozen dataclass's own overridden `__setattr__` directly, which still raises
`FrozenInstanceError` at runtime, passes `mypy --strict` with no ignore, and
triggers no ruff rule (`B010` targets the builtin `setattr()` call, not the
dunder method). Verified live: setting `frozen=False` on `Recipe` and on
`MealSnapshot` each makes the corresponding test fail with "DID NOT RAISE
FrozenInstanceError"; both reverted, hash-confirmed identical to baseline.

**Record correction (§5, §6):** both sections previously claimed no
`# type: ignore` was used anywhere in this feature. That was false — see the
corrections inline in §5 and §6 above.

**Result:** `./init.sh` exit 0. `ruff format --check`, `ruff check`, `mypy
--strict` (28 source files, no issues) and `pytest` (71 passed, +1 for the new
F1 self-test) all green. Feature left `in_progress` for the reviewer.
