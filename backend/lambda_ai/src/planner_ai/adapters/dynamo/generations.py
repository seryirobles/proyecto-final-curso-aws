"""The `ai` worker's write-back to `PETICIONIA#<idPeticionIA>/METADATA`
(docs/data_model.md section 4.6): `claim` (the idempotent-consumer guard) and
`record_result` (the terminal status + per-slot payload). Mirrors
`planner_api.adapters.sqs.SqsGenerationQueue`'s two methods — the shared
`GenerationQueue` contract suite keeps them in step (specs/ai_lambda/design.md
section 6)."""

from __future__ import annotations

import json

from botocore.exceptions import ClientError
from planner_core.ports.generation_queue import PerSlotResult

from planner_ai.adapters.dynamo import _table

_METADATA_SK = "METADATA"


def _pk(idempotency_key: str) -> str:
    # Adapter boundary: the domain's English `idempotency_key` maps to the
    # persisted `PETICIONIA#<hash>` key here (docs/data_model.md section 2).
    return f"PETICIONIA#{idempotency_key}"


class DynamoGenerationRecords:
    """A `GenerationResultSink`: the two writes the worker makes to the
    idempotency record. No SQS — this Lambda is the consumer, not a producer."""

    def claim(self, idempotency_key: str) -> bool:
        # R11/R37: conditional pending -> running; ConditionalCheckFailed -> False.
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
        # R14/R39: unconditional UpdateItem — the preceding claim established ownership.
        _table.table().update_item(
            Key={"PK": _pk(idempotency_key), "SK": _METADATA_SK},
            UpdateExpression="SET #estado = :estado, #resultado = :resultado",
            ExpressionAttributeNames={"#estado": "estado", "#resultado": "resultado"},
            ExpressionAttributeValues={":estado": status, ":resultado": json.dumps(per_slot)},
        )
