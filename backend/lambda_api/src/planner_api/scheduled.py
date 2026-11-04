"""Non-HTTP entry point for scheduled week rollover (R32-R34), invoked by
EventBridge Scheduler (docs/rest_api_contract.md section 7 Q8). Promotion and
next-week initialisation are no-ops at the storage layer - `idSemana` is
derived from the clock, never stored - so only the archive snapshot and the
`FR-SHOP-09` cleanup survive (docs/data_model.md section 9)."""

from __future__ import annotations

import logging
from typing import Any  # untyped JSON in/out is the wire boundary itself (conventions.md)

from planner_core.domain.calendar import civil_date, current_week, next_week
from planner_core.domain.rollover import roll_over

from planner_api.wiring import Dependencies, RolloverDependencies, build_rollover_dependencies

logger = logging.getLogger("planner_api")


def handle(
    event: dict[str, Any], deps: RolloverDependencies | Dependencies | None = None
) -> dict[str, Any]:
    """R34 - re-running for the same boundary repeats the same read-only
    archive snapshot and calls the already-idempotent `delete_checked_items`
    (feature 8), so a second invocation changes nothing further."""
    resolved = deps if deps is not None else build_rollover_dependencies()
    today = civil_date(resolved.clock.now())
    ending_week = current_week(today)

    plans = resolved.weeks.get_week(ending_week)
    next_plans = resolved.weeks.get_week(next_week(today))
    shopping_items = resolved.shopping.list_items()

    result = roll_over(ending_week, plans, next_plans, shopping_items)
    resolved.archive.save(result.archived)
    resolved.shopping.delete_checked_items()

    logger.info(
        "Rollover completed for week %s", ending_week.week_id, extra={"weekId": ending_week.week_id}
    )
    return {"status": "ok", "archivedWeekId": ending_week.week_id}


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda entry point; `context` is not the deps bundle (issue 22)."""
    return handle(event)
