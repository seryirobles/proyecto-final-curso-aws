"""Shopping-list editing (AP19-AP21) and the re-sync composition (FR-SHOP-06,
FR-SHOP-10, docs/rest_api_contract.md section 3.3)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime

from planner_core.domain.calendar import current_week, next_week
from planner_core.domain.shopping import (
    ShoppingItem,
    ShoppingItemNotFound,
    check_item,
    required_shopping_items,
    resync,
    uncheck_item,
)
from planner_core.ports.shopping_list import ShoppingListRepository
from planner_core.ports.weeks import WeekRepository


@dataclass(frozen=True)
class ResyncOutcome:
    """The full list after the additive merge, plus the marker of the last item
    write. `marker` is None when the list was already in sync and nothing was
    written (feature 16 then keeps the client's held marker)."""

    items: tuple[ShoppingItem, ...]
    marker: int | None


@dataclass(frozen=True)
class ShoppingView:
    """AP18 read: the shopping-list items plus its change marker (R34), marker
    read before the payload (R35)."""

    items: tuple[ShoppingItem, ...]
    marker: int


def list_shopping(*, shopping: ShoppingListRepository) -> ShoppingView:
    """AP18 — the shopping-list items and its marker, marker read first."""
    marker = shopping.current_version()  # marker before payload (R35)
    return ShoppingView(items=shopping.list_items(), marker=marker)


def poll_marker(*, shopping: ShoppingListRepository) -> int:
    """Feature 26's conditional-GET short-circuit: the marker alone, without
    `list_items`'s payload — keeps the marker name out of `planner_api/routing.py`
    (test_change_marker_is_not_a_write_condition.py's R12 scan, feature 27)."""
    return shopping.current_version()


def save_item(item: ShoppingItem, *, shopping: ShoppingListRepository) -> int:
    """AP19 — add or edit by id (upsert)."""
    return shopping.save_item(item)


def set_checked(item_id: str, checked: bool, *, shopping: ShoppingListRepository) -> int:
    """AP19 (PATCH) — the check/uncheck path (FR-SHOP-07)."""
    items = shopping.list_items()
    if not any(i.id == item_id for i in items):
        raise ShoppingItemNotFound(item_id)
    flipped = (check_item if checked else uncheck_item)(items, item_id)
    changed = next(i for i in flipped if i.id == item_id)
    return shopping.save_item(changed)


def delete_item(item_id: str, *, shopping: ShoppingListRepository) -> int:
    """AP20."""
    return shopping.delete_item(item_id)


def delete_checked(*, shopping: ShoppingListRepository) -> int:
    """AP21 — a no-op with nothing checked does not bump the marker."""
    return shopping.delete_checked_items()


def resync_shopping_list(
    owner_id: str,
    today: date,
    now: datetime,
    lock_expires_at: datetime,
    new_ids: Sequence[str],
    *,
    shopping: ShoppingListRepository,
    weeks: WeekRepository,
) -> ResyncOutcome:
    """Acquire the FR-SHOP-10 lock, read the in-scope definitive meals in-process
    (AP9), additively merge onto the list, release the lock.

    Never removes an item (R21) and never writes a checked one (R22): those
    guarantees are the domain resync's (G-77). A held lock raises
    ShoppingListLockHeld before the week is read (R23, R24)."""
    shopping.acquire_lock(owner_id, now, lock_expires_at)
    try:
        plans = {
            **weeks.get_week(current_week(today)),
            **weeks.get_week(next_week(today)),
        }
        required = required_shopping_items(plans, today)
        before = shopping.list_items()
        merged = resync(before, required, new_ids)

        by_id = {item.id: item for item in before}
        changed = tuple(item for item in merged if by_id.get(item.id) != item)
        marker = shopping.save_items(changed)  # one bump per re-sync (feature 26, R8, R9)
    finally:
        shopping.release_lock(owner_id)
    return ResyncOutcome(items=merged, marker=marker)
