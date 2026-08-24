# Review — feature 4 (recipe_model)

**Verdict:** CHANGES_REQUESTED

> **Superseded in part, 2026-08-24 (`G-82`).** After this review ran, the human
> struck `IngredientCategory.VEGETARIAN` and replaced it with `VEGETABLE`, and
> added `EGGS`. Rows M4 and M19 below describe mutants built on the old member
> name; they are left verbatim as the record of what was actually executed on
> 2026-08-23. Nothing else in this document is affected -- the mutants they
> describe still die for the same reason under the new vocabulary.

Reviewer session 2026-08-23. `./init.sh` exit 0, 70 backend tests (55 before
this feature), every gate green — the feature is *correct*; it is rejected on
**two surviving mutants**, both of which are missing assertions rather than
broken code. No source file needs to change to clear this review; two tests do.

---

## Requirement coverage (FR → R)

- FR-LIB-03:  [x] covered by R1, R2, R3, R4, R5, R6, R7, R8, R15
- FR-LIB-05:  [x] covered by R3, R9, R15
- FR-CAND-07: [x] covered by R10, R11, R12, R13
- FR-MENU-04: [x] covered by R14

Every `R<n>` cites at least one id from the `covers` array and no other. No
requirement invented. `requirements.md` §"Scope note" correctly fences the two
shared ids (`FR-LIB-05` with features 3/12, `FR-MENU-04` with feature 20).

## Test traceability (R → test)

- R1:  [x] `test_recipe_is_frozen`
- R2:  [x] `test_recipe_fields_are_exactly_the_fixed_shape`
- R3:  [ ]  ← **half-verified.** `test_ingredient_fields_are_exactly_the_fixed_shape`
  proves the field *names*; nothing proves `unit`'s declared type is `Unit`.
  See mutant M12 below.
- R4:  [x] `test_the_ingredient_category_vocabulary_is_closed`
- R5:  [x] `test_parse_category_resolves_every_code`
- R6:  [x] `test_parse_category_rejects_a_value_outside_the_list`
- R7:  [x] `test_unknown_ingredient_category_is_a_planner_error`
- R8:  [x] `test_planner_core_has_one_ingredient_category_vocabulary`
- R9:  [x] `test_planner_core_never_constructs_unit_directly` (with the gap in M7)
- R10: [x] `test_meal_snapshot_is_a_distinct_frozen_type`
- R11: [x] `test_snapshot_copies_the_recipes_content`
- R12: [x] `test_meal_snapshot_holds_no_reference_to_the_recipe` — passes, but
  see the observation below: it did **not** notice mutant M10; the suite caught
  that one through R10's field-parity assertion instead.
- R13: [x] `test_editing_or_deleting_the_library_recipe_leaves_an_existing_snapshot_unchanged`
- R14: [x] `test_snapshot_copies_the_recipes_content`
- R15: [x] `test_the_shared_kernel_modules_are_ascii_only`

## Tasks complete

T1–T25: all `[x]` in `specs/recipe_model/tasks.md`. None skipped, none
unjustified. T21 carries an inline implementation note recording a deviation
from its own spec text; that deviation is assessed under M6/M7 below.

## Invariants exercised (`docs/verification.md` Level 4)

- **Snapshots (`FR-CAND-07`, `G-05`)**: [x]
  `test_editing_or_deleting_the_library_recipe_leaves_an_existing_snapshot_unchanged`
  (`backend/core/tests/domain/test_recipe.py:100`). This is a real property
  test, not a frozen-dataclass tautology — verified by mutant M2: making
  `snapshot()` write a constant category equal to the *edited* recipe's
  category (`legume` → `meat`) fails it on `test_recipe.py:114` with
  `- legume / + meat`. That is exactly the G-05 violation shape, and the test
  asserts against the **original** values after both the edit and the delete.
- **Normalised matching (`G-56`)**: [x] not re-implemented here; the feature-3
  fold guard is live against the new modules — mutant M3 (a `.lower()` inside
  `parse_category`) was killed by `test_planner_core_has_one_name_fold` as well
  as by the R6 test.
- No other §4 invariant is touched by this feature.

## Mutation testing — 11 killed / 13 run

