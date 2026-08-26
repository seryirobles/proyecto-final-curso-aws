# shopping_list_state — Requirements

> Feature 8 · tier 1 · `sdd: true`
> Covers: `FR-SHOP-01`, `FR-SHOP-02`, `FR-SHOP-04`, `FR-SHOP-06`, `FR-SHOP-07`, `FR-SHOP-08`
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen
> requirement ids it implements and is verifiable by at least one concrete
> test that asserts a value.

## Purpose in one sentence

The shared, provenance-free shopping list — a flat item shape (name, quantity,
unit, check state), manual add/edit/remove, check-off with a two-section
split, and a re-sync merge that is purely additive, writes only to an
unchecked item (creating one if none matches), and **never writes to a
checked item at all** — a shortfall becomes a brand-new unchecked item
carrying the remainder (`G-77`).

## One `SHALL` per requirement

Every `R<n>` below carries exactly one `SHALL` or one `SHALL NOT`, counted
mechanically rather than by eye, per the checklist in `AGENTS.md` /
`docs/specs.md`. Where a rule reads naturally as a positive-plus-guard (e.g.
"edit changes name and quantity, and SHALL NOT touch the unit"), the guard is
split into its own `R<n>`.

## Scope note — `FR-SHOP-10` is cited though absent from `covers`

`feature_list.json`'s `covers` array for this feature does not list
`FR-SHOP-10`, but two of its own acceptance criteria explicitly cite it
("two consecutive presses produce an identical list", "a checked item and an
unchecked item may share a normalized name + unit"). This is not an invented
requirement: `specs/shopping_aggregation/design.md` §1 already promised this
split — feature 7 implements `FR-SHOP-10`'s "recomputes... deterministically"
half (a pure function returns equal results for equal inputs); **"the
additive merge into a persisted, checkable shopping list... both feature 8"**
is this feature's half, and `G-77`'s "left unresolved, deliberately" note
scopes the *coexistence* of a checked and unchecked row under the same
requirement id. `R16` and `R18` below cite `FR-SHOP-10` alongside
`FR-SHOP-06`/`FR-SHOP-08` for exactly that reason. `FR-SHOP-11` is not cited
anywhere in this document — it was removed by `G-74` and stays removed.

## Depends on

Feature 7 (`shopping_aggregation`, done). `required_shopping_items()` in
`backend/core/src/planner_core/domain/shopping.py` returns the deterministic
required-item set as `tuple[Ingredient, ...]` (name, quantity, unit), merged
on normalized name + unit. This feature's re-sync consumes that tuple
directly as its `required` input — it does not re-aggregate.

---

## R1
Implements: FR-SHOP-01, FR-SHOP-04, FR-SHOP-08

The system SHALL NOT include, on any shopping-list item, an attribute other
than an identifying id, a name, a quantity, a unit and a check state.

## R2
Implements: FR-SHOP-02

WHEN a user adds a shopping-list item manually, the system SHALL append a new
unchecked item carrying the given name, quantity and unit to the list.

## R3
Implements: FR-SHOP-02

WHEN a user edits a shopping-list item's name and quantity, the system SHALL
replace that item's name and quantity.

## R4
Implements: FR-SHOP-02

WHEN a user edits a shopping-list item's name and quantity, the system SHALL
NOT modify that item's unit or check state.

## R5
Implements: FR-SHOP-02

WHEN a user removes a shopping-list item, the system SHALL delete the
matching item from the list.

## R6
Implements: FR-SHOP-02, FR-SHOP-07

IF an edit, remove, check or uncheck operation targets an item id absent from
the shopping list, THEN the system SHALL raise a named exception.

## R7
Implements: FR-SHOP-07

WHEN a user checks a shopping-list item, the system SHALL set that item's
check state to checked.

## R8
Implements: FR-SHOP-07, FR-SHOP-08

WHEN a user unchecks a shopping-list item, the system SHALL set that item's
check state to unchecked.

## R9
Implements: FR-SHOP-07, FR-SHOP-08

The system SHALL partition the shopping list into an unchecked group and a
checked group such that every item is a member of exactly one group matching
its own check state.

## R10
Implements: FR-SHOP-06

WHEN re-sync runs, for each normalized name and unit present in the
required-item set, the system SHALL compute the outstanding quantity as the
required quantity minus the quantity already carried by checked items sharing
that normalized name and unit.

## R11
Implements: FR-SHOP-06

WHEN the outstanding quantity for a normalized name and unit is greater than
zero and an unchecked item sharing that normalized name and unit exists, the
system SHALL set that unchecked item's quantity to the outstanding quantity.

## R12
Implements: FR-SHOP-06, FR-SHOP-08

WHEN the outstanding quantity for a normalized name and unit is greater than
zero and no unchecked item sharing that normalized name and unit exists, the
system SHALL add a new unchecked item carrying that name, that unit and the
outstanding quantity.

## R13
Implements: FR-SHOP-06

IF the outstanding quantity for a normalized name and unit is zero or less,
THEN the system SHALL NOT add or modify any item for that normalized name and
unit during re-sync.

## R14
Implements: FR-SHOP-04, FR-SHOP-06

The system SHALL NOT remove any shopping-list item as part of re-sync.

## R15
Implements: FR-SHOP-08

The system SHALL NOT modify a checked shopping-list item's check state or
quantity during re-sync.

## R16
Implements: FR-SHOP-06

WHEN a shopping-list item's normalized name and unit do not appear in the
required-item set, the system SHALL NOT modify that item during re-sync.

## R17
Implements: FR-SHOP-06, FR-SHOP-10

WHEN re-sync is invoked twice in succession with an unchanged required-item
set and no manual or check-state change between invocations, the system SHALL
return an identical shopping list both times.

## R18
Implements: FR-SHOP-06, FR-SHOP-08, FR-SHOP-10

WHEN re-sync adds a new unchecked item whose normalized name and unit match an
existing checked item's, the system SHALL retain both items as separate
entries in the resulting list.

## R19
Implements: FR-SHOP-02

The system SHALL NOT reject an add, edit, check or uncheck operation because
the item's normalized name and unit match another list item's.

## R20
Implements: FR-SHOP-06

IF more than one unchecked item shares the normalized name and unit of an
outstanding entry, THEN the system SHALL write that entry's outstanding
quantity to the first such item in list order (`design.md` section 7, section
9 gate question 1).

## R21
Implements: FR-SHOP-06

WHEN re-sync writes the outstanding quantity to a matched unchecked item, the
system SHALL NOT modify that item's name or unit (`design.md` section 7,
section 9 gate question 3).

