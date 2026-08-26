"""Contract suite for RecipeRepository: one suite, run against every registered
implementation (R9)."""

from __future__ import annotations

import pytest
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Recipe
from planner_core.ports.recipes import LibraryRecipe, RecipeNotFound
from support.fakes import FakeRecipeRepository

IMPLEMENTATIONS = [FakeRecipeRepository]


def _recipe(name: str = "Tortilla") -> Recipe:
    return Recipe(
        name=name, ingredients=(), tools=(), procedure=(), category=IngredientCategory.EGGS
    )


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_save_then_get_and_list_round_trip(repository_factory: type[FakeRecipeRepository]) -> None:
    repo = repository_factory()
    entry = LibraryRecipe(id="r1", recipe=_recipe(), author="u1")

    repo.save(entry)

    assert repo.get("r1") == entry
    assert repo.list_all() == (entry,)


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_save_overwrites_by_id(repository_factory: type[FakeRecipeRepository]) -> None:
    repo = repository_factory()
    repo.save(LibraryRecipe(id="r1", recipe=_recipe("Tortilla"), author="u1"))

    repo.save(LibraryRecipe(id="r1", recipe=_recipe("Tortilla de patata"), author="u1"))

    entry = repo.get("r1")
    assert entry is not None
    assert entry.recipe.name == "Tortilla de patata"


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_delete_removes_the_entry_and_raises_when_missing(
    repository_factory: type[FakeRecipeRepository],
) -> None:
    repo = repository_factory()
    repo.save(LibraryRecipe(id="r1", recipe=_recipe(), author="u1"))

    repo.delete("r1")

    assert repo.get("r1") is None
    with pytest.raises(RecipeNotFound):
        repo.delete("r1")
