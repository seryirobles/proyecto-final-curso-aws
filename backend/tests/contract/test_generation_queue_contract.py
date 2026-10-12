"""Contract suite for GenerationQueue: the in-memory fake and the moto-backed
SQS + PETICIONIA adapter agree on the idempotency-record surface (FR-AI-08)."""

from __future__ import annotations

import inspect
import json
from collections.abc import Callable, Mapping

import pytest
from planner_core.domain.calendar import IsoWeek, MealSlot
from planner_core.domain.generation import (
    GenerationMode,
    GenerationRequest,
    GenerationSnapshot,
    ReferenceSource,
    RunStatus,
    SingleRecipeRequest,
    SlotError,
    SlotProgress,
    SlotStatus,
    SpecificationSource,
)
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.rules import CategoryCountRule, PinRule, RuleSet
from planner_core.ports.generation_queue import GenerationQueue, SlotNotRetryable, StoredGeneration
from support.fakes import FakeGenerationQueue

from tests.contract.dynamo_contract import received_generation_messages, sqs_generation_queue

IMPLEMENTATIONS: list[Callable[[], GenerationQueue]] = [FakeGenerationQueue, sqs_generation_queue]

REQUEST = GenerationRequest(week=IsoWeek(2026, 34), mode=GenerationMode.MIX)


