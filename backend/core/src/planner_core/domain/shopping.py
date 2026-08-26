"""Deterministic aggregation of definitive meals in scope into a required-item set."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date

from planner_core.domain.calendar import SlotRef, current_week, next_week, slots_from
from planner_core.domain.candidate import SlotContents, definitive
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
