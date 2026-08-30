"""Tests for the ShoppingListRepository port and its in-memory fake."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import get_type_hints

import pytest
from support.fakes import FakeShoppingListRepository

from planner_core.domain.shopping import ShoppingItem, ShoppingItemNotFound
from planner_core.domain.units import Unit
from planner_core.ports.shopping_list import ShoppingListLockHeld, ShoppingListRepository

NOW = datetime(2026, 7, 20, 10, 0, tzinfo=UTC)


def _item(item_id: str = "i1", checked: bool = False) -> ShoppingItem:
    return ShoppingItem(id=item_id, name="Tomate", quantity=1, unit=Unit.UNIT, checked=checked)


def test_fake_shopping_list_repository_satisfies_the_port() -> None:
    assert isinstance(FakeShoppingListRepository(), ShoppingListRepository)


def test_save_then_list_and_delete_round_trip() -> None:
    repo = FakeShoppingListRepository()
    item = _item()

    repo.save_item(item)
    assert repo.list_items() == (item,)

    repo.delete_item("i1")
    assert repo.list_items() == ()


def test_delete_item_raises_shopping_item_not_found_for_a_missing_id() -> None:
    with pytest.raises(ShoppingItemNotFound):
        FakeShoppingListRepository().delete_item("missing")


def test_delete_checked_items_is_a_no_op_when_nothing_is_checked() -> None:
    repo = FakeShoppingListRepository()
    repo.save_item(_item("i1", checked=False))

    repo.delete_checked_items()

    assert repo.list_items() == (_item("i1", checked=False),)


def test_delete_checked_items_removes_only_checked_ones() -> None:
    repo = FakeShoppingListRepository()
    repo.save_item(_item("i1", checked=True))
    repo.save_item(_item("i2", checked=False))

    repo.delete_checked_items()

    assert repo.list_items() == (_item("i2", checked=False),)


def test_acquire_lock_raises_when_held_and_unexpired() -> None:
    repo = FakeShoppingListRepository()
    repo.acquire_lock("owner-a", NOW, NOW + timedelta(minutes=5))

    with pytest.raises(ShoppingListLockHeld):
        repo.acquire_lock("owner-b", NOW, NOW + timedelta(minutes=5))


def test_acquire_lock_raises_at_the_exact_expiry_instant() -> None:
    """Boundary: expires_at == now is still held, per the port's `< now` contract."""
    repo = FakeShoppingListRepository()
    repo.acquire_lock("owner-a", NOW, NOW)

    with pytest.raises(ShoppingListLockHeld):
        repo.acquire_lock("owner-b", NOW, NOW + timedelta(minutes=5))


def test_acquire_lock_succeeds_once_the_existing_lock_is_expired() -> None:
    repo = FakeShoppingListRepository()
    repo.acquire_lock("owner-a", NOW, NOW + timedelta(minutes=5))

    later = NOW + timedelta(minutes=10)
    repo.acquire_lock("owner-b", later, later + timedelta(minutes=5))

    # No raise: the new owner now holds it, provable by owner-a failing to acquire.
    with pytest.raises(ShoppingListLockHeld):
        repo.acquire_lock("owner-a", later, later + timedelta(minutes=5))


def test_release_lock_is_a_no_op_for_a_non_owner() -> None:
    repo = FakeShoppingListRepository()
    repo.acquire_lock("owner-a", NOW, NOW + timedelta(minutes=5))

    repo.release_lock("owner-b")

    with pytest.raises(ShoppingListLockHeld):
        repo.acquire_lock("owner-c", NOW, NOW + timedelta(minutes=5))


def test_release_lock_then_acquire_by_another_owner_succeeds() -> None:
    repo = FakeShoppingListRepository()
    repo.acquire_lock("owner-a", NOW, NOW + timedelta(minutes=5))

    repo.release_lock("owner-a")
    repo.acquire_lock("owner-b", NOW, NOW + timedelta(minutes=5))

    with pytest.raises(ShoppingListLockHeld):
        repo.acquire_lock("owner-c", NOW, NOW + timedelta(minutes=5))


# --- change marker (FR-RT-01): R2, R4, R5, R9 ---


def test_the_shopping_list_repository_protocol_pins_the_marker_surface() -> None:
    """R1: current_version and the int-returning writes are on the Protocol
    itself, not only the fake — deleting either from ports/shopping_list.py
    fails here. acquire_lock / release_lock stay -> None (design.md section 3)."""
    assert "current_version" in ShoppingListRepository.__dict__
    for method in ("save_item", "delete_item", "delete_checked_items"):
        assert get_type_hints(getattr(ShoppingListRepository, method))["return"] is int
    for method in ("acquire_lock", "release_lock"):
        assert get_type_hints(getattr(ShoppingListRepository, method))["return"] is type(None)


def test_current_version_is_zero_before_any_write() -> None:
    assert FakeShoppingListRepository().current_version() == 0  # R3


def test_save_item_and_delete_item_advance_the_marker_and_return_the_new_value() -> None:
    repo = FakeShoppingListRepository()

    saved = repo.save_item(_item("i1"))
    assert saved == 1  # R4, R5
    assert repo.current_version() == saved  # R4

    deleted = repo.delete_item("i1")
    assert deleted == 2
    assert repo.current_version() == deleted  # R4


def test_reads_do_not_advance_the_marker() -> None:
    repo = FakeShoppingListRepository()
    repo.save_item(_item("i1"))

    repo.list_items()
    repo.current_version()

    assert repo.current_version() == 1  # R2


def test_delete_checked_items_with_nothing_checked_returns_the_marker_without_advancing() -> None:
    repo = FakeShoppingListRepository()
    repo.save_item(_item("i1", checked=False))

    first = repo.delete_checked_items()
    second = repo.delete_checked_items()  # Level 4: idempotent, marker included

    assert (first, second) == (1, 1)  # R9 — returns the marker, does not advance
    assert repo.current_version() == 1


def test_delete_checked_items_advances_the_marker_when_it_removes_an_item() -> None:
    repo = FakeShoppingListRepository()
    repo.save_item(_item("i1", checked=True))
    repo.save_item(_item("i2", checked=False))

    returned = repo.delete_checked_items()

    assert returned == 3  # two saves + this removal (R5)
    assert repo.current_version() == returned
    assert repo.list_items() == (_item("i2", checked=False),)


def test_delete_checked_items_leaves_an_unchecked_item_byte_for_byte_untouched() -> None:
    repo = FakeShoppingListRepository()
    kept = _item("i2", checked=False)
    repo.save_item(_item("i1", checked=True))
    repo.save_item(kept)

    repo.delete_checked_items()

    assert repo.list_items() == (kept,)


def test_lock_operations_do_not_advance_the_marker() -> None:
    repo = FakeShoppingListRepository()
    repo.save_item(_item("i1"))

    repo.acquire_lock("owner-a", NOW, NOW + timedelta(minutes=5))
    repo.release_lock("owner-a")

    assert repo.current_version() == 1  # R2 — the lock is not shopping-list content
