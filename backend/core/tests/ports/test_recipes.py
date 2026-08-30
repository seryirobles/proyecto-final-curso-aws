"""Tests for the RecipeRepository port and its in-memory fake."""

from __future__ import annotations

import dataclasses
from typing import get_type_hints

import pytest
from support.fakes import FakeRecipeRepository

from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Recipe
from planner_core.ports.recipes import LibraryRecipe, RecipeNotFound, RecipeRepository


def _recipe(name: str = "Tortilla") -> Recipe:
    return Recipe(
        name=name,
        ingredients=(),
        tools=(),
        procedure=(),
        category=IngredientCategory.EGGS,
    )


def test_library_recipe_is_frozen() -> None:
    """docs/conventions.md: every new frozen dataclass gets this test."""
    entry = LibraryRecipe(id="r1", recipe=_recipe(), author="u1")
    with pytest.raises(dataclasses.FrozenInstanceError):
        entry.__setattr__("author", "u2")


def test_fake_recipe_repository_satisfies_the_recipe_repository_port() -> None:
    assert isinstance(FakeRecipeRepository(), RecipeRepository)


def test_save_then_get_and_list_round_trip() -> None:
    repo = FakeRecipeRepository()
    entry = LibraryRecipe(id="r1", recipe=_recipe(), author="u1")

    repo.save(entry)

    assert repo.get("r1") == entry
    assert repo.list_all() == (entry,)


def test_save_overwrites_by_id() -> None:
    repo = FakeRecipeRepository()
    repo.save(LibraryRecipe(id="r1", recipe=_recipe("Tortilla"), author="u1"))
    repo.save(LibraryRecipe(id="r1", recipe=_recipe("Tortilla de patata"), author="u1"))

    entry = repo.get("r1")
    assert entry is not None
    assert entry.recipe.name == "Tortilla de patata"
    assert repo.list_all() == (entry,)


def test_get_returns_none_when_absent() -> None:
    assert FakeRecipeRepository().get("missing") is None


def test_delete_removes_the_entry() -> None:
    repo = FakeRecipeRepository()
    repo.save(LibraryRecipe(id="r1", recipe=_recipe(), author="u1"))

    repo.delete("r1")

    assert repo.get("r1") is None
    assert repo.list_all() == ()


def test_delete_raises_recipe_not_found_for_a_missing_id() -> None:
    with pytest.raises(RecipeNotFound):
        FakeRecipeRepository().delete("missing")


# --- change marker (FR-RT-01): R1, R2, R3, R4, R5 ---


def test_the_recipe_repository_protocol_pins_the_marker_surface() -> None:
    """R1: current_version and the int-returning writes are on the Protocol
    itself, not only the fake — deleting either from ports/recipes.py fails here."""
    assert "current_version" in RecipeRepository.__dict__
    for method in ("save", "delete"):
        assert get_type_hints(getattr(RecipeRepository, method))["return"] is int


def test_current_version_is_zero_before_any_write() -> None:
    assert FakeRecipeRepository().current_version() == 0  # R3


def test_save_and_delete_advance_the_marker_and_return_the_new_value() -> None:
    repo = FakeRecipeRepository()
    entry = LibraryRecipe(id="r1", recipe=_recipe(), author="u1")

    saved = repo.save(entry)
    assert saved == 1  # R4, R5
    assert repo.current_version() == saved  # R4

    deleted = repo.delete("r1")
    assert deleted == 2
    assert repo.current_version() == deleted  # R4


def test_reads_do_not_advance_the_marker() -> None:
    repo = FakeRecipeRepository()
    repo.save(LibraryRecipe(id="r1", recipe=_recipe(), author="u1"))

    repo.get("r1")
    repo.list_all()
    repo.current_version()

    assert repo.current_version() == 1  # R2
