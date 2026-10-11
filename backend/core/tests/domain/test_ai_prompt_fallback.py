"""Registry tests for the v4 fallback sentence (specs/ai_fallback_recipe R1, R10, R11, R16)."""

from __future__ import annotations

import dataclasses
import hashlib

import pytest

from planner_core.domain.ai_prompt import (
    HEALTHY_BALANCED_INSTRUCTION_V4,
    PROMPT_INSTRUCTION_VERSIONS,
    resolve_prompt_version,
)

_SNAPSHOT = {
    "v1": "991c2895d9ba5d4e58f756ad8ffa94e416e1191e3cbbde5ea99f4049457d01d1",
    "v2": "c53672ae6e477aa5868d6bebcab8bf1c877af95aed405af43305e4a6947a288e",
    "v3": "23633f929afc104c70e6bce917fe15a23797778e77f11397620548c961716d0c",
}
_FALLBACK = (
    "If the ingredients, tools or specifications below are empty, generic, "
    'unrelated to cooking or unintelligible (for example "test"), ignore the '
    "unusable part and still produce one valid dish that follows these "
    "guidelines; honour any part that is usable."
)


def test_v4_instruction_ends_with_the_fallback_sentence() -> None:
    assert HEALTHY_BALANCED_INSTRUCTION_V4.endswith(_FALLBACK)
    assert resolve_prompt_version("v4").healthy_balanced_instruction == (
        HEALTHY_BALANCED_INSTRUCTION_V4
    )


@pytest.mark.parametrize("version_id", sorted(_SNAPSHOT))
def test_retained_versions_are_unchanged(version_id: str) -> None:
    fields = dataclasses.asdict(PROMPT_INSTRUCTION_VERSIONS[version_id])
    digest = hashlib.sha256(repr(sorted(fields.items())).encode()).hexdigest()

    assert digest == _SNAPSHOT[version_id]


def test_v4_is_v3_with_only_the_healthy_balanced_instruction_replaced() -> None:
    v3 = dataclasses.asdict(PROMPT_INSTRUCTION_VERSIONS["v3"])
    v4 = dataclasses.asdict(PROMPT_INSTRUCTION_VERSIONS["v4"])

    changed = {k for k in v3 if v3[k] != v4[k]}
    assert changed == {"version_id", "healthy_balanced_instruction"}
