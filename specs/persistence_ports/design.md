# persistence_ports — Design

> Feature 14 · tier 2 · `planner_core.ports` + `backend/core/tests/support` +
> `backend/tests/contract`
> Read `requirements.md` first. Depends on feature 5 `week_plan_model`,
> feature 6 `rules_model`, feature 8 `shopping_list_state` (all `done`);
> reuses feature 2 `week_calendar`, feature 4 `recipe_model`, feature 9
> `password_policy` and feature 13 `rollover_job_logic` (all `done`) — see
> `requirements.md` § *Depends on*.

## 0. What this feature is, and is not

**Is:** six `typing.Protocol` definitions in `planner_core/ports/`, an
in-memory fake for each in `backend/core/tests/support/fakes.py`, and one
parametrized contract-test suite per port in `backend/tests/contract/`.

**Is not:** a real adapter. No `boto3`, no DynamoDB item shapes, no
transaction code. `docs/architecture.md` §1.2.2 draws the line precisely: a
port's *default implementation* — one importing nothing outside the standard
library — ships beside the `Protocol`; only an implementation that pulls in
an external dependency is an adapter, and adapters live in the Lambda
package that owns that dependency. Every fake this feature adds imports
nothing beyond `dataclasses`, `typing`, `collections.abc` and sibling
`planner_core` modules, so it is a default implementation by that same test
— not a smell, and not a step toward a real adapter that happens to live in
the wrong place. `lambda_api/adapters/` (empty today) is where a real
DynamoDB adapter implementing these same six `Protocol`s eventually lives,
once `docs/architecture.md` §2 P6 (deployment topology) is decided. That is
future work, not this feature's.

## 1. Layering

`docs/architecture.md` §3, §3.1:

| Piece | Layer | Why |
|---|---|---|
| `AccountRepository`, `RecipeRepository`, `WeekRepository`, `RuleRepository`, `ShoppingListRepository`, `ArchiveRepository` and their value types (`AccountRecord`, `LibraryRecipe`) | `planner_core/ports/` | Interfaces. Rule 2: `application/` imports `domain/` and `ports/`; a port importing `domain/` types for its method signatures (`SlotContents`, `RuleSet`, `ShoppingItem`, `Recipe`, `ArchivedWeek`, `IsoWeek`, `SlotRef`) is the normal, expected shape of a repository port — every existing repository-port example in this codebase's peers works this way (`ports/clock.py` imports nothing from `domain/` only because `datetime` has no domain type to reference). |
| `FakeAccountRepository`, `FakeRecipeRepository`, `FakeWeekRepository`, `FakeRuleRepository`, `FakeShoppingListRepository`, `FakeArchiveRepository` | `backend/core/tests/support/fakes.py` | Fakes implementing ports, `docs/conventions.md` § *Tests*: "Fakes, not mocks, for our own ports... live in `backend/core/tests/support/` so contract tests can reuse them." |
| Contract suites (one file per port) | `backend/tests/contract/` | `docs/architecture.md` §3.2: "for every port, one suite in `backend/tests/contract/` runs against both the in-memory fake and the real adapter." |
| Mechanical import-scan tests (R7, R10) | `backend/core/tests/test_ports_are_storage_agnostic.py` | Same technique and same directory level as the existing `backend/core/tests/test_no_ambient_time.py` (§1.2.2) — a mechanical, not eyeballed, guard. |

No `application/` piece. Nothing in `planner_core/application/` calls any of
these ports yet — every application-layer use case that would (feature 15
`auth_flow`, and the rollover/generation orchestration features) is blocked
on architecture §2 items this feature does not touch. `R8`'s "used by
application-layer tests" acceptance bullet is satisfied by a **test**, not
new `application/` source — see §8.

## 2. Files

### Created

