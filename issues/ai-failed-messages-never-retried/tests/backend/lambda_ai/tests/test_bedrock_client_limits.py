"""The Bedrock client is bounded, so one slot cannot eat the function's 900 s
(issues/ai-failed-messages-never-retried/plan.md E17)."""

from __future__ import annotations

from typing import Any

from planner_ai.adapters.bedrock import BedrockAiProvider

_FUNCTION_SECONDS = 900  # ai_timeout (terraform/locals.tf)
_SLOTS = 14


def _config() -> Any:
    return BedrockAiProvider()._bedrock().meta.config


def test_a_response_wait_fits_in_one_slots_share_of_the_function() -> None:
    assert _config().read_timeout < _FUNCTION_SECONDS / _SLOTS


def test_a_connection_attempt_gives_up_within_seconds() -> None:
    assert _config().connect_timeout <= 10


def test_retries_use_the_standard_mode() -> None:
    assert (_config().retries or {}).get("mode") == "standard"


def test_a_call_makes_at_most_two_attempts() -> None:
    assert (_config().retries or {}).get("total_max_attempts", 5) <= 2
