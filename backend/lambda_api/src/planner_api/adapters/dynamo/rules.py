"""DynamoDB `RuleRepository` — GRUPOREGLAS partition (docs/data_model.md
section 1, section 4.5). GQ3: one REGLA#<idRegla> item per rule, keyed by the
rule's deterministic natural id; AP23/AP24 are single-item writes."""

from __future__ import annotations

from typing import Any

from planner_core.domain.calendar import MealSlot
from planner_core.domain.ingredient_category import parse_category
from planner_core.domain.rules import (
    CategoryCountRule,
    DisabledDay,
    PinRule,
    Rule,
    RuleSet,
    rule_id,
)

from planner_api.adapters.dynamo import _table

_REGLA_PREFIX = "REGLA#"


def _pk() -> str:
    return f"GRUPOREGLAS#{_table.RULES_ID}"


def _item(rule: Rule) -> dict[str, Any]:
    base: dict[str, Any] = {"PK": _pk(), "SK": f"{_REGLA_PREFIX}{rule_id(rule)}"}
    match rule:
        case CategoryCountRule():
            return {
                **base,
                "tipoRegla": "cat",
                "tipoAlimento": rule.category.value,
                "cantidad": rule.count,
            }
        case PinRule():
            return {
                **base,
                "tipoRegla": "pin",
                "numeroDia": rule.day,
                "numeroComida": rule.slot.value,
                "idPlato": rule.recipe_id,
            }
        case DisabledDay():
            return {**base, "tipoRegla": "day", "numeroDia": rule.day}


def _to_rule(item: dict[str, Any]) -> Rule:
    kind = str(item["tipoRegla"])
    if kind == "cat":
        return CategoryCountRule(
            category=parse_category(str(item["tipoAlimento"])),
            count=int(_table.decode_number(item["cantidad"])),
        )
    if kind == "pin":
        return PinRule(
            day=int(_table.decode_number(item["numeroDia"])),
            slot=MealSlot(int(_table.decode_number(item["numeroComida"]))),
            recipe_id=str(item["idPlato"]),
        )
    return DisabledDay(day=int(_table.decode_number(item["numeroDia"])))


class DynamoRuleRepository:
    def current_version(self) -> int:
        return _table.read_marker(_pk())

    def get(self) -> RuleSet:
        rules = [_to_rule(row) for row in _table.query_prefix(_pk(), _REGLA_PREFIX)]
        return RuleSet(
            category_counts=tuple(r for r in rules if isinstance(r, CategoryCountRule)),
            pins=tuple(r for r in rules if isinstance(r, PinRule)),
            disabled_days=tuple(r.day for r in rules if isinstance(r, DisabledDay)),
        )

    def save_rule(self, rule: Rule) -> int:
        return _table.commit(_pk(), [_table.put_action(_item(rule))])

    def delete_rule(self, rule_id: str) -> int:
        return _table.commit(_pk(), [_table.delete_action(_pk(), f"{_REGLA_PREFIX}{rule_id}")])
