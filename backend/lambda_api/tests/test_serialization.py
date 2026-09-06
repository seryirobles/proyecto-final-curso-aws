"""serialization.py: JSON parsing, camelCase encoding, path-param parsing
(R18, R38, R39)."""

from __future__ import annotations

import pytest
from planner_core.domain.calendar import IsoWeek, MealSlot
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Ingredient, Recipe
from planner_core.domain.units import Unit

from planner_api.serialization import (
    MalformedRequest,
    decode_recipe,
    encode_recipe,
    parse_day,
    parse_json_body,
    parse_slot,
    parse_week_id,
    reject_keys,
)


def test_absent_body_decodes_as_an_empty_dict() -> None:
    assert parse_json_body(None) == {}


def test_unparseable_json_raises_malformed_request() -> None:
    with pytest.raises(MalformedRequest):
        parse_json_body("{not json")


def test_a_json_array_body_raises_malformed_request() -> None:
    with pytest.raises(MalformedRequest):
        parse_json_body("[1, 2]")


def test_client_supplied_id_is_rejected() -> None:
    with pytest.raises(MalformedRequest):
        reject_keys({"id": "client-chosen"}, "id", "author")


def test_client_supplied_author_is_rejected() -> None:
    with pytest.raises(MalformedRequest):
        reject_keys({"author": "someone"}, "id", "author")


def test_a_body_without_forbidden_keys_passes() -> None:
    reject_keys({"name": "Lentejas"}, "id", "author")  # no raise


def test_recipe_round_trips_through_camel_case_keys() -> None:
    recipe = Recipe(
        name="Lentejas al curry",
        ingredients=(Ingredient(name="lentejas", quantity=300, unit=Unit.GRAM),),
        tools=("olla",),
        procedure=("Sofreir la cebolla.",),
        category=IngredientCategory.LEGUME,
        servings=4,
        estimated_time="45 min",
    )

    wire = encode_recipe(recipe)
    assert wire == {
        "name": "Lentejas al curry",
        "category": "legume",
        "servings": 4,
        "estimatedTime": "45 min",
        "ingredients": [{"name": "lentejas", "quantity": 300, "unit": "g"}],
        "tools": ["olla"],
        "procedure": ["Sofreir la cebolla."],
    }
    assert decode_recipe(wire) == recipe


def test_a_recipe_body_carrying_an_id_is_rejected() -> None:
    with pytest.raises(MalformedRequest):
        decode_recipe({"id": "x", "name": "n", "category": "meat"})


def test_valid_week_id_parses_to_an_iso_week() -> None:
    assert parse_week_id("2026-W33") == IsoWeek(2026, 33)


@pytest.mark.parametrize("value", ["not-a-week", "2026-W99", "2026", ""])
def test_malformed_week_id_raises_malformed_request(value: str) -> None:
    with pytest.raises(MalformedRequest):
        parse_week_id(value)


def test_valid_day_parses_to_an_int() -> None:
    assert parse_day("3") == 3


@pytest.mark.parametrize("value", ["0", "8", "abc", ""])
def test_out_of_range_or_unparseable_day_raises_malformed_request(value: str) -> None:
    with pytest.raises(MalformedRequest):
        parse_day(value)


def test_valid_slot_parses_to_a_meal_slot() -> None:
    assert parse_slot("2") == MealSlot.DINNER


@pytest.mark.parametrize("value", ["0", "3", "abc"])
def test_invalid_slot_raises_malformed_request(value: str) -> None:
    with pytest.raises(MalformedRequest):
        parse_slot(value)
