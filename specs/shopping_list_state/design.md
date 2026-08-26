# shopping_list_state — Design

> Feature 8 · tier 1 · pure `planner_core.domain`
> Read `requirements.md` first. This document records the technical decisions
> taken before any code is written, per `docs/specs.md`.
> Depends on feature 7 `shopping_aggregation` (done — `required_shopping_items`,
> `Ingredient`) and reuses feature 3 `text_and_units` (closed — `normalize`,
> `Unit`). This feature **extends** `planner_core/domain/shopping.py` rather
> than adding a new module — `specs/shopping_aggregation/design.md` §9 gate
> question 3 named this module for exactly this extension.

## 0. The invariant this feature exists to protect

`docs/architecture.md` §4, invariant 2:

> **Never silently undo the user's reality.** ... **Stricter on purchases:** a
> checked shopping item is not merely preserved, it is **never written to at
> all**; a later shortfall arrives as its own new unchecked item carrying the
> remainder (`G-77`, supersedes `G-44`).

`docs/gaps_and_resolutions.md`, `G-77`:

> Re-sync never modifies a checked item at all — not its state, not its
> quantity... In the rice case the checked `arroz 500 g` is left alone and a
> new unchecked `arroz 300 g` appears — the amount still to buy, not the gross
> requirement.

Every function below is subordinate to this: `resync` never constructs a
`ShoppingItem` with `checked=True`, never looks up a checked item as a write
target, and the value it ever writes is an **outstanding** amount already net
of what checked items carry — never the gross `required` quantity.

---

## 1. Scope boundary

`FR-SHOP-06`'s "additive merge... so repeated presses converge" and
`FR-SHOP-10`'s persisted-list half (see `requirements.md`'s scope note) are
implemented here, over feature 7's already-deterministic
`required_shopping_items` output. **Not implemented here:**

- **Serialization against concurrent presses.** `G-77`'s "left unresolved,
  deliberately" note and `docs/data_model.md` §5.3 (the `LockLista` TTL
  protocol) both scope this to the persistence/data-structure pass — feature
  14 (`persistence_ports`) at the earliest, once a real port exists to hold a
  lock against. `resync` here is a pure function; nothing about "two
  concurrent presses" is representable without IO.
- **Persistence mapping.** `docs/data_model.md` §1's `DatosIngredienteLista`
  (`nombreIngrediente, cantidad, unidad, isComprado`) is the eventual
  persisted shape of `ShoppingItem`; `idIngrediente` maps to `ShoppingItem.id`.
  Nothing here writes to DynamoDB or imports a port — that mapping is an
  adapter's job, not yet built.
