"""R34/R35 — the four pollable read use cases return the resource's current
`marcaCambio` (the value `current_version` reports) and read that marker before
they read the payload (docs/rest_api_contract.md section 6)."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from support.fakes import (
    FakeRecipeRepository,
    FakeRuleRepository,
    FakeShoppingListRepository,
    FakeWeekRepository,
)

from planner_core.application import library_editing, rule_editing, shopping_editing, week_editing
from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import Candidate, SlotContents
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import MealSnapshot, Recipe
from planner_core.domain.rules import DisabledDay, RuleSet
from planner_core.domain.shopping import ShoppingItem
from planner_core.domain.units import Unit
from planner_core.ports.recipes import LibraryRecipe

WEEK = IsoWeek(2026, 30)
SLOT = SlotRef(date(2026, 7, 20), MealSlot.LUNCH)


def _meal() -> MealSnapshot:
    return MealSnapshot(
        name="Lentejas", ingredients=(), tools=(), procedure=(), category=IngredientCategory.LEGUME
    )


class SpyWeeks(FakeWeekRepository):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[str] = []

    def current_version(self, week: IsoWeek) -> int:
        self.calls.append("marker")
        return super().current_version(week)

    def get_week(self, week: IsoWeek) -> Mapping[SlotRef, SlotContents]:
        self.calls.append("payload")
        return super().get_week(week)


class SpyRecipes(FakeRecipeRepository):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[str] = []

    def current_version(self) -> int:
        self.calls.append("marker")
        return super().current_version()

    def list_all(self) -> tuple[LibraryRecipe, ...]:
        self.calls.append("payload")
        return super().list_all()


class SpyRules(FakeRuleRepository):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[str] = []

    def current_version(self) -> int:
        self.calls.append("marker")
        return super().current_version()

    def get(self) -> RuleSet:
        self.calls.append("payload")
        return super().get()


class SpyShopping(FakeShoppingListRepository):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[str] = []

    def current_version(self) -> int:
        self.calls.append("marker")
        return super().current_version()

    def list_items(self) -> tuple[ShoppingItem, ...]:
        self.calls.append("payload")
        return super().list_items()


def test_load_week_returns_the_current_marker_and_reads_it_first() -> None:
    repo = SpyWeeks()
    candidate = Candidate(id="c1", meal=_meal(), author="u1")
    repo.save_slot(WEEK, SLOT, SlotContents(candidates=(candidate,)))
    repo.calls.clear()

    view = week_editing.load_week(WEEK, weeks=repo)

    assert view.marker == repo.current_version(WEEK)
    assert repo.calls[:2] == ["marker", "payload"]


def test_list_library_returns_the_current_marker_and_reads_it_first() -> None:
    repo = SpyRecipes()
    recipe = Recipe(
        name="Tortilla", ingredients=(), tools=(), procedure=(), category=IngredientCategory.EGGS
    )
    repo.save(LibraryRecipe(id="r1", recipe=recipe, author="u1"))
    repo.calls.clear()

    view = library_editing.list_library(recipes=repo)

    assert view.marker == repo.current_version()
    assert repo.calls[:2] == ["marker", "payload"]


def test_read_rules_returns_the_current_marker_and_reads_it_first() -> None:
    repo = SpyRules()
    repo.save_rule(DisabledDay(day=6))
    repo.calls.clear()

    view = rule_editing.read_rules(rules=repo)

    assert view.marker == repo.current_version()
    assert repo.calls[:2] == ["marker", "payload"]


def test_list_shopping_returns_the_current_marker_and_reads_it_first() -> None:
    repo = SpyShopping()
    repo.save_item(ShoppingItem(id="s1", name="arroz", quantity=500, unit=Unit.GRAM))
    repo.calls.clear()

    view = shopping_editing.list_shopping(shopping=repo)

    assert view.marker == repo.current_version()
    assert repo.calls[:2] == ["marker", "payload"]
