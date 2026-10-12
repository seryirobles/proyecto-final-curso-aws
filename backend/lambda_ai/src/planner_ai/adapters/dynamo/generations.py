"""The `ai` worker's write-back to `PETICIONIA#<idPeticionIA>/METADATA`
(docs/data_model.md section 4.6): `claim` (the idempotent-consumer guard),
`record_result` (single-recipe payload) and the per-slot progress methods.
Mirrors `planner_api.adapters.sqs.SqsGenerationQueue` — the shared contract
suites keep them in step (specs/ai_lambda/design.md section 6,
specs/week_generation_backend/design.md section 2)."""

from __future__ import annotations

import json
from typing import Any

from botocore.exceptions import ClientError
from planner_core.domain.calendar import IsoWeek, MealSlot
from planner_core.domain.generation import (
    GenerationMode,
    GenerationSnapshot,
    RunStatus,
    SlotError,
    SlotProgress,
    SlotStatus,
)
from planner_core.domain.ingredient_category import parse_category
from planner_core.domain.rules import CategoryCountRule, PinRule, RuleSet
from planner_core.ports.generation_queue import ResultPayload, StoredGeneration

from planner_ai.adapters.dynamo import _table

_METADATA_SK = "METADATA"


def _pk(idempotency_key: str) -> str:
    # Adapter boundary: the domain's English `idempotency_key` maps to the
    # persisted `PETICIONIA#<hash>` key here (docs/data_model.md section 2).
    return f"PETICIONIA#{idempotency_key}"


def _slot_key(day: int, slot: int) -> str:
    # docs/data_model.md section 2: the slot-map key is "<day>-<slot>".
    return f"{day}-{slot}"


def _slot_entry(progress: SlotProgress) -> dict[str, str]:
    entry = {"estado": progress.status.value}
    if progress.error is not None:
        entry["codigo"] = progress.error.code
        entry["mensaje"] = progress.error.message
    return entry


def _decode_slots(franjas: dict[str, Any]) -> tuple[SlotProgress, ...]:
    slots: list[SlotProgress] = []
    for key, entry in franjas.items():
        day, slot = (int(part) for part in key.split("-"))
        error = (
            SlotError(str(entry["codigo"]), str(entry["mensaje"])) if "codigo" in entry else None
        )
        slots.append(SlotProgress(day, slot, SlotStatus(str(entry["estado"])), error))
    return tuple(sorted(slots, key=lambda p: (p.day, p.slot)))


def _decode_snapshot(solicitud: dict[str, Any]) -> GenerationSnapshot:
    rules = solicitud["reglas"]
    return GenerationSnapshot(
        week=IsoWeek(*(int(part) for part in str(solicitud["semana"]).split("-W"))),
        mode=GenerationMode(str(solicitud["modo"])),
        rules=RuleSet(
            category_counts=tuple(
                CategoryCountRule(parse_category(str(r["category"])), int(r["count"]))
                for r in rules["categoryCounts"]
            ),
            pins=tuple(
                PinRule(int(p["day"]), MealSlot(int(p["slot"])), str(p["recipeId"]))
                for p in rules["pins"]
            ),
            disabled_days=tuple(int(d) for d in rules["disabledDays"]),
        ),
        prompt_version_id=str(solicitud["versionPrompt"] or ""),
    )


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

    def record_result(self, idempotency_key: str, status: str, payload: ResultPayload) -> None:
        # R14/R39: unconditional UpdateItem — the preceding claim established ownership.
        _table.table().update_item(
            Key={"PK": _pk(idempotency_key), "SK": _METADATA_SK},
            UpdateExpression="SET #estado = :estado, #resultado = :resultado",
            ExpressionAttributeNames={"#estado": "estado", "#resultado": "resultado"},
            ExpressionAttributeValues={":estado": status, ":resultado": json.dumps(payload)},
        )

    def stored_generation(self, idempotency_key: str) -> StoredGeneration | None:
        item = _table.get_item(_pk(idempotency_key), _METADATA_SK, consistent=True)
        if item is None:
            return None
        result = item.get("resultado")
        franjas = item.get("franjas")
        solicitud = item.get("solicitud")
        return StoredGeneration(
            idempotency_key=idempotency_key,
            status=str(item["estado"]),
            result=None if result is None else str(result),
            slots=None if franjas is None else _decode_slots(franjas),
            snapshot=None if solicitud is None else _decode_snapshot(solicitud),
        )

    def begin_slots(self, idempotency_key: str, slots: tuple[SlotProgress, ...]) -> None:
        # R17/R21: one UpdateItem naming each slot path; never a read-modify-write.
        if not slots:
            return
        names = {"#f": "franjas"}
        values: dict[str, Any] = {}
        sets: list[str] = []
        for index, progress in enumerate(slots):
            names[f"#k{index}"] = _slot_key(progress.day, progress.slot)
            values[f":v{index}"] = _slot_entry(progress)
            sets.append(f"#f.#k{index} = :v{index}")
        _table.table().update_item(
            Key={"PK": _pk(idempotency_key), "SK": _METADATA_SK},
            UpdateExpression="SET " + ", ".join(sets),
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
        )

    def record_slot(self, idempotency_key: str, progress: SlotProgress) -> None:
        # R21: unconditional, one slot's entry only — the claim established ownership.
        _table.table().update_item(
            Key={"PK": _pk(idempotency_key), "SK": _METADATA_SK},
            UpdateExpression="SET #f.#k = :v",
            ExpressionAttributeNames={
                "#f": "franjas",
                "#k": _slot_key(progress.day, progress.slot),
            },
            ExpressionAttributeValues={":v": _slot_entry(progress)},
        )

    def claim_slot(self, idempotency_key: str, day: int, slot: int) -> bool:
        # R47: conditional pending -> running on this slot's estado.
        try:
            _table.table().update_item(
                Key={"PK": _pk(idempotency_key), "SK": _METADATA_SK},
                UpdateExpression="SET #f.#k.#e = :running",
                ConditionExpression="#f.#k.#e = :pending",
                ExpressionAttributeNames={
                    "#f": "franjas",
                    "#k": _slot_key(day, slot),
                    "#e": "estado",
                },
                ExpressionAttributeValues={":running": "running", ":pending": "pending"},
            )
        except ClientError as error:
            if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return False
            raise
        return True

    def record_status(self, idempotency_key: str, status: RunStatus) -> None:
        # R27: the run's estado only; resultado is not written for week runs.
        _table.table().update_item(
            Key={"PK": _pk(idempotency_key), "SK": _METADATA_SK},
            UpdateExpression="SET #estado = :estado",
            ExpressionAttributeNames={"#estado": "estado"},
            ExpressionAttributeValues={":estado": status.value},
        )
