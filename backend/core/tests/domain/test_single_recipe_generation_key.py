"""Single-recipe request types and key (specs/single_recipe_generation R7-R10)."""

from __future__ import annotations

import dataclasses
from datetime import date

import pytest

from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.generation import (
    GenerationMode,
    GenerationTargets,
    ReferenceSource,
    SingleRecipeRequest,
    SpecificationSource,
    idempotency_key,
    single_recipe_key,
)
from planner_core.domain.rules import RuleSet

SLOT = SlotRef(date(2026, 7, 15), MealSlot.LUNCH)


def _spec(
    ingredients: tuple[str, ...] = ("a", "b"), tools: tuple[str, ...] = ("x", "y")
) -> SingleRecipeRequest:
    return SingleRecipeRequest(SLOT, SpecificationSource(ingredients, tools))


def _ref(recipe_id: str = "r1", extra: tuple[str, ...] = ("p", "q")) -> SingleRecipeRequest:
    return SingleRecipeRequest(SLOT, ReferenceSource(recipe_id, extra))


def test_request_and_source_types_are_frozen() -> None:
    """R7 (types)."""
    for instance in (_spec(), _ref(), _spec().source, _ref().source):
        with pytest.raises(dataclasses.FrozenInstanceError):
            instance.__setattr__("source", None)


def test_key_is_deterministic() -> None:
    """R7."""
    assert single_recipe_key(_spec(), 0) == single_recipe_key(_spec(), 0)


def test_key_changes_with_attempt() -> None:
    """R7."""
    assert single_recipe_key(_spec(), 0) != single_recipe_key(_spec(), 1)


def test_key_ignores_list_order() -> None:
    """R8."""
    assert single_recipe_key(_spec(("a", "b"), ("x", "y")), 0) == single_recipe_key(
        _spec(("b", "a"), ("y", "x")), 0
    )
    assert single_recipe_key(_ref(extra=("p", "q")), 0) == single_recipe_key(
        _ref(extra=("q", "p")), 0
    )


def test_key_differs_by_scope_source_kind_and_content() -> None:
    """R9."""
    other_slot = SingleRecipeRequest(SlotRef(date(2026, 7, 15), MealSlot.DINNER), _spec().source)
    library = SingleRecipeRequest(None, _spec().source)
    keys = {
        single_recipe_key(request, 0)
        for request in (
            _spec(),
            other_slot,
            library,
            _spec(("a", "c")),
            _spec(tools=("x", "z")),
            _ref(),
            _ref("r2"),
            _ref(extra=("p",)),
        )
    }
    assert len(keys) == 8


def test_whole_week_key_is_pinned_by_a_golden_hash() -> None:
    """R10."""
    targets = GenerationTargets(
        open_slots=(SLOT,), pinned_slots=(), skipped_pins=(), remaining_category_counts=()
    )
    key = idempotency_key(IsoWeek(2026, 29), targets, RuleSet(), GenerationMode.MIX)
    assert key == "c8003ccd9baabd770cdeb7bcca7f06c48ae00101f39787bbd658ccde9c0a9a52"
