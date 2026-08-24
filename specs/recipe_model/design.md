# recipe_model — Design

> Feature 4 · tier 1 · pure `planner_core.domain`
> Read `requirements.md` first. This document records the technical decisions
> taken before any code is written, per `docs/specs.md`.
> Depends on feature 3 `text_and_units` (closed) — this feature **consumes**
> `planner_core.domain.units.{Unit, parse_unit, UnknownUnit}` and never
> re-derives them.

## 0. The invariant this feature exists to protect

`docs/architecture.md` §4 invariant 1:

> **Snapshots, not references.** A recipe added to a menu stores a *copy* of
> the recipe content. Later library edits or deletes must never retroactively
> mutate a live or archived week. (`FR-CAND-07`, `G-05`)

Everything in §§4–5 below serves that sentence. The rest of the feature — the
`Recipe` content shape and the `IngredientCategory` vocabulary — exists
because `FR-CAND-07` needs something concrete to copy, and `FR-LIB-03`/
`FR-LIB-05` define exactly what that something is.

---

## 1. Scope boundary — what this feature owns of each `FR-*`

| Requirement | Owned **here** | Deferred to |
|---|---|---|
| `FR-LIB-03` | The `Recipe` content shape (name, ingredients, tools, procedure) and the `IngredientCategory` vocabulary plus its single entry point `parse_category`. The absence of cuisine, difficulty and kcal. | The authoring-flow dropdown and library category filter — **feature 20 `frontend_spa`**. AI output validation against the same vocabulary — **feature 12 `ai_output_validation`**. Category counts as prompt instructions and post-generation verification — **feature 11 `ai_prompt_builder`**, **feature 6 `rules_model`** (which reuses `IngredientCategory`, never redeclares it — R8). |
| `FR-LIB-05` | `Ingredient.unit` typed as the shared `Unit` (feature 3), and the guarantee that nothing in `planner_core` constructs a `Unit` member without going through `parse_unit` (R9). | The dropdown itself — feature 20. Validating AI output against the list and reporting the es-ES failure — feature 12. |
| `FR-CAND-07` | `MealSnapshot`, a value object structurally distinct from `Recipe`, and `snapshot(recipe) -> MealSnapshot`. | Attribution (`añadidoPor`), which meal a snapshot belongs to, and persistence identity (`idPlato`) — **feature 5 `week_plan_model`** wraps a `MealSnapshot` into a `Candidate` carrying those. Servings (`numeroComensales`) and prep time (`tiempo`) appear in `docs/data_model.md` §1's item types but no `FR-*` in this feature's `covers` array assigns them here; inventing them now would be exactly what `docs/specs.md` forbids. `numeroComensales` is `FR-AI-13`'s territory (feature 11, `G-64`). |
| `FR-MENU-04` | The content shape a detail view renders: ingredients with quantities, tools, procedure — identical on `Recipe` and on `MealSnapshot` (R14). | The click-to-open navigation and the view itself — **feature 20**. |

**The reusable artefacts this feature adds.** `Recipe`, `Ingredient`,
`IngredientCategory`, `MealSnapshot` and `snapshot()`. Feature 5 constructs
`Candidate` around `MealSnapshot`; feature 6 reuses `IngredientCategory` for
rule definitions; features 11/12 reuse it for AI prompts and output
validation. None of them may redeclare it.

---

## 2. Layering

`docs/architecture.md` §3: `domain/` is *"Pure logic. No IO, no AWS SDK, no
framework, no clock."* Every piece here is a plain value or a pure function of
plain values — no port, no clock, no IO, no persistence identity.

| Piece | Layer | Why |
|---|---|---|
| `Ingredient`, `Recipe`, `MealSnapshot`, `snapshot` | `planner_core/domain/recipe.py` | Pure value objects and a pure function between them. |
| `IngredientCategory`, `parse_category`, `UnknownIngredientCategory` | `planner_core/domain/ingredient_category.py` | Pure closed vocabulary and its validation — same shape as feature 3's `units.py`, kept in its own module because feature 6 depends on it independently of `Recipe`. |

No `application/` piece: nothing here orchestrates a port or a repository.
`core` keeps `dependencies = []` — `dataclasses` and `enum` are standard
library.

---

## 3. Files

### Created

