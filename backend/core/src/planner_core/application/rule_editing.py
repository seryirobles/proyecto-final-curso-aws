"""Per-rule editing (AP23/AP24): load the whole set, apply the change in
memory, check satisfiability, then commit the single-item write (FR-RULE-07,
docs/rest_api_contract.md section 7 Q5 consequence i)."""

from __future__ import annotations

from dataclasses import dataclass

from planner_core.domain.rules import (
    CategoryCountRule,
    DisabledDay,
    PinRule,
    Rule,
    RuleSet,
    UnsatisfiableRuleSet,
    apply_rule,
    remove_rule_by_id,
)
from planner_core.ports.rules import RuleRepository


def _existing_conflicts(current: RuleSet, attempted: Rule) -> tuple[Rule, ...]:
    """The existing rules that clash with `attempted` (R16): the pin vs the
    disabled day it lands on, otherwise the slot-budget holders (category counts
    plus disabled days) the attempted rule does not itself replace."""
    disabled = tuple(DisabledDay(day=day) for day in current.disabled_days)
    if isinstance(attempted, PinRule):
        day_clash = tuple(day for day in disabled if day.day == attempted.day)
        if day_clash:
            return day_clash
    if isinstance(attempted, DisabledDay):
        pin_clash = tuple(pin for pin in current.pins if pin.day == attempted.day)
        if pin_clash:
            return pin_clash
    kept_counts = tuple(
        rule
        for rule in current.category_counts
        if not (isinstance(attempted, CategoryCountRule) and rule.category == attempted.category)
    )
    kept_disabled = tuple(
        day
        for day in disabled
        if not (isinstance(attempted, DisabledDay) and day.day == attempted.day)
    )
    return (*kept_counts, *kept_disabled)


@dataclass(frozen=True)
class RulesView:
    """AP22 read: the shared rule set plus its change marker (R34), marker read
    before the payload (R35)."""

    rule_set: RuleSet
    marker: int


def read_rules(*, rules: RuleRepository) -> RulesView:
    """AP22 — the shared rule set and its marker, marker read first."""
    marker = rules.current_version()  # marker before payload (R35)
    return RulesView(rule_set=rules.get(), marker=marker)


def save_rule(rule: Rule, *, rules: RuleRepository) -> int:
    """Validate the whole resulting set in memory, then write the one item.

    An unsatisfiable result raises UnsatisfiableRuleSet carrying the conflicting
    existing rules and never reaches the repository (R16, R17)."""
    current = rules.get()
    try:
        apply_rule(current, rule)
    except UnsatisfiableRuleSet as exc:
        raise UnsatisfiableRuleSet(_existing_conflicts(current, rule)) from exc
    return rules.save_rule(rule)


def delete_rule(rule_id_value: str, *, rules: RuleRepository) -> int:
    """Rebuild the resulting set in memory (validating the id), then delete the
    one item. A removal only relaxes constraints, so it never unsatisfies."""
    remove_rule_by_id(rules.get(), rule_id_value)
    return rules.delete_rule(rule_id_value)
