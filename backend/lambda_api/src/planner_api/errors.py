"""`PlannerError` -> RFC 9457 `application/problem+json` (docs/rest_api_contract.md
section 4). The one place that maps an exception to a wire error (R14-R21)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any  # untyped JSON in/out is the wire boundary itself (conventions.md)

from planner_core import messages
from planner_core.domain.authentication_guards import PasswordResetPending
from planner_core.domain.authorization import Forbidden
from planner_core.domain.calendar import InvalidIsoWeek
from planner_core.domain.candidate import CandidateNotFound
from planner_core.domain.errors import PlannerError
from planner_core.domain.ingredient_category import UnknownIngredientCategory
from planner_core.domain.login_policy import InvalidCredentials
from planner_core.domain.password_policy import PasswordTooShort
from planner_core.domain.rules import (
    InvalidRuleId,
    InvalidWeekday,
    PinRulesAffected,
    UnsatisfiableRuleSet,
)
from planner_core.domain.session_policy import SessionExpired
from planner_core.domain.shopping import ShoppingItemNotFound
from planner_core.domain.units import UnknownUnit
from planner_core.domain.username_policy import UsernameAlreadyTaken, UsernameReserved
from planner_core.ports.accounts import AccountNotFound
from planner_core.ports.recipes import RecipeNotFound
from planner_core.ports.shopping_list import ShoppingListLockHeld

from planner_api.serialization import (
    GenerationNotFound,
    MalformedRequest,
    RouteNotFound,
    encode_rule,
)

logger = logging.getLogger("planner_api")

_DetailsBuilder = Callable[[PlannerError], dict[str, Any]]


@dataclass(frozen=True)
class _ErrorSpec:
    status: int
    code: str
    message: str
    details: _DetailsBuilder | None = None


def _pin_rules_details(exc: PlannerError) -> dict[str, Any]:
    assert isinstance(exc, PinRulesAffected)  # table dispatch guarantees the type
    return {"pins": [{"day": pin.day, "slot": int(pin.slot.value)} for pin in exc.pins]}


def _unsatisfiable_details(exc: PlannerError) -> dict[str, Any]:
    assert isinstance(exc, UnsatisfiableRuleSet)
    return {"conflicts": [encode_rule(rule) for rule in exc.conflicting]}


_TABLE: dict[type[Exception], _ErrorSpec] = {
    InvalidCredentials: _ErrorSpec(401, "INVALID_CREDENTIALS", messages.INVALID_CREDENTIALS),
    SessionExpired: _ErrorSpec(401, "SESSION_EXPIRED", messages.SESSION_EXPIRED),
    Forbidden: _ErrorSpec(403, "FORBIDDEN", messages.FORBIDDEN),
    PasswordResetPending: _ErrorSpec(403, "PASSWORD_RESET_PENDING", messages.SET_PASSWORD_REQUIRED),
    AccountNotFound: _ErrorSpec(404, "ACCOUNT_NOT_FOUND", messages.ACCOUNT_NOT_FOUND),
    RecipeNotFound: _ErrorSpec(404, "RECIPE_NOT_FOUND", messages.RECIPE_NOT_FOUND),
    CandidateNotFound: _ErrorSpec(404, "CANDIDATE_NOT_FOUND", messages.CANDIDATE_NOT_FOUND),
    ShoppingItemNotFound: _ErrorSpec(
        404, "SHOPPING_ITEM_NOT_FOUND", messages.SHOPPING_ITEM_NOT_FOUND
    ),
    UsernameAlreadyTaken: _ErrorSpec(
        409, "USERNAME_ALREADY_TAKEN", messages.USERNAME_ALREADY_TAKEN
    ),
    ShoppingListLockHeld: _ErrorSpec(
        409, "SHOPPING_LIST_LOCK_HELD", messages.SHOPPING_LIST_LOCK_HELD
    ),
    PinRulesAffected: _ErrorSpec(
        409, "PIN_RULES_AFFECTED", messages.PIN_RULES_AFFECTED, _pin_rules_details
    ),
    UsernameReserved: _ErrorSpec(422, "USERNAME_RESERVED", messages.USERNAME_RESERVED),
    PasswordTooShort: _ErrorSpec(422, "PASSWORD_TOO_SHORT", messages.PASSWORD_TOO_SHORT),
    UnknownUnit: _ErrorSpec(422, "UNKNOWN_UNIT", messages.UNKNOWN_UNIT),
    UnknownIngredientCategory: _ErrorSpec(
        422, "UNKNOWN_INGREDIENT_CATEGORY", messages.UNKNOWN_INGREDIENT_CATEGORY
    ),
    InvalidWeekday: _ErrorSpec(422, "INVALID_WEEKDAY", messages.INVALID_WEEKDAY),
    UnsatisfiableRuleSet: _ErrorSpec(
        422, "UNSATISFIABLE_RULE_SET", messages.UNSATISFIABLE_RULE_SET, _unsatisfiable_details
    ),
    InvalidIsoWeek: _ErrorSpec(422, "INVALID_ISO_WEEK", messages.INVALID_ISO_WEEK),
    # InvalidRuleId only ever originates from the {ruleId} path segment in this
    # contract (design.md section 4 — origin known at the parse site).
    InvalidRuleId: _ErrorSpec(400, "INVALID_RULE_ID", messages.INVALID_RULE_ID),
    MalformedRequest: _ErrorSpec(400, "MALFORMED_REQUEST", messages.MALFORMED_REQUEST),
    GenerationNotFound: _ErrorSpec(404, "GENERATION_NOT_FOUND", messages.GENERATION_NOT_FOUND),
    RouteNotFound: _ErrorSpec(404, "NOT_FOUND", messages.ROUTE_NOT_FOUND),
}

_FALLBACK = _ErrorSpec(500, "INTERNAL_ERROR", messages.INTERNAL_ERROR)


@dataclass(frozen=True)
class ProblemResponse:
    status: int
    body: dict[str, Any]


def build_problem_response(exc: Exception) -> ProblemResponse:
    """R14-R21, R24. Any `PlannerError` this table does not name gets the
    generic 500 (R20); its traceback is logged, never returned (R24, R25)."""
    spec = _TABLE.get(type(exc))
    if spec is None:
        logger.exception("Unmapped error handling request", exc_info=exc)
        spec = _FALLBACK
    details = (
        spec.details(exc) if spec.details is not None and isinstance(exc, PlannerError) else None
    )
    body: dict[str, Any] = {
        "type": f"urn:planner:{spec.code.lower().replace('_', '-')}",
        "title": spec.code.replace("_", " ").capitalize(),
        "status": spec.status,
        "detail": spec.message,
        "code": spec.code,
    }
    if details is not None:
        body["details"] = details
    return ProblemResponse(status=spec.status, body=body)
