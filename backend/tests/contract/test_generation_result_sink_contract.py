"""Contract suite for GenerationResultSink.claim / record_result: the in-memory
fake, the planner_api SQS+PETICIONIA adapter and the planner_ai DynamoDB
write-back all agree (FR-AI-09; specs/ai_lambda/design.md section 6)."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping

import pytest
from planner_core.domain.calendar import IsoWeek, MealSlot
from planner_core.domain.generation import (
    GenerationMode,
    GenerationSnapshot,
    RunStatus,
    SlotError,
    SlotProgress,
    SlotStatus,
)
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.rules import CategoryCountRule, PinRule, RuleSet
from planner_core.ports.generation_queue import GenerationResultSink, StoredGeneration
from support.fakes import FakeGenerationQueue

from tests.contract.dynamo_contract import ai_generation_records, sqs_generation_queue

IMPLEMENTATIONS: list[Callable[[], GenerationResultSink]] = [
    FakeGenerationQueue,
    sqs_generation_queue,
    ai_generation_records,
]

_RESULT: Mapping[str, object] = {"error": {"code": "invalid_output", "message": "x"}}


def _seed_pending(sink: GenerationResultSink, key: str) -> None:
    if isinstance(sink, FakeGenerationQueue):
        sink.stored[key] = StoredGeneration(idempotency_key=key, status="pending")
        return
    from planner_api.adapters.dynamo import _table

    _table.table().put_item(
        Item={"PK": f"PETICIONIA#{key}", "SK": "METADATA", "estado": "pending", "resultado": None}
    )


def _read(sink: GenerationResultSink, key: str) -> tuple[str, object]:
    if isinstance(sink, FakeGenerationQueue):
        record = sink.stored[key]
        return record.status, json.loads(record.result or "null")
    from planner_api.adapters.dynamo import _table

    item = _table.get_item(f"PETICIONIA#{key}", "METADATA")
    assert item is not None
    return str(item["estado"]), json.loads(str(item["resultado"]))


@pytest.mark.parametrize("factory", IMPLEMENTATIONS)
def test_the_first_claim_transitions_pending_and_a_second_fails(
    factory: Callable[[], GenerationResultSink],
) -> None:
    sink = factory()
    _seed_pending(sink, "k")

    assert sink.claim("k") is True
    assert sink.claim("k") is False


@pytest.mark.parametrize("factory", IMPLEMENTATIONS)
def test_claim_of_an_absent_record_returns_false(
    factory: Callable[[], GenerationResultSink],
) -> None:
    assert factory().claim("never-seeded") is False


@pytest.mark.parametrize("factory", IMPLEMENTATIONS)
def test_record_result_writes_the_terminal_status_and_payload(
    factory: Callable[[], GenerationResultSink],
) -> None:
    sink = factory()
    _seed_pending(sink, "k")
    sink.claim("k")

    sink.record_result("k", "failed", _RESULT)

    status, payload = _read(sink, "k")
    assert status == "failed"
    assert payload == _RESULT


@pytest.mark.parametrize("factory", IMPLEMENTATIONS)
def test_record_result_accepts_a_single_recipe_dict_payload(
    factory: Callable[[], GenerationResultSink],
) -> None:
    """specs/single_recipe_generation R23: the bare recipe dict is the payload."""
    sink = factory()
    _seed_pending(sink, "k")
    sink.claim("k")
    recipe = {"name": "Tortilla", "ingredients": [], "tools": ["sarten"]}

    sink.record_result("k", "completed", recipe)

    assert _read(sink, "k") == ("completed", recipe)


# --- per-slot progress (week_generation_backend R17-R21, R27, R47, R52) -----

_SNAPSHOT = GenerationSnapshot(
    IsoWeek(2026, 34),
    GenerationMode.MIX,
    RuleSet(
        category_counts=(CategoryCountRule(IngredientCategory.LEGUME, 2),),
        pins=(PinRule(2, MealSlot.DINNER, "r-1"),),
        disabled_days=(5,),
    ),
    "v1",
)
_ERR = SlotError("invalid_output", "La receta no es válida.")


def _seed_week_run(sink: GenerationResultSink, key: str) -> None:
    if isinstance(sink, FakeGenerationQueue):
        sink.stored[key] = StoredGeneration(key, "pending", slots=(), snapshot=_SNAPSHOT)
        return
    from planner_api.adapters.dynamo import _table

    _table.table().put_item(
        Item={
            "PK": f"PETICIONIA#{key}",
            "SK": "METADATA",
            "estado": "pending",
            "resultado": None,
            "franjas": {},
            "solicitud": {
                "semana": "2026-W34",
                "modo": "mix",
                "reglas": {
                    "categoryCounts": [{"category": "legume", "count": 2}],
                    "pins": [{"day": 2, "slot": 2, "recipeId": "r-1"}],
                    "disabledDays": [5],
                },
                "versionPrompt": "v1",
            },
        }
    )


def _slots(sink: GenerationResultSink, key: str) -> list[tuple[int, int, str]]:
    stored = sink.stored_generation(key)
    assert stored is not None and stored.slots is not None
    return [(p.day, p.slot, p.status.value) for p in stored.slots]


@pytest.mark.parametrize("factory", IMPLEMENTATIONS)
def test_begin_slots_records_every_slot_pending_ordered_by_day_then_slot(
    factory: Callable[[], GenerationResultSink],
) -> None:
    sink = factory()
    _seed_week_run(sink, "k")

    sink.begin_slots(
        "k", tuple(SlotProgress(d, s, SlotStatus.PENDING) for d, s in [(3, 1), (1, 2), (1, 1)])
    )

    assert _slots(sink, "k") == [(1, 1, "pending"), (1, 2, "pending"), (3, 1, "pending")]


@pytest.mark.parametrize("factory", IMPLEMENTATIONS)
def test_begin_slots_with_no_slot_is_a_no_op(
    factory: Callable[[], GenerationResultSink],
) -> None:
    sink = factory()
    _seed_week_run(sink, "k")

    sink.begin_slots("k", ())

    assert _slots(sink, "k") == []


@pytest.mark.parametrize("factory", IMPLEMENTATIONS)
def test_record_slot_changes_only_that_slot_and_round_trips_the_error(
    factory: Callable[[], GenerationResultSink],
) -> None:
    sink = factory()
    _seed_week_run(sink, "k")
    sink.begin_slots(
        "k", (SlotProgress(1, 1, SlotStatus.PENDING), SlotProgress(1, 2, SlotStatus.PENDING))
    )

    sink.record_slot("k", SlotProgress(1, 2, SlotStatus.ERROR, _ERR))

    stored = sink.stored_generation("k")
    assert stored is not None and stored.slots is not None
    assert stored.slots[0] == SlotProgress(1, 1, SlotStatus.PENDING)
    assert stored.slots[1] == SlotProgress(1, 2, SlotStatus.ERROR, _ERR)


@pytest.mark.parametrize("factory", IMPLEMENTATIONS)
def test_a_done_slot_drops_a_previous_error(factory: Callable[[], GenerationResultSink]) -> None:
    sink = factory()
    _seed_week_run(sink, "k")
    sink.begin_slots("k", (SlotProgress(1, 1, SlotStatus.PENDING),))
    sink.record_slot("k", SlotProgress(1, 1, SlotStatus.ERROR, _ERR))

    sink.record_slot("k", SlotProgress(1, 1, SlotStatus.DONE))

    stored = sink.stored_generation("k")
    assert stored is not None and stored.slots == (SlotProgress(1, 1, SlotStatus.DONE),)


@pytest.mark.parametrize("factory", IMPLEMENTATIONS)
def test_claim_slot_moves_pending_to_running_once(
    factory: Callable[[], GenerationResultSink],
) -> None:
    sink = factory()
    _seed_week_run(sink, "k")
    sink.begin_slots("k", (SlotProgress(1, 1, SlotStatus.PENDING),))

    assert sink.claim_slot("k", 1, 1) is True
    assert sink.claim_slot("k", 1, 1) is False
    assert _slots(sink, "k") == [(1, 1, "running")]


@pytest.mark.parametrize("factory", IMPLEMENTATIONS)
def test_claim_slot_of_an_absent_slot_returns_false(
    factory: Callable[[], GenerationResultSink],
) -> None:
    sink = factory()
    _seed_week_run(sink, "k")

    assert sink.claim_slot("k", 4, 2) is False


@pytest.mark.parametrize("factory", IMPLEMENTATIONS)
def test_record_status_writes_the_run_status_and_leaves_the_slots(
    factory: Callable[[], GenerationResultSink],
) -> None:
    sink = factory()
    _seed_week_run(sink, "k")
    sink.begin_slots("k", (SlotProgress(1, 1, SlotStatus.DONE),))

    sink.record_status("k", RunStatus.COMPLETED)

    stored = sink.stored_generation("k")
    assert stored is not None and stored.status == "completed"
    assert _slots(sink, "k") == [(1, 1, "done")]


@pytest.mark.parametrize("factory", IMPLEMENTATIONS)
def test_the_snapshot_round_trips(factory: Callable[[], GenerationResultSink]) -> None:
    sink = factory()
    _seed_week_run(sink, "k")

    stored = sink.stored_generation("k")

    assert stored is not None and stored.snapshot == _SNAPSHOT


def test_the_dynamo_slot_writes_name_only_their_own_slot_path() -> None:
    """R21 — a nested SET, never a read-modify-write of the whole map."""
    import inspect

    from planner_ai.adapters.dynamo.generations import DynamoGenerationRecords

    code = "\n".join(
        line
        for line in inspect.getsource(DynamoGenerationRecords.record_slot).splitlines()
        if not line.lstrip().startswith("#")
    )
    assert "SET #f.#k = :v" in code and "get_item" not in code
