"""The clock port: the only source of the present instant inside planner_core."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Supplies the present instant.

    The contract is *timezone-aware*, not *UTC*: an adapter may return the
    instant in any offset. Domain code converts it to ``Europe/Madrid`` itself,
    so every offset denoting the same moment yields the same answer. A naive
    value violates the contract and is rejected by ``civil_date``.
    """

    def now(self) -> datetime:
        """Return the present instant as a timezone-aware datetime."""
        ...


class SystemClock:
    """The default `Clock`: the host's present instant, expressed in UTC.

    It ships beside the `Protocol` it satisfies rather than in a Lambda package
    because it imports nothing outside the standard library, so it adds no
    runtime dependency to planner_core: a default implementation, not an adapter
    (docs/architecture.md section 1.2.2). Only an implementation that pulls in an
    external dependency belongs to the Lambda that owns that dependency.
    """

    def now(self) -> datetime:
        """Return the present instant as a timezone-aware datetime."""
        # The aware form below, never the bare utcnow(): that one returns a naive
        # value, which civil_date rejects with NaiveInstant, and it is deprecated
        # from Python 3.12. Writing that trap correctly exactly once is why this
        # class is not duplicated per Lambda (docs/architecture.md section 1.2.2).
        #
        # This is the sole sanctioned ambient-time call in planner_core, and
        # tests/test_no_ambient_time.py allows this one line and nothing else.
        return datetime.now(UTC)