| Path | Contents |
|---|---|
| `backend/core/src/planner_core/ports/accounts.py` | `AccountRecord`, `AccountNotFound`, `AccountRepository`. |
| `backend/core/src/planner_core/ports/recipes.py` | `LibraryRecipe`, `RecipeNotFound`, `RecipeRepository`. |
| `backend/core/src/planner_core/ports/weeks.py` | `WeekRepository`. |
| `backend/core/src/planner_core/ports/rules.py` | `RuleRepository`. |
| `backend/core/src/planner_core/ports/shopping_list.py` | `ShoppingListLockHeld`, `ShoppingListRepository`. |
| `backend/core/src/planner_core/ports/archive.py` | `ArchiveRepository`. |
| `backend/core/tests/ports/test_accounts.py` … `test_archive.py` | One conformance-test module per port, mirroring `tests/ports/test_clock.py` — `isinstance(fake, Port)` plus one behavioural test per method. |
| `backend/core/tests/test_ports_are_storage_agnostic.py` | R7, R10: mechanical import-allowlist scan. |
| `backend/core/tests/application/test_persistence_fakes_compose.py` | R8's "used by application-layer tests" bullet — see §8. |
| `backend/tests/contract/conftest.py` | Adds `backend/core/tests` to `sys.path` so contract tests can `from support.fakes import ...` — see §6. |
| `backend/tests/contract/test_account_repository_contract.py` … `test_archive_repository_contract.py` | R9: one parametrized suite per port. |

### Modified

| Path | Change |
|---|---|
| `backend/core/tests/support/fakes.py` | Add `FakeAccountRepository`, `FakeRecipeRepository`, `FakeWeekRepository`, `FakeRuleRepository`, `FakeShoppingListRepository`, `FakeArchiveRepository`, appended after the existing `FakeClock`/`FakeConfig`. |

No `pyproject.toml` change anywhere: every new module imports only stdlib
plus sibling `planner_core` code. `planner-core` keeps `dependencies = []`.

## 3. Signatures

```python
# backend/core/src/planner_core/ports/accounts.py
"""The account repository port: persistence for USUARIOS (docs/data_model.md section 1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from planner_core.domain.errors import PlannerError


@dataclass(frozen=True)
class AccountRecord:
    """One persisted account (DatosUsuario). role is an opaque string here —
    no domain Role model exists yet; feature 15 auth_flow owns that (design.md section 7)."""

    user_id: str
    username: str
    role: str
    password_hash: str
    password_reset_required: bool


class AccountNotFound(PlannerError):
    """Raised when an operation targets a user_id absent from the repository."""

    user_id: str

    def __init__(self, user_id: str) -> None:
        super().__init__(user_id)
        self.user_id = user_id


@runtime_checkable
class AccountRepository(Protocol):
    """Persistence for user accounts and the username reservation (FR-AUTH-17,
    docs/data_model.md section 5.1, section 5.2). Username uniqueness and the
    rename-releases-its-reservation lookup are the implementation's job, not
    the caller's: create() and rename() are each one atomic operation from
    the caller's point of view."""

    def get_by_id(self, user_id: str) -> AccountRecord | None: ...

    def get_by_username(self, username: str) -> AccountRecord | None:
        """Case-/accent-/whitespace-insensitive match (docs/data_model.md section 2, the fold)."""
        ...

    def list_all(self) -> tuple[AccountRecord, ...]: ...

    def create(self, account: AccountRecord) -> None:
        """Raises UsernameAlreadyTaken if the folded username is already reserved."""
        ...

    def rename(self, user_id: str, new_username: str) -> None:
        """Raises AccountNotFound or UsernameAlreadyTaken. Releases the old
        reservation by looking it up, never by re-folding the old name
        (docs/data_model.md section 5.2 — the trap)."""
        ...

    def update_credentials(
        self, user_id: str, password_hash: str, password_reset_required: bool
    ) -> None:
        """Raises AccountNotFound."""
        ...

    def delete(self, user_id: str) -> None:
        """Raises AccountNotFound. Releases the username reservation too (section 5.2)."""
        ...
```

