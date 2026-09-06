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

from planner_api.adapters.dynamo.accounts import DynamoAccountRepository
from planner_api.adapters.dynamo.recipes import DynamoRecipeRepository
from planner_api.adapters.dynamo.rules import DynamoRuleRepository
from planner_api.adapters.dynamo.shopping_list import DynamoShoppingListRepository
from planner_api.adapters.dynamo.weeks import DynamoWeekRepository
from planner_api.adapters.sqs import SqsGenerationQueue

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


def build_dependencies(config: ConfigPort | None = None) -> Dependencies:
    """The real, AWS-backed stack (R10, R32, R35). `config` is injected so a
    deployed function and a local run can source `SESSION_SECRET_KEY`
    differently without a second composition root."""
    cfg = config or EnvConfig()
    secret = cfg.get("SESSION_SECRET_KEY")
    if secret is None:
        raise RuntimeError("SESSION_SECRET_KEY is not configured")
    return Dependencies(
        accounts=DynamoAccountRepository(),
        recipes=DynamoRecipeRepository(),
        weeks=DynamoWeekRepository(),
        rules=DynamoRuleRepository(),
        shopping=DynamoShoppingListRepository(),
        archive=NoOpArchiveRepository(),
        queue=SqsGenerationQueue(),
        hasher=Pbkdf2PasswordHasher(),
        signer=HmacTokenSigner(secret.encode("utf-8")),
        clock=SystemClock(),
        config=cfg,
    )
