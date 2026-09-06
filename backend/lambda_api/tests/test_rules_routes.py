"""Rules routes: per-rule PUT/DELETE (R31) and the 422 UNSATISFIABLE_RULE_SET
mapping with its conflicts detail (R21)."""

from __future__ import annotations

import json

from _helpers import api_event, authorizer_context, make_deps, seed_user
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.rules import DisabledDay

from planner_api.handler import handle


def test_put_rule_maps_to_the_single_rule_write_operation() -> None:
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    event = api_event(
        "PUT",
        "/v1/rules/{ruleId}",
        path_params={"ruleId": "cat#meat"},
        body={"type": "categoryCount", "category": "meat", "count": 2},
        context=authorizer_context(user_id="u-1"),
    )

    response = handle(event, deps)

    assert response["statusCode"] == 200
    stored = deps.rules.get()
    assert stored.category_counts[0].category is IngredientCategory.MEAT
    assert stored.category_counts[0].count == 2


def test_a_body_that_does_not_match_the_path_ruleid_is_rejected() -> None:
    """T9 - the {ruleId} path segment is authoritative; a body describing a
    different rule must not silently overwrite whatever the path names."""
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    event = api_event(
        "PUT",
        "/v1/rules/{ruleId}",
        path_params={"ruleId": "cat#meat"},
        body={"type": "categoryCount", "category": "fish", "count": 2},
        context=authorizer_context(user_id="u-1"),
    )

    response = handle(event, deps)

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["code"] == "MALFORMED_REQUEST"
    assert deps.rules.get().category_counts == ()


def test_delete_rule_maps_to_the_single_rule_delete_operation() -> None:
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    deps.rules.save_rule(DisabledDay(day=6))
    event = api_event(
        "DELETE",
        "/v1/rules/{ruleId}",
        path_params={"ruleId": "day#6"},
        context=authorizer_context(user_id="u-1"),
    )

    response = handle(event, deps)

    assert response["statusCode"] == 204
    assert deps.rules.get().disabled_days == ()


def test_an_unsatisfiable_rule_change_is_rejected_422_with_conflicts() -> None:
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    # 14 total slots/week; disabling every day but one leaves 2, then a count
    # of 3 for one category cannot fit (FR-RULE-07).
    for day in range(1, 7):
        deps.rules.save_rule(DisabledDay(day=day))
    event = api_event(
        "PUT",
        "/v1/rules/{ruleId}",
        path_params={"ruleId": "cat#meat"},
        body={"type": "categoryCount", "category": "meat", "count": 3},
        context=authorizer_context(user_id="u-1"),
    )

    response = handle(event, deps)

    assert response["statusCode"] == 422
    parsed = json.loads(response["body"])
    assert parsed["code"] == "UNSATISFIABLE_RULE_SET"
    assert "conflicts" in parsed["details"]
