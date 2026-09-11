"""`AiProvider` backed by AWS Bedrock + Anthropic Claude (docs/architecture.md
section 1.2.6). Renders the prompt value object to the Anthropic messages format,
calls `bedrock-runtime:InvokeModel`, and parses the JSON recipe block the model
returns into a `RawRecipeOutput`. A parse or call failure raises `AiProviderError`
(specs/ai_lambda/design.md section 4)."""

from __future__ import annotations

import json
import os
from string import Template
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from planner_core.domain.ai_output import RawIngredient, RawRecipeOutput
from planner_core.domain.ai_prompt import CategoryPrompt, ReferencePrompt, SpecificationPrompt
from planner_core.ports.ai_provider import AiPrompt, AiProviderError

BEDROCK_MODEL_ID = "anthropic.claude-sonnet-5"
"""Bedrock's `anthropic.` prefix; Sonnet to start (architecture.md section 1.2.6).
Overridable by AI_MODEL_ID so the Haiku evaluation needs no code change (design.md section 10)."""

_ANTHROPIC_VERSION = "bedrock-2023-05-31"
_MAX_TOKENS = 4096
_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


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


def _extract_text(response_body: dict[str, Any]) -> str:
    blocks = response_body.get("content", [])
    for block in blocks:
        if block.get("type") == "text" and isinstance(block.get("text"), str):
            return str(block["text"])
    raise AiProviderError("no text block in the model response")


def _parse_recipe(text: str) -> RawRecipeOutput:
    try:
        start, end = text.index("{"), text.rindex("}")
        payload = json.loads(text[start : end + 1])
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
            estimated_time=None
            if payload.get("estimated_time") is None
            else str(payload["estimated_time"]),
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise AiProviderError(f"unparseable model output: {exc}") from exc


class BedrockAiProvider:
    """`client` is injected in tests; production reads the default Bedrock-runtime client."""

    def __init__(self, client: Any = None) -> None:
        # boto3 ships no type stubs, so the client handle is untyped
        # (docs/conventions.md — no bare Any without a justification).
        self._client = client

    def _bedrock(self) -> Any:
        return self._client or boto3.client("bedrock-runtime", region_name=_REGION)

    def generate(self, prompt: AiPrompt) -> RawRecipeOutput:
        body = json.dumps(
            {
                "anthropic_version": _ANTHROPIC_VERSION,
                "max_tokens": _MAX_TOKENS,
                "messages": [{"role": "user", "content": _render(prompt)}],
            }
        )
        try:
            response = self._bedrock().invoke_model(modelId=_model_id(), body=body)
            payload = json.loads(response["body"].read())
        except (BotoCoreError, ClientError, ValueError, KeyError) as exc:
            raise AiProviderError(f"Bedrock invocation failed: {exc}") from exc
        return _parse_recipe(_extract_text(payload))
