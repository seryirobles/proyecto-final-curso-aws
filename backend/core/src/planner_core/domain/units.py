"""The closed measurement-unit vocabulary and the one entry point that validates against it."""

from __future__ import annotations

from enum import StrEnum

from planner_core.domain.errors import PlannerError


class Unit(StrEnum):
    """The admissible measurement units: exactly one per physical dimension.

    FR-SHOP-03 forbids cross-unit conversion, so a second unit for the same
    dimension would be a permanent split in the shopping list rather than a
    convenience: two lines that can never merge (G-39). StrEnum because the
    member's value is the stored unidad code itself, so no second mapping table
    exists to drift from this one.
    """

    GRAM = "g"
    MILLILITRE = "ml"
    UNIT = "unit"


class UnknownUnit(PlannerError):
    """Raised when a value is not a member of the fixed unit list.

    Carries the rejected value and nothing else. The Castilian rejection text
    belongs to the features that own the user-facing flow, in the single es-ES
    messages module (docs/conventions.md, Language policy).
    """

    value: str

    def __init__(self, value: str) -> None:
        super().__init__(value)
        self.value = value


def parse_unit(value: str) -> Unit:
    """Resolve a unit code to its member, or raise UnknownUnit."""
    # Exact match only, never through normalize() (G-48): fuzzy parsing
    # would let "kg" pass as "g", a cross-unit conversion in disguise.
    for unit in Unit:
        if value == unit.value:
            return unit
    raise UnknownUnit(value)
