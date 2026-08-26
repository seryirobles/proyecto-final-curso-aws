# generation_request — Requirements

> Feature 10 · tier 1 · `sdd: true`
> Covers: `FR-AI-03`, `FR-AI-05`, `FR-AI-08`, `FR-AI-11`
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen
> requirement ids it implements and is verifiable by at least one concrete
> test that asserts a value.

## Purpose in one sentence

Resolve a whole-week generation request into three pure, independently
testable facts — the effective `RuleSet` for the run, the slots it must
target (with pins deterministically resolved, existing definitives skipped
and reported, and category counts reduced to the week's remainder), and a
deterministic idempotency key — without generating, persisting or adding
anything itself.

## Revision note — `mode` added to the idempotency key (2026-08-26)

Gate question 3 (`design.md` §9) originally recommended excluding `mode` from
`idempotency_key`'s inputs, on a literal reading of `FR-AI-08`'s three named
components ("same week, slot(s), and effective rules"). The human overturned
that recommendation: a mode change (e.g. `LIBRARY_ONLY` → `AI_ONLY`) over an
otherwise-identical week/slots/rules is a deliberate, different request, not a
duplicate resubmission, and must not be silently deduped. `idempotency_key`
now takes `mode` as a fourth parameter; `R16` was reworded to hold all four
inputs constant for its equality guarantee, `R24` now passes `request.mode`
as the fourth argument, and `R25` is new. This revision adds one requirement
without renumbering the rest — `R1`–`R24` are unchanged in number and text
except `R16` and `R24` themselves, per this project's convention of
renumbering only to close a gap left by *removal* (see
`specs/password_policy/requirements.md`'s own revision note), which does not
apply to an addition.

## One `SHALL` per requirement

Every `R<n>` below carries exactly one `SHALL` or one `SHALL NOT`, counted
mechanically rather than by eye, per the checklist in `AGENTS.md` /
`docs/specs.md`.

## Scope note on the four covered requirements

Several of the four ids in `covers` are UI-facing, persistence-facing, or
straddle a feature not yet built (AI invocation, whole-week orchestration).
This spec claims only the half each one names below; the rest belongs
elsewhere and is not implemented here. `FR-RULE-05` is also cited on several
requirements below — it is not in this feature's `covers` array (it belongs
to `rules_model`, feature 6, already closed), but this feature directly
consumes and re-exercises the guarantee it names at its own boundary.

| Requirement | Owned **here** | Deferred to |
|---|---|---|
| `FR-AI-03` | The `GenerationMode` enum modelling the three modes, and the `mode` field carried by `GenerationRequest`/`GenerationPlan`. | Which mode actually fills a slot — a library pick, an AI call, or a mix of both — **feature 11** (`ai_prompt_builder`), **feature 12** (`ai_output_validation`) and **feature 17** (`ai_lambda`). |
| `FR-AI-05` | The pure composition of an effective `RuleSet` from the shared rules plus an optional per-run override, reusing `rules_model.apply_override`, and the `GenerationRequest`/`GenerationPlan` shape that carries it end to end. | The confirmation-prompt UI that displays the target week and current rules and offers the override editor — **feature 20**. Accepting a submitted override over the wire — **feature 16** (`rest_api_lambda`). |
| `FR-AI-08` | The idempotency key: a deterministic hash of the week, the resolved target slot set, the effective rules, and the mode (added by explicit human override of `design.md` §9 gate question 3, 2026-08-26 — see revision note above), plus the proof that identical inputs reproduce it and that a changed component changes it. | Enforcing the key via a conditional write against a store — **feature 14** (`persistence_ports`) and **feature 17** (`ai_lambda`). This feature computes the key; it neither persists nor checks it. |
| `FR-AI-11` | Target-slot resolution: exclusion of disabled days, today-onward scoping for the current week (reusing `calendar.slots_from`), skip-on-existing-definitive with the outranked pin reported rather than silently applied, deterministic resolution of an unoccupied pinned slot, and weekly ingredient-category counts reduced to the remainder still needed. | Actually generating or adding candidates for `open_slots`/`pinned_slots` — **feature 11**, **feature 12**, **feature 17**. The per-slot progress/failure UI (`FR-AI-12`) — **feature 20**. |

---

## R1
Implements: FR-AI-03

The system SHALL declare `GenerationMode` as a `StrEnum` in
`planner_core.domain.generation` with exactly three members:
`LIBRARY_ONLY`, `AI_ONLY` and `MIX`.

## R2
Implements: FR-AI-05, FR-RULE-05

The system SHALL declare `RuleOverride` as `@dataclass(frozen=True)` in
`planner_core.domain.generation` with fields exactly `category_counts:
tuple[CategoryCountRule, ...] | None = None`, `pins: tuple[PinRule, ...] |
None = None` and `disabled_days: tuple[int, ...] | None = None`.

## R3
Implements: FR-AI-05, FR-RULE-05

WHEN `effective_rules` is called with `override` equal to `None`, the
system SHALL return a `RuleSet` equal to `shared`.

## R4
Implements: FR-AI-05, FR-RULE-05

WHEN `effective_rules` is called with `override` not `None`, the system
SHALL return `rules.apply_override(shared, override.category_counts,
override.pins, override.disabled_days)`.

## R5
Implements: FR-RULE-05

The system SHALL NOT modify any field of the `shared` argument passed to
`effective_rules`.

## R6
Implements: FR-AI-11

The system SHALL declare `PinnedTarget` as `@dataclass(frozen=True)` in
`planner_core.domain.generation` with fields exactly `slot: SlotRef` and
`recipe_id: str`.

## R7
Implements: FR-AI-11

The system SHALL declare `SkippedPin` as `@dataclass(frozen=True)` in
`planner_core.domain.generation` with fields exactly `slot: SlotRef` and
`pin: PinRule`.

## R8
Implements: FR-AI-11

The system SHALL declare `GenerationTargets` as `@dataclass(frozen=True)`
in `planner_core.domain.generation` with fields exactly `open_slots:
tuple[SlotRef, ...]`, `pinned_slots: tuple[PinnedTarget, ...]`,
`skipped_pins: tuple[SkippedPin, ...]` and `remaining_category_counts:
tuple[CategoryCountRule, ...]`.

## R9
Implements: FR-AI-11

The system SHALL provide `resolve_targets(week: IsoWeek, rules: RuleSet,
first_day: date, occupancy: Mapping[SlotRef, SlotContents]) ->
GenerationTargets` whose candidate slots exclude every slot whose
`day_number` is a member of `rules.disabled_days`.

## R10
Implements: FR-AI-11

`resolve_targets`'s candidate slots SHALL exclude every slot of `week`
occurring before `first_day`, reusing `calendar.slots_from`.

## R11
Implements: FR-AI-11

WHEN a candidate slot's entry in `occupancy` has a definitive (per
`candidate.definitive`), the system SHALL exclude that slot from both
`GenerationTargets.open_slots` and `GenerationTargets.pinned_slots`.

