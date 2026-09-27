"""Single-recipe submission: probe loop, reference snapshot, guards (R2, R3, R11-R18)."""

from __future__ import annotations

import dataclasses
from datetime import date

import pytest
from support.fakes import FakeConfig, FakeGenerationQueue, FakeRecipeRepository

from planner_core.application.single_recipe_submission import (
    SingleRecipeOutcome,
    submit_single_recipe,
)
from planner_core.domain.ai_prompt import PROMPT_VERSION_CONFIG_KEY, UnknownPromptVersion
from planner_core.domain.calendar import MealSlot, SlotRef
from planner_core.domain.generation import (
    ReferenceSource,
    SingleRecipeRequest,
    SpecificationSource,
    single_recipe_key,
)
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import MissingIngredients, MissingTools, Recipe
from planner_core.ports.generation_queue import StoredGeneration
from planner_core.ports.recipes import LibraryRecipe, RecipeNotFound

SLOT = SlotRef(date(2026, 8, 19), MealSlot.LUNCH)
SPEC = SingleRecipeRequest(SLOT, SpecificationSource(("lentejas",), ("olla",)))


def _submit(
    request: SingleRecipeRequest,
    queue: FakeGenerationQueue,
    recipes: FakeRecipeRepository | None = None,
    config: FakeConfig | None = None,
) -> SingleRecipeOutcome:
    return submit_single_recipe(
        request,
        queue=queue,
        recipes=recipes if recipes is not None else FakeRecipeRepository(),
        author="u-1",
        config=config if config is not None else FakeConfig({PROMPT_VERSION_CONFIG_KEY: "v1"}),
    )


def _set(
    queue: FakeGenerationQueue, request: SingleRecipeRequest, attempt: int, status: str
) -> None:
    key = single_recipe_key(request, attempt)
    queue.stored[key] = StoredGeneration(idempotency_key=key, status=status)


def test_outcome_is_frozen() -> None:
    outcome = SingleRecipeOutcome("k", 0, None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        outcome.__setattr__("attempt", 1)


def test_fresh_specification_enqueues_at_attempt_zero() -> None:
    """R1, R11."""
    queue = FakeGenerationQueue()
    outcome = _submit(SPEC, queue)
    assert outcome.attempt == 0 and outcome.stored is None
    assert outcome.idempotency_key == single_recipe_key(SPEC, 0)
    sent = queue.recipe_submitted[0]
    assert (sent.request, sent.reference_recipe, sent.prompt_version_id, sent.author) == (
        SPEC,
        None,
        "v1",
        "u-1",
    )


def test_reference_source_carries_the_library_snapshot() -> None:
    """R2."""
    recipe = Recipe(
        name="Tortilla",
        ingredients=(),
        tools=(),
        procedure=(),
        category=IngredientCategory.MEAT,
    )
    recipes = FakeRecipeRepository({"r1": LibraryRecipe("r1", recipe, "u-2")})
    queue = FakeGenerationQueue()
    request = SingleRecipeRequest(None, ReferenceSource("r1", ("sin gluten",)))
    outcome = _submit(request, queue, recipes)
    assert outcome.stored is None
    assert queue.recipe_submitted[0].reference_recipe == recipe


def test_unknown_reference_recipe_raises_and_enqueues_nothing() -> None:
    """R3."""
    queue = FakeGenerationQueue()
    with pytest.raises(RecipeNotFound):
        _submit(SingleRecipeRequest(None, ReferenceSource("nope", ())), queue)
    assert queue.recipe_submitted == []


@pytest.mark.parametrize("status", ["pending", "running"])
def test_in_flight_record_is_returned_without_enqueueing(status: str) -> None:
    """R12."""
    queue = FakeGenerationQueue()
    _set(queue, SPEC, 0, status)
    outcome = _submit(SPEC, queue)
    assert outcome.stored is not None and outcome.stored.status == status
    assert outcome.attempt == 0
    assert queue.recipe_submitted == []


@pytest.mark.parametrize("terminal", ["completed", "failed"])
def test_terminal_record_advances_the_attempt(terminal: str) -> None:
    """R11, R13."""
    queue = FakeGenerationQueue()
    _set(queue, SPEC, 0, terminal)
    outcome = _submit(SPEC, queue)
    assert outcome.attempt == 1 and outcome.stored is None
    assert queue.recipe_submitted[0].idempotency_key == single_recipe_key(SPEC, 1)


def test_consecutive_terminals_then_in_flight_returns_that_one() -> None:
    """R11."""
    queue = FakeGenerationQueue()
    _set(queue, SPEC, 0, "completed")
    _set(queue, SPEC, 1, "failed")
    _set(queue, SPEC, 2, "running")
    outcome = _submit(SPEC, queue)
    assert outcome.attempt == 2 and outcome.stored is not None


def test_discarding_the_terminal_record_rederives_its_attempt() -> None:
    """R15."""
    queue = FakeGenerationQueue()
    _set(queue, SPEC, 0, "completed")
    _set(queue, SPEC, 1, "completed")
    queue.discard(single_recipe_key(SPEC, 1))
    assert _submit(SPEC, queue).attempt == 1


def test_a_different_key_for_the_same_slot_is_accepted_independently() -> None:
    """R16."""
    queue = FakeGenerationQueue()
    _set(queue, SPEC, 0, "running")
    other = SingleRecipeRequest(SLOT, SpecificationSource(("arroz",), ("olla",)))
    outcome = _submit(other, queue)
    assert outcome.stored is None
    assert len(queue.recipe_submitted) == 1


def test_empty_ingredients_or_tools_are_rejected_before_any_enqueue() -> None:
    """R17, R18."""
    queue = FakeGenerationQueue()
    with pytest.raises(MissingIngredients):
        _submit(SingleRecipeRequest(SLOT, SpecificationSource((), ("olla",))), queue)
    with pytest.raises(MissingTools):
        _submit(SingleRecipeRequest(SLOT, SpecificationSource(("a",), ())), queue)
    assert queue.recipe_submitted == []


def test_unset_prompt_version_fails_before_any_write() -> None:
    """R2: the whole-week path's finding-2 guard applies here too."""
    queue = FakeGenerationQueue()
    with pytest.raises(UnknownPromptVersion):
        _submit(SPEC, queue, config=FakeConfig())
    assert queue.recipe_submitted == [] and queue.stored == {}