| # | `R<n>` | Mutation | Result |
|---|---|---|---|
| M1 | R11, R14 | `snapshot()` returns `procedure=()` instead of copying | [x] killed by `test_snapshot_copies_the_recipes_content` + the G-05 test |
| M2 | R13 (G-05) | `snapshot()` returns `category=IngredientCategory.MEAT`, i.e. the edited recipe's value | [x] killed by the G-05 test alone (`test_recipe.py:114`) |
| M3 | R6 | `parse_category` weakened to `value.strip().lower() == ...` | [x] killed by `test_parse_category_rejects_a_value_outside_the_list` **and** `test_planner_core_has_one_name_fold` |
| M4 | R6, R7 | guard clause dropped: `raise` → `return IngredientCategory.VEGETARIAN` | [x] killed by the R6 and R7 tests |
| M5 | R4 | sixth member `DAIRY = "dairy"` added to the closed enum | [x] killed by `test_the_ingredient_category_vocabulary_is_closed` (+2) |
| M6 | R9 | real `return Unit("g")` planted in `domain/recipe.py` | [x] killed by `test_planner_core_never_constructs_unit_directly` |
| M7 | R9 | the same construction placed on a class-header line | [ ] **MUTANT SURVIVED** — see F1 |
| M8 | R8 | second vocabulary (`class RecipeIngredientCategory` + `MEAT = ...`) in `recipe.py` | [x] killed by `test_planner_core_has_one_ingredient_category_vocabulary` |
| M9 | R2 | `kcal: int = 0` added to `Recipe` (G-68, G-36) | [x] killed by `test_recipe_fields_are_exactly_the_fixed_shape` |
| M10 | R12 | `origin: Recipe \| None = None` added to `MealSnapshot`, set by `snapshot()` | [x] killed — **but by R10's parity assertion, not by R12's own test** (see observation O1) |
| M11 | R1 | `@dataclass(frozen=True)` → `@dataclass()` on `Recipe` | [x] killed by `test_recipe_is_frozen` |
| M12 | R3 | `Ingredient.unit` re-declared `unit: str` | [ ] **MUTANT SURVIVED** — see F2 |
| M13 | R15 | non-ASCII `ñ` inserted into `recipe.py`'s docstring | [x] killed by `test_the_shared_kernel_modules_are_ascii_only` |

- Tree restored: [x] `git status --porcelain` matches the pre-review state
  byte-for-byte; all three mutated files verified against SHA-256 baselines
  after every single mutation, and again at the end. Re-ran `ruff format
  --check`, `ruff check`, `mypy` and `pytest` after the final restore: green,
  70 passed.

---

## Blocking findings

### F1 — the T21 class-header exclusion is broader than specified and hides a genuine R9 violation

`backend/core/tests/test_shared_kernel_guards.py:60`

```python
CLASS_HEADER_LINE = re.compile(r"^\s*class\s+\w+\(")
```

`_matches_excluding_class_headers` (`:74`) skips **the entire line** of **every**
class header in `planner_core`, not just `class Unit(StrEnum):`.

**The re-spec itself is sound and R9 still catches what it exists to catch.**
Mutant M6 — a plain `return Unit("g")` in `domain/recipe.py` — was caught and
reported with file and line number. The implementer's diagnosis in
`progress/impl_recipe_model.md` §4 is correct: the literal-substring reading in
`design.md` §7 does fire on feature 3's `class Unit(StrEnum):` and on
`raise UnknownUnit(value)`, and `\bUnit\(` is the right fix for the second.

**The gap is the width of the exclusion, not its existence.** Both `design.md`
§7 and the guard's own comment (`:58-59`) describe the exemption as *"the
enum's own `class Unit(StrEnum):`"* — one specific declaration. The implemented
regex exempts any `class X(`. Planting this legal, runtime-valid PEP 487 class
keyword argument in `domain/recipe.py`:

```python
class _Sneaky(_Base, unit=Unit("g")):
```

leaves the full suite green — **70 passed**. A direct enum construction, exactly
what R9 forbids "anywhere in the `planner_core` package", passes the guard.

Realism is admittedly low; a class keyword argument is not a shape this
codebase reaches for. But the leader asked whether the exclusion is broad
enough to hide a genuine violation, and the demonstrated answer is yes. The
exclusion should match what its own comment claims it matches, with a self-test
proving a construction on a non-`Unit` class header is still caught.

### F2 — `Ingredient.unit`'s declared type is unverified; re-declaring it `str` passes every gate

`backend/core/src/planner_core/domain/recipe.py:22`,
test at `backend/core/tests/domain/test_recipe.py:47`

