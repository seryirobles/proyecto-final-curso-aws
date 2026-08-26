"""The active AI prompt-instruction version, resolved from one reading of the config port."""

from __future__ import annotations

from planner_core.domain.ai_prompt import (
    PROMPT_VERSION_CONFIG_KEY,
    PromptInstructionsVersion,
    UnknownPromptVersion,
    resolve_prompt_version,
)
from planner_core.ports.config import ConfigPort


def resolve_active_prompt_version(config: ConfigPort) -> PromptInstructionsVersion:
    """The one place ConfigPort meets domain/ai_prompt.py (FR-AI-14, R3, R4, R7).

    Reads the port exactly once and resolves the plain id it returns; raises
    UnknownPromptVersion if the key is unset or names an unregistered version.
    """
    version_id = config.get(PROMPT_VERSION_CONFIG_KEY)
    if version_id is None:
        raise UnknownPromptVersion(PROMPT_VERSION_CONFIG_KEY)
    return resolve_prompt_version(version_id)
