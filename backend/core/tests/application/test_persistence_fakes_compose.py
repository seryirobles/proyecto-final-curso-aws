"""R8's "used by application-layer tests" bullet: the fakes compose across
ports the way a real use case eventually will (design.md section 8), with no
application/ module needed to prove it."""

from __future__ import annotations

from datetime import UTC, date, datetime

from support.fakes import (
    FakeAccountRepository,
    FakeRecipeRepository,
    FakeShoppingListRepository,
    FakeWeekRepository,
)

from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import SlotContents, new_candidate, promote
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Ingredient, Recipe, snapshot
from planner_core.domain.role import Role
from planner_core.domain.shopping import ShoppingItem, required_shopping_items
from planner_core.domain.units import Unit
from planner_core.ports.accounts import AccountRecord
from planner_core.ports.recipes import LibraryRecipe

WEEK = IsoWeek(2026, 30)
SLOT = SlotRef(date(2026, 7, 20), MealSlot.LUNCH)


def test_fakes_compose_from_account_through_recipe_week_and_shopping_list() -> None:
    accounts = FakeAccountRepository()
    recipes = FakeRecipeRepository()
    weeks = FakeWeekRepository()
    shopping_list = FakeShoppingListRepository()

    accounts.create(
        AccountRecord(
            user_id="u1",
            username="Ana",
            role=Role.USER,
            password_hash="hash",
            password_reset_required=True,
            credentials_valid_since=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )

    recipe = Recipe(
        name="Lentejas",
        ingredients=(Ingredient(name="Lentejas", quantity=200, unit=Unit.GRAM),),
        tools=(),
        procedure=(),
        category=IngredientCategory.LEGUME,
    )
    recipes.save(LibraryRecipe(id="r1", recipe=recipe, author="u1"))

    entry = recipes.get("r1")
    assert entry is not None
    candidate = new_candidate(id="c1", meal=snapshot(entry.recipe), author="u1")
    plan = promote(SlotContents(candidates=(candidate,)), "c1")
    weeks.save_slot(WEEK, SLOT, plan)

    required = required_shopping_items(weeks.get_week(WEEK), today=SLOT.day)
    assert required == (Ingredient(name="Lentejas", quantity=200, unit=Unit.GRAM),)

    for index, ingredient in enumerate(required):
        shopping_list.save_item(
            ShoppingItem(
                id=f"s{index}",
                name=ingredient.name,
                quantity=ingredient.quantity,
                unit=ingredient.unit,
            )
        )

    assert shopping_list.list_items() == (
        ShoppingItem(id="s0", name="Lentejas", quantity=200, unit=Unit.GRAM),
    )
    assert accounts.get_by_username("ana") is not None
