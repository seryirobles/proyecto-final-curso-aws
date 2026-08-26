"""Provider-agnostic AI prompt assembly: single-recipe and whole-week category-targeted requests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from planner_core.domain.recipe import Recipe
from planner_core.domain.rules import CategoryCountRule
from planner_core.domain.units import Unit

CONFIGURED_SERVINGS: Final[int] = 4
"""Deployment configuration (G-64); approved at this spec's human gate (design.md section 4)."""

OUTPUT_LANGUAGE: Final[str] = "es-ES"
"""FR-AI-07: AI output is produced in Castilian Spanish."""

HEALTHY_BALANCED_INSTRUCTION: Final[str] = (
    "Genera un menu saludable y equilibrado, variando las fuentes de proteina "
    "entre los platos. Esta indicacion tiene fines de planificacion domestica "
    "y no constituye un consejo medico."
)
"""FR-AI-06: healthy/balanced/protein-varied, labelled non-medical (design.md section 4)."""

ALLOWED_UNITS: Final[tuple[Unit, ...]] = tuple(Unit)
"""FR-LIB-05 (consumed): the fixed unit vocabulary, reused from units.py, never redeclared."""


@dataclass(frozen=True)
class PromptInstructions:
    """The instructions every AI recipe-generation prompt carries, regardless of mode."""

    servings: int
    output_language: str
    healthy_balanced_instruction: str
    allowed_units: tuple[Unit, ...]


@dataclass(frozen=True)
class SpecificationPrompt:
    """FR-AI-01: a single recipe generated from user-supplied ingredients and tools."""

    instructions: PromptInstructions
    ingredients: tuple[str, ...]
    tools: tuple[str, ...]


@dataclass(frozen=True)
class ReferencePrompt:
    """FR-AI-02: a single recipe generated from a chosen library recipe plus specifications."""

    instructions: PromptInstructions
    reference_recipe: Recipe
    extra_specifications: tuple[str, ...]


@dataclass(frozen=True)
class CategoryPrompt:
    """FR-AI-04: one open slot's AI-generated meal, carrying the week's remaining category needs."""

    instructions: PromptInstructions
    category_counts: tuple[CategoryCountRule, ...]


def build_instructions() -> PromptInstructions:
    """The shared instruction block every prompt carries (R6-R9)."""
    return PromptInstructions(
        servings=CONFIGURED_SERVINGS,
        output_language=OUTPUT_LANGUAGE,
        healthy_balanced_instruction=HEALTHY_BALANCED_INSTRUCTION,
        allowed_units=ALLOWED_UNITS,
    )


def build_specification_prompt(
    ingredients: tuple[str, ...], tools: tuple[str, ...]
) -> SpecificationPrompt:
    """FR-AI-01 (R13-R15)."""
    return SpecificationPrompt(
        instructions=build_instructions(), ingredients=ingredients, tools=tools
    )


def build_reference_prompt(
    reference_recipe: Recipe, extra_specifications: tuple[str, ...]
) -> ReferencePrompt:
    """FR-AI-02 (R16-R18)."""
    return ReferencePrompt(
        instructions=build_instructions(),
        reference_recipe=reference_recipe,
        extra_specifications=extra_specifications,
    )


def build_category_prompt(category_counts: tuple[CategoryCountRule, ...]) -> CategoryPrompt:
    """FR-AI-04 (R19-R20). category_counts is the caller's snapshot (design.md section 1) —
    typically generation_request's GenerationTargets.remaining_category_counts, passed
    unchanged for one open slot; this function neither reads nor recomputes it."""
    return CategoryPrompt(instructions=build_instructions(), category_counts=category_counts)
