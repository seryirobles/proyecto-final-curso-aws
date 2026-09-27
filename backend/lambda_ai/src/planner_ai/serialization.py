"""The recipe wire shape the `ai` worker writes and reads. A deliberate copy of
`planner_api.serialization`'s encoder, kept in step by a parity test
(specs/single_recipe_generation/design.md sections 2 and 6)."""

from __future__ import annotations

from typing import Any  # untyped JSON in/out is the wire boundary itself (conventions.md)

from planner_core.domain.ingredient_category import parse_category
from planner_core.domain.recipe import Ingredient, Recipe
from planner_core.domain.units import parse_unit


def encode_recipe(recipe: Recipe) -> dict[str, Any]:
    return {
        "name": recipe.name,
        "category": recipe.category.value,
        "servings": recipe.servings,
        "estimatedTime": recipe.estimated_time,
        "ingredients": [
            {"name": i.name, "quantity": i.quantity, "unit": i.unit.value}
            for i in recipe.ingredients
        ],
        "tools": list(recipe.tools),
        "procedure": list(recipe.procedure),
    }


def decode_recipe(payload: dict[str, Any]) -> Recipe:
    """The reference snapshot the api put on the message; it is already-stored
    library content, so no write-boundary section rule applies here."""
    return Recipe(
        name=str(payload["name"]),
        ingredients=tuple(
            Ingredient(
                name=str(i["name"]), quantity=float(i["quantity"]), unit=parse_unit(str(i["unit"]))
            )
            for i in payload["ingredients"]
        ),
        tools=tuple(str(t) for t in payload["tools"]),
        procedure=tuple(str(s) for s in payload["procedure"]),
        category=parse_category(str(payload["category"])),
        servings=payload.get("servings"),
        estimated_time=payload.get("estimatedTime"),
    )
