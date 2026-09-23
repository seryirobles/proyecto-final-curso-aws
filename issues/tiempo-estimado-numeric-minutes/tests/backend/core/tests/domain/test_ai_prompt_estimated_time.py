"""Issue 11 (E6): the prompt instructs the model to state the estimated
prep/cook time as an integer minute count (`G-90`, amending `FR-AI-13`). The
wording change lands as a **new** prompt version — `FR-AI-14` / `G-84` make the
registry append-only, so v1 and v2 keep the free-text wording they shipped
with."""

from __future__ import annotations

from planner_core.domain.ai_prompt import PROMPT_INSTRUCTION_VERSIONS, resolve_prompt_version

NUMERIC_TIME_VERSION = "v3"


def test_the_numeric_time_prompt_version_is_registered() -> None:
    assert NUMERIC_TIME_VERSION in PROMPT_INSTRUCTION_VERSIONS
    assert resolve_prompt_version(NUMERIC_TIME_VERSION).version_id == NUMERIC_TIME_VERSION


def test_the_numeric_time_version_declares_estimated_time_as_an_integer() -> None:
    instruction = resolve_prompt_version(NUMERIC_TIME_VERSION).json_output_instruction

    assert "estimated_time (int|null" in instruction
    assert "estimated_time (str|null" not in instruction


def test_the_numeric_time_version_asks_the_model_for_minutes() -> None:
    instruction = resolve_prompt_version(NUMERIC_TIME_VERSION).recipe_metadata_instruction

    assert "minute" in instruction.lower() or "minuto" in instruction.lower()


def test_the_earlier_prompt_versions_keep_the_wording_they_shipped_with() -> None:
    """`G-84`: a version is added, never rewritten."""
    for version_id in ("v1", "v2"):
        assert (
            "estimated_time (str|null)"
            in resolve_prompt_version(version_id).json_output_instruction
        )
