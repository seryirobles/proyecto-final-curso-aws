# shopping_aggregation — Design

> Feature 7 · tier 1 · pure `planner_core.domain`
> Read `requirements.md` first. This document records the technical decisions
> taken before any code is written, per `docs/specs.md`.
> Depends on feature 3 `text_and_units` (closed, `normalize()`, `Unit`) and
> feature 5 `week_plan_model` (closed, `SlotContents`, `definitive()`) and
> reuses feature 2 `week_calendar` (closed, `current_week`, `next_week`,
> `slots_from`) — this feature **consumes** all three and re-derives none of
> their vocabulary.

## 0. The invariant this feature exists to protect

`docs/architecture.md` §4:

> **5. Compound operations are idempotent.** AI generation (`FR-AI-08`),
> shopping re-sync (`FR-SHOP-10`, `G-54`) and week rollover (`FR-MENU-08`,
> `G-61`) must converge to one result under retry, double-click or partial
> failure. Recompute-from-source beats diff-and-patch.

> **6. Definitive meals derive the shopping list. Candidates never do.**
> (`FR-SHOP-05`, `G-04`)

`docs/gaps_and_resolutions.md`, `G-72`:

> The MVP stores no auto/manual marker and no manual-override state.

Every function below is subordinate to these three sentences: the result is
recomputed whole from the in-scope definitive meals on every call rather than
patched (§5), a slot without a definitive contributes nothing (§6), and the
result item carries no attribute a later press could contradict or that would
need updating (§6, §8).

---

## 1. Scope boundary — what this feature owns of each `FR-*`

See `requirements.md`'s scope-note table for the full per-requirement split.
Two lines deserve emphasis because they are easy to get wrong:

**`FR-SHOP-10`'s "applies it as an additive merge... so repeated presses
converge" clause is not implemented here.** This feature's "repeated
invocations converge" (R7) is the simpler, purity-level fact that a pure
function called twice with the same arguments returns the same result — it
says nothing about merging into a *persisted* list that also holds checked
items, manual items and prior unchecked auto items. That merge, and the
"serialized" half `G-77` explicitly left "unresolved, deliberately," are
feature 8's (`shopping_list_state`).

**`FR-SHOP-03`'s button and fixed unit list are not implemented here.** The
`Unit` vocabulary and `normalize()` already shipped in feature 3
(`text_and_units`, closed); this feature only *uses* them. The UI trigger
belongs to feature 8 / feature 20.

**The reusable artefact this feature adds.** `required_shopping_items`, the
pure top-level composition, plus its two building blocks
(`in_scope_slots`, `aggregate_ingredients`) — each independently testable and
each answering exactly one of R1/R2, R3/R4, and R5/R6. No later feature needs
to redeclare "which slots are in scope for shopping" or "how two ingredients
merge" — feature 8 consumes this feature's result tuple directly as the
"required" side of its outstanding-quantity computation (`FR-SHOP-06`).

---

## 2. Layering

`docs/architecture.md` §3: `domain/` is *"Pure logic. No IO, no AWS SDK, no
framework, no clock."* Every function below is a pure transformation of plain
values — no port, no clock, no id generator, no IO.

| Piece | Layer | Why |
|---|---|---|
| `in_scope_slots`, `definitive_ingredients`, `aggregate_ingredients`, `required_shopping_items` | `planner_core/domain/shopping.py` | Pure functions over plain values (`date`, `Mapping[SlotRef, SlotContents]`, `Ingredient`); no IO, no ambient state, no clock. |