Mutating `unit: Unit` to `unit: str` (keeping the `Unit` import live so the
change is not caught incidentally as F401) leaves **all four backend gates
green**: `pytest` 70 passed, `mypy` strict "no issues in 28 source files",
`ruff check` clean, `ruff format --check` clean.

Under that mutation, this type-checks clean under `mypy --strict`:

```python
Ingredient(name="patatas", quantity=2, unit="kg")
```

— verified with a throwaway probe module, since removed. An unlisted unit
reaches an `Ingredient`, defeating `FR-LIB-05`, R3's `unit:
planner_core.domain.units.Unit` clause, and the `feature_list.json` acceptance
criterion *"Ingredient quantities only accept units from the fixed unit list"*.

The cause is that T14 (`test_ingredient_unit_is_the_shared_unit_enum`) asserts
the value it just constructed with:

```python
ingredient = Ingredient(name="arroz", quantity=100, unit=parse_unit("g"))
assert isinstance(ingredient.unit, Unit)
assert ingredient.unit is Unit.GRAM
```

`parse_unit("g")` returns a `Unit` whatever the field is annotated as, so the
assertions hold for any annotation. This is precisely the *"asserts the code
does what it does"* shape `docs/verification.md` Level 5 exists to surface.

The suite already knows the idiom that would close this — R12's test introspects
declared types via `dataclasses.fields(...)[i].type` (`test_recipe.py:97`). The
same introspection applied to `Ingredient` would have killed the mutant.

### F3 — `progress/impl_recipe_model.md` states no `# type: ignore` was used; two are present

- `backend/core/tests/domain/test_recipe.py:32` — `recipe.name = "Otro"  # type: ignore[misc]`
- `backend/core/tests/domain/test_recipe.py:74` — `taken.name = "Otro"  # type: ignore[misc]`

`impl_recipe_model.md` §5 says *"No `# type: ignore` was used"* and §6's boundary
table records *"`# type: ignore` | None used"*. Both are inaccurate. These are
the first two in the whole backend — `rg "type:\s*ignore" backend` returns only
these two lines.

