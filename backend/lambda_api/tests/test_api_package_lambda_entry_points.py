"""The api-package Lambda entry points under AWS's real calling convention,
`lambda_handler(event, context)` (issues/lambda-handler-receives-context-as-deps)."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from types import ModuleType
from typing import Any

import pytest
from _helpers import api_event, make_deps, seed_user
from planner_core.domain.shopping import ShoppingItem
from planner_core.domain.units import Unit

from planner_api import authorizer, handler, scheduled, wiring
from planner_api.wiring import Dependencies

_METHOD_ARN = "arn:aws:execute-api:eu-west-1:123:abc/prod/GET/v1/weeks/2026-W33"


class FakeLambdaContext:
    """Shaped like the runtime's LambdaContext; it carries no ports."""

    function_name = "planner-dev-api"
    aws_request_id = "req-1"

    def get_remaining_time_in_millis(self) -> int:
        return 29_000


class _FalsyDependencies(Dependencies):
    def __bool__(self) -> bool:
        return False


def _wire(monkeypatch: pytest.MonkeyPatch, entry: ModuleType, builder: str, deps: Any) -> list[int]:
    """Replace the wiring builder wherever the entry module may resolve it."""
    calls: list[int] = []

    def build(*_args: object, **_kwargs: object) -> Any:
        calls.append(1)
        return deps

    monkeypatch.setattr(wiring, builder, build)
    if hasattr(entry, builder):
        monkeypatch.setattr(entry, builder, build)
    return calls


def _refuse(monkeypatch: pytest.MonkeyPatch, entry: ModuleType, builder: str) -> None:
    def build(*_args: object, **_kwargs: object) -> Any:
        raise AssertionError(f"{builder} must not run here")

    monkeypatch.setattr(wiring, builder, build)
    if hasattr(entry, builder):
        monkeypatch.setattr(entry, builder, build)


def _login_event() -> dict[str, Any]:
    return api_event("POST", "/v1/session", body={"username": "user-u-1", "password": "irrelevant"})


def test_api_lambda_handler_logs_in_with_wired_dependencies_not_the_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E1 - reproduction: today the context is taken as `deps` and login is a 500."""
    deps = make_deps()
    seed_user(deps, user_id="u-1")
    calls = _wire(monkeypatch, handler, "build_dependencies", deps)

    response = handler.lambda_handler(_login_event(), FakeLambdaContext())

    assert response["statusCode"] == 200, response["body"]
    assert response["headers"]["Set-Cookie"].startswith("session=")
    assert calls == [1]


def test_api_lambda_handler_maps_a_wiring_failure_to_the_problem_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E1 regression - a missing secret stays a 500 problem body, never an unhandled raise."""

    def broken(*_args: object, **_kwargs: object) -> Any:
        raise RuntimeError("SESSION_SECRET_KEY is not configured")

    monkeypatch.setattr(wiring, "build_dependencies", broken)
    if hasattr(handler, "build_dependencies"):
        monkeypatch.setattr(handler, "build_dependencies", broken)

    response = handler.lambda_handler(_login_event(), FakeLambdaContext())

    assert response["statusCode"] == 500
    assert response["headers"]["Cache-Control"] == "no-store"
    assert '"code": "INTERNAL_ERROR"' in response["body"]


def test_authorizer_lambda_handler_allows_a_valid_session_with_wired_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E2 - today the context is taken as `deps`: AttributeError on `.accounts`."""
    deps = make_deps()
    token = seed_user(deps, user_id="u-1")
    calls = _wire(monkeypatch, authorizer, "build_authorizer_dependencies", deps)
    event = {"methodArn": _METHOD_ARN, "headers": {"Cookie": f"session={token}"}}

    policy = authorizer.lambda_handler(event, FakeLambdaContext())

    assert policy["policyDocument"]["Statement"][0]["Effect"] == "Allow"
    assert policy["context"]["userId"] == "u-1"
    assert calls == [1]


def test_authorizer_lambda_handler_denies_a_missing_cookie_without_building_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E2 regression - no cookie never reaches Secrets Manager or DynamoDB."""
    _refuse(monkeypatch, authorizer, "build_authorizer_dependencies")
    event = {"methodArn": _METHOD_ARN, "headers": {}}

    policy = authorizer.lambda_handler(event, FakeLambdaContext())

    assert policy["policyDocument"]["Statement"][0]["Effect"] == "Deny"


def test_rollover_lambda_handler_runs_with_wired_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E3 - today the context is taken as `deps`: AttributeError on `.clock`."""
    deps = make_deps()
    deps.shopping.save_item(
        ShoppingItem(id="s-1", name="arroz", quantity=1, unit=Unit.GRAM, checked=True)
    )
    calls = _wire(monkeypatch, scheduled, "build_rollover_dependencies", deps)

    result = scheduled.lambda_handler({}, FakeLambdaContext())

    assert result["status"] == "ok"
    assert list(deps.shopping.list_items()) == []
    assert calls == [1]


def _falsy(deps: Dependencies) -> _FalsyDependencies:
    fields = {f.name: getattr(deps, f.name) for f in dataclasses.fields(deps)}
    return _FalsyDependencies(**fields)


def _call_api(deps: Dependencies) -> bool:
    seed_user(deps, user_id="u-1")
    response = handler.handle(_login_event(), deps=_falsy(deps))
    return bool(response["statusCode"] == 200)


def _call_authorizer(deps: Dependencies) -> bool:
    token = seed_user(deps, user_id="u-1")
    event = {"methodArn": _METHOD_ARN, "headers": {"Cookie": f"session={token}"}}
    policy = authorizer.handle(event, deps=_falsy(deps))
    return bool(policy["policyDocument"]["Statement"][0]["Effect"] == "Allow")


def _call_rollover(deps: Dependencies) -> bool:
    return bool(scheduled.handle({}, deps=_falsy(deps))["status"] == "ok")


@pytest.mark.parametrize(
    ("entry", "builder", "call"),
    [
        (handler, "build_dependencies", _call_api),
        (authorizer, "build_authorizer_dependencies", _call_authorizer),
        (scheduled, "build_rollover_dependencies", _call_rollover),
    ],
    ids=["api", "authorizer", "rollover"],
)
def test_an_injected_bundle_is_used_even_when_it_is_falsy(
    monkeypatch: pytest.MonkeyPatch,
    entry: ModuleType,
    builder: str,
    call: Callable[[Dependencies], bool],
) -> None:
    """E5 - injection is decided by presence, not truthiness (`or` trap)."""
    _refuse(monkeypatch, entry, builder)

    assert call(make_deps()) is True