def _force_done(queue: GenerationQueue, idempotency_key: str, result: str) -> None:
    """Advance the stored record as the ai worker would (feature 17), so a
    resubmit can be checked for clobbering (docs/data_model.md section 4.6)."""
    if isinstance(queue, FakeGenerationQueue):
        queue.stored[idempotency_key] = StoredGeneration(idempotency_key, "done", result)
    else:
        from planner_api.adapters.dynamo import _table

        _table.table().put_item(
            Item={
                "PK": f"PETICIONIA#{idempotency_key}",
                "SK": "METADATA",
                "estado": "done",
                "resultado": result,
            }
        )


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_stored_generation_is_none_for_an_unknown_id(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    assert queue_factory().stored_generation("unknown") is None


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_submit_creates_a_readable_record(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    queue = queue_factory()

    queue.submit("hash-1", REQUEST, effective_rules=RuleSet())

    stored = queue.stored_generation("hash-1")
    assert stored is not None
    assert stored.idempotency_key == "hash-1"
    assert stored.status == "pending"


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_resubmit_never_clobbers_a_stored_result(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    """FR-AI-08 / docs/data_model.md section 4.6 — losing the payload means
    paying for a result that then exists nowhere; submit is create-if-absent."""
    queue = queue_factory()
    queue.submit("hash-1", REQUEST, effective_rules=RuleSet())
    _force_done(queue, "hash-1", '{"ok": true}')

    queue.submit("hash-1", REQUEST, effective_rules=RuleSet())

    assert queue.stored_generation("hash-1") == StoredGeneration("hash-1", "done", '{"ok": true}')


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_discard_removes_a_stored_record(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    """R31/R32 (AP27) — submit then discard leaves no stored record."""
    queue = queue_factory()
    queue.submit("hash-1", REQUEST, effective_rules=RuleSet())

    queue.discard("hash-1")

    assert queue.stored_generation("hash-1") is None


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_discard_of_an_unknown_id_does_not_raise(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    """R33 — an unconditional DeleteItem; an absent key succeeds silently."""
    queue_factory().discard("never-stored")


def test_the_sqs_discard_passes_no_condition_expression() -> None:
    """R32/R33 — the adapter's discard is an unconditional DeleteItem, so an
    absent key succeeds silently."""
    from planner_api.adapters.sqs import SqsGenerationQueue

    source = inspect.getsource(SqsGenerationQueue.discard)
    code = "".join(line.split("#", 1)[0] for line in source.splitlines())
    assert "ConditionExpression" not in code


# --- R36-R39: claim / record_result -----------------------------------------

_PER_SLOT: list[Mapping[str, object]] = [
    {"day": 1, "slot": 1, "status": "completed", "message": None}
]


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_the_first_claim_after_submit_wins_and_a_redelivery_loses(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    """R36/R37 — pending -> running is applied once; a redelivered message finds
    it already claimed."""
    queue = queue_factory()
    queue.submit("hash-1", REQUEST, effective_rules=RuleSet())

    assert queue.claim("hash-1") is True
    assert queue.claim("hash-1") is False


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_claim_of_an_absent_record_returns_false(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    """R37 — an already-claimed or absent record is not claimable."""
    assert queue_factory().claim("never-submitted") is False


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_record_result_writes_the_terminal_status_and_per_slot_payload(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    """R38 — a later stored_generation reports the recorded estado + resultado."""
    queue = queue_factory()
    queue.submit("hash-1", REQUEST, effective_rules=RuleSet())
    queue.claim("hash-1")

    queue.record_result("hash-1", "completed", _PER_SLOT)

    stored = queue.stored_generation("hash-1")
    assert stored is not None
    assert stored.status == "completed"
    assert stored.result is not None and json.loads(stored.result) == _PER_SLOT


def _statement_lines(source: str) -> str:
    """Drop full-line comments; keep code (DynamoDB `#alias` names have a `#`)."""
    return "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("#"))


def test_the_sqs_record_result_passes_no_condition_expression() -> None:
    """R39 — record_result is unconditional; the preceding claim owns the item."""
    from planner_api.adapters.sqs import SqsGenerationQueue

    code = _statement_lines(inspect.getsource(SqsGenerationQueue.record_result))
    assert "ConditionExpression" not in code


def test_the_sqs_claim_conditions_only_on_estado_never_the_marker() -> None:
    """R37 / design.md section 9 — claim's one write-precondition is on estado."""
    from planner_api.adapters.sqs import SqsGenerationQueue

    code = _statement_lines(inspect.getsource(SqsGenerationQueue.claim))
    assert 'ConditionExpression="#estado = :pending"' in code
    assert "marca" not in code.lower()


# --- single-recipe hand-off (specs/single_recipe_generation R1, R2, R23, R26) ---

RECIPE_REQUEST = SingleRecipeRequest(None, SpecificationSource(("lentejas",), ("olla",)))


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_submit_recipe_creates_a_readable_pending_record(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    queue = queue_factory()

    queue.submit_recipe(
        "hash-r", RECIPE_REQUEST, reference_recipe=None, prompt_version_id="v1", author="u-1"
    )

    stored = queue.stored_generation("hash-r")
    assert stored is not None and stored.status == "pending"


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_submit_recipe_never_clobbers_a_stored_result(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    queue = queue_factory()
    queue.submit_recipe(
        "hash-r", RECIPE_REQUEST, reference_recipe=None, prompt_version_id="v1", author="u-1"
    )
    _force_done(queue, "hash-r", '{"ok": true}')

    queue.submit_recipe(
        "hash-r", RECIPE_REQUEST, reference_recipe=None, prompt_version_id="v1", author="u-1"
    )

    assert queue.stored_generation("hash-r") == StoredGeneration("hash-r", "done", '{"ok": true}')


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_record_result_accepts_a_single_recipe_dict_payload(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    queue = queue_factory()
    queue.submit_recipe(
        "hash-r", RECIPE_REQUEST, reference_recipe=None, prompt_version_id="v1", author="u-1"
    )
    queue.claim("hash-r")
    payload = {"error": {"code": "invalid_output", "message": "x"}}

    queue.record_result("hash-r", "failed", payload)

    stored = queue.stored_generation("hash-r")
    assert stored is not None and stored.status == "failed"
    assert stored.result is not None and json.loads(stored.result) == payload


def test_the_sqs_recipe_message_carries_type_source_and_reference_snapshot() -> None:
    """R2 — the worker holds no RecipeRepository, so the snapshot rides the message."""
    from planner_core.domain.ingredient_category import IngredientCategory
    from planner_core.domain.recipe import Recipe

    queue = sqs_generation_queue()
    recipe = Recipe(
        name="Tortilla",
        ingredients=(),
        tools=("sarten",),
        procedure=(),
        category=IngredientCategory.MEAT,
    )
    request = SingleRecipeRequest(None, ReferenceSource("r1", ("sin gluten",)))

    queue.submit_recipe(
        "hash-r", request, reference_recipe=recipe, prompt_version_id="v1", author="u-1"
    )

    body = json.loads(received_generation_messages()[0])
    assert body["type"] == "recipe" and body["idPeticionIA"] == "hash-r"
    assert body["target"] == {"kind": "library"}
    assert body["source"] == {
        "kind": "reference",
        "recipeId": "r1",
        "extraSpecifications": ["sin gluten"],
    }
    assert body["referenceRecipe"]["name"] == "Tortilla"
    assert (body["promptVersionId"], body["authorUserId"]) == ("v1", "u-1")


# --- submit snapshot + per-slot retry (week_generation_backend R34, R36-R46) ---


def _errored_run(queue: GenerationQueue) -> None:
    """A submitted, claimed run whose slot 1-2 failed and 1-1 succeeded."""
    queue.submit("hash-1", REQUEST, effective_rules=RuleSet(), prompt_version_id="v1", author="u-1")
    queue.claim("hash-1")
    queue.begin_slots(
        "hash-1",
        (SlotProgress(1, 1, SlotStatus.PENDING), SlotProgress(1, 2, SlotStatus.PENDING)),
    )
    queue.record_slot("hash-1", SlotProgress(1, 1, SlotStatus.DONE))
    queue.record_slot(
        "hash-1", SlotProgress(1, 2, SlotStatus.ERROR, SlotError("invalid_output", "x"))
    )
    queue.record_status("hash-1", RunStatus.PARTIAL)


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_submit_stores_the_run_and_an_empty_slot_map(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    queue = queue_factory()

    queue.submit("hash-1", REQUEST, effective_rules=RuleSet(), prompt_version_id="v1")

    stored = queue.stored_generation("hash-1")
    assert stored is not None and stored.slots == ()
    assert stored.snapshot == GenerationSnapshot(
        IsoWeek(2026, 34), GenerationMode.MIX, RuleSet(), "v1"
    )


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_a_single_recipe_record_has_no_slot_map(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    queue = queue_factory()
    queue.submit_recipe(
        "hash-r", RECIPE_REQUEST, reference_recipe=None, prompt_version_id="v1", author="u-1"
    )

    stored = queue.stored_generation("hash-r")
    assert stored is not None and stored.slots is None and stored.snapshot is None


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_retry_sets_the_slot_pending_and_the_run_running(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    queue = queue_factory()
    _errored_run(queue)

    queue.retry_slot("hash-1", 1, 2, author="u-2")

    stored = queue.stored_generation("hash-1")
    assert stored is not None and stored.status == "running"
    assert stored.slots == (
        SlotProgress(1, 1, SlotStatus.DONE),  # R52 — untouched
        SlotProgress(1, 2, SlotStatus.PENDING),
    )


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_of_two_concurrent_retries_exactly_one_is_accepted(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    queue = queue_factory()
    _errored_run(queue)
    queue.retry_slot("hash-1", 1, 2, author="u-2")

    with pytest.raises(SlotNotRetryable):
        queue.retry_slot("hash-1", 1, 2, author="u-3")


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_retry_of_a_slot_not_in_error_is_refused(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    queue = queue_factory()
    _errored_run(queue)

    with pytest.raises(SlotNotRetryable):
        queue.retry_slot("hash-1", 1, 1, author="u-2")  # done
    with pytest.raises(SlotNotRetryable):
        queue.retry_slot("hash-1", 5, 1, author="u-2")  # absent


def test_the_sqs_retry_enqueues_exactly_one_slot_retry_message_with_the_stored_run() -> None:
    queue = sqs_generation_queue()
    _errored_run(queue)
    received_generation_messages()  # drain the submit message

    queue.retry_slot("hash-1", 1, 2, author="u-2")

    (raw,) = received_generation_messages()
    body = json.loads(raw)
    assert body == {
        "type": "slot_retry",
        "idPeticionIA": "hash-1",
        "day": 1,
        "slot": 2,
        "weekId": "2026-W34",
        "mode": "mix",
        "effectiveRules": {"categoryCounts": [], "pins": [], "disabledDays": []},
        "promptVersionId": "v1",
        "authorUserId": "u-2",
    }


def test_a_refused_sqs_retry_enqueues_nothing() -> None:
    queue = sqs_generation_queue()
    _errored_run(queue)
    received_generation_messages()

    with pytest.raises(SlotNotRetryable):
        queue.retry_slot("hash-1", 1, 1, author="u-2")

    assert received_generation_messages() == []


def test_a_failed_enqueue_restores_the_slot_to_error_and_the_run_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R46."""
    from planner_api.adapters.sqs import SqsGenerationQueue

    queue = sqs_generation_queue()
    _errored_run(queue)

    class _Broken:
        def send_message(self, **_kwargs: object) -> None:
            raise RuntimeError("sqs down")

    monkeypatch.setattr(SqsGenerationQueue, "_sqs", lambda self: _Broken())

    with pytest.raises(RuntimeError):
        queue.retry_slot("hash-1", 1, 2, author="u-2")

    stored = queue.stored_generation("hash-1")
    assert stored is not None and stored.status == "partial"
    assert stored.slots is not None
    # code and message survive the restore (R20)
    assert stored.slots[1] == SlotProgress(1, 2, SlotStatus.ERROR, SlotError("invalid_output", "x"))
    monkeypatch.undo()
    queue.retry_slot("hash-1", 1, 2, author="u-2")


def test_the_sqs_retry_is_one_conditional_write_on_the_slot_estado() -> None:
    """R36/R40 — a single UpdateItem carries the condition."""
    import inspect

    from planner_api.adapters.sqs import SqsGenerationQueue

    code = _statement_lines(inspect.getsource(SqsGenerationQueue.retry_slot))
    assert code.count("update_item(") == 1
    assert 'ConditionExpression="#f.#k.#e = :error"' in code


_RULES = RuleSet(
    category_counts=(CategoryCountRule(IngredientCategory.LEGUME, 2),),
    pins=(PinRule(2, MealSlot.DINNER, "r-1"),),
    disabled_days=(5,),
)
_RULES_PAYLOAD = {
    "categoryCounts": [{"category": "legume", "count": 2}],
    "pins": [{"day": 2, "slot": 2, "recipeId": "r-1"}],
    "disabledDays": [5],
}


@pytest.mark.parametrize("queue_factory", IMPLEMENTATIONS)
def test_submit_stores_the_effective_rules_and_the_mode_it_was_given(
    queue_factory: Callable[[], GenerationQueue],
) -> None:
    """R34 — not the defaults."""
    queue = queue_factory()
    request = GenerationRequest(week=IsoWeek(2026, 35), mode=GenerationMode.LIBRARY_ONLY)

    queue.submit("hash-2", request, effective_rules=_RULES, prompt_version_id="v7")

    stored = queue.stored_generation("hash-2")
    assert stored is not None
    assert stored.snapshot == GenerationSnapshot(
        IsoWeek(2026, 35), GenerationMode.LIBRARY_ONLY, _RULES, "v7"
    )


def test_the_sqs_retry_message_carries_the_stored_non_empty_rules_and_mode() -> None:
    """R44, R49 — the parent's rules and mode, not defaults."""
    queue = sqs_generation_queue()
    request = GenerationRequest(week=IsoWeek(2026, 35), mode=GenerationMode.LIBRARY_ONLY)
    queue.submit("hash-2", request, effective_rules=_RULES, prompt_version_id="v7")
    queue.claim("hash-2")
    queue.begin_slots("hash-2", (SlotProgress(1, 1, SlotStatus.PENDING),))
    queue.record_slot("hash-2", SlotProgress(1, 1, SlotStatus.ERROR, SlotError("c", "m")))
    received_generation_messages()

    queue.retry_slot("hash-2", 1, 1, author="u-2")

    body = json.loads(received_generation_messages()[0])
    assert body["effectiveRules"] == _RULES_PAYLOAD
    assert (body["mode"], body["weekId"], body["promptVersionId"]) == (
        "library_only",
        "2026-W35",
        "v7",
    )
