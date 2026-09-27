"""planner_ai recipe wire encoder/decoder (specs/single_recipe_generation R20, R23)."""

from __future__ import annotations

import pytest
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Ingredient, Recipe
from planner_core.domain.units import Unit

from planner_ai.serialization import decode_recipe, encode_recipe

RECIPE = Recipe(
    name="Lentejas",
    ingredients=(Ingredient(name="lentejas", quantity=300.5, unit=Unit.GRAM),),
    tools=("olla",),
    procedure=("Cocer.",),
    category=IngredientCategory.LEGUME,
    servings=4,
    estimated_time=45,
)


def test_encode_produces_the_wire_shape() -> None:
    assert encode_recipe(RECIPE) == {
        "name": "Lentejas",
        "category": "legume",
        "servings": 4,
        "estimatedTime": 45,
        "ingredients": [{"name": "lentejas", "quantity": 300.5, "unit": "g"}],
        "tools": ["olla"],
        "procedure": ["Cocer."],
    }


def test_decode_round_trips_encode() -> None:
    assert decode_recipe(encode_recipe(RECIPE)) == RECIPE


def test_decode_defaults_absent_servings_and_time_to_none() -> None:
    payload = encode_recipe(RECIPE)
    del payload["servings"], payload["estimatedTime"]

    decoded = decode_recipe(payload)

    assert decoded.servings is None and decoded.estimated_time is None


def test_decode_rejects_a_payload_missing_a_required_key() -> None:
    payload = encode_recipe(RECIPE)
    del payload["name"]

    with pytest.raises(KeyError):
        decode_recipe(payload)
