"""Tests for generation requests, effective rules, target resolution and the key (R1-R25)."""

from __future__ import annotations

import dataclasses
from datetime import date

import pytest

from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import Candidate, SlotContents, promote
from planner_core.domain.generation import (
    GenerationMode,
    GenerationPlan,
    GenerationRequest,
    GenerationTargets,
    PinnedTarget,
    RuleOverride,
    SkippedPin,
    build_plan,
    effective_rules,
    idempotency_key,
    resolve_targets,
)
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Ingredient, MealSnapshot
from planner_core.domain.rules import CategoryCountRule, PinRule, RuleSet
from planner_core.domain.units import parse_unit

WEEK = IsoWeek(2026, 29)  # Monday 2026-07-13 through Sunday 2026-07-19.


def _meal(name: str, category: IngredientCategory) -> MealSnapshot:
    return MealSnapshot(
        name=name,
        ingredients=(Ingredient(name="ingrediente", quantity=1, unit=parse_unit("g")),),
        tools=(),
        procedure=(),
        category=category,
    )


def _definitive(id: str, category: IngredientCategory) -> SlotContents:
    candidate = Candidate(id=id, meal=_meal(id, category), author="u1")
    return promote(SlotContents(candidates=(candidate,)), id)


def _candidates_only(id: str) -> SlotContents:
    candidate = Candidate(id=id, meal=_meal(id, IngredientCategory.MEAT), author="u1")
    return SlotContents(candidates=(candidate,))


# --- GenerationMode (R1) -------------------------------------------------


def test_generation_mode_has_exactly_the_three_members() -> None:
    """R1."""
    assert {member.value for member in GenerationMode} == {"library_only", "ai_only", "mix"}
    assert GenerationMode.LIBRARY_ONLY.value == "library_only"
    assert GenerationMode.AI_ONLY.value == "ai_only"
    assert GenerationMode.MIX.value == "mix"


# --- RuleOverride and effective_rules (R2-R5) -----------------------------


def test_rule_override_fields_are_exactly_the_fixed_shape() -> None:
    """R2."""
    field_names = {f.name for f in dataclasses.fields(RuleOverride)}
    assert field_names == {"category_counts", "pins", "disabled_days"}

    override = RuleOverride()
    assert override.category_counts is None
    assert override.pins is None
    assert override.disabled_days is None


def test_rule_override_is_frozen() -> None:
    """R2: mutating means constructing a new instance (docs/conventions.md)."""
    override = RuleOverride()

    with pytest.raises(dataclasses.FrozenInstanceError):
        override.__setattr__("pins", ())


def test_effective_rules_returns_shared_unchanged_when_override_is_none() -> None:
    """R3."""
    shared = RuleSet(
        category_counts=(CategoryCountRule(category=IngredientCategory.MEAT, count=2),)
    )

    assert effective_rules(shared, None) == shared


def test_effective_rules_applies_the_override_when_given() -> None:
    """R4."""
    shared = RuleSet(
        category_counts=(CategoryCountRule(category=IngredientCategory.MEAT, count=2),)
    )
    override = RuleOverride(
        category_counts=(CategoryCountRule(category=IngredientCategory.FISH, count=1),),
        pins=(PinRule(day=1, slot=MealSlot.LUNCH, recipe_id="r1"),),
        disabled_days=(3,),
    )

    result = effective_rules(shared, override)

    assert result.category_counts == override.category_counts
    assert result.pins == override.pins
    assert result.disabled_days == override.disabled_days


def test_effective_rules_never_mutates_shared() -> None:
    """R5."""
    shared = RuleSet(disabled_days=(2,))
    before = shared.disabled_days

    effective_rules(shared, RuleOverride(disabled_days=(4,)))

    assert shared.disabled_days is before
    assert shared.disabled_days == (2,)


# --- Value shapes (R6-R8) -------------------------------------------------


def test_pinned_target_fields_are_exactly_the_fixed_shape() -> None:
    """R6."""
    field_names = {f.name for f in dataclasses.fields(PinnedTarget)}
    assert field_names == {"slot", "recipe_id"}


