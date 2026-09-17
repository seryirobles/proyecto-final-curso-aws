"""Contract suite for AiProvider: the in-memory fake and the Bedrock adapter
(with a stubbed client) agree — a well-formed response parses to RawRecipeOutput,
a malformed one raises AiProviderError (FR-AI-09; specs/ai_lambda/design.md section 4)."""

from __future__ import annotations

import json
from typing import Any

import pytest
from planner_ai.adapters.bedrock import _MAX_TOKENS, BedrockAiProvider, _render
from planner_core.domain.ai_output import RawIngredient, RawRecipeOutput
from planner_core.domain.ai_prompt import build_category_prompt
from planner_core.ports.ai_provider import AiPrompt, AiProvider, AiProviderError
from support.fakes import FakeAiProvider

PROMPT: AiPrompt = build_category_prompt((), "v1")

_RECIPE_JSON = json.dumps(
    {
        "name": "Arroz con verduras",
        "ingredients": [{"name": "arroz", "quantity": 200, "unit": "g"}],
        "tools": ["olla"],
        "procedure": ["Cocer el arroz.", "Añadir las verduras."],
        "category": "carbohydrate",
        "servings": 2,
        "estimated_time": "30 min",
    }
)

_EXPECTED = RawRecipeOutput(
    name="Arroz con verduras",
    ingredients=(RawIngredient(name="arroz", quantity=200.0, unit="g"),),
    tools=("olla",),
    procedure=("Cocer el arroz.", "Añadir las verduras."),
    category="carbohydrate",
    servings=2,
    estimated_time="30 min",
)


class _StubBedrock:
    """Stubs the Converse response shape (output.message.content)."""

    def __init__(self, text: str) -> None:
        self._text = text
        self.messages: Any = None
        self.inference_config: Any = None

    def converse(self, *, modelId: str, messages: Any, inferenceConfig: Any) -> dict[str, Any]:
        self.messages = messages
        self.inference_config = inferenceConfig
        return {"output": {"message": {"content": [{"text": self._text}]}}}


def _working() -> list[AiProvider]:
    return [
        FakeAiProvider(default_output=_EXPECTED),
        BedrockAiProvider(client=_StubBedrock(f"Aquí tienes: {_RECIPE_JSON}")),
    ]


def _failing() -> list[AiProvider]:
    return [
        FakeAiProvider(responses=[AiProviderError("boom")]),
        BedrockAiProvider(client=_StubBedrock("lo siento, no puedo generar eso")),
    ]


@pytest.mark.parametrize("provider", _working())
def test_a_well_formed_response_parses_to_raw_recipe_output(provider: AiProvider) -> None:
    assert provider.generate(PROMPT) == _EXPECTED


@pytest.mark.parametrize("provider", _failing())
def test_a_malformed_response_raises_ai_provider_error(provider: AiProvider) -> None:
    with pytest.raises(AiProviderError):
        provider.generate(PROMPT)


def test_the_converse_envelope_role_and_content_shape() -> None:
    stub = _StubBedrock(f"Aquí tienes: {_RECIPE_JSON}")

    BedrockAiProvider(client=stub).generate(PROMPT)

    assert stub.messages[0]["role"] == "user"
    assert isinstance(stub.messages[0]["content"], list)
    assert stub.messages[0]["content"][0]["text"] == _render(PROMPT)
    assert stub.inference_config == {"maxTokens": _MAX_TOKENS}
