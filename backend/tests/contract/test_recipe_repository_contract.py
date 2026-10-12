"""Contract suite for RecipeRepository: one suite, run against every registered
implementation (R9)."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Recipe
from planner_core.ports.recipes import LibraryRecipe, RecipeNotFound, RecipeRepository
from support.fakes import FakeRecipeRepository

from tests.contract.dynamo_contract import ai_dynamo_recipe_repository, dynamo_recipe_repository

IMPLEMENTATIONS: list[Callable[[], RecipeRepository]] = [
    FakeRecipeRepository,
    dynamo_recipe_repository,
    ai_dynamo_recipe_repository,  # the planner_ai copy (week_generation_backend R16)
]


def _recipe(name: str = "Tortilla") -> Recipe:
    return Recipe(
        name=name, ingredients=(), tools=(), procedure=(), category=IngredientCategory.EGGS
    )


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_save_then_get_and_list_round_trip(
    repository_factory: Callable[[], RecipeRepository],
) -> None:
    repo = repository_factory()
    entry = LibraryRecipe(id="r1", recipe=_recipe(), author="u1")

    repo.save(entry)

    assert repo.get("r1") == entry
    assert repo.list_all() == (entry,)


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_save_overwrites_by_id(repository_factory: Callable[[], RecipeRepository]) -> None:
    repo = repository_factory()
    repo.save(LibraryRecipe(id="r1", recipe=_recipe("Tortilla"), author="u1"))

    repo.save(LibraryRecipe(id="r1", recipe=_recipe("Tortilla de patata"), author="u1"))

    entry = repo.get("r1")
    assert entry is not None
    assert entry.recipe.name == "Tortilla de patata"


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_delete_removes_the_entry_and_raises_when_missing(
    repository_factory: Callable[[], RecipeRepository],
) -> None:
    repo = repository_factory()
    repo.save(LibraryRecipe(id="r1", recipe=_recipe(), author="u1"))

    repo.delete("r1")

    assert repo.get("r1") is None
    with pytest.raises(RecipeNotFound):
        repo.delete("r1")


# --- change marker (FR-RT-01): R2, R4, R5, R8, R11 ---


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_every_mutating_method_advances_the_marker_and_returns_the_new_value(
    repository_factory: Callable[[], RecipeRepository],
) -> None:
    repo = repository_factory()
    entry = LibraryRecipe(id="r1", recipe=_recipe(), author="u1")

    assert repo.save(entry) == 1  # R4, R5
    assert repo.current_version() == 1
    assert repo.delete("r1") == 2
    assert repo.current_version() == 2


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_reads_leave_the_marker_unchanged(
    repository_factory: Callable[[], RecipeRepository],
) -> None:
    repo = repository_factory()
    repo.save(LibraryRecipe(id="r1", recipe=_recipe(), author="u1"))

    repo.get("r1")
    repo.list_all()
    repo.current_version()

    assert repo.current_version() == 1  # R2


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_two_successive_writes_both_apply_and_advance_the_marker_twice(
    repository_factory: Callable[[], RecipeRepository],
) -> None:
    repo = repository_factory()
    entry = LibraryRecipe(id="r1", recipe=_recipe(), author="u1")

    first = repo.save(entry)
    second = repo.save(entry)  # no raise: upsert, last-write-wins (R8)

    assert (first, second) == (1, 2)  # R11
