# realtime_channel_persistence — Requirements

> Feature 18 · tier 2 · `sdd: true`
> `covers`: **`["FR-RT-01"]`** in `feature_list.json` (human gate ruling,
> 2026-08-30) — see the note below and `design.md` §10.
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen
> requirement id(s) it implements and is verifiable by at least one concrete
> test that asserts a value. Exactly one `SHALL` / `SHALL NOT` per `R<n>`,
> counted mechanically.

## Purpose in one sentence

The persistence half of `G-88`'s polling design: a per-resource change
marker exposed on the four pollable repository ports — a `current_version`
read, and a version-returning bump folded into every mutating write —
plus the in-memory fakes and contract tests that pin the behaviour, with
**no HTTP layer, no handler, no polling logic** (that is feature 26,
blocked on P5).

## Why every `R<n>` cites `FR-RT-01`, and how `FR-RT-02` is handled

`feature_list.json` gives feature 18 `covers: ["FR-RT-01"]` (human gate
ruling, 2026-08-30: keeping the feature requirement-free "would not be
honest"). Feature 18 was split off `realtime_channel` on 2026-08-27
(`G-88`, `docs/architecture.md` §1.2.4) as the **data-layer half** of the
polling mechanism; `G-88` states *"`FR-RT-01`–`-03` are satisfied by this
mechanism as written"* and the mechanism's write side — the `MarcaCambio`
marker bumped inside each write — is exactly this feature. Every `R<n>`
here is **translation, not invention**: each restates `FR-RT-01` scoped to
the persistence half.

`R7` and `R8` keep the door shut on optimistic locking. Per `G-88` the
marker *"must never appear in a `ConditionExpression`"* — read-only
metadata, never a write precondition — which is intrinsic to `FR-RT-01`'s
polling design, so both cite `FR-RT-01`. They also **preserve** `FR-RT-02`
(last-write-wins, `G-07`): conditioning a write on the marker would
silently turn last-write-wins into optimistic locking. The gate ruled
`FR-RT-02` is **not** added to `covers` — feature 18 does not implement the
shared-collaboration model, it only avoids breaking it. `FR-RT-03`
(indicate connection loss, reconnect, resynchronise) is entirely
client-side and stays with feature 26; no `R<n>` here cites it.

## Scope note — what this feature does not do

`FR-RT-03`'s UI behaviour, conditional-GET / `If-None-Match` / `304`
mechanics, the polling interval and its backoff, and how the marker
travels over HTTP (header vs. payload field) are all **feature 26**,
blocked on P5 (`G-88`'s boundary note). Collapsing a bulk operation's
per-item marker bumps into one bump per logical action is a future
transaction-shape decision (`docs/data_model.md` §4.2/§4.4), explicitly
**out of scope here** — `R11` fixes the current, safe, per-call
behaviour.

## Depends on

`feature_list.json` lists `depends_on: [4, 5, 6, 8, 14]`. This feature
amends the four repository ports feature 14 `persistence_ports` created
(`WeekRepository`, `RecipeRepository`, `RuleRepository`,
`ShoppingListRepository`) and their fakes and contract suites; it reuses
the domain value types those ports already carry (`SlotContents`,
`RuleSet`, `ShoppingItem`, `LibraryRecipe`, `IsoWeek`, `SlotRef`)
unchanged. `AccountRepository` and `ArchiveRepository` are **not** pollable
resources (`docs/data_model.md` §1 — no `MarcaCambio` instance for
`USUARIOS` or the archive) and are untouched.

---

## R1
Implements: FR-RT-01

The system SHALL expose on each of `WeekRepository`, `RecipeRepository`,
`RuleRepository` and `ShoppingListRepository` a `current_version`
operation that returns the current integer value of that resource's
change marker.

## R2
Implements: FR-RT-01

WHEN any read-only operation of one of those four repositories is called,
the system SHALL leave that resource's change marker unchanged.

## R3
Implements: FR-RT-01

WHEN `current_version` is called for a resource that has never been
written, the system SHALL return the fixed baseline value `0`.

## R4
Implements: FR-RT-01

WHEN a mutating operation of one of those four repositories completes, the
system SHALL return the resource's change-marker value as updated by that
operation.

## R5
Implements: FR-RT-01

WHEN a mutating operation changes a resource's stored data, the system
SHALL advance that resource's change marker within the same operation.

## R6
Implements: FR-RT-01

The system SHALL NOT expose any repository operation that advances a
resource's change marker without performing the data write that the
advance marks.

## R7
Implements: FR-RT-01

The system SHALL NOT accept a caller-supplied expected change-marker value
as a parameter to any mutating repository operation.

The marker only works as a cheap poll short-circuit (`FR-RT-01`, `G-88`)
if it is never a write precondition. This is also a
preservation-of-`FR-RT-02` constraint: a caller-supplied expected value
would enable optimistic locking, which `FR-RT-02` / `G-07` last-write-wins
forbids. `FR-RT-02` is not in this feature's `covers` (gate ruling
2026-08-30) — R7 preserves it, it does not implement it.

## R8
Implements: FR-RT-01

WHEN two mutating operations target the same resource in succession, the
system SHALL apply the second without raising a conflict.

Last-write-wins keeps the marker mechanism (`FR-RT-01`, `G-88`) free of
write-precondition semantics. As with R7 this is a
preservation-of-`FR-RT-02` constraint (`G-07`), not a reason to add
`FR-RT-02` to `covers`.

## R9
Implements: FR-RT-01

WHEN `delete_checked_items` is called and no shopping-list item is
checked, the system SHALL leave the shopping list's change marker
unchanged.

## R10
Implements: FR-RT-01

The system SHALL provide an in-memory implementation of each of the four
amended repository ports that maintains the change marker as an
incrementing integer counter.

## R11
Implements: FR-RT-01

WHERE a caller composes several single-item mutating operations into one
logical action, the system SHALL advance the change marker once for each
such operation.

## R12
Implements: FR-RT-01

The system SHALL NOT reference the change marker from any module outside
`planner_core.ports` and the test-support fakes.

---

## Coverage map

| Frozen requirement | Covered by |
|---|---|
| `FR-RT-01` | R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12 |

`R7` / `R8` also stand as preservation-of-`FR-RT-02` constraints (see their
R-blocks and the note above); `FR-RT-02` is deliberately not in `covers`.

| `feature_list.json` acceptance criterion | Covered by |
|---|---|
| "A `MarcaCambio` item type exists, one instance per pollable partition …" | R1 (one marker per pollable repository), R3 (baseline for a never-written resource); the four DynamoDB item instances are `design.md` §3's data-model mapping |
| "… each gain a `current_version` read (AP29 shape) — a cheap, strongly-consistent read of only the marker" | R1, R2; "cheap / strongly-consistent / marker-only" is a Protocol-docstring contract on the future adapter (`design.md` §3, §10 ruling 5), verified now as read-your-writes by R4 + the contract suite |
| "Every mutating method … returns the resource's new version instead of `None`, and bumps `marcaCambio` inside the same atomic operation … never a separate call, never before the data write" | R4 (returns), R5 (same operation), R6 (no standalone bump) |
| "The marker is never used as a write precondition/ConditionExpression … mechanically enforced by a scan test" | R7 (no expected-version parameter), R8 (last-write-wins, no conflict); the scan is `design.md` §6 |
| "Fakes … implement the version bump with a simple in-memory counter" | R10 |
| "Contract suites assert: every mutating method changes the version; no read method changes it; the version a write returns equals … the next `current_version()`; `delete_checked_items()` with nothing checked stays a no-op and does not bump" | R5 (mutating changes it), R2 (reads do not), R4 (returned value equals next read), R9 (`delete_checked_items` no-op) |
| "No `handler.py`, no `wiring.py`, no HTTP concern … pure `planner_core` plus contract tests" | R12 |
| "A bulk logical operation bumping its marker once per underlying item write … is accepted as correct-but-not-optimal; collapsing it to one bump is explicitly out of scope" | R11 (once per call); the out-of-scope collapse is the *Scope note* above and `design.md` §0 |