`CHECKPOINTS.md` C4 requires mypy clean *"with no new `# type: ignore`"*, so the
box cannot be ticked as written. The suppression is defensible in intent (the
line must be illegal for mypy for the runtime assertion to mean anything, and
neither `docs/conventions.md` nor `docs/verification.md`'s *"instead of fixing
the type"* anti-pattern squarely covers it) — but the report must not claim the
opposite of what the file contains. Either drop the suppressions (`setattr(recipe,
"name", "Otro")` raises `FrozenInstanceError` at runtime without a mypy error)
or correct §5 and §6 and let the human rule on C4.

---

## Non-blocking observations

**O1 — R12's own test is weaker than its name.**
`test_meal_snapshot_holds_no_reference_to_the_recipe` (`test_recipe.py:89`)
checks a three-name denylist (`id`, `recipe`, `source`) and `field.type !=
"Recipe"`. Under mutant M10 — a field `origin: Recipe | None = None` holding
the source recipe — **that test passes**: `"origin"` is not in the denylist and
the annotation string is `"Recipe | None"`, not `"Recipe"`. Confirmed by running
it in isolation: `1 passed`. The mutant was still killed, by R10's
`fields(MealSnapshot) == fields(Recipe)` parity assertion, so this is not a
surviving mutant — but R12's coverage is incidental, and a substring check
(`"Recipe" in field.type`) would make it real.

**O2 — the ingredient-category and unit vocabularies are consumed, not
re-implemented.** Verified in all three directions the leader asked about:
`domain/recipe.py:8` imports `Unit` from `planner_core.domain.units`; no second
fold exists (`test_planner_core_has_one_name_fold` scans every module and M3
proved it live against the new code); no second category enum exists (M8 proved
that guard live). `domain/ingredient_category.py` correctly does **not** import
`recipe.py`, keeping feature 6's dependency clean per `design.md` §8 F.

**O3 — no `tiempo` finding raised**, per instruction. Deliberately absent, not
assessed.

## Boundaries

- No Terraform / `*.tfvars` / CI files generated: [x] `git status --porcelain`
  shows none; `init.sh` §4 guardrail green.
- No architecture decision from `docs/architecture.md` §2 made silently: [x] the
  one §2.1 *decide-in-a-spec* item (the ingredient-category list) was proposed in
  `design.md` §4 and approved by the human at the gate on 2026-08-23.
- Frozen requirement docs unmodified: [x] `git status --porcelain docs/` empty.
- `feature_list.json` untouched by the implementer: [x] the only diff is the
  leader's `pending` → `in_progress` on feature 4.
- `core` runtime dependencies: [x] `backend/core/pyproject.toml` still
  `dependencies = []`.

## Layering (`docs/architecture.md` §3.1)

- `domain/` importing `application/`, `ports/`, an adapter, a handler or an AWS
  SDK: [x] none. `recipe.py` imports `dataclasses` + two `domain` modules;
  `ingredient_category.py` imports `enum` + `domain.errors`.
- `core` importing an AWS SDK or a Lambda package: [x] none.
- `core` runtime dependency declared: [x] none.
- Ambient time: [x] `backend/core/tests/test_no_ambient_time.py` unmodified and
  green — no exemption widened, no allowance loosened, no self-check deleted.
- `application/` importing an adapter or handler: [x] n/a, no `application/`
  piece added.
- Adapter imported outside a `wiring.py`: [x] n/a, no adapter.

## Conventions (`docs/conventions.md`)

- Naming, typing, error handling: [x] `UnknownIngredientCategory(PlannerError)`
  carries only the rejected value; `parse_category` raises rather than returning
  `None`.
- Language rule: [x] no user-facing Spanish string literal outside a messages
  module. The Spanish recipe names in `test_recipe.py` are fixture *data* for an
  es-ES domain, not UI copy, and match feature 3's approved precedent.
- **Comment ceiling — three lines, tests included**: [x] scanned mechanically
  for runs of `#` lines across `backend/core`. Longest run in this feature's
  files is **two** lines (`ingredient_category.py:42-43`, `test_recipe.py:63-64`,
  `test_shared_kernel_guards.py:41-42, 47-48, 54-55, 58-59`). No comment
  reproduces a document; all point at one. Clean.
- `# type: ignore`: see F3.

## Checkpoints

- C1: [x] harness complete, frozen docs unmodified, `./init.sh` exit 0.
- C2: [x] one `in_progress`; every `blocked` has a reason; `current.md` describes
  this session.
- C3: [x] layering, two Lambda packages, zero `core` deps, no stray `print()`,
  no context-free TODO.
- C4: [ ] ← `ruff` and `pytest` green and `mypy` clean, but two **new**
  `# type: ignore` comments (F3), which C4 names explicitly.
- C5: [x] no stray files; my probe module was removed and the tree verified.
  (`backend/tests/contract/` still empty — the documented feature-14 deferral,
  unchanged by this feature.)
- C6: [ ] ← spec folder complete, strict EARS, every `R<n>` cites an `FR-*`,
  every `FR-*` in `covers` appears, all tasks `[x]` — but *"every `R<n>` is
  covered by at least one concrete test"* fails for R3 (F2).
- C7: [x] no agent-generated IaC/CI, no §2 decision taken, no invented
  requirement, frozen docs unedited.

---

## Required changes

1. **Add an assertion that `Ingredient.unit`'s declared type is `Unit`** (F2,
   R3). Mutating it to `str` currently passes `pytest`, `mypy --strict`, `ruff
   check` and `ruff format`. Use the `dataclasses.fields(...)[i].type`
   introspection the R12 test already uses. Do **not** change `recipe.py` — the
   source is correct; the mutation was reverted.
2. **Narrow the T21 class-header exclusion to the declaration it documents**
   (F1, R9), and add a self-test proving a `Unit(` construction on a class
   header that is *not* `class Unit(...)` is still reported.
3. **Reconcile `progress/impl_recipe_model.md` §5 and §6 with the two
   `# type: ignore[misc]` comments at `test_recipe.py:32` and `:74`** (F3) —
   either remove the suppressions or correct the report, and let the human rule
   on `CHECKPOINTS.md` C4.
4. *(Optional, non-blocking)* Strengthen R12's test so it notices a
   differently-named field typed `Recipe | None` (O1).

---

# Re-review — feature 4 (recipe_model), 2026-08-24

**Verdict:** APPROVED

