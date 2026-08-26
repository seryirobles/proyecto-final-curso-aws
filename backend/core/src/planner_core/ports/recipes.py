"""The recipe repository port: persistence for BIBLIOTECA (docs/data_model.md section 1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from planner_core.domain.errors import PlannerError
from planner_core.domain.recipe import Recipe


@dataclass(frozen=True)
class LibraryRecipe:
    """A library recipe as persisted: its id and author alongside its Recipe
    content. Recipe itself carries neither (design.md section 7)."""

    id: str
    recipe: Recipe
    author: str


class RecipeNotFound(PlannerError):
    """Raised when an operation targets a recipe_id absent from the repository."""

    recipe_id: str

    def __init__(self, recipe_id: str) -> None:
        super().__init__(recipe_id)
        self.recipe_id = recipe_id


@runtime_checkable
class RecipeRepository(Protocol):
    """Persistence for the shared recipe library."""

    def get(self, recipe_id: str) -> LibraryRecipe | None: ...

    def list_all(self) -> tuple[LibraryRecipe, ...]: ...

    def save(self, entry: LibraryRecipe) -> None:
        """Create or overwrite by id (AP16 is a PutItem — an upsert)."""
        ...

    def delete(self, recipe_id: str) -> None:
        """Raises RecipeNotFound."""
        ...
