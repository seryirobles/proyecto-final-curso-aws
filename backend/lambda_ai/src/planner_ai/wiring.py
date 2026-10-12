"""Composition root for the `ai` worker (docs/conventions.md — the only module
naming a concrete adapter, selected by environment). Builds the real stack:
Bedrock provider, SSM kill-switch gate, the DynamoDB week, library (read) + generation-record
adapters, and the system clock."""

from __future__ import annotations

from dataclasses import dataclass

from planner_core.ports.ai_provider import AiProvider
from planner_core.ports.clock import Clock, SystemClock
from planner_core.ports.generation_gate import GenerationGate
from planner_core.ports.generation_queue import GenerationResultSink
from planner_core.ports.recipes import RecipeRepository
from planner_core.ports.weeks import WeekRepository

from planner_ai.adapters.bedrock import BedrockAiProvider
from planner_ai.adapters.dynamo.generations import DynamoGenerationRecords
from planner_ai.adapters.dynamo.recipes import DynamoRecipeRepository
from planner_ai.adapters.dynamo.weeks import DynamoWeekRepository
from planner_ai.adapters.ssm import SsmGenerationGate


@dataclass(frozen=True)
class Dependencies:
    """Every port the worker use case needs, bundled once per invocation."""

    provider: AiProvider
    weeks: WeekRepository
    recipes: RecipeRepository
    records: GenerationResultSink
    gate: GenerationGate
    clock: Clock


def build_dependencies() -> Dependencies:
    """The real, AWS-backed stack; a deployed function calls this, tests build
    their own `Dependencies` from `core`'s fakes."""
    return Dependencies(
        provider=BedrockAiProvider(),
        weeks=DynamoWeekRepository(),
        recipes=DynamoRecipeRepository(),
        records=DynamoGenerationRecords(),
        gate=SsmGenerationGate(),
        clock=SystemClock(),
    )
