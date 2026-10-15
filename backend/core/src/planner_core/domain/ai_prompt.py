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

JSON_OUTPUT_INSTRUCTION: Final[str] = (
    "Responde EXCLUSIVAMENTE con un objeto JSON con las claves: name (str), "
    "ingredients (lista de {name, quantity, unit}), tools (lista de str), "
    "procedure (lista de str), category (str), servings (int|null), "
    "estimated_time (str|null). Sin texto adicional."
)
"""FR-AI-14 (G-84): the model-output contract line, versioned here so an edit
bumps the version key instead of silently changing every prompt. Consumed by
planner_ai's Bedrock adapter (specs/ai_lambda/design.md finding 6)."""

OUTPUT_LANGUAGE_TEMPLATE: Final[str] = "Idioma de salida: ${language}."
ALLOWED_UNITS_TEMPLATE: Final[str] = "Unidades permitidas: ${units}."
CATEGORY_FRAMING_TEMPLATE: Final[str] = (
    "Genera una receta para un hueco abierto. Necesidades de la semana: ${needs}."
)
SPECIFICATION_FRAMING_TEMPLATE: Final[str] = "Ingredientes: ${ingredients}.\nUtensilios: ${tools}."
REFERENCE_FRAMING_TEMPLATE: Final[str] = (
    "Receta de referencia: ${recipe}.\nEspecificaciones: ${specifications}."
)
"""FR-AI-14: the adapter's connective/framing wording, versioned (finding 6).
`string.Template` placeholders — the assembler interpolates, holds no Spanish."""

HEALTHY_BALANCED_INSTRUCTION_V2: Final[str] = (
    "Generate a healthy, balanced menu, varying the protein sources across "
    "dishes. This instruction is for household meal-planning purposes only "
    "and does not constitute medical advice."
)
RECIPE_METADATA_INSTRUCTION_V2: Final[str] = (
    "Also state the number of diners it serves and an estimated preparation "
    "and cooking time for each generated recipe. These are purely "
    "informational: do not adjust the ingredient quantities based on them."
)
JSON_OUTPUT_INSTRUCTION_V2: Final[str] = (
    "Respond EXCLUSIVELY with a JSON object with the keys: name (str), "
    "ingredients (list of {name, quantity, unit}), tools (list of str), "
    "procedure (list of str), category (str), servings (int|null), "
    "estimated_time (str|null). No additional text."
)
OUTPUT_LANGUAGE_TEMPLATE_V2: Final[str] = "Output language: ${language}."
ALLOWED_UNITS_TEMPLATE_V2: Final[str] = "Allowed units: ${units}."
CATEGORY_FRAMING_TEMPLATE_V2: Final[str] = (
    "Generate a recipe for an open slot. This week's remaining needs: ${needs}."
)
SPECIFICATION_FRAMING_TEMPLATE_V2: Final[str] = "Ingredients: ${ingredients}.\nTools: ${tools}."
REFERENCE_FRAMING_TEMPLATE_V2: Final[str] = (
    "Reference recipe: ${recipe}.\nSpecifications: ${specifications}."
)
"""v2 (2026-09-11 owner correction): English instruction wording — Bedrock
tokenizes English more efficiently. `OUTPUT_LANGUAGE` (es-ES) is untouched;
only the instruction sentences change (FR-AI-14/G-84 append-only)."""

RECIPE_METADATA_INSTRUCTION_V3: Final[str] = (
    "Also state the number of diners it serves and an estimated preparation "
    "and cooking time, in whole minutes, for each generated recipe. These are "
    "purely informational: do not adjust the ingredient quantities based on them."
)
JSON_OUTPUT_INSTRUCTION_V3: Final[str] = (
    "Respond EXCLUSIVELY with a JSON object with the keys: name (str), "
    "ingredients (list of {name, quantity, unit}), tools (list of str), "
    "procedure (list of str), category (str), servings (int|null); "
    "estimated_time (int|null, whole minutes from 0 to 6000 inclusive). No additional text."
)
"""v3 (issue tiempo-estimado-numeric-minutes, G-90): the prep/cook time field
becomes an integer minute count instead of free text. Everything else keeps
v2's wording verbatim (FR-AI-14/G-84 append-only) - only these two lines
change, worded so they do not repeat v2's verbatim (the metadata-scan test
matches line-for-line)."""
HEALTHY_BALANCED_INSTRUCTION_V4: Final[str] = (
    "Produce one healthy, balanced dish (a single recipe, not a menu), varying "
    "protein sources across the household's meals. Name the recipe after the "
    "dish itself. This instruction is for household meal-planning purposes only "
    "and does not constitute medical advice. If the ingredients, tools or "
    "specifications below are empty, generic, unrelated to cooking or "
    'unintelligible (for example "test"), ignore the unusable part and still '
    "produce one valid dish that follows these guidelines; honour any part "
    "that is usable."
)
"""v4 (issue generated-recipe-title-is-the-instruction): one dish, named after
itself, instead of "generate a menu"; every other v3 field is reused. Ends with
the unusable-input fallback (feature ai_fallback_recipe, edited in place)."""

