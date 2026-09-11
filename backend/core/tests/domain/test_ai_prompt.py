"""Tests for AI prompt assembly: shared instructions and the three mode-specific shapes.

R1-R20 below are specs/ai_prompt_builder/requirements.md (feature 11).
Tests naming R18-R25 explicitly are specs/recipe_metadata_fields/requirements.md
(feature 25) instead - the two specs' numbering collides, disambiguated by name.
"""

from __future__ import annotations

import dataclasses

import pytest

from planner_core.domain.ai_prompt import (
    ALLOWED_UNITS,
    ALLOWED_UNITS_TEMPLATE,
    ALLOWED_UNITS_TEMPLATE_V2,
    CATEGORY_FRAMING_TEMPLATE,
    CATEGORY_FRAMING_TEMPLATE_V2,
    HEALTHY_BALANCED_INSTRUCTION,
    HEALTHY_BALANCED_INSTRUCTION_V2,
    JSON_OUTPUT_INSTRUCTION,
    JSON_OUTPUT_INSTRUCTION_V2,
    OUTPUT_LANGUAGE,
    OUTPUT_LANGUAGE_TEMPLATE,
    OUTPUT_LANGUAGE_TEMPLATE_V2,
    PROMPT_INSTRUCTION_VERSIONS,
    RECIPE_METADATA_INSTRUCTION,
    RECIPE_METADATA_INSTRUCTION_V2,
    REFERENCE_FRAMING_TEMPLATE,
    REFERENCE_FRAMING_TEMPLATE_V2,
    SPECIFICATION_FRAMING_TEMPLATE,
    SPECIFICATION_FRAMING_TEMPLATE_V2,
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


def test_recipe_metadata_instruction_is_the_approved_wording() -> None:
    """recipe_metadata_fields R23, R24 (G-86): the approved wording (design.md section 6)."""
    assert RECIPE_METADATA_INSTRUCTION == (
        "Indica tambien el numero de comensales y una estimacion del tiempo de "
        "preparacion y coccion para cada receta generada. Son datos meramente "
        "informativos: no ajustes las cantidades de los ingredientes en funcion "
        "de ellos."
    )


def test_allowed_units_contains_every_unit_member() -> None:
    """R4: FR-LIB-05 (consumed)."""
    assert ALLOWED_UNITS == tuple(Unit)
    assert set(ALLOWED_UNITS) == set(Unit)


def test_prompt_instructions_fields_are_exactly_the_fixed_shape() -> None:
    """R5, amended by recipe_metadata_fields R19: no servings field,
    recipe_metadata_instruction added."""
    field_names = {field.name for field in dataclasses.fields(PromptInstructions)}
    assert field_names == {
        "output_language",
        "healthy_balanced_instruction",
        "recipe_metadata_instruction",
        "allowed_units",
        "json_output_instruction",
        "output_language_template",
        "allowed_units_template",
        "category_framing_template",
        "specification_framing_template",
        "reference_framing_template",
    }


def test_prompt_instructions_is_frozen() -> None:
    """R5: mutating means constructing a new instance (docs/conventions.md)."""
    instructions = build_instructions("v1")

    with pytest.raises(dataclasses.FrozenInstanceError):
        instructions.__setattr__("output_language", "en-US")


def test_build_instructions_matches_the_module_constants() -> None:
    """R6, R7, R8, R9 (specs/ai_prompt_builder/requirements.md, amended by features 24, 25)."""
    instructions = build_instructions("v1")

    assert instructions.output_language == OUTPUT_LANGUAGE
    assert instructions.healthy_balanced_instruction == HEALTHY_BALANCED_INSTRUCTION
    assert instructions.recipe_metadata_instruction == RECIPE_METADATA_INSTRUCTION
    assert instructions.allowed_units == ALLOWED_UNITS
    assert instructions.json_output_instruction == JSON_OUTPUT_INSTRUCTION
    assert instructions.output_language_template == OUTPUT_LANGUAGE_TEMPLATE
    assert instructions.allowed_units_template == ALLOWED_UNITS_TEMPLATE
    assert instructions.category_framing_template == CATEGORY_FRAMING_TEMPLATE
    assert instructions.specification_framing_template == SPECIFICATION_FRAMING_TEMPLATE
    assert instructions.reference_framing_template == REFERENCE_FRAMING_TEMPLATE


def test_build_instructions_sources_content_from_the_named_version() -> None:
    """FR-AI-14, R5: build_instructions(version_id) reads output_language,
    healthy_balanced_instruction and recipe_metadata_instruction from that
    version's own content, not the module constants directly."""
    other_version = PromptInstructionsVersion(
        version_id="v-test-only",
        output_language="fr-FR",
        healthy_balanced_instruction="Otra instruccion.",
        recipe_metadata_instruction="Otra instruccion de metadatos.",
        json_output_instruction="Otra instruccion JSON.",
        output_language_template="Langue: ${language}.",
        allowed_units_template="Unites: ${units}.",
        category_framing_template="Besoins: ${needs}.",
        specification_framing_template="Ingredients: ${ingredients}. Outils: ${tools}.",
        reference_framing_template="Reference: ${recipe}. Specs: ${specifications}.",
    )
    PROMPT_INSTRUCTION_VERSIONS[other_version.version_id] = other_version
    try:
        instructions = build_instructions(other_version.version_id)
    finally:
        del PROMPT_INSTRUCTION_VERSIONS[other_version.version_id]

    assert instructions.output_language == "fr-FR"
    assert instructions.healthy_balanced_instruction == "Otra instruccion."
    assert instructions.recipe_metadata_instruction == "Otra instruccion de metadatos."
    assert instructions.allowed_units == ALLOWED_UNITS
    assert instructions.json_output_instruction == "Otra instruccion JSON."
    assert instructions.category_framing_template == "Besoins: ${needs}."


def test_build_instructions_raises_unknown_prompt_version_for_unregistered_id() -> None:
    """FR-AI-14, R4."""
    with pytest.raises(UnknownPromptVersion):
        build_instructions("does-not-exist")


def test_healthy_balanced_instruction_v2_is_the_approved_english_wording() -> None:
    """2026-09-11 owner correction: literal content, not a self-comparison against
    the same constant (R1), so a blanked constant fails this test."""
    assert HEALTHY_BALANCED_INSTRUCTION_V2 == (
        "Generate a healthy, balanced menu, varying the protein sources across "
        "dishes. This instruction is for household meal-planning purposes only "
        "and does not constitute medical advice."
    )


def test_recipe_metadata_instruction_v2_is_the_approved_english_wording() -> None:
    """2026-09-11 owner correction: literal content, not a self-comparison against
    the same constant (R1), so a blanked constant fails this test."""
    assert RECIPE_METADATA_INSTRUCTION_V2 == (
        "Also state the number of diners it serves and an estimated preparation "
        "and cooking time for each generated recipe. These are purely "
        "informational: do not adjust the ingredient quantities based on them."
    )


def test_resolve_prompt_version_registry_carries_every_expected_version() -> None:
    """FR-AI-14, R1, R2, R6: v1 carries feature 11's/feature 25's already-approved
    constants; v2 (2026-09-11 owner correction) adds the English instruction wording."""
    assert set(PROMPT_INSTRUCTION_VERSIONS) == {"v1", "v2"}

    version = resolve_prompt_version("v1")

    assert version.version_id == "v1"
    assert version.output_language == OUTPUT_LANGUAGE
    assert version.healthy_balanced_instruction == HEALTHY_BALANCED_INSTRUCTION
    assert version.recipe_metadata_instruction == RECIPE_METADATA_INSTRUCTION


def test_resolve_prompt_version_v2_carries_the_english_wording() -> None:
    """R2, R6: v2 is retained and retrievable, English wording, same es-ES output."""
    version = resolve_prompt_version("v2")

    assert version.version_id == "v2"
    assert version.output_language == OUTPUT_LANGUAGE == "es-ES"
    assert version.healthy_balanced_instruction == HEALTHY_BALANCED_INSTRUCTION_V2
    assert version.recipe_metadata_instruction == RECIPE_METADATA_INSTRUCTION_V2
    assert version.json_output_instruction == JSON_OUTPUT_INSTRUCTION_V2
    assert version.output_language_template == OUTPUT_LANGUAGE_TEMPLATE_V2
    assert version.allowed_units_template == ALLOWED_UNITS_TEMPLATE_V2
    assert version.category_framing_template == CATEGORY_FRAMING_TEMPLATE_V2
    assert version.specification_framing_template == SPECIFICATION_FRAMING_TEMPLATE_V2
    assert version.reference_framing_template == REFERENCE_FRAMING_TEMPLATE_V2


def test_build_instructions_v2_sources_from_the_v2_constants() -> None:
    """R5: build_instructions("v2") reads v2's content, proving v1 stays untouched
    (append-only) while a second version is genuinely reachable."""
    instructions = build_instructions("v2")

    assert instructions.output_language == OUTPUT_LANGUAGE
    assert instructions.healthy_balanced_instruction == HEALTHY_BALANCED_INSTRUCTION_V2
    assert instructions.recipe_metadata_instruction == RECIPE_METADATA_INSTRUCTION_V2
    assert instructions.json_output_instruction == JSON_OUTPUT_INSTRUCTION_V2


def test_resolve_prompt_version_raises_unknown_prompt_version_for_unregistered_id() -> None:
    """FR-AI-14, R4."""
    with pytest.raises(UnknownPromptVersion):
        resolve_prompt_version("unregistered")


def test_prompt_instructions_version_is_frozen() -> None:
    """FR-AI-14, R1: an immutable value carrying its own version identifier."""
    version = resolve_prompt_version("v1")

    with pytest.raises(dataclasses.FrozenInstanceError):
        version.__setattr__("output_language", "en-US")


def test_prompt_instructions_version_fields_are_exactly_the_fixed_shape() -> None:
    """recipe_metadata_fields R20: no servings field, recipe_metadata_instruction added."""
    field_names = {field.name for field in dataclasses.fields(PromptInstructionsVersion)}
    assert field_names == {
        "version_id",
        "output_language",
        "healthy_balanced_instruction",
        "recipe_metadata_instruction",
        "json_output_instruction",
        "output_language_template",
        "allowed_units_template",
        "category_framing_template",
        "specification_framing_template",
        "reference_framing_template",
    }


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


def test_build_specification_prompt_carries_the_recipe_metadata_instruction() -> None:
    """recipe_metadata_fields R25: reaches build_specification_prompt's result too."""
    result = build_specification_prompt(("tomate",), ("sarten",), "v1")

    assert result.instructions.recipe_metadata_instruction == RECIPE_METADATA_INSTRUCTION


def test_build_reference_prompt_carries_its_inputs() -> None:
    """R16, R17, R18 (specs/ai_prompt_builder/requirements.md, amended by feature 24)."""
    recipe = _make_recipe()
    extra_specifications = ("sin gluten",)

    result = build_reference_prompt(recipe, extra_specifications, "v1")

    assert result.instructions == build_instructions("v1")
    assert result.reference_recipe == recipe
    assert result.extra_specifications == extra_specifications


def test_build_reference_prompt_carries_the_recipe_metadata_instruction() -> None:
    """recipe_metadata_fields R25: reaches build_reference_prompt's result too."""
    result = build_reference_prompt(_make_recipe(), (), "v1")

    assert result.instructions.recipe_metadata_instruction == RECIPE_METADATA_INSTRUCTION


def test_build_category_prompt_carries_its_input() -> None:
    """R19, R20 (specs/ai_prompt_builder/requirements.md, amended by feature 24)."""
    category_counts = (
        CategoryCountRule(category=IngredientCategory.MEAT, count=2),
        CategoryCountRule(category=IngredientCategory.FISH, count=1),
    )

    result = build_category_prompt(category_counts, "v1")

    assert result.instructions == build_instructions("v1")
    assert result.category_counts == category_counts


def test_build_category_prompt_carries_the_recipe_metadata_instruction() -> None:
    """recipe_metadata_fields R25: reaches build_category_prompt's result too."""
    result = build_category_prompt(
        (CategoryCountRule(category=IngredientCategory.MEAT, count=1),), "v1"
    )

    assert result.instructions.recipe_metadata_instruction == RECIPE_METADATA_INSTRUCTION
