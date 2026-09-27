"""Tests for the GenerationQueue port and its in-memory fake (FR-AI-08)."""

from __future__ import annotations

import dataclasses

import pytest
from support.fakes import FakeGenerationQueue

from planner_core.domain.calendar import IsoWeek
from planner_core.domain.generation import GenerationMode, GenerationRequest
from planner_core.domain.rules import RuleSet
from planner_core.ports.generation_queue import GenerationQueue, StoredGeneration

REQUEST = GenerationRequest(week=IsoWeek(2026, 34), mode=GenerationMode.MIX)


def test_fake_satisfies_the_generation_queue_port() -> None:
    assert isinstance(FakeGenerationQueue(), GenerationQueue)


def test_stored_generation_is_frozen() -> None:
    record = StoredGeneration(idempotency_key="h1", status="done", result="{}")
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.__setattr__("status", "running")


def test_stored_generation_lookup_and_submit_round_trip() -> None:
    queue = FakeGenerationQueue()
    assert queue.stored_generation("h1") is None

    queue.submit("h1", REQUEST, effective_rules=RuleSet())
    assert queue.submissions == [("h1", REQUEST)]

    queue.stored["h1"] = StoredGeneration(idempotency_key="h1", status="pending")
    assert queue.stored_generation("h1") is not None


def test_the_port_names_no_queue_technology() -> None:
    """R25: the Protocol's method signatures name no queue technology."""
    import inspect

    signatures = "".join(
        str(inspect.signature(getattr(GenerationQueue, name)))
        for name in (
            "stored_generation",
            "submit",
            "submit_recipe",
            "discard",
            "claim",
            "record_result",
        )
    )
    for banned in ("sqs", "kinesis", "sns", "kafka", "queue_url", "boto", "Message"):
        assert banned not in signatures
