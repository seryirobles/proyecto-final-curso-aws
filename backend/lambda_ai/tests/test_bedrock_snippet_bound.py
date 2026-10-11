"""The snippet in the provider error is capped at 500 (issue 14 E4)."""

from __future__ import annotations

import re

import pytest
from planner_core.domain.ai_prompt import build_category_prompt
from planner_core.ports.ai_provider import AiProviderError
from test_bedrock_failure_diagnostics import _Client, _text_response

from planner_ai.adapters.bedrock import BedrockAiProvider


def test_snippet_has_at_most_500_filler_characters() -> None:
    provider = BedrockAiProvider(client=_Client(_text_response("{" + "z" * 900)))
    with pytest.raises(AiProviderError) as raised:
        provider.generate(build_category_prompt((), "v1"))
    assert max(len(m) for m in re.findall(r"z+", str(raised.value))) <= 500
