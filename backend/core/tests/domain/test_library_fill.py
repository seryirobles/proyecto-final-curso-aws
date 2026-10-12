"""select_library_fill, reduce_needs and run_status (week_generation_backend R7-R12, R23-R26)."""

from __future__ import annotations

import dataclasses
from datetime import date

import pytest

from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.generation import (
    GenerationMode,
    GenerationSnapshot,
    RunStatus,
    SlotError,
    SlotProgress,
    SlotStatus,
    reduce_needs,
    run_status,
    select_library_fill,
)
from planner_core.domain.ingredient_category import IngredientCategory as Cat
from planner_core.domain.recipe import Recipe
from planner_core.domain.rules import CategoryCountRule, RuleSet
from planner_core.ports.recipes import LibraryRecipe

DAY = date(2026, 8, 24)
SLOTS = tuple(SlotRef(DAY, s) for s in (MealSlot.LUNCH, MealSlot.DINNER))
SEED = "k"


def _entry(rid: str, name: str, category: Cat) -> LibraryRecipe:
    recipe = Recipe(name=name, ingredients=(), tools=("olla",), procedure=("x",), category=category)
    return LibraryRecipe(id=rid, recipe=recipe, author="u")


def _need(category: Cat, count: int) -> CategoryCountRule:
    return CategoryCountRule(category=category, count=count)


def test_value_types_are_frozen() -> None:
    progress = SlotProgress(1, 1, SlotStatus.PENDING)
    snap = GenerationSnapshot(IsoWeek(2026, 34), GenerationMode.MIX, RuleSet(), "v1")
    for obj, attr in ((progress, "day"), (snap, "mode"), (SlotError("c", "m"), "code")):
        with pytest.raises(dataclasses.FrozenInstanceError):
            obj.__setattr__(attr, None)


def test_category_with_a_remaining_count_is_filled_first() -> None:  # R9
    library = (_entry("a", "A", Cat.MEAT), _entry("b", "B", Cat.LEGUME), _entry("c", "C", Cat.MEAT))

    picks = select_library_fill(SLOTS, library, (_need(Cat.LEGUME, 1),), frozenset(), SEED)

    assert picks[SLOTS[0]].recipe.category is Cat.LEGUME


def test_a_spent_need_falls_back_to_any_recipe() -> None:  # R10
    library = (_entry("a", "A", Cat.MEAT), _entry("b", "B", Cat.LEGUME))

    picks = select_library_fill(SLOTS, library, (_need(Cat.LEGUME, 1),), frozenset(), SEED)

    assert [picks[s].recipe.category for s in SLOTS] == [Cat.LEGUME, Cat.MEAT]


def test_a_need_without_an_eligible_recipe_falls_back() -> None:  # R10
    library = (_entry("a", "A", Cat.MEAT),)

    picks = select_library_fill(SLOTS, library, (_need(Cat.LEGUME, 2),), frozenset(), SEED)

    assert picks[SLOTS[0]].id == "a" and SLOTS[1] not in picks


def test_used_names_are_excluded_case_folded() -> None:  # R8
    library = (_entry("a", "Lentejas", Cat.LEGUME), _entry("b", "Arroz", Cat.CARBOHYDRATE))

    picks = select_library_fill(SLOTS, library, (), frozenset({"lentejas"}), SEED)

    assert [e.id for e in picks.values()] == ["b"]


def test_a_name_picked_in_the_run_is_not_picked_twice() -> None:  # R8
    library = (_entry("a", "ARROZ", Cat.MEAT), _entry("b", "arroz", Cat.MEAT))

    picks = select_library_fill(SLOTS, library, (), frozenset(), SEED)

    assert len(picks) == 1


def test_equal_inputs_give_equal_picks_regardless_of_library_order() -> None:  # R11
    library = tuple(_entry(f"r{i}", f"N{i}", Cat.MEAT) for i in range(10))

    first = select_library_fill(SLOTS, library, (), frozenset(), SEED)
    again = select_library_fill(SLOTS, tuple(reversed(library)), (), frozenset(), SEED)

    assert first == again
    other = select_library_fill(SLOTS, library, (), frozenset(), "other-seed-xyz")
    assert first != other


def test_an_empty_library_picks_nothing() -> None:
    assert select_library_fill(SLOTS, (), (), frozenset(), SEED) == {}


def test_reduce_needs_subtracts_and_floors_at_zero() -> None:  # R12
    needs = (_need(Cat.MEAT, 2), _need(Cat.LEGUME, 1))

    reduced = reduce_needs(needs, [Cat.MEAT, Cat.MEAT, Cat.MEAT, Cat.VEGETABLE])

    assert reduced == (_need(Cat.MEAT, 0), _need(Cat.LEGUME, 1))


def _p(status: SlotStatus) -> SlotProgress:
    return SlotProgress(1, 1, status)


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        ((), RunStatus.COMPLETED),  # R24
        ((SlotStatus.DONE, SlotStatus.DONE), RunStatus.COMPLETED),  # R24
        ((SlotStatus.DONE, SlotStatus.ERROR), RunStatus.PARTIAL),  # R25
        ((SlotStatus.ERROR, SlotStatus.ERROR), RunStatus.FAILED),  # R26
        ((SlotStatus.DONE, SlotStatus.PENDING), RunStatus.RUNNING),  # R23
        ((SlotStatus.ERROR, SlotStatus.RUNNING), RunStatus.RUNNING),  # R23
    ],
)
def test_run_status_table(statuses: tuple[SlotStatus, ...], expected: RunStatus) -> None:
    assert run_status([_p(s) for s in statuses]) is expected
