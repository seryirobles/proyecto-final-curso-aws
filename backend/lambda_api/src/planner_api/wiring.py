"""Composition root: the only module naming a concrete adapter
(docs/conventions.md § *Packaging conventions*). Builds the real AWS-backed
stack; pytest builds its own `Dependencies` from `core`'s fakes instead of
calling this module, mirroring `backend/tests/contract/conftest.py`'s pattern
(design.md section 0 - no test-only import belongs in production wiring)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from planner_core.domain.calendar import IsoWeek
from planner_core.domain.rollover import ArchivedWeek
from planner_core.ports.accounts import AccountRepository
from planner_core.ports.archive import ArchiveRepository
from planner_core.ports.clock import Clock, SystemClock
from planner_core.ports.config import ConfigPort, EnvConfig
from planner_core.ports.generation_queue import GenerationQueue
from planner_core.ports.password_hasher import PasswordHasher, Pbkdf2PasswordHasher
from planner_core.ports.recipes import RecipeRepository
from planner_core.ports.rules import RuleRepository
from planner_core.ports.shopping_list import ShoppingListRepository
from planner_core.ports.tokens import HmacTokenSigner, TokenSigner
from planner_core.ports.weeks import WeekRepository

logger = logging.getLogger("planner_api")


class NoOpArchiveRepository:
    """Archive is parked for the MVP (owner ruling 2026-08-31, design.md
    section 7): retains nothing, logs the discarded record (R40, R41)."""

    def get(self, week: IsoWeek) -> ArchivedWeek | None:
        return None

    def save(self, archived: ArchivedWeek) -> None:
        logger.info(
            "Discarding archived week (archive parked for MVP)",
            extra={"weekId": archived.week.week_id},
        )


@dataclass(frozen=True)
class Dependencies:
    """Every port a route handler may need, bundled once per invocation."""

    accounts: AccountRepository
    recipes: RecipeRepository
    weeks: WeekRepository
    rules: RuleRepository
    shopping: ShoppingListRepository
    archive: ArchiveRepository
    queue: GenerationQueue
    hasher: PasswordHasher
    signer: TokenSigner
    clock: Clock
    config: ConfigPort


@dataclass(frozen=True)
class AuthorizerDependencies:
    """What the authorizer uses; `Dependencies` satisfies it structurally."""

    accounts: AccountRepository
    signer: TokenSigner
    clock: Clock


@dataclass(frozen=True)
class RolloverDependencies:
    """What the scheduled rollover uses; `Dependencies` satisfies it structurally."""

    weeks: WeekRepository
    shopping: ShoppingListRepository
    archive: ArchiveRepository
    clock: Clock


def _session_signer(cfg: ConfigPort) -> TokenSigner:
    # Adapter imports are lazy so narrow entry points load only what they build.
    from planner_api.adapters.secrets import fetch_session_secret  # noqa: PLC0415

    secret_arn = cfg.get("SESSION_SECRET_ARN")
    secret = fetch_session_secret(secret_arn) if secret_arn else cfg.get("SESSION_SECRET_KEY")
    if secret is None:
        raise RuntimeError("SESSION_SECRET_KEY is not configured")
    return HmacTokenSigner(secret.encode("utf-8"))


def build_authorizer_dependencies(config: ConfigPort | None = None) -> AuthorizerDependencies:
    """Accounts, signer and clock only: no queue, no other repositories."""
    from planner_api.adapters.dynamo.accounts import DynamoAccountRepository  # noqa: PLC0415

    return AuthorizerDependencies(
        accounts=DynamoAccountRepository(),
        signer=_session_signer(config or EnvConfig()),
        clock=SystemClock(),
    )


def build_rollover_dependencies() -> RolloverDependencies:
    """Weeks, shopping, archive and clock only: no signer, secret or queue."""
    from planner_api.adapters.dynamo.shopping_list import (  # noqa: PLC0415
        DynamoShoppingListRepository,
    )
    from planner_api.adapters.dynamo.weeks import DynamoWeekRepository  # noqa: PLC0415

    return RolloverDependencies(
        weeks=DynamoWeekRepository(),
        shopping=DynamoShoppingListRepository(),
        archive=NoOpArchiveRepository(),
        clock=SystemClock(),
    )


def build_dependencies(config: ConfigPort | None = None) -> Dependencies:
    """The real, AWS-backed stack (R10, R32, R35). `config` is injected so a
    deployed function and a local run can source `SESSION_SECRET_KEY`
    differently without a second composition root. `SESSION_SECRET_ARN` wins
    over `SESSION_SECRET_KEY` when both are set."""
    from planner_api.adapters.dynamo.accounts import DynamoAccountRepository  # noqa: PLC0415
    from planner_api.adapters.dynamo.recipes import DynamoRecipeRepository  # noqa: PLC0415
    from planner_api.adapters.dynamo.rules import DynamoRuleRepository  # noqa: PLC0415
    from planner_api.adapters.dynamo.shopping_list import (  # noqa: PLC0415
        DynamoShoppingListRepository,
    )
    from planner_api.adapters.dynamo.weeks import DynamoWeekRepository  # noqa: PLC0415
    from planner_api.adapters.sqs import SqsGenerationQueue  # noqa: PLC0415

    cfg = config or EnvConfig()
    signer = _session_signer(cfg)
    return Dependencies(
        accounts=DynamoAccountRepository(),
        recipes=DynamoRecipeRepository(),
        weeks=DynamoWeekRepository(),
        rules=DynamoRuleRepository(),
        shopping=DynamoShoppingListRepository(),
        archive=NoOpArchiveRepository(),
        queue=SqsGenerationQueue(),
        hasher=Pbkdf2PasswordHasher(),
        signer=signer,
        clock=SystemClock(),
        config=cfg,
    )
