"""Every AI worker variable is documented in both docs (specs/ai_inference_config R21, R22)."""

from __future__ import annotations

from pathlib import Path

import pytest

_DOCS = Path(__file__).resolve().parents[3] / "docs"
_VARS = (
    "AI_MODEL_ID",
    "AI_REASONING_ENABLED",
    "AI_REASONING_EFFORT",
    "AI_MAX_TOKENS",
    "AI_TEMPERATURE",
    "AI_TOP_P",
    "AI_SERVICE_TIER",
)


@pytest.mark.parametrize("doc", ["local_development.md", "architecture.md"])
@pytest.mark.parametrize("variable", _VARS)
def test_the_variable_is_documented(doc: str, variable: str) -> None:
    assert variable in (_DOCS / doc).read_text(encoding="utf-8")


def test_the_local_doc_example_is_nova() -> None:
    text = (_DOCS / "local_development.md").read_text(encoding="utf-8")

    assert "AI_MODEL_ID=eu.amazon.nova-2-lite-v1:0" in text
    assert "gpt-5.6" not in text
