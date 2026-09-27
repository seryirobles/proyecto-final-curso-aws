"""The planner_ai recipe encoder is a copy of planner_api's; drift fails here
(specs/single_recipe_generation R23, R29)."""

from __future__ import annotations

import pytest
from planner_ai import serialization as ai_ser
from planner_api import serialization as api_ser
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Ingredient, Recipe
from planner_core.domain.units import Unit

RECIPES = [
    Recipe(
        name="Lentejas",
        ingredients=(Ingredient(name="lentejas", quantity=300.5, unit=Unit.GRAM),),
        tools=("olla", "cazo"),
        procedure=("Cocer.", "Servir."),
        category=IngredientCategory.LEGUME,
        servings=4,
        estimated_time=45,
    ),
    Recipe(
        name="Ensalada",
        ingredients=(),
        tools=(),
        procedure=(),
        category=IngredientCategory.VEGETABLE,
    ),
]


@pytest.mark.parametrize("recipe", RECIPES)
def test_the_ai_encoder_equals_the_api_encoder(recipe: Recipe) -> None:
    assert ai_ser.encode_recipe(recipe) == api_ser.encode_recipe(recipe)


def test_a_wire_recipe_the_worker_writes_is_accepted_by_the_api_decoder() -> None:
    recipe = RECIPES[0]

    assert api_ser.decode_recipe(ai_ser.encode_recipe(recipe)) == recipe


@pytest.mark.parametrize("recipe", RECIPES)
def test_the_ai_decoder_round_trips_the_api_encoding(recipe: Recipe) -> None:
    assert ai_ser.decode_recipe(api_ser.encode_recipe(recipe)) == recipe
