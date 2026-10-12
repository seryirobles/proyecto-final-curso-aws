"""The ai worker handler: one use-case run per SQS record, per-record isolation
(R1, R4)."""

from __future__ import annotations

import dataclasses
import json

from planner_core.domain.calendar import IsoWeek
from support.fakes import (
    FakeAiProvider,
    FakeClock,
    FakeGenerationGate,
    FakeGenerationQueue,
    FakeRecipeRepository,
    FakeWeekRepository,
)

from planner_ai.handler import handle
from planner_ai.wiring import Dependencies


def _deps(queue: FakeGenerationQueue, weeks: FakeWeekRepository) -> Dependencies:
    return Dependencies(
        provider=FakeAiProvider(),
        weeks=weeks,
        recipes=FakeRecipeRepository(),
        records=queue,
        gate=FakeGenerationGate(),
        clock=FakeClock.at("2026-08-17T10:00:00+00:00"),
    )


def _body(key: str, week_id: str) -> str:
    return json.dumps(
        {
            "idPeticionIA": key,
            "weekId": week_id,
            "mode": "mix",
            "promptVersionId": "v1",
            "authorUserId": "u-1",
            "effectiveRules": {},
        }
    )


def test_a_two_record_batch_runs_both_and_isolates_a_failure() -> None:
    from planner_core.ports.generation_queue import StoredGeneration

    queue = FakeGenerationQueue()
    queue.stored["k1"] = StoredGeneration(idempotency_key="k1", status="pending")
    queue.stored["k2"] = StoredGeneration(idempotency_key="k2", status="pending")
    weeks = FakeWeekRepository()
    event = {
        "Records": [
            {"body": _body("k1", "not-a-week")},  # malformed — parse raises before any claim
            {"body": _body("k2", "2026-W34")},
        ]
    }

    handle(event, _deps(queue, weeks))

    assert queue.claims == ["k2"]  # k1 never reached claim; k2 processed (R4)
    assert queue.stored["k2"].status == "completed"
    assert queue.stored["k1"].status == "pending"  # untouched


def test_each_record_is_one_use_case_run() -> None:
    from planner_core.ports.generation_queue import StoredGeneration

    queue = FakeGenerationQueue()
    queue.stored["k1"] = StoredGeneration(idempotency_key="k1", status="pending")
    queue.stored["k2"] = StoredGeneration(idempotency_key="k2", status="pending")
    weeks = FakeWeekRepository()
    event = {"Records": [{"body": _body("k1", "2026-W34")}, {"body": _body("k2", "2026-W35")}]}

    handle(event, _deps(queue, weeks))

    assert set(queue.claims) == {"k1", "k2"}
    assert {queue.stored[k].status for k in ("k1", "k2")} == {"completed"}  # one settled run each


def _retry_body(key: str = "k1", day: int = 7, slot: int = 1) -> str:
    return json.dumps(
        {
            "type": "slot_retry",
            "idPeticionIA": key,
            "day": day,
            "slot": slot,
            "weekId": "2026-W34",
            "mode": "mix",
            "promptVersionId": "v1",
            "authorUserId": "u-2",
            "effectiveRules": {},
        }
    )


def _pending_retry_run() -> FakeGenerationQueue:
    from planner_core.domain.generation import SlotProgress, SlotStatus
    from planner_core.ports.generation_queue import StoredGeneration

    queue = FakeGenerationQueue()
    queue.stored["k1"] = StoredGeneration(
        idempotency_key="k1",
        status="running",
        slots=(SlotProgress(7, 1, SlotStatus.PENDING), SlotProgress(7, 2, SlotStatus.DONE)),
    )
    return queue


def test_a_slot_retry_record_runs_the_slot_and_settles_the_run() -> None:
    """R47-R53 — the `slot_retry` branch reaches run_slot_retry."""
    queue = _pending_retry_run()
    weeks = FakeWeekRepository()

    handle({"Records": [{"body": _retry_body()}]}, _deps(queue, weeks))

    assert queue.stored["k1"].status == "completed"
    candidates = [c for s in weeks.get_week(IsoWeek(2026, 34)).values() for c in s.candidates]
    assert [c.author for c in candidates] == ["u-2"]  # R53


def test_a_malformed_slot_retry_is_isolated_and_touches_nothing() -> None:
    queue = _pending_retry_run()

    handle({"Records": [{"body": _retry_body(day=9)}]}, _deps(queue, FakeWeekRepository()))

    assert queue.stored["k1"].status == "running"


def test_a_library_only_slot_retry_never_calls_the_provider() -> None:
    """R49 — the parent's mode rides the message."""
    from planner_core.domain.ingredient_category import IngredientCategory
    from planner_core.domain.recipe import Recipe
    from planner_core.ports.recipes import LibraryRecipe

    queue = _pending_retry_run()
    provider = FakeAiProvider()
    recipes = FakeRecipeRepository()
    recipe = Recipe("Lentejas", (), ("olla",), ("x",), IngredientCategory.LEGUME)
    recipes.save(LibraryRecipe("r", recipe, "chef"))
    deps = dataclasses.replace(
        _deps(queue, FakeWeekRepository()), provider=provider, recipes=recipes
    )
    body = json.loads(_retry_body())
    body["mode"] = "library_only"

    handle({"Records": [{"body": json.dumps(body)}]}, deps)

    assert provider.calls == 0
    assert queue.stored["k1"].status == "completed"
