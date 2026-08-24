"""Tests for the closed ingredient-category vocabulary and its only entry point (R4-R7)."""

from __future__ import annotations

import pytest

from planner_core.domain.errors import PlannerError
from planner_core.domain.ingredient_category import (
    IngredientCategory,
    UnknownIngredientCategory,
    parse_category,
)


def test_the_ingredient_category_vocabulary_is_closed() -> None:
    """R4: exactly the six terms G-82 closed FR-RULE-04's ellipsis at."""
    assert [category.value for category in IngredientCategory] == [
        "meat",
        "fish",
        "carbohydrate",
        "legume",
        "vegetable",
        "eggs",
    ]
    assert [category.name for category in IngredientCategory] == [
        "MEAT",
        "FISH",
        "CARBOHYDRATE",
        "LEGUME",
        "VEGETABLE",
        "EGGS",
    ]


def test_parse_category_resolves_every_code() -> None:
    """R5: the single entry point from a stored or submitted code to a member."""
    assert parse_category("meat") is IngredientCategory.MEAT
    assert parse_category("fish") is IngredientCategory.FISH
    assert parse_category("carbohydrate") is IngredientCategory.CARBOHYDRATE
    assert parse_category("legume") is IngredientCategory.LEGUME
    assert parse_category("vegetable") is IngredientCategory.VEGETABLE
    assert parse_category("eggs") is IngredientCategory.EGGS


def test_parse_category_rejects_a_value_outside_the_list() -> None:
    """R6: exact match only - no case folding, no trimming, no prefix match.

    "vegetarian" is the one code that used to be valid (G-82 struck it), so a
    stale record, dropdown or AI prompt is its likeliest source.
    """
    for rejected in ("MEAT", " meat", "dairy", "", "vegetarian", "vegetables"):
        with pytest.raises(UnknownIngredientCategory):
            parse_category(rejected)


def test_unknown_ingredient_category_is_a_planner_error() -> None:
    """R7: the handler layer catches the family by its base, never by name."""
    assert issubclass(UnknownIngredientCategory, PlannerError)

    with pytest.raises(PlannerError) as raised:
        parse_category("dairy")

    assert isinstance(raised.value, UnknownIngredientCategory)
