"""Issue rule-creation-400-invalid-request: a ruleId holds `#`, so it reaches
the api Lambda percent-encoded (`cat%23meat`) and must be decoded before the
T9 path/body check and before delete_rule."""

from __future__ import annotations

import json

import pytest
from _helpers import api_event, authorizer_context, make_deps, seed_user
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Recipe
from planner_core.domain.rules import CategoryCountRule, DisabledDay
from planner_core.ports.recipes import LibraryRecipe

from planner_api import local_server
from planner_api.handler import handle
from planner_api.wiring import Dependencies


def _session(deps: Dependencies) -> dict[str, str]:
    token = seed_user(deps, user_id="u-1")
    return {"Cookie": f"session={token}"}


def _seed_recipe(deps: Dependencies) -> None:
    recipe = Recipe(
        name="Lentejas", ingredients=(), tools=(), procedure=(), category=IngredientCategory.LEGUME
    )
    deps.recipes.save(LibraryRecipe(id="r1", recipe=recipe, author="u-1"))


@pytest.mark.parametrize(
    ("target", "body"),
    [
        ("/v1/rules/cat%23meat", {"type": "categoryCount", "category": "meat", "count": 2}),
        ("/v1/rules/pin%231%231", {"type": "pin", "day": 1, "slot": 1, "recipeId": "r1"}),
        ("/v1/rules/day%236", {"type": "disabledDay", "day": 6}),
    ],
)
def test_put_with_a_percent_encoded_rule_id_saves_the_rule(
    target: str, body: dict[str, object]
) -> None:
    deps = make_deps()
    headers = _session(deps)
    _seed_recipe(deps)

    response = local_server.handle_request(
        "PUT", target, headers, json.dumps(body).encode("utf-8"), deps=deps
    )

    assert response["statusCode"] == 200
    assert json.loads(response["body"])["type"] == body["type"]


def test_put_saves_a_category_count_rule_under_its_decoded_id() -> None:
    deps = make_deps()
    headers = _session(deps)
    body = json.dumps({"type": "categoryCount", "category": "meat", "count": 2}).encode("utf-8")

    local_server.handle_request("PUT", "/v1/rules/cat%23meat", headers, body, deps=deps)

    assert deps.rules.get().category_counts == (
        CategoryCountRule(category=IngredientCategory.MEAT, count=2),
    )


def test_delete_with_a_percent_encoded_rule_id_removes_the_rule() -> None:
    deps = make_deps()
    headers = _session(deps)
    deps.rules.save_rule(DisabledDay(day=6))

    response = local_server.handle_request("DELETE", "/v1/rules/day%236", headers, None, deps=deps)

    assert response["statusCode"] == 204
    assert deps.rules.get().disabled_days == ()


def test_the_handler_accepts_an_undecoded_rule_id_path_parameter() -> None:
    # API Gateway's decoding of pathParameters is not relied on (analysis.md).
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    event = api_event(
        "PUT",
        "/v1/rules/{ruleId}",
        path_params={"ruleId": "cat%23meat"},
        body={"type": "categoryCount", "category": "meat", "count": 2},
        context=authorizer_context(user_id="u-1"),
    )

    response = handle(event, deps)

    assert response["statusCode"] == 200


def test_a_rule_id_truncated_at_the_hash_is_still_rejected() -> None:
    # Regression guard: the path segment stays authoritative (T9).
    deps = make_deps()
    headers = _session(deps)
    body = json.dumps({"type": "categoryCount", "category": "meat", "count": 2}).encode("utf-8")

    response = local_server.handle_request("PUT", "/v1/rules/cat", headers, body, deps=deps)

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["code"] == "MALFORMED_REQUEST"
    assert deps.rules.get().category_counts == ()
