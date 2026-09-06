"""SQS-backed `GenerationQueue`: the `api` -> `ai` producer (docs/architecture.md
section 1.2, docs/rest_api_contract.md section 7 Q12), plus the AP25/AP26
idempotency record on `PETICIONIA#<idPeticionIA>` (docs/data_model.md section 4.6)."""

from __future__ import annotations

import json
import os
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError
from planner_core.domain.generation import GenerationRequest, RuleOverride
from planner_core.ports.generation_queue import StoredGeneration

from planner_api.adapters.dynamo import _table

_RESULT_TTL_SECONDS = 7 * 24 * 3600
_METADATA_SK = "METADATA"
_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


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


class SqsGenerationQueue:
    """queue_url comes from configuration (feature 16's wiring passes it in)."""

    def __init__(self, queue_url: str | None = None) -> None:
        self._queue_url = queue_url or os.environ["GENERATION_QUEUE_URL"]

    def _sqs(self) -> Any:
        # boto3 ships no type stubs, so the client handle is untyped
        # (docs/conventions.md — no bare `Any` without a justification).
        return boto3.client("sqs", region_name=_REGION)

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

    def submit(self, idempotency_key: str, request: GenerationRequest) -> None:
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
                }
            ),
        )

    def discard(self, idempotency_key: str) -> None:
        # Unconditional DeleteItem on PETICIONIA#<hash>/METADATA (R32, AP27):
        # unconditional, so an absent key succeeds silently (R33).
        _table.table().delete_item(Key={"PK": _pk(idempotency_key), "SK": _METADATA_SK})
