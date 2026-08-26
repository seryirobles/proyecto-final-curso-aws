# rollover_job_logic — Requirements

> Feature 13 · tier 1 · `sdd: true`
> Covers: `FR-MENU-06`, `FR-MENU-08`, `FR-ARCH-01`, `FR-ARCH-02`, `FR-SHOP-09`
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen
> requirement ids it implements and is verifiable by at least one concrete
> test that asserts a value.

## Purpose in one sentence

The week rollover transition — archive the ending current week (with a
shopping-list snapshot taken before cleanup), promote the former next week to
current unchanged, initialize a fresh empty next week, and clear every
checked shopping item unconditionally — expressed as one pure, total,
deterministic function plus its three named internal steps (`FR-MENU-06`,
`FR-ARCH-01`, `FR-ARCH-02`, `FR-SHOP-09`), with the determinism of each step
standing in for `FR-MENU-08`'s retry-safety at this tier (see `design.md`
section 5 for why, and the gate question that flags this interpretation).

## One `SHALL` per requirement

Every `R<n>` below carries exactly one `SHALL` (or one `SHALL raise` / `SHALL
NOT`), counted mechanically rather than by eye, per the checklist in
`AGENTS.md` / `docs/specs.md`.

## Depends on

Feature 8 (`shopping_list_state`, done): `ShoppingItem` and `unchecked_items`
in `planner_core.domain.shopping` — rollover's cleanup step reuses
`unchecked_items` directly rather than reimplementing the checked/unchecked
filter (`design.md` section 4, rejected alternative C). Also reuses, without
extending, feature 2 (`week_calendar`, done: `IsoWeek`, `SlotRef`) and
feature 5 (`week_plan_model`, done: `SlotContents`) — this feature adds no
field to any of the three.

---

## R1
Implements: FR-ARCH-01

The system SHALL declare `ArchivedWeek` as `@dataclass(frozen=True)` in
`planner_core.domain.rollover` with fields exactly `week: IsoWeek`,
`plans: Mapping[SlotRef, SlotContents]` and
`shopping_snapshot: tuple[ShoppingItem, ...]`.

## R2
Implements: FR-ARCH-02

IF code attempts to set an attribute on an `ArchivedWeek` instance after
construction, THEN the system SHALL raise `dataclasses.FrozenInstanceError`.

## R3
Implements: FR-MENU-06, FR-MENU-08

The system SHALL declare `RolloverResult` as `@dataclass(frozen=True)` in
`planner_core.domain.rollover` with fields exactly `archived: ArchivedWeek`,
`new_current_plans: Mapping[SlotRef, SlotContents]`,
`new_next_plans: Mapping[SlotRef, SlotContents]` and
`shopping_items: tuple[ShoppingItem, ...]`.

## R4
Implements: FR-MENU-06, FR-ARCH-01

`roll_over(former_current_week, former_current_plans, former_next_plans,
shopping_items)`'s result's `archived.week` field SHALL equal
`former_current_week`.

## R5
Implements: FR-MENU-06, FR-ARCH-01

`roll_over(...)`'s result's `archived.plans` field SHALL equal
`former_current_plans` exactly, unchanged.

## R6
Implements: FR-ARCH-02

`roll_over(...)`'s result's `archived.shopping_snapshot` field SHALL equal
`shopping_items` exactly as passed in, before any cleanup is applied to it.

## R7
Implements: FR-MENU-06

`roll_over(...)`'s result's `new_current_plans` field SHALL equal
`former_next_plans` exactly, unchanged — the former next week's candidates
and definitives carry over (`G-28`).

## R8
Implements: FR-MENU-06

`roll_over(...)`'s result's `new_next_plans` field SHALL equal an empty
mapping (`G-15`).

## R9
Implements: FR-MENU-06, FR-SHOP-09

`roll_over(...)`'s result's `shopping_items` field SHALL equal exactly the
items of `shopping_items` whose `checked` is `False`, in list order
(`G-73`).

## R10
Implements: FR-MENU-06

The system SHALL declare `init_empty_next_week` to take no parameters
(`G-15`: no rule or generation input can reach a function with none to give
it).

## R11
Implements: FR-MENU-08

WHEN any of `archive_week`, `promote_next_to_current` or
`init_empty_next_week` is invoked twice with identical arguments (zero
arguments, for `init_empty_next_week`), the system SHALL return two equal
results each time.

## R12
Implements: FR-MENU-08, FR-SHOP-09

WHEN `unchecked_items` is applied to a shopping list already containing no
checked items, the system SHALL return that list unchanged.

## R13
Implements: FR-MENU-08

WHEN `roll_over` is invoked twice with identical arguments, the system SHALL
return two equal `RolloverResult` values.

---

## Coverage map

| Frozen requirement | Covered by |
|---|---|
| `FR-MENU-06` | R3, R4, R5, R7, R8, R9, R10 |
| `FR-MENU-08` | R3, R11, R12, R13 |
| `FR-ARCH-01` | R1, R4, R5 |
| `FR-ARCH-02` | R2, R6 |
| `FR-SHOP-09` | R9, R12 |

| `feature_list.json` acceptance criterion | Covered by |
|---|---|
| The five steps execute in order: archive, shopping-list snapshot, promote next to current, init empty next week, clean bought items (`FR-MENU-06`, `G-61`) | R4–R9 (each step's own field-equality proof); `design.md` section 3 (the composition order in `roll_over`) |
| The archive snapshot is taken BEFORE the cleanup (`FR-ARCH-02`, `G-53`) | R6 (archived from the raw, uncleaned `shopping_items`) vs. R9 (the final `shopping_items` is the cleaned result) — two different fields of the same result, proving the pre-cleanup value reached the archive |
| The former next week becomes the current week carrying over its candidates and definitives (`FR-MENU-06`, `G-28`) | R7 |
| The new next week starts empty; rules never auto-populate it (`FR-MENU-06`, `G-15`) | R8, R10 |
| Cleanup removes every CHECKED item unconditionally; all unchecked items are untouched and keep their state (`FR-SHOP-09`, `G-73`) | R9 (equality with the exact unchecked subset, in order — structurally unconditional: no next-week-requirement parameter exists for a condition to test) |
| Archived weeks become read-only (`FR-ARCH-02`) | R2 |
| Test proves re-running after interruption at each of the five steps completes without data loss, double-archiving or double-cleanup (`FR-MENU-08`, `G-61`) | R11 (archive/promote/init steps are each deterministic on retry — a retried write reproduces the identical value, never a duplicate); R12 (cleanup is a fixed point on an already-clean list — a retried cleanup loses nothing further); R13 (the composed job as a whole is deterministic and total, so it can never return or leave behind a partial result) |

Supporting requirement not demanded by a single acceptance bullet but
required by the invariant those bullets rest on: R1 (the `ArchivedWeek` type
`R2`, `R4`, `R5`, `R6` assume exists).
