"""Shared test scaffolding: a fully-faked `Dependencies` bundle, a seeded
user, and an API-Gateway-shaped event builder. Not collected as tests itself
(no `test_` prefix)."""

from __future__ import annotations

import json
from typing import Any

from planner_core.domain.ai_prompt import PROMPT_VERSION_CONFIG_KEY
from planner_core.domain.role import Role
from planner_core.ports.accounts import AccountRecord, AccountRepository
from planner_core.ports.archive import ArchiveRepository
from planner_core.ports.clock import Clock
from planner_core.ports.config import ConfigPort
from planner_core.ports.generation_queue import GenerationQueue
from planner_core.ports.password_hasher import PasswordHasher
from planner_core.ports.recipes import RecipeRepository
from planner_core.ports.rules import RuleRepository
from planner_core.ports.shopping_list import ShoppingListRepository
from planner_core.ports.tokens import HmacTokenSigner, TokenSigner
from planner_core.ports.weeks import WeekRepository
from support.fakes import (
    FakeAccountRepository,
    FakeArchiveRepository,
    FakeClock,
    FakeConfig,
    FakeGenerationQueue,
    FakePasswordHasher,
    FakeRecipeRepository,
    FakeRuleRepository,
    FakeShoppingListRepository,
    FakeWeekRepository,
)

from planner_api.wiring import Dependencies

SECRET = b"test-secret-key"


def make_deps(
    *,
    accounts: AccountRepository | None = None,
    recipes: RecipeRepository | None = None,
    weeks: WeekRepository | None = None,
    rules: RuleRepository | None = None,
    shopping: ShoppingListRepository | None = None,
    archive: ArchiveRepository | None = None,
    queue: GenerationQueue | None = None,
    hasher: PasswordHasher | None = None,
    signer: TokenSigner | None = None,
    clock: Clock | None = None,
    config: ConfigPort | None = None,
) -> Dependencies:
    return Dependencies(
        accounts=accounts if accounts is not None else FakeAccountRepository(),
        recipes=recipes if recipes is not None else FakeRecipeRepository(),
        weeks=weeks if weeks is not None else FakeWeekRepository(),
        rules=rules if rules is not None else FakeRuleRepository(),
        shopping=shopping if shopping is not None else FakeShoppingListRepository(),
        archive=archive if archive is not None else FakeArchiveRepository(),
        queue=queue if queue is not None else FakeGenerationQueue(),
        hasher=hasher if hasher is not None else FakePasswordHasher(),
        signer=signer if signer is not None else HmacTokenSigner(SECRET),
        clock=clock if clock is not None else FakeClock.at("2026-08-17T10:00:00+00:00"),
        config=config if config is not None else FakeConfig({PROMPT_VERSION_CONFIG_KEY: "v1"}),
    )


def seed_user(
    deps: Dependencies,
    *,
    user_id: str = "u-1",
    role: Role = Role.USER,
    password_reset_required: bool = False,
) -> str:
    """Create the account and return a valid session token for it."""
    deps.accounts.create(
        AccountRecord(
            user_id=user_id,
            username=f"user-{user_id}",
            role=role,
            password_hash=deps.hasher.hash("irrelevant"),
            password_reset_required=password_reset_required,
            credentials_valid_since=deps.clock.now(),
        )
    )
    return deps.signer.issue(user_id, deps.clock.now())


def authorizer_context(
    user_id: str = "u-1", role: Role = Role.USER, password_reset_required: bool = False
) -> dict[str, str]:
    return {
        "userId": user_id,
        "role": role.value,
        "passwordResetRequired": "true" if password_reset_required else "false",
    }


def api_event(
    method: str,
    resource: str,
    *,
    path_params: dict[str, str] | None = None,
    query: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    cookie: str | None = None,
    context: dict[str, str] | None = None,
) -> dict[str, Any]:
    headers: dict[str, str] = {}
    if cookie is not None:
        headers["Cookie"] = f"session={cookie}"
    request_context: dict[str, Any] = {}
    if context is not None:
        request_context["authorizer"] = context
    return {
        "httpMethod": method,
        "resource": resource,
        "pathParameters": path_params,
        "queryStringParameters": query,
        "headers": headers,
        "body": None if body is None else json.dumps(body),
        "requestContext": request_context,
    }
