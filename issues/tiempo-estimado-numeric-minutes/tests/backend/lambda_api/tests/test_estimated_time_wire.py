"""Issue 11 (E2, E5, E8): `estimatedTime` crosses the wire as an integer
number of minutes from 0 to 6000 inclusive, or null (`G-90`).

The two rejections follow `rest_api_contract.md` section 4's own split: a value
of the wrong JSON type is **malformed** (400, as `servings` already is), while a
well-formed integer outside the range is **rejected by a domain rule** (422)
carrying its es-ES message — `G-90`'s "rejected the same way an empty required
field is". A `tiempo` already stored as free text reads back as absent instead
of raising.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any  # untyped JSON in is the wire boundary itself (conventions.md)

import pytest
from planner_core import messages
from planner_core.domain.recipe import MAX_ESTIMATED_MINUTES, InvalidEstimatedTime

from planner_api.adapters.dynamo import _meal
from planner_api.errors import build_problem_response
from planner_api.serialization import MalformedRequest, decode_recipe, encode_recipe


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


# --- E2: the write boundary, shape -----------------------------------------


def test_decode_recipe_keeps_an_integer_estimated_time() -> None:
    recipe = decode_recipe(_body(estimatedTime=45))

    assert recipe.estimated_time == 45
    assert isinstance(recipe.estimated_time, int)


def test_decode_recipe_reads_an_absent_estimated_time_as_none() -> None:
    assert decode_recipe(_body()).estimated_time is None


def test_decode_recipe_reads_a_null_estimated_time_as_none() -> None:
    assert decode_recipe(_body(estimatedTime=None)).estimated_time is None


@pytest.mark.parametrize("value", ["45 min", "hora y media", "45", "", 45.5, True, []])
def test_decode_recipe_rejects_an_estimated_time_of_the_wrong_type(value: Any) -> None:
    """`G-90` supersedes `G-85`'s free text: the unit is no longer inside the
    value, so a string is malformed, not content."""
    with pytest.raises(MalformedRequest):
        decode_recipe(_body(estimatedTime=value))


def test_encode_recipe_emits_the_integer_minute_count() -> None:
    recipe = decode_recipe(_body(estimatedTime=45))

    assert encode_recipe(recipe)["estimatedTime"] == 45


# --- E8: the write boundary, range -----------------------------------------


def test_decode_recipe_accepts_both_bounds_exactly() -> None:
    """Boundary regression: 0 and 6000 are inside the range, not outside it."""
    assert decode_recipe(_body(estimatedTime=0)).estimated_time == 0
    assert decode_recipe(_body(estimatedTime=6000)).estimated_time == 6000
    assert MAX_ESTIMATED_MINUTES == 6000


@pytest.mark.parametrize("value", [-1, 6001, 100000])
def test_decode_recipe_rejects_an_estimated_time_outside_the_range(value: int) -> None:
    with pytest.raises(InvalidEstimatedTime):
        decode_recipe(_body(estimatedTime=value))


@pytest.mark.parametrize("value", [-1, 6001])
def test_an_out_of_range_estimated_time_is_a_422_naming_the_permitted_range(value: int) -> None:
    """`G-90`: rejected the way an empty required field is — a domain
    rejection of a well-formed request (contract section 4), carrying an es-ES
    message the SPA shows verbatim (`FR-UX-03`)."""
    with pytest.raises(InvalidEstimatedTime) as raised:
        decode_recipe(_body(estimatedTime=value))
    problem = build_problem_response(raised.value)

    assert problem.status == 422
    assert problem.body["code"] == "INVALID_ESTIMATED_TIME"
    assert problem.body["detail"] == messages.INVALID_ESTIMATED_TIME
    assert "6000" in messages.INVALID_ESTIMATED_TIME


# --- E5: reading data written before G-90 ----------------------------------


def test_reading_a_numeric_tiempo_gives_the_minute_count() -> None:
    assert _meal.read_estimated_time({"tiempo": Decimal(45)}) == 45
    assert _meal.read_estimated_time({"tiempo": 45}) == 45


def test_reading_a_legacy_free_text_tiempo_reads_as_absent_and_never_raises() -> None:
    """`G-90` backward compatibility: the dev environment holds rows written
    under `G-85`; a read of one must not raise."""
    assert _meal.read_estimated_time({"tiempo": "45 min"}) is None
    assert _meal.read_estimated_time({"tiempo": "hora y media"}) is None


def test_reading_an_absent_tiempo_is_still_none() -> None:
    assert _meal.read_estimated_time({}) is None
    assert _meal.read_estimated_time({"tiempo": None}) is None
