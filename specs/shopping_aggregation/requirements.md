# shopping_aggregation — Requirements

> Feature 7 · tier 1 · `sdd: true`
> Covers: `FR-SHOP-03`, `FR-SHOP-05`, `FR-SHOP-10`
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen
> requirement ids it implements and is verifiable by at least one concrete
> test that asserts a value.

## Purpose in one sentence

A pure function from the in-scope definitive meals (current week from today
onward, plus the whole next week) to the required-ingredient set: merge on
normalized name + unit, no cross-unit conversion, no provenance, and
deterministic so repeated invocations converge.

## One `SHALL` per requirement

Every `R<n>` below carries exactly one `SHALL` or one `SHALL NOT`, counted
mechanically rather than by eye, per the checklist in `AGENTS.md` /
`docs/specs.md`.

## Scope note on the three covered requirements

`FR-SHOP-03` and `FR-SHOP-10` are both larger than what this feature builds:
`FR-SHOP-03` also names the button and the fixed unit list, `FR-SHOP-10` also
names the additive merge into the persisted list and serialization against
concurrent presses. This spec claims only the half each one names below; the
rest belongs to feature 8 (`shopping_list_state`, not yet built, owns
`FR-SHOP-01/02/04/06/07/08`).

| Requirement | Owned **here** | Deferred to |
|---|---|---|
| `FR-SHOP-03` | The merge rule itself: two ingredients combine into one aggregated item only when their normalized names and units both match; no cross-unit conversion. | The button that triggers a re-sync, and the fixed `Unit` list's own declaration — **feature 3** (`text_and_units`, closed) already shipped the vocabulary and `normalize()`; the UI button is **feature 8**. |
| `FR-SHOP-05` | The in-scope slot set (current week from today onward, plus the whole next week) and the rule that only a slot's definitive contributes — candidates never do. | Nothing; this feature is `FR-SHOP-05`'s entire implementation. |
| `FR-SHOP-10` | The "recomputes... deterministically" half: two invocations with equal inputs produce equal results, and the result carries no stored state a later press could contradict. | The additive merge into a persisted, checkable shopping list, and "serialized" (concurrency control against simultaneous button presses) — both **feature 8**, per `docs/gaps_and_resolutions.md` `G-77`'s "left unresolved, deliberately" note. |

---

## R1
Implements: FR-SHOP-05

WHEN computing the shopping-aggregation scope for a given civil date `today`,
the system SHALL include every slot of the ISO week containing `today` whose
day is on or after `today`.

## R2
Implements: FR-SHOP-05

WHEN computing the shopping-aggregation scope for a given civil date `today`,
the system SHALL include every slot of the ISO week immediately following the
one containing `today`.

## R3
Implements: FR-SHOP-05

WHEN an in-scope slot holds a definitive candidate, the system SHALL include
every ingredient of that candidate's meal in the aggregation input.

## R4
Implements: FR-SHOP-05

IF an in-scope slot holds no definitive candidate, THEN the system SHALL NOT
include any ingredient from that slot's candidates in the aggregation input.

## R5
Implements: FR-SHOP-03

The system SHALL sum, into one aggregated item's quantity, the quantities of
every ingredient in the aggregation input whose name normalizes to the same
value and whose unit is the same.

## R6
Implements: FR-SHOP-03

The system SHALL NOT convert an ingredient's quantity from its stored unit to
any other unit when aggregating.

## R7
Implements: FR-SHOP-10

WHEN the aggregation function is invoked twice with equal `plans` and `today`
arguments, the system SHALL return equal results both times.

## R8
Implements: FR-SHOP-03, FR-SHOP-10

The system SHALL NOT include, on any item of the aggregation result, a field
other than an ingredient name, a quantity and a unit.

---

## Coverage map

| Frozen requirement | Covered by |
|---|---|
| `FR-SHOP-03` | R5, R6, R8 |
| `FR-SHOP-05` | R1, R2, R3, R4 |
| `FR-SHOP-10` | R7, R8 |

| `feature_list.json` acceptance criterion | Covered by |
|---|---|
| Aggregation derives only from definitive meals; candidates never contribute (`FR-SHOP-05`, `G-04`) | R3, R4 |
| Scope is the current week from today onward plus the whole next week (`FR-SHOP-05`) | R1, R2 |
| Items merge only on matching normalized name + unit; no cross-unit conversion (`FR-SHOP-03`) | R5, R6 |
| The function is pure and deterministic: same inputs produce the same required-item set, so repeated runs converge (`FR-SHOP-10`, `G-54`) | R7 |
| Items carry no provenance: no auto/manual marker, no override state and no record of which week requires them (`G-72`, `G-73`) | R8 |
| Test proves running the aggregation twice yields an identical result | R7 |

R8 consolidates three separate absences named by `G-72`/`G-73` (no
auto/manual marker, no manual-override state, no per-item week record) into
one mechanical field-name check, because all three reduce to the same fact
about the result item's shape — exactly `{name, quantity, unit}` — mirroring
`specs/rules_model/requirements.md`'s `R21` (author/editor/owner absence
collapsed into one field-name check).
