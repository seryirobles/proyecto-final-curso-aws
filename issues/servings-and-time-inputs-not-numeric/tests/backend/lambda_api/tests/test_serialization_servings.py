"""Issue 4 (E6, E7): `servings` crosses the wire as an integer or null
(rest_api_contract.md section 3.1); anything else is a 400 (section 4), never a
value persisted into `numeroComensales`. `estimatedTime` stays free text
(FR-LIB-03, G-85)."""

from __future__ import annotations

from typing import Any  # untyped JSON in is the wire boundary itself (conventions.md)

import pytest

from planner_api.serialization import MalformedRequest, decode_recipe


def _body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "name": "Lentejas al curry",
        "category": "legume",
        "ingredients": [],
        "tools": [],
        "procedure": [],
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


def test_decode_recipe_keeps_estimated_time_as_the_clients_free_text() -> None:
    """G-85: the unit lives inside the string; nothing parses or normalises it."""
    assert decode_recipe(_body(estimatedTime="45 min")).estimated_time == "45 min"
    assert decode_recipe(_body(estimatedTime="hora y media")).estimated_time == "hora y media"


def test_decode_recipe_reads_an_absent_estimated_time_as_none() -> None:
    assert decode_recipe(_body()).estimated_time is None
