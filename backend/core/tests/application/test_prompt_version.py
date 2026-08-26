"""Tests for resolving the active AI prompt-instruction version from the config port."""

from __future__ import annotations

import pytest
from support.fakes import FakeConfig

from planner_core.application.prompt_version import resolve_active_prompt_version
from planner_core.domain.ai_prompt import (
    PROMPT_VERSION_CONFIG_KEY,
    UnknownPromptVersion,
    resolve_prompt_version,
)


def test_resolve_active_prompt_version_returns_the_version_named_by_the_config_key() -> None:
    """FR-AI-14, R3, R7: the identifier travels alongside the resolved content."""
    config = FakeConfig({PROMPT_VERSION_CONFIG_KEY: "v1"})

    version = resolve_active_prompt_version(config)

    assert version == resolve_prompt_version("v1")
    assert version.version_id == "v1"


def test_resolve_active_prompt_version_raises_when_the_key_is_unset() -> None:
    """FR-AI-14, R4: no configured value, no silent fallback."""
    config = FakeConfig({})

    with pytest.raises(UnknownPromptVersion):
        resolve_active_prompt_version(config)


def test_resolve_active_prompt_version_raises_when_the_configured_id_is_unregistered() -> None:
    """FR-AI-14, R4: a configured value naming no retained version."""
    config = FakeConfig({PROMPT_VERSION_CONFIG_KEY: "does-not-exist"})

    with pytest.raises(UnknownPromptVersion):
        resolve_active_prompt_version(config)


def test_resolve_active_prompt_version_reads_the_config_port_exactly_once() -> None:
    """Mirrors the analogous single-read assertion made for Clock (docs/specs.md)."""
    config = FakeConfig({PROMPT_VERSION_CONFIG_KEY: "v1"})

    resolve_active_prompt_version(config)

    assert config.readings == 1
