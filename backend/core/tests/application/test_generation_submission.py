"""Tests for whole-week generation submission: deterministic idPeticionIA, an
idempotent hit returns the stored result without enqueuing, message enrichment
and synchronous pinned-slot candidate writes (R27, R28, R29, R40-R43)."""

from __future__ import annotations

import dataclasses
from datetime import date

import pytest
from support.fakes import (
    FakeConfig,
    FakeGenerationQueue,
    FakeRecipeRepository,
    FakeRuleRepository,
    FakeWeekRepository,
)

from planner_core.application.generation_submission import SubmissionOutcome, submit_generation
from planner_core.domain.ai_prompt import PROMPT_VERSION_CONFIG_KEY, UnknownPromptVersion
from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import definitive
from planner_core.domain.generation import (
    GenerationMode,
    GenerationRequest,
    GenerationTargets,
    build_plan,
)
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Recipe
from planner_core.domain.rules import CategoryCountRule, PinRule, RuleSet
from planner_core.ports.config import ConfigPort
from planner_core.ports.generation_queue import StoredGeneration
from planner_core.ports.recipes import LibraryRecipe

FIRST_DAY = date(2026, 8, 17)  # Monday of 2026-W34
REQUEST = GenerationRequest(week=IsoWeek(2026, 34), mode=GenerationMode.MIX)


def _submit(
    request: GenerationRequest = REQUEST,
    first_day: date = FIRST_DAY,
    *,
    weeks: FakeWeekRepository,
    rules: FakeRuleRepository,
    queue: FakeGenerationQueue,
    recipes: FakeRecipeRepository | None = None,
    author: str = "u-1",
    config: ConfigPort | None = None,
) -> SubmissionOutcome:
    return submit_generation(
        request,
        first_day,
        weeks=weeks,
        rules=rules,
        queue=queue,
        recipes=recipes if recipes is not None else FakeRecipeRepository(),
        author=author,
        config=config if config is not None else FakeConfig({PROMPT_VERSION_CONFIG_KEY: "v1"}),
    )


def _fakes() -> tuple[FakeWeekRepository, FakeRuleRepository, FakeGenerationQueue]:
    return FakeWeekRepository(), FakeRuleRepository(), FakeGenerationQueue()


