"""The ai worker's composition root: its frozen Dependencies bundle
(docs/conventions.md § Tests)."""

from __future__ import annotations

import dataclasses

import pytest
from support.fakes import (
    FakeAiProvider,
    FakeClock,
    FakeGenerationGate,
    FakeGenerationQueue,
    FakeWeekRepository,
)

from planner_ai.wiring import Dependencies


def _deps() -> Dependencies:
    return Dependencies(
        provider=FakeAiProvider(),
        weeks=FakeWeekRepository(),
        records=FakeGenerationQueue(),
        gate=FakeGenerationGate(),
        clock=FakeClock.at("2026-08-17T10:00:00+00:00"),
    )


def test_dependencies_is_frozen() -> None:
    deps = _deps()
    with pytest.raises(dataclasses.FrozenInstanceError):
        deps.__setattr__("clock", deps.clock)


def test_dependencies_is_declared_a_dataclass() -> None:
    assert dataclasses.is_dataclass(Dependencies)