def test_pinned_target_is_frozen() -> None:
    """R6: mutating means constructing a new instance (docs/conventions.md)."""
    target = PinnedTarget(slot=SlotRef(date(2026, 7, 13), MealSlot.LUNCH), recipe_id="r1")

    with pytest.raises(dataclasses.FrozenInstanceError):
        target.__setattr__("recipe_id", "r2")


def test_skipped_pin_fields_are_exactly_the_fixed_shape() -> None:
    """R7."""
    field_names = {f.name for f in dataclasses.fields(SkippedPin)}
    assert field_names == {"slot", "pin"}


def test_skipped_pin_is_frozen() -> None:
    """R7: mutating means constructing a new instance (docs/conventions.md)."""
    skipped = SkippedPin(
        slot=SlotRef(date(2026, 7, 13), MealSlot.LUNCH),
        pin=PinRule(day=1, slot=MealSlot.LUNCH, recipe_id="r1"),
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        skipped.__setattr__("pin", PinRule(day=2, slot=MealSlot.DINNER, recipe_id="r2"))


def test_generation_targets_fields_are_exactly_the_fixed_shape() -> None:
    """R8."""
    field_names = {f.name for f in dataclasses.fields(GenerationTargets)}
    assert field_names == {
        "open_slots",
        "pinned_slots",
        "skipped_pins",
        "remaining_category_counts",
    }


def test_generation_targets_is_frozen() -> None:
    """R8: mutating means constructing a new instance (docs/conventions.md)."""
    targets = GenerationTargets(
        open_slots=(), pinned_slots=(), skipped_pins=(), remaining_category_counts=()
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        targets.__setattr__("open_slots", (SlotRef(date(2026, 7, 13), MealSlot.LUNCH),))


# --- resolve_targets (R9-R15) ---------------------------------------------


def test_resolve_targets_excludes_disabled_days() -> None:
    """R9."""
    rules = RuleSet(disabled_days=(3,))  # Wednesday

    targets = resolve_targets(WEEK, rules, WEEK.monday, {})

    wednesday = date(2026, 7, 15)
    assert all(slot.day != wednesday for slot in targets.open_slots)
    assert len(targets.open_slots) == 12  # 14 slots minus Wednesday's two


def test_resolve_targets_excludes_days_before_first_day() -> None:
    """R10: reuses calendar.slots_from, never days already past (G-45)."""
    first_day = date(2026, 7, 16)  # Thursday

    targets = resolve_targets(WEEK, RuleSet(), first_day, {})

    assert len(targets.open_slots) == 8
    assert all(slot.day >= first_day for slot in targets.open_slots)


def test_resolve_targets_resolves_pins_skips_and_category_remainder() -> None:
    """R11-R15: occupancy decides targets; an existing definitive outranks a pin (G-71)."""
    monday, wednesday, thursday = date(2026, 7, 13), date(2026, 7, 15), date(2026, 7, 16)
    friday, saturday, sunday = date(2026, 7, 17), date(2026, 7, 18), date(2026, 7, 19)

    rules = RuleSet(
        category_counts=(
            CategoryCountRule(category=IngredientCategory.MEAT, count=5),
            CategoryCountRule(category=IngredientCategory.FISH, count=1),
            CategoryCountRule(category=IngredientCategory.VEGETABLE, count=0),
        ),
        pins=(
            PinRule(day=2, slot=MealSlot.LUNCH, recipe_id="past-pin"),  # Tuesday: before first_day
            PinRule(day=4, slot=MealSlot.DINNER, recipe_id="thu-dinner-recipe"),
            PinRule(day=6, slot=MealSlot.LUNCH, recipe_id="sat-lunch-recipe"),
        ),
        disabled_days=(5,),  # Friday
    )
    occupancy = {
        SlotRef(monday, MealSlot.LUNCH): _definitive("past-meat", IngredientCategory.MEAT),
        SlotRef(wednesday, MealSlot.LUNCH): _definitive("past-veg", IngredientCategory.VEGETABLE),
        SlotRef(friday, MealSlot.LUNCH): _definitive("disabled-fish", IngredientCategory.FISH),
        SlotRef(thursday, MealSlot.LUNCH): _definitive("thu-lunch-meat", IngredientCategory.MEAT),
        SlotRef(saturday, MealSlot.LUNCH): _definitive("sat-lunch-meat", IngredientCategory.MEAT),
        SlotRef(saturday, MealSlot.DINNER): _candidates_only("sat-dinner-candidate"),
    }

    targets = resolve_targets(WEEK, rules, thursday, occupancy)

    # Thu lunch (occupied, no pin) is skipped silently; Thu dinner (unoccupied,
    # pinned) resolves; Sat lunch (occupied AND pinned) is reported (R11-R13).
    assert targets.open_slots == (
        SlotRef(saturday, MealSlot.DINNER),  # candidates-only slot stays open (R14)
        SlotRef(sunday, MealSlot.LUNCH),
        SlotRef(sunday, MealSlot.DINNER),
    )
    assert targets.pinned_slots == (
        PinnedTarget(slot=SlotRef(thursday, MealSlot.DINNER), recipe_id="thu-dinner-recipe"),
    )
    assert targets.skipped_pins == (
        SkippedPin(
            slot=SlotRef(saturday, MealSlot.LUNCH),
            pin=PinRule(day=6, slot=MealSlot.LUNCH, recipe_id="sat-lunch-recipe"),
        ),
    )
    # day=2's pin falls before first_day: out of scope, neither targeted nor reported.
    assert all(target.recipe_id != "past-pin" for target in targets.pinned_slots)
    assert all(skip.pin.recipe_id != "past-pin" for skip in targets.skipped_pins)

    # R15: a definitive on a disabled (Friday) or past (Monday, Wednesday) day
    # still counts toward the week's final state.
    assert targets.remaining_category_counts == (
        CategoryCountRule(category=IngredientCategory.MEAT, count=2),  # 5 - 3 occupied
        CategoryCountRule(category=IngredientCategory.FISH, count=0),  # 1 - 1 occupied
        CategoryCountRule(category=IngredientCategory.VEGETABLE, count=0),  # floors at zero
    )


# --- idempotency_key (R16-R19, R25) ---------------------------------------


def test_idempotency_key_is_deterministic_for_identical_inputs() -> None:
    """R16."""
    slot = SlotRef(date(2026, 7, 13), MealSlot.LUNCH)
    targets = GenerationTargets(
        open_slots=(slot,), pinned_slots=(), skipped_pins=(), remaining_category_counts=()
    )
    rules = RuleSet()

    key_one = idempotency_key(WEEK, targets, rules, GenerationMode.LIBRARY_ONLY)
    key_two = idempotency_key(WEEK, targets, rules, GenerationMode.LIBRARY_ONLY)

    assert key_one == key_two


def test_idempotency_key_ignores_construction_order_of_every_sorted_collection() -> None:
    """R16: two collections differing only by tuple order still hash equal (design.md section 6)."""
    slot_one = SlotRef(date(2026, 7, 13), MealSlot.LUNCH)
    slot_two = SlotRef(date(2026, 7, 14), MealSlot.DINNER)
    pin_a = PinRule(day=1, slot=MealSlot.LUNCH, recipe_id="r1")
    pin_b = PinRule(day=2, slot=MealSlot.DINNER, recipe_id="r2")
    rules_forward = RuleSet(
        category_counts=(
            CategoryCountRule(category=IngredientCategory.MEAT, count=2),
            CategoryCountRule(category=IngredientCategory.FISH, count=1),
        ),
        pins=(pin_a, pin_b),
        disabled_days=(3, 4),
    )
    rules_reversed = RuleSet(
        category_counts=(
            CategoryCountRule(category=IngredientCategory.FISH, count=1),
            CategoryCountRule(category=IngredientCategory.MEAT, count=2),
        ),
        pins=(pin_b, pin_a),
        disabled_days=(4, 3),
    )
    targets_forward = GenerationTargets(
        open_slots=(slot_one, slot_two),
        pinned_slots=(),
        skipped_pins=(),
        remaining_category_counts=(),
    )
    targets_reversed = GenerationTargets(
        open_slots=(slot_two, slot_one),
        pinned_slots=(),
        skipped_pins=(),
        remaining_category_counts=(),
    )

    key_forward = idempotency_key(WEEK, targets_forward, rules_forward, GenerationMode.MIX)
    key_reversed = idempotency_key(WEEK, targets_reversed, rules_reversed, GenerationMode.MIX)

    assert key_forward == key_reversed


def test_idempotency_key_changes_when_rules_change() -> None:
    """R17."""
    targets = GenerationTargets(
        open_slots=(), pinned_slots=(), skipped_pins=(), remaining_category_counts=()
    )
    rules_a = RuleSet(disabled_days=(1,))
    rules_b = RuleSet(disabled_days=(2,))

    key_a = idempotency_key(WEEK, targets, rules_a, GenerationMode.MIX)
    key_b = idempotency_key(WEEK, targets, rules_b, GenerationMode.MIX)

    assert key_a != key_b


def test_idempotency_key_changes_when_targets_change() -> None:
    """R18."""
    rules = RuleSet()
    targets_a = GenerationTargets(
        open_slots=(SlotRef(date(2026, 7, 13), MealSlot.LUNCH),),
        pinned_slots=(),
        skipped_pins=(),
        remaining_category_counts=(),
    )
    targets_b = GenerationTargets(
        open_slots=(SlotRef(date(2026, 7, 14), MealSlot.LUNCH),),
        pinned_slots=(),
        skipped_pins=(),
        remaining_category_counts=(),
    )

    key_a = idempotency_key(WEEK, targets_a, rules, GenerationMode.MIX)
    key_b = idempotency_key(WEEK, targets_b, rules, GenerationMode.MIX)

    assert key_a != key_b


def test_idempotency_key_changes_when_pinned_slots_change() -> None:
    """R18: pinned_slots alone must affect the hash — a free pinned slot and a
    slot already covered by a definitive (reported via skipped_pins, never
    hashed per design.md section 6) must not collide on the same key."""
    rules = RuleSet()
    shared_open_slots = (SlotRef(date(2026, 7, 13), MealSlot.LUNCH),)
    shared_skipped_pins = (
        SkippedPin(
            slot=SlotRef(date(2026, 7, 14), MealSlot.LUNCH),
            pin=PinRule(day=2, slot=MealSlot.LUNCH, recipe_id="r1"),
        ),
    )
    targets_with_pin = GenerationTargets(
        open_slots=shared_open_slots,
        pinned_slots=(
            PinnedTarget(slot=SlotRef(date(2026, 7, 15), MealSlot.DINNER), recipe_id="r2"),
        ),
        skipped_pins=shared_skipped_pins,
        remaining_category_counts=(),
    )
    targets_without_pin = GenerationTargets(
        open_slots=shared_open_slots,
        pinned_slots=(),
        skipped_pins=shared_skipped_pins,
        remaining_category_counts=(),
    )

    key_with_pin = idempotency_key(WEEK, targets_with_pin, rules, GenerationMode.MIX)
    key_without_pin = idempotency_key(WEEK, targets_without_pin, rules, GenerationMode.MIX)

    assert key_with_pin != key_without_pin


def test_idempotency_key_changes_when_week_changes() -> None:
    """R19."""
    targets = GenerationTargets(
        open_slots=(), pinned_slots=(), skipped_pins=(), remaining_category_counts=()
    )
    rules = RuleSet()

    key_a = idempotency_key(WEEK, targets, rules, GenerationMode.MIX)
    key_b = idempotency_key(IsoWeek(2026, 30), targets, rules, GenerationMode.MIX)

    assert key_a != key_b


def test_idempotency_key_changes_when_mode_changes() -> None:
    """R25: a mode switch alone is a deliberate different request (revision note, 2026-08-26)."""
    targets = GenerationTargets(
        open_slots=(), pinned_slots=(), skipped_pins=(), remaining_category_counts=()
    )
    rules = RuleSet()

    key_library = idempotency_key(WEEK, targets, rules, GenerationMode.LIBRARY_ONLY)
    key_ai = idempotency_key(WEEK, targets, rules, GenerationMode.AI_ONLY)

    assert key_library != key_ai


# --- GenerationRequest, GenerationPlan and build_plan (R20-R24) -----------


def test_generation_request_fields_are_exactly_the_fixed_shape() -> None:
    """R20."""
    field_names = {f.name for f in dataclasses.fields(GenerationRequest)}
    assert field_names == {"week", "mode", "rule_override"}

    request = GenerationRequest(week=WEEK, mode=GenerationMode.MIX)
    assert request.rule_override is None


def test_generation_request_is_frozen() -> None:
    """R20: mutating means constructing a new instance (docs/conventions.md)."""
    request = GenerationRequest(week=WEEK, mode=GenerationMode.MIX)

    with pytest.raises(dataclasses.FrozenInstanceError):
        request.__setattr__("mode", GenerationMode.AI_ONLY)


def test_generation_plan_fields_are_exactly_the_fixed_shape() -> None:
    """R21-R24: the shape build_plan's result carries."""
    field_names = {f.name for f in dataclasses.fields(GenerationPlan)}
    assert field_names == {"effective_rules", "targets", "mode", "idempotency_key"}


def test_build_plan_composes_effective_rules_targets_mode_and_key() -> None:
    """R21, R22, R23, R24."""
    shared = RuleSet(
        category_counts=(CategoryCountRule(category=IngredientCategory.MEAT, count=2),)
    )
    override = RuleOverride(
        category_counts=(CategoryCountRule(category=IngredientCategory.FISH, count=1),)
    )
    request = GenerationRequest(week=WEEK, mode=GenerationMode.AI_ONLY, rule_override=override)
    occupancy: dict[SlotRef, SlotContents] = {}
    first_day = WEEK.monday

    plan = build_plan(request, shared, first_day, occupancy)

    expected_rules = effective_rules(shared, override)
    expected_targets = resolve_targets(WEEK, expected_rules, first_day, occupancy)
    expected_key = idempotency_key(WEEK, expected_targets, expected_rules, request.mode)

    assert plan.effective_rules == expected_rules
    assert plan.targets == expected_targets
    assert plan.mode == GenerationMode.AI_ONLY
    assert plan.idempotency_key == expected_key


def test_build_plan_resubmitting_the_same_request_yields_the_same_key() -> None:
    """R24: proves one logical invocation survives a duplicate submission (FR-AI-08)."""
    shared = RuleSet()
    request = GenerationRequest(week=WEEK, mode=GenerationMode.LIBRARY_ONLY)
    occupancy: dict[SlotRef, SlotContents] = {}

    plan_one = build_plan(request, shared, WEEK.monday, occupancy)
    plan_two = build_plan(request, shared, WEEK.monday, occupancy)

    assert plan_one.idempotency_key == plan_two.idempotency_key
    assert plan_one.targets == plan_two.targets


def test_build_plan_reflects_a_mode_change_in_the_idempotency_key() -> None:
    """R24, R25: an otherwise-identical request with a different mode gets a different key."""
    shared = RuleSet()
    occupancy: dict[SlotRef, SlotContents] = {}
    request_library = GenerationRequest(week=WEEK, mode=GenerationMode.LIBRARY_ONLY)
    request_ai = GenerationRequest(week=WEEK, mode=GenerationMode.AI_ONLY)

    plan_library = build_plan(request_library, shared, WEEK.monday, occupancy)
    plan_ai = build_plan(request_ai, shared, WEEK.monday, occupancy)

    assert plan_library.idempotency_key != plan_ai.idempotency_key
