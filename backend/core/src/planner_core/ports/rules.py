"""The rule repository port: persistence for GRUPOREGLAS (docs/data_model.md section 1)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from planner_core.domain.rules import Rule, RuleSet


@runtime_checkable
class RuleRepository(Protocol):
    """Persistence for the single shared rule set (docs/data_model.md section 7:
    GRUPOREGLAS is a single-value partition — one household, one rule set).

    GQ3 (design.md section 3): writes are per-rule single items keyed by the
    rule's deterministic natural key, so FR-RT-02 last-write-wins applies per
    rule, not to the whole set. There is no whole-RuleSet blob write."""

    def current_version(self) -> int:
        """The rule set's change marker (docs/data_model.md section 4.7, AP29).
        A real adapter reads it strongly-consistently, marker attribute only;
        0 before any write. No side effects."""
        ...

    def get(self) -> RuleSet:
        """Returns RuleSet() (all-empty) if never written."""
        ...

    def save_rule(self, rule: Rule) -> int:
        """Upsert one rule keyed by its natural id (AP23); return the rule set's
        marker as advanced by this write, bumped in the same operation
        (docs/data_model.md section 1.1/5.5)."""
        ...

    def delete_rule(self, rule_id: str) -> int:
        """Delete one rule by its natural id (AP24); return the rule set's marker
        as advanced by this delete, bumped in the same operation
        (docs/data_model.md section 1.1/5.5)."""
        ...
