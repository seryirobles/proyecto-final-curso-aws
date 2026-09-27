"""POST/GET/DELETE /v1/generations for `type: "recipe"` (specs/single_recipe_generation
R1-R6, R12, R13, R15, R17, R18, R28-R30)."""

from __future__ import annotations

import json
from typing import Any

import pytest
from _helpers import api_event, authorizer_context, make_deps, seed_user
from planner_core.application.single_recipe_generation import run_single_recipe_generation
from planner_core.domain.generation import SpecificationSource
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Recipe
from planner_core.ports.generation_queue import StoredGeneration
from planner_core.ports.recipes import LibraryRecipe
from support.fakes import FakeAiProvider, FakeGenerationGate, FakeGenerationQueue

from planner_api import serialization as ser
from planner_api.handler import handle
from planner_api.wiring import Dependencies

SLOT_TARGET = {"kind": "slot", "weekId": "2026-W34", "day": 3, "slot": 1}
SPEC_SOURCE = {"kind": "specification", "ingredients": ["lentejas"], "tools": ["olla"]}


def _body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"type": "recipe", "target": SLOT_TARGET, "source": SPEC_SOURCE}
    body.update(overrides)
    return body


def _setup() -> tuple[Dependencies, FakeGenerationQueue]:
    queue = FakeGenerationQueue()
    deps = make_deps(queue=queue)
    seed_user(deps, user_id="u-1")
    return deps, queue


def _post(deps: Dependencies, body: dict[str, Any]) -> dict[str, Any]:
    return handle(
        api_event("POST", "/v1/generations", body=body, context=authorizer_context(user_id="u-1")),
        deps,
    )


def _get(deps: Dependencies, generation_id: str) -> dict[str, Any]:
    return handle(
        api_event(
            "GET",
            "/v1/generations/{generationId}",
            path_params={"generationId": generation_id},
            context=authorizer_context(user_id="u-1"),
        ),
        deps,
    )


def _json(response: dict[str, Any]) -> dict[str, Any]:
    parsed: dict[str, Any] = json.loads(response["body"])
    return parsed


def test_specification_request_is_accepted_with_location_and_no_targets() -> None:
    """R1."""
    deps, queue = _setup()

    response = _post(deps, _body())

    payload = _json(response)
    assert response["statusCode"] == 202
    assert payload == {"generationId": payload["generationId"], "status": "pending"}
    assert response["headers"]["Location"] == f"/v1/generations/{payload['generationId']}"
    assert len(queue.recipe_submitted) == 1 and queue.submissions == []


def test_reference_request_carries_the_library_snapshot() -> None:
    """R2."""
    deps, queue = _setup()
    recipe = Recipe(
        name="Tortilla", ingredients=(), tools=(), procedure=(), category=IngredientCategory.MEAT
    )
    deps.recipes.save(LibraryRecipe(id="r-1", recipe=recipe, author="u-2"))
    source = {"kind": "reference", "recipeId": "r-1", "extraSpecifications": ["sin gluten"]}

    response = _post(deps, _body(source=source))

    assert response["statusCode"] == 202
    assert queue.recipe_submitted[0].reference_recipe == recipe
    assert queue.recipe_submitted[0].author == "u-1"


def test_reference_to_an_unknown_recipe_is_404_and_enqueues_nothing() -> None:
    """R3."""
    deps, queue = _setup()
    source = {"kind": "reference", "recipeId": "nope", "extraSpecifications": []}

    response = _post(deps, _body(source=source))

    assert response["statusCode"] == 404
    assert _json(response)["code"] == "RECIPE_NOT_FOUND"
    assert queue.recipe_submitted == []


@pytest.mark.parametrize(
    "body",
    [
        _body(type="other"),
        _body(source={"kind": "voice"}),
        _body(target={"kind": "moon"}),
        {"type": "recipe", "target": SLOT_TARGET},
        {"type": "recipe", "source": SPEC_SOURCE},
        _body(target={**SLOT_TARGET, "weekId": "nonsense"}),
        _body(target={**SLOT_TARGET, "day": 8}),
        _body(target={**SLOT_TARGET, "day": "3"}),
        _body(target={**SLOT_TARGET, "slot": 3}),
        _body(target={"kind": "slot", "weekId": "2026-W34", "day": 3}),
        _body(source={**SPEC_SOURCE, "ingredients": "lentejas"}),
        _body(source={"kind": "reference", "recipeId": "r-1"}),
        _body(source={"kind": "reference", "recipeId": 7, "extraSpecifications": []}),
        _body(attempt=1),
    ],
)
def test_malformed_bodies_are_400_and_enqueue_nothing(body: dict[str, Any]) -> None:
    """R4, R6."""
    deps, queue = _setup()

    response = _post(deps, body)

    assert response["statusCode"] == 400
    assert queue.recipe_submitted == []


