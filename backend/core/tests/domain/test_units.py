"""Tests for the closed unit vocabulary and its only entry point (R14, R15, R17-R21).

Every input and expected result is taken verbatim from
`specs/text_and_units/design.md` section 8.2.

R21 is a negative claim about the module's surface rather than about a call, so
it is asserted as a set: the module defines exactly three public names, and no
member carries a factor, a ratio or a base unit that a conversion could be built
from. Asserting "no conversion exists" any other way would be a comment.
"""

from __future__ import annotations

from types import ModuleType

import pytest

from planner_core.domain import units
from planner_core.domain.errors import PlannerError
from planner_core.domain.units import Unit, UnknownUnit, parse_unit


def _defined_here(module: ModuleType) -> set[str]:
    """Public names the module declares itself, ignoring the ones it imports."""
    return {
        name
        for name, value in vars(module).items()
        if not name.startswith("_") and getattr(value, "__module__", None) == module.__name__
    }


def test_the_unit_vocabulary_is_closed() -> None:
    """R14, R15: three members, one per dimension, and the code is the stored value."""
    assert [unit.value for unit in Unit] == ["g", "ml", "unit"]
    assert [unit.name for unit in Unit] == ["GRAM", "MILLILITRE", "UNIT"]


def test_parse_unit_resolves_every_code() -> None:
    """R17: the single entry point from a stored or submitted code to a member."""
    assert parse_unit("g") is Unit.GRAM
    assert parse_unit("ml") is Unit.MILLILITRE
    assert parse_unit("unit") is Unit.UNIT


def test_parse_unit_rejects_a_value_outside_the_list() -> None:
    """R18: exact match only. "kg" is the deliberate exclusion, "G" the deliberate strictness."""
    for rejected in ("G", " g", "gramos", "kg", ""):
        with pytest.raises(UnknownUnit):
            parse_unit(rejected)


def test_unknown_unit_is_a_planner_error() -> None:
    """R19: the handler layer catches the family by its base, never by name."""
    assert issubclass(UnknownUnit, PlannerError)

    with pytest.raises(PlannerError) as raised:
        parse_unit("gramos")

    assert isinstance(raised.value, UnknownUnit)


def test_unknown_unit_carries_the_rejected_value() -> None:
    """R20: the caller builds the es-ES sentence; this feature supplies only the value."""
    for rejected in ("gramos", "G"):
        with pytest.raises(UnknownUnit) as raised:
            parse_unit(rejected)

        assert raised.value.value == rejected


def test_the_units_module_exposes_no_conversion() -> None:
    """R21: FR-SHOP-03 forbids cross-unit conversion, so no API for one may exist."""
    assert _defined_here(units) == {"Unit", "UnknownUnit", "parse_unit"}

    declared_on_the_enum = {name for name in vars(Unit) if not name.startswith("_")}
    assert declared_on_the_enum == {"GRAM", "MILLILITRE", "UNIT"}

    for unit in Unit:
        carried = {name for name in vars(unit) if not name.startswith("_")}
        assert carried == set(), f"{unit.name} carries {sorted(carried)}"