No `application/` piece. Like `week_plan_model` and `rules_model`, this
feature's own logic needs no "now" beyond a caller-supplied `date` — the one
place a real clock is read is `application/live_weeks.py`'s
`resolve_live_weeks(clock)` (feature 2), which is **not** this feature's
concern: a future caller (feature 8's use case, not yet built) reads
`LiveWeeks.today` and passes it straight into `required_shopping_items`,
exactly the "`domain/` takes a plain date, `application/` reads the clock
once" split `docs/specs.md`'s own R1–R3 example illustrates.

---

## 3. Files

### Created

| Path | Contents |
|---|---|
| `backend/core/src/planner_core/domain/shopping.py` | `in_scope_slots`, `definitive_ingredients`, `aggregate_ingredients`, `required_shopping_items`. |
| `backend/core/tests/domain/test_shopping.py` | R1–R8. |

### Modified

None. `shopping.py` declares no dataclass, no enum, no closed vocabulary of
its own — it consumes `Ingredient` (feature 4), `Unit` (feature 3),
`normalize` (feature 3), `SlotRef`/`current_week`/`next_week`/`slots_from`
(feature 2) and `SlotContents`/`definitive` (feature 5), restating none of
them. `backend/core/tests/test_shared_kernel_guards.py`'s
`SHARED_KERNEL_MODULES` tuple needs no addition (mirrors
`specs/rules_model/design.md` §7 and `specs/week_plan_model/design.md` §7 —
same reasoning, a fourth time). No `pyproject.toml` change: no dependency
added, `planner-core` keeps `dependencies = []`.

---

## 4. `docs/architecture.md` §2.1 items

None of the four named items (unit list, ingredient-category list, servings
count, the now-removed per-user cap) are touched here. The unit list this
feature relies on (`Unit`, `FR-SHOP-03`) was already decided and shipped by
feature 3; this feature imports it and proposes no value of its own.

---

## 5. Composition over one monolithic function

`FR-SHOP-05`'s scope rule and `FR-SHOP-03`'s merge rule are independent
concerns — one is about *which ingredients feed the aggregation*, the other
about *how two ingredients combine*. Two shapes could deliver the "auto-item
set" the feature description names:

**A. One function**, `required_shopping_items(plans, today)`, doing slot
scoping, definitive lookup and merging inline in a single body.

**B. Three small pure functions composed by a fourth** (chosen here):
`in_scope_slots(today)` answers R1/R2 alone; `definitive_ingredients(plans,
slots)` answers R3/R4 alone, taking an explicit slot sequence rather than
recomputing scope itself; `aggregate_ingredients(ingredients)` answers R5/R6
alone, taking a flat `Iterable[Ingredient]` with no notion of slots or weeks
at all; `required_shopping_items(plans, today)` composes the three. Each
acceptance criterion in `requirements.md`'s coverage map becomes a test
against the one function that actually implements it, rather than every test
having to construct a full `plans` mapping and a real `today` to exercise, say,
the merge rule alone. This is the same decomposition `rules_model` used for
`max_selectable_count` / `available_days_for_pin` / `available_days_to_disable`
(`specs/rules_model/design.md` §8, rejected alternative E) — independent pure
functions, one per question, composed by callers that need more than one
answer.

---

## 6. Signatures

```python
"""Deterministic aggregation of definitive meals in scope into a required-item set."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date

from planner_core.domain.calendar import SlotRef, current_week, next_week, slots_from
from planner_core.domain.candidate import SlotContents, definitive
from planner_core.domain.recipe import Ingredient
from planner_core.domain.text import normalize
from planner_core.domain.units import Unit


def in_scope_slots(today: date) -> tuple[SlotRef, ...]: ...
    # slots_from(current_week(today), today) + slots_from(next_week(today), today)
    # (R1, R2)

def definitive_ingredients(
    plans: Mapping[SlotRef, SlotContents], slots: Iterable[SlotRef]
) -> tuple[Ingredient, ...]: ...
    # for each slot (in order): plans.get(slot) -> definitive(plan) -> extend with
    # candidate.meal.ingredients; a missing slot or an absent definitive contributes
    # nothing (R3, R4)

def aggregate_ingredients(ingredients: Iterable[Ingredient]) -> tuple[Ingredient, ...]: ...
    # merge on (normalize(name), unit); sum quantities; no unit conversion (R5, R6)

def required_shopping_items(
    plans: Mapping[SlotRef, SlotContents], today: date
) -> tuple[Ingredient, ...]: ...
    # aggregate_ingredients(definitive_ingredients(plans, in_scope_slots(today)))
    # (R7, R8 as a consequence of returning Ingredient — see rejected alternative B)
```

**`in_scope_slots` calls `slots_from` twice with the same `today`, once per
week**, exactly mirroring `application/live_weeks.py::LiveWeeks.slots_in_scope`'s
own comment: *"today always precedes the next week's Monday, so all fourteen
of its slots survive without a second branch."* This feature cannot call
`LiveWeeks.slots_in_scope` itself — `LiveWeeks` lives in `application/`, and
`docs/architecture.md` §3.1 rule 1 forbids `domain/` importing `application/`
— so the union both weeks need is re-expressed here at the domain layer, over
the same `slots_from` primitive, not a second implementation of it (rejected
alternative A, §8).

**`definitive_ingredients` takes an explicit `slots: Iterable[SlotRef]`
parameter rather than a `today: date`.** This is what lets R3/R4 be tested
against a hand-built slot list with no calendar arithmetic in the test at
all, and it is what lets `required_shopping_items` compose two independently
correct pieces instead of one function re-deriving scope internally.

**`aggregate_ingredients` iterates its input once, tracking first-occurrence
order.** The merge key is `(normalize(ingredient.name), ingredient.unit)`; the
kept display `name` for a key is the **first** raw spelling seen for it, and
the quantity is the running sum. Because `definitive_ingredients` already
walks `in_scope_slots`' day-then-slot order and each meal's `ingredients`
tuple in its own fixed order, iterating this way needs no explicit sort step
to be deterministic (R7) — see rejected alternative D, §8, for the
alternative considered.

**No exception type is added.** Every function here is total over its
declared parameter types: an empty `plans`, an empty `slots`, or an empty
`ingredients` iterable all produce an empty result tuple, never a raised
error. `docs/architecture.md` §4 invariant 12 ("functions that can fail raise
named domain exceptions... they do not return `None`") does not require an
exception where nothing can fail; `required_shopping_items` never returns
`None` either way — an empty tuple is exactly the honest answer for "nothing
is required yet."

---

## 7. Why R8 needs no new type, and what it actually guards

`aggregate_ingredients` and `required_shopping_items` return
`tuple[Ingredient, ...]` — the same `Ingredient` feature 4 already declared
in `planner_core.domain.recipe`, with fields exactly `name`, `quantity`,
`unit` (`specs/recipe_model`, `test_ingredient_fields_are_exactly_the_fixed_
shape`). Reusing it, rather than declaring a feature-local `RequiredItem`
twin with the identical three fields, is what makes R8 ("no field other than
name, quantity and unit") true **by construction**: there is no second
dataclass this feature could accidentally grow a `source` or `week` field on.
See rejected alternative B (§8) for the type this replaces, and gate question
1 for why this is flagged rather than assumed.

---

## 8. Rejected alternatives

**A. Depend on `application.live_weeks.LiveWeeks` / `resolve_live_weeks`
directly instead of re-deriving the current+next union from `today` inside
`domain/shopping.py`.**
Rejected. `docs/architecture.md` §3.1 rule 1 forbids `domain/` importing
`application/` at all — this is not a style preference to weigh, it is the
layer boundary the reviewer enforces mechanically. `in_scope_slots(today)`
therefore calls the same `current_week` / `next_week` / `slots_from`
primitives `resolve_live_weeks` and `LiveWeeks.slots_in_scope` already call,
rather than calling those two application-layer names.

**B. Declare a feature-local `RequiredItem` dataclass (`name`, `quantity`,
`unit`) instead of reusing `recipe.Ingredient` as the aggregation result
type.**
Considered, not chosen — see gate question 1. The two shapes would be
field-for-field identical, and `Ingredient` already carries the exact
"quantity of a named ingredient in the fixed unit vocabulary" meaning the
aggregation result needs. A new type would exist only to have a different
name, at the cost of a second import path for every downstream caller
(feature 8) that has to decide which one to use where `Ingredient` already
appears (inside `MealSnapshot.ingredients`).

**C. Add the current+next-week union helper to `planner_core/domain/
calendar.py` (feature 2, closed) instead of keeping it local to
`shopping.py`.**
Rejected, following the precedent `rules_model` already set for its own
`WEEKDAYS` constant (`specs/rules_model/design.md` §8, rejected alternative
C) and `week_plan_model` set for not retrofitting `recipe.py` (`specs/
week_plan_model/design.md` §8, rejected alternative E): modifying a different,
already-closed feature's file from inside this feature's spec blurs exactly
the boundary `docs/specs.md` exists to keep clear. Nothing about "current
week today-onward plus the whole next week" is a calendar primitive other
features need — `FR-AI-11` (feature 10/11, not yet built) targets *one*
selected live week at a time, never the union of both (`docs/requirements.md`
line 110), so there is no second consumer to justify moving this into
`calendar.py`.

**D. Keep the display name from the *last* occurrence of a normalized key,
or re-derive a normalized display form, instead of the *first* occurrence.**
Considered, not chosen — see gate question 2. No `FR-*` decides which raw
spelling survives a merge; `docs/requirements.md`'s `FR-SHOP-03` only fixes
*that* names merge, never which one a shopper reads afterward. First
occurrence was chosen because it needs no extra bookkeeping beyond the
insertion-ordered dict `aggregate_ingredients` already builds, and it means
the item's displayed name is always one some user actually typed (never a
synthesized or re-cased form), consistent with `normalize()`'s own docstring
promise of "no rewriting of the display name the user actually typed."

---

## 9. Boundary checks and gate questions

### Boundary checks

- **`docs/architecture.md` §2 (pending, human-owned):** nothing here needs
  P2, P3, P4, P5 or P6. This feature is pure `domain/` with no port, no
  adapter, no Lambda.
- **§2.1 decide-in-a-spec items:** none proposed here; the one this feature
  relies on (`Unit`) was already decided and shipped by feature 3 (§4).
- **Frozen docs:** none modified. `docs/data_model.md`'s `DatosIngredienteLista`
  shape (`nombreIngrediente, cantidad, unidad, isComprado`) is feature 8's
  concern — this feature's result type has no `isComprado` and no persistence
  identity, matching `docs/data_model.md` line 428 ("re-sync re-derives [the
  normalized name] each press; not worth an attribute").
- **User-facing strings:** none. This feature produces no Castilian text and
  raises no new exception with a message.
- **Runtime dependencies:** none added; `planner-core` keeps
  `dependencies = []`.
- **Requirements invented:** none. Every `R<n>` cites one or more of
  `FR-SHOP-03`, `FR-SHOP-05`, `FR-SHOP-10` — all three in this feature's
  `covers` array, no others.

### Gate questions for the human

1. **Reuse `recipe.Ingredient` as the aggregation result item type rather
   than declaring a new `RequiredItem` (§7, §8 rejected alternative B).**
   Recommended: reuse, since the shape is field-for-field identical and it
   makes R8 ("no extra field") true by construction rather than by
   discipline. Alternative: a distinct `RequiredItem` dataclass, purely for
   readability — "this is a shopping requirement, not a recipe line" — with
   no behavioral difference either way. What turns on it: whether feature 8
   imports `Ingredient` from `recipe.py` or a new name from `shopping.py`
   when it wires the outstanding-quantity computation against this feature's
   result.

2. **First-occurrence-wins for the kept display name when two ingredients'
   normalized names match but their raw spelling differs (§6, §8 rejected
   alternative D).** Recommended: first occurrence in scope order (day, then
   slot, then a meal's own ingredient order) — deterministic, no extra sort,
   never a synthesized name. Alternative: none is decided by any `FR-*`; a
   human ruling here becomes precedent the way "domain takes a date, never a
   Clock" did for feature 2. What turns on it: which of two differently-cased
   or differently-spaced spellings a shopper actually sees on the list feature
   8 eventually renders.

3. **New module `planner_core/domain/shopping.py`, anticipating feature 8
   extending it with the persisted, checkable shopping-list shapes.**
   Recommended: yes — feature 8 covers the rest of the same `FR-SHOP-*`
   family and will need to import `required_shopping_items` regardless of
   where it lives; naming the module now avoids a rename later. Alternative:
   a narrower module name (e.g. `shopping_aggregation.py`) that leaves
   feature 8 free to choose its own module identity independently. What turns
   on it: purely a file-naming precedent, no behavioral difference.