```python
# backend/core/src/planner_core/ports/recipes.py
"""The recipe repository port: persistence for BIBLIOTECA (docs/data_model.md section 1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from planner_core.domain.errors import PlannerError
from planner_core.domain.recipe import Recipe


@dataclass(frozen=True)
class LibraryRecipe:
    """A library recipe as persisted: its id and author alongside its Recipe
    content. Recipe itself carries neither (design.md section 7)."""

    id: str
    recipe: Recipe
    author: str


class RecipeNotFound(PlannerError):
    """Raised when an operation targets a recipe_id absent from the repository."""

    recipe_id: str

    def __init__(self, recipe_id: str) -> None:
        super().__init__(recipe_id)
        self.recipe_id = recipe_id


@runtime_checkable
class RecipeRepository(Protocol):
    """Persistence for the shared recipe library."""

    def get(self, recipe_id: str) -> LibraryRecipe | None: ...

    def list_all(self) -> tuple[LibraryRecipe, ...]: ...

    def save(self, entry: LibraryRecipe) -> None:
        """Create or overwrite by id (AP16 is a PutItem — an upsert)."""
        ...

    def delete(self, recipe_id: str) -> None:
        """Raises RecipeNotFound."""
        ...
```

```python
# backend/core/src/planner_core/ports/weeks.py
"""The week repository port: persistence for SEMANA (docs/data_model.md section 1)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from planner_core.domain.calendar import IsoWeek, SlotRef
from planner_core.domain.candidate import SlotContents


@runtime_checkable
class WeekRepository(Protocol):
    """Persistence for a live week's slot contents. Operates at SlotContents
    granularity, not DynamoDB's per-item split (candidates vs. the DEFINITIVO
    pointer) — design.md section 9, rejected alternative A."""

    def get_week(self, week: IsoWeek) -> Mapping[SlotRef, SlotContents]:
        """Returns an empty mapping for a week with no data yet — weeks are
        created lazily on first write (docs/data_model.md section 9)."""
        ...

    def save_slot(self, week: IsoWeek, slot: SlotRef, contents: SlotContents) -> None:
        """Overwrite one slot's contents. contents is already invariant-checked
        by SlotContents.__post_init__ before this is ever called."""
        ...

    def save_week(self, week: IsoWeek, plans: Mapping[SlotRef, SlotContents]) -> None:
        """Overwrite every slot at once — rollover's promote/init steps need
        a whole-week write, not fourteen slot writes (FR-MENU-06, out of covers,
        cited only as the caller this method exists for)."""
        ...
```

```python
# backend/core/src/planner_core/ports/rules.py
"""The rule repository port: persistence for GRUPOREGLAS (docs/data_model.md section 1)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from planner_core.domain.rules import RuleSet


@runtime_checkable
class RuleRepository(Protocol):
    """Persistence for the single shared rule set (docs/data_model.md section 7:
    GRUPOREGLAS is a single-value partition — one household, one rule set)."""

    def get(self) -> RuleSet:
        """Returns RuleSet() (all-empty) if never written."""
        ...

    def save(self, rule_set: RuleSet) -> None: ...
```

```python
# backend/core/src/planner_core/ports/shopping_list.py
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
```

```python
# backend/core/src/planner_core/ports/archive.py
"""The archive repository port: persistence for a rolled-over week's frozen
record (FR-ARCH-01, FR-ARCH-02, out of covers; docs/data_model.md section 9)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from planner_core.domain.calendar import IsoWeek
from planner_core.domain.rollover import ArchivedWeek


@runtime_checkable
class ArchiveRepository(Protocol):
    """Persistence for ArchivedWeek — the menu and the shopping-list snapshot
    together, exactly as feature 13 produces it. No listing or browsing
    operation: FR-ARCH-04's reverse-chronological browse is out of this
    feature's scope and blocked on feature 19 (design.md section 11, gate
    question 4)."""

    def get(self, week: IsoWeek) -> ArchivedWeek | None: ...

    def save(self, archived: ArchivedWeek) -> None:
        """Overwrite, not create-only: idempotent so a rollover retry
        (FR-MENU-08, out of covers) can call this again safely."""
        ...
```

