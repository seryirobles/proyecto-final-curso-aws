"""Shared generation rules and satisfiability: category counts, pins, disabled days."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from planner_core.domain.calendar import MealSlot
from planner_core.domain.errors import PlannerError
from planner_core.domain.ingredient_category import IngredientCategory

DAYS_PER_WEEK: Final[int] = 7
SLOTS_PER_DAY: Final[int] = len(MealSlot)
TOTAL_SLOTS: Final[int] = DAYS_PER_WEEK * SLOTS_PER_DAY
WEEKDAYS: Final[frozenset[int]] = frozenset(range(1, DAYS_PER_WEEK + 1))


class InvalidWeekday(PlannerError):
    """Raised when a day value is not one of the seven weekdays (1..7)."""

    value: int

    def __init__(self, value: int) -> None:
        super().__init__(value)
        self.value = value


class UnsatisfiableRuleSet(PlannerError):
    """Raised when a RuleSet's own rules cannot all hold at once (FR-RULE-07).

    `conflicting` carries the existing rules that clash with an attempted change
    (R16); empty when raised from bare RuleSet validation."""

    conflicting: tuple[Rule, ...]

    def __init__(self, conflicting: tuple[Rule, ...] = ()) -> None:
        super().__init__(conflicting)
        self.conflicting = conflicting


@dataclass(frozen=True)
class CategoryCountRule:
    """How many meals of one ingredient category the week should hold."""

    category: IngredientCategory
    count: int


@dataclass(frozen=True)
class PinRule:
    """A library recipe pinned to one day/slot."""

    day: int
    slot: MealSlot
    recipe_id: str


@dataclass(frozen=True)
class DisabledDay:
    """A single disabled weekday, addressable as one rule item (GQ3,
    docs/data_model.md section 4.5 — one REGLA#<idRegla> per rule)."""

    day: int

    def __post_init__(self) -> None:
        if self.day not in WEEKDAYS:
            raise InvalidWeekday(self.day)


class PinRulesAffected(PlannerError):
    """Raised when a library-recipe delete would leave pin rules dangling and
    the caller has not confirmed the cascade (docs/rest_api_contract.md section 3.4)."""

    pins: tuple[PinRule, ...]

    def __init__(self, pins: tuple[PinRule, ...]) -> None:
        super().__init__(pins)
        self.pins = pins


Rule = CategoryCountRule | PinRule | DisabledDay


def rule_id(rule: Rule) -> str:
    """The deterministic natural-key id of a rule (design.md section 3):
    cat#<category>, pin#<day>#<slot>, day#<day>."""
    match rule:
        case CategoryCountRule():
            return f"cat#{rule.category.value}"
        case PinRule():
            return f"pin#{rule.day}#{rule.slot.value}"
        case DisabledDay():
            return f"day#{rule.day}"


@dataclass(frozen=True)
class RuleSet:
    """The shared generation rules. Applies to every week by construction (FR-RULE-01)."""

    category_counts: tuple[CategoryCountRule, ...] = ()
    pins: tuple[PinRule, ...] = ()
    disabled_days: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        for day in self.disabled_days:
            if day not in WEEKDAYS:
                raise InvalidWeekday(day)
        for pin in self.pins:
            if pin.day not in WEEKDAYS:
                raise InvalidWeekday(pin.day)

        available = TOTAL_SLOTS - SLOTS_PER_DAY * len(self.disabled_days)
        total_required = sum(rule.count for rule in self.category_counts)
        if total_required > available:
            raise UnsatisfiableRuleSet()

        disabled = set(self.disabled_days)
        if any(pin.day in disabled for pin in self.pins):
            raise UnsatisfiableRuleSet()


@dataclass(frozen=True)
class RemovePinsResult:
    """The rule set after a cascade removal, plus exactly what was removed (G-20)."""

    rule_set: RuleSet
    removed_pins: tuple[PinRule, ...]


def set_category_count(rule_set: RuleSet, category: IngredientCategory, count: int) -> RuleSet:
    """Replace the rule for category, keeping every other category's rule unchanged."""
    kept = tuple(rule for rule in rule_set.category_counts if rule.category != category)
    return RuleSet(
        category_counts=(*kept, CategoryCountRule(category=category, count=count)),
        pins=rule_set.pins,
        disabled_days=rule_set.disabled_days,
    )


def remove_category_count(rule_set: RuleSet, category: IngredientCategory) -> RuleSet:
    """Drop the rule for category; a no-op if none exists (design.md section 8, alt D)."""
    kept = tuple(rule for rule in rule_set.category_counts if rule.category != category)
    return RuleSet(
        category_counts=kept,
        pins=rule_set.pins,
        disabled_days=rule_set.disabled_days,
    )


def set_pin(rule_set: RuleSet, day: int, slot: MealSlot, recipe_id: str) -> RuleSet:
    """Replace the pin for (day, slot), keeping every other pin unchanged."""
    kept = tuple(pin for pin in rule_set.pins if (pin.day, pin.slot) != (day, slot))
    return RuleSet(
        category_counts=rule_set.category_counts,
        pins=(*kept, PinRule(day=day, slot=slot, recipe_id=recipe_id)),
        disabled_days=rule_set.disabled_days,
    )


def remove_pin(rule_set: RuleSet, day: int, slot: MealSlot) -> RuleSet:
    """Drop the pin for (day, slot); a no-op if none exists (design.md section 8, alt D)."""
    kept = tuple(pin for pin in rule_set.pins if (pin.day, pin.slot) != (day, slot))
    return RuleSet(
        category_counts=rule_set.category_counts,
        pins=kept,
        disabled_days=rule_set.disabled_days,
    )


def disable_day(rule_set: RuleSet, day: int) -> RuleSet:
    """Add day to disabled_days; idempotent if already disabled."""
    if day in rule_set.disabled_days:
        return rule_set
    return RuleSet(
        category_counts=rule_set.category_counts,
        pins=rule_set.pins,
        disabled_days=(*rule_set.disabled_days, day),
    )


def enable_day(rule_set: RuleSet, day: int) -> RuleSet:
    """Remove day from disabled_days; a no-op if not disabled (design.md section 8, alt D)."""
    return RuleSet(
        category_counts=rule_set.category_counts,
        pins=rule_set.pins,
        disabled_days=tuple(d for d in rule_set.disabled_days if d != day),
    )


def max_selectable_count(rule_set: RuleSet, category: IngredientCategory) -> int:
    """The highest count category could take without exceeding available slots (FR-RULE-07)."""
    available = TOTAL_SLOTS - SLOTS_PER_DAY * len(rule_set.disabled_days)
    other = sum(rule.count for rule in rule_set.category_counts if rule.category != category)
    return max(0, available - other)


def available_days_for_pin(rule_set: RuleSet) -> tuple[int, ...]:
    """The weekdays not disabled, in ascending order."""
    return tuple(sorted(WEEKDAYS - set(rule_set.disabled_days)))


def available_days_to_disable(rule_set: RuleSet) -> tuple[int, ...]:
    """The weekdays neither disabled nor already carrying a pin, in ascending order."""
    pinned = {pin.day for pin in rule_set.pins}
    return tuple(sorted(WEEKDAYS - set(rule_set.disabled_days) - pinned))


def remove_pins_referencing(rule_set: RuleSet, recipe_id: str) -> RemovePinsResult:
    """Cascade-remove every pin naming recipe_id (G-20): a deleted recipe leaves no dangling pin."""
    removed = tuple(pin for pin in rule_set.pins if pin.recipe_id == recipe_id)
    kept = tuple(pin for pin in rule_set.pins if pin.recipe_id != recipe_id)
    new_rule_set = RuleSet(
        category_counts=rule_set.category_counts,
        pins=kept,
        disabled_days=rule_set.disabled_days,
    )
    return RemovePinsResult(rule_set=new_rule_set, removed_pins=removed)


class InvalidRuleId(PlannerError):
    """Raised when a rule id does not match a known natural-key prefix."""

    value: str

    def __init__(self, value: str) -> None:
        super().__init__(value)
        self.value = value


def apply_rule(rule_set: RuleSet, rule: Rule) -> RuleSet:
    """Apply one per-rule change through the existing natural-key mutators; the
    resulting RuleSet validates itself in __post_init__ (design.md section 3)."""
    match rule:
        case CategoryCountRule():
            return set_category_count(rule_set, rule.category, rule.count)
        case PinRule():
            return set_pin(rule_set, rule.day, rule.slot, rule.recipe_id)
        case DisabledDay():
            return disable_day(rule_set, rule.day)


def remove_rule_by_id(rule_set: RuleSet, rule_id_value: str) -> RuleSet:
    """Drop the rule the natural-key id names; a no-op if none matches
    (design.md section 3, mirrors the per-mutator no-op contract)."""
    kind, _, rest = rule_id_value.partition("#")
    try:
        if kind == "cat":
            return remove_category_count(rule_set, IngredientCategory(rest))
        if kind == "pin":
            day_str, _, slot_str = rest.partition("#")
            return remove_pin(rule_set, int(day_str), MealSlot(int(slot_str)))
        if kind == "day":
            return enable_day(rule_set, int(rest))
    except ValueError as exc:
        # A known prefix with a malformed body is still an invalid id, not a
        # 500: raise the named domain exception (architecture.md section 4, invariant 12).
        raise InvalidRuleId(rule_id_value) from exc
    raise InvalidRuleId(rule_id_value)


def apply_override(
    shared: RuleSet,
    category_counts: tuple[CategoryCountRule, ...] | None = None,
    pins: tuple[PinRule, ...] | None = None,
    disabled_days: tuple[int, ...] | None = None,
) -> RuleSet:
    """Compose a per-run effective RuleSet; shared is never written to (FR-RULE-05, G-06)."""
    return RuleSet(
        category_counts=shared.category_counts if category_counts is None else category_counts,
        pins=shared.pins if pins is None else pins,
        disabled_days=shared.disabled_days if disabled_days is None else disabled_days,
    )
