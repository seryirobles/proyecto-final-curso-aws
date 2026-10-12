"""The `ai` worker's SQS entry point (docs/conventions.md — thin: parse the
event, call one use case per record, map nothing). Each record is processed
independently so one failure does not abort the batch (R1, R4)."""

from __future__ import annotations

import json
import logging
from typing import Any

from planner_core.application.single_recipe_generation import run_single_recipe_generation
from planner_core.application.week_generation import run_slot_retry, run_week_generation
from planner_core.domain.calendar import civil_date

from planner_ai.message import (
    MalformedMessage,
    message_type,
    parse_message,
    parse_recipe_message,
    parse_slot_retry_message,
)
from planner_ai.serialization import encode_recipe
from planner_ai.wiring import Dependencies, build_dependencies

logger = logging.getLogger("planner_ai")


def _process_recipe(body: dict[str, Any], deps: Dependencies) -> None:
    recipe_message = parse_recipe_message(body)
    outcome = run_single_recipe_generation(
        recipe_message.idempotency_key,
        recipe_message.source,
        recipe_message.prompt_version_id,
        provider=deps.provider,
        queue=deps.records,
        gate=deps.gate,
        encode_recipe=encode_recipe,
    )
    logger.info(
        "Processed single-recipe generation %s",
        recipe_message.idempotency_key,
        extra={"idPeticionIA": recipe_message.idempotency_key, "claimed": outcome.claimed},
    )


def _process_slot_retry(body: dict[str, Any], deps: Dependencies) -> None:
    retry = parse_slot_retry_message(body)
    message = retry.generation
    outcome = run_slot_retry(
        message.idempotency_key,
        retry.day,
        retry.slot,
        message.request,
        message.effective_rules,
        message.prompt_version_id,
        message.author,
        civil_date(deps.clock.now()),
        provider=deps.provider,
        weeks=deps.weeks,
        recipes=deps.recipes,
        queue=deps.records,
        gate=deps.gate,
    )
    logger.info(
        "Processed slot retry %s",
        message.idempotency_key,
        extra={
            "idPeticionIA": message.idempotency_key,
            "claimed": outcome.claimed,
            "day": retry.day,
            "slot": retry.slot,
        },
    )


def _process_record(record: dict[str, Any], deps: Dependencies) -> None:
    body = json.loads(record["body"])
    kind = message_type(body)
    if kind == "recipe":
        _process_recipe(body, deps)
        return
    if kind == "slot_retry":
        _process_slot_retry(body, deps)
        return
    if kind != "week":
        raise MalformedMessage(f"type: {kind!r}")
    message = parse_message(body)
    first_day = civil_date(deps.clock.now())
    outcome = run_week_generation(
        message.idempotency_key,
        message.request,
        message.effective_rules,
        message.prompt_version_id,
        message.author,
        first_day,
        provider=deps.provider,
        weeks=deps.weeks,
        recipes=deps.recipes,
        queue=deps.records,
        gate=deps.gate,
    )
    logger.info(
        "Processed generation request %s",
        message.idempotency_key,
        extra={
            "idPeticionIA": message.idempotency_key,
            "claimed": outcome.claimed,
            "slots": len(outcome.per_slot),
        },
    )


def handle(event: dict[str, Any], deps: Dependencies | None = None) -> None:
    """`deps` is injected by tests; a deployed function resolves the real stack."""
    resolved = deps or build_dependencies()
    for record in event.get("Records", []):
        try:
            _process_record(record, resolved)
        except Exception:  # per-record isolation — one bad message never blocks the rest (R4)
            logger.exception("Failed to process SQS record")


lambda_handler = handle
