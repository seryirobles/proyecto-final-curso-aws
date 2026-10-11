"""`AiProvider` backed by AWS Bedrock + OpenAI GPT-5.6 Terra (docs/architecture.md
section 1.2.6). Renders the prompt value object to a plain text instruction,
calls `bedrock-runtime:Converse` (this model has no InvokeModel support), and
reads the recipe from a forced tool call's input into a `RawRecipeOutput`. A parse
or call failure raises `AiProviderError` (specs/ai_lambda/design.md section 4)."""

from __future__ import annotations

import json
import os
from string import Template
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from planner_core.domain.ai_output import RawIngredient, RawRecipeOutput, recipe_output_schema
from planner_core.domain.ai_prompt import CategoryPrompt, ReferencePrompt, SpecificationPrompt
from planner_core.ports.ai_provider import AiPrompt, AiProviderError

BEDROCK_MODEL_ID = "global.openai.gpt-5.6-terra"
"""The Global cross-Region inference profile id (architecture.md section
1.2.6) - eu-south-2 supports no In-Region/Geo profile for this model.
Overridable by AI_MODEL_ID (design.md section 10)."""

_MAX_TOKENS = 4096
_REGION = os.environ.get("AWS_DEFAULT_REGION", "eu-south-2")


def _model_id() -> str:
    return os.environ.get("AI_MODEL_ID", BEDROCK_MODEL_ID)


def _render(prompt: AiPrompt) -> str:
    # Pure assembler: every instruction string lives in the versioned prompt
    # registry (domain/ai_prompt.py), so editing wording bumps a version key (finding 6).
    ins = prompt.instructions
    lines = [
        ins.healthy_balanced_instruction,
        ins.recipe_metadata_instruction,
        Template(ins.output_language_template).substitute(language=ins.output_language),
        Template(ins.allowed_units_template).substitute(
            units=", ".join(unit.value for unit in ins.allowed_units)
        ),
    ]
    if isinstance(prompt, CategoryPrompt):
        needs = ", ".join(f"{r.count}x {r.category.value}" for r in prompt.category_counts)
        lines.append(Template(ins.category_framing_template).substitute(needs=needs))
    elif isinstance(prompt, SpecificationPrompt):
        lines.append(
            Template(ins.specification_framing_template).substitute(
                ingredients=", ".join(prompt.ingredients), tools=", ".join(prompt.tools)
            )
        )
    elif isinstance(prompt, ReferencePrompt):
        lines.append(
            Template(ins.reference_framing_template).substitute(
                recipe=prompt.reference_recipe.name,
                specifications=", ".join(prompt.extra_specifications),
            )
        )
    lines.append(ins.json_output_instruction)
    return "\n".join(lines)


_SNIPPET_LIMIT = 500
_TOOL_NAME = "submit_recipe"
# Forced tool = structured output; Nova 2 Lite has no outputConfig (issue 15).
_TOOL_CONFIG: dict[str, Any] = {
    "tools": [
        {
            "toolSpec": {
                "name": _TOOL_NAME,
                "description": "Submit the generated recipe.",
                "inputSchema": {"json": recipe_output_schema()},
            }
        }
    ],
    "toolChoice": {"tool": {"name": _TOOL_NAME}},
}


def _stop(response: dict[str, Any]) -> object:
    return response.get("stopReason")


def _text_snippet(response: dict[str, Any]) -> str:
    for block in _content(response):
        if isinstance(block.get("text"), str):
            return str(block["text"])[:_SNIPPET_LIMIT]
    return ""


def _content(response: dict[str, Any]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = response.get("output", {}).get("message", {}).get("content", [])
    return blocks


def _tool_input(response: dict[str, Any]) -> dict[str, Any]:
    # First toolUse block, never content[0]: with reasoning on a reasoningContent
    # block comes first. No toolUse is a loud failure, never a text parse.
    for block in _content(response):
        tool_use = block.get("toolUse")
        if isinstance(tool_use, dict) and isinstance(tool_use.get("input"), dict):
            payload: dict[str, Any] = tool_use["input"]
            return payload
    raise AiProviderError(
        f"no toolUse block in the model response (stopReason={_stop(response)}) "
        f"{_text_snippet(response)!r}"
    )


def _parse_recipe(payload: dict[str, Any], stop_reason: object = None) -> RawRecipeOutput:
    try:
        return RawRecipeOutput(
            name=str(payload["name"]),
            ingredients=tuple(
                RawIngredient(
                    name=str(item["name"]),
                    quantity=float(item["quantity"]),
                    unit=str(item["unit"]),
                )
                for item in payload["ingredients"]
            ),
            tools=tuple(str(tool) for tool in payload.get("tools", [])),
            procedure=tuple(str(step) for step in payload["procedure"]),
            category=str(payload["category"]),
            servings=None if payload.get("servings") is None else int(payload["servings"]),
            # Passed through raw (G-90): the domain validator, not this
            # adapter, is what rejects a bad value (issue
            # tiempo-estimado-numeric-minutes).
            estimated_time=payload.get("estimated_time"),
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise AiProviderError(
            f"unparseable tool input: {exc} (stopReason={stop_reason}) "
            f"{json.dumps(payload, ensure_ascii=False)[:_SNIPPET_LIMIT]!r}"
        ) from exc


class BedrockAiProvider:
    """`client` is injected in tests; production reads the default Bedrock-runtime client."""

    def __init__(self, client: Any = None) -> None:
        # boto3 ships no type stubs, so the client handle is untyped
        # (docs/conventions.md — no bare Any without a justification).
        self._client = client

    def _bedrock(self) -> Any:
        return self._client or boto3.client("bedrock-runtime", region_name=_REGION)

    def generate(self, prompt: AiPrompt) -> RawRecipeOutput:
        messages = [{"role": "user", "content": [{"text": _render(prompt)}]}]
        try:
            response = self._bedrock().converse(
                modelId=_model_id(),
                messages=messages,
                inferenceConfig={"maxTokens": _MAX_TOKENS},
                toolConfig=_TOOL_CONFIG,
            )
        except (BotoCoreError, ClientError) as exc:
            raise AiProviderError(f"Bedrock invocation failed: {exc}") from exc
        return _parse_recipe(_tool_input(response), _stop(response))
