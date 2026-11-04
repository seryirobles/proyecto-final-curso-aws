"""In-memory fakes for the planner_core ports."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime

from planner_core.domain.ai_output import RawIngredient, RawRecipeOutput
from planner_core.domain.calendar import IsoWeek, SlotRef
from planner_core.domain.candidate import SlotContents
from planner_core.domain.generation import (
    GenerationRequest,
    GenerationSnapshot,
    RunStatus,
    SingleRecipeRequest,
    SlotProgress,
    SlotStatus,
)
from planner_core.domain.recipe import Recipe
from planner_core.domain.role import Role
from planner_core.domain.rollover import ArchivedWeek
from planner_core.domain.rules import (
    CategoryCountRule,
    DisabledDay,
    PinRule,
    Rule,
    RuleSet,
    rule_id,
)
from planner_core.domain.shopping import ShoppingItem, ShoppingItemNotFound
from planner_core.domain.text import normalize
from planner_core.domain.username_policy import UsernameAlreadyTaken
from planner_core.ports.accounts import AccountAlreadyExists, AccountNotFound, AccountRecord
from planner_core.ports.ai_provider import AiPrompt
from planner_core.ports.generation_queue import ResultPayload, SlotNotRetryable, StoredGeneration
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
        if account.user_id in self.accounts:
            raise AccountAlreadyExists(account.user_id)
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

    def reset_admin_credentials(
        self, user_id: str, password_hash: str, credentials_valid_since: datetime
    ) -> None:
        existing = self.accounts.get(user_id)
        if existing is None or existing.role is not Role.ADMIN:
            raise AccountNotFound(user_id)
        self.update_credentials(user_id, password_hash, True, credentials_valid_since)

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

    def dummy_hash(self) -> str:
        return "dummy-hash-without-the-fake-prefix"


@dataclass
class FakeRecipeRepository:
    """A `RecipeRepository` over a plain dict keyed by recipe id.

    `version` is the in-memory change marker (docs/data_model.md section 1.1):
    a counter bumped inside each mutating method, 0 before any write."""

    entries: dict[str, LibraryRecipe] = field(default_factory=dict)
    version: int = 0

    def current_version(self) -> int:
        return self.version

    def get(self, recipe_id: str) -> LibraryRecipe | None:
        return self.entries.get(recipe_id)

    def list_all(self) -> tuple[LibraryRecipe, ...]:
        return tuple(self.entries.values())

    def save(self, entry: LibraryRecipe) -> int:
        self.entries[entry.id] = entry
        self.version += 1
        return self.version

    def delete(self, recipe_id: str) -> int:
        if recipe_id not in self.entries:
            raise RecipeNotFound(recipe_id)
        del self.entries[recipe_id]
        self.version += 1
        return self.version


@dataclass
class FakeWeekRepository:
    """A `WeekRepository` over a dict of dicts, keyed by `IsoWeek` then `SlotRef`.

    `versions` holds one change marker per week (docs/data_model.md section 1.1):
    a counter bumped inside each mutating method, 0 for a week never written."""

    weeks: dict[IsoWeek, dict[SlotRef, SlotContents]] = field(default_factory=dict)
    versions: dict[IsoWeek, int] = field(default_factory=dict)

    def current_version(self, week: IsoWeek) -> int:
        return self.versions.get(week, 0)

    def get_week(self, week: IsoWeek) -> Mapping[SlotRef, SlotContents]:
        return dict(self.weeks.get(week, {}))

    def save_slot(self, week: IsoWeek, slot: SlotRef, contents: SlotContents) -> int:
        self.weeks.setdefault(week, {})[slot] = contents
        self.versions[week] = self.versions.get(week, 0) + 1
        return self.versions[week]

    def save_week(self, week: IsoWeek, plans: Mapping[SlotRef, SlotContents]) -> int:
        self.weeks[week] = dict(plans)
        self.versions[week] = self.versions.get(week, 0) + 1
        return self.versions[week]


@dataclass
class FakeRuleRepository:
    """A `RuleRepository` over per-rule items keyed by natural id (GQ3).

    `version` is the in-memory change marker (docs/data_model.md section 1.1):
    a counter bumped inside each mutating method, 0 before any write. `writes`
    counts mutations so a test can assert an unsatisfiable change never wrote."""

    rules: dict[str, Rule] = field(default_factory=dict)
    version: int = 0
    writes: int = 0

    def current_version(self) -> int:
        return self.version

    def get(self) -> RuleSet:
        category_counts = tuple(r for r in self.rules.values() if isinstance(r, CategoryCountRule))
        pins = tuple(r for r in self.rules.values() if isinstance(r, PinRule))
        disabled_days = tuple(r.day for r in self.rules.values() if isinstance(r, DisabledDay))
        return RuleSet(category_counts=category_counts, pins=pins, disabled_days=disabled_days)

    def save_rule(self, rule: Rule) -> int:
        self.rules[rule_id(rule)] = rule
        self.version += 1
        self.writes += 1
        return self.version

    def delete_rule(self, rule_id: str) -> int:
        self.rules.pop(rule_id, None)
        self.version += 1
        self.writes += 1
        return self.version


@dataclass
class FakeShoppingListRepository:
    """A `ShoppingListRepository` over a dict of items plus one lock slot.

    `acquire_lock` compares `expires_at` against the caller-supplied `now` as
    data, never as a guarantee that a real TTL sweep already removed a stale
    lock (design.md section 4, section 5.3's trap)."""

    items: dict[str, ShoppingItem] = field(default_factory=dict)
    lock: tuple[str, datetime] | None = None  # (owner_id, expires_at)
    version: int = 0  # change marker (docs/data_model.md section 1.1), 0 before any write

    def current_version(self) -> int:
        return self.version

    def list_items(self) -> tuple[ShoppingItem, ...]:
        return tuple(self.items.values())

    def save_item(self, item: ShoppingItem) -> int:
        self.items[item.id] = item
        self.version += 1
        return self.version

    def save_items(self, items: Sequence[ShoppingItem]) -> int | None:
        if not items:  # R10 - no write, no bump
            return None
        for item in items:
            self.items[item.id] = item
        self.version += 1  # R8, R9 - one bump for the whole batch
        return self.version

    def delete_item(self, item_id: str) -> int:
        if item_id not in self.items:
            raise ShoppingItemNotFound(item_id)
        del self.items[item_id]
        self.version += 1
        return self.version

    def delete_checked_items(self) -> int:
        survivors = {item_id: item for item_id, item in self.items.items() if not item.checked}
        if len(survivors) != len(self.items):  # removed >= 1 checked item (R9)
            self.items = survivors
            self.version += 1
        return self.version

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


@dataclass
class SubmittedGeneration:
    """One hand-off recorded by FakeGenerationQueue; R40 asserts the enrichment."""

    idempotency_key: str
    request: GenerationRequest
    effective_rules: RuleSet
    prompt_version_id: str | None
    author: str | None


@dataclass
class SubmittedRecipe:
    """One single-recipe hand-off recorded by FakeGenerationQueue."""

    idempotency_key: str
    request: SingleRecipeRequest
    reference_recipe: Recipe | None
    prompt_version_id: str
    author: str


@dataclass
class FakeGenerationQueue:
    """A `GenerationQueue` over a dict of stored records and a list of submissions.

    `submissions` lets a test assert an idempotent hit enqueued nothing while a
    fresh request enqueued exactly once (design.md section 9); `submitted` keeps
    the enriched hand-off for R40."""

    stored: dict[str, StoredGeneration] = field(default_factory=dict)
    submissions: list[tuple[str, GenerationRequest]] = field(default_factory=list)
    submitted: list[SubmittedGeneration] = field(default_factory=list)
    discards: list[str] = field(default_factory=list)
    claims: list[str] = field(default_factory=list)
    results: dict[str, ResultPayload] = field(default_factory=dict)
    recipe_submitted: list[SubmittedRecipe] = field(default_factory=list)
    retries: list[tuple[str, int, int, str]] = field(default_factory=list)
    events: list[str] = field(default_factory=list)

    def stored_generation(self, idempotency_key: str) -> StoredGeneration | None:
        return self.stored.get(idempotency_key)

    def submit(
        self,
        idempotency_key: str,
        request: GenerationRequest,
        *,
        effective_rules: RuleSet,
        prompt_version_id: str | None = None,
        author: str | None = None,
    ) -> None:
        # AP25: the hand-off writes a pending record, mirroring the SQS adapter.
        self.submissions.append((idempotency_key, request))
        self.submitted.append(
            SubmittedGeneration(
                idempotency_key, request, effective_rules, prompt_version_id, author
            )
        )
        snapshot = GenerationSnapshot(
            request.week, request.mode, effective_rules, prompt_version_id or ""
        )
        self.stored.setdefault(
            idempotency_key,
            StoredGeneration(
                idempotency_key=idempotency_key, status="pending", slots=(), snapshot=snapshot
            ),
        )

    def submit_recipe(
        self,
        idempotency_key: str,
        request: SingleRecipeRequest,
        *,
        reference_recipe: Recipe | None,
        prompt_version_id: str,
        author: str,
    ) -> None:
        self.recipe_submitted.append(
            SubmittedRecipe(idempotency_key, request, reference_recipe, prompt_version_id, author)
        )
        self.stored.setdefault(
            idempotency_key, StoredGeneration(idempotency_key=idempotency_key, status="pending")
        )

    def discard(self, idempotency_key: str) -> None:
        # AP27: drop the record; a missing key is a no-op (HTTP DELETE idempotency).
        self.discards.append(idempotency_key)
        self.stored.pop(idempotency_key, None)

    def claim(self, idempotency_key: str) -> bool:
        # R36/R37: conditional pending -> running; only the first claim per key wins.
        record = self.stored.get(idempotency_key)
        if record is None or record.status != "pending":
            return False
        self.stored[idempotency_key] = replace(record, status="running")
        self.claims.append(idempotency_key)
        return True

    def record_result(self, idempotency_key: str, status: str, payload: ResultPayload) -> None:
        # R38/R39: unconditional; stored_generation then reports estado + resultado.
        self.results[idempotency_key] = payload
        self.events.append("record_result")
        self.stored[idempotency_key] = replace(
            self.stored[idempotency_key], status=status, result=json.dumps(payload)
        )

    def _put_slots(self, key: str, changes: tuple[SlotProgress, ...]) -> None:
        record = self.stored[key]
        merged = {(p.day, p.slot): p for p in record.slots or ()}
        merged.update({(p.day, p.slot): p for p in changes})
        ordered = tuple(merged[k] for k in sorted(merged))
        self.stored[key] = replace(record, slots=ordered)

    def begin_slots(self, idempotency_key: str, slots: tuple[SlotProgress, ...]) -> None:
        self.events.append("begin_slots")
        self._put_slots(idempotency_key, slots)

    def record_slot(self, idempotency_key: str, progress: SlotProgress) -> None:
        self.events.append(f"slot:{progress.day}-{progress.slot}:{progress.status.value}")
        self._put_slots(idempotency_key, (progress,))

    def claim_slot(self, idempotency_key: str, day: int, slot: int) -> bool:
        record = self.stored.get(idempotency_key)
        current = (
            next((p for p in (record.slots or ()) if (p.day, p.slot) == (day, slot)), None)
            if record
            else None
        )
        if current is None or current.status is not SlotStatus.PENDING:
            return False
        self._put_slots(idempotency_key, (SlotProgress(day, slot, SlotStatus.RUNNING),))
        return True

    def record_status(self, idempotency_key: str, status: RunStatus) -> None:
        self.events.append(f"status:{status.value}")
        self.stored[idempotency_key] = replace(self.stored[idempotency_key], status=status.value)

    def retry_slot(self, idempotency_key: str, day: int, slot: int, *, author: str) -> None:
        record = self.stored[idempotency_key]
        current = next((p for p in record.slots or () if (p.day, p.slot) == (day, slot)), None)
        if current is None or current.status is not SlotStatus.ERROR:
            raise SlotNotRetryable(f"{day}-{slot}")
        self._put_slots(idempotency_key, (SlotProgress(day, slot, SlotStatus.PENDING),))
        self.stored[idempotency_key] = replace(self.stored[idempotency_key], status="running")
        self.retries.append((idempotency_key, day, slot, author))


def _default_ai_output() -> RawRecipeOutput:
    # Non-empty tools (issue recipe-saved-without-required-sections, G-89):
    # feeds every week-generation success test via FakeAiProvider.
    return RawRecipeOutput(
        name="Ensalada templada de lentejas",
        ingredients=(RawIngredient(name="lentejas", quantity=200.0, unit="g"),),
        tools=("bol",),
        procedure=("Cocer las lentejas y servir templadas.",),
        category="legume",
    )


@dataclass
class FakeAiProvider:
    """An `AiProvider` returning `default_output` per call. `responses`, if set,
    is consumed first — each entry a RawRecipeOutput or an exception to raise.
    `calls` counts invocations so a disabled-gate test can assert zero."""

    default_output: RawRecipeOutput = field(default_factory=_default_ai_output)
    responses: list[RawRecipeOutput | Exception] = field(default_factory=list)
    calls: int = 0

    def generate(self, prompt: AiPrompt) -> RawRecipeOutput:
        self.calls += 1
        if self.responses:
            nxt = self.responses.pop(0)
            if isinstance(nxt, Exception):
                raise nxt
            return nxt
        return self.default_output


@dataclass
class FakeGenerationGate:
    """A `GenerationGate` returning a fixed boolean; `reads` counts the checks."""

    enabled: bool = True
    reads: int = 0

    def is_generation_enabled(self) -> bool:
        self.reads += 1
        return self.enabled