## 4. Fakes — shape, not full listing

Each fake is a plain class over an internal `dict`/`list`, `@runtime_checkable`
conformant, no IO. Two points worth stating rather than leaving implicit:

- **`FakeAccountRepository`** must replicate `create`/`rename`'s atomicity —
  raising `UsernameAlreadyTaken` (reused from
  `planner_core.domain.username_policy`) on a folded-name collision, and
  releasing the old reservation *by looking up the record actually stored
  under `user_id`*, never by re-folding a caller-supplied old name. This is
  precisely `docs/data_model.md` §5.2's trap, restated for the fake: getting
  it wrong in the fake would make the contract suite pass against a fake that
  is not a faithful stand-in for how a real adapter must behave.
- **`FakeShoppingListRepository.acquire_lock`** must compare `expires_at`
  against `now` as data (`expires_at < now` ⇒ acquirable), never treat an
  existing lock record as gone just because enough fake-clock time has
  "passed" — there is no real TTL sweep to model, and the whole point of
  §5.3 is that a real one cannot be trusted either.

## 5. The contract suite

One module per port under `backend/tests/contract/`. Each parametrizes over
a list of factories, today holding exactly one entry:

```python
# backend/tests/contract/test_shopping_list_repository_contract.py
import pytest
from support.fakes import FakeShoppingListRepository

IMPLEMENTATIONS = [FakeShoppingListRepository]


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_save_then_list_returns_the_saved_item(repository_factory):
    repo = repository_factory()
    ...
```

Adding a real adapter later (feature 15+/19+/21+, once the relevant
architecture item is decided) is exactly one line — append its factory to
`IMPLEMENTATIONS` and mark the new parametrize case `@pytest.mark.aws` per
`docs/verification.md`'s test tiers. Nothing in the test bodies changes.

## 6. Import wiring for `backend/tests/contract/`

`backend/core/tests/conftest.py` inserts `backend/core/tests` onto
`sys.path` under pytest's `prepend` import mode, but only for test files
pytest collects *under that directory* — `backend/tests/contract/` is a
different tree and gets no such insertion for free. `backend/tests/contract/conftest.py`
adds one:

```python
# backend/tests/contract/conftest.py
from __future__ import annotations

import sys
from pathlib import Path

_CORE_TESTS = Path(__file__).resolve().parents[2] / "core" / "tests"
if str(_CORE_TESTS) not in sys.path:
    sys.path.insert(0, str(_CORE_TESTS))
```

This is the only way `from support.fakes import ...` resolves from
`backend/tests/contract/` without duplicating the fakes or turning
`core/tests/support` into a distributed package (which `docs/conventions.md`
never asks for — fakes are dev-only, and `core` ships zero runtime
dependencies regardless of what its own test tree imports).

## 7. Two gaps this feature surfaces without fixing

**`Recipe` (feature 4, done, not reopened here) carries no `tiempo` or
`numeroComensales`, though `docs/data_model.md` §1's `DatosPlatoBiblioteca`
and `DatosPlatoSemana` list both.** `FR-LIB-03` (frozen) states what a
library recipe stores — name, ingredients, tools, procedure, one category —
and explicitly excludes cuisine/difficulty/kcal, but never mentions time or
servings either way; `numeroComensales` reads as the value `FR-AI-13`
already tracks as **deployment configuration** (`planner_core.ports.config`,
feature 11, done), not a per-recipe field. `LibraryRecipe` above persists
exactly what `Recipe` carries — no more. This is a data-model/domain
mismatch pre-dating this feature (feature 4 shipped before `data_model.md`'s
§1 was verified against the spreadsheet), not something a ports feature is
entitled to fix by adding fields to a closed domain type. Flagged as a gate
question (§9.2) rather than patched here.

