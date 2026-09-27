"""Single-recipe AI generation worker use case (FR-AI-01, -02, -10, NFR-AI-01):
claim, prompt, gate, provider, validate, record; never touches WeekRepository
(specs/single_recipe_generation/design.md sections 1 and 3)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from planner_core.domain.ai_output import (
    GenerationFailure,
    GenerationFailureReason,
    accept_preview,
    build_generation_failure,
    validate_and_preview,
)
from planner_core.domain.ai_prompt import build_reference_prompt, build_specification_prompt
from planner_core.domain.generation import SpecificationSource
from planner_core.domain.recipe import Recipe
from planner_core.ports.ai_provider import AiPrompt, AiProvider, AiProviderError
from planner_core.ports.generation_gate import GenerationGate
from planner_core.ports.generation_queue import GenerationResultSink

_COMPLETED = "completed"
_FAILED = "failed"


@dataclass(frozen=True)
class ReferenceInputs:
    """A reference source as the worker holds it: the snapshot the api put on the message."""

    recipe: Recipe
    extra_specifications: tuple[str, ...]


@dataclass(frozen=True)
class SingleRecipeRunOutcome:
    """Whether this worker claimed the message and the terminal status recorded."""

    claimed: bool
    terminal_status: str | None


def _failed(
    sink: GenerationResultSink, key: str, failure: GenerationFailure
) -> SingleRecipeRunOutcome:
    error = {"code": failure.reason.value, "message": failure.message}
    sink.record_result(key, _FAILED, {"error": error})
    return SingleRecipeRunOutcome(claimed=True, terminal_status=_FAILED)


def run_single_recipe_generation(
    idempotency_key: str,
    source: SpecificationSource | ReferenceInputs,
    prompt_version_id: str,
    *,
    provider: AiProvider,
    queue: GenerationResultSink,
    gate: GenerationGate,
    encode_recipe: Callable[[Recipe], Mapping[str, object]],
) -> SingleRecipeRunOutcome:
    """R19-R26. `encode_recipe` yields the wire recipe shape the accept path
    decodes (R23); it is injected because core owns no wire format."""
    if not queue.claim(idempotency_key):  # R21 - redelivery guard
        return SingleRecipeRunOutcome(claimed=False, terminal_status=None)

    if not gate.is_generation_enabled():  # R22
        unavailable = build_generation_failure(GenerationFailureReason.GENERATION_UNAVAILABLE)
        return _failed(queue, idempotency_key, unavailable)

    prompt: AiPrompt
    if isinstance(source, SpecificationSource):
        prompt = build_specification_prompt(source.ingredients, source.tools, prompt_version_id)
    else:
        prompt = build_reference_prompt(
            source.recipe, source.extra_specifications, prompt_version_id
        )

    try:
        raw = provider.generate(prompt)
    except AiProviderError:  # R26
        invalid = build_generation_failure(GenerationFailureReason.INVALID_OUTPUT)
        return _failed(queue, idempotency_key, invalid)

    outcome = validate_and_preview(raw)
    if isinstance(outcome, GenerationFailure):  # R26
        return _failed(queue, idempotency_key, outcome)

    recipe = accept_preview(outcome.preview)
    queue.record_result(idempotency_key, _COMPLETED, encode_recipe(recipe))  # R23
    return SingleRecipeRunOutcome(claimed=True, terminal_status=_COMPLETED)
