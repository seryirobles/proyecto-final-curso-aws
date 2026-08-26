# persistence_ports — Requirements

> Feature 14 · tier 2 · `sdd: true`
> Covers: `NFR-BKP-01` (only)
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen
> requirement id(s) it implements and is verifiable by at least one concrete
> test that asserts a value.

## Purpose in one sentence

Repository interfaces — `typing.Protocol` definitions, one per persistent
aggregate — for every category `NFR-BKP-01` names (users, recipes, menus,
past weeks, the shopping list and its archived snapshots, rules), plus an
in-memory fake for each and a contract-test harness that will later run the
same suite against a real, backed-up adapter.

## Why every `R<n>` below cites only `NFR-BKP-01`

`feature_list.json`'s `covers` array for this feature lists `NFR-BKP-01`
alone: *"Every persistent datastore shall have automated backups (users,
recipes, menus, past weeks, the shopping list and its archived snapshots,
rules)."* `NFR-BKP-01` is an infrastructure requirement — the actual backup
configuration is `feature_list.json` feature 21 `infrastructure_terraform`
(human-owned, blocked). This feature's contribution to `NFR-BKP-01` is
**structural, not infrastructural**: unless a persistence port exists for
every category the requirement names, nothing forces a future real adapter
(and the backup configuration sitting behind it) to actually cover that
category — a category with no port is a category no amount of DynamoDB
backup configuration can reach, because nothing ever writes it through a
boundary a backed-up table could sit behind. `R1`–`R6` below establish that
boundary, one per category; `R7`–`R10` establish the properties
(storage-agnostic signatures, a working fake, a contract suite proving fake
and future real adapter agree, no AWS SDK creeping into `core`) that make
"swap the fake for a real, backed-up adapter with no other code change" true
later, which is the entire reason a fake now is credible evidence about a
production adapter later (`docs/architecture.md` §3.2, "contract-test rule").

No other `FR-*`/`NFR-*` is cited. This feature does **not** implement
`FR-AUTH-*`, `FR-ARCH-*`, `FR-RULE-*`, `FR-SHOP-*` or any other family's
*business* rules — those stay exactly where `feature_list.json` already
assigns them (features 9, 13, 15, 19 and others). It only gives each of
those families' data a place to be written and read, and reuses domain types
those features already built rather than re-deriving them.

## One `SHALL` per requirement

Every `R<n>` below carries exactly one `SHALL` or one `SHALL NOT`, counted
mechanically per the checklist in `AGENTS.md` / `docs/specs.md`.

## Depends on

`feature_list.json` lists `depends_on: [5, 6, 8]` (`week_plan_model`,
`rules_model`, `shopping_list_state`, all `done`) — the three tier-1 features
whose value objects (`SlotContents`, `RuleSet`, `ShoppingItem`) the weekly,
rule and shopping-list ports wrap directly. This spec also reuses, as a
shipped shared kernel, three types from features **not** listed in
`depends_on` — the same situation `specs/password_policy/requirements.md`
already documented for its own reuse of feature 3's `normalize`:

- `IsoWeek`, `SlotRef` (feature 2 `week_calendar`, done) — `WeekRepository`
  and `ArchiveRepository` key on `IsoWeek`.
- `Recipe` (feature 4 `recipe_model`, done) — `RecipeRepository` persists it.
- `ArchivedWeek` (feature 13 `rollover_job_logic`, done) — `ArchiveRepository`
  persists it whole, unmodified.
- `UsernameAlreadyTaken` (feature 9 `password_policy`, done,
  `planner_core.domain.username_policy`) — reused as `AccountRepository`'s
  uniqueness-collision exception rather than defining a second type meaning
  the same thing.

No field is added to any of these types; see `design.md` §7 for the one gap
this reuse surfaces (`Recipe` carries no `tiempo`/`numeroComensales`, though
`docs/data_model.md` §1's `DatosPlatoBiblioteca` lists both).

---

## R1
Implements: NFR-BKP-01

The system SHALL define, in `planner_core.ports.accounts`, an
`AccountRepository` `typing.Protocol` exposing operations to create,
retrieve by id, retrieve by username, list, rename, update the credentials
of, and delete a user account, so every account `NFR-BKP-01` names as
"users" can be persisted through it.

## R2
Implements: NFR-BKP-01

The system SHALL define, in `planner_core.ports.recipes`, a
`RecipeRepository` `typing.Protocol` exposing operations to retrieve, list,
save and delete a library recipe, so every entry `NFR-BKP-01` names as
"recipes" can be persisted through it.

## R3
Implements: NFR-BKP-01

The system SHALL define, in `planner_core.ports.weeks`, a `WeekRepository`
`typing.Protocol` exposing operations to retrieve and overwrite a live
week's slot contents, so every plan `NFR-BKP-01` names as "menus" can be
persisted through it.

## R4
Implements: NFR-BKP-01

The system SHALL define, in `planner_core.ports.rules`, a `RuleRepository`
`typing.Protocol` exposing operations to retrieve and overwrite the shared
rule set, so the data `NFR-BKP-01` names as "rules" can be persisted through
it.

## R5
Implements: NFR-BKP-01

The system SHALL define, in `planner_core.ports.shopping_list`, a
`ShoppingListRepository` `typing.Protocol` exposing operations to list,
save and delete a shopping-list item, delete every checked item, and
acquire or release the re-sync serialization lock, so the data `NFR-BKP-01`
names as "the shopping list" can be persisted through it.

## R6
Implements: NFR-BKP-01

The system SHALL define, in `planner_core.ports.archive`, an
`ArchiveRepository` `typing.Protocol` exposing operations to retrieve and
save one archived week's menu and shopping-list snapshot together, so the
data `NFR-BKP-01` names as "past weeks" and "its archived snapshots" can be
persisted through it.

## R7
Implements: NFR-BKP-01

The system SHALL NOT declare, in any method signature of a persistence port
defined by this feature, a parameter or return type specific to a storage
technology.

## R8
Implements: NFR-BKP-01

The system SHALL provide an in-memory implementation of each persistence
port defined by this feature that satisfies that port's `Protocol`.

## R9
Implements: NFR-BKP-01

WHEN a persistence port's contract-test suite runs, the system SHALL execute
every test in that suite once for each implementation registered for that
port.

## R10
Implements: NFR-BKP-01

The system SHALL NOT import an AWS SDK module in any file this feature adds.

---

## Coverage map

| Frozen requirement | Covered by |
|---|---|
| `NFR-BKP-01` | R1–R10 (all) |

| `feature_list.json` acceptance criterion | Covered by |
|---|---|
| "Ports are `typing.Protocol` definitions in `planner_core.ports` with no storage technology leaking into their signatures" | R1–R7 |
| "In-memory fakes in `core/tests/support` implement every port and are used by application-layer tests" | R8 (existence + `Protocol` conformance); the "in `core/tests/support`" location and the "used by application-layer tests" placement are `tasks.md` T-level commitments (`design.md` §3, §8) rather than a separate `R<n>` — an EARS requirement states a system property, not a file's path |
| "A contract suite in `backend/tests/contract` exercises each port and is parametrized to run against any implementation (fake now, real adapter later)" | R9; the suite's location and its current single-fake registration are `design.md` §5 |
| "No AWS SDK import anywhere in this feature" | R10 |