## R12
Implements: FR-AI-11

WHEN a candidate slot's entry in `occupancy` has a definitive and
`rules.pins` contains a `PinRule` for that slot, the system SHALL include a
`SkippedPin` pairing that slot with that `PinRule` in
`GenerationTargets.skipped_pins`.

## R13
Implements: FR-AI-11

WHEN a candidate slot's entry in `occupancy` has no definitive and
`rules.pins` contains a `PinRule` for that slot, the system SHALL include a
`PinnedTarget` pairing that slot with that `PinRule`'s `recipe_id` in
`GenerationTargets.pinned_slots`.

## R14
Implements: FR-AI-11

WHEN a candidate slot's entry in `occupancy` has no definitive and
`rules.pins` contains no `PinRule` for that slot, the system SHALL include
that slot in `GenerationTargets.open_slots` regardless of whether that
entry already holds one or more candidates.

## R15
Implements: FR-AI-11

The system SHALL set `GenerationTargets.remaining_category_counts` to one
`CategoryCountRule` per element of `rules.category_counts`, each carrying
`count` equal to `max(0, original_count - occupied_count)`, where
`occupied_count` is the number of entries across the whole `occupancy`
mapping whose definitive's `meal.category` equals that rule's `category`.

## R16
Implements: FR-AI-08

