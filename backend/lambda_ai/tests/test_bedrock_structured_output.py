"""The Bedrock adapter constrains the model's recipe to a JSON schema through a
forced tool (Nova 2 Lite has no outputConfig support), with category and unit
as enums of the domain vocabularies (FR-LIB-03, FR-LIB-05, G-69, G-48)
(issues/single-recipe-unknown-ingredient-category)."""

from __future__ import annotations

import json
from typing import Any

import pytest
from botocore.exceptions import ClientError
from planner_core.domain.ai_output import (
    GenerationFailure,
    GenerationFailureReason,
    validate_and_preview,
)
from planner_core.domain.ai_prompt import (
    build_category_prompt,
    build_reference_prompt,
    build_specification_prompt,
)
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import MAX_ESTIMATED_MINUTES, Ingredient, Recipe
from planner_core.domain.rules import CategoryCountRule
from planner_core.domain.units import Unit, parse_unit
from planner_core.ports.ai_provider import AiPrompt, AiProviderError

from planner_ai.adapters.bedrock import BedrockAiProvider

# The schema does not depend on the prompt version; v3 is a fixed render target.
ACTIVE = "v3"

_REFERENCE = Recipe(
    name="Tortilla de patatas",
    ingredients=(Ingredient(name="patata", quantity=500, unit=parse_unit("g")),),
    tools=("sarten",),
    procedure=("Freir la patata.", "Cuajar con el huevo."),
    category=IngredientCategory.CARBOHYDRATE,
)
_PROMPTS: dict[str, AiPrompt] = {
    "specification": build_specification_prompt(("pollo", "arroz"), ("sarten",), ACTIVE),
    "reference": build_reference_prompt(_REFERENCE, ("sin gluten",), ACTIVE),
    "week_slot": build_category_prompt(
        (CategoryCountRule(category=IngredientCategory.FISH, count=2),), ACTIVE
    ),
}
_RECIPE: dict[str, Any] = {
    "name": "Lentejas estofadas",
    "ingredients": [{"name": "lentejas", "quantity": 300, "unit": "g"}],
    "tools": ["olla"],
    "procedure": ["Cocer las lentejas."],
    "category": "legume",
    "servings": 4,
    "estimated_time": 45,
}


class _Client:
    """Records the Converse kwargs; answers with the forced tool's input."""

    def __init__(self, recipe: dict[str, Any] | None = None, content: Any = None) -> None:
        self._recipe = recipe
        self._content = content
        self.kwargs: dict[str, Any] = {}

    def converse(self, **kwargs: Any) -> dict[str, Any]:
        self.kwargs = kwargs
        if self._content is not None:
            return {"output": {"message": {"content": self._content}}, "stopReason": "end_turn"}
        name = kwargs["toolConfig"]["toolChoice"]["tool"]["name"]
        block = {"toolUse": {"toolUseId": "t-1", "name": name, "input": self._recipe}}
        return {"output": {"message": {"content": [block]}}, "stopReason": "tool_use"}


def _schema(kwargs: dict[str, Any]) -> dict[str, Any]:
    config = kwargs["toolConfig"]
    (tool,) = config["tools"]
    assert config["toolChoice"] == {"tool": {"name": tool["toolSpec"]["name"]}}
    schema: dict[str, Any] = tool["toolSpec"]["inputSchema"]["json"]
    return schema


