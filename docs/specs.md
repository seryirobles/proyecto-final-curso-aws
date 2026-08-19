# Spec Driven Development (SDD)

> Kiro-style flow: requirements → design → tasks → code.
> No code is written until a human has approved the spec.

## What is different about this project

Most SDD projects invent requirements during the spec phase. **This one does
not.** `docs/requirements.md` already contains ~90 frozen, numbered, traceable
requirements produced by a completed requirements phase.

So the `spec_author`'s job is **translation, not invention**:

> Take the `FR-*` ids this feature claims, and restate them as testable EARS
> requirements scoped to exactly what this feature implements.

If a feature needs something no `FR-*` covers, that is not a licence to invent —
it is a finding. Mark the feature `blocked` and report it.

## Structure

Every feature with `"sdd": true` gets a folder as soon as it leaves `pending`:

```
specs/<feature-name>/
├── requirements.md   # WHAT is needed (EARS notation, cites FR ids)
├── design.md         # HOW it will be built (technical decisions)
└── tasks.md          # CONCRETE steps to implement
```

`<feature-name>` matches the `name` field in `feature_list.json`.

## Feature states

| State | Meaning |
|---|---|
| `pending` | No spec. `spec_author` acts first. |
| `spec_ready` | Spec drafted. Awaiting human approval. **No code is touched.** |
| `in_progress` | Spec approved. `implementer` working. |
| `done` | Code green, `reviewer` approved, session closed. |
| `blocked` | Stuck. Reason in `blocked_reason` and `progress/current.md`. |

## The human approval gate

The automated flow stops **once**: when `spec_author` finishes its three files,
sets the feature to `spec_ready`, and halts. The human reads `specs/<feature>/`
and says "approved" (or requests changes).

Only then does the `leader` move `spec_ready → in_progress` and launch the
`implementer`.

```
pending → [spec_author] → spec_ready → ⏸ HUMAN APPROVES → in_progress → [implementer → reviewer] → done
```

## requirements.md — strict EARS

Requirements use **EARS** (Easy Approach to Requirements Syntax). Each one is a
numbered paragraph following one of five patterns:

| Pattern | Template |
|---|---|
| **Ubiquitous** | `The system SHALL <action>.` |
| **Event** | `WHEN <trigger>, the system SHALL <action>.` |
| **State** | `WHILE <state>, the system SHALL <action>.` |
| **Optional** | `WHERE <optional feature>, the system SHALL <action>.` |
| **Unwanted** | `IF <unwanted event>, THEN the system SHALL <action>.` |

Hard rules:

- Each requirement has a stable id: `R1`, `R2`, …
- **Each requirement cites the `FR-*` / `NFR-*` ids it implements.** No orphans.
- Each requirement MUST be verifiable by at least one concrete test.
- Never combine several `SHALL`s in one requirement. Split instead.
- No soft verbs ("could", "may", "supports"). Only `SHALL` / `SHALL NOT`.

Example:

```markdown
## R1
Implements: FR-MENU-02, FR-UX-06

The system SHALL compute the current week as the ISO week (Monday–Sunday)
containing the present instant in the `Europe/Madrid` timezone.

## R2
Implements: FR-SHOP-05, FR-AI-11

WHEN scoping the current week for shopping aggregation, the system SHALL
include only days from the present day onward in `Europe/Madrid`.

## R3
Implements: FR-MENU-02

IF the injected clock is not timezone-aware, THEN the system SHALL raise
`AmbiguousInstant` rather than assume a timezone.
```

### Coverage obligation

Every `FR-*` listed in the feature's `covers` array in `feature_list.json` must
appear in at least one `R<n>`. The reviewer checks this and rejects if any is
missing.

## design.md — technical decisions

Capture **before** touching code:

- Files created / modified.
- New signatures (functions, classes, ports).
- Exceptions reused or added.
- Which layer each piece lives in, per `docs/architecture.md` §3.
- Concrete values proposed for the "decide in a spec" items of
  `docs/architecture.md` §2.1, if the feature touches them.
- **At least one rejected alternative, with the reason.**

This is not first-principles engineering — lean on `docs/architecture.md` and
`docs/conventions.md`. `design.md` documents where your feature meets the edge
of those rules.

If the design needs anything from `docs/architecture.md` §2 (pending,
human-owned), **stop**. Do not propose an architecture. Set `blocked`.

## tasks.md — executable checklist

Discrete, ordered steps, each with a checkbox. Each task references at least one
`R<n>` it covers.

```markdown
- [ ] T1 — Add `Clock` protocol in `core/src/planner_core/ports/clock.py`. Covers: R3.
- [ ] T2 — Add `current_week(today)` in `core/src/planner_core/domain/calendar.py`. Covers: R1.
- [ ] T3 — Add `days_from_today(week, today)` in `core/src/planner_core/domain/calendar.py`. Covers: R2.
- [ ] T4 — Add `resolve_live_weeks(clock)` in `core/src/planner_core/application/live_weeks.py`. Covers: R1, R2.
- [ ] T5 — Add `FakeClock` in `core/tests/support/fakes.py`. Covers: R1, R2, R3.
- [ ] T6 — Add `test_current_week_is_iso_week_in_madrid`. Covers: R1.
- [ ] T7 — Add `test_scope_excludes_days_before_today`. Covers: R2.
- [ ] T8 — Add `test_naive_clock_raises_ambiguous_instant`. Covers: R3.
```

Note the layering in T2–T4, decided by the human 2026-08-18: **`domain/`
functions take a plain `date` or instant, never a `Clock`.** The `Clock`
protocol lives in `ports/`, and a thin `application/` function reads it once and
passes the resulting civil date down — `docs/architecture.md` §3 (*"domain: pure
logic … no clock"*) and §3.1 rule 1 (`domain/` never imports `ports/`). An
earlier version of this example showed `current_week(clock)` in `domain/`; that
was wrong and is corrected here.

The `implementer` ticks `[x]` as each task completes. The `reviewer` rejects if
any `[ ]` remains without a documented justification.

## Traceability (hard rule)

The full chain:

```
US<n>  →  FR-xxx-nn  →  R<n>  →  T<n>  →  test
```

- Every `R<n>` cites at least one `FR-*`.
- Every `FR-*` in the feature's `covers` array appears in at least one `R<n>`.
- Every `R<n>` is covered by at least one concrete test.
- The `reviewer` verifies all three directions explicitly and rejects on any gap.

The `implementer` records the map in `progress/impl_<name>.md`:

```markdown
## Traceability
- R1 (FR-MENU-02, FR-UX-06) → `test_current_week_is_iso_week_in_madrid`
- R2 (FR-SHOP-05, FR-AI-11) → `test_scope_excludes_days_before_today`
- R3 (FR-MENU-02)           → `test_naive_clock_raises_ambiguous_instant`
```

## When SDD does not apply

Features with `"sdd": false` are pure scaffolding or configuration with no
product requirement behind them (e.g. `project_scaffold`). They still need tests
where testable, still need `./init.sh` green, and still get a `reviewer` pass —
they just skip the EARS spec.
