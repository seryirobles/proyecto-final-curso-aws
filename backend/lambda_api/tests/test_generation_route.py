"""POST /v1/generations: the SQS enqueue call site and the idempotent-hit
shortcut (R35, R37), plus the no-Bedrock-SDK import scan (R36)."""

from __future__ import annotations

import ast
from pathlib import Path

from _helpers import api_event, authorizer_context, make_deps, seed_user
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
