"""In-memory fakes for the planner_core ports."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FakeClock:
    """A `Clock` frozen at one explicit instant.

    It never advances and never consults a real clock, so a test that uses it
    cannot accidentally depend on the host's time or timezone. ``readings``
    records how often it was consulted, which is how the single-read rule of
    ``resolve_live_weeks`` is asserted.
    """

    instant: datetime
    readings: int = field(default=0)

    @classmethod
    def at(cls, iso_8601: str) -> FakeClock:
        """Build a clock from an ISO-8601 instant, e.g. `2026-07-16T10:00:00+00:00`."""
        return cls(datetime.fromisoformat(iso_8601))

    def now(self) -> datetime:
        self.readings += 1
        return self.instant


@dataclass
class FakeConfig:
    """A `ConfigPort` backed by a plain dict, never the host's real environment.

    ``readings`` counts every ``get`` call, mirroring ``FakeClock.readings``'
    role in asserting the single-read rule (docs/specs.md's own worked example).
    """

    values: dict[str, str] = field(default_factory=dict)
    readings: int = field(default=0)

    def get(self, key: str) -> str | None:
        self.readings += 1
        return self.values.get(key)
