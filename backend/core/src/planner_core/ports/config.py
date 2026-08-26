"""The config port: the only source of deployment configuration inside planner_core."""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable


@runtime_checkable
class ConfigPort(Protocol):
    """Supplies a deployment configuration value by key.

    Mirrors Clock's contract shape (planner_core/ports/clock.py): one small
    method, no assumption about where a real implementation reads from.
    """

    def get(self, key: str) -> str | None:
        """Return the configured value for `key`, or None if unset."""
        ...


class EnvConfig:
    """The default `ConfigPort`: reads `os.environ`.

    Ships beside the `Protocol` it satisfies (docs/architecture.md section
    1.2.2) because it imports nothing outside the standard library -- the
    same reasoning that keeps the Clock port's default implementation beside
    `Clock` rather than in a Lambda's `adapters/`.
    """

    def get(self, key: str) -> str | None:
        return os.environ.get(key)
