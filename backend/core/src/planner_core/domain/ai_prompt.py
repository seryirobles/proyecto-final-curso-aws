"""Provider-agnostic AI prompt assembly: single-recipe and whole-week category-targeted requests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from planner_core.domain.errors import PlannerError
from planner_core.domain.recipe import Recipe
from planner_core.domain.rules import CategoryCountRule
from planner_core.domain.units import Unit

OUTPUT_LANGUAGE: Final[str] = "es-ES"
"""FR-AI-07: AI output is produced in Castilian Spanish."""

HEALTHY_BALANCED_INSTRUCTION: Final[str] = (
    "Genera un menu saludable y equilibrado, variando las fuentes de proteina "
    "entre los platos. Esta indicacion tiene fines de planificacion domestica "
    "y no constituye un consejo medico."
)
"""FR-AI-06: healthy/balanced/protein-varied, labelled non-medical (design.md section 4)."""

RECIPE_METADATA_INSTRUCTION: Final[str] = (
    "Indica tambien el numero de comensales y una estimacion del tiempo de "
    "preparacion y coccion para cada receta generada. Son datos meramente "
    "informativos: no ajustes las cantidades de los ingredientes en funcion "
    "de ellos."
)
"""FR-AI-13 (G-86): instructs the model to state both fields itself, never
a target value the app supplies. Second sentence heads off ingredient-
quantity scaling off the stated count - specs/recipe_metadata_fields/design.md section 6."""

ALLOWED_UNITS: Final[tuple[Unit, ...]] = tuple(Unit)
"""FR-LIB-05 (consumed): the fixed unit vocabulary, reused from units.py, never redeclared."""


@dataclass(frozen=True)
class PromptInstructionsVersion:
    """One version of the wording FR-AI-06, FR-AI-07 and FR-AI-13 require (FR-AI-14, R1).

    No per-recipe target field here (R20, G-85/G-86) - recipe_metadata_instruction
    replaces it with an instruction, not a value. See design.md section 6.
    """

    version_id: str
    output_language: str
    healthy_balanced_instruction: str
    recipe_metadata_instruction: str


PROMPT_INSTRUCTION_VERSIONS: Final[dict[str, PromptInstructionsVersion]] = {
    "v1": PromptInstructionsVersion(
        version_id="v1",
        output_language=OUTPUT_LANGUAGE,
        healthy_balanced_instruction=HEALTHY_BALANCED_INSTRUCTION,
        recipe_metadata_instruction=RECIPE_METADATA_INSTRUCTION,
    ),
}
"""Append-only (R2, G-84): a version is added here when wording changes; an
existing key is never removed or overwritten (specs/ai_prompt_versioning/design.md
section 4)."""

PROMPT_VERSION_CONFIG_KEY: Final[str] = "AI_PROMPT_VERSION_ID"
"""The ConfigPort key naming which PROMPT_INSTRUCTION_VERSIONS entry is active (R3)."""


class UnknownPromptVersion(PlannerError):
    """Raised when a prompt version identifier does not resolve, or none is configured (R4)."""


def resolve_prompt_version(version_id: str) -> PromptInstructionsVersion:
    """Every retained version is retrievable by its identifier (R6)."""
    try:
        return PROMPT_INSTRUCTION_VERSIONS[version_id]
    except KeyError:
        raise UnknownPromptVersion(version_id) from None


@dataclass(frozen=True)
class PromptInstructions:
    """The instructions every AI recipe-generation prompt carries, regardless of mode.

    No per-recipe target field here (R19) - see PromptInstructionsVersion above.
    """

    output_language: str
    healthy_balanced_instruction: str
    recipe_metadata_instruction: str
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


def build_instructions(version_id: str) -> PromptInstructions:
    """The shared instruction block every prompt carries.

    output_language, healthy_balanced_instruction and
    recipe_metadata_instruction come from the prompt-instruction version
    named by version_id (FR-AI-14, R25); raises UnknownPromptVersion if it
    does not resolve.
    """
    version = resolve_prompt_version(version_id)
    return PromptInstructions(
        output_language=version.output_language,
        healthy_balanced_instruction=version.healthy_balanced_instruction,
        recipe_metadata_instruction=version.recipe_metadata_instruction,
        allowed_units=ALLOWED_UNITS,
    )


def build_specification_prompt(
    ingredients: tuple[str, ...], tools: tuple[str, ...], version_id: str
) -> SpecificationPrompt:
    """FR-AI-01 (R13-R15)."""
    return SpecificationPrompt(
        instructions=build_instructions(version_id), ingredients=ingredients, tools=tools
    )


def build_reference_prompt(
    reference_recipe: Recipe, extra_specifications: tuple[str, ...], version_id: str
) -> ReferencePrompt:
    """FR-AI-02 (R16-R18)."""
    return ReferencePrompt(
        instructions=build_instructions(version_id),
        reference_recipe=reference_recipe,
        extra_specifications=extra_specifications,
    )


def build_category_prompt(
    category_counts: tuple[CategoryCountRule, ...], version_id: str
) -> CategoryPrompt:
    """FR-AI-04 (R19-R20). category_counts is the caller's snapshot (design.md section 1) —
    typically generation_request's GenerationTargets.remaining_category_counts, passed
    unchanged for one open slot; this function neither reads nor recomputes it."""
    return CategoryPrompt(
        instructions=build_instructions(version_id), category_counts=category_counts
    )
