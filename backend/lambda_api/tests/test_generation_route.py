"""POST /v1/generations: the SQS enqueue call site and the idempotent-hit
shortcut (R35, R37), plus the no-Bedrock-SDK import scan (R36)."""

from __future__ import annotations

import ast
import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from _helpers import api_event, authorizer_context, make_deps, seed_user
from planner_core.domain.calendar import IsoWeek
from planner_core.domain.generation import (
    GenerationMode,
    GenerationSnapshot,
    SlotError,
    SlotProgress,
    SlotStatus,
)
from planner_core.domain.role import Role
from planner_core.domain.rules import RuleSet
from planner_core.ports.generation_queue import StoredGeneration
from support.fakes import FakeGenerationQueue

from planner_api.handler import handle

_SRC = Path(__file__).resolve().parents[1] / "src" / "planner_api"


def test_submitting_a_fresh_generation_enqueues_through_the_generation_queue_port() -> None:
    queue = FakeGenerationQueue()
    deps = make_deps(queue=queue)
    seed_user(deps, user_id="u-1")
    event = api_event(
        "POST",
        "/v1/generations",
        body={"type": "week", "weekId": "2026-W34", "mode": "library_only"},
        context=authorizer_context(user_id="u-1"),
    )

    response = handle(event, deps)

    assert response["statusCode"] == 202
    assert len(queue.submissions) == 1


def test_a_stored_idempotent_hit_returns_200_without_enqueueing() -> None:
    queue = FakeGenerationQueue()
    deps = make_deps(queue=queue)
    seed_user(deps, user_id="u-1")
    body = {"type": "week", "weekId": "2026-W34", "mode": "library_only"}
    first = handle(
        api_event("POST", "/v1/generations", body=body, context=authorizer_context(user_id="u-1")),
        deps,
    )
    assert first["statusCode"] == 202

    second = handle(
        api_event("POST", "/v1/generations", body=body, context=authorizer_context(user_id="u-1")),
        deps,
    )

    assert second["statusCode"] == 200
    assert len(queue.submissions) == 1


def test_deleting_a_generation_discards_it_with_the_path_id_and_returns_204_no_etag() -> None:
    """R42 (AP27) — DELETE /v1/generations/{id} calls GenerationQueue.discard with
    the path segment, returns 204, emits no ETag (PETICIONIA# has no MarcaCambio)."""
    queue = FakeGenerationQueue()
    queue.stored["g-1"] = StoredGeneration(idempotency_key="g-1", status="pending")
    queue.stored["g-other"] = StoredGeneration(idempotency_key="g-other", status="pending")
    deps = make_deps(queue=queue)
    seed_user(deps, user_id="u-1")
    event = api_event(
        "DELETE",
        "/v1/generations/{generationId}",
        path_params={"generationId": "g-1"},
        context=authorizer_context(user_id="u-1"),
    )

    response = handle(event, deps)

    assert response["statusCode"] == 204
    assert "ETag" not in response["headers"]
    assert queue.discards == ["g-1"]
    assert queue.stored_generation("g-1") is None
    assert queue.stored_generation("g-other") is not None


# --- week_generation_backend: slots shape + per-slot retry -------------------

_RETRY = "/v1/generations/{generationId}/slots/{day}/{slot}/retry"
_ERR = SlotError("insufficient_library_recipes", "sin recetas")


def _week_run(*slots: SlotProgress, status: str = "partial") -> FakeGenerationQueue:
    queue = FakeGenerationQueue()
    queue.stored["g-1"] = StoredGeneration(
        idempotency_key="g-1",
        status=status,
        slots=slots,
        snapshot=GenerationSnapshot(
            IsoWeek.containing(date(2026, 8, 17)), GenerationMode.MIX, RuleSet(), "v1"
        ),
    )
    return queue


def _get(queue: FakeGenerationQueue) -> dict[str, Any]:
    deps = make_deps(queue=queue)
    seed_user(deps, user_id="u-1")
    event = api_event(
        "GET",
        "/v1/generations/{generationId}",
        path_params={"generationId": "g-1"},
        context=authorizer_context(user_id="u-1"),
    )
    response = handle(event, deps)
    assert response["statusCode"] == 200
    body: dict[str, Any] = json.loads(response["body"])
    return body


def test_a_week_run_returns_ordered_slots_with_error_only_on_error_slots() -> None:
    """R28, R29, R30 — no `result`, `error{code,message}` only when status is error."""
    queue = _week_run(
        SlotProgress(1, 1, SlotStatus.DONE),
        SlotProgress(1, 2, SlotStatus.ERROR, _ERR),
        SlotProgress(2, 1, SlotStatus.RUNNING),
    )

    body = _get(queue)

    assert body == {
        "generationId": "g-1",
        "status": "partial",
        "slots": [
            {"day": 1, "slot": 1, "status": "done"},
            {
                "day": 1,
                "slot": 2,
                "status": "error",
                "error": {"code": "insufficient_library_recipes", "message": "sin recetas"},
            },
            {"day": 2, "slot": 1, "status": "running"},
        ],
    }


