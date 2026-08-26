"""The week-rollover transition: archive the ending week, promote next to
current, initialize an empty next week, and clean bought shopping items —
composed as one pure, deterministic function (FR-MENU-06, FR-MENU-08, G-61)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from planner_core.domain.calendar import IsoWeek, SlotRef
from planner_core.domain.candidate import SlotContents
from planner_core.domain.shopping import ShoppingItem, unchecked_items


@dataclass(frozen=True)
class ArchivedWeek:
    """A closed week's full record: its menu and the shopping list as it
    stood before rollover cleanup (FR-ARCH-01, FR-ARCH-02). Frozen — no
    function in this module mutates one once built (R2)."""

    week: IsoWeek
    plans: Mapping[SlotRef, SlotContents]
    shopping_snapshot: tuple[ShoppingItem, ...]


@dataclass(frozen=True)
class RolloverResult:
    """The complete post-rollover state, produced by one call (FR-MENU-08)."""

    archived: ArchivedWeek
    new_current_plans: Mapping[SlotRef, SlotContents]
    new_next_plans: Mapping[SlotRef, SlotContents]
    shopping_items: tuple[ShoppingItem, ...]


def archive_week(
    week: IsoWeek,
    plans: Mapping[SlotRef, SlotContents],
    shopping_items: tuple[ShoppingItem, ...],
) -> ArchivedWeek:
    """Steps 1+2: snapshot the ending week's menu and the list, before
    cleanup (R1, R4, R5, R6; see design.md section 6, rejected alternative D,
    on why these two collapse)."""
    return ArchivedWeek(week=week, plans=plans, shopping_snapshot=shopping_items)


def promote_next_to_current(
    next_plans: Mapping[SlotRef, SlotContents],
) -> Mapping[SlotRef, SlotContents]:
    """Step 3: the former next week's plans become the new current week's,
    unchanged (R7, G-28)."""
    return next_plans


def init_empty_next_week() -> Mapping[SlotRef, SlotContents]:
    """Step 4: a fresh next week starts with no slots. Zero parameters, so no
    rule or generation input has anywhere to enter (R8, R10, G-15)."""
    return {}


def roll_over(
    former_current_week: IsoWeek,
    former_current_plans: Mapping[SlotRef, SlotContents],
    former_next_plans: Mapping[SlotRef, SlotContents],
    shopping_items: tuple[ShoppingItem, ...],
) -> RolloverResult:
    """The five-step transition, composed in order (FR-MENU-06, G-61).

    Total and deterministic: same arguments always return an equal result
    (R13); this is FR-MENU-08's retry-safety basis (design.md section 5).
    """
    archived = archive_week(former_current_week, former_current_plans, shopping_items)
    new_current_plans = promote_next_to_current(former_next_plans)
    new_next_plans = init_empty_next_week()
    cleaned_items = unchecked_items(shopping_items)
    return RolloverResult(
        archived=archived,
        new_current_plans=new_current_plans,
        new_next_plans=new_next_plans,
        shopping_items=cleaned_items,
    )
