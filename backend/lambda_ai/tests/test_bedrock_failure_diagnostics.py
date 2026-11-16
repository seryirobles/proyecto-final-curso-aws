"""An unusable model response raises an AiProviderError that says why: the
stop reason and a bounded snippet of the text.
The use case logs that error (issue 13), so this text is what reaches the log."""

from __future__ import annotations

from typing import Any

import pytest
from planner_core.domain.ai_prompt import build_category_prompt
from planner_core.ports.ai_provider import AiProviderError

from planner_ai.adapters.bedrock import BedrockAiProvider

PROMPT = build_category_prompt((), "v1")
TRUNCATED = '{"name": "Lentejas guisadas", "ingredients": [{"name": "lentejas", "quan'


class _Client:
    def __init__(self, response: dict[str, Any]) -> None:
        self._response = response

    def converse(self, **kwargs: Any) -> dict[str, Any]:
        return self._response


def _text_response(text: str, stop_reason: str = "max_tokens") -> dict[str, Any]:
    return {"output": {"message": {"content": [{"text": text}]}}, "stopReason": stop_reason}


def test_unparseable_output_error_carries_stop_reason_and_snippet() -> None:
    """E4 - a cut-off JSON body is diagnosable from the log line alone."""
    provider = BedrockAiProvider(client=_Client(_text_response(TRUNCATED)))

    with pytest.raises(AiProviderError) as raised:
        provider.generate(PROMPT)

    assert "max_tokens" in str(raised.value)
    assert "Lentejas guisadas" in str(raised.value)


def test_the_snippet_in_the_error_is_bounded() -> None:
    """E4 - 500-char cap on model text; the error stays well under 1000."""
    huge = "{" + "z" * 20_000
    provider = BedrockAiProvider(client=_Client(_text_response(huge, "end_turn")))

    with pytest.raises(AiProviderError) as raised:
        provider.generate(PROMPT)

    assert "end_turn" in str(raised.value)
    assert len(str(raised.value)) <= 1_000


def test_a_response_with_no_text_block_names_the_stop_reason() -> None:
    """E4 - e.g. a content-filtered or reasoning-only response."""
    response = {"output": {"message": {"content": []}}, "stopReason": "content_filtered"}
    provider = BedrockAiProvider(client=_Client(response))

    with pytest.raises(AiProviderError) as raised:
        provider.generate(PROMPT)

    assert "content_filtered" in str(raised.value)