| Path | Contents |
|---|---|
| `backend/core/src/planner_core/domain/recipe.py` | `Ingredient`, `Recipe`, `MealSnapshot`, `snapshot`. |
| `backend/core/src/planner_core/domain/ingredient_category.py` | `IngredientCategory`, `UnknownIngredientCategory`, `parse_category`. |
| `backend/core/tests/domain/test_recipe.py` | R1, R2, R3, R9, R10, R11, R12, R13, R14. |
| `backend/core/tests/domain/test_ingredient_category.py` | R4, R5, R6, R7. |

### Modified

| Path | Change |
|---|---|
| `backend/core/tests/test_shared_kernel_guards.py` | Add a fourth scan, `test_planner_core_has_one_ingredient_category_vocabulary` (R8), built to the same self-testing discipline as the existing three. Extend `test_the_shared_kernel_modules_are_ascii_only`'s asserted module set to include `domain/recipe.py` and `domain/ingredient_category.py` (R15). |

Nothing else changes. `planner_core/domain/errors.py` already declares
`PlannerError` (feature 2) — `UnknownIngredientCategory` subclasses it and
changes nothing there. Nothing is added to `backend/core/tests/support/`:
this feature implements no port and needs no fake.

---

## 4. The ingredient-category vocabulary — the `docs/architecture.md` §2.1 item

`docs/architecture.md` §2.1 lists *"the literal ingredient-category list for
the rules (`G-69`, supersedes `G-63`; `FR-RULE-04`)"* as a **decide-in-a-spec**
item, not an architecture-pending one — the same status feature 3 found the
unit list in. `FR-RULE-04`'s own text supplies the candidate values: *"meat,
fish, carbohydrates, legumes, vegetarian, …"*. The trailing ellipsis is the
open part; the five named terms are not.

### Proposed vocabulary

| Member | Code (stored in `tipoAlimento`) |
|---|---|
| `IngredientCategory.MEAT` | `"meat"` |
| `IngredientCategory.FISH` | `"fish"` |
| `IngredientCategory.CARBOHYDRATE` | `"carbohydrate"` |
| `IngredientCategory.LEGUME` | `"legume"` |
| ~~`IngredientCategory.VEGETARIAN`~~ | ~~`"vegetarian"`~~ — **removed** by `G-82` |
| `IngredientCategory.VEGETABLE` | `"vegetable"` — **added** by `G-82` |
| `IngredientCategory.EGGS` | `"eggs"` — **added** at the gate |

