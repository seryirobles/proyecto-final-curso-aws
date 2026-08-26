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


def in_scope_slots(today: date) -> tuple[SlotRef, ...]:
    """Current week's slots from today onward, plus every slot of next week (R1, R2)."""
    return slots_from(current_week(today), today) + slots_from(next_week(today), today)


def definitive_ingredients(
    plans: Mapping[SlotRef, SlotContents], slots: Iterable[SlotRef]
) -> tuple[Ingredient, ...]:
    """Ingredients of each slot's definitive meal, in slot order (R3, R4).

    A slot missing from plans, or holding no definitive, contributes nothing
    (docs/architecture.md section 4 invariant 6).
    """
    ingredients: list[Ingredient] = []
    for slot in slots:
        plan = plans.get(slot)
        if plan is None:
            continue
        candidate = definitive(plan)
        if candidate is None:
            continue
        ingredients.extend(candidate.meal.ingredients)
    return tuple(ingredients)


def aggregate_ingredients(ingredients: Iterable[Ingredient]) -> tuple[Ingredient, ...]:
    """Merge on normalized name + unit; sum quantities; no cross-unit conversion (R5, R6).

    First occurrence of a key keeps its raw spelling (design.md section 6,
    section 8 rejected alternative D). ingredient.unit is carried through
    unchanged; no Unit is constructed directly here.
    """
    order: list[tuple[str, Unit]] = []
    names: dict[tuple[str, Unit], str] = {}
    totals: dict[tuple[str, Unit], float] = {}

    for ingredient in ingredients:
        key = (normalize(ingredient.name), ingredient.unit)
        if key not in names:
            order.append(key)
            names[key] = ingredient.name
            totals[key] = 0
        totals[key] += ingredient.quantity

    return tuple(Ingredient(name=names[key], quantity=totals[key], unit=key[1]) for key in order)


def required_shopping_items(
    plans: Mapping[SlotRef, SlotContents], today: date
) -> tuple[Ingredient, ...]:
    """The full aggregation entry point: scope, then definitive lookup, then merge (R1-R8)."""
    return aggregate_ingredients(definitive_ingredients(plans, in_scope_slots(today)))


class ShoppingItemNotFound(PlannerError):
    """Raised when an edit, remove, check or uncheck targets an absent item id."""

    item_id: str

    def __init__(self, item_id: str) -> None:
        super().__init__(item_id)
        self.item_id = item_id


class InsufficientNewIds(PlannerError):
    """Raised when resync needs more ids than new_ids supplied (R12, design.md section 5)."""


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


def add_item(items: tuple[ShoppingItem, ...], item: ShoppingItem) -> tuple[ShoppingItem, ...]:
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
    """Items not yet bought, in list order - the primary section (R9)."""
    return tuple(i for i in items if not i.checked)


def checked_items(items: tuple[ShoppingItem, ...]) -> tuple[ShoppingItem, ...]:
    """Items already bought, in list order - the greyed-out section below (R9)."""
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
    normalized name + unit (design.md section 7 tie-break), or append a new
    one built from new_ids. Every other item - checked, or unchecked with a
    non-required key - passes through unchanged. Nothing is ever removed.
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
        match_idx = matched_index.get(key)
        if match_idx is not None:
            existing = updated[match_idx]
            updated[match_idx] = ShoppingItem(
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
