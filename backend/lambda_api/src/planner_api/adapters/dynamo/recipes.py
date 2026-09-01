"""DynamoDB `RecipeRepository` — BIBLIOTECA partition (docs/data_model.md
section 1, section 4.3). AP14 excludes MARCA with begins_with(SK, 'ID#')."""

from __future__ import annotations

from typing import Any

from planner_core.domain.recipe import Recipe
from planner_core.ports.recipes import LibraryRecipe, RecipeNotFound

from planner_api.adapters.dynamo import _meal, _table

_ID_PREFIX = "ID#"


def _pk() -> str:
    return f"BIBLIOTECA#{_table.LIBRARY_ID}"


def _sk(recipe_id: str) -> str:
    return f"{_ID_PREFIX}{recipe_id}"


def _to_entry(item: dict[str, Any]) -> LibraryRecipe:
    recipe = Recipe(
        name=str(item["nombrePlato"]),
        ingredients=_meal.read_ingredients(item),
        tools=_meal.read_tools(item),
        procedure=_meal.read_procedure(item),
        category=_meal.read_category(item),
        servings=_meal.read_servings(item),
        estimated_time=_meal.read_estimated_time(item),
    )
    return LibraryRecipe(
        id=str(item["SK"]).removeprefix(_ID_PREFIX),
        recipe=recipe,
        author=str(item["añadidoPor"]),
    )


def _item(entry: LibraryRecipe) -> dict[str, Any]:
    recipe = entry.recipe
    return {
        "PK": _pk(),
        "SK": _sk(entry.id),
        "añadidoPor": entry.author,
        **_meal.content_attrs(
            name=recipe.name,
            ingredients=recipe.ingredients,
            tools=recipe.tools,
            procedure=recipe.procedure,
            category=recipe.category,
            servings=recipe.servings,
            estimated_time=recipe.estimated_time,
        ),
    }


class DynamoRecipeRepository:
    def current_version(self) -> int:
        return _table.read_marker(_pk())

    def get(self, recipe_id: str) -> LibraryRecipe | None:
        item = _table.get_item(_pk(), _sk(recipe_id))
        return _to_entry(item) if item is not None else None

    def list_all(self) -> tuple[LibraryRecipe, ...]:
        return tuple(_to_entry(row) for row in _table.query_prefix(_pk(), _ID_PREFIX))

    def save(self, entry: LibraryRecipe) -> int:
        return _table.commit(_pk(), [_table.put_action(_item(entry))])

    def delete(self, recipe_id: str) -> int:
        if _table.get_item(_pk(), _sk(recipe_id)) is None:
            raise RecipeNotFound(recipe_id)
        return _table.commit(_pk(), [_table.delete_action(_pk(), _sk(recipe_id))])