AVOID_NAMES_TEMPLATE_V5: Final[str] = (
    "Dishes already planned for this household: ${names}. Do not repeat or "
    "closely imitate any of them; produce a clearly different dish."
)
"""v5 (issue ai-week-dishes-repeat, G-95): the names-to-avoid line. Kept in its
own registry so v1-v4 stay byte-identical (FR-AI-14)."""

CATEGORY_FRAMING_TEMPLATE_V6: Final[str] = "Generate a recipe for an open slot."
NEEDS_TEMPLATE_V6: Final[str] = "This week's remaining needs: ${needs}."
AVOID_NAMES_TEMPLATE_V6: Final[str] = (
    "Dishes already planned for this household: ${names}. Do not repeat or "
    "closely imitate any of them: do not reuse their names, their main "
    "ingredient or their style of preparation. Choose a dish from a different "
    "cuisine than those dishes, with a different main ingredient."
)
"""v6 (issue ai-week-dishes-still-similar, G-95): needs-free framing, the needs
sentence on its own (emitted only when needs exist), and a wider avoid line with a
positive cuisine steer. v1-v5 stay byte-identical (FR-AI-14)."""


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
    json_output_instruction: str
    output_language_template: str
    allowed_units_template: str
    category_framing_template: str
    specification_framing_template: str
    reference_framing_template: str


PROMPT_INSTRUCTION_VERSIONS: Final[dict[str, PromptInstructionsVersion]] = {
    "v1": PromptInstructionsVersion(
        version_id="v1",
        output_language=OUTPUT_LANGUAGE,
        healthy_balanced_instruction=HEALTHY_BALANCED_INSTRUCTION,
        recipe_metadata_instruction=RECIPE_METADATA_INSTRUCTION,
        json_output_instruction=JSON_OUTPUT_INSTRUCTION,
        output_language_template=OUTPUT_LANGUAGE_TEMPLATE,
        allowed_units_template=ALLOWED_UNITS_TEMPLATE,
        category_framing_template=CATEGORY_FRAMING_TEMPLATE,
        specification_framing_template=SPECIFICATION_FRAMING_TEMPLATE,
        reference_framing_template=REFERENCE_FRAMING_TEMPLATE,
    ),
    "v2": PromptInstructionsVersion(
        version_id="v2",
        output_language=OUTPUT_LANGUAGE,
        healthy_balanced_instruction=HEALTHY_BALANCED_INSTRUCTION_V2,
        recipe_metadata_instruction=RECIPE_METADATA_INSTRUCTION_V2,
        json_output_instruction=JSON_OUTPUT_INSTRUCTION_V2,
        output_language_template=OUTPUT_LANGUAGE_TEMPLATE_V2,
        allowed_units_template=ALLOWED_UNITS_TEMPLATE_V2,
        category_framing_template=CATEGORY_FRAMING_TEMPLATE_V2,
        specification_framing_template=SPECIFICATION_FRAMING_TEMPLATE_V2,
        reference_framing_template=REFERENCE_FRAMING_TEMPLATE_V2,
    ),
    "v3": PromptInstructionsVersion(
        version_id="v3",
        output_language=OUTPUT_LANGUAGE,
        healthy_balanced_instruction=HEALTHY_BALANCED_INSTRUCTION_V2,
        recipe_metadata_instruction=RECIPE_METADATA_INSTRUCTION_V3,
        json_output_instruction=JSON_OUTPUT_INSTRUCTION_V3,
        output_language_template=OUTPUT_LANGUAGE_TEMPLATE_V2,
        allowed_units_template=ALLOWED_UNITS_TEMPLATE_V2,
        category_framing_template=CATEGORY_FRAMING_TEMPLATE_V2,
        specification_framing_template=SPECIFICATION_FRAMING_TEMPLATE_V2,
        reference_framing_template=REFERENCE_FRAMING_TEMPLATE_V2,
    ),
    "v4": PromptInstructionsVersion(
        version_id="v4",
        output_language=OUTPUT_LANGUAGE,
        healthy_balanced_instruction=HEALTHY_BALANCED_INSTRUCTION_V4,
        recipe_metadata_instruction=RECIPE_METADATA_INSTRUCTION_V3,
        json_output_instruction=JSON_OUTPUT_INSTRUCTION_V3,
        output_language_template=OUTPUT_LANGUAGE_TEMPLATE_V2,
        allowed_units_template=ALLOWED_UNITS_TEMPLATE_V2,
        category_framing_template=CATEGORY_FRAMING_TEMPLATE_V2,
        specification_framing_template=SPECIFICATION_FRAMING_TEMPLATE_V2,
        reference_framing_template=REFERENCE_FRAMING_TEMPLATE_V2,
    ),
    "v5": PromptInstructionsVersion(
        version_id="v5",
        output_language=OUTPUT_LANGUAGE,
        healthy_balanced_instruction=HEALTHY_BALANCED_INSTRUCTION_V4,
        recipe_metadata_instruction=RECIPE_METADATA_INSTRUCTION_V3,
        json_output_instruction=JSON_OUTPUT_INSTRUCTION_V3,
        output_language_template=OUTPUT_LANGUAGE_TEMPLATE_V2,
        allowed_units_template=ALLOWED_UNITS_TEMPLATE_V2,
        category_framing_template=CATEGORY_FRAMING_TEMPLATE_V2,
        specification_framing_template=SPECIFICATION_FRAMING_TEMPLATE_V2,
        reference_framing_template=REFERENCE_FRAMING_TEMPLATE_V2,
    ),
    "v6": PromptInstructionsVersion(
        version_id="v6",
        output_language=OUTPUT_LANGUAGE,
        healthy_balanced_instruction=HEALTHY_BALANCED_INSTRUCTION_V4,
        recipe_metadata_instruction=RECIPE_METADATA_INSTRUCTION_V3,
        json_output_instruction=JSON_OUTPUT_INSTRUCTION_V3,
        output_language_template=OUTPUT_LANGUAGE_TEMPLATE_V2,
        allowed_units_template=ALLOWED_UNITS_TEMPLATE_V2,
        category_framing_template=CATEGORY_FRAMING_TEMPLATE_V6,
        specification_framing_template=SPECIFICATION_FRAMING_TEMPLATE_V2,
        reference_framing_template=REFERENCE_FRAMING_TEMPLATE_V2,
    ),
}
"""Append-only (R2, G-84): a version is added here when wording changes; an
existing key is never removed or overwritten (specs/ai_prompt_versioning/design.md
section 4). v2 (2026-09-11): English instruction wording, same es-ES
output_language. v3 (issue tiempo-estimado-numeric-minutes, G-90): reuses
every v2 field except the two prep/cook-time-bearing instructions. v4 (issue
generated-recipe-title-is-the-instruction): v3 with only the healthy-balanced line.
v5 (issue ai-week-dishes-repeat, G-95): v4 plus the names-to-avoid line.
v6 (issue ai-week-dishes-still-similar): v5 with the v6 framing and avoid wording."""

