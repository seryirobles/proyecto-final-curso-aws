"""`GenerationGate` read from the `AI_GENERATION_SWITCH` env var; used while the
shared role cannot read SSM."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)
_VARIABLE = "AI_GENERATION_SWITCH"


class EnvGenerationGate:
    """Read on every call, no cache; anything but `true` is disabled (NFR-AI-01)."""

    def __init__(self) -> None:
        self._last_disabled = False

    def is_generation_enabled(self) -> bool:
        enabled = os.environ.get(_VARIABLE, "").strip().lower() == "true"
        if not enabled and not self._last_disabled:  # parity with issue 14 E7
            logger.info("Env switch %s is off; generation disabled", _VARIABLE)
        self._last_disabled = not enabled
        return enabled
