"""Issue 4 (E6, E7): `servings` crosses the wire as an integer or null
(rest_api_contract.md section 3.1); anything else is a 400 (section 4), never a
value persisted into `numeroComensales`. `estimatedTime`'s own G-85 free-text
case moved to test_estimated_time_wire.py - G-90 supersedes that shape for
this field (issue tiempo-estimado-numeric-minutes)."""

from __future__ import annotations

from typing import Any  # untyped JSON in is the wire boundary itself (conventions.md)

import pytest

from planner_api.serialization import MalformedRequest, decode_recipe


def _body(**overrides: Any) -> dict[str, Any]:
    # Non-empty sections (issue recipe-saved-without-required-sections, G-89):
    # this file is about servings, not section cardinality.
    body: dict[str, Any] = {
        "name": "Lentejas al curry",
        "category": "legume",
        "ingredients": [{"name": "lentejas", "quantity": 500, "unit": "g"}],
        "tools": ["olla"],
        "procedure": ["Cocer las lentejas."],
    }
    body.update(overrides)
    return body


def test_decode_recipe_keeps_an_integer_servings() -> None:
    recipe = decode_recipe(_body(servings=4))

    assert recipe.servings == 4
    assert isinstance(recipe.servings, int)


def test_decode_recipe_reads_an_absent_servings_as_none() -> None:
    assert decode_recipe(_body()).servings is None


def test_decode_recipe_reads_a_null_servings_as_none() -> None:
    assert decode_recipe(_body(servings=None)).servings is None


def test_decode_recipe_rejects_an_empty_string_servings() -> None:
    """The blank-field payload the SPA used to send: it stored an unreadable
    `numeroComensales` instead of failing the request."""
    with pytest.raises(MalformedRequest):
        decode_recipe(_body(servings=""))


@pytest.mark.parametrize("value", ["4", "cuatro", 4.5, True, []])
def test_decode_recipe_rejects_a_servings_that_is_not_an_integer(value: Any) -> None:
    with pytest.raises(MalformedRequest):
        decode_recipe(_body(servings=value))


def test_decode_recipe_reads_an_absent_estimated_time_as_none() -> None:
    assert decode_recipe(_body()).estimated_time is None
