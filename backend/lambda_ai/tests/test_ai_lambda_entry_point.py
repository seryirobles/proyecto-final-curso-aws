"""The ai worker's Lambda entry point under AWS's real calling convention,
`lambda_handler(event, context)` (issues/lambda-handler-receives-context-as-deps)."""

from __future__ import annotations

import dataclasses
import json
from typing import Any

import pytest
from planner_core.ports.generation_queue import StoredGeneration
from support.fakes import (
    FakeAiProvider,
    FakeClock,
    FakeGenerationGate,
    FakeGenerationQueue,
    FakeRecipeRepository,
    FakeWeekRepository,
)

from planner_ai import handler, wiring
from planner_ai.wiring import Dependencies


class FakeLambdaContext:
    """Shaped like the runtime's LambdaContext; it carries no ports."""

    function_name = "planner-dev-ai"
    aws_request_id = "req-1"

    def get_remaining_time_in_millis(self) -> int:
        return 900_000


class _FalsyDependencies(Dependencies):
    def __bool__(self) -> bool:
        return False


def _deps(queue: FakeGenerationQueue) -> Dependencies:
    return Dependencies(
        provider=FakeAiProvider(),
        weeks=FakeWeekRepository(),
        recipes=FakeRecipeRepository(),
        records=queue,
        gate=FakeGenerationGate(),
        clock=FakeClock.at("2026-08-17T10:00:00+00:00"),
    )


def _pending_queue() -> FakeGenerationQueue:
    queue = FakeGenerationQueue()
    queue.stored["k1"] = StoredGeneration(idempotency_key="k1", status="pending")
    return queue


def _event() -> dict[str, Any]:
    body = {
        "idPeticionIA": "k1",
        "weekId": "2026-W34",
        "mode": "mix",
        "promptVersionId": "v1",
        "authorUserId": "u-1",
        "effectiveRules": {},
    }
    return {"Records": [{"body": json.dumps(body)}]}


def _patch_builder(monkeypatch: pytest.MonkeyPatch, build: Any) -> None:
    monkeypatch.setattr(wiring, "build_dependencies", build)
    if hasattr(handler, "build_dependencies"):
        monkeypatch.setattr(handler, "build_dependencies", build)


def test_ai_lambda_handler_processes_a_record_with_wired_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E4 - reproduction: today the context is taken as `deps` and every record
    fails inside the per-record catch, so nothing is claimed."""
    queue = _pending_queue()
    calls: list[int] = []

    def build(*_args: object, **_kwargs: object) -> Dependencies:
        calls.append(1)
        return _deps(queue)

    _patch_builder(monkeypatch, build)

    handler.lambda_handler(_event(), FakeLambdaContext())

    assert queue.claims == ["k1"]
    assert queue.stored["k1"].status == "completed"
    assert calls == [1]


def test_an_injected_ai_bundle_is_used_even_when_it_is_falsy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E5 - injection is decided by presence, not truthiness (`or` trap)."""

    def refuse(*_args: object, **_kwargs: object) -> Dependencies:
        raise AssertionError("build_dependencies must not run here")

    _patch_builder(monkeypatch, refuse)
    queue = _pending_queue()
    base = _deps(queue)
    falsy = _FalsyDependencies(**{f.name: getattr(base, f.name) for f in dataclasses.fields(base)})

    handler.handle(_event(), deps=falsy)

    assert queue.claims == ["k1"]
