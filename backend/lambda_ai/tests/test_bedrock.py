"""BedrockAiProvider: prompt rendering, response parsing and the AI_MODEL_ID
override (specs/ai_lambda/design.md section 4, section 10). No live call."""

from __future__ import annotations

from typing import Any

import pytest
from botocore.exceptions import ClientError
from planner_core.domain.ai_prompt import ALLOWED_UNITS, build_category_prompt, build_instructions
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.rules import CategoryCountRule
from planner_core.ports.ai_provider import AiProviderError

from planner_ai.adapters.bedrock import BEDROCK_MODEL_ID, BedrockAiProvider, _render
from planner_ai.adapters.inference_config import DEFAULT_MAX_TOKENS

PROMPT = build_category_prompt((), "v1")


def test_render_carries_the_versioned_instructions_and_the_category_counts() -> None:
    """T15/R2 — _render is a pure assembler; the rendered body must carry the
    active version's wording and the slot's category needs (finding 5/6)."""
    version = build_instructions("v1")
    prompt = build_category_prompt(
        (CategoryCountRule(category=IngredientCategory.VEGETABLE, count=3),), "v1"
    )

    rendered = _render(prompt)

    assert version.healthy_balanced_instruction in rendered
    assert version.recipe_metadata_instruction in rendered
    assert version.output_language in rendered
    assert version.json_output_instruction in rendered
    for unit in ALLOWED_UNITS:
        assert unit.value in rendered
    assert "3x vegetable" in rendered


def test_render_is_version_agnostic_and_renders_v2_english_wording() -> None:
    """2026-09-11 owner correction: v2's English instructions render too, proving
    the assembler sources wording from the given version_id, not hardcoded to v1."""
    version = build_instructions("v2")
    prompt = build_category_prompt(
        (CategoryCountRule(category=IngredientCategory.VEGETABLE, count=3),), "v2"
    )

    rendered = _render(prompt)

    assert version.healthy_balanced_instruction in rendered
    assert version.recipe_metadata_instruction in rendered
    assert version.output_language in rendered
    assert version.json_output_instruction in rendered
    for unit in ALLOWED_UNITS:
        assert unit.value in rendered
    assert "3x vegetable" in rendered


def _tool_use(recipe: Any) -> dict[str, Any]:
    return {"toolUse": {"toolUseId": "t-1", "name": "submit_recipe", "input": recipe}}


class _Client:
    """Stands in for the Converse response shape: output.message.content, here a
    forced tool's toolUse block (issue single-recipe-unknown-ingredient-category)."""

    def __init__(self, recipe: Any) -> None:
        self.recipe = recipe
        self.model_id: str | None = None
        self.messages: Any = None
        self.inference_config: Any = None

    def converse(self, **kwargs: Any) -> dict[str, Any]:
        self.model_id = kwargs["modelId"]
        self.messages = kwargs["messages"]
        self.inference_config = kwargs["inferenceConfig"]
        return {"output": {"message": {"content": [_tool_use(self.recipe)]}}}


class _FailingClient:
    def converse(self, **kwargs: Any) -> dict[str, Any]:
        raise ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "too many requests"}}, "Converse"
        )


_MINIMAL = {"name": "X", "ingredients": [], "procedure": [], "category": "eggs"}


def test_it_uses_the_module_model_id_by_default() -> None:
    client = _Client(_MINIMAL)

    BedrockAiProvider(client=client).generate(PROMPT)

    assert client.model_id == BEDROCK_MODEL_ID == "eu.amazon.nova-2-lite-v1:0"
    assert client.messages[0]["role"] == "user"
    assert isinstance(client.messages[0]["content"], list)
    assert client.messages[0]["content"][0]["text"] == _render(PROMPT)
    assert client.inference_config == {"maxTokens": DEFAULT_MAX_TOKENS}


def test_the_ai_model_id_env_var_overrides_the_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_MODEL_ID", "eu.openai.gpt-5.6-terra")
    client = _Client(_MINIMAL)

    BedrockAiProvider(client=client).generate(PROMPT)

    assert client.model_id == "eu.openai.gpt-5.6-terra"


def test_a_response_with_no_tool_use_block_raises() -> None:
    class _TextOnly:
        def converse(self, **kwargs: Any) -> dict[str, Any]:
            return {"output": {"message": {"content": [{"text": "no puedo ayudarte con eso"}]}}}

    with pytest.raises(AiProviderError):
        BedrockAiProvider(client=_TextOnly()).generate(PROMPT)


def test_a_tool_input_missing_a_required_key_raises() -> None:
    client = _Client({"name": "X", "procedure": []})  # no ingredients / category
    with pytest.raises(AiProviderError):
        BedrockAiProvider(client=client).generate(PROMPT)


def test_a_converse_client_error_raises_ai_provider_error() -> None:
    # ThrottlingException etc. are ClientError subclasses on bedrock-runtime's
    # own .exceptions, per the boto3 Converse docs - same catch as before.
    with pytest.raises(AiProviderError):
        BedrockAiProvider(client=_FailingClient()).generate(PROMPT)


class _MultiBlockClient:
    """A reasoningContent block precedes the toolUse block (reasoning on);
    _tool_input must take the first toolUse, never content[0]."""

    def converse(self, **kwargs: Any) -> dict[str, Any]:
        content = [{"reasoningContent": {"text": "thinking..."}}, _tool_use(_MINIMAL)]
        return {"output": {"message": {"content": content}}}


def test_a_leading_reasoning_block_is_skipped_and_the_tool_use_parses() -> None:
    output = BedrockAiProvider(client=_MultiBlockClient()).generate(PROMPT)

    assert output.name == "X"
