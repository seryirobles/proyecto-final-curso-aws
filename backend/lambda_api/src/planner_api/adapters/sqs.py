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
from planner_core.domain.calendar import IsoWeek, MealSlot
from planner_core.domain.generation import (
    GenerationMode,
    GenerationRequest,
    GenerationSnapshot,
    RuleOverride,
    RunStatus,
    SingleRecipeRequest,
    SlotError,
    SlotProgress,
    SlotStatus,
    SpecificationSource,
    run_status,
)
from planner_core.domain.ingredient_category import parse_category
from planner_core.domain.recipe import Recipe
from planner_core.domain.rules import CategoryCountRule, PinRule, RuleSet
from planner_core.ports.generation_queue import ResultPayload, SlotNotRetryable, StoredGeneration

from planner_api.adapters.dynamo import _table
from planner_api.serialization import encode_recipe

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


def _recipe_message(
    idempotency_key: str,
    request: SingleRecipeRequest,
    reference_recipe: Recipe | None,
    prompt_version_id: str,
    author: str,
) -> dict[str, Any]:
    target = request.target
    source = request.source
    return {
        "type": "recipe",
        "idPeticionIA": idempotency_key,
        "target": {"kind": "library"}
        if target is None
        else {
            "kind": "slot",
            "weekId": IsoWeek.containing(target.day).week_id,
            "day": target.day_number,
            "slot": int(target.slot.value),
        },
        "source": {
            "kind": "specification",
            "ingredients": list(source.ingredients),
            "tools": list(source.tools),
        }
        if isinstance(source, SpecificationSource)
        else {
            "kind": "reference",
            "recipeId": source.recipe_id,
            "extraSpecifications": list(source.extra_specifications),
        },
        "referenceRecipe": None if reference_recipe is None else encode_recipe(reference_recipe),
        "promptVersionId": prompt_version_id,
        "authorUserId": author,
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
        franjas = item.get("franjas")
        solicitud = item.get("solicitud")
        return StoredGeneration(
            idempotency_key=idempotency_key,
            status=str(item["estado"]),
            result=None if result is None else str(result),
            slots=None if franjas is None else _decode_slots(franjas),
            snapshot=None if solicitud is None else _decode_snapshot(solicitud),
        )

    def _put_pending(self, idempotency_key: str, week_run: dict[str, Any] | None = None) -> None:
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
                    **(week_run or {}),
                },
                ConditionExpression="attribute_not_exists(PK)",
            )
        except ClientError as error:
            if error.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise

    def submit(
        self,
        idempotency_key: str,
        request: GenerationRequest,
        *,
        effective_rules: RuleSet,
        prompt_version_id: str | None = None,
        author: str | None = None,
    ) -> None:
        # `franjas` starts empty (a nested SET needs the parent map) and `solicitud`
        # stores the resolved run so a retry reproduces it (R34, design.md section 2).
        self._put_pending(
            idempotency_key,
            {
                "franjas": {},
                "solicitud": {
                    "semana": request.week.week_id,
                    "modo": request.mode.value,
                    "reglas": _rule_set_payload(effective_rules),
                    "versionPrompt": prompt_version_id,
                },
            },
        )
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

    def submit_recipe(
        self,
        idempotency_key: str,
        request: SingleRecipeRequest,
        *,
        reference_recipe: Recipe | None,
        prompt_version_id: str,
        author: str,
    ) -> None:
        self._put_pending(idempotency_key)
        self._sqs().send_message(
            QueueUrl=self._queue_url,
            MessageBody=json.dumps(
                _recipe_message(
                    idempotency_key, request, reference_recipe, prompt_version_id, author
                )
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

    def record_result(self, idempotency_key: str, status: str, payload: ResultPayload) -> None:
        # R38/R39: unconditional UpdateItem — the preceding claim established ownership.
        _table.table().update_item(
            Key={"PK": _pk(idempotency_key), "SK": _METADATA_SK},
            UpdateExpression="SET #estado = :estado, #resultado = :resultado",
            ExpressionAttributeNames={"#estado": "estado", "#resultado": "resultado"},
            ExpressionAttributeValues={":estado": status, ":resultado": json.dumps(payload)},
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
        # R21: unconditional, one slot's entry only.
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

    def retry_slot(self, idempotency_key: str, day: int, slot: int, *, author: str) -> None:
        # R36/R40: ONE conditional write; exactly one of two racing retries sees `error`.
        try:
            response = _table.table().update_item(
                Key={"PK": _pk(idempotency_key), "SK": _METADATA_SK},
                UpdateExpression="SET #f.#k = :pending, #s = :running",
                ConditionExpression="#f.#k.#e = :error",
                ExpressionAttributeNames={
                    "#f": "franjas",
                    "#k": _slot_key(day, slot),
                    "#e": "estado",
                    "#s": "estado",
                },
                ExpressionAttributeValues={
                    ":pending": {"estado": "pending"},
                    ":running": "running",
                    ":error": "error",
                },
                ReturnValues="ALL_OLD",
            )
        except ClientError as error:
            if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise SlotNotRetryable(_slot_key(day, slot)) from error
            raise
        old = response["Attributes"]
        previous = old["franjas"][_slot_key(day, slot)]  # keeps codigo/mensaje for a restore
        snapshot = _decode_snapshot(old["solicitud"])
        try:
            self._sqs().send_message(
                QueueUrl=self._queue_url,
                MessageBody=json.dumps(
                    {
                        "type": "slot_retry",
                        "idPeticionIA": idempotency_key,
                        "day": day,
                        "slot": slot,
                        "weekId": snapshot.week.week_id,
                        "mode": snapshot.mode.value,
                        "effectiveRules": _rule_set_payload(snapshot.rules),
                        "promptVersionId": snapshot.prompt_version_id,
                        "authorUserId": author,
                    }
                ),
            )
        except Exception:
            self._restore_error(idempotency_key, day, slot, previous)  # R46
            raise

    def _restore_error(
        self, idempotency_key: str, day: int, slot: int, previous: dict[str, Any]
    ) -> None:
        """Put the slot back to `error` and recompute the run status (R46)."""
        _table.table().update_item(
            Key={"PK": _pk(idempotency_key), "SK": _METADATA_SK},
            UpdateExpression="SET #f.#k = :previous",
            ExpressionAttributeNames={"#f": "franjas", "#k": _slot_key(day, slot)},
            ExpressionAttributeValues={":previous": previous},
        )
        stored = self.stored_generation(idempotency_key)
        if stored is not None:
            self.record_status(idempotency_key, run_status(stored.slots or ()))
