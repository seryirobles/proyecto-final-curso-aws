"""Contract suite for ShoppingListRepository: one suite, run against every
registered implementation (R9)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest
from planner_core.domain.shopping import ShoppingItem, ShoppingItemNotFound
from planner_core.domain.units import Unit
from planner_core.ports.shopping_list import ShoppingListLockHeld, ShoppingListRepository
from support.fakes import FakeShoppingListRepository

from tests.contract.dynamo_contract import dynamo_shopping_list_repository

IMPLEMENTATIONS: list[Callable[[], ShoppingListRepository]] = [
    FakeShoppingListRepository,
    dynamo_shopping_list_repository,
]

NOW = datetime(2026, 7, 20, 10, 0, tzinfo=UTC)


def _item(item_id: str = "i1", checked: bool = False) -> ShoppingItem:
    return ShoppingItem(id=item_id, name="Tomate", quantity=1, unit=Unit.UNIT, checked=checked)


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_save_then_list_and_delete_round_trip(
    repository_factory: Callable[[], ShoppingListRepository],
) -> None:
    repo = repository_factory()
    item = _item()

    repo.save_item(item)
    assert repo.list_items() == (item,)

    repo.delete_item("i1")
    assert repo.list_items() == ()


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_delete_item_raises_shopping_item_not_found_for_a_missing_id(
    repository_factory: Callable[[], ShoppingListRepository],
) -> None:
    with pytest.raises(ShoppingItemNotFound):
        repository_factory().delete_item("missing")


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_delete_checked_items_is_a_no_op_when_nothing_is_checked(
    repository_factory: Callable[[], ShoppingListRepository],
) -> None:
    repo = repository_factory()
    repo.save_item(_item("i1", checked=False))

    repo.delete_checked_items()

    assert repo.list_items() == (_item("i1", checked=False),)


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_acquire_lock_raises_when_held_and_unexpired_then_succeeds_once_expired(
    repository_factory: Callable[[], ShoppingListRepository],
) -> None:
    repo = repository_factory()
    repo.acquire_lock("owner-a", NOW, NOW + timedelta(minutes=5))

    with pytest.raises(ShoppingListLockHeld):
        repo.acquire_lock("owner-b", NOW, NOW + timedelta(minutes=5))

    later = NOW + timedelta(minutes=10)
    repo.acquire_lock("owner-b", later, later + timedelta(minutes=5))
    with pytest.raises(ShoppingListLockHeld):
        repo.acquire_lock("owner-a", later, later + timedelta(minutes=5))


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_acquire_lock_raises_at_the_exact_expiry_instant(
    repository_factory: Callable[[], ShoppingListRepository],
) -> None:
    """Boundary: expires_at == now is still held, per the port's `< now` contract."""
    repo = repository_factory()
    repo.acquire_lock("owner-a", NOW, NOW)

    with pytest.raises(ShoppingListLockHeld):
        repo.acquire_lock("owner-b", NOW, NOW + timedelta(minutes=5))


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_release_lock_is_a_no_op_for_a_non_owner(
    repository_factory: Callable[[], ShoppingListRepository],
) -> None:
    repo = repository_factory()
    repo.acquire_lock("owner-a", NOW, NOW + timedelta(minutes=5))

    repo.release_lock("owner-b")

    with pytest.raises(ShoppingListLockHeld):
        repo.acquire_lock("owner-c", NOW, NOW + timedelta(minutes=5))


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_release_lock_by_the_owner_frees_it_for_the_next_holder(
    repository_factory: Callable[[], ShoppingListRepository],
) -> None:
    """Positive path — pins the `#ownerId` alias target in the adapter's
    release condition (docs/data_model.md 5.3)."""
    repo = repository_factory()
    repo.acquire_lock("owner-a", NOW, NOW + timedelta(minutes=5))

    repo.release_lock("owner-a")

    repo.acquire_lock("owner-b", NOW, NOW + timedelta(minutes=5))


# --- change marker (FR-RT-01): R2, R4, R5, R8, R9, R11 ---


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_every_mutating_method_advances_the_marker_and_returns_the_new_value(
    repository_factory: Callable[[], ShoppingListRepository],
) -> None:
    repo = repository_factory()

    assert repo.save_item(_item("i1")) == 1  # R4, R5
    assert repo.current_version() == 1
    repo.save_item(_item("i2", checked=True))
    assert repo.delete_item("i1") == 3
    assert repo.delete_checked_items() == 4  # removed i2 (R5)
    assert repo.current_version() == 4


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_reads_leave_the_marker_unchanged(
    repository_factory: Callable[[], ShoppingListRepository],
) -> None:
    repo = repository_factory()
    repo.save_item(_item("i1"))

    repo.list_items()
    repo.current_version()
    repo.acquire_lock("owner-a", NOW, NOW + timedelta(minutes=5))
    repo.release_lock("owner-a")

    assert repo.current_version() == 1  # R2 — reads and the lock do not advance


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_two_successive_writes_both_apply_and_advance_the_marker_twice(
    repository_factory: Callable[[], ShoppingListRepository],
) -> None:
    repo = repository_factory()

    first = repo.save_item(_item("i1"))
    second = repo.save_item(_item("i1"))  # no raise: upsert, last-write-wins (R8)

    assert (first, second) == (1, 2)  # R11


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_delete_checked_items_with_nothing_checked_does_not_advance_the_marker(
    repository_factory: Callable[[], ShoppingListRepository],
) -> None:
    repo = repository_factory()
    repo.save_item(_item("i1", checked=False))

    assert repo.delete_checked_items() == 1  # R9 — returns the marker, no bump
    assert repo.current_version() == 1
