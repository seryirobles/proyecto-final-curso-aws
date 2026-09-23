"""Base class for every domain error raised by planner_core."""

from __future__ import annotations


class PlannerError(Exception):
    """Base class for domain errors."""


class EmptyField(PlannerError):
    """A required field was blank (missing, empty or whitespace-only).

    One subclass per field (R17: lambda_api/errors.py's `_TABLE` maps every
    `code` to a static `planner_core.messages` constant, never a composed
    string) - same shape as RecipeNotFound/CandidateNotFound/
    ShoppingItemNotFound (issue empty-field-error-messages).
    """


class EmptyName(EmptyField):
    """The recipe's or shopping item's `name` was blank."""


class EmptyCategory(EmptyField):
    """The recipe's `category` was blank."""


class EmptyIngredientName(EmptyField):
    """An ingredient's `name` was blank."""


class EmptyQuantity(EmptyField):
    """An ingredient's `quantity` was absent-valued or blank."""


class EmptyMeasure(EmptyField):
    """A recipe ingredient's or shopping item's `unit` was blank.

    Named EmptyMeasure, not EmptyUnit: the latter trips
    test_shared_kernel_guards.py's second-unit-vocabulary scan (R16).
    """


class EmptyTool(EmptyField):
    """A `tools` entry was blank."""


class EmptyProcedureStep(EmptyField):
    """A `procedure` entry was blank."""
