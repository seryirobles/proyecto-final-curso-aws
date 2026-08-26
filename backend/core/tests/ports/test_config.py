"""Tests for the ConfigPort, its default implementation, and the fake tests read config from."""

from __future__ import annotations

import pytest
from support.fakes import FakeConfig

from planner_core.ports.config import ConfigPort, EnvConfig


def test_fake_config_satisfies_the_config_port() -> None:
    """The only source of deployment configuration is the port, and the fake implements it."""
    config = FakeConfig({"SOME_KEY": "some-value"})

    assert isinstance(config, ConfigPort)

    assert config.get("SOME_KEY") == "some-value"
    assert config.readings == 1


def test_env_config_satisfies_the_config_port_and_reads_the_exact_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """EnvConfig.get returns os.environ's value for exactly the requested key,
    not a wrong key or a prefixed variant."""
    monkeypatch.setenv("AI_PROMPT_VERSION_ID", "v1")
    monkeypatch.setenv("OTHER_KEY", "should-not-be-returned")
    config = EnvConfig()

    assert isinstance(config, ConfigPort)

    assert config.get("AI_PROMPT_VERSION_ID") == "v1"


def test_env_config_returns_none_for_an_unset_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """No default, no fallback: an unset key returns None (design.md section 8)."""
    monkeypatch.delenv("DOES_NOT_EXIST_AS_AN_ENV_VAR", raising=False)
    config = EnvConfig()

    assert config.get("DOES_NOT_EXIST_AS_AN_ENV_VAR") is None
