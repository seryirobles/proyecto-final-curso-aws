"""Recipe content shape and the value-object snapshot taken when it enters a week."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from planner_core.domain.errors import PlannerError
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.units import Unit

MAX_ESTIMATED_MINUTES: Final[int] = 6000
"""G-90: the permitted estimated_time range is 0 to this value, inclusive."""


class InvalidEstimatedTime(PlannerError):
    """Raised when estimated_time is not an integer minute count in
    [0, MAX_ESTIMATED_MINUTES] (G-90, amending G-85/FR-LIB-03)."""


def parse_estimated_minutes(value: Any) -> int | None:
    """`None` stays `None`; a non-`int` (a `bool` included) or an out-of-range
    integer raises. Called at both write boundaries only - never a
    constructor invariant, so a recipe already persisted under G-85's free
    text stays readable (G-90, same reasoning as G-89)."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidEstimatedTime(value)
    if not (0 <= value <= MAX_ESTIMATED_MINUTES):
        raise InvalidEstimatedTime(value)
    return value


class InvalidIngredientQuantity(PlannerError):
    """Raised when an ingredient quantity is not strictly greater than zero
    (issue negative-ingredient-quantity, Part H delegates the bound itself)."""


def parse_quantity(value: float) -> float:
    """Strictly positive, mirroring parse_unit/parse_category: the caller
    resolves the field before constructing Ingredient (design.md section 6)."""
    if not value > 0:
        raise InvalidIngredientQuantity(value)
    return value


class InvalidServings(PlannerError):
    """Raised when servings is present but not a strictly positive integer
    (G-91, Part AA, amending G-85/FR-LIB-03/FR-AI-13)."""


def parse_servings_count(value: int | None) -> int | None:
    """`None` stays `None` (servings is optional); called at both write
    boundaries only, never a constructor invariant - a recipe already
    persisted with servings <= 0 stays readable (same reasoning as G-90)."""
    if value is None:
        return None
    if value <= 0:
        raise InvalidServings(value)
    return value


class MissingIngredients(PlannerError):
    """Raised when a recipe write's ingredients list is empty or absent
    (G-89, Part Y, amending FR-LIB-03)."""


class MissingTools(PlannerError):
    """Raised when a recipe write's tools list is empty or absent (G-89)."""


class MissingProcedure(PlannerError):
    """Raised when a recipe write's procedure list is empty or absent (G-89)."""


def require_recipe_sections(
    ingredients: tuple[Ingredient, ...],
    tools: tuple[str, ...],
    procedure: tuple[str, ...],
) -> None:
    """Each of the three lists carries at least one item (G-89, Part Y).
    Called at both write boundaries only - never a constructor invariant
    (Recipe itself stays permissive), so a recipe already persisted with an
    empty section stays readable."""
    if len(ingredients) == 0:
        raise MissingIngredients
    if len(tools) == 0:
        raise MissingTools
    if len(procedure) == 0:
        raise MissingProcedure


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

    No cuisine, difficulty or kcal field (G-68, G-36). servings/estimated_time
    are purely informational (G-85) - see test_no_recipe_metadata_logic.py.
    estimated_time is a whole minute count, 0-6000 inclusive, or absent
    (G-90); no constructor check - see parse_estimated_minutes above.
    """

    name: str
    ingredients: tuple[Ingredient, ...]
    tools: tuple[str, ...]
    procedure: tuple[str, ...]
    category: IngredientCategory
    servings: int | None = None
    estimated_time: int | None = None


@dataclass(frozen=True)
class MealSnapshot:
    """The copy of a recipe's content taken when it enters a week (FR-CAND-07).

    A distinct type from Recipe, holding no reference back to it, so a later
    library edit or delete can never retroactively mutate a week (G-05).
    Mirrors Recipe's shape field-for-field (G-85) - see snapshot() below.
    """

    name: str
    ingredients: tuple[Ingredient, ...]
    tools: tuple[str, ...]
    procedure: tuple[str, ...]
    category: IngredientCategory
    servings: int | None = None
    estimated_time: int | None = None


def snapshot(recipe: Recipe) -> MealSnapshot:
    """Return a MealSnapshot decoupled from recipe (FR-CAND-07, G-05)."""
    return MealSnapshot(
        name=recipe.name,
        ingredients=recipe.ingredients,
        tools=recipe.tools,
        procedure=recipe.procedure,
        category=recipe.category,
        servings=recipe.servings,
        estimated_time=recipe.estimated_time,
    )
