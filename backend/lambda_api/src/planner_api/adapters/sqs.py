"""SQS-backed `GenerationQueue`: the `api` -> `ai` producer (docs/architecture.md
section 1.2, docs/rest_api_contract.md section 7 Q12), plus the AP25/AP26
idempotency record on `PETICIONIA#<idPeticionIA>` (docs/data_model.md section 4.6)."""

from __future__ import annotations

import json
import os
import time
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from planner_core.domain.generation import GenerationRequest, RuleOverride
from planner_core.domain.rules import RuleSet
from planner_core.ports.generation_queue import PerSlotResult, StoredGeneration

from planner_api.adapters.dynamo import _table

_RESULT_TTL_SECONDS = 7 * 24 * 3600
_METADATA_SK = "METADATA"
_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
# Same local-override pattern as _table.py's DYNAMODB_ENDPOINT_URL: unset ->
# real AWS, set -> a local queue emulator with a short fail-fast timeout.
_ENDPOINT_URL = os.environ.get("SQS_ENDPOINT_URL")
_CONFIG = (
    Config(connect_timeout=2, read_timeout=2, retries={"max_attempts": 1})
    if _ENDPOINT_URL
    else None
)


def _pk(idempotency_key: str) -> str:
    # Adapter boundary: the domain's English `idempotency_key` maps to the
    # persisted `PETICIONIA#<hash>` key here (docs/data_model.md section 2).
    return f"PETICIONIA#{idempotency_key}"


def _override_payload(override: RuleOverride | None) -> dict[str, Any] | None:
    if override is None:
        return None
    return {
        "categoryCounts": None
        if override.category_counts is None
        else [{"category": r.category.value, "count": r.count} for r in override.category_counts],
        "pins": None
        if override.pins is None
        else [{"day": p.day, "slot": p.slot.value, "recipeId": p.recipe_id} for p in override.pins],
        "disabledDays": None if override.disabled_days is None else list(override.disabled_days),
    }


def _rule_set_payload(rules: RuleSet) -> dict[str, Any]:
    # R40: the resolved effective rules travel on the message so the worker
    # generates against exactly what idPeticionIA was hashed from (design.md section 8).
    return {
        "categoryCounts": [
            {"category": r.category.value, "count": r.count} for r in rules.category_counts
        ],
        "pins": [
            {"day": p.day, "slot": int(p.slot.value), "recipeId": p.recipe_id} for p in rules.pins
        ],
        "disabledDays": list(rules.disabled_days),
    }


class SqsGenerationQueue:
    """queue_url comes from configuration (feature 16's wiring passes it in)."""

    def __init__(self, queue_url: str | None = None) -> None:
        self._queue_url = queue_url or os.environ["GENERATION_QUEUE_URL"]

    def _sqs(self) -> Any:
        # boto3 ships no type stubs, so the client handle is untyped
        # (docs/conventions.md — no bare `Any` without a justification).
        return boto3.client("sqs", region_name=_REGION, endpoint_url=_ENDPOINT_URL, config=_CONFIG)

    def stored_generation(self, idempotency_key: str) -> StoredGeneration | None:
        item = _table.get_item(_pk(idempotency_key), _METADATA_SK, consistent=True)
        if item is None:
            return None
        result = item.get("resultado")
        return StoredGeneration(
            idempotency_key=idempotency_key,
            status=str(item["estado"]),
            result=None if result is None else str(result),
        )

    def submit(
        self,
        idempotency_key: str,
        request: GenerationRequest,
        *,
        effective_rules: RuleSet,
        prompt_version_id: str | None = None,
        author: str | None = None,
    ) -> None:
        # Create-if-absent, mirroring FakeGenerationQueue's setdefault: a concurrent
        # resubmit must never clobber a stored result (docs/data_model.md section 4.6).
        try:
            _table.table().put_item(
                Item={
                    "PK": _pk(idempotency_key),
                    "SK": _METADATA_SK,
                    "estado": "pending",
                    "resultado": None,
                    "ttl": int(time.time()) + _RESULT_TTL_SECONDS,
                },
                ConditionExpression="attribute_not_exists(PK)",
            )
        except ClientError as error:
            if error.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise
        self._sqs().send_message(
            QueueUrl=self._queue_url,
            MessageBody=json.dumps(
                {
                    "idPeticionIA": idempotency_key,
                    "weekId": request.week.week_id,
                    "mode": request.mode.value,
                    "ruleOverride": _override_payload(request.rule_override),
                    "effectiveRules": _rule_set_payload(effective_rules),
                    "promptVersionId": prompt_version_id,
                    "authorUserId": author,
                }
            ),
        )

    def discard(self, idempotency_key: str) -> None:
        # Unconditional DeleteItem on PETICIONIA#<hash>/METADATA (R32, AP27):
        # unconditional, so an absent key succeeds silently (R33).
        _table.table().delete_item(Key={"PK": _pk(idempotency_key), "SK": _METADATA_SK})

    def claim(self, idempotency_key: str) -> bool:
        # R36/R37: conditional pending -> running; ConditionalCheckFailed -> False.
        # Alias every non-key name (docs/data_model.md L240-242, fix-round-4 precedent).
        try:
            _table.table().update_item(
                Key={"PK": _pk(idempotency_key), "SK": _METADATA_SK},
                UpdateExpression="SET #estado = :running",
                ConditionExpression="#estado = :pending",
                ExpressionAttributeNames={"#estado": "estado"},
                ExpressionAttributeValues={":running": "running", ":pending": "pending"},
            )
        except ClientError as error:
            if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return False
            raise
        return True

    def record_result(
        self, idempotency_key: str, status: str, per_slot: list[PerSlotResult]
    ) -> None:
        # R38/R39: unconditional UpdateItem — the preceding claim established ownership.
        _table.table().update_item(
            Key={"PK": _pk(idempotency_key), "SK": _METADATA_SK},
            UpdateExpression="SET #estado = :estado, #resultado = :resultado",
            ExpressionAttributeNames={"#estado": "estado", "#resultado": "resultado"},
            ExpressionAttributeValues={":estado": status, ":resultado": json.dumps(per_slot)},
        )
