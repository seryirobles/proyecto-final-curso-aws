"""Bedrock inference settings from the environment (specs/ai_inference_config R1-R20,
R23). A recording fake client stands in for Converse; no live call."""

from __future__ import annotations

import json
import logging
from typing import Any

import pytest
from planner_core.domain.ai_prompt import build_category_prompt
from planner_core.ports.ai_provider import AiProviderError
from planner_core.ports.generation_queue import StoredGeneration
from support.fakes import (
    FakeClock,
    FakeGenerationGate,
    FakeGenerationQueue,
    FakeRecipeRepository,
    FakeWeekRepository,
)

from planner_ai.adapters.bedrock import BedrockAiProvider
from planner_ai.adapters.inference_config import (
    InferenceConfigError,
    InferenceSettings,
    converse_kwargs,
    load_inference_settings,
)
from planner_ai.handler import handle
from planner_ai.wiring import Dependencies

PROMPT = build_category_prompt((), "v1")
SENTINEL = "SENTINEL-BEARER-TOKEN-123"
_VARS = (
    "AI_MODEL_ID",
    "AI_REASONING_ENABLED",
    "AI_REASONING_EFFORT",
    "AI_MAX_TOKENS",
    "AI_TEMPERATURE",
    "AI_TOP_P",
    "AI_SERVICE_TIER",
)
_RECIPE = {"name": "X", "ingredients": [], "procedure": [], "category": "eggs"}


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", SENTINEL)