**`AccountRecord.role` is a plain `str`, not an enum.** No domain `Role`
type exists — feature 15 `auth_flow` (blocked on architecture §2 P2) is
where the two roles `FR-AUTH-01` names would get a real type. Typing it here
would mean inventing a piece of that feature's domain model to serve a
signature, which is exactly the invention `docs/specs.md` rules out. The
port persists whatever string it is given.

## 8. R8's "used by application-layer tests" bullet, with no application code to use it

No `planner_core/application/` use case calls any of these ports yet — every
feature that would (15, and the rollover/generation orchestration features)
is blocked on an undecided architecture item. `feature_list.json`'s bullet
says the fakes are "used by application-layer tests," not "used by
application-layer code" — satisfiable by a **test**, not new production
code. `backend/core/tests/application/test_persistence_fakes_compose.py`
composes two or more fakes the way a real use case eventually will: create
an `AccountRecord` via `FakeAccountRepository`, save a `Recipe` via
`FakeRecipeRepository`, build a `Candidate`/`SlotContents` from it
(`planner_core.domain.candidate`, feature 5) and write it via
`FakeWeekRepository`, then derive the shopping items from it
(`planner_core.domain.shopping.required_shopping_items`, feature 7) and
write those via `FakeShoppingListRepository`. This proves the fakes compose
across ports the way application code will, without writing the
`application/` module that would actually need P2/P5 decided to have a real
caller.

## 9. Rejected alternatives

**A. `WeekRepository` exposing per-item operations mirroring AP11–AP13's
exact DynamoDB granularity** (`add_candidate_item`, `remove_candidate_item`,
`set_definitive_pointer`, `clear_definitive_pointer`) instead of
`save_slot`/`save_week` taking a whole `SlotContents`. Rejected. That
granularity is *why* `docs/data_model.md` §5.4 needs a read-time rule at
all — a candidate item and its slot's `DEFINITIVO` pointer are two separate
DynamoDB items, so deleting one without a matching write to the other
produces exactly the dangling reference §5.4 resolves at read time.
`SlotContents.__post_init__` (feature 5, done) already raises
`CandidateNotFound` if `definitive_id` does not match a candidate in the
same object — operating at that granularity makes the dangling-reference
scenario **structurally unreachable through this port's write path**, which
is strictly stronger than replicating a defensive read-time check, and it
does not leak DynamoDB's item split into the port (R7). A future real
adapter's own `get_week`/`save_slot` implementation is where §5.4's
read-time resolution actually has to live, reconstructing one `SlotContents`
from the (still two, at the DynamoDB level) stored items — that reassembly
is the adapter's job, not this Protocol's shape.

**B. One `PersistencePort` mega-`Protocol`** combining all six repositories'
methods into a single interface, so `wiring.py` selects one object instead
of six. Rejected. It would force every consumer — a rename operation, a
shopping-list re-sync — to depend on methods it never calls, and it
contradicts `docs/architecture.md` §3.2's "one suite in
`backend/tests/contract/` per port": a combined suite could not report which
aggregate actually broke. Six small ports, six focused contract suites, one
composition root (`wiring.py`, not built until an adapter exists) is the
same shape `Clock`/`ConfigPort` already established, scaled up.

**C. `ShoppingListRepository.acquire_lock`/`release_lock` as a separate
`ShoppingListLock` `Protocol`.** Considered, rejected for now.
`docs/data_model.md` §1 stores `LockLista` in the *same* `COMPRA#<idLista>`
partition as the ingredient items — "one concept, one name" is explicitly
why §7 rejected moving it to its own partition. Splitting it into a second
port here would reintroduce the same split this codebase's own data model
already reverted. If a future feature needs to swap the lock's
implementation independently of the list's, that is grounds to revisit —
not something this feature has a reason to do pre-emptively.

**D. `AccountRepository.get_by_username` taking an already-folded key,
pushing the fold to the caller.** Rejected. `docs/data_model.md` §2 places
the fold in "application code," but every existing fold call site
(`username_policy.validate_username`) takes the raw string and folds
internally via the shared `normalize()` helper — matching that shape here
means one fewer place a caller could fold slightly differently and produce
a lookup that silently never matches, the exact failure mode §2 warns about
for the reservation key.

