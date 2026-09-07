"""The AI provider port: a prompt value object in, a parsed provider-agnostic
`RawRecipeOutput` out (FR-AI-09). No SDK import — the Bedrock adapter lives in
`planner_ai` (docs/architecture.md section 1.2.6 / 3.1)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from planner_core.domain.ai_output import RawRecipeOutput
from planner_core.domain.ai_prompt import CategoryPrompt, ReferencePrompt, SpecificationPrompt
from planner_core.domain.errors import PlannerError

AiPrompt = CategoryPrompt | SpecificationPrompt | ReferencePrompt


class AiProviderError(PlannerError):
    """Raised by an adapter when the model call fails or its output cannot be
    parsed into a RawRecipeOutput. The use case catches it as a per-slot
    failure (GenerationFailureReason.INVALID_OUTPUT — specs/ai_lambda/design.md section 4)."""


@runtime_checkable
class AiProvider(Protocol):
    """Renders a prompt, calls the model, parses its output. One method."""

    def generate(self, prompt: AiPrompt) -> RawRecipeOutput:
        """Raises AiProviderError on an unparseable or failed response."""
        ...
