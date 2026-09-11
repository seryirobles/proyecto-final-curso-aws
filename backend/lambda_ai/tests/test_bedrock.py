"""BedrockAiProvider: prompt rendering, response parsing and the AI_MODEL_ID
override (specs/ai_lambda/design.md section 4, section 10). No live call."""

from __future__ import annotations

import json
from typing import Any

import pytest
from planner_core.domain.ai_prompt import ALLOWED_UNITS, build_category_prompt, build_instructions
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.rules import CategoryCountRule
from planner_core.ports.ai_provider import AiProviderError

from planner_ai.adapters.bedrock import BEDROCK_MODEL_ID, BedrockAiProvider, _render

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


class _Body:
    def __init__(self, text: str) -> None:
        self._text = text

    def read(self) -> bytes:
        return json.dumps({"content": [{"type": "text", "text": self._text}]}).encode()


class _Client:
    def __init__(self, text: str) -> None:
        self.text = text
        self.model_id: str | None = None

    def invoke_model(self, *, modelId: str, body: str) -> dict[str, Any]:
        self.model_id = modelId
        return {"body": _Body(self.text)}


def test_it_uses_the_module_model_id_by_default() -> None:
    client = _Client(
        json.dumps({"name": "X", "ingredients": [], "procedure": [], "category": "eggs"})
    )

    BedrockAiProvider(client=client).generate(PROMPT)

    assert client.model_id == BEDROCK_MODEL_ID == "anthropic.claude-sonnet-5"


def test_the_ai_model_id_env_var_overrides_the_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_MODEL_ID", "anthropic.claude-haiku-4-5")
    client = _Client(
        json.dumps({"name": "X", "ingredients": [], "procedure": [], "category": "eggs"})
    )

    BedrockAiProvider(client=client).generate(PROMPT)

    assert client.model_id == "anthropic.claude-haiku-4-5"


def test_a_response_with_no_json_block_raises() -> None:
    with pytest.raises(AiProviderError):
        BedrockAiProvider(client=_Client("no puedo ayudarte con eso")).generate(PROMPT)


def test_a_json_block_missing_a_required_key_raises() -> None:
    client = _Client(json.dumps({"name": "X", "procedure": []}))  # no ingredients / category
    with pytest.raises(AiProviderError):
        BedrockAiProvider(client=client).generate(PROMPT)
