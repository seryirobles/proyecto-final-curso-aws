"""Bedrock Converse inference settings read from the environment
(specs/ai_inference_config/design.md). Invalid values fail fast; messages name the
variable and its domain, never the value or any credential (R15-R17)."""

from __future__ import annotations

import logging
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, cast

from planner_core.ports.ai_provider import AiProviderError

logger = logging.getLogger(__name__)

DEFAULT_MAX_TOKENS = 4096
_MAX_TOKENS_CEILING = 65000
_TIERS = ("standard", "priority", "flex")
_EFFORTS = ("low", "medium", "high")


class InferenceConfigError(AiProviderError):
    """An inference variable is out of domain or the combination is rejected."""


@dataclass(frozen=True)
class InferenceSettings:
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float | None = None
    top_p: float | None = None
    service_tier: Literal["standard", "priority", "flex"] = "standard"
    reasoning: bool = False
    effort: Literal["low", "medium", "high"] = "low"


def _reject(variable: str, domain: str) -> InferenceConfigError:
    message = f"{variable} must be {domain}"
    logger.error(message)
    return InferenceConfigError(message)


def _raw(environ: Mapping[str, str], variable: str) -> str | None:
    value = environ.get(variable, "").strip()  # blank means unset (R18)
    return value or None


def _unit_float(environ: Mapping[str, str], variable: str) -> float | None:
    raw = _raw(environ, variable)
    if raw is None:
        return None
    domain = "a number from 0 to 1"
    try:
        value = float(raw)
    except ValueError:
        raise _reject(variable, domain) from None
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise _reject(variable, domain)
    return value


def _enum(environ: Mapping[str, str], variable: str, options: tuple[str, ...], default: str) -> str:
    raw = _raw(environ, variable)
    if raw is None:
        return default
    if raw not in options:
        raise _reject(variable, "one of " + ", ".join(options))
    return raw


def _max_tokens(environ: Mapping[str, str]) -> int:
    raw = _raw(environ, "AI_MAX_TOKENS")
    if raw is None:
        return DEFAULT_MAX_TOKENS
    if not (raw.isascii() and raw.isdecimal()) or not 1 <= int(raw) <= _MAX_TOKENS_CEILING:
        raise _reject("AI_MAX_TOKENS", f"an integer from 1 to {_MAX_TOKENS_CEILING}")
    return int(raw)


def load_inference_settings(environ: Mapping[str, str]) -> InferenceSettings:
    reasoning = _enum(environ, "AI_REASONING_ENABLED", ("true", "false"), "false")
    # Effort is validated even with reasoning off, to catch a typo early.
    effort = _enum(environ, "AI_REASONING_EFFORT", _EFFORTS, "low")
    return InferenceSettings(
        max_tokens=_max_tokens(environ),
        temperature=_unit_float(environ, "AI_TEMPERATURE"),
        top_p=_unit_float(environ, "AI_TOP_P"),
        service_tier=cast(
            Literal["standard", "priority", "flex"],
            _enum(environ, "AI_SERVICE_TIER", _TIERS, "standard"),
        ),
        reasoning=reasoning == "true",
        effort=cast(Literal["low", "medium", "high"], effort),
    )


def converse_kwargs(settings: InferenceSettings) -> dict[str, Any]:
    """Only inferenceConfig, plus serviceTier / additionalModelRequestFields when
    needed. Never topK, stopSequences, guardrail or cache point (R14)."""
    high = settings.reasoning and settings.effort == "high"
    if high:
        conflicts = [
            name
            for name, value in (
                ("AI_TEMPERATURE", settings.temperature),
                ("AI_TOP_P", settings.top_p),
            )
            if value is not None
        ]
        if conflicts:
            message = (
                f"{' and '.join(conflicts)} cannot be set while "
                "AI_REASONING_ENABLED=true and AI_REASONING_EFFORT=high"
            )
            logger.error(message)
            raise InferenceConfigError(message)
    config: dict[str, Any] = {}
    if not high:  # Bedrock rejects maxTokens with effort high (R23)
        config["maxTokens"] = settings.max_tokens
    if settings.temperature is not None:
        config["temperature"] = settings.temperature
    if settings.top_p is not None:
        config["topP"] = settings.top_p
    kwargs: dict[str, Any] = {"inferenceConfig": config}
    if settings.service_tier != "standard":
        kwargs["serviceTier"] = {"type": settings.service_tier}
    if settings.reasoning:
        kwargs["additionalModelRequestFields"] = {
            "reasoningConfig": {"type": "enabled", "maxReasoningEffort": settings.effort}
        }
    return kwargs