## 10. Boundary checks

- **`docs/architecture.md` §2 (pending, human-owned):** no port here needs
  P2–P6 decided to be *defined*. §9.2 below flags the residual risk that
  `AccountRepository`'s existence presupposes application-managed credential
  storage (consistent with `docs/data_model.md` §1's closed `DatosUsuario`,
  P1) rather than a managed identity provider (P2's still-open Cognito
  option) — a risk to surface, not a reason to block a port whose shape
  `docs/data_model.md` §1 already commits to.
- **§2.1 decide-in-a-spec items:** none touched. No unit, category or
  servings value enters this feature.
- **Frozen docs:** none modified.
- **`SlotContents`/`RuleSet`/`ShoppingItem`/`Recipe`/`ArchivedWeek`/`IsoWeek`/`SlotRef`:**
  unchanged. No field added to any of them (§7 names the one place this
  matters).
- **User-facing strings:** none new. `AccountNotFound`, `RecipeNotFound`,
  `ShoppingListLockHeld` carry no es-ES text — persistence-layer exceptions,
  not user-facing validation (`docs/conventions.md`, Language policy: only
  the feature owning the user-facing flow adds message text, same pattern
  `specs/text_and_units/design.md` §6 and `specs/password_policy/requirements.md`
  § *Scope note* already established). `UsernameAlreadyTaken` is reused
  as-is, already carrying `USERNAME_ALREADY_TAKEN`.
- **Runtime dependencies:** none added. `core` stays `dependencies = []`.
- **Requirements invented:** none. Every `R<n>` cites `NFR-BKP-01`, the only
  id in this feature's `covers` array.

## 11. Gate questions for the human

1. **`AccountRepository`'s shape presupposes application-managed credential
   storage in the single table** (`password_hash`, `password_reset_required`
   fields mirroring `DatosUsuario`), which is consistent with
   `docs/data_model.md` §1 (closed, P1) but sits ahead of architecture §2 P2
   (Cognito vs. application-managed) formally being decided. Recommendation:
   accept it — P1's closure already bakes in `passHash` as a stored
   attribute, and `docs/architecture.md` §1.2.1 states P1's closure
   "unblocks `persistence_ports` (feature 14)" by name. If the human intends
   P2 to still leave Cognito on the table, the port most likely to be
   discarded or reshaped later is this one specifically — worth confirming
   now rather than after feature 15 is built on top of it.
2. **`Recipe`/`MealSnapshot` carry no `tiempo`/`numeroComensales`, though
   `docs/data_model.md` §1 lists both on `DatosPlatoBiblioteca` and
   `DatosPlatoSemana`.** `LibraryRecipe` in this design persists only what
   `Recipe` actually carries. Recommendation: treat this as a pre-existing
   gap to close in whichever feature next touches `Recipe` (not this one) —
   or, if the human considers the two attributes already dead (never
   promoted to a frozen `FR-*`), strike them from `data_model.md`'s
   `DatosPlatoBiblioteca`/`DatosPlatoSemana`/`[receta]` rows instead. Either
   resolution is the human's; this feature does not decide it.
3. **Six ports, one per aggregate** (§9, rejected alternative B), rather than
   a consolidated interface or a finer split (e.g., a seventh port for the
   shopping-list lock, rejected alternative C). Recommendation: accept as
   designed — it mirrors `docs/architecture.md` §3.2's "one suite per port"
   and `docs/data_model.md`'s own partition-per-aggregate shape.
4. **`ArchiveRepository` is deliberately minimal** — `get`/`save` only, no
   listing or browsing. `FR-ARCH-03`/`FR-ARCH-04` (cold storage, browsing)
   stay entirely with feature 19, blocked on P6, and are not cited by any
   `R<n>` here. Recommendation: accept — `NFR-BKP-01` only asks that past
   weeks and their snapshots be persisted somewhere a backup can reach, not
   that they be browsable.
