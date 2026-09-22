"""The wire boundary rejects a non-positive ingredient quantity as 422.

Issue 7 (negative-ingredient-quantity): E1.
"""

from __future__ import annotations

from typing import Any

import pytest
from planner_core import messages
from planner_core.domain.errors import PlannerError

from planner_api.errors import build_problem_response
from planner_api.serialization import decode_ingredient, decode_recipe


def _recipe_payload(quantity: float) -> dict[str, Any]:
    return {
        "name": "Lentejas con chorizo",
        "category": "legume",
        "ingredients": [{"name": "lentejas", "quantity": quantity, "unit": "g"}],
        "tools": ["olla"],
        "procedure": ["Cocer las lentejas."],
    }


@pytest.mark.parametrize("quantity", [-500, -0.5, 0])
def test_decode_recipe_rejects_a_non_positive_ingredient_quantity(quantity: float) -> None:
    """E1: the entry point every manual recipe write takes (routing.py 356/407/523)."""
    with pytest.raises(PlannerError):
        decode_recipe(_recipe_payload(quantity))


def test_decode_recipe_accepts_a_positive_ingredient_quantity() -> None:
    recipe = decode_recipe(_recipe_payload(500))

    assert recipe.ingredients[0].quantity == 500.0


def test_the_rejection_reaches_the_client_as_422_with_an_es_es_message() -> None:
    """E1: well-formed but domain-rejected (rest_api_contract.md section 4), with a
    detail taken from planner_core.messages (FR-UX-03), never a composed string."""
    with pytest.raises(PlannerError) as excinfo:
        decode_ingredient({"name": "lentejas", "quantity": -500, "unit": "g"})

    problem = build_problem_response(excinfo.value)
    known_messages = {value for value in vars(messages).values() if isinstance(value, str)}

    assert problem.status == 422
    assert problem.body["detail"] in known_messages
    assert problem.body["detail"] != messages.INTERNAL_ERROR