- **The re-sync button and horizon display (`FR-SHOP-01`'s "covering the
  shopping horizon" clause, `FR-SHOP-03`'s button).** Those are UI-facing
  (feature 20) and already-shipped aggregation scope (feature 7) respectively.

---

## 2. Layering

`docs/architecture.md` §3: `domain/` is pure logic, no IO, no port, no clock.
Every function below is a pure transformation of plain values — no exception
to that in this feature; re-sync's only external input beyond `items` and
`required` is a plain, pre-resolved `Sequence[str]` of ids (§5).

| Piece | Layer | Why |
|---|---|---|
| `ShoppingItem`, `ShoppingItemNotFound`, `InsufficientNewIds`, `add_item`, `edit_item`, `remove_item`, `check_item`, `uncheck_item`, `unchecked_items`, `checked_items`, `outstanding_amounts`, `resync` | `planner_core/domain/shopping.py` (extended) | Pure functions/types over plain values (`tuple[ShoppingItem, ...]`, `tuple[Ingredient, ...]`, `Sequence[str]`); no IO, no ambient state, no clock, no port import. |

No `application/` piece is added by this feature. A future use case
(feature 14+) reads the persisted list and `LiveWeeks.today` (feature 2),
calls `required_shopping_items` (feature 7) then `resync` (this feature), and
persists the result — none of that orchestration exists yet and none of it
is this feature's concern.

---

## 3. Files

### Modified

| Path | Change |
|---|---|
| `backend/core/src/planner_core/domain/shopping.py` | Add `ShoppingItem`, `ShoppingItemNotFound`, `InsufficientNewIds`, `add_item`, `edit_item`, `remove_item`, `check_item`, `uncheck_item`, `unchecked_items`, `checked_items`, `outstanding_amounts`, `resync`. Existing `in_scope_slots`, `definitive_ingredients`, `aggregate_ingredients`, `required_shopping_items` (feature 7) are untouched. |
| `backend/core/tests/domain/test_shopping.py` | Extended with R1–R19's tests, appended after feature 7's R1–R8 tests. |

### Created

None.

---

## 4. `docs/architecture.md` §2.1 items

None proposed here. The unit list (`Unit`) this feature relies on shipped
with feature 3; nothing in `covers` touches the ingredient-category list,
servings count, or the removed per-user cap.

---

## 5. Id supply for new items — a plain `Sequence[str]`, not a live generator

`resync` may need to create zero, one, or several new items in a single call
(one per required key with no matching unchecked item and a positive
outstanding amount). Something must supply their ids.

**Chosen: `new_ids: Sequence[str]`, drawn from front to back as needed, via
`iter()`/`next()`.** The caller (eventually an application-layer use case
holding an id port, not yet built) generates however many ids it might need
*before* calling `resync` and passes them in as an already-resolved,
finite collection. `resync` consumes only as many as it actually needs and
never generates one itself.

**Why not a `Callable[[], str]` id factory instead.** Considered and
rejected — see rejected alternative A (§8). A callable parameter is exactly
the shape `docs/specs.md`'s own worked example rejected for `Clock`: *"domain
functions take a plain date, never a Clock... An earlier version of this
example showed `current_week(clock)` in `domain/`; that was wrong."* The
principle generalises past time: `domain/` takes **already-resolved plain
values**, never a live, ambient-capable abstraction it could call
repeatedly and unpredictably. `Sequence[str]` is the "plain date" here;
`Callable[[], str]` would be the "Clock."

**Contract, and what happens when it is under-supplied.** The caller must
supply at least as many ids as `resync` will need — a safe, cheap upper bound
is `len(outstanding_amounts(items, required))`, computable by the caller
before calling `resync` at all (§9 gate question 2 asks the human to confirm
this contract rather than a friendlier alternative). If `new_ids` is
exhausted mid-computation, `resync` raises `InsufficientNewIds` rather than
silently creating fewer items than `outstanding_amounts` says are owed —
`docs/architecture.md` §4 invariant 12: functions that can fail raise, they
never return an incomplete result and call it done.

---

## 6. Signatures

```python
"""Deterministic aggregation of definitive meals in scope into a required-item set,
plus the shared, provenance-free shopping list: manual CRUD, check-off, and a
re-sync merge that never writes to a checked item (G-77)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from planner_core.domain.calendar import SlotRef, current_week, next_week, slots_from
from planner_core.domain.candidate import SlotContents, definitive
from planner_core.domain.errors import PlannerError
from planner_core.domain.recipe import Ingredient
from planner_core.domain.text import normalize
from planner_core.domain.units import Unit

# ... feature 7's in_scope_slots / definitive_ingredients / aggregate_ingredients /
# required_shopping_items are unchanged and appear above this addition ...


class ShoppingItemNotFound(PlannerError):
    """Raised when an edit, remove, check or uncheck targets an absent item id."""

    item_id: str

    def __init__(self, item_id: str) -> None:
        super().__init__(item_id)
        self.item_id = item_id


class InsufficientNewIds(PlannerError):
    """Raised when resync needs more new-item ids than new_ids supplied (R12, section 5)."""


@dataclass(frozen=True)
class ShoppingItem:
    """One shopping-list row: an id, a name, a quantity, a unit, a check state.

    No auto/manual marker, no override state, no updated-since-checked flag
    (FR-SHOP-01, FR-SHOP-04, FR-SHOP-08; G-72, G-77).
    """

    id: str
    name: str
    quantity: float
    unit: Unit
    checked: bool = False


def add_item(
    items: tuple[ShoppingItem, ...], item: ShoppingItem
) -> tuple[ShoppingItem, ...]:
    """Append item unconditionally; no rejection on a matching key (R2, R19)."""
    return (*items, item)


def edit_item(
    items: tuple[ShoppingItem, ...], item_id: str, name: str, quantity: float
) -> tuple[ShoppingItem, ...]:
    """Replace the matching item's name and quantity; unit and check state survive (R3, R4)."""
    if not any(i.id == item_id for i in items):
        raise ShoppingItemNotFound(item_id)
    return tuple(
        ShoppingItem(id=i.id, name=name, quantity=quantity, unit=i.unit, checked=i.checked)
        if i.id == item_id
        else i
        for i in items
    )


def remove_item(items: tuple[ShoppingItem, ...], item_id: str) -> tuple[ShoppingItem, ...]:
    """Delete the matching item (R5)."""
    if not any(i.id == item_id for i in items):
        raise ShoppingItemNotFound(item_id)
    return tuple(i for i in items if i.id != item_id)


def check_item(items: tuple[ShoppingItem, ...], item_id: str) -> tuple[ShoppingItem, ...]:
    """Set the matching item's check state to checked (R7)."""
    if not any(i.id == item_id for i in items):
        raise ShoppingItemNotFound(item_id)
    return tuple(
        ShoppingItem(id=i.id, name=i.name, quantity=i.quantity, unit=i.unit, checked=True)
        if i.id == item_id
        else i
        for i in items
    )


def uncheck_item(items: tuple[ShoppingItem, ...], item_id: str) -> tuple[ShoppingItem, ...]:
    """Set the matching item's check state to unchecked (R8)."""
    if not any(i.id == item_id for i in items):
        raise ShoppingItemNotFound(item_id)
    return tuple(
        ShoppingItem(id=i.id, name=i.name, quantity=i.quantity, unit=i.unit, checked=False)
        if i.id == item_id
        else i
        for i in items
    )


def unchecked_items(items: tuple[ShoppingItem, ...]) -> tuple[ShoppingItem, ...]:
    """Items not yet bought, in list order — the primary section (R9)."""
    return tuple(i for i in items if not i.checked)


def checked_items(items: tuple[ShoppingItem, ...]) -> tuple[ShoppingItem, ...]:
    """Items already bought, in list order — the greyed-out section below (R9)."""
    return tuple(i for i in items if i.checked)


def outstanding_amounts(
    items: tuple[ShoppingItem, ...], required: tuple[Ingredient, ...]
) -> tuple[Ingredient, ...]:
    """Per normalized name + unit: required minus what checked items already carry (R10, R13).

    Entries whose outstanding amount is zero or less are omitted, never
    returned as a non-positive quantity.
    """
    checked_totals: dict[tuple[str, Unit], float] = {}
    for item in items:
        if not item.checked:
            continue
        key = (normalize(item.name), item.unit)
        checked_totals[key] = checked_totals.get(key, 0) + item.quantity

    result: list[Ingredient] = []
    for req in required:
        key = (normalize(req.name), req.unit)
        outstanding = req.quantity - checked_totals.get(key, 0)
        if outstanding > 0:
            result.append(Ingredient(name=req.name, quantity=outstanding, unit=req.unit))
    return tuple(result)


def resync(
    items: tuple[ShoppingItem, ...],
    required: tuple[Ingredient, ...],
    new_ids: Sequence[str],
) -> tuple[ShoppingItem, ...]:
    """Additive merge of outstanding_amounts onto items; never touches a checked item (R11-R18).

    Per outstanding entry: write to the first unchecked item sharing its
    normalized name + unit (section 7 tie-break), or append a new one built
    from new_ids. Every other item — checked, or unchecked with a
    non-required key — passes through unchanged. Nothing is ever removed.
    """
    outstanding = outstanding_amounts(items, required)

    matched_index: dict[tuple[str, Unit], int] = {}
    for idx, item in enumerate(items):
        if item.checked:
            continue
        key = (normalize(item.name), item.unit)
        matched_index.setdefault(key, idx)

    updated = list(items)
    new_id_iter = iter(new_ids)
    appended: list[ShoppingItem] = []

    for ing in outstanding:
        key = (normalize(ing.name), ing.unit)
        idx = matched_index.get(key)
        if idx is not None:
            existing = updated[idx]
            updated[idx] = ShoppingItem(
                id=existing.id,
                name=existing.name,
                quantity=ing.quantity,
                unit=existing.unit,
                checked=False,
            )
        else:
            try:
                new_id = next(new_id_iter)
            except StopIteration as exc:
                raise InsufficientNewIds from exc
            appended.append(
                ShoppingItem(id=new_id, name=ing.name, quantity=ing.quantity, unit=ing.unit)
            )

    return (*updated, *appended)
```

---

## 7. Two determinism notes

**`resync` writes only to the *first* unchecked item (in list order) sharing
a normalized name + unit.** No `FR-*` decides what happens when two unchecked
items already share a key (possible since `FR-SHOP-11`'s removal, `G-74`,
means manual add never rejects a duplicate — `R19`). First-occurrence-in-list-
order was chosen for the same reason `shopping_aggregation` chose it for
kept spelling (`specs/shopping_aggregation/design.md` §6, §8 alternative D):
deterministic, no extra sort, and it needs no bookkeeping beyond the
single-pass `matched_index` scan already required. See gate question 1 (§9).

**`resync` writes only the outstanding *quantity* to a matched unchecked
item — never its `name` or `unit`.** The matched item's own raw spelling
(possibly differently-cased or -spaced from `required`'s) survives untouched,
mirroring `edit_candidate`'s "preserve everything not named by the edit"
shape (`planner_core/domain/candidate.py`). `FR-SHOP-06` says re-sync "writes
[the outstanding amount] to the matching unchecked item" — quantity only: it
never says re-sync renames a user's own row. See gate question 3 (§9).

---

## 8. Rejected alternatives

**A. A `Callable[[], str]` id factory parameter for `resync`, instead of a
plain pre-resolved `Sequence[str]`.**
Rejected — see §5. A callable domain could invoke ambiently is exactly the
shape `docs/specs.md` already rejected for `Clock`. A `Sequence[str]` is
inert data; a `Callable[[], str]` is a live resource domain would be reaching
into, indistinguishable in kind from `datetime.now()` — both are "ask an
external system for a fresh, unpredictable value," which `docs/architecture.md`
§3.1 rule 6 exists to keep out of `core`.

**B. Derive a new item's id deterministically from its normalized name + unit
(e.g. `f"{normalized_name}#{unit.value}"`) instead of taking a caller-supplied
id.**
Rejected. `G-77` explicitly relies on a checked and an unchecked item sharing
a normalized name + unit as **two distinct rows** — "the surrogate
`idIngrediente` already permits this." A key-derived id would collide the
moment such a pair exists, precisely the case this feature must support
(`R18`). It would also reintroduce the exact staleness trap
`docs/data_model.md` §5.2 documents for the username fold: a normalization
refined later stops matching an id minted from an earlier normalization,
except here the mismatch corrupts identity, not just a lookup.

**C. One monolithic `resync` computing and applying the outstanding amount in
a single pass, instead of `outstanding_amounts` + `resync`.**
Considered, not chosen. Decomposing lets `R10` (the outstanding computation)
and `R13` (omit non-positive amounts) be tested directly against
`outstanding_amounts` with no `ShoppingItem` construction beyond the checked
items needed to prove the subtraction, while `R11`/`R12`/`R14`–`R18` are
tested against `resync`'s list-mutation behavior alone. Same reasoning
`shopping_aggregation` gave for its own three-function decomposition
(`specs/shopping_aggregation/design.md` §5, alternative B chosen there):
independent pure functions, one per question, composed by the one that needs
both answers.

**D. Overwrite a matched unchecked item's `name` (and/or `unit`) to
`required`'s spelling when writing the outstanding quantity.**
Rejected — see §7. Nothing in `FR-SHOP-06` asks re-sync to rename a row; it
asks it to write a quantity. Overwriting the name would also silently discard
whatever raw spelling a user typed when they manually created that unchecked
item, which is exactly the kind of "the next press quietly changes what I
typed" `G-72` already accepted as a **quantity**-level cost, not a rationale
to extend to the name too.

**E. Silently create fewer items than `outstanding_amounts` calls for when
`new_ids` runs out, instead of raising `InsufficientNewIds`.**
Rejected. `docs/architecture.md` §4 invariant 12 requires a named exception,
not a truncated result masquerading as success — a caller checking
`len(result)` against what it expected would have no signal that a shortfall
was silently dropped, which is precisely the "silently undo the user's
reality" failure mode invariant 2 exists to prevent, applied to a shortfall
that never got a chance to reach the list at all.

---

## 9. Boundary checks and gate questions

### Boundary checks

- **`docs/architecture.md` §2 (pending, human-owned):** nothing here needs P2,
  P3, P4, P5 or P6. This feature is pure `domain/`, no port, no adapter, no
  Lambda. Serialization (`FR-SHOP-10`'s "serialized" clause) is explicitly
  deferred (§1) rather than decided here.
- **§2.1 decide-in-a-spec items:** none proposed; this feature reuses `Unit`
  (shipped by feature 3) and proposes no new closed vocabulary of its own.
- **Frozen docs:** none modified. `docs/data_model.md`'s `DatosIngredienteLista`
  shape (`nombreIngrediente, cantidad, unidad, isComprado`) maps to
  `ShoppingItem` field-for-field (`idIngrediente` → `id`); this feature does
  not touch persistence code, only names the eventual mapping.
- **User-facing strings:** none. No Castilian text; the two new exceptions
  carry only an id in their `args`, same shape as `CandidateNotFound`.
- **Runtime dependencies:** none added; `planner-core` keeps
  `dependencies = []`.
- **Requirements invented:** none. Every `R<n>` cites `FR-SHOP-01/02/04/06/07/08`
  (this feature's `covers`) or `FR-SHOP-10` (cited per the scope note in
  `requirements.md`, already anticipated by feature 7's own design doc) — no
  other id, and `FR-SHOP-11` is never cited (removed, `G-74`).

### Gate questions for the human

1. **First-occurrence-in-list-order as the tie-break when two unchecked items
   already share a normalized name + unit (§7).** Recommended: first
   occurrence, mirroring `shopping_aggregation`'s own precedent for kept
   spelling. Alternative: none is decided by any `FR-*`. What turns on it:
   which of two pre-existing unchecked duplicates receives re-sync's write
   the first time a shortfall touches that key; the other is left exactly as
   a user typed it, forever, until they edit or delete it themselves.

2. **The `new_ids: Sequence[str]` contract — the caller must supply at least
   `len(outstanding_amounts(items, required))` ids before calling `resync`,
   or it raises `InsufficientNewIds` (§5).** Recommended: yes, as the
   simplest contract that keeps `resync` a pure function with no ambient id
   generation. Alternative: a friendlier signature that lets `resync` report
   how many ids it still needed instead of raising — more forgiving, but adds
   a second return shape (success vs. partial) that `docs/architecture.md` §4
   invariant 12 argues against. What turns on it: how the eventual
   application-layer caller (not yet built, feature 14+) is expected to size
   its id-generation call before invoking `resync`.

3. **Re-sync writes only the outstanding quantity to a matched unchecked
   item, never its name or unit (§7, §8 alternative D).** Recommended: yes —
   `FR-SHOP-06`'s own wording says "writes the outstanding amount," nothing
   about renaming. Alternative: none proposed; flagged because it is easy to
   implement wrong by "helpfully" normalizing display spelling on every
   write, which this design explicitly forbids. What turns on it: whether a
   shopper ever sees their own typed spelling silently replaced by whatever
   spelling a recipe's ingredient list happened to use.
