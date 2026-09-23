"""Shared recipe-content (de)serialisation for the library and week adapters:
the *[receta]* shape of docs/data_model.md section 4.2/4.3, mapped between the
Spanish stored attributes and the English domain value objects."""

from __future__ import annotations

from decimal import InvalidOperation
from typing import Any

from planner_core.domain.ingredient_category import IngredientCategory, parse_category
from planner_core.domain.recipe import Ingredient
from planner_core.domain.units import parse_unit

from planner_api.adapters.dynamo import _table


def content_attrs(
    *,
    name: str,
    ingredients: tuple[Ingredient, ...],
    tools: tuple[str, ...],
    procedure: tuple[str, ...],
    category: IngredientCategory,
    servings: int | None,
    estimated_time: int | None,
) -> dict[str, Any]:
    return {
        "nombrePlato": name,
        "tipoAlimento": category.value,
        "tiempo": estimated_time,
        "numeroComensales": servings,
        "ingredientes": [
            {
                "nombreIngrediente": ing.name,
                "cantidad": ing.quantity,
                "unidad": ing.unit.value,
            }
            for ing in ingredients
        ],
        "utensilios": list(tools),
        "pasos": [
            {"numeroPaso": number, "descripcionPaso": step}
            for number, step in enumerate(procedure, start=1)
        ],
    }


def read_ingredients(item: dict[str, Any]) -> tuple[Ingredient, ...]:
    return tuple(
        Ingredient(
            name=str(row["nombreIngrediente"]),
            quantity=_table.decode_number(row["cantidad"]),
            unit=parse_unit(str(row["unidad"])),
        )
        for row in item.get("ingredientes", [])
    )


def read_tools(item: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(tool) for tool in item.get("utensilios", []))


def read_procedure(item: dict[str, Any]) -> tuple[str, ...]:
    steps = sorted(item.get("pasos", []), key=lambda row: _table.decode_number(row["numeroPaso"]))
    return tuple(str(row["descripcionPaso"]) for row in steps)


def read_category(item: dict[str, Any]) -> IngredientCategory:
    return parse_category(str(item["tipoAlimento"]))


def read_servings(item: dict[str, Any]) -> int | None:
    value = item.get("numeroComensales")
    return None if value is None else int(_table.decode_number(value))


def read_estimated_time(item: dict[str, Any]) -> int | None:
    """A `tiempo` written before G-90 as free text reads back as absent
    instead of raising (issue tiempo-estimado-numeric-minutes)."""
    value = item.get("tiempo")
    if value is None:
        return None
    try:
        return int(_table.decode_number(value))
    except InvalidOperation:
        return None