def test_library_target_needs_no_week_day_or_slot() -> None:
    """R5."""
    deps, queue = _setup()

    response = _post(deps, _body(target={"kind": "library"}))

    assert response["statusCode"] == 202
    assert queue.recipe_submitted[0].request.target is None


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ({**SPEC_SOURCE, "ingredients": []}, "MISSING_INGREDIENTS"),
        ({**SPEC_SOURCE, "tools": []}, "MISSING_TOOLS"),
        ({k: v for k, v in SPEC_SOURCE.items() if k != "ingredients"}, "MISSING_INGREDIENTS"),
        ({k: v for k, v in SPEC_SOURCE.items() if k != "tools"}, "MISSING_TOOLS"),
    ],
)
def test_empty_ingredients_or_tools_are_422(source: dict[str, Any], code: str) -> None:
    """R17, R18."""
    deps, queue = _setup()

    response = _post(deps, _body(source=source))

    assert response["statusCode"] == 422
    assert _json(response)["code"] == code
    assert queue.recipe_submitted == []


def test_an_identical_in_flight_request_is_200_and_enqueues_nothing() -> None:
    """R12."""
    deps, queue = _setup()
    first = _json(_post(deps, _body()))

    second = _post(deps, _body())

    assert second["statusCode"] == 200
    assert _json(second) == {
        "generationId": first["generationId"],
        "status": "pending",
        "result": None,
    }
    assert len(queue.recipe_submitted) == 1


def test_a_terminal_record_makes_the_identical_request_a_fresh_attempt() -> None:
    """R13."""
    deps, queue = _setup()
    first = _json(_post(deps, _body()))
    queue.stored[first["generationId"]] = StoredGeneration(first["generationId"], "completed", "{}")

    second = _post(deps, _body())

    assert second["statusCode"] == 202
    assert _json(second)["generationId"] != first["generationId"]


def test_discarding_then_resubmitting_derives_the_discarded_attempt() -> None:
    """R15, R30."""
    deps, queue = _setup()
    first = _json(_post(deps, _body()))["generationId"]
    queue.stored[first] = StoredGeneration(first, "completed", "{}")
    second = _json(_post(deps, _body()))["generationId"]
    queue.stored[second] = StoredGeneration(second, "completed", "{}")

    deleted = handle(
        api_event(
            "DELETE",
            "/v1/generations/{generationId}",
            path_params={"generationId": second},
            context=authorizer_context(user_id="u-1"),
        ),
        deps,
    )
    again = _post(deps, _body())

    assert deleted["statusCode"] == 204
    assert _json(again)["generationId"] == second


def _complete(deps: Dependencies, queue: FakeGenerationQueue, key: str) -> None:
    run_single_recipe_generation(
        key,
        SpecificationSource(("lentejas",), ("olla",)),
        "v1",
        provider=FakeAiProvider(),
        queue=queue,
        gate=FakeGenerationGate(),
        encode_recipe=ser.encode_recipe,
    )


def test_get_returns_the_completed_recipe_as_an_object() -> None:
    """R28."""
    deps, queue = _setup()
    key = _json(_post(deps, _body()))["generationId"]
    _complete(deps, queue, key)

    response = _get(deps, key)

    payload = _json(response)
    assert payload["status"] == "completed"
    assert payload["result"]["name"] == "Ensalada templada de lentejas"


def test_get_returns_the_failed_error_object() -> None:
    """R28 (failure shape, contract section 3.6)."""
    deps, queue = _setup()
    key = _json(_post(deps, _body()))["generationId"]
    run_single_recipe_generation(
        key,
        SpecificationSource(("lentejas",), ("olla",)),
        "v1",
        provider=FakeAiProvider(),
        queue=queue,
        gate=FakeGenerationGate(enabled=False),
        encode_recipe=ser.encode_recipe,
    )

    payload = _json(_get(deps, key))

    assert payload["status"] == "failed"
    assert payload["result"]["error"]["code"] == "generation_unavailable"


def test_a_completed_result_is_accepted_through_the_generation_source() -> None:
    """R29."""
    deps, queue = _setup()
    key = _json(_post(deps, _body()))["generationId"]
    _complete(deps, queue, key)

    response = handle(
        api_event(
            "POST",
            "/v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates",
            path_params={"weekId": "2026-W34", "day": "3", "slot": "1"},
            body={"source": "generation", "generationId": key},
            context=authorizer_context(user_id="u-1"),
        ),
        deps,
    )

    assert response["statusCode"] == 201
    assert _json(response)["candidate"]["recipe"]["name"] == "Ensalada templada de lentejas"