class _Client:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def converse(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        block = {"toolUse": {"toolUseId": "t", "name": "submit_recipe", "input": _RECIPE}}
        return {"output": {"message": {"content": [block]}}}


def _call(monkeypatch: pytest.MonkeyPatch, **env: str) -> dict[str, Any]:
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    client = _Client()
    BedrockAiProvider(client=client).generate(PROMPT)
    return client.calls[0]


def test_unset_env_sends_exactly_model_messages_config_and_the_fixed_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R2, R14."""
    call = _call(monkeypatch)

    assert set(call) == {"modelId", "messages", "inferenceConfig", "toolConfig"}
    assert call["inferenceConfig"] == {"maxTokens": 4096}
    assert call["modelId"] == "eu.amazon.nova-2-lite-v1:0"  # R3


def test_each_variable_maps_to_its_converse_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """R3-R7, R9."""
    call = _call(
        monkeypatch,
        AI_MODEL_ID="eu.other:0",
        AI_MAX_TOKENS="65000",
        AI_TEMPERATURE="0",
        AI_TOP_P="1",
        AI_SERVICE_TIER="priority",
        AI_REASONING_ENABLED="true",
        AI_REASONING_EFFORT="medium",
    )

    assert call["modelId"] == "eu.other:0"
    assert call["inferenceConfig"] == {"maxTokens": 65000, "temperature": 0.0, "topP": 1.0}
    assert call["serviceTier"] == {"type": "priority"}
    assert call["additionalModelRequestFields"] == {
        "reasoningConfig": {"type": "enabled", "maxReasoningEffort": "medium"}
    }


def test_flex_is_sent_and_standard_is_omitted(monkeypatch: pytest.MonkeyPatch) -> None:
    """R7, R8."""
    assert _call(monkeypatch, AI_SERVICE_TIER="flex")["serviceTier"] == {"type": "flex"}
    assert "serviceTier" not in _call(monkeypatch, AI_SERVICE_TIER="standard")


def test_reasoning_defaults_to_low_effort_and_off_omits_the_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R10, R11."""
    on = _call(monkeypatch, AI_REASONING_ENABLED="true")
    assert on["additionalModelRequestFields"]["reasoningConfig"]["maxReasoningEffort"] == "low"
    off = _call(monkeypatch, AI_REASONING_ENABLED="false", AI_REASONING_EFFORT="high")
    assert "additionalModelRequestFields" not in off


def test_effort_high_with_temperature_or_top_p_raises_before_the_client(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """R12, R13."""
    monkeypatch.setenv("AI_REASONING_ENABLED", "true")
    monkeypatch.setenv("AI_REASONING_EFFORT", "high")
    monkeypatch.setenv("AI_TEMPERATURE", "0.5")
    monkeypatch.setenv("AI_TOP_P", "0.5")
    client = _Client()

    with caplog.at_level(logging.ERROR), pytest.raises(InferenceConfigError):
        BedrockAiProvider(client=client).generate(PROMPT)

    assert client.calls == []
    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(errors) == 1
    assert "AI_TEMPERATURE" in errors[0].message and "AI_TOP_P" in errors[0].message


def test_reasoning_off_with_effort_high_keeps_temperature(monkeypatch: pytest.MonkeyPatch) -> None:
    """R5, R11, R12 (rule only fires while reasoning is on)."""
    call = _call(monkeypatch, AI_REASONING_EFFORT="high", AI_TEMPERATURE="0.3", AI_TOP_P="0.2")

    assert call["inferenceConfig"]["temperature"] == 0.3
    assert call["inferenceConfig"]["topP"] == 0.2


def test_effort_high_omits_max_tokens_even_when_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """R23."""
    high = {"AI_REASONING_ENABLED": "true", "AI_REASONING_EFFORT": "high"}
    assert _call(monkeypatch, **high)["inferenceConfig"] == {}
    assert _call(monkeypatch, AI_MAX_TOKENS="9000", **high)["inferenceConfig"] == {}
    low = _call(monkeypatch, AI_REASONING_ENABLED="true", AI_REASONING_EFFORT="low")
    assert low["inferenceConfig"] == {"maxTokens": 9000}


@pytest.mark.parametrize(
    "settings",
    [
        InferenceSettings(),
        InferenceSettings(temperature=0.5, top_p=0.5, service_tier="flex", reasoning=True),
        InferenceSettings(reasoning=True, effort="high"),
    ],
)
def test_converse_kwargs_never_carry_the_fixed_fields(settings: InferenceSettings) -> None:
    """R14."""
    blob = json.dumps(converse_kwargs(settings))

    for forbidden in ("topK", "stopSequences", "guardrail", "cachePoint"):
        assert forbidden not in blob


@pytest.mark.parametrize(
    ("variable", "value"),
    [
        ("AI_MAX_TOKENS", "0"),
        ("AI_MAX_TOKENS", "65001"),
        ("AI_MAX_TOKENS", "abc"),
        ("AI_MAX_TOKENS", "12.5"),
        ("AI_MAX_TOKENS", "-5"),
        ("AI_TEMPERATURE", "1.5"),
        ("AI_TEMPERATURE", "-0.1"),
        ("AI_TEMPERATURE", "hot"),
        ("AI_TEMPERATURE", "nan"),
        ("AI_TOP_P", "2"),
        ("AI_TOP_P", "inf"),
        ("AI_TOP_P", "x"),
        ("AI_SERVICE_TIER", "prioirty"),
        ("AI_SERVICE_TIER", "Priority"),
        ("AI_REASONING_ENABLED", "yes"),
        ("AI_REASONING_ENABLED", "True"),
        ("AI_REASONING_EFFORT", "extreme"),
    ],
)
def test_an_invalid_value_raises_before_the_client_and_names_the_variable(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    variable: str,
    value: str,
) -> None:
    """R15, R16, R17."""
    monkeypatch.setenv(variable, value)
    client = _Client()

    with caplog.at_level(logging.ERROR), pytest.raises(AiProviderError) as raised:
        BedrockAiProvider(client=client).generate(PROMPT)

    assert client.calls == []
    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(errors) == 1 and variable in errors[0].message
    assert "Bedrock invocation failed" not in str(raised.value)
    assert SENTINEL not in caplog.text and SENTINEL not in str(raised.value)


@pytest.mark.parametrize("variable", _VARS[1:])
@pytest.mark.parametrize("blank", ["", "   "])
def test_a_blank_value_is_treated_as_unset(
    monkeypatch: pytest.MonkeyPatch, variable: str, blank: str
) -> None:
    """R18."""
    monkeypatch.setenv(variable, blank)

    assert load_inference_settings({variable: blank}) == InferenceSettings()
    assert _call(monkeypatch)["inferenceConfig"] == {"maxTokens": 4096}


def test_whitespace_around_a_valid_value_is_stripped() -> None:
    """R18 (design: whitespace stripped)."""
    assert load_inference_settings({"AI_MAX_TOKENS": " 100 "}).max_tokens == 100


def test_a_reasoning_block_before_the_tool_use_parses(monkeypatch: pytest.MonkeyPatch) -> None:
    """R19 (superseded by issue 15: the recipe comes from the first toolUse block)."""

    class _Reasoning:
        def converse(self, **kwargs: Any) -> dict[str, Any]:
            tool = {"toolUse": {"toolUseId": "t", "name": "submit_recipe", "input": _RECIPE}}
            return {"output": {"message": {"content": [{"reasoningContent": {}}, tool]}}}

    monkeypatch.setenv("AI_REASONING_ENABLED", "true")

    assert BedrockAiProvider(client=_Reasoning()).generate(PROMPT).name == "X"


def test_settings_are_read_on_every_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """R1."""
    client = _Client()
    provider = BedrockAiProvider(client=client)
    provider.generate(PROMPT)
    monkeypatch.setenv("AI_MAX_TOKENS", "100")
    provider.generate(PROMPT)

    assert [c["inferenceConfig"]["maxTokens"] for c in client.calls] == [4096, 100]


def _deps(queue: FakeGenerationQueue, client: _Client) -> Dependencies:
    return Dependencies(
        provider=BedrockAiProvider(client=client),
        weeks=FakeWeekRepository(),
        recipes=FakeRecipeRepository(),
        records=queue,
        gate=FakeGenerationGate(),
        clock=FakeClock.at("2026-08-17T10:00:00+00:00"),
    )


def test_single_recipe_and_week_jobs_send_identical_inference_kwargs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R20, R1."""
    monkeypatch.setenv("AI_MAX_TOKENS", "2000")
    monkeypatch.setenv("AI_TEMPERATURE", "0.4")
    monkeypatch.setenv("AI_SERVICE_TIER", "flex")
    queue = FakeGenerationQueue()
    for key in ("r1", "w1"):
        queue.stored[key] = StoredGeneration(idempotency_key=key, status="pending")
    recipe = {
        "type": "recipe",
        "idPeticionIA": "r1",
        "target": {"kind": "library"},
        "source": {"kind": "specification", "ingredients": ["lentejas"], "tools": ["olla"]},
        "referenceRecipe": None,
        "promptVersionId": "v1",
        "authorUserId": "u-1",
    }
    week = {
        "idPeticionIA": "w1",
        "weekId": "2026-W34",
        "mode": "mix",
        "promptVersionId": "v1",
        "authorUserId": "u-1",
        "effectiveRules": {},
    }
    seen: list[list[dict[str, Any]]] = []
    for body in (recipe, week):
        client = _Client()
        handle({"Records": [{"body": json.dumps(body)}]}, _deps(queue, client))
        seen.append(client.calls)

    keys = ("inferenceConfig", "serviceTier", "modelId")
    assert seen[0] and seen[1]
    assert {tuple(json.dumps(c[k]) for k in keys) for calls in seen for c in calls} == {
        (
            json.dumps({"maxTokens": 2000, "temperature": 0.4}),
            json.dumps({"type": "flex"}),
            json.dumps("eu.amazon.nova-2-lite-v1:0"),
        )
    }