**Amended at the gate (2026-08-24, `G-82`).** The human answered gate question
1 below by closing the ellipsis at **six** members, not five: `eggs` was added
(an addition inside `FR-RULE-04`'s "…", needing no requirement change), and
`vegetarian` was **struck and replaced by `vegetable`** — which did need one,
since the frozen text names `vegetarian` explicitly. The rationale is recorded
in `docs/gaps_and_resolutions.md` Part R. The two paragraphs immediately below
are the `spec_author`'s original recommendation, kept as written; the paragraph
on `VEGETARIAN`'s axis is what the gate decision acted on.

**Why exactly these five and no more.** They are the only terms `FR-RULE-04`
itself names. Adding a sixth (dairy, egg, vegetable, …) would be inventing
scope no `FR-*` grants — precisely what `docs/specs.md` forbids of a
`spec_author`. The ellipsis is left for the human to close explicitly at the
gate (§9), not for this document to guess at.

**Singular nouns, plural source text.** `FR-RULE-04` writes "carbohydrates"
and "legumes"; the enumeration members are singular (`CARBOHYDRATE`,
`LEGUME`) for the same reason `Unit.GRAM` is singular — a member names one
thing, not a count of it. Cosmetic, not a scope decision.

**English, ASCII codes; the es-ES label is feature 20's.** Same reasoning as
`Unit` (`specs/text_and_units/design.md` §4): identifiers and stored technical
values are English per `docs/conventions.md` § *Language policy*; Castilian
rendering lives in the frontend messages module.

**`VEGETARIAN` sits beside `MEAT` and `FISH` on a different axis.** The
frozen text lists it as a peer category anyway, and `G-69`'s own reasoning
accepts exactly this: *"'lentejas con chorizo' is filed under whichever
category prevails, so the counts approximate composition and are not a
nutritional measure."* A dish is filed under whichever single member the
person authoring it judges predominant — the ambiguity is inherent in
`FR-RULE-04`'s own list, not introduced here. Recorded as **gate question 1**
so the human can adjust the closed set if the ellipsis was meant to open it
further. **Answered:** the human removed the mixed axis outright (`G-82`) —
every member now names a predominant ingredient, and `vegetable` covers the
dishes `vegetarian` used to absorb. The accepted cost is that a *"vegetarian
meals per week"* rule is no longer expressible.

**Where the vocabulary is stored.** `tipoAlimento` on `DatosPlatoBiblioteca`
and `DatosPlatoSemana` (`docs/data_model.md` §1). A category code is an
attribute value, not a key segment, so `docs/data_model.md` §2 needs no
addition — same conclusion feature 3 reached for `unidad`.

---

## 5. The snapshot — what "decoupled" means at the domain layer

`docs/data_model.md` §5.4 already states the persistence-layer half of this:

> Week meals are **snapshots** (`FR-CAND-07`), so deleting a library recipe
> cannot dangle one — editing or deleting the library entry leaves existing
> snapshots untouched.

At the domain layer, with no persistence identity in play yet, "decoupled"
means two things, both testable without any storage:

1. **A distinct type.** `MealSnapshot` is not `Recipe`. `docs/data_model.md`
   §1 already models the library entry (`DatosPlatoBiblioteca`) and the week
   item (`DatosPlatoSemana`) as two different item types — the domain mirrors
   that split so an adapter can never be tempted to persist one where the
   other belongs, and no later refactor can quietly make `snapshot()` an
   identity function that just returns its argument.
2. **No held reference.** `MealSnapshot` carries no field of type `Recipe`
   (R12) and no id. `snapshot()` copies field values into a new object; it
   does not wrap or point at the source `Recipe`. Because every field
   (`tuple[Ingredient, ...]`, `tuple[str, ...]`, an enum member) is itself
   immutable, copying the values is total and sufficient — there is no
   mutable container left to alias.

**Why this makes the G-05 test meaningful rather than tautological.** Since
`Recipe` is `frozen`, nothing can mutate one in place — every "edit" the
product describes is really *"a different `Recipe` object now sits where the
library kept the old one."* The domain-level proof of G-05 is therefore: take
a snapshot, then discard or replace the binding the "library" held to the
source `Recipe`, and show the snapshot's fields are unaffected. `tasks.md`
T19 models "the library" as the smallest fixture that can vary independently
of the snapshot — a plain `dict[str, Recipe]` local to the test, not a new
port. Introducing a repository port for this would need `application/` and a
fake, which `docs/architecture.md` §3.1 reserves for orchestration this
feature does not do.

---

## 6. Signatures

### `planner_core/domain/ingredient_category.py`

```python
class IngredientCategory(StrEnum):
    MEAT = "meat"
    FISH = "fish"
    CARBOHYDRATE = "carbohydrate"
    LEGUME = "legume"
    VEGETABLE = "vegetable"
    EGGS = "eggs"


class UnknownIngredientCategory(PlannerError):
    """Raised when a value is not a member of the fixed ingredient-category list."""

    value: str

    def __init__(self, value: str) -> None: ...


def parse_category(value: str) -> IngredientCategory:
    """Resolve a category code to its member, or raise UnknownIngredientCategory."""
```

Exact match only, no `normalize()`, no case folding — same reasoning as
`parse_unit` (`specs/text_and_units/design.md` §9 D): the value reaches this
function from a dropdown or from AI output already instructed to use the
fixed codes, so a mismatch is a caller bug, not free text to be forgiving
about.

### `planner_core/domain/recipe.py`

```python
@dataclass(frozen=True)
class Ingredient:
    name: str
    quantity: float
    unit: Unit


@dataclass(frozen=True)
class Recipe:
    name: str
    ingredients: tuple[Ingredient, ...]
    tools: tuple[str, ...]
    procedure: tuple[str, ...]
    category: IngredientCategory


@dataclass(frozen=True)
class MealSnapshot:
    name: str
    ingredients: tuple[Ingredient, ...]
    tools: tuple[str, ...]
    procedure: tuple[str, ...]
    category: IngredientCategory


def snapshot(recipe: Recipe) -> MealSnapshot:
    """Return a MealSnapshot decoupled from recipe (FR-CAND-07, G-05)."""
```

**`Ingredient.unit` takes an already-resolved `Unit`, never a raw string.**
Mirrors `SlotRef.slot: MealSlot` in `domain/calendar.py`: the typed field
carries no internal parsing, and the one path from an untrusted string to a
`Unit` stays `parse_unit` (feature 3), so a caller holding a raw code (a
dropdown value, deserialized AI output) writes
`Ingredient(name=..., quantity=..., unit=parse_unit(raw))`. This is what R9
guards: nothing in this module may call `Unit(raw)` directly, which would
raise a bare `ValueError` instead of the documented `UnknownUnit` and would
duplicate the one validated entry point feature 3 built.

**No runtime coercion of list-like inputs to tuples.** Fields are typed
`tuple[...]`; a caller passing a `list` is a `mypy --strict` failure, not a
runtime one — the same convention `IsoWeek`/`WeekDay` already use for their
tuple-returning properties. Adding an `__post_init__` coercion would be
defensive code against a caller error the type checker already catches
(`docs/conventions.md` § *Python style*, strict typing).

**`quantity: float`.** No bound or positivity check. `docs/gaps_and_resolutions.md`'s
"examined and rejected" list names *"field-level validation minutiae (name
lengths, quantity bounds, …)"* as out of MVP scope; inventing one here would
contradict that entry.

