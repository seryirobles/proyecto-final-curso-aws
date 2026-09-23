"""The wire boundary rejects a non-positive servings count as 422.

Issue 7 (negative-ingredient-quantity), servings extension: E7. A servings of
the wrong JSON type stays 400 (test_serialization_servings.py, issue 4).
"""

from __future__ import annotations

from typing import Any

import pytest
from planner_core import messages
from planner_core.domain.errors import PlannerError

from planner_api.errors import build_problem_response
from planner_api.serialization import decode_recipe


def _recipe_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": "Lentejas con chorizo",
        "category": "legume",
        "ingredients": [{"name": "lentejas", "quantity": 500, "unit": "g"}],
        "tools": ["olla"],
        "procedure": ["Cocer las lentejas."],
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize("servings", [-4, -1, 0])
def test_decode_recipe_rejects_a_non_positive_servings(servings: int) -> None:
    """E7: the entry point of every manual write and of the AI-preview accept."""
    with pytest.raises(PlannerError):
        decode_recipe(_recipe_payload(servings=servings))


def test_decode_recipe_accepts_one_serving_exactly() -> None:
    """Boundary regression: 1 is the smallest valid count, not the first invalid one."""
    assert decode_recipe(_recipe_payload(servings=1)).servings == 1


def test_decode_recipe_still_reads_an_absent_servings_as_none() -> None:
    """Regression: servings stays optional (FR-LIB-03, G-85)."""
    assert decode_recipe(_recipe_payload()).servings is None


def test_the_servings_rejection_reaches_the_client_as_422_with_an_es_es_message() -> None:
    """E7: well-formed but domain-rejected (rest_api_contract.md section 4), with a
    detail taken from planner_core.messages (FR-UX-03)."""
    with pytest.raises(PlannerError) as excinfo:
        decode_recipe(_recipe_payload(servings=0))

    problem = build_problem_response(excinfo.value)
    known_messages = {value for value in vars(messages).values() if isinstance(value, str)}

    assert problem.status == 422
    assert problem.body["detail"] in known_messages
    assert problem.body["detail"] != messages.INTERNAL_ERROR
