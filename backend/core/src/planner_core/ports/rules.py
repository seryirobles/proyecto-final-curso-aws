"""The rule repository port: persistence for GRUPOREGLAS (docs/data_model.md section 1)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from planner_core.domain.rules import RuleSet


@runtime_checkable
class RuleRepository(Protocol):
    """Persistence for the single shared rule set (docs/data_model.md section 7:
    GRUPOREGLAS is a single-value partition — one household, one rule set)."""

    def get(self) -> RuleSet:
        """Returns RuleSet() (all-empty) if never written."""
        ...

    def save(self, rule_set: RuleSet) -> None: ...
