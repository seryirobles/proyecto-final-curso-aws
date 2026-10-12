"""Parsing a single-recipe SQS body and dispatching on `type`
(specs/single_recipe_generation R14, R19, R20, R27)."""

from __future__ import annotations

import dataclasses
import json
from typing import Any

import pytest
from planner_core.application.single_recipe_generation import ReferenceInputs
from planner_core.domain.generation import SpecificationSource
from planner_core.ports.generation_queue import StoredGeneration
from support.fakes import (
    FakeAiProvider,
    FakeClock,
    FakeGenerationGate,
    FakeGenerationQueue,
    FakeRecipeRepository,
    FakeWeekRepository,
)

from planner_ai.handler import handle
from planner_ai.message import MalformedMessage, RecipeMessage, message_type, parse_recipe_message
from planner_ai.wiring import Dependencies

REFERENCE_RECIPE = {
    "name": "Tortilla",
    "category": "meat",
    "servings": None,
    "estimatedTime": None,
    "ingredients": [{"name": "huevos", "quantity": 4, "unit": "unit"}],
    "tools": ["sarten"],
    "procedure": ["Cuajar."],
}


def _spec_body(key: str = "k1", **overrides: object) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": "recipe",
        "idPeticionIA": key,
        "target": {"kind": "library"},
        "source": {"kind": "specification", "ingredients": ["lentejas"], "tools": ["olla"]},
        "referenceRecipe": None,
        "promptVersionId": "v1",
        "authorUserId": "u-1",
    }
    body.update(overrides)
    return body


def _ref_body() -> dict[str, Any]:
    return _spec_body(
        source={"kind": "reference", "recipeId": "r-1", "extraSpecifications": ["sin gluten"]},
        referenceRecipe=REFERENCE_RECIPE,
    )


def test_recipe_message_is_frozen() -> None:
    message = parse_recipe_message(_spec_body())
    with pytest.raises(dataclasses.FrozenInstanceError):
        message.__setattr__("author", "x")


def test_a_specification_body_parses() -> None:
    """R19."""
    message = parse_recipe_message(_spec_body())
    assert isinstance(message, RecipeMessage)
    assert message.source == SpecificationSource(("lentejas",), ("olla",))
    assert (message.idempotency_key, message.prompt_version_id, message.author) == (
        "k1",
        "v1",
        "u-1",
    )


def test_a_reference_body_parses_with_its_snapshot() -> None:
    """R20."""
    source = parse_recipe_message(_ref_body()).source
    assert isinstance(source, ReferenceInputs)
    assert source.recipe.name == "Tortilla"
    assert source.extra_specifications == ("sin gluten",)


@pytest.mark.parametrize(
    "body",
    [
        _spec_body(source={"kind": "voice"}),
        _spec_body(source={"kind": "specification", "ingredients": ["a"]}),
        _spec_body(source={"kind": "reference", "extraSpecifications": []}, referenceRecipe=None),
    ],
)
def test_malformed_recipe_bodies_are_rejected(body: dict[str, Any]) -> None:
    with pytest.raises(MalformedMessage):
        parse_recipe_message(body)


def test_a_body_without_type_is_a_week_message() -> None:
    assert message_type({}) == "week"
    assert message_type({"type": "recipe"}) == "recipe"


def _deps(queue: FakeGenerationQueue, provider: FakeAiProvider) -> Dependencies:
    return Dependencies(
        provider=provider,
        weeks=FakeWeekRepository(),
        recipes=FakeRecipeRepository(),
        records=queue,
        gate=FakeGenerationGate(),
        clock=FakeClock.at("2026-08-17T10:00:00+00:00"),
    )


def _pending(*keys: str) -> FakeGenerationQueue:
    queue = FakeGenerationQueue()
    for key in keys:
        queue.stored[key] = StoredGeneration(idempotency_key=key, status="pending")
    return queue


def test_the_handler_dispatches_a_recipe_record_and_isolates_a_bad_one() -> None:
    """R27."""
    queue = _pending("k1", "k2")
    provider = FakeAiProvider()
    event = {
        "Records": [
            {"body": json.dumps(_spec_body("k1", source={"kind": "voice"}))},
            {"body": json.dumps(_spec_body("k2"))},
        ]
    }

    handle(event, _deps(queue, provider))

    assert queue.claims == ["k2"]
    assert queue.stored["k2"].status == "completed"
    assert queue.stored["k1"].status == "pending"


def test_a_recipe_message_never_touches_the_week_repository() -> None:
    """R24: the deps' week repository stays empty and unwritten."""
    queue = _pending("k1")
    deps = _deps(queue, FakeAiProvider())

    handle({"Records": [{"body": json.dumps(_spec_body("k1"))}]}, deps)

    assert isinstance(deps.weeks, FakeWeekRepository)
    assert deps.weeks.weeks == {} and deps.weeks.versions == {}


def test_double_delivery_invokes_the_provider_once() -> None:
    """R14, R21."""
    queue = _pending("k1")
    provider = FakeAiProvider()
    record = {"body": json.dumps(_spec_body("k1"))}

    handle({"Records": [record, record]}, _deps(queue, provider))

    assert provider.calls == 1


def test_an_unknown_message_type_is_isolated() -> None:
    queue = _pending("k1")
    provider = FakeAiProvider()

    handle(
        {"Records": [{"body": json.dumps(_spec_body("k1", type="quux"))}]}, _deps(queue, provider)
    )

    assert provider.calls == 0
