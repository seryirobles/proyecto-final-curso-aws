"""Single-recipe worker use case, with fakes (R19-R26)."""

from __future__ import annotations

import dataclasses
import inspect
from collections.abc import Mapping
from dataclasses import dataclass, field

import pytest
from support.fakes import FakeAiProvider, FakeGenerationGate, FakeGenerationQueue

from planner_core import messages
from planner_core.application.single_recipe_generation import (
    ReferenceInputs,
    SingleRecipeRunOutcome,
    run_single_recipe_generation,
)
from planner_core.domain.ai_output import RawRecipeOutput
from planner_core.domain.ai_prompt import ReferencePrompt, SpecificationPrompt
from planner_core.domain.generation import SpecificationSource
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Recipe
from planner_core.ports.ai_provider import AiPrompt, AiProviderError
from planner_core.ports.generation_queue import StoredGeneration

KEY = "k-1"
SPEC = SpecificationSource(("lentejas",), ("olla",))
REFERENCE = ReferenceInputs(
    Recipe(
        name="Tortilla", ingredients=(), tools=(), procedure=(), category=IngredientCategory.MEAT
    ),
    ("sin gluten",),
)


def _encode(recipe: Recipe) -> Mapping[str, object]:
    return {"name": recipe.name}


@dataclass
class _SpyProvider(FakeAiProvider):
    prompts: list[AiPrompt] = field(default_factory=list)

    def generate(self, prompt: AiPrompt) -> RawRecipeOutput:
        self.prompts.append(prompt)
        return super().generate(prompt)


def _run(
    source: SpecificationSource | ReferenceInputs = SPEC,
    *,
    provider: FakeAiProvider | None = None,
    queue: FakeGenerationQueue | None = None,
    gate: FakeGenerationGate | None = None,
) -> SingleRecipeRunOutcome:
    return run_single_recipe_generation(
        KEY,
        source,
        "v1",
        provider=provider if provider is not None else FakeAiProvider(),
        queue=queue if queue is not None else _pending_queue(),
        gate=gate if gate is not None else FakeGenerationGate(),
        encode_recipe=_encode,
    )


def _pending_queue() -> FakeGenerationQueue:
    queue = FakeGenerationQueue()
    queue.stored[KEY] = StoredGeneration(idempotency_key=KEY, status="pending")
    return queue


def test_run_outcome_and_reference_inputs_are_frozen() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        SingleRecipeRunOutcome(True, None).__setattr__("claimed", False)
    with pytest.raises(dataclasses.FrozenInstanceError):
        REFERENCE.__setattr__("extra_specifications", ())


def test_specification_message_builds_the_specification_prompt() -> None:
    """R19."""
    provider = _SpyProvider()
    _run(SPEC, provider=provider)
    prompt = provider.prompts[0]
    assert isinstance(prompt, SpecificationPrompt)
    assert (prompt.ingredients, prompt.tools) == (SPEC.ingredients, SPEC.tools)


def test_reference_message_builds_the_reference_prompt() -> None:
    """R20."""
    provider = _SpyProvider()
    _run(REFERENCE, provider=provider)
    prompt = provider.prompts[0]
    assert isinstance(prompt, ReferencePrompt)
    assert prompt.reference_recipe == REFERENCE.recipe
    assert prompt.extra_specifications == REFERENCE.extra_specifications


def test_a_lost_claim_never_invokes_the_provider() -> None:
    """R21."""
    queue = _pending_queue()
    queue.stored[KEY] = StoredGeneration(idempotency_key=KEY, status="running")
    provider = FakeAiProvider()
    outcome = _run(provider=provider, queue=queue)
    assert outcome.claimed is False and outcome.terminal_status is None
    assert provider.calls == 0 and queue.results == {}


def test_disabled_gate_records_the_unavailable_failure_without_the_provider() -> None:
    """R22."""
    queue = _pending_queue()
    provider = FakeAiProvider()
    outcome = _run(provider=provider, queue=queue, gate=FakeGenerationGate(enabled=False))
    assert outcome.terminal_status == "failed" and provider.calls == 0
    assert queue.results[KEY] == {
        "error": {
            "code": "generation_unavailable",
            "message": messages.AI_GENERATION_UNAVAILABLE,
        }
    }
    assert queue.stored[KEY].status == "failed"


def test_valid_output_records_completed_with_the_encoded_recipe() -> None:
    """R23."""
    queue = _pending_queue()
    outcome = _run(queue=queue)
    assert outcome.claimed is True and outcome.terminal_status == "completed"
    assert queue.stored[KEY].status == "completed"
    assert queue.results[KEY] == {"name": "Ensalada templada de lentejas"}


def test_provider_error_records_failed_with_the_es_es_message() -> None:
    """R26."""
    queue = _pending_queue()
    _run(provider=FakeAiProvider(responses=[AiProviderError("boom")]), queue=queue)
    assert queue.stored[KEY].status == "failed"
    assert queue.results[KEY] == {
        "error": {"code": "invalid_output", "message": messages.AI_GENERATION_INVALID_OUTPUT}
    }


def test_invalid_output_records_failed() -> None:
    """R26."""
    bad = RawRecipeOutput(
        name="x", ingredients=(), tools=("bol",), procedure=("a",), category="nonsense"
    )
    queue = _pending_queue()
    _run(provider=FakeAiProvider(responses=[bad]), queue=queue)
    assert queue.stored[KEY].status == "failed"


def test_the_use_case_takes_no_week_repository() -> None:
    """R24, R25: nothing to call, nothing to bump."""
    params = set(inspect.signature(run_single_recipe_generation).parameters)
    assert not params & {"weeks", "week_repository", "recipes"}
