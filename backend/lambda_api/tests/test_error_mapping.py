"""errors.py: PlannerError -> RFC 9457 problem+json (R14-R21, R24, R25)."""

from __future__ import annotations

import pytest
from planner_core import messages
from planner_core.domain.authorization import Forbidden
from planner_core.domain.calendar import MealSlot
from planner_core.domain.role import Role
from planner_core.domain.rules import (
    DisabledDay,
    PinRule,
    PinRulesAffected,
    UnsatisfiableRuleSet,
)
from planner_core.domain.session_policy import SessionExpired
from planner_core.ports.accounts import AccountNotFound

from planner_api.errors import _TABLE, build_problem_response
from planner_api.serialization import MalformedRequest


@pytest.mark.parametrize(
    ("exc", "status", "code", "detail"),
    [
        (SessionExpired(), 401, "SESSION_EXPIRED", messages.SESSION_EXPIRED),
        (Forbidden(Role.USER), 403, "FORBIDDEN", messages.FORBIDDEN),
        (AccountNotFound("u-1"), 404, "ACCOUNT_NOT_FOUND", messages.ACCOUNT_NOT_FOUND),
        (MalformedRequest(), 400, "MALFORMED_REQUEST", messages.MALFORMED_REQUEST),
    ],
)
def test_known_domain_exceptions_map_to_the_contract_status_and_code(
    exc: Exception, status: int, code: str, detail: str
) -> None:
    problem = build_problem_response(exc)

    assert problem.status == status
    assert problem.body["code"] == code
    assert problem.body["detail"] == detail


def test_problem_body_is_rfc9457_shaped() -> None:
    problem = build_problem_response(SessionExpired())

    assert problem.body["type"] == "urn:planner:session-expired"
    assert problem.body["title"] == "Session expired"
    assert problem.body["status"] == 401
    assert set(problem.body) == {"type", "title", "status", "detail", "code"}


def test_unmapped_planner_error_maps_to_500_internal_error() -> None:
    class SomeUnmappedError(Exception):
        pass

    problem = build_problem_response(SomeUnmappedError("boom"))

    assert problem.status == 500
    assert problem.body["code"] == "INTERNAL_ERROR"
    assert problem.body["detail"] == messages.INTERNAL_ERROR
    assert "boom" not in str(problem.body)  # R25 - no stack frame or raw exception text


def test_unsatisfiable_rule_set_carries_the_conflicting_rules_as_details() -> None:
    conflicting = (DisabledDay(day=3),)

    problem = build_problem_response(UnsatisfiableRuleSet(conflicting))

    assert problem.status == 422
    assert problem.body["code"] == "UNSATISFIABLE_RULE_SET"
    assert problem.body["details"] == {"conflicts": [{"type": "disabledDay", "day": 3}]}


def test_pin_rules_affected_carries_the_affected_pins_as_details() -> None:
    pins = (PinRule(day=7, slot=MealSlot.LUNCH, recipe_id="r-1"),)

    problem = build_problem_response(PinRulesAffected(pins))

    assert problem.status == 409
    assert problem.body["code"] == "PIN_RULES_AFFECTED"
    assert problem.body["details"] == {"pins": [{"day": 7, "slot": 1}]}


def test_every_mapped_detail_is_a_messages_module_constant() -> None:
    """R17 - the table never composes its own string; every `message` value
    is one of `planner_core.messages`' own constants."""
    known_messages = {value for value in vars(messages).values() if isinstance(value, str)}
    for spec in _TABLE.values():
        assert spec.message in known_messages, spec.code