Second reviewer session, scoped to the fix round for **F1, F2 and F3**. `./init.sh`
exit 0, **71 backend tests** (70 before; +1 for the new F1 self-test). **6 of 6
mutations killed (100%)** — including re-runs of the two round-1 survivors, both
of which now die. The 2026-08-23 verdict above stands as history; nothing in it
was rewritten.

**O1 was explicitly out of scope for this round** (leader's decision) and is
**not** treated as a regression. It remains open, unchanged, and non-blocking.

---

## The three findings

### F1 — CLOSED

`backend/core/tests/test_shared_kernel_guards.py:61`

```python
CLASS_HEADER_LINE = re.compile(r"^\s*class\s+Unit\(")
```

Narrowed from `^\s*class\s+\w+\(` to `^\s*class\s+Unit\(`. It now exempts exactly
the one declaration its own comment (`:58-60`) and `tasks.md` T21's implementation
note describe — feature 3's `class Unit(StrEnum):` base-list parens — and nothing
else.

The self-test `test_the_class_header_exclusion_only_hides_units_own_declaration`
(`:206-214`) pins both halves via `tmp_path`: `class _Sneaky(_Base, unit=Unit("g")):`
is reported, `class Unit(StrEnum):` is not. Proved live, not just read — mutation
M15 below plants a runtime-valid PEP 487 keyword-argument construction in
`domain/recipe.py` and the guard now reports it with file and line.

### F2 — CLOSED

`backend/core/tests/domain/test_recipe.py:54`

```python
assert typing.get_type_hints(Ingredient)["unit"] is Unit
```

The **declared** type is now asserted, not merely the runtime value of something
`parse_unit` produced. The two original runtime assertions were kept, correctly —
the new line adds, it does not replace. `typing.get_type_hints` is the right tool
here and is stronger than the `dataclasses.fields(...)[i].type` introspection I
suggested: under `from __future__ import annotations` the latter yields the
*string* `"Unit"`, which a same-named shadow would satisfy, while `get_type_hints`
resolves the annotation to the object and `is Unit` compares identity against the
imported enum.

Re-ran the exact mutation the finding named — mutation M14 below. It now **fails**.

### F3 — CLOSED

`rg "type:\s*ignore" backend/` returns **no matches**. Both suppressions are gone.
`progress/impl_recipe_model.md` §5 and §6 now carry dated corrections stating the
truth (the original claim was false), and the round-2 section records the removal.
The report no longer contradicts the file. `CHECKPOINTS.md` C4 is tickable.

---

## Ruling on the `__setattr__` judgement call

`test_recipe.py:33` and `:80` — `recipe.__setattr__("name", "Otro")`.

**Acceptable, and it should stay.** The gate conflict the implementer describes is
real; I verified it rather than taking it on trust, with an isolated probe module
outside the repo (since deleted), run against this repo's own settings
(`select = ["E", "F", "I", "UP", "B"]`, `strict = true`):

- `setattr(r, "name", "Otro")` → `B010 Do not call setattr with a constant
  attribute value`, whose autofix suggestion is literally `r.name = "Otro"`.
- `r.name = "Otro"` → rejected by `mypy --strict` on a frozen dataclass.
- `r.__setattr__("name", "Otro")` → clean under `ruff format`, `ruff check` **and**
  `mypy --strict`, with no suppression of any kind.

The two gates genuinely point at each other, and my suggested fix walked straight
into it. The chosen resolution is the honest one: it is not an evasion of either
gate, it is the precise expression of what the test means — *invoke the frozen
dataclass's own `__setattr__` and require it to raise*. Calling a dunder directly
is mildly unusual style, but every alternative is worse. `# noqa: B010` and
`# type: ignore` are both suppressions, and C4 bans the second by name. The one
other gate-clean option I found — binding the attribute name to a variable so
`B010`'s constant-value trigger never fires (verified clean under both gates) — is
indirection whose only purpose is dodging a linter, which reads worse than the
dunder it would replace.

Decisive point: it is **proved live**, not assumed. Mutations M16 and M17 remove
`frozen=True` from `Recipe` and from `MealSnapshot` respectively, and each makes
its test fail with `DID NOT RAISE FrozenInstanceError`. The idiom still catches the
defect it exists to catch. That is the only thing that settles the question.

## Mutation testing — 6 killed / 6 run (100%)

| # | `R<n>` | Mutation | Result |
|---|---|---|---|
| M14 | R3 (F2) | `Ingredient.unit` re-declared `unit: str` in `recipe.py:22` | [x] killed — `test_ingredient_unit_is_the_shared_unit_enum`, `test_recipe.py:54`, `assert <class 'str'> is Unit`. **Round-1 survivor M12 now dies.** |
| M15 | R9 (F1) | `class _Sneaky(_Base, unit=Unit("g")):` (runtime-valid; `_Base` defines `__init_subclass__`) appended to `recipe.py` | [x] killed — `test_planner_core_never_constructs_unit_directly` reports `recipe.py:70`. **Round-1 survivor M7 now dies.** |
| M16 | R1 (F3 idiom) | `@dataclass(frozen=True)` → `@dataclass()` on `Recipe` | [x] killed — `test_recipe_is_frozen`, `DID NOT RAISE FrozenInstanceError` |
| M17 | R10 (F3 idiom) | `@dataclass(frozen=True)` → `@dataclass()` on `MealSnapshot` | [x] killed — `test_meal_snapshot_is_a_distinct_frozen_type`, `test_recipe.py:79` |
| M18 | R13, R11, R14 (G-05) | `snapshot()` writes `category=IngredientCategory.MEAT` instead of copying | [x] killed by **two** tests — the G-05 invariant test (`- legume / + meat`) and `test_snapshot_copies_the_recipes_content` |
| M19 | R6, R7 | `parse_category`'s `raise` replaced by `return IngredientCategory.VEGETARIAN` | [x] killed by both `test_parse_category_rejects_a_value_outside_the_list` and `test_unknown_ingredient_category_is_a_planner_error` |

M14 and M15 are the round-1 survivors re-run verbatim. M16 and M17 exist because F3
changed *how* the frozen tests assert, and that had to be re-proved rather than
assumed. M18 re-checks the §4 invariant after the fix round, M19 the error path.

- **Tree restored: [x]** `git status --porcelain` is byte-identical to the
  pre-review state (4 modified, 7 untracked, same paths). All five feature files
  verified against `git hash-object` baselines taken before the first mutation and
  again after the last: `recipe.py 0c2b97f2`, `ingredient_category.py 412ac03f`,
  `test_shared_kernel_guards.py c8b091e8`, `test_recipe.py 5e6bfad c`,
  `test_ingredient_category.py d79afe5a`. Re-ran the suite after the final revert:
  **71 passed**. Both probe modules lived in the scratchpad, outside the repo, and
  were deleted. No git write command was run; `feature_list.json` untouched.

## Requirement coverage (FR → R)

Unchanged from round 1 and re-verified against `specs/recipe_model/requirements.md`:

- FR-LIB-03:  [x] R1, R2, R3, R4, R5, R6, R7, R8, R15
- FR-LIB-05:  [x] R3, R9, R15
- FR-CAND-07: [x] R10, R11, R12, R13
- FR-MENU-04: [x] R14

## Test traceability (R → test)

- R1:  [x] `test_recipe_is_frozen` (idiom changed; killing power re-proved by M16)
- R2:  [x] `test_recipe_fields_are_exactly_the_fixed_shape`
- R3:  [x] `test_ingredient_fields_are_exactly_the_fixed_shape` **+
  `test_ingredient_unit_is_the_shared_unit_enum`** — was `[ ]`, closed by F2 / M14
- R4:  [x] `test_the_ingredient_category_vocabulary_is_closed`
- R5:  [x] `test_parse_category_resolves_every_code`
- R6:  [x] `test_parse_category_rejects_a_value_outside_the_list`
- R7:  [x] `test_unknown_ingredient_category_is_a_planner_error`
- R8:  [x] `test_planner_core_has_one_ingredient_category_vocabulary`
- R9:  [x] `test_planner_core_never_constructs_unit_directly` **+
  `test_the_class_header_exclusion_only_hides_units_own_declaration`** — the M7 gap
  is closed
- R10: [x] `test_meal_snapshot_is_a_distinct_frozen_type` (re-proved by M17)
- R11: [x] `test_snapshot_copies_the_recipes_content`
- R12: [x] `test_meal_snapshot_holds_no_reference_to_the_recipe` (see O1, still open)
- R13: [x] `test_editing_or_deleting_the_library_recipe_leaves_an_existing_snapshot_unchanged`
- R14: [x] `test_snapshot_copies_the_recipes_content`
- R15: [x] `test_the_shared_kernel_modules_are_ascii_only`

## Tasks complete

T1–T25 all `[x]` in `specs/recipe_model/tasks.md`; zero `[ ]` remain, checked
mechanically. T21's inline implementation note is now accurate — it describes a
class-header exclusion for `class Unit(StrEnum):` specifically, which is what the
code now does.

## Invariants exercised (`docs/verification.md` Level 4)

- **Snapshots (`FR-CAND-07`, `G-05`)**: [x] re-proved this round by M18, which two
  separate tests catch.
- **Normalised matching (`G-56`)**: [x] not re-implemented here; feature 3's fold
  guard remains live against the new modules.
- No other §4 invariant is touched by this feature.

## Boundaries

- No Terraform / `*.tfvars` / CI files generated: [x] `init.sh` §4 guardrail green,
  `git status` shows none.
- No architecture decision from §2 made silently: [x] unchanged from round 1.
- Frozen requirement docs unmodified: [x] `git status --porcelain docs/` empty.
- `feature_list.json` untouched by the fix round: [x] the only diff remains the
  leader's earlier `pending` → `in_progress`.

## Layering (`docs/architecture.md` §3.1)

The fix round changed **test files only** — `recipe.py` and `ingredient_category.py`
are byte-identical to what round 1 cleared. Every layering conclusion carries over:
no `application`/`ports`/adapter/handler/AWS import in `domain/`, no AWS SDK or
Lambda package in `core`, `dependencies = []` in `backend/core/pyproject.toml`.
`backend/core/tests/test_no_ambient_time.py` is unmodified and green — no exemption
widened, no allowance loosened, no self-check deleted.

## Conventions (`docs/conventions.md`)

- Comment ceiling — three lines, tests included: [x] the longest new run is the
  three-line `CLASS_HEADER_LINE` comment (`test_shared_kernel_guards.py:58-60`),
  exactly at the ceiling. No comment reproduces a document.
- Language rule: [x] no user-facing Spanish literal outside a messages module.
- `# type: ignore`: [x] none anywhere in `backend/`.

## Checkpoints

- C1: [x] harness complete, frozen docs unmodified, `./init.sh` exit 0.
- C2: [x] exactly one `in_progress` (feature 4); every `blocked` carries a reason;
  `current.md` describes this session.
- C3: [x] layering, two Lambda packages, zero `core` deps, no stray `print()`, no
  context-free TODO.
- C4: **[x]** ← was `[ ]`. `ruff format`, `ruff check`, `mypy --strict` and `pytest`
  (71) all green, and **no `# type: ignore` exists anywhere in `backend/`**, new or
  old. The `Clock` contract-suite deferral noted under C4 belongs to feature 14 and
  is unaffected by this feature.
- C5: [x] no stray files; both probe modules lived outside the repo and are deleted;
  `progress/history.md` carries the previous session's entry; feature 4 correctly
  left `in_progress` for the leader to close.
- C6: **[x]** ← was `[ ]`. Spec folder complete, strict EARS, every `R<n>` cites an
  `FR-*`, every `FR-*` in `covers` appears, all tasks `[x]`, and **every `R<n>` is
  now covered by a concrete test** — R3 was the sole gap and F2 closed it.
- C7: [x] no agent-generated IaC/CI, no §2 decision taken, no invented requirement,
  frozen docs unedited.

## Non-blocking observations

**O1 — still open, deliberately out of scope.**
`test_meal_snapshot_holds_no_reference_to_the_recipe` (`test_recipe.py:95`) still
uses a three-name denylist plus `field.type != "Recipe"`, so a field named `origin`
annotated `Recipe | None` slips past it; R12's real coverage remains incidental, via
R10's field-parity assertion. Excluded from this round by the leader — recorded, not
counted against the verdict. A substring test (`"Recipe" in field.type`) closes it
whenever it is picked up.

**O2 (new, cosmetic) — one stale docstring.** `_matches_excluding_class_headers`
(`test_shared_kernel_guards.py:76`) still reads *"skips a class statement's
base-class line entirely"*, which described the old wide regex; the behaviour is now
narrower. The constant's own comment (`:58-60`) is accurate and the new self-test
pins the behaviour exactly, so nothing here can hide a defect. Worth a five-word
edit next time the file is open; not worth a round trip on its own.

## Required changes

**None.** All three blocking findings are closed, each verified by a mutation rather
than by reading the diff. Feature 4 `recipe_model` is ready for the leader to close
as `done`.
