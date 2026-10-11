"""The closed ingredient-category vocabulary and its one entry point (FR-RULE-04)."""

from __future__ import annotations

from enum import StrEnum

from planner_core.domain.errors import PlannerError


class IngredientCategory(StrEnum):
    """The predominant ingredient category a recipe is filed under.

    Six ingredient-only terms (FR-RULE-04, G-69, G-82); the earlier diet-label
    member was struck for mixing axes with the rest. A dish is filed under
    whichever single member the author judges predominant.
    """

    MEAT = "meat"
    FISH = "fish"
    CARBOHYDRATE = "carbohydrate"
    LEGUME = "legume"
    VEGETABLE = "vegetable"
    EGGS = "eggs"


class UnknownIngredientCategory(PlannerError):
    """Raised when a value is not a member of the fixed category list.

    Carries the rejected value and nothing else. The Castilian rejection text
    belongs to the feature that owns the user-facing flow (docs/conventions.md,
    Language policy).
    """

    value: str

    def __init__(self, value: str) -> None:
        super().__init__(value)
        self.value = value


def parse_category(value: str) -> IngredientCategory:
    """Resolve a category code to its member, or raise UnknownIngredientCategory."""
    # Exact match only, mirroring parse_unit (design.md section 6): the value
    # comes from a dropdown or AI output whose schema restricts it to the codes (G-48 backstop).
    for category in IngredientCategory:
        if value == category.value:
            return category
    raise UnknownIngredientCategory(value)
