"""The AI generation kill-switch port (NFR-AI-01, resolves G-81): one
deployment-wide boolean, read before every provider invocation. No per-user
quota (G-70). The SSM-backed adapter lives in `planner_ai`
(specs/ai_lambda/design.md section 5)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class GenerationGate(Protocol):
    """The deployment-wide generation switch."""

    def is_generation_enabled(self) -> bool:
        """One global state — no user argument (R19, R20)."""
        ...
