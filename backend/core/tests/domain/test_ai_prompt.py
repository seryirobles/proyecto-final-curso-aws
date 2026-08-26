"""Tests for AI prompt assembly: shared instructions and the three mode-specific shapes (R1-R20)."""

from __future__ import annotations

import dataclasses

import pytest

from planner_core.domain.ai_prompt import (
    ALLOWED_UNITS,
    CONFIGURED_SERVINGS,
    HEALTHY_BALANCED_INSTRUCTION,
    OUTPUT_LANGUAGE,
    PROMPT_INSTRUCTION_VERSIONS,
    CategoryPrompt,
    PromptInstructions,
    PromptInstructionsVersion,
    ReferencePrompt,
    SpecificationPrompt,
    UnknownPromptVersion,
    build_category_prompt,
    build_instructions,
    build_reference_prompt,
    build_specification_prompt,
    resolve_prompt_version,
)
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Ingredient, Recipe
from planner_core.domain.rules import CategoryCountRule
from planner_core.domain.units import Unit, parse_unit


def _make_recipe() -> Recipe:
    return Recipe(
        name="Lentejas con chorizo",
        ingredients=(Ingredient(name="lentejas", quantity=500, unit=parse_unit("g")),),
        tools=("olla",),
        procedure=("Sofreir el chorizo.", "Anadir las lentejas y cocer."),
        category=IngredientCategory.LEGUME,
    )


def test_configured_servings_is_four() -> None:
    """R1: FR-AI-13, the approved value (design.md section 4)."""
    assert CONFIGURED_SERVINGS == 4
    assert isinstance(CONFIGURED_SERVINGS, int)


def test_output_language_is_es_es() -> None:
    """R2: FR-AI-07."""
    assert OUTPUT_LANGUAGE == "es-ES"


def test_healthy_balanced_instruction_is_non_empty() -> None:
    """R3: FR-AI-06, the approved wording (design.md section 4)."""
    assert HEALTHY_BALANCED_INSTRUCTION == (
        "Genera un menu saludable y equilibrado, variando las fuentes de proteina "
        "entre los platos. Esta indicacion tiene fines de planificacion domestica "
        "y no constituye un consejo medico."
    )


def test_allowed_units_contains_every_unit_member() -> None:
    """R4: FR-LIB-05 (consumed)."""
    assert ALLOWED_UNITS == tuple(Unit)
    assert set(ALLOWED_UNITS) == set(Unit)


def test_prompt_instructions_fields_are_exactly_the_fixed_shape() -> None:
    """R5."""
    field_names = {field.name for field in dataclasses.fields(PromptInstructions)}
    assert field_names == {
        "servings",
        "output_language",
        "healthy_balanced_instruction",
        "allowed_units",
    }


def test_prompt_instructions_is_frozen() -> None:
    """R5: mutating means constructing a new instance (docs/conventions.md)."""
    instructions = build_instructions("v1")

    with pytest.raises(dataclasses.FrozenInstanceError):
        instructions.__setattr__("servings", 6)


def test_build_instructions_matches_the_module_constants() -> None:
    """R6, R7, R8, R9 (specs/ai_prompt_builder/requirements.md, amended by feature 24)."""
    instructions = build_instructions("v1")

    assert instructions.servings == CONFIGURED_SERVINGS
    assert instructions.output_language == OUTPUT_LANGUAGE
    assert instructions.healthy_balanced_instruction == HEALTHY_BALANCED_INSTRUCTION
    assert instructions.allowed_units == ALLOWED_UNITS


def test_build_instructions_sources_content_from_the_named_version() -> None:
    """FR-AI-14, R5: build_instructions(version_id) reads servings, output_language
    and healthy_balanced_instruction from that version's own content, not the
    module constants directly."""
    other_version = PromptInstructionsVersion(
        version_id="v-test-only",
        servings=2,
        output_language="fr-FR",
        healthy_balanced_instruction="Otra instruccion.",
    )
    PROMPT_INSTRUCTION_VERSIONS[other_version.version_id] = other_version
    try:
        instructions = build_instructions(other_version.version_id)
    finally:
        del PROMPT_INSTRUCTION_VERSIONS[other_version.version_id]

    assert instructions.servings == 2
    assert instructions.output_language == "fr-FR"
    assert instructions.healthy_balanced_instruction == "Otra instruccion."
    assert instructions.allowed_units == ALLOWED_UNITS


