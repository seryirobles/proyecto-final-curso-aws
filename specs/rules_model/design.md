# rules_model — Design

> Feature 6 · tier 1 · pure `planner_core.domain`
> Read `requirements.md` first. This document records the technical decisions
> taken before any code is written, per `docs/specs.md`.
> Depends on feature 2 `week_calendar` (closed, `MealSlot`) and feature 4
> `recipe_model` (closed, `IngredientCategory`) — this feature **consumes**
> both and re-derives neither.

## 0. The invariant this feature exists to protect

`docs/gaps_and_resolutions.md`, `G-20`:

> Constrain the dropdown options so contradictory combinations cannot be
> composed... Warn-and-remove (rather than blocking the delete) keeps
> library management unobstructed while never leaving a broken rule behind
> silently.

Every operation below is subordinate to this: a `RuleSet` that exists at all
is satisfiable by construction (§5), and a pin whose recipe is gone is
surfaced and removable, never left dangling (§6).

---

## 1. Scope boundary — what this feature owns of each `FR-*`

See `requirements.md`'s scope-note table for the full per-requirement split.
Two lines deserve emphasis because they are easy to get wrong:

**`FR-RULE-07`'s satisfiability check stops at the rules, not the week's
actual occupancy.** `G-71` (feature 12's territory) settled that a runtime
shortfall caused by slots already holding a definitive meal is `FR-AI-12`
per-slot messaging, explicitly *not* a rewrite of `FR-RULE-07`. This feature
validates only the three rule collections against each other — never against
any week's live content, and never against a clock.

**`FR-RULE-04`'s ingredient-category list is not proposed here.** `G-69`
(supersedes `G-63`) and `G-82` already fixed the six-member set, and feature
4 already shipped it as `planner_core.domain.ingredient_category
.IngredientCategory`. This feature imports it; `backend/core/tests
/test_shared_kernel_guards.py::test_planner_core_has_one_ingredient_category
_vocabulary` already anticipates `rules_model` doing exactly that and fails
on a second declaration.

**The reusable artefact this feature adds.** `RuleSet`, `CategoryCountRule`,
`PinRule`, `RemovePinsResult`, and the operations that construct, mutate and
query them. No later tier-1 feature in this backlog needs to redeclare a
rule shape — feature 11/12 (AI generation, not yet built) consumes a
`RuleSet` value (the shared one, or one produced by `apply_override`)
exactly as this feature returns it.

---

## 2. Layering

`docs/architecture.md` §3: `domain/` is *"Pure logic. No IO, no AWS SDK, no
framework, no clock."* Every function below is a pure transformation of
plain values — no port, no clock, no id generator, no IO.

| Piece | Layer | Why |
|---|---|---|
| `RuleSet`, `CategoryCountRule`, `PinRule`, `RemovePinsResult`, `InvalidWeekday`, `UnsatisfiableRuleSet`, and every function in §6 | `planner_core/domain/rules.py` | Pure value objects and pure functions between them; no IO, no ambient state, no clock (R2 forbids even accepting one). |

No `application/` piece. Like feature 5 (`week_plan_model`), nothing here
needs "now" — disabled days and pins name a generic weekday (`1..7`), not a
calendar date, so there is nothing for a `Clock` to resolve. This feature's
tests need no fake beyond plain values.

---

## 3. Files

### Created

| Path | Contents |
|---|---|
| `backend/core/src/planner_core/domain/rules.py` | `RuleSet`, `CategoryCountRule`, `PinRule`, `RemovePinsResult`, `InvalidWeekday`, `UnsatisfiableRuleSet`, `DAYS_PER_WEEK`, `SLOTS_PER_DAY`, `TOTAL_SLOTS`, `WEEKDAYS`, `set_category_count`, `remove_category_count`, `set_pin`, `remove_pin`, `disable_day`, `enable_day`, `max_selectable_count`, `available_days_for_pin`, `available_days_to_disable`, `remove_pins_referencing`, `apply_override`. |
| `backend/core/tests/domain/test_rules.py` | R1–R22. |

### Modified

None. `rules.py` declares no second vocabulary of an already-guarded kind —
it declares two *new* dataclasses (`CategoryCountRule`, `PinRule`) that are
not enums and carry no fixed member list, so
`backend/core/tests/test_shared_kernel_guards.py`'s `SHARED_KERNEL_MODULES`
tuple needs no addition (see §7). No `pyproject.toml` change: no dependency
added, `planner-core` keeps `dependencies = []`.

---

## 4. `docs/architecture.md` §2.1 items

**The ingredient-category list is not re-proposed here.** It is the one
§2.1 item this feature's `covers` array touches (`FR-RULE-04`), and it was
already decided and shipped by feature 4 (`G-69`, amended `G-82`): six
members — `meat, fish, carbohydrate, legume, vegetable, eggs`. `R3` cites
`IngredientCategory` by import; no new value is proposed.

The `14`-slot figure appearing in `R6` and `R14` (`TOTAL_SLOTS` in §6) is
**not** a §2.1 proposal — it is arithmetic over two facts already fixed
elsewhere: seven days per ISO week (`FR-MENU-02`) and two meal slots per day
(`MealSlot`, feature 2). No human sign-off is being requested for "14";
it is derived, not chosen.

---

## 5. `RuleSet`'s own constructor is the satisfiability gate

`FR-RULE-07` requires the rule set to stay "consistent and satisfiable" and
names two contradictions explicitly: category totals exceeding the slots
left after disabled days, and a pin on a disabled day. Two shapes could
enforce this:

**A. Validate inside each mutating function** (`set_category_count`,
`set_pin`, `disable_day`, ...), independently. Every function that can
produce a new combination has to remember to re-check both rules. Four
functions, one invariant, four chances to forget it or check it slightly
differently.

**B. Validate once, in `RuleSet.__post_init__`** (chosen here). Every
mutating function in §6 does nothing but build a new `RuleSet` from the old
one's fields plus one change, and returns it — `__post_init__` runs on that
construction and raises `UnsatisfiableRuleSet` if the *result* would be
contradictory, regardless of which function produced it or whether it was
produced by hand. "Cannot be composed" (`FR-RULE-07`'s own words) becomes a
property of the type, not a discipline every call site has to uphold. This
is the same shape `week_plan_model` chose for "at most one definitive" — see
`specs/week_plan_model/design.md` §5 — generalized from one dangling-pointer
check to two arithmetic ones.

`R5`'s `InvalidWeekday` guard runs first in `__post_init__`, before the two
`UnsatisfiableRuleSet` checks: a `day` outside `1..7` is not a contradiction
between rules, it is a value that was never a rule to begin with (mirrors
`IsoWeek.__post_init__` raising `InvalidIsoWeek` on a week number that does
not exist, `specs/week_calendar/design.md` §4).

---

## 6. Signatures

```python
"""Shared generation rules and satisfiability: category counts, pins, disabled days."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from planner_core.domain.calendar import MealSlot
from planner_core.domain.errors import PlannerError
from planner_core.domain.ingredient_category import IngredientCategory

DAYS_PER_WEEK: Final[int] = 7
SLOTS_PER_DAY: Final[int] = len(MealSlot)
TOTAL_SLOTS: Final[int] = DAYS_PER_WEEK * SLOTS_PER_DAY
WEEKDAYS: Final[frozenset[int]] = frozenset(range(1, DAYS_PER_WEEK + 1))


class InvalidWeekday(PlannerError):
    """Raised when a day value is not one of the seven weekdays (1..7)."""

    value: int

    def __init__(self, value: int) -> None:
        super().__init__(value)
        self.value = value


class UnsatisfiableRuleSet(PlannerError):
    """Raised when a RuleSet's own rules cannot all hold at once (FR-RULE-07)."""


@dataclass(frozen=True)
class CategoryCountRule:
    category: IngredientCategory
    count: int


@dataclass(frozen=True)
class PinRule:
    day: int
    slot: MealSlot
    recipe_id: str


@dataclass(frozen=True)
class RuleSet:
    category_counts: tuple[CategoryCountRule, ...] = ()
    pins: tuple[PinRule, ...] = ()
    disabled_days: tuple[int, ...] = ()

    def __post_init__(self) -> None: ...
        # raises InvalidWeekday (R5), then UnsatisfiableRuleSet (R6, R7)


@dataclass(frozen=True)
class RemovePinsResult:
    rule_set: RuleSet
    removed_pins: tuple[PinRule, ...]


def set_category_count(rule_set: RuleSet, category: IngredientCategory, count: int) -> RuleSet: ...

def remove_category_count(rule_set: RuleSet, category: IngredientCategory) -> RuleSet: ...

def set_pin(rule_set: RuleSet, day: int, slot: MealSlot, recipe_id: str) -> RuleSet: ...

def remove_pin(rule_set: RuleSet, day: int, slot: MealSlot) -> RuleSet: ...

def disable_day(rule_set: RuleSet, day: int) -> RuleSet: ...

def enable_day(rule_set: RuleSet, day: int) -> RuleSet: ...

def max_selectable_count(rule_set: RuleSet, category: IngredientCategory) -> int: ...

def available_days_for_pin(rule_set: RuleSet) -> tuple[int, ...]: ...

def available_days_to_disable(rule_set: RuleSet) -> tuple[int, ...]: ...

def remove_pins_referencing(rule_set: RuleSet, recipe_id: str) -> RemovePinsResult: ...

def apply_override(
    shared: RuleSet,
    category_counts: tuple[CategoryCountRule, ...] | None = None,
    pins: tuple[PinRule, ...] | None = None,
    disabled_days: tuple[int, ...] | None = None,
) -> RuleSet: ...
```

**`category_counts`, `pins` and `disabled_days` all default to `()`**, so an
unconfigured rule set is `RuleSet()` — trivially satisfiable (zero required,
zero disabled, zero pins).

**Every "set" function replaces, never appends.** `set_category_count`
filters out any existing `CategoryCountRule` for `category` before appending
the new one; `set_pin` does the same keyed on `(day, slot)`. This is what
makes "exactly one rule per category" and "exactly one pin per slot" true
without a separate uniqueness check in `__post_init__` — the same reasoning
`week_plan_model` used for `edit_candidate` replacing by `id` rather than
`SlotContents` validating uniqueness structurally.

**`remove_category_count`, `remove_pin` and `enable_day` are idempotent
no-ops on a target that is not present**, not raising errors. This
deliberately diverges from `week_plan_model`'s `CandidateNotFound` on an
unknown `candidate_id` — see §8, rejected alternative D, for why the two
domains call for different answers.

**`max_selectable_count`, `available_days_for_pin` and
`available_days_to_disable` exist because `docs/conventions.md`'s frontend
rules forbid recomputing rule satisfiability in the client** ("Week
boundaries, aggregation, rule satisfiability and scoping are backend domain
code... two implementations of a rule silently diverge"). Feature 20's
dropdowns call these instead of re-deriving `FR-RULE-07`'s arithmetic in
JavaScript.

### Exceptions

| Exception | Base | Raised when |
|---|---|---|
| `InvalidWeekday` | `PlannerError` | `RuleSet.__post_init__` sees a `day` outside `1..7` in `disabled_days` or in any `pins` element (R5). |
| `UnsatisfiableRuleSet` | `PlannerError` | `RuleSet.__post_init__` sees `category_counts`' total exceed the available slots (R6), or a pin whose `day` is disabled (R7). Reached from every mutating function in §6, since each one only ever constructs a new `RuleSet`. |

No function in this feature returns `None` to signal failure
(`docs/architecture.md` §4 invariant 12).

---

## 7. Why `rules.py` is not added to the ASCII shared-kernel guard

`backend/core/tests/test_shared_kernel_guards.py`'s `SHARED_KERNEL_MODULES`
tuple guards modules that declare a **closed vocabulary** other features
must reuse rather than redeclare — an enum with named members
(`text.py`'s fold rule, `units.py`'s `Unit`, `ingredient_category.py`'s
`IngredientCategory`) plus `recipe.py`. `rules.py` declares no enum: `day`
is a plain validated `int`, and `CategoryCountRule`/`PinRule` are ordinary
value shapes, not fixed vocabularies. It *consumes*
`IngredientCategory` and `MealSlot` but restates neither — the guard's
existing `test_planner_core_has_one_ingredient_category_vocabulary` already
names `rules_model` in its own docstring as the feature expected to import,
not redeclare. Nothing about `rules.py` risks a second, drifting
vocabulary the way a second `IngredientCategory` would. The source is
written ASCII-only regardless, just not mechanically enforced, matching
`candidate.py`'s precedent (`specs/week_plan_model/design.md` §7).

---

## 8. Rejected alternatives

**A. Validate satisfiability inside each mutating function instead of once
in `RuleSet.__post_init__`.**
Rejected — see §5. It turns one invariant into N call sites that must all
independently get it right, and a fifth function added later (say, by
feature 12) could easily be the one that forgets.

**B. A whole-`RuleSet` override for `FR-RULE-05` — `apply_override(shared:
RuleSet, override: RuleSet) -> RuleSet` returning `override` unchanged —
instead of three independently-optional fields.**
Rejected. `G-06`'s decision reads "a per-run override... without altering
the shared rules," not "a wholly separate rule set for one run." A UI that
wants to tweak only the category counts for one generation would otherwise
have to copy `shared.pins` and `shared.disabled_days` into the override by
hand just to keep them unchanged — an easy place to accidentally drop a
pin for one run. `None`-means-inherit per field removes that copying
entirely; the caller states only what changes.

**C. Extend `planner_core/domain/calendar.py` with a `WEEKDAYS` constant
instead of defining it locally in `rules.py`.**
Considered, not chosen — see gate question 3. `calendar.py` is feature 2,
already closed; adding to it from inside this feature's spec would blur the
same boundary `week_plan_model`'s rejected alternative E flagged for
`recipe.py`. The duplication cost is one `frozenset(range(1, 8))` literal —
not a named-member vocabulary, so the shared-kernel guard (§7) has nothing
to protect here the way it does for `Unit` or `IngredientCategory`.

**D. `remove_category_count`, `remove_pin` and `enable_day` raise
`CategoryRuleNotFound`/`PinNotFound`/similar on a target that is not
present, mirroring `week_plan_model`'s `CandidateNotFound`.**
Rejected. `week_plan_model`'s candidates are a caller-supplied, unbounded id
space where "unknown id" usually signals a real bug (stale UI state, a
double-submit). This feature's targets are drawn from small, fixed,
enumerable sets the UI's own dropdowns list exhaustively (six categories,
seven days, two slots) — "remove the pin on Tuesday lunch" when none exists
is not a caller bug, it is the ordinary shape of a UI offering a "clear"
control next to a slot that happens to be empty. Raising would force
feature 20 to pre-check existence before every removal for no safety gained.

**E. Fold `max_selectable_count` / `available_days_for_pin` /
`available_days_to_disable` into a single function returning a bundled
"current option state" object.**
Considered, not chosen — see gate question 4. Three independent pure
functions each answer one dropdown's question directly and are independently
testable; a bundling object would need its own shape decision (a fourth
dataclass) to save three function calls a caller already has to make anyway
(each dropdown is a separate UI control).

---

## 9. Boundary checks and gate questions

### Boundary checks

- **`docs/architecture.md` §2 (pending, human-owned):** nothing here needs
  P2, P3, P4, P5 or P6. Real-time broadcast of rule edits (`FR-RULE-06`) is
  named in scope-note as deferred to `P3`; this feature builds none of it.
- **§2.1 decide-in-a-spec items:** the only one this feature's `covers`
  array touches (the ingredient-category list) was already decided by
  feature 4 and is reused unchanged (§4). No new §2.1 value is proposed.
- **Frozen docs:** none modified. `docs/data_model.md` §4.5 already names
  the persisted shape (`DatosRegla`: `tipoRegla, tipoAlimento, cantidad,
  numeroDia, numeroComida, idPlato`) this feature's three rule types will
  eventually map onto at the adapter boundary — feature 14's job, not
  this one's.
- **User-facing strings:** none. `InvalidWeekday` and `UnsatisfiableRuleSet`
  carry no message text, matching `UnknownUnit`/`UnknownIngredientCategory`
  (`docs/conventions.md`, Language policy — Castilian text lives in the
  messages module owned by the feature with the UI flow).
- **Runtime dependencies:** none added; `planner-core` keeps
  `dependencies = []`.
- **Requirements invented:** none. Every `R<n>` cites one or more of
  `FR-RULE-01`–`FR-RULE-07` — all seven in this feature's `covers` array,
  no others.

### Gate questions for the human

1. **Idempotent no-op vs. raising on `remove_category_count` / `remove_pin`
   / `enable_day` targeting an absent rule (§6, §8 rejected alternative D).**
   Recommended: idempotent no-op, since the target space is small and fixed
   and a UI "clear" control routinely fires against an already-empty slot.
   Alternative: raise a not-found exception, mirroring
   `week_plan_model`'s `CandidateNotFound`. What turns on it: whether
   feature 20 must pre-check existence before every removal call.

2. **Per-axis `None`-means-inherit override for `FR-RULE-05` vs. a
   whole-`RuleSet` override (§8, rejected alternative B).** Recommended:
   per-axis, so a caller changing only category counts for one run never
   has to manually copy `pins`/`disabled_days` to preserve them.
   Alternative: whole-`RuleSet`, simpler signature, more copying at every
   call site. What turns on it: the shape feature 12 (`ai_output_validation`,
   not yet built) will code against when it wires `FR-AI-05`'s override
   parameter.

3. **`WEEKDAYS`/`DAYS_PER_WEEK` defined locally in `rules.py` rather than in
   `calendar.py` (§8, rejected alternative C).** Recommended: local,
   since it is a single unnamed-member literal, not a vocabulary the
   shared-kernel guard needs to protect. Alternative: move it to
   `calendar.py` so every future weekday-range need (this feature's, and
   any later one) shares one declaration. What turns on it: whether the
   human wants `calendar.py` (feature 2, closed) reopened for this.

4. **Three independent dropdown-option functions vs. one bundled result
   type (§8, rejected alternative E).** Recommended: independent functions,
   since each dropdown is a separate UI control needing one answer.
   Alternative: a bundled `AvailableOptions` value covering all three in one
   call. What turns on it: purely ergonomics for feature 20's future caller
   code; no behavioral difference either way.