def _resolve(schema: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    """Follows one local `$ref` (#/$defs/x), if the schema uses one."""
    ref = node.get("$ref")
    if ref is None:
        return node
    *_, section, name = ref.split("/")
    resolved: dict[str, Any] = schema[section][name]
    return resolved


def _sent_schema(prompt: AiPrompt) -> dict[str, Any]:
    client = _Client(_RECIPE)
    BedrockAiProvider(client=client).generate(prompt)
    return _schema(client.kwargs)


@pytest.mark.parametrize("mode", ["specification", "reference"])
def test_single_recipe_call_constrains_category_to_the_fixed_set(mode: str) -> None:
    """Reproduction: no constraint let the model answer category 'menú'."""
    schema = _sent_schema(_PROMPTS[mode])

    category = _resolve(schema, schema["properties"]["category"])
    assert set(category["enum"]) == {c.value for c in IngredientCategory}


def test_week_slot_call_constrains_category_to_the_fixed_set() -> None:
    """Blast radius: week slots share the adapter (FR-AI-03, FR-AI-04)."""
    schema = _sent_schema(_PROMPTS["week_slot"])

    category = _resolve(schema, schema["properties"]["category"])
    assert set(category["enum"]) == {c.value for c in IngredientCategory}


@pytest.mark.parametrize("mode", ["specification", "reference", "week_slot"])
def test_every_call_constrains_ingredient_units_to_the_fixed_list(mode: str) -> None:
    schema = _sent_schema(_PROMPTS[mode])

    ingredients = _resolve(schema, schema["properties"]["ingredients"])
    item = _resolve(schema, ingredients["items"])
    assert set(_resolve(schema, item["properties"]["unit"])["enum"]) == {u.value for u in Unit}


def test_the_schema_is_closed_and_requires_the_recipe_sections() -> None:
    """Every key the domain reads is required; nothing else is allowed (G-89)."""
    schema = _sent_schema(_PROMPTS["specification"])
    item = _resolve(schema, _resolve(schema, schema["properties"]["ingredients"])["items"])

    assert schema["additionalProperties"] is False
    assert {"name", "ingredients", "tools", "procedure", "category"} <= set(schema["required"])
    assert item["additionalProperties"] is False
    assert {"name", "quantity", "unit"} <= set(item["required"])
    for section in ("ingredients", "tools", "procedure"):
        assert _resolve(schema, schema["properties"][section])["minItems"] == 1


def test_the_recipe_is_read_from_the_tool_input() -> None:
    raw = BedrockAiProvider(client=_Client(_RECIPE)).generate(_PROMPTS["specification"])

    assert raw.name == "Lentejas estofadas"
    assert raw.category == "legume"
    assert raw.ingredients[0].unit == "g"
    assert (raw.servings, raw.estimated_time) == (4, 45)


def test_an_out_of_set_category_still_reaches_the_domain_backstop() -> None:
    """The adapter neither repairs nor drops it; G-48 validation decides."""
    off_schema = {**_RECIPE, "category": "menú"}

    raw = BedrockAiProvider(client=_Client(off_schema)).generate(_PROMPTS["specification"])
    outcome = validate_and_preview(raw)

    assert raw.category == "menú"
    assert isinstance(outcome, GenerationFailure)
    assert outcome.reason is GenerationFailureReason.INVALID_OUTPUT


def test_a_plain_text_reply_fails_loudly_instead_of_being_parsed() -> None:
    """No silent fallback to the old `{...}` text hunt; E4 diagnostics kept."""
    text = json.dumps({**_RECIPE, "name": "Menú equilibrado"}, ensure_ascii=False)
    client = _Client(content=[{"text": text}])

    with pytest.raises(AiProviderError) as raised:
        BedrockAiProvider(client=client).generate(_PROMPTS["specification"])

    assert "end_turn" in str(raised.value)
    assert "Menú equilibrado" in str(raised.value)


class _RejectingClient:
    def converse(self, **kwargs: Any) -> dict[str, Any]:
        raise ClientError(
            {"Error": {"Code": "ValidationException", "Message": "tool use unsupported"}},
            "Converse",
        )


def test_a_model_that_rejects_the_request_fails_loudly() -> None:
    """Guard: an unsupported model surfaces as a provider error (logged, issue 13)."""
    with pytest.raises(AiProviderError):
        BedrockAiProvider(client=_RejectingClient()).generate(_PROMPTS["specification"])


def _all_properties(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Top-level and ingredient-item properties, keyed `name` / `ingredients.name`."""
    item = _resolve(schema, _resolve(schema, schema["properties"]["ingredients"])["items"])
    found = {k: _resolve(schema, v) for k, v in schema["properties"].items()}
    found.update({f"ingredients.{k}": _resolve(schema, v) for k, v in item["properties"].items()})
    return found


def test_every_property_carries_a_description() -> None:
    """Nova's documented pattern: the schema, not the prompt, explains each field."""
    properties = _all_properties(_sent_schema(_PROMPTS["specification"]))

    missing = [k for k, v in properties.items() if not str(v.get("description", "")).strip()]
    assert missing == []


def test_the_category_description_states_the_predominant_ingredient_rule() -> None:
    """FR-LIB-03 / G-69: the one category that predominates in the dish."""
    schema = _sent_schema(_PROMPTS["specification"])

    description = _resolve(schema, schema["properties"]["category"])["description"]
    assert "predominat" in description.lower()


def test_estimated_time_is_bounded_by_the_domain_maximum() -> None:
    """Only bounds with a domain constant are sent (G-90: MAX_ESTIMATED_MINUTES)."""
    schema = _sent_schema(_PROMPTS["specification"])

    assert _resolve(schema, schema["properties"]["estimated_time"])["maximum"] == (
        MAX_ESTIMATED_MINUTES
    )


def test_procedure_is_the_last_property_and_nesting_stays_within_two_layers() -> None:
    """Nova best practice: long string arguments last; at most two nesting layers."""
    schema = _sent_schema(_PROMPTS["specification"])
    item = _resolve(schema, _resolve(schema, schema["properties"]["ingredients"])["items"])

    assert list(schema["properties"])[-1] == "procedure"
    assert all(
        _resolve(schema, v).get("type") not in ("object", "array")
        for v in item["properties"].values()
    )
