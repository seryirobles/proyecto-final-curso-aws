"""Contract suite for GenerationQueue: the in-memory fake and the moto-backed
SQS + PETICIONIA adapter agree on the idempotency-record surface (FR-AI-08)."""

from __future__ import annotations

import inspect
import json
from collections.abc import Callable, Mapping

import pytest
from planner_core.domain.calendar import IsoWeek
from planner_core.domain.generation import (
    GenerationMode,
    GenerationRequest,
    ReferenceSource,
    SingleRecipeRequest,
    SpecificationSource,
)
from planner_core.domain.rules import RuleSet
from planner_core.ports.generation_queue import GenerationQueue, StoredGeneration
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
