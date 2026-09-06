"""routing.py's dispatch table: every contract access pattern is routed except
`AP3`/`AP9`/`AP29`/rollover (R26, R27, R33), and no `GET` entry ever reaches a
mutating port method (R2)."""

from __future__ import annotations

from typing import Any, cast

import pytest
from _helpers import make_deps, seed_user
from planner_core.domain.role import Role
from planner_core.ports.accounts import AccountRepository
from planner_core.ports.generation_queue import GenerationQueue
from planner_core.ports.recipes import RecipeRepository
from planner_core.ports.rules import RuleRepository
from planner_core.ports.shopping_list import ShoppingListRepository
from planner_core.ports.weeks import WeekRepository
from support.fakes import (
    FakeAccountRepository,
    FakeGenerationQueue,
    FakeRecipeRepository,
    FakeRuleRepository,
    FakeShoppingListRepository,
    FakeWeekRepository,
)

from planner_api.routing import ROUTES, AuthContext
from planner_api.wiring import Dependencies

EXPECTED_ROUTES = {
    ("POST", "/v1/session"),
    ("DELETE", "/v1/session"),
    ("PUT", "/v1/session/password"),
    ("GET", "/v1/users"),
    ("GET", "/v1/users/{userId}"),
    ("POST", "/v1/users"),
    ("PATCH", "/v1/users/{userId}"),
    ("DELETE", "/v1/users/{userId}"),
    ("GET", "/v1/live-weeks"),
    ("GET", "/v1/weeks/{weekId}"),
    ("GET", "/v1/weeks/{weekId}/summary"),
    ("GET", "/v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates/{candidateId}"),
    ("POST", "/v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates"),
    ("PUT", "/v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates/{candidateId}"),
    ("DELETE", "/v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates/{candidateId}"),
    ("PUT", "/v1/weeks/{weekId}/days/{day}/slots/{slot}/definitive"),
    ("DELETE", "/v1/weeks/{weekId}/days/{day}/slots/{slot}/definitive"),
    ("GET", "/v1/library/recipes"),
    ("GET", "/v1/library/recipes/{recipeId}"),
    ("POST", "/v1/library/recipes"),
    ("PUT", "/v1/library/recipes/{recipeId}"),
    ("DELETE", "/v1/library/recipes/{recipeId}"),
    ("GET", "/v1/rules"),
    ("PUT", "/v1/rules/{ruleId}"),
    ("DELETE", "/v1/rules/{ruleId}"),
    ("GET", "/v1/shopping-list"),
    ("POST", "/v1/shopping-list/items"),
    ("PUT", "/v1/shopping-list/items/{itemId}"),
    ("PATCH", "/v1/shopping-list/items/{itemId}"),
    ("DELETE", "/v1/shopping-list/items/{itemId}"),
    ("DELETE", "/v1/shopping-list/checked-items"),
    ("POST", "/v1/shopping-list/resync"),
    ("POST", "/v1/generations"),
    ("GET", "/v1/generations/{generationId}"),
    ("DELETE", "/v1/generations/{generationId}"),  # AP27 discard (R42)
}


def test_every_contract_endpoint_is_routed_exactly_once() -> None:
    assert set(ROUTES) == EXPECTED_ROUTES


def test_no_route_exposes_ap9_ingredients_or_rollover() -> None:
    for _method, resource in ROUTES:
        assert "include" not in resource
        assert "rollover" not in resource


_MUTATORS = frozenset(
    {
        "create",
        "rename",
        "update_credentials",
        "delete",
        "revoke_credentials",
        "save_slot",
        "save_week",
        "save_item",
        "delete_item",
        "delete_checked_items",
        "acquire_lock",
        "release_lock",
        "save",
        "save_rule",
        "delete_rule",
        "submit",
        "discard",
    }
)


class _ReadOnlyGuard:
    """Wraps a fake port; raises if a `GET` handler reaches for a mutator (R2)."""

    def __init__(self, inner: object) -> None:
        self._inner = inner

    def __getattr__(self, name: str) -> Any:
        if name in _MUTATORS:

            def _blocked(*_args: object, **_kwargs: object) -> object:
                raise AssertionError(f"a GET route must not call {name}()")

            return _blocked
        return getattr(self._inner, name)


def _no_write_deps() -> Dependencies:
    # Seed through the raw (unwrapped) fake first - the guard would otherwise
    # block seed_user's own accounts.create() call.
    accounts_fake = FakeAccountRepository()
    seed_user(make_deps(accounts=accounts_fake), user_id="u-2")
    return make_deps(
        accounts=cast(AccountRepository, _ReadOnlyGuard(accounts_fake)),
        recipes=cast(RecipeRepository, _ReadOnlyGuard(FakeRecipeRepository())),
        weeks=cast(WeekRepository, _ReadOnlyGuard(FakeWeekRepository())),
        rules=cast(RuleRepository, _ReadOnlyGuard(FakeRuleRepository())),
        shopping=cast(ShoppingListRepository, _ReadOnlyGuard(FakeShoppingListRepository())),
        queue=cast(GenerationQueue, _ReadOnlyGuard(FakeGenerationQueue())),
    )


def _auth_for(resource: str) -> AuthContext:
    role = Role.ADMIN if resource.startswith("/v1/users") else Role.USER
    return AuthContext(user_id="u-2", role=role, password_reset_required=False)


@pytest.mark.parametrize(
    ("resource", "path_params"),
    [
        ("/v1/users", {}),
        ("/v1/users/{userId}", {"userId": "u-2"}),
        ("/v1/live-weeks", {}),
        ("/v1/weeks/{weekId}", {"weekId": "2026-W33"}),
        ("/v1/weeks/{weekId}/summary", {"weekId": "2026-W33"}),
        (
            "/v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates/{candidateId}",
            {"weekId": "2026-W33", "day": "1", "slot": "1", "candidateId": "c-1"},
        ),
        ("/v1/library/recipes", {}),
        ("/v1/library/recipes/{recipeId}", {"recipeId": "r-1"}),
        ("/v1/rules", {}),
        ("/v1/shopping-list", {}),
        ("/v1/generations/{generationId}", {"generationId": "g-1"}),
    ],
)
def test_get_routes_never_call_a_mutating_port_method(
    resource: str, path_params: dict[str, str]
) -> None:
    deps = _no_write_deps()
    spec = ROUTES[("GET", resource)]

    try:
        spec.handler(path_params, {}, {}, _auth_for(resource), deps)
    except AssertionError:
        raise  # a mutator fired - the failure this test exists to catch
    except Exception:  # unseeded fixtures 404 legitimately here; only writes matter
        pass
