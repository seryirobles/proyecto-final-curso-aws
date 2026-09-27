"""Single-recipe generation submission (FR-AI-01, -02, -08, -09): derive the
attempt by probing AP26, then hand the request off once (G-92,
specs/single_recipe_generation/design.md section 1)."""

from __future__ import annotations

from dataclasses import dataclass

from planner_core.application.prompt_version import resolve_active_prompt_version
from planner_core.domain.generation import (
    SingleRecipeRequest,
    SpecificationSource,
    single_recipe_key,
)
from planner_core.domain.recipe import MissingIngredients, MissingTools, Recipe
from planner_core.ports.config import ConfigPort
from planner_core.ports.generation_queue import GenerationQueue, StoredGeneration
from planner_core.ports.recipes import RecipeNotFound, RecipeRepository

_IN_FLIGHT = ("pending", "running")


@dataclass(frozen=True)
class SingleRecipeOutcome:
    """The derived key and attempt, plus the in-flight record (returned as 200,
    nothing enqueued) or None (freshly enqueued, 202)."""

    idempotency_key: str
    attempt: int
    stored: StoredGeneration | None


def submit_single_recipe(
    request: SingleRecipeRequest,
    *,
    queue: GenerationQueue,
    recipes: RecipeRepository,
    author: str,
    config: ConfigPort,
) -> SingleRecipeOutcome:
    """R2, R3, R11-R13, R15-R18. `attempt` is the count of consecutive terminal
    records from 0 (never client-supplied); a terminal record, failed included,
    advances it. No per-scope lock exists (FR-AI-09, R16)."""
    source = request.source
    reference: Recipe | None = None
    if isinstance(source, SpecificationSource):
        if len(source.ingredients) == 0:
            raise MissingIngredients
        if len(source.tools) == 0:
            raise MissingTools
    else:
        entry = recipes.get(source.recipe_id)
        if entry is None:
            raise RecipeNotFound(source.recipe_id)
        reference = entry.recipe

    attempt = 0
    while True:
        key = single_recipe_key(request, attempt)
        stored = queue.stored_generation(key)
        if stored is None:
            break
        if stored.status in _IN_FLIGHT:
            return SingleRecipeOutcome(idempotency_key=key, attempt=attempt, stored=stored)
        attempt += 1

    version = resolve_active_prompt_version(config)  # fail before anything is enqueued
    queue.submit_recipe(
        key,
        request,
        reference_recipe=reference,
        prompt_version_id=version.version_id,
        author=author,
    )
    return SingleRecipeOutcome(idempotency_key=key, attempt=attempt, stored=None)
