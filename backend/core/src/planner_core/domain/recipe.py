"""Recipe content shape and the value-object snapshot taken when it enters a week."""

from __future__ import annotations

from dataclasses import dataclass

from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.units import Unit


@dataclass(frozen=True)
class Ingredient:
    """A quantity of a named ingredient in the fixed unit vocabulary.

    unit takes an already-resolved Unit, never a raw string: the caller
    resolves it explicitly via parse_unit (design.md section 6, rejected
    alternative B).
    """

    name: str
    quantity: float
    unit: Unit


@dataclass(frozen=True)
class Recipe:
    """A library recipe's immutable content (FR-LIB-03).

    No cuisine, difficulty or kcal field (G-68, G-36).
    """

    name: str
    ingredients: tuple[Ingredient, ...]
    tools: tuple[str, ...]
    procedure: tuple[str, ...]
    category: IngredientCategory


@dataclass(frozen=True)
class MealSnapshot:
    """The copy of a recipe's content taken when it enters a week (FR-CAND-07).

    A distinct type from Recipe, holding no reference back to it, so a later
    library edit or delete can never retroactively mutate a week (G-05).
    """

    name: str
    ingredients: tuple[Ingredient, ...]
    tools: tuple[str, ...]
    procedure: tuple[str, ...]
    category: IngredientCategory


def snapshot(recipe: Recipe) -> MealSnapshot:
    """Return a MealSnapshot decoupled from recipe (FR-CAND-07, G-05)."""
    return MealSnapshot(
        name=recipe.name,
        ingredients=recipe.ingredients,
        tools=recipe.tools,
        procedure=recipe.procedure,
        category=recipe.category,
    )