WHEN `idempotency_key` is called twice with the same `week`, the same
`targets`, the same `rules` and the same `mode`, the system SHALL return
equal values.

## R17
Implements: FR-AI-08

WHEN `idempotency_key` is called twice with the same `week` and the same
`targets` but a different `rules`, the system SHALL return different
values.

## R18
Implements: FR-AI-08

WHEN `idempotency_key` is called twice with the same `week` and the same
`rules` but a different `targets`, the system SHALL return different
values.

## R19
Implements: FR-AI-08

WHEN `idempotency_key` is called twice with the same `targets` and the
same `rules` but a different `week`, the system SHALL return different
values.

## R20
Implements: FR-AI-03, FR-AI-05

The system SHALL declare `GenerationRequest` as `@dataclass(frozen=True)`
in `planner_core.domain.generation` with fields exactly `week: IsoWeek`,
`mode: GenerationMode` and `rule_override: RuleOverride | None = None`.

## R21
Implements: FR-AI-05, FR-RULE-05

The system SHALL provide `build_plan(request: GenerationRequest,
shared_rules: RuleSet, first_day: date, occupancy: Mapping[SlotRef,
SlotContents]) -> GenerationPlan` whose result's `effective_rules` field
equals `effective_rules(shared_rules, request.rule_override)`.

## R22
Implements: FR-AI-11

`build_plan`'s result's `targets` field SHALL equal
`resolve_targets(request.week, <that result's effective_rules>, first_day,
occupancy)`.

## R23
Implements: FR-AI-03

`build_plan`'s result's `mode` field SHALL equal `request.mode`.

## R24
Implements: FR-AI-08

`build_plan`'s result's `idempotency_key` field SHALL equal
`idempotency_key(request.week, <that result's targets>, <that result's
effective_rules>, request.mode)`.

## R25
Implements: FR-AI-08

WHEN `idempotency_key` is called twice with the same `week`, the same
`targets` and the same `rules` but a different `mode`, the system SHALL
return different values.

---

## Coverage map

| Frozen requirement | Covered by |
|---|---|
| `FR-AI-03` | R1, R20, R23 |
| `FR-AI-05` | R2, R3, R4, R20, R21 |
| `FR-AI-08` | R16, R17, R18, R19, R24, R25 |
| `FR-AI-11` | R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R22 |
| `FR-RULE-05` (consumed, not in `covers`) | R2, R3, R4, R5, R21 |

| `feature_list.json` acceptance criterion | Covered by |
|---|---|
| Effective rules = shared rules with the per-run override applied, leaving shared rules untouched (`FR-AI-05`, `FR-RULE-05`) | R2, R3, R4, R5, R21 |
| Target slots exclude disabled days; pinned slots resolve to their pinned library meal (`FR-AI-11`) | R9, R13 |
| Slots already holding a definitive meal are skipped entirely; an existing definitive outranks a pin rule, and the skipped pin is reported rather than applied silently (`FR-AI-11`, `G-71`) | R11, R12 |
| Ingredient-category counts describe the week's final state: meals already present count toward each total and generation supplies only the remainder (`FR-AI-11`, `G-71`) | R15 |
| For the current week, target slots start at today (Europe/Madrid) — never days already past (`FR-AI-11`, `G-45`) | R10 |
| Generation adds candidates and never removes existing candidates or definitives (`FR-AI-11`, `G-18`) | R14 (an existing candidate never causes a slot to be excluded; this module provides no removal operation) |
| An idempotency key is derived from week + slots + effective rules (`FR-AI-08`) | R16, R17, R18, R19, R24, R25 |
| Test proves the same request submitted twice yields one candidate set and one logical invocation | R16 |
| The three modes (library-only / AI-only / mix) are modelled (`FR-AI-03`) | R1, R20, R23 |

Supporting requirements not demanded by a single acceptance bullet but
required by the invariants those bullets rest on: R6, R7, R8 (the value
shapes `resolve_targets`'s guarantees are stated in terms of), R20 (the
request shape `build_plan` consumes), R22, R24 (`build_plan`'s composition
of `resolve_targets` and `idempotency_key`, which is what lets a caller
reach either from one request rather than re-deriving `first_day` and
`effective_rules` twice).
