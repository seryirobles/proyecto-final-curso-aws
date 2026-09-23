"""ETag marker emission on the four pollable resources and their mutations
(R28, R29)."""

from __future__ import annotations

from _helpers import api_event, authorizer_context, make_deps, seed_user
from planner_core.domain.calendar import IsoWeek
from planner_core.domain.role import Role
from planner_core.domain.rules import DisabledDay
from planner_core.domain.shopping import ShoppingItem
from planner_core.domain.units import Unit

from planner_api.handler import handle

_WEEK = IsoWeek(2026, 33)


def test_get_week_carries_the_weeks_marker_as_a_strong_etag() -> None:
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    deps.weeks.save_week(_WEEK, {})
    event = api_event(
        "GET",
        "/v1/weeks/{weekId}",
        path_params={"weekId": "2026-W33"},
        context=authorizer_context(user_id="u-1"),
    )

    response = handle(event, deps)

    assert response["statusCode"] == 200
    assert response["headers"]["ETag"] == f'"{deps.weeks.current_version(_WEEK)}"'


def test_adding_a_library_recipe_returns_the_writes_marker_as_the_etag() -> None:
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    event = api_event(
        "POST",
        "/v1/library/recipes",
        body={
            "source": "manual",
            "recipe": {
                "name": "Tortilla",
                "category": "eggs",
                "ingredients": [{"name": "huevo", "quantity": 3, "unit": "unit"}],
                # Non-empty sections (issue recipe-saved-without-required-sections, G-89).
                "tools": ["sartén"],
                "procedure": ["Batir los huevos y cuajar."],
            },
        },
        context=authorizer_context(user_id="u-1"),
    )

    response = handle(event, deps)

    assert response["statusCode"] == 201
    assert response["headers"]["ETag"] == f'"{deps.recipes.current_version()}"'


def test_deleting_a_rule_returns_the_writes_marker_as_the_etag() -> None:
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
    assert response["headers"]["ETag"] == f'"{deps.rules.current_version()}"'


def test_shopping_list_read_carries_its_own_marker() -> None:
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    deps.shopping.save_item(ShoppingItem(id="s-1", name="arroz", quantity=500, unit=Unit.GRAM))
    event = api_event(
        "GET", "/v1/shopping-list", context=authorizer_context(user_id="u-1", role=Role.USER)
    )

    response = handle(event, deps)

    assert response["statusCode"] == 200
    assert response["headers"]["ETag"] == f'"{deps.shopping.current_version()}"'