---

## Coverage map

| Frozen requirement | Covered by |
|---|---|
| `FR-SHOP-01` | R1 |
| `FR-SHOP-02` | R2, R3, R4, R5, R6, R19 |
| `FR-SHOP-04` | R1, R14 |
| `FR-SHOP-06` | R10, R11, R12, R13, R14, R16, R17, R18, R20, R21 |
| `FR-SHOP-07` | R6, R7, R8, R9 |
| `FR-SHOP-08` | R1, R8, R9, R12, R15, R18 |
| `FR-SHOP-10` (cited, see scope note) | R17, R18 |

| `feature_list.json` acceptance criterion | Covered by |
|---|---|
| One shared list; item is name, quantity, unit, check state, no marker, no override state (`FR-SHOP-01`, `FR-SHOP-04`, `G-72`) | R1 |
| Re-sync is purely additive: outstanding = required − checked, written to the matching unchecked item, adding one if none exists (`FR-SHOP-06`, `G-72`, `G-77`) | R10, R11, R12, R20, R21 |
| Re-sync never removes anything — stale, manual and checked items all survive it (`FR-SHOP-04`, `FR-SHOP-06`, `G-72`) | R14, R16 |
| Test proves two consecutive presses produce an identical list, and a manual item absent from the computed set is still present afterwards (`FR-SHOP-10`) | R16, R17 |
| Items are checkable/uncheckable; checked ones sort into a separate section below (`FR-SHOP-07`, `FR-SHOP-08`) | R7, R8, R9 |
| Re-sync never writes to a checked item at all — neither state nor quantity; no updated-since-checked flag exists (`FR-SHOP-08`, `G-77`, supersedes `G-44`) | R15, R1 |
| Test proves raising the requirement above what a checked item covers leaves it untouched and produces a NEW unchecked item carrying the remainder, not the gross amount (`FR-SHOP-06`, `FR-SHOP-08`, `G-77`) | R10, R12, R15 |
| A checked item and an unchecked item may share a normalized name + unit — a purchase plus a remainder, not a duplicate (`FR-SHOP-10`, `G-77`) | R18 |
| No duplicate-grouping behaviour is implemented — `FR-SHOP-11` removed (`G-74`) | R19 (see design.md — true by construction: no grouping type is declared) |

R1 consolidates three separate absences (no auto/manual marker, no override
state, no updated-since-checked flag) into one mechanical field-name check,
the same collapsing technique `specs/shopping_aggregation/requirements.md`'s
`R8` and `specs/rules_model/requirements.md`'s `R21` already used for their
own provenance-absence clauses.
