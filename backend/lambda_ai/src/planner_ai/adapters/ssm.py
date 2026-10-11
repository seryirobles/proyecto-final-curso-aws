"""`GenerationGate` backed by SSM Parameter Store (specs/ai_lambda/design.md
section 5, section 10): the `String` parameter `/planner/<env>/ai-generation-enabled`
(`"true"` / `"false"`), read through a short in-process TTL cache so a hot Lambda
does not call SSM per slot. Reads that fail resolve to disabled — a cost
kill-switch fails closed (NFR-AI-01)."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)
_REGION = os.environ.get("AWS_DEFAULT_REGION", "eu-south-2")
_TTL_SECONDS = 5.0


class SsmGenerationGate:
    """`client` is injected in tests; production reads the default SSM client."""

    def __init__(
        self, env: str | None = None, *, client: Any = None, ttl_seconds: float = _TTL_SECONDS
    ) -> None:
        resolved_env = env or os.environ.get("PLANNER_ENV", "dev")
        self._parameter = f"/planner/{resolved_env}/ai-generation-enabled"
        self._client = client  # boto3 ships no stubs (docs/conventions.md)
        self._ttl = ttl_seconds
        self._cached: bool | None = None
        self._fetched_at = 0.0
        self._last_disabled_by_switch = False

    def _ssm(self) -> Any:
        return self._client or boto3.client("ssm", region_name=_REGION)

    def is_generation_enabled(self) -> bool:
        now = time.monotonic()
        if self._cached is not None and now - self._fetched_at < self._ttl:
            return self._cached
        try:
            response = self._ssm().get_parameter(Name=self._parameter)
            enabled = str(response["Parameter"]["Value"]).strip().lower() == "true"
            if not enabled and not self._last_disabled_by_switch:  # issue 14 E7
                logger.info("SSM switch %s is off; generation disabled", self._parameter)
            self._last_disabled_by_switch = not enabled
        except (BotoCoreError, ClientError, KeyError) as error:
            logger.warning(
                "SSM switch %s unreadable (%s %s); generation fails closed",
                self._parameter,
                type(error).__name__,
                getattr(error, "response", {}).get("Error", {}).get("Code", ""),
            )
            self._last_disabled_by_switch = False
            enabled = False  # fail closed — the switch exists to stop spend (NFR-AI-01)
        self._cached = enabled
        self._fetched_at = now
        return enabled
