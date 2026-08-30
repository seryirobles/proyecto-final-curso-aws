"""The rule repository port: persistence for GRUPOREGLAS (docs/data_model.md section 1)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from planner_core.domain.rules import RuleSet


@runtime_checkable
class RuleRepository(Protocol):
    """Persistence for the single shared rule set (docs/data_model.md section 7:
    GRUPOREGLAS is a single-value partition — one household, one rule set)."""

    def current_version(self) -> int:
        """The rule set's change marker (docs/data_model.md section 4.7, AP29).
        A real adapter reads it strongly-consistently, marker attribute only;
        0 before any write. No side effects (R2)."""
        ...

    def get(self) -> RuleSet:
        """Returns RuleSet() (all-empty) if never written."""
        ...

    def save(self, rule_set: RuleSet) -> int:
        """Return the rule set's marker as advanced by this write, bumped in the
        same operation (docs/data_model.md section 1.1/5.5)."""
        ...
