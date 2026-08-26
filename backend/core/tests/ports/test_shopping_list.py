"""Tests for the ShoppingListRepository port and its in-memory fake."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

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