def test_build_instructions_raises_unknown_prompt_version_for_unregistered_id() -> None:
    """FR-AI-14, R4."""
    with pytest.raises(UnknownPromptVersion):
        build_instructions("does-not-exist")


def test_resolve_prompt_version_registry_carries_every_expected_version() -> None:
    """FR-AI-14, R1, R2, R6: v1 carries feature 11's already-approved constants."""
    assert set(PROMPT_INSTRUCTION_VERSIONS) == {"v1"}

    version = resolve_prompt_version("v1")

    assert version.version_id == "v1"
    assert version.servings == CONFIGURED_SERVINGS
    assert version.output_language == OUTPUT_LANGUAGE
    assert version.healthy_balanced_instruction == HEALTHY_BALANCED_INSTRUCTION


def test_resolve_prompt_version_raises_unknown_prompt_version_for_unregistered_id() -> None:
    """FR-AI-14, R4."""
    with pytest.raises(UnknownPromptVersion):
        resolve_prompt_version("unregistered")


def test_prompt_instructions_version_is_frozen() -> None:
    """FR-AI-14, R1: an immutable value carrying its own version identifier."""
    version = resolve_prompt_version("v1")

    with pytest.raises(dataclasses.FrozenInstanceError):
        version.__setattr__("servings", 6)


def test_specification_prompt_fields_are_exactly_the_fixed_shape() -> None:
    """R10."""
    field_names = {field.name for field in dataclasses.fields(SpecificationPrompt)}
    assert field_names == {"instructions", "ingredients", "tools"}


def test_specification_prompt_is_frozen() -> None:
    """R10: mutating means constructing a new instance (docs/conventions.md)."""
    prompt = build_specification_prompt(("tomate",), ("sarten",), "v1")

    with pytest.raises(dataclasses.FrozenInstanceError):
        prompt.__setattr__("tools", ("olla",))


def test_reference_prompt_fields_are_exactly_the_fixed_shape() -> None:
    """R11."""
    field_names = {field.name for field in dataclasses.fields(ReferencePrompt)}
    assert field_names == {"instructions", "reference_recipe", "extra_specifications"}


def test_reference_prompt_is_frozen() -> None:
    """R11: mutating means constructing a new instance (docs/conventions.md)."""
    prompt = build_reference_prompt(_make_recipe(), ("sin gluten",), "v1")

    with pytest.raises(dataclasses.FrozenInstanceError):
        prompt.__setattr__("extra_specifications", ())


def test_category_prompt_fields_are_exactly_the_fixed_shape() -> None:
    """R12."""
    field_names = {field.name for field in dataclasses.fields(CategoryPrompt)}
    assert field_names == {"instructions", "category_counts"}


def test_category_prompt_is_frozen() -> None:
    """R12: mutating means constructing a new instance (docs/conventions.md)."""
    prompt = build_category_prompt(
        (CategoryCountRule(category=IngredientCategory.MEAT, count=2),), "v1"
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        prompt.__setattr__("category_counts", ())


def test_build_specification_prompt_carries_its_inputs() -> None:
    """R13, R14, R15 (specs/ai_prompt_builder/requirements.md, amended by feature 24)."""
    ingredients = ("tomate", "cebolla")
    tools = ("sarten",)

    result = build_specification_prompt(ingredients, tools, "v1")

    assert result.instructions == build_instructions("v1")
    assert result.ingredients == ingredients
    assert result.tools == tools


def test_build_reference_prompt_carries_its_inputs() -> None:
    """R16, R17, R18 (specs/ai_prompt_builder/requirements.md, amended by feature 24)."""
    recipe = _make_recipe()
    extra_specifications = ("sin gluten",)

    result = build_reference_prompt(recipe, extra_specifications, "v1")

    assert result.instructions == build_instructions("v1")
    assert result.reference_recipe == recipe
    assert result.extra_specifications == extra_specifications


def test_build_category_prompt_carries_its_input() -> None:
    """R19, R20 (specs/ai_prompt_builder/requirements.md, amended by feature 24)."""
    category_counts = (
        CategoryCountRule(category=IngredientCategory.MEAT, count=2),
        CategoryCountRule(category=IngredientCategory.FISH, count=1),
    )

    result = build_category_prompt(category_counts, "v1")

    assert result.instructions == build_instructions("v1")
    assert result.category_counts == category_counts