AVOID_NAMES_TEMPLATES: Final[dict[str, str]] = {
    "v5": AVOID_NAMES_TEMPLATE_V5,
    "v6": AVOID_NAMES_TEMPLATE_V6,
}
"""Versions that carry a names-to-avoid line; an absent key renders none."""

NEEDS_TEMPLATES: Final[dict[str, str]] = {"v6": NEEDS_TEMPLATE_V6}
"""Versions whose needs sentence is separate from the framing; absent = in the framing."""

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
    json_output_instruction: str
    output_language_template: str
    allowed_units_template: str
    category_framing_template: str
    specification_framing_template: str
    reference_framing_template: str
    avoid_names_template: str = ""
    needs_template: str = ""


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
    avoid_names: tuple[str, ...] = ()  # G-95: dishes the model must not repeat


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
        json_output_instruction=version.json_output_instruction,
        output_language_template=version.output_language_template,
        allowed_units_template=version.allowed_units_template,
        category_framing_template=version.category_framing_template,
        specification_framing_template=version.specification_framing_template,
        reference_framing_template=version.reference_framing_template,
        avoid_names_template=AVOID_NAMES_TEMPLATES.get(version.version_id, ""),
        needs_template=NEEDS_TEMPLATES.get(version.version_id, ""),
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
    category_counts: tuple[CategoryCountRule, ...],
    version_id: str,
    avoid_names: tuple[str, ...] = (),
) -> CategoryPrompt:
    """FR-AI-04 (R19-R20). category_counts is the caller's snapshot (design.md section 1) —
    typically generation_request's GenerationTargets.remaining_category_counts, passed
    unchanged for one open slot; this function neither reads nor recomputes it."""
    return CategoryPrompt(
        instructions=build_instructions(version_id),
        category_counts=category_counts,
        avoid_names=avoid_names,
    )