### Exceptions

| Exception | Base | Raised when |
|---|---|---|
| `UnknownIngredientCategory` | `PlannerError` | `parse_category` receives a value that is not exactly a member's code (R6). |

Carries the rejected value and nothing else, for the same reason
`UnknownUnit` does (`specs/text_and_units/design.md` §6): the es-ES rejection
text belongs to whichever feature owns the user-facing flow that calls this
(feature 12's AI-output validation, feature 20's dropdown), and that messages
module does not exist yet.

---

## 7. The two mechanical guards this feature adds

Extending `backend/core/tests/test_shared_kernel_guards.py`, built to the
self-testing discipline that module already established (`design.md` of
feature 3, §7):

| Guard | Scans for | Self-test |
|---|---|---|
| R8 — one category vocabulary | a class definition whose name contains `IngredientCategory`, and assignments to `MEAT`/`FISH`/`CARBOHYDRATE`/`LEGUME`/`VEGETABLE`/`EGGS`, outside `domain/ingredient_category.py` | Asserted to match inside `domain/ingredient_category.py`; scanned file list asserted non-empty and to contain `domain/recipe.py`. |
| R9 — no direct `Unit(...)` construction | the literal pattern `Unit(` across the whole `planner_core` package | Asserted to match nothing today (the only current construction path is `parse_unit`'s own `for unit in Unit:` loop, which does not call `Unit(`); if a future call site legitimately needs it, that is exactly the review friction R9 exists to create. |
| R15 — ASCII only (extension) | `domain/recipe.py` and `domain/ingredient_category.py` added to the existing asserted module set | The existing assertion already fails loudly (a hard-coded set literal) if a new module is added without updating it — the extension itself is proof the guard is live. |

---

## 8. Rejected alternatives

**A. Give `Recipe` a sixth category, or leave the set open-ended.**
~~Rejected — see §4. `FR-RULE-04` names exactly five terms; adding more invents
scope, and an open-ended set is not a *fixed, predefined set*, which the
requirement's own words demand.~~

**Half of this was overtaken at the gate (2026-08-24, `G-82`).** The *sixth
category* half is **no longer rejected**: the human closed `FR-RULE-04`'s
ellipsis at six members — `MEAT`, `FISH`, `CARBOHYDRATE`, `LEGUME`,
`VEGETABLE`, `EGGS` — and that set is what the code implements. The rejection
above was a `spec_author` declining to *invent* scope, which was correct for a
spec author and was never a prohibition on the human exercising the choice
`docs/architecture.md` §2.1 reserves for them.

The *open-ended set* half **still stands, unchanged**: the set remains closed
and fixed, because `FR-RULE-04` demands a "fixed, predefined set" and
`FR-AI-04` verifies counts against it. Adding a member is a gate decision with
a numbered gap behind it, not something a later feature may do in passing.

**For features 6, 11 and 12**, which reuse this vocabulary: the count is six,
the source of truth is `planner_core/domain/ingredient_category.py`, and none
of you may redeclare it (`R8` guards this).

**B. Let `Ingredient.unit` accept a raw `str` and resolve it internally via
`parse_unit` in `__post_init__`.**
Rejected. It would put a second call site of `parse_unit` behind an implicit
coercion, one call ambient enough that a reviewer scanning for "does this
value come from a trusted source" cannot tell from the constructor call
alone. Requiring the caller to resolve the value explicitly
(`Ingredient(unit=parse_unit(raw))`) keeps the boundary visible at the call
site, matching `SlotRef`/`MealSlot`'s existing convention (§6).

**C. Make `snapshot()` an identity function — `MealSnapshot = Recipe`, or
`snapshot(recipe) -> Recipe` returning its argument unchanged.**
Rejected — see §5. It would satisfy the "unchanged" half of G-05 (nothing
here is mutable anyway) but not the "value object decoupled from the library
entry" wording of the acceptance criterion, and it collapses the two-item-type
distinction `docs/data_model.md` §1 draws between `DatosPlatoBiblioteca` and
`DatosPlatoSemana` back into one, inviting exactly the kind of adapter code
that would need to re-derive which one a value actually is.

**D. Model `MealSnapshot` as a repository-backed entity with an id, and prove
decoupling through a fake `RecipeRepository` port.**
Rejected. This feature is tier 1, pure domain (`docs/architecture.md` §3.1);
persistence identity (`idPlato`) is a key-format concern of
`docs/data_model.md` §2, assigned at the adapter boundary, not here. A port
and a fake for this would be layering theatre — `docs/architecture.md` §2
gives no `FR-*` reason to reach for one, and `text_and_units` (feature 3, §2)
rejected the same move for the same reason.

**E. Give `Ingredient` and `Recipe` an explicit step-number field
(`numeroPaso`) instead of relying on tuple order for `procedure`.**
Rejected. `docs/data_model.md` §3 already establishes the pattern of deriving
order from position rather than storing a redundant counter (*"week ordering
falls out of the sort key … no padding is required"*). `procedure`'s tuple
index is the step number; storing it twice is the kind of denormalization
§6 of `docs/data_model.md` warns against, generalized to the domain layer.
Mapping a tuple index to the persisted `numeroPaso` attribute is an adapter
concern, out of scope here.

**F. Put `IngredientCategory` in `domain/recipe.py` alongside `Recipe`,
one module.**
Rejected, same reasoning as feature 3's alternative I for `units.py`/
`text.py`: feature 6 (`rules_model`) needs `IngredientCategory` independently
of `Recipe` (a rule references a category count, not a recipe), so the two
belong in separate modules with no import from `ingredient_category.py` back
to `recipe.py`.

**G. Enforce a non-empty `ingredients` tuple, or a non-blank `name`.**
Rejected as invention — no `FR-*` in this feature's `covers` array says a
recipe must have at least one ingredient or a non-blank name. `docs/specs.md`
forbids inventing a requirement no `FR-*` covers; if this is ever wanted, it
is a finding for a future spec, not a default to assume now.

---

## 9. Boundary checks and gate questions

### Boundary checks

- **`docs/architecture.md` §2 (pending, human-owned):** nothing here needs P2,
  P3, P4, P5 or P6. No message format is emitted (§6), so P5 is untouched even
  by proximity.
- **§2.1 decide-in-a-spec items:** exactly one is touched here, **the
  ingredient-category list** (proposed in §4). The unit list was feature 3's;
  the servings count (`G-64`) belongs to feature 11.
- **Frozen docs:** none modified. `docs/data_model.md` needs no change — a
  category code is an attribute value, not one of the five key formats of §2.
- **User-facing strings:** none, enforced by R15.
- **Runtime dependencies:** none added; `planner-core` keeps
  `dependencies = []`.
- **Requirements invented:** none. Every `R<n>` cites `FR-LIB-03`,
  `FR-LIB-05`, `FR-CAND-07` or `FR-MENU-04` — all four in this feature's
  `covers` array, no others.

### Gate questions for the human

1. ~~**The ingredient-category vocabulary (§4).** Recommended: exactly the
   five terms `FR-RULE-04` names.~~ **Answered 2026-08-24** — the human closed
   the ellipsis at six: `MEAT`, `FISH`, `CARBOHYDRATE`, `LEGUME`, `VEGETABLE`,
   `EGGS`. `VEGETARIAN` was struck as a diet label on a foreign axis; see
   `docs/gaps_and_resolutions.md` `G-82` (Part R).
2. **`Ingredient.unit` requires a pre-resolved `Unit`, never a raw string
   (§6, rejected alternative B).** Confirming the boundary stays at the call
   site rather than moving into `Ingredient.__post_init__`.
3. **No servings, prep-time or attribution field on `Recipe` or
   `MealSnapshot` (§1).** Confirming these remain feature 11's
   (`numeroComensales`, `G-64`) and feature 5's (`añadidoPor`) to add, not
   this feature's.