def test_a_week_run_with_no_recorded_slots_returns_an_empty_list() -> None:  # R31
    assert _get(_week_run(status="pending"))["slots"] == []


def test_a_single_recipe_run_keeps_its_result_body() -> None:  # R33
    queue = FakeGenerationQueue()
    queue.stored["g-1"] = StoredGeneration("g-1", "completed", '{"name": "Tortilla"}')

    assert _get(queue) == {
        "generationId": "g-1",
        "status": "completed",
        "result": {"name": "Tortilla"},
    }


def test_a_stored_week_hit_on_post_returns_the_get_shape() -> None:  # R32
    queue = FakeGenerationQueue()
    deps = make_deps(queue=queue)
    seed_user(deps, user_id="u-1")
    body = {"type": "week", "weekId": "2026-W34", "mode": "library_only"}
    ctx = authorizer_context(user_id="u-1")
    handle(api_event("POST", "/v1/generations", body=body, context=ctx), deps)

    second = handle(api_event("POST", "/v1/generations", body=body, context=ctx), deps)

    assert second["statusCode"] == 200
    assert json.loads(second["body"])["slots"] == []


def _retry(
    queue: FakeGenerationQueue, day: str = "1", slot: str = "2", generation_id: str = "g-1"
) -> dict[str, Any]:
    deps = make_deps(queue=queue)
    seed_user(deps, user_id="u-1")
    event = api_event(
        "POST",
        _RETRY,
        path_params={"generationId": generation_id, "day": day, "slot": slot},
        context=authorizer_context(user_id="u-1"),
    )
    return handle(event, deps)


def test_retrying_an_error_slot_returns_202_location_and_the_get_body() -> None:
    """R36, R37, R45, R53."""
    queue = _week_run(
        SlotProgress(1, 1, SlotStatus.DONE), SlotProgress(1, 2, SlotStatus.ERROR, _ERR)
    )
    # The fake clock is 2026-08-17 (Monday): every slot of the week is open.
    response = _retry(queue)

    assert response["statusCode"] == 202
    assert response["headers"]["Location"] == "/v1/generations/g-1"
    body = json.loads(response["body"])
    assert body["status"] == "running"
    assert body["slots"][1] == {"day": 1, "slot": 2, "status": "pending"}
    assert queue.retries == [("g-1", 1, 2, "u-1")]


@pytest.mark.parametrize("status", [SlotStatus.PENDING, SlotStatus.RUNNING, SlotStatus.DONE])
def test_retrying_a_slot_that_is_not_in_error_is_409(status: SlotStatus) -> None:  # R38
    response = _retry(_week_run(SlotProgress(1, 2, status)))

    assert response["statusCode"] == 409
    assert json.loads(response["body"])["code"] == "SLOT_NOT_RETRYABLE"


def test_retrying_an_unknown_generation_is_404() -> None:  # R41
    response = _retry(FakeGenerationQueue())

    assert response["statusCode"] == 404
    assert json.loads(response["body"])["code"] == "GENERATION_NOT_FOUND"


def test_retrying_a_slot_the_run_lacks_is_404() -> None:  # R42
    response = _retry(_week_run(SlotProgress(1, 1, SlotStatus.ERROR, _ERR)))

    assert response["statusCode"] == 404
    assert json.loads(response["body"])["code"] == "GENERATION_SLOT_NOT_FOUND"


@pytest.mark.parametrize(("day", "slot"), [("0", "1"), ("8", "1"), ("1", "3"), ("x", "1")])
def test_retrying_with_a_bad_day_or_slot_is_400(day: str, slot: str) -> None:  # R43
    response = _retry(_week_run(SlotProgress(1, 1, SlotStatus.ERROR, _ERR)), day=day, slot=slot)

    assert response["statusCode"] == 400


def test_the_retry_route_requires_the_user_role() -> None:  # R35
    from planner_api.routing import ROUTES

    spec = ROUTES[("POST", _RETRY)]
    assert spec.requires_role is Role.USER and spec.public is False


def test_planner_api_imports_no_ai_provider_sdk_module() -> None:
    """R36 - a mechanical scan, mirroring test_no_ambient_time.py's technique."""
    forbidden = ("bedrock", "anthropic", "boto3.session")
    for path in _SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                names = [node.module]
            else:
                continue
            for name in names:
                assert not any(f in name.lower() for f in forbidden), (
                    f"{path}: imports {name}, an AI provider SDK module"
                )
