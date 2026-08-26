"""The shopping-list repository port: persistence for COMPRA (docs/data_model.md section 1)."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from planner_core.domain.errors import PlannerError
from planner_core.domain.shopping import ShoppingItem


class ShoppingListLockHeld(PlannerError):
    """Raised when acquire_lock finds an unexpired lock held by another owner
    (FR-SHOP-10's serialization clause, docs/data_model.md section 5.3)."""

    owner_id: str

    def __init__(self, owner_id: str) -> None:
        super().__init__(owner_id)
        self.owner_id = owner_id


@runtime_checkable
class ShoppingListRepository(Protocol):
    """Persistence for the single shared shopping list, plus its re-sync lock."""

    def list_items(self) -> tuple[ShoppingItem, ...]: ...

    def save_item(self, item: ShoppingItem) -> None:
        """Create or overwrite by id (AP19 is a PutItem — an upsert)."""
        ...

    def delete_item(self, item_id: str) -> None:
        """Raises ShoppingItemNotFound (planner_core.domain.shopping)."""
        ...

    def delete_checked_items(self) -> None:
        """FR-SHOP-09 cleanup, out of covers. Idempotent: a no-op if none are
        checked (docs/architecture.md section 4, invariant 5)."""
        ...

    def acquire_lock(self, owner_id: str, now: datetime, expires_at: datetime) -> None:
        """Raises ShoppingListLockHeld unless no lock exists or the existing
        lock's expiry is before now — the ttl-is-data-not-a-guarantee rule
        (docs/data_model.md section 5.3). now and expires_at are caller-resolved
        instants, never read from an ambient clock inside this port."""
        ...

    def release_lock(self, owner_id: str) -> None:
        """A no-op, never a raise, when owner_id does not hold the lock — a
        stale holder whose lease already expired must not delete its
        successor's lock (section 5.3)."""
        ...
