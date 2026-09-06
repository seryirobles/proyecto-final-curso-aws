"""Every `@dataclass(frozen=True)` this feature adds gets a frozen-instance
test (docs/conventions.md § Tests): attribute assignment must raise."""

from __future__ import annotations

import dataclasses

import pytest
from _helpers import make_deps
from planner_core.domain.role import Role

from planner_api.errors import ProblemResponse, _ErrorSpec
from planner_api.routing import AuthContext, RouteResult, RouteSpec
from planner_api.wiring import Dependencies


def test_auth_context_is_frozen() -> None:
    context = AuthContext(user_id="u-1", role=Role.USER, password_reset_required=False)
    with pytest.raises(dataclasses.FrozenInstanceError):
        context.__setattr__("user_id", "u-2")


def test_route_result_is_frozen() -> None:
    result = RouteResult(status=200)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.__setattr__("status", 500)


def test_route_spec_is_frozen() -> None:
    spec = RouteSpec(handler=lambda *_args: RouteResult(status=200))
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.__setattr__("public", True)


def test_error_spec_is_frozen() -> None:
    spec = _ErrorSpec(status=404, code="X", message="y")
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.__setattr__("status", 500)


def test_problem_response_is_frozen() -> None:
    problem = ProblemResponse(status=404, body={})
    with pytest.raises(dataclasses.FrozenInstanceError):
        problem.__setattr__("status", 500)


def test_dependencies_is_frozen() -> None:
    deps = make_deps()
    with pytest.raises(dataclasses.FrozenInstanceError):
        deps.__setattr__("clock", deps.clock)


def test_dependencies_is_declared_a_dataclass() -> None:
    assert dataclasses.is_dataclass(Dependencies)
