# recipe_model — Requirements

> Feature 4 · tier 1 · `sdd: true`
> Covers: `FR-LIB-03`, `FR-LIB-05`, `FR-CAND-07`, `FR-MENU-04`
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen
> requirement ids it implements and is verifiable by at least one concrete test
> that asserts a value.

## Purpose in one sentence

Give the library its immutable content shape — name, ingredients (quantity +
the fixed unit), tools, procedure, exactly one predominant ingredient category
— and the value-object copy taken when that content enters a week, so a later
library edit or delete can never retroactively rewrite a live or archived menu
(`docs/architecture.md` §4 invariant 1).

## One `SHALL` per requirement

Every `R<n>` below carries exactly one `SHALL` or one `SHALL NOT`, counted
mechanically rather than by eye. `specs/week_calendar/requirements.md` records
four combined requirements as an accepted deviation; that is not a pattern to
copy, and this file does not repeat it.

## Scope note on the four covered requirements

`FR-LIB-05` is shared with feature 3 (`text_and_units`, closed) and with
feature 12 (`ai_output_validation`, pending). This feature owns only the point
where a recipe's ingredient shape **consumes** the fixed unit vocabulary —
it declares no second vocabulary and adds no parsing entry point.
`FR-MENU-04` is a UI requirement (opening a detail view on click); this
feature owns only the domain content shape that view renders — the click
behaviour itself belongs to feature 20. `design.md` §1 draws both lines.

---

## R1
Implements: FR-LIB-03

The system SHALL declare `Recipe` as `@dataclass(frozen=True)` in
`planner_core.domain.recipe`.

## R2
Implements: FR-LIB-03

The system SHALL declare `Recipe`'s fields as exactly `name: str`,
`ingredients: tuple[Ingredient, ...]`, `tools: tuple[str, ...]`,
`procedure: tuple[str, ...]` and `category: IngredientCategory`, admitting no
cuisine, difficulty or kcal attribute.

## R3
Implements: FR-LIB-03, FR-LIB-05

The system SHALL declare `Ingredient` as `@dataclass(frozen=True)` in
`planner_core.domain.recipe` with fields exactly `name: str`,
`quantity: float` and `unit: planner_core.domain.units.Unit`.

## R4
Implements: FR-LIB-03

The system SHALL declare `IngredientCategory` as a closed enumeration in
`planner_core.domain.ingredient_category` whose members are exactly `MEAT`,
`FISH`, `CARBOHYDRATE`, `LEGUME`, `VEGETABLE` and `EGGS` (`G-82` closed
`FR-RULE-04`'s trailing ellipsis at these six and struck `VEGETARIAN`).

## R5
Implements: FR-LIB-03

WHEN a value equals the code of a member of `IngredientCategory` exactly, the
system SHALL resolve it to that member through `parse_category(value)`.

## R6
Implements: FR-LIB-03

IF a value is not exactly the code of a member of `IngredientCategory`, THEN
the system SHALL raise `UnknownIngredientCategory`.

## R7
Implements: FR-LIB-03

The system SHALL derive `UnknownIngredientCategory` from `PlannerError`.

## R8
Implements: FR-LIB-03

The system SHALL NOT declare a second ingredient-category vocabulary anywhere
in the `planner_core` package.

## R9
Implements: FR-LIB-05

The system SHALL NOT call the `Unit` constructor directly (`Unit(...)`)
anywhere in the `planner_core` package.

## R10
Implements: FR-CAND-07

The system SHALL declare `MealSnapshot` as `@dataclass(frozen=True)` in
`planner_core.domain.recipe`, a type distinct from `Recipe`, with fields
exactly `name`, `ingredients`, `tools`, `procedure` and `category`.

## R11
Implements: FR-CAND-07

The system SHALL provide `snapshot(recipe: Recipe) -> MealSnapshot` in
`planner_core.domain.recipe`, constructing a new `MealSnapshot` from
`recipe`'s field values.

## R12
Implements: FR-CAND-07

The system SHALL NOT declare, on `MealSnapshot`, any field holding a
reference to the `Recipe` instance it was built from.

## R13
Implements: FR-CAND-07

WHEN the library recipe a snapshot was taken from is later edited or deleted,
the system SHALL leave that snapshot's content unchanged.

## R14
Implements: FR-MENU-04

WHEN `snapshot(recipe)` is called, the system SHALL produce a `MealSnapshot`
whose `ingredients`, `tools` and `procedure` equal the source `Recipe`'s
`ingredients`, `tools` and `procedure` exactly.

## R15
Implements: FR-LIB-03, FR-LIB-05

The system SHALL restrict the source modules added by this feature
(`domain/recipe.py`, `domain/ingredient_category.py`) to ASCII characters.

---

## Coverage map

| Frozen requirement | Covered by |
|---|---|
| `FR-LIB-03` | R1, R2, R3, R4, R5, R6, R7, R8, R15 |
| `FR-LIB-05` | R3, R9, R15 |
| `FR-CAND-07` | R10, R11, R12, R13 |
| `FR-MENU-04` | R14 |

| `feature_list.json` acceptance criterion | Covered by |
|---|---|
| Recipe is a frozen dataclass carrying name, ingredients, tools, procedure | R1, R2 |
| Recipe carries exactly one `tipoAlimento` from the fixed FR-RULE-04 set (FR-LIB-03, G-69) | R2, R4, R5, R6, R7 |
| Recipe carries no cuisine, difficulty or kcal attribute (G-68, G-36) | R2 |
| Ingredient quantities only accept units from the fixed unit list (FR-LIB-05) | R3, R9 |
| A snapshot function produces a value object decoupled from the library entry (FR-CAND-07) | R10, R11, R12 |
| Test proves editing or deleting the library recipe leaves an existing snapshot unchanged (G-05) | R13 |

Supporting requirements not demanded by a single criterion but required by the
documents the criteria rest on: R8 (one category vocabulary, mirroring
feature 3's R16 for `Unit` — feature 6 `rules_model` reuses the same
enumeration and must not redeclare it), R9 (the fixed-unit-list guarantee only
holds if nothing bypasses `parse_unit`'s raise, mirroring feature 3's R2/R16
discipline), R14 (FR-MENU-04's content-fidelity half — the click/navigation
half is feature 20's), R15 (no user-facing text in backend domain code —
`docs/conventions.md` § *Language policy*, same reasoning as feature 3's R22).