def test_submission_outcome_is_frozen() -> None:
    """docs/conventions.md: every new frozen dataclass gets this test."""
    outcome = SubmissionOutcome(
        idempotency_key="x", targets=GenerationTargets((), (), (), ()), stored=None, enqueued=True
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        outcome.__setattr__("enqueued", False)


def test_submission_derives_the_same_id_twice_for_the_same_input() -> None:
    weeks, rules, queue = _fakes()
    # R27 — the id equals the domain-derived key (empty fakes -> RuleSet(), no week);
    # asserting against the derivation defeats a hardcoded constant id.
    expected = build_plan(REQUEST, RuleSet(), FIRST_DAY, {}).idempotency_key

    first = _submit(weeks=weeks, rules=rules, queue=queue)
    second = _submit(weeks=weeks, rules=rules, queue=queue)

    assert first.idempotency_key == expected
    assert second.idempotency_key == expected


def test_submission_derives_a_different_id_for_a_materially_different_request() -> None:
    """R27 — a constant id would collide two distinct inputs."""
    weeks, rules, queue = _fakes()
    other = GenerationRequest(week=IsoWeek(2026, 35), mode=GenerationMode.MIX)

    first = _submit(weeks=weeks, rules=rules, queue=queue)
    second = _submit(other, date(2026, 8, 24), weeks=weeks, rules=rules, queue=queue)

    assert first.idempotency_key != second.idempotency_key


def test_a_fresh_request_enqueues_exactly_once() -> None:
    weeks, rules, queue = _fakes()

    outcome = _submit(weeks=weeks, rules=rules, queue=queue)

    assert outcome.enqueued is True and outcome.stored is None
    assert queue.submissions == [(outcome.idempotency_key, REQUEST)]


def test_an_idempotent_hit_returns_the_stored_result_without_enqueuing() -> None:
    weeks, rules, queue = _fakes()
    key = _submit(weeks=weeks, rules=rules, queue=queue).idempotency_key
    queue.submissions.clear()
    queue.stored[key] = StoredGeneration(idempotency_key=key, status="done", result="{}")

    outcome = _submit(weeks=weeks, rules=rules, queue=queue)

    assert outcome.enqueued is False
    assert outcome.stored is not None and outcome.stored.result == "{}"
    assert queue.submissions == []


# --- R40: message enrichment --------------------------------------------------


def test_submit_payload_enrichment() -> None:
    """R40 — effectiveRules match build_plan's effective_rules; promptVersionId
    and authorUserId ride along."""
    weeks, rules, queue = _fakes()
    rules.save_rule(CategoryCountRule(category=IngredientCategory.VEGETABLE, count=2))
    expected = build_plan(REQUEST, rules.get(), FIRST_DAY, {}).effective_rules

    _submit(weeks=weeks, rules=rules, queue=queue, author="u-9")

    assert len(queue.submitted) == 1
    handed = queue.submitted[0]
    assert handed.effective_rules == expected
    assert handed.prompt_version_id == "v1"  # resolved via feature 24's guard (finding 2)
    assert handed.author == "u-9"


def test_an_unset_prompt_version_key_raises_and_enqueues_nothing() -> None:
    """finding 2 — the submit fails fast through feature 24's guard instead of
    enqueuing a run the worker would lose after claiming."""
    weeks, rules, queue = _fakes()

    with pytest.raises(UnknownPromptVersion):
        _submit(weeks=weeks, rules=rules, queue=queue, config=FakeConfig({}))

    assert queue.submissions == [] and queue.submitted == []


# --- R41-R43: pinned-slot candidate persistence ------------------------------


def _seed_pinned_recipe(recipes: FakeRecipeRepository, rules: FakeRuleRepository) -> SlotRef:
    """A library recipe plus a rule pinning it to Monday lunch (an open slot)."""
    recipe = Recipe(
        name="Lentejas",
        ingredients=(),
        tools=(),
        procedure=("Cocer",),
        category=IngredientCategory.LEGUME,
    )
    recipes.entries["r-1"] = LibraryRecipe(id="r-1", recipe=recipe, author="chef")
    rules.save_rule(PinRule(day=1, slot=MealSlot.LUNCH, recipe_id="r-1"))
    return SlotRef(IsoWeek(2026, 34).monday, MealSlot.LUNCH)


def test_a_fresh_submit_writes_the_pinned_slot_candidate_authored_by_the_submitter() -> None:
    """R41, R42 — deterministic library-snapshot copy, no model call, attributed
    to the submitting user, decoupled from the library entry."""
    weeks, rules, queue = _fakes()
    recipes = FakeRecipeRepository()
    slot = _seed_pinned_recipe(recipes, rules)

    _submit(weeks=weeks, rules=rules, queue=queue, recipes=recipes, author="u-7")

    plan = weeks.get_week(IsoWeek(2026, 34))[slot]
    assert len(plan.candidates) == 1
    candidate = plan.candidates[0]
    assert candidate.author == "u-7"
    assert candidate.meal.name == "Lentejas"
    # snapshot is a distinct type holding no reference back (FR-CAND-07, G-05)
    assert not isinstance(candidate.meal, Recipe)


def test_an_idempotent_hit_writes_no_pinned_candidate() -> None:
    """R43 — the pinned candidates were written on the original fresh submit."""
    weeks, rules, queue = _fakes()
    recipes = FakeRecipeRepository()
    slot = _seed_pinned_recipe(recipes, rules)
    key = _submit(weeks=weeks, rules=rules, queue=queue, recipes=recipes).idempotency_key
    writes_after_first = weeks.versions[IsoWeek(2026, 34)]
    queue.stored[key] = StoredGeneration(idempotency_key=key, status="done", result="{}")

    outcome = _submit(weeks=weeks, rules=rules, queue=queue, recipes=recipes)

    assert outcome.enqueued is False
    assert weeks.versions[IsoWeek(2026, 34)] == writes_after_first
    assert len(weeks.get_week(IsoWeek(2026, 34))[slot].candidates) == 1
    assert definitive(weeks.get_week(IsoWeek(2026, 34))[slot]) is None
