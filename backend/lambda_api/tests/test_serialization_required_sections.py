"""The wire boundary rejects a recipe whose ingredients, tools or procedure
list is empty (G-89, FR-LIB-03).

Issue 8 (recipe-saved-without-required-sections): E1, E2, E3, E7.
"""

from __future__ import annotations

from typing import Any

import pytest
from planner_core import messages
from planner_core.domain.errors import PlannerError

from planner_api.errors import build_problem_response
from planner_api.serialization import decode_recipe

SECTIONS = ["ingredients", "tools", "procedure"]


def _payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": "Lentejas con chorizo",
        "category": "legume",
        "ingredients": [{"name": "lentejas", "quantity": 500, "unit": "g"}],
        "tools": ["olla"],
        "procedure": ["Cocer las lentejas."],
    }
    payload.update(overrides)
    return payload


def _es_es_messages() -> set[str]:
    return {value for value in vars(messages).values() if isinstance(value, str)}


@pytest.mark.parametrize("section", SECTIONS)
def test_decode_recipe_rejects_an_empty_section(section: str) -> None:
    """E1/E2/E3: the entry point every recipe write takes - library
    create/update, candidate create/update and AI-preview accept."""
    with pytest.raises(PlannerError):
        decode_recipe(_payload(**{section: []}))


@pytest.mark.parametrize("section", SECTIONS)
def test_decode_recipe_rejects_an_absent_section(section: str) -> None:
    """E1/E2/E3: an omitted list is today's empty default, so it is the same rule."""
    payload = _payload()
    del payload[section]

    with pytest.raises(PlannerError):
        decode_recipe(payload)


@pytest.mark.parametrize("section", SECTIONS)
def test_an_empty_section_reaches_the_client_as_422_with_an_es_es_message(section: str) -> None:
    """E1/E2/E3: well-formed but domain-rejected (rest_api_contract.md section 4),
    with a detail taken from planner_core.messages (FR-UX-03)."""
    with pytest.raises(PlannerError) as excinfo:
        decode_recipe(_payload(**{section: []}))

    problem = build_problem_response(excinfo.value)

    assert problem.status == 422
    assert problem.body["detail"] in _es_es_messages()
    assert problem.body["detail"] != messages.INTERNAL_ERROR


def test_a_recipe_with_one_item_in_each_section_still_decodes() -> None:
    """E7: the rule is a minimum of one, not a minimum of more than one."""
    recipe = decode_recipe(_payload())

    assert len(recipe.ingredients) == 1
    assert recipe.tools == ("olla",)
    assert recipe.procedure == ("Cocer las lentejas.",)
