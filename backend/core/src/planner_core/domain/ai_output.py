"""AI recipe output validation and the single-recipe preview lifecycle (FR-AI-10, FR-AI-12)."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from enum import StrEnum

from planner_core.domain.calendar import SlotRef
from planner_core.domain.ingredient_category import UnknownIngredientCategory, parse_category
from planner_core.domain.recipe import (
    Ingredient,
    InvalidEstimatedTime,
    InvalidIngredientQuantity,
    InvalidServings,
    MissingIngredients,
    MissingProcedure,
    MissingTools,
    Recipe,
    parse_estimated_minutes,
    parse_quantity,
    parse_servings_count,
    require_recipe_sections,
)
from planner_core.domain.units import UnknownUnit, parse_unit
from planner_core.messages import (
    AI_GENERATION_INSUFFICIENT_LIBRARY_RECIPES,
    AI_GENERATION_INVALID_OUTPUT,
    AI_GENERATION_UNAVAILABLE,
)


@dataclass(frozen=True)
class RawIngredient:
    """One ingredient line from an already-parsed, provider-agnostic AI response."""

    name: str
    quantity: float
    unit: str


@dataclass(frozen=True)
class RawRecipeOutput:
    """A single AI-generated recipe, already-parsed but not yet validated (design.md section 1)."""

    name: str
    ingredients: tuple[RawIngredient, ...]
    tools: tuple[str, ...]
    procedure: tuple[str, ...]
    category: str
    servings: int | None = None
    estimated_time: int | str | None = None


def validate_ai_recipe_output(raw: RawRecipeOutput) -> Recipe:
    """Resolve raw's unit and category strings against the fixed vocabularies (G-48).

    Raises UnknownUnit or UnknownIngredientCategory rather than building a
    Recipe from unresolved data. Each ingredient's quantity is resolved
    through parse_quantity (issue negative-ingredient-quantity): a
    non-positive value raises InvalidIngredientQuantity. servings is resolved
    through parse_servings_count (G-91, amending G-85): a non-positive value
    raises InvalidServings; absence is not a failure. estimated_time is
    resolved through parse_estimated_minutes (G-90): free text or an
    out-of-range value raises InvalidEstimatedTime rather than persisting.
    """
    ingredients = tuple(
        Ingredient(
            name=item.name, quantity=parse_quantity(item.quantity), unit=parse_unit(item.unit)
        )
        for item in raw.ingredients
    )
    require_recipe_sections(ingredients, raw.tools, raw.procedure)  # G-89, Part Y
    return Recipe(
        name=raw.name,
        ingredients=ingredients,
        tools=raw.tools,
        procedure=raw.procedure,
        category=parse_category(raw.category),
        servings=parse_servings_count(raw.servings),
        estimated_time=parse_estimated_minutes(raw.estimated_time),
    )


@dataclass(frozen=True)
class RecipePreview:
    """A validated recipe not yet persisted (FR-AI-10); no quota, count or usage field (G-70)."""

    recipe: Recipe


def new_preview(recipe: Recipe) -> RecipePreview:
    """Wrap recipe as a not-yet-persisted preview."""
    return RecipePreview(recipe=recipe)


def accept_preview(preview: RecipePreview) -> Recipe:
    """Return the recipe to persist; persistence is the caller's job (design.md section 1)."""
    return preview.recipe


def discard_preview(preview: RecipePreview) -> None:
    """Nothing was ever persisted (R13), so discarding is simply not keeping the reference."""
    return None


class GenerationFailureReason(StrEnum):
    """Named failure causes a per-slot generation result can carry (FR-AI-12, G-66)."""

    INVALID_OUTPUT = "invalid_output"
    INSUFFICIENT_LIBRARY_RECIPES = "insufficient_library_recipes"
    GENERATION_UNAVAILABLE = "generation_unavailable"


@dataclass(frozen=True)
class GenerationFailure:
    """A named, es-ES-messaged generation failure (FR-AI-12)."""

    reason: GenerationFailureReason
    message: str
    # Diagnostic only, never on the wire (issue 14 E1); excluded from equality.
    cause: str | None = field(default=None, compare=False)


@dataclass(frozen=True)
class GenerationSuccess:
    """A successful single-recipe generation, not yet accepted (FR-AI-10)."""

    preview: RecipePreview


GenerationOutcome = GenerationSuccess | GenerationFailure

_FAILURE_MESSAGES: dict[GenerationFailureReason, str] = {
    GenerationFailureReason.INVALID_OUTPUT: AI_GENERATION_INVALID_OUTPUT,
    GenerationFailureReason.INSUFFICIENT_LIBRARY_RECIPES: (
        AI_GENERATION_INSUFFICIENT_LIBRARY_RECIPES
    ),
    GenerationFailureReason.GENERATION_UNAVAILABLE: AI_GENERATION_UNAVAILABLE,
}


def build_generation_failure(reason: GenerationFailureReason) -> GenerationFailure:
    """Pair reason with its es-ES message constant (FR-UX-03)."""
    return GenerationFailure(reason=reason, message=_FAILURE_MESSAGES[reason])


_CAUSE_VALUE_LIMIT = 100


def _describe(exc: Exception) -> str:
    """Validator class name plus its offending value, capped (issue 14 E3)."""
    value = f" {str(exc.args[0])[:_CAUSE_VALUE_LIMIT]}" if exc.args else ""
    return f"{type(exc).__name__}{value}"


def validate_and_preview(raw: RawRecipeOutput) -> GenerationOutcome:
    """Validate raw and surface the result as a value, never a propagated raise (G-48)."""
    try:
        recipe = validate_ai_recipe_output(raw)
    except (
        UnknownUnit,
        UnknownIngredientCategory,
        InvalidEstimatedTime,
        InvalidIngredientQuantity,
        InvalidServings,
        MissingIngredients,
        MissingTools,
        MissingProcedure,
    ) as exc:
        failure = build_generation_failure(GenerationFailureReason.INVALID_OUTPUT)
        return dataclasses.replace(failure, cause=_describe(exc))
    return GenerationSuccess(preview=new_preview(recipe))


@dataclass(frozen=True)
class SlotGenerationResult:
    """One slot's generation outcome, independent of any other slot's (FR-AI-09, FR-AI-12)."""

    slot: SlotRef
    outcome: GenerationOutcome
