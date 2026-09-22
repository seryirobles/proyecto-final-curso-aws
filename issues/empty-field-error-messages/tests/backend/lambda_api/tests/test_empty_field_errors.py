"""An empty required field names the field, instead of rejecting its value
(issue 5: E1-E9). Wire-level: decode + build_problem_response, the pair the
handler runs for every authoring request. `servings`/`estimatedTime` are not
required fields (G-85) and belong to issue 4."""

from __future__ import annotations

from typing import Any

import pytest
from planner_core.domain.errors import PlannerError

from planner_api.errors import build_problem_response
from planner_api.serialization import decode_recipe, decode_shopping_item

EMPTY_FIELD = "EMPTY_FIELD"

EMPTY_NAME = "El campo Nombre no puede estar vacío."
EMPTY_CATEGORY = "El campo Categoría no puede estar vacío."
EMPTY_INGREDIENT_NAME = "El campo Nombre del ingrediente no puede estar vacío."
EMPTY_QUANTITY = "El campo Cantidad no puede estar vacío."
EMPTY_UNIT = "El campo Unidad no puede estar vacío."
EMPTY_TOOL = "El campo Utensilio no puede estar vacío."
EMPTY_PROCEDURE_STEP = "El campo Paso de la elaboración no puede estar vacío."


def valid_recipe() -> dict[str, Any]:
    return {
        "name": "Lentejas al curry",
        "category": "legume",
        "servings": 4,
        "estimatedTime": "45 min",
        "ingredients": [{"name": "lentejas", "quantity": 300, "unit": "g"}],
        "tools": ["olla"],
        "procedure": ["Sofreir la cebolla."],
    }


def valid_shopping_item() -> dict[str, Any]:
    return {"name": "lentejas", "quantity": 300, "unit": "g"}


def assert_empty_field(body: dict[str, Any], detail: str) -> None:
    assert body["code"] == EMPTY_FIELD
    assert body["detail"] == detail


def recipe_problem(payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    with pytest.raises(PlannerError) as excinfo:
        decode_recipe(payload)
    problem = build_problem_response(excinfo.value)
    return problem.status, problem.body


def shopping_problem(payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    with pytest.raises(PlannerError) as excinfo:
        decode_shopping_item(payload, item_id="s-1")
    problem = build_problem_response(excinfo.value)
    return problem.status, problem.body


# --- E1: the reported case -------------------------------------------------


def test_an_unselected_unit_reports_the_empty_unit_message() -> None:
    """E1. Today the detail is UNKNOWN_UNIT's: the unit is not permitted."""
    payload = valid_recipe()
    payload["ingredients"] = [{"name": "lentejas", "quantity": 300, "unit": ""}]

    status, body = recipe_problem(payload)

    assert status == 422
    assert_empty_field(body, EMPTY_UNIT)


# --- E2-E7: the same rule for every other required recipe field ------------


def test_an_empty_recipe_name_reports_the_empty_name_message() -> None:
    """E2."""
    payload = valid_recipe()
    payload["name"] = ""

    status, body = recipe_problem(payload)

    assert status == 422
    assert_empty_field(body, EMPTY_NAME)


def test_a_whitespace_only_recipe_name_is_empty_too() -> None:
    """E2."""
    payload = valid_recipe()
    payload["name"] = "   "

    status, body = recipe_problem(payload)

    assert status == 422
    assert_empty_field(body, EMPTY_NAME)


def test_an_unselected_category_reports_the_empty_category_message() -> None:
    """E3."""
    payload = valid_recipe()
    payload["category"] = ""

    status, body = recipe_problem(payload)

    assert status == 422
    assert_empty_field(body, EMPTY_CATEGORY)


def test_an_empty_ingredient_name_reports_the_empty_ingredient_name_message() -> None:
    """E4."""
    payload = valid_recipe()
    payload["ingredients"] = [{"name": "", "quantity": 300, "unit": "g"}]

    status, body = recipe_problem(payload)

    assert status == 422
    assert_empty_field(body, EMPTY_INGREDIENT_NAME)


@pytest.mark.parametrize("blank", [None, "", "  "])
def test_a_blank_ingredient_quantity_reports_the_empty_quantity_message(blank: Any) -> None:
    """E5. A partially filled form sends the blank through, never a silent 0."""
    payload = valid_recipe()
    payload["ingredients"] = [{"name": "lentejas", "quantity": blank, "unit": "g"}]

    status, body = recipe_problem(payload)

    assert status == 422
    assert_empty_field(body, EMPTY_QUANTITY)


def test_a_blank_tool_entry_reports_the_empty_tool_message() -> None:
    """E6."""
    payload = valid_recipe()
    payload["tools"] = ["olla", ""]

    status, body = recipe_problem(payload)

    assert status == 422
    assert_empty_field(body, EMPTY_TOOL)


def test_a_blank_procedure_step_reports_the_empty_step_message() -> None:
    """E7."""
    payload = valid_recipe()
    payload["procedure"] = ["Sofreir la cebolla.", "   "]

    status, body = recipe_problem(payload)

    assert status == 422
    assert_empty_field(body, EMPTY_PROCEDURE_STEP)


# --- E8: the shopping item shares the decoders and the unit vocabulary -----


def test_an_unselected_unit_on_a_shopping_item_reports_the_empty_unit_message() -> None:
    """E8."""
    payload = valid_shopping_item()
    payload["unit"] = ""

    status, body = shopping_problem(payload)

    assert status == 422
    assert_empty_field(body, EMPTY_UNIT)


def test_an_empty_shopping_item_name_reports_the_empty_name_message() -> None:
    """E8."""
    payload = valid_shopping_item()
    payload["name"] = ""

    status, body = shopping_problem(payload)

    assert status == 422
    assert_empty_field(body, EMPTY_NAME)


# --- E9: nothing that is filled in, or deliberately optional, changes ------


def test_a_fully_filled_recipe_still_decodes() -> None:
    """E9."""
    recipe = decode_recipe(valid_recipe())

    assert recipe.name == "Lentejas al curry"
    assert recipe.ingredients[0].unit.value == "g"


def test_an_absent_estimated_time_is_still_accepted() -> None:
    """E9: freeform and purely informational, so never a required field (G-85)."""
    payload = valid_recipe()
    del payload["estimatedTime"]

    assert decode_recipe(payload).estimated_time is None


def test_a_filled_in_unit_outside_the_list_still_reports_unknown_unit() -> None:
    """E9: FR-LIB-05's rejection survives; only the empty case is re-routed."""
    payload = valid_recipe()
    payload["ingredients"] = [{"name": "lentejas", "quantity": 300, "unit": "kg"}]

    status, body = recipe_problem(payload)

    assert status == 422
    assert body["code"] == "UNKNOWN_UNIT"


def test_a_filled_in_category_outside_the_list_still_reports_unknown_category() -> None:
    """E9."""
    payload = valid_recipe()
    payload["category"] = "pasta"

    status, body = recipe_problem(payload)

    assert status == 422
    assert body["code"] == "UNKNOWN_INGREDIENT_CATEGORY"


def test_a_filled_in_shopping_item_still_decodes() -> None:
    """E9."""
    item = decode_shopping_item(valid_shopping_item(), item_id="s-1")

    assert item.name == "lentejas"
    assert item.unit.value == "g"
