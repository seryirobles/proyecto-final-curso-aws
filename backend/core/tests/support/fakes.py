"""In-memory fakes for the planner_core ports."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime

from planner_core.domain.calendar import IsoWeek, SlotRef
from planner_core.domain.candidate import SlotContents
from planner_core.domain.rollover import ArchivedWeek
from planner_core.domain.rules import RuleSet
from planner_core.domain.shopping import ShoppingItem, ShoppingItemNotFound
from planner_core.domain.text import normalize
from planner_core.domain.username_policy import UsernameAlreadyTaken
from planner_core.ports.accounts import AccountNotFound, AccountRecord
from planner_core.ports.recipes import LibraryRecipe, RecipeNotFound
from planner_core.ports.shopping_list import ShoppingListLockHeld


@dataclass
class FakeClock:
    """A `Clock` frozen at one explicit instant.

    It never advances and never consults a real clock, so a test that uses it
    cannot accidentally depend on the host's time or timezone. ``readings``
    records how often it was consulted, which is how the single-read rule of
    ``resolve_live_weeks`` is asserted.
    """

    instant: datetime
    readings: int = field(default=0)

    @classmethod
    def at(cls, iso_8601: str) -> FakeClock:
        """Build a clock from an ISO-8601 instant, e.g. `2026-07-16T10:00:00+00:00`."""
        return cls(datetime.fromisoformat(iso_8601))

    def now(self) -> datetime:
        self.readings += 1
        return self.instant


@dataclass
class FakeConfig:
    """A `ConfigPort` backed by a plain dict, never the host's real environment.

    ``readings`` counts every ``get`` call, mirroring ``FakeClock.readings``'
    role in asserting the single-read rule (docs/specs.md's own worked example).
    """

    values: dict[str, str] = field(default_factory=dict)
    readings: int = field(default=0)

    def get(self, key: str) -> str | None:
        self.readings += 1
        return self.values.get(key)


@dataclass
class FakeAccountRepository:
    """An `AccountRepository` over two dicts: accounts by id, and a folded-name
    reservation index. create/rename release/reserve through the reservation
    index, never by re-folding a caller-supplied old name (design.md section 4,
    section 5.2's trap: the old reservation is released by looking up the
    record actually stored under user_id)."""

    accounts: dict[str, AccountRecord] = field(default_factory=dict)
    reservations: dict[str, str] = field(default_factory=dict)  # folded username -> user_id

    def get_by_id(self, user_id: str) -> AccountRecord | None:
        return self.accounts.get(user_id)

    def get_by_username(self, username: str) -> AccountRecord | None:
        user_id = self.reservations.get(normalize(username))
        return None if user_id is None else self.accounts[user_id]

    def list_all(self) -> tuple[AccountRecord, ...]:
        return tuple(self.accounts.values())

    def create(self, account: AccountRecord) -> None:
        folded = normalize(account.username)
        if folded in self.reservations:
            raise UsernameAlreadyTaken(account.username)
        self.accounts[account.user_id] = account
        self.reservations[folded] = account.user_id

    def rename(self, user_id: str, new_username: str) -> None:
        existing = self.accounts.get(user_id)
        if existing is None:
            raise AccountNotFound(user_id)
        old_folded = normalize(existing.username)
        new_folded = normalize(new_username)
        if new_folded != old_folded and new_folded in self.reservations:
            raise UsernameAlreadyTaken(new_username)
        del self.reservations[old_folded]
        self.reservations[new_folded] = user_id
        self.accounts[user_id] = AccountRecord(
            user_id=user_id,
            username=new_username,
            role=existing.role,
            password_hash=existing.password_hash,
            password_reset_required=existing.password_reset_required,
            credentials_valid_since=existing.credentials_valid_since,
        )

    def update_credentials(
        self,
        user_id: str,
        password_hash: str,
        password_reset_required: bool,
        credentials_valid_since: datetime,
    ) -> None:
        existing = self.accounts.get(user_id)
        if existing is None:
            raise AccountNotFound(user_id)
        self.accounts[user_id] = AccountRecord(
            user_id=user_id,
            username=existing.username,
            role=existing.role,
            password_hash=password_hash,
            password_reset_required=password_reset_required,
            credentials_valid_since=credentials_valid_since,
        )

    def delete(self, user_id: str) -> None:
        existing = self.accounts.get(user_id)
        if existing is None:
            raise AccountNotFound(user_id)
        del self.accounts[user_id]
        del self.reservations[normalize(existing.username)]

    def revoke_credentials(self, user_id: str, revoked_at: datetime) -> None:
        existing = self.accounts.get(user_id)
        if existing is None:
            raise AccountNotFound(user_id)
        self.accounts[user_id] = AccountRecord(
            user_id=user_id,
            username=existing.username,
            role=existing.role,
            password_hash=existing.password_hash,
            password_reset_required=existing.password_reset_required,
            credentials_valid_since=revoked_at,
        )


@dataclass
class FakePasswordHasher:
    """A `PasswordHasher` stand-in: fast and deterministic, never the real
    600,000-iteration PBKDF2 loop (docs/conventions.md's fakes-not-mocks rule)."""

    prefix: str = "fake:"

    def hash(self, password: str) -> str:
        return self.prefix + password

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == self.prefix + password


@dataclass
class FakeRecipeRepository:
    """A `RecipeRepository` over a plain dict keyed by recipe id."""

    entries: dict[str, LibraryRecipe] = field(default_factory=dict)

    def get(self, recipe_id: str) -> LibraryRecipe | None:
        return self.entries.get(recipe_id)

    def list_all(self) -> tuple[LibraryRecipe, ...]:
        return tuple(self.entries.values())

    def save(self, entry: LibraryRecipe) -> None:
        self.entries[entry.id] = entry

    def delete(self, recipe_id: str) -> None:
        if recipe_id not in self.entries:
            raise RecipeNotFound(recipe_id)
        del self.entries[recipe_id]


@dataclass
class FakeWeekRepository:
    """A `WeekRepository` over a dict of dicts, keyed by `IsoWeek` then `SlotRef`."""

    weeks: dict[IsoWeek, dict[SlotRef, SlotContents]] = field(default_factory=dict)

    def get_week(self, week: IsoWeek) -> Mapping[SlotRef, SlotContents]:
        return dict(self.weeks.get(week, {}))

    def save_slot(self, week: IsoWeek, slot: SlotRef, contents: SlotContents) -> None:
        self.weeks.setdefault(week, {})[slot] = contents

    def save_week(self, week: IsoWeek, plans: Mapping[SlotRef, SlotContents]) -> None:
        self.weeks[week] = dict(plans)


@dataclass
class FakeRuleRepository:
    """A `RuleRepository` over a single stored `RuleSet`, defaulting to empty."""

    rule_set: RuleSet | None = None

    def get(self) -> RuleSet:
        return self.rule_set if self.rule_set is not None else RuleSet()

    def save(self, rule_set: RuleSet) -> None:
        self.rule_set = rule_set


@dataclass
class FakeShoppingListRepository:
    """A `ShoppingListRepository` over a dict of items plus one lock slot.

    `acquire_lock` compares `expires_at` against the caller-supplied `now` as
    data, never as a guarantee that a real TTL sweep already removed a stale
    lock (design.md section 4, section 5.3's trap)."""

    items: dict[str, ShoppingItem] = field(default_factory=dict)
    lock: tuple[str, datetime] | None = None  # (owner_id, expires_at)

    def list_items(self) -> tuple[ShoppingItem, ...]:
        return tuple(self.items.values())

    def save_item(self, item: ShoppingItem) -> None:
        self.items[item.id] = item

    def delete_item(self, item_id: str) -> None:
        if item_id not in self.items:
            raise ShoppingItemNotFound(item_id)
        del self.items[item_id]

    def delete_checked_items(self) -> None:
        self.items = {item_id: item for item_id, item in self.items.items() if not item.checked}

    def acquire_lock(self, owner_id: str, now: datetime, expires_at: datetime) -> None:
        if self.lock is not None:
            existing_owner, existing_expires_at = self.lock
            if existing_expires_at >= now:
                raise ShoppingListLockHeld(existing_owner)
        self.lock = (owner_id, expires_at)

    def release_lock(self, owner_id: str) -> None:
        if self.lock is not None and self.lock[0] == owner_id:
            self.lock = None


@dataclass
class FakeArchiveRepository:
    """An `ArchiveRepository` over a plain dict keyed by `IsoWeek`."""

    archives: dict[IsoWeek, ArchivedWeek] = field(default_factory=dict)

    def get(self, week: IsoWeek) -> ArchivedWeek | None:
        return self.archives.get(week)

    def save(self, archived: ArchivedWeek) -> None:
        self.archives[archived.week] = archived
