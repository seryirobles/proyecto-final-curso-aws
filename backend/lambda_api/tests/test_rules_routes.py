"""Rules routes: per-rule PUT/DELETE (R31) and the 422 UNSATISFIABLE_RULE_SET
mapping with its conflicts detail (R21)."""

from __future__ import annotations

import json

from _helpers import api_event, authorizer_context, make_deps, seed_user
from planner_core.domain.calendar import MealSlot
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Recipe
from planner_core.domain.rules import (
    CategoryCountRule,
    DisabledDay,
    PinRule,
    available_days_for_pin,
    available_days_to_disable,
    max_selectable_count,
)
from planner_core.ports.recipes import LibraryRecipe

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


def test_put_rule_echo_for_a_pin_has_no_recipename_key() -> None:
    """serialization.py's encode_rule omits recipeName when no read-time
    resolution happened (PUT echo, docs/data_model.md section 6) - a surviving
    mutant on that guard leaks `"recipeName": null` into this response."""
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    recipe = Recipe(
        name="Lentejas", ingredients=(), tools=(), procedure=(), category=IngredientCategory.LEGUME
    )
    deps.recipes.save(LibraryRecipe(id="r1", recipe=recipe, author="u-1"))
    event = api_event(
        "PUT",
        "/v1/rules/{ruleId}",
        path_params={"ruleId": "pin#1#1"},
        body={"type": "pin", "day": 1, "slot": 1, "recipeId": "r1"},
        context=authorizer_context(user_id="u-1"),
    )

    response = handle(event, deps)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body == {"type": "pin", "day": 1, "slot": 1, "recipeId": "r1"}
    assert "recipeName" not in body


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


def test_get_rules_resolves_a_pin_rules_recipe_name_from_the_library() -> None:
    """docs/rest_api_contract.md 'Rules': pin rules carry recipeName, resolved
    at read time from the library, never stored (data_model.md section 6)."""
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    recipe = Recipe(
        name="Lentejas", ingredients=(), tools=(), procedure=(), category=IngredientCategory.LEGUME
    )
    deps.recipes.save(LibraryRecipe(id="r1", recipe=recipe, author="u-1"))
    deps.rules.save_rule(PinRule(day=1, slot=MealSlot.LUNCH, recipe_id="r1"))
    event = api_event("GET", "/v1/rules", context=authorizer_context(user_id="u-1"))

    response = handle(event, deps)

    assert response["statusCode"] == 200
    pins = [r for r in json.loads(response["body"])["rules"] if r["type"] == "pin"]
    assert pins == [
        {"type": "pin", "day": 1, "slot": 1, "recipeId": "r1", "recipeName": "Lentejas"}
    ]


def test_get_rules_available_options_matches_the_pure_functions_on_the_same_rule_set() -> None:
    """R2-R4: availableOptions is read verbatim off rules.py's own functions,
    applied to the same RuleSet the rules array was built from."""
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    deps.rules.save_rule(CategoryCountRule(category=IngredientCategory.MEAT, count=5))
    deps.rules.save_rule(CategoryCountRule(category=IngredientCategory.FISH, count=3))
    deps.rules.save_rule(DisabledDay(day=7))
    deps.rules.save_rule(PinRule(day=1, slot=MealSlot.LUNCH, recipe_id="r1"))
    event = api_event("GET", "/v1/rules", context=authorizer_context(user_id="u-1"))

    response = handle(event, deps)

    assert response["statusCode"] == 200
    available_options = json.loads(response["body"])["availableOptions"]
    rule_set = deps.rules.get()
    assert available_options == {
        "maxCountByCategory": {
            category.value: max_selectable_count(rule_set, category)
            for category in IngredientCategory
        },
        "daysAvailableForPin": list(available_days_for_pin(rule_set)),
        "daysAvailableToDisable": list(available_days_to_disable(rule_set)),
    }
    # Sanity: the scenario actually exercises non-trivial values, not all-default.
    assert available_options["maxCountByCategory"]["meat"] not in (0, None)
    assert available_options["daysAvailableForPin"] == [1, 2, 3, 4, 5, 6]
    assert available_options["daysAvailableToDisable"] == [2, 3, 4, 5, 6]


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


def test_unsatisfiable_conflicts_array_has_no_recipename_for_a_conflicting_pin() -> None:
    """errors.py's conflicts array reuses encode_rule with no name resolved
    (rule_editing.py's pin_clash branch) - must not leak `"recipeName": null`."""
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    recipe = Recipe(
        name="Lentejas", ingredients=(), tools=(), procedure=(), category=IngredientCategory.LEGUME
    )
    deps.recipes.save(LibraryRecipe(id="r1", recipe=recipe, author="u-1"))
    deps.rules.save_rule(PinRule(day=1, slot=MealSlot.LUNCH, recipe_id="r1"))
    event = api_event(
        "PUT",
        "/v1/rules/{ruleId}",
        path_params={"ruleId": "day#1"},
        body={"type": "disabledDay", "day": 1},
        context=authorizer_context(user_id="u-1"),
    )

    response = handle(event, deps)

    assert response["statusCode"] == 422
    parsed = json.loads(response["body"])
    assert parsed["details"]["conflicts"] == [
        {"type": "pin", "day": 1, "slot": 1, "recipeId": "r1"}
    ]
