# week_calendar — Requirements

> Feature 2 · tier 1 · `sdd: true`
> Covers: `FR-MENU-01`, `FR-MENU-02`, `FR-UX-06`, `FR-AI-11`, `FR-SHOP-05`
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen
> requirement ids it implements and is verifiable by at least one concrete test.

## Purpose in one sentence

Make "which week is it, which days does it contain, and which of its slots are
still in play" a single, deterministic, timezone-correct answer that every user
and every consuming feature shares — `docs/architecture.md` §4 invariant 7:
**every user must agree on which week is current.**

## Accepted deviation — R4, R8, R16 and R22 each carry two `SHALL`s

`docs/specs.md` says *"Never combine several `SHALL`s in one requirement. Split
instead."* **R4**, **R8**, **R16** and **R22** each break that rule: R4, R8 and
R16 pair a `SHALL` with the `SHALL NOT` that guards it, and R22 pairs providing
a `FakeClock` with the obligation on the tests to use it.

> **R16 was missed by finding F5**, which listed only R4, R8 and R22. Found by
> counting `SHALL`s mechanically across every requirement rather than trusting
> the list — the same reason this file states the rule instead of assuming the
> next reader knows it. Both halves of R16 are tested
> (`test_live_week_labels_are_stable_identifiers` and
> `test_calendar_modules_contain_no_user_facing_text`), so it is accepted on
> identical grounds.

**Accepted 2026-08-18, not overlooked.** Raised as finding **F5** in
`progress/review_week_calendar.md` after the spec had been approved, implemented
and verified. Both halves of all three are covered by concrete tests, so nothing
is unverifiable and the rule's purpose is met — the rule exists so a
half-implementation cannot claim compliance. Splitting them retroactively would
renumber requirements cited by 40+ task lines, the implementation report and the
review, which is real risk to a traceability chain that currently holds, in
exchange for no behavioural change.

**Do not copy this pattern.** The cause was that
`.claude/agents/spec_author.md`'s EARS checklist did not name the rule, although
`docs/specs.md` did; the checklist was corrected on 2026-08-18. Features 3–13
split the prohibition into its own `R<n>`.

## Scope note on the two shared requirements

`FR-AI-11` and `FR-SHOP-05` are each claimed by a later feature as well. This
feature owns **only the calendar clause** of both — the today-onward scoping
rule, expressed once as a reusable domain function. See `design.md` §1 for the
exact split.

---

## R1
Implements: FR-MENU-02, FR-AI-11, FR-SHOP-05

The system SHALL obtain the present instant exclusively through a `Clock` port
declared in `planner_core.ports`, whose single operation returns a
timezone-aware `datetime`.

## R2
Implements: FR-MENU-02, FR-AI-11, FR-SHOP-05

The system SHALL NOT call `datetime.now`, `datetime.utcnow`, `date.today`,
`time.time`, `time.localtime` or any other ambient-time function anywhere in
the `planner_core` package, except the single `SystemClock.now` call in
`planner_core/ports/clock.py` required by R23.

> **Amended 2026-08-19.** R2 originally forbade ambient time *"anywhere in the
> `planner_core` package"* with no carve-out. R23 then put `SystemClock` inside
> that package, so the unqualified text became **false**: `clock.py` calls
> `datetime.now(UTC)`, and `test_planner_core_never_calls_an_ambient_clock`
> passed only because the scan skipped that line. The exception was real and
> intended, but it lived in R23's note and in the scan's code rather than in the
> requirement it qualified — the `AGENTS.md` §3.1 failure mode, inside a
> requirement this time. The exception is now stated where the prohibition is.
> Still one `SHALL NOT`; no new deviation from `docs/specs.md`.
>
> The exception stays **exactly** this narrow. `backend/core/tests/test_no_ambient_time.py`
> permits one line matching `return datetime.now(UTC)` in `clock.py` alone, and
> asserts that `datetime.now()`, `datetime.utcnow()` and
> `datetime.now(UTC) + drift` are all still caught there.

## R3
Implements: FR-MENU-02

IF the `Clock` returns a `datetime` whose `utcoffset()` is `None`, THEN the
system SHALL raise `NaiveInstant` rather than assume a timezone.

## R4
Implements: FR-MENU-02, FR-AI-11, FR-SHOP-05 *(Two `SHALL`s — accepted deviation, see the note at the top of this file.)*

The system SHALL derive the present civil date by converting the instant
supplied by the `Clock` to the `Europe/Madrid` timezone, and SHALL NOT use the
host process's local timezone for that conversion.

## R5
Implements: FR-MENU-02, FR-AI-11, FR-SHOP-05

The system SHALL derive identical results from any two `Clock` instants that
denote the same absolute moment, irrespective of the UTC offset in which each
instant is expressed.

## R6
Implements: FR-MENU-02

The system SHALL compute the current week as the ISO week — Monday through
Sunday — containing the present civil date in `Europe/Madrid`.

## R7
Implements: FR-MENU-02

The system SHALL compute the next week as the ISO week immediately following
the current week.

## R8
Implements: FR-MENU-02 *(Two `SHALL`s — accepted deviation, see the note at the top of this file.)*

The system SHALL identify a week by the string `<isoYear>-W<ww>`, where
`isoYear` is the **ISO week-numbering year** of the week and `ww` is the ISO
week number zero-padded to two digits; the system SHALL NOT use the calendar
year of any date in the week.

## R9
Implements: FR-MENU-02

IF a week is constructed with a week number that does not exist in its ISO
week-numbering year, THEN the system SHALL raise `InvalidIsoWeek`.

## R10
Implements: FR-MENU-01

The system SHALL expose, for each live week, exactly seven days ordered Monday
first and Sunday last.

## R11
Implements: FR-MENU-01

The system SHALL number the days of a week from 1 for Monday to 7 for Sunday,
derived from `date.isocalendar()`.

## R12
Implements: FR-MENU-01

The system SHALL expose, for each day, exactly two meal slots — lunch numbered
1 and dinner numbered 2 — ordered lunch before dinner.

## R13
Implements: FR-MENU-01

The system SHALL expose, for a whole week, exactly fourteen slots ordered by
day number and then by slot number.

## R14
Implements: FR-MENU-01, FR-UX-06

The system SHALL derive both live weeks — current and next — from a single
reading of the `Clock`.

## R15
Implements: FR-UX-06

The system SHALL expose, for each live week, its Monday date and its Sunday
date as that week's date range.

## R16
Implements: FR-UX-06 *(Two `SHALL`s — accepted deviation, see the note at the top of this file.)*

The system SHALL distinguish the two live weeks by an enumeration with exactly
the members `CURRENT` and `NEXT`, and SHALL NOT emit any user-facing text for
that distinction.

## R17
Implements: FR-AI-11, FR-SHOP-05

WHEN scoping the current week, the system SHALL include only the slots of days
whose date is on or after the present civil date in `Europe/Madrid`.

## R18
Implements: FR-AI-11, FR-SHOP-05

WHEN scoping the next week, the system SHALL include all fourteen of its slots.

## R19
Implements: FR-AI-11, FR-SHOP-05

WHILE scoping the current week, the system SHALL include both slots of the
present day regardless of the time of day of the present instant.

## R20
Implements: FR-MENU-02, FR-AI-11, FR-SHOP-05

WHEN the present instant falls on a day on which `Europe/Madrid` changes its
UTC offset, the system SHALL derive the civil date, the week and the in-scope
slots that the `Europe/Madrid` civil calendar gives for that instant.

## R21
Implements: FR-MENU-02

WHERE the present civil date lies in an ISO week-numbering year that differs
from its calendar year, or in the 53rd week of a 53-week ISO year, the system
SHALL still satisfy R6, R7 and R8.

## R22
Implements: FR-MENU-02, FR-AI-11, FR-SHOP-05 *(Two `SHALL`s — accepted deviation, see the note at the top of this file.)*

The system SHALL provide a `FakeClock` implementation of the `Clock` port
returning an explicitly supplied fixed instant, and the tests of this feature
SHALL obtain time only from it, reaching neither a real clock nor the network.

## R23
Implements: FR-MENU-02, FR-AI-11, FR-SHOP-05

The system SHALL provide, in the same module as the `Clock` port, a
`SystemClock` implementation of that port which returns the host's present
instant as a timezone-aware `datetime` and imports nothing outside the Python
standard library.

> **Added 2026-08-18, after this spec was approved and implemented.** The
> architecture had no rule saying where a real `Clock` implementation belongs,
> so the feature shipped with only the `FakeClock` of R22. The human decided the
> rule outright — `docs/architecture.md` §1.2.2, *a port's dependency-free
> default implementation ships with the port* — and R23 records the consequence
> for this feature. It adds no runtime dependency to `planner-core` and does not
> change any behaviour R1–R22 describes: nothing in `planner_core` constructs a
> `SystemClock`, since selecting it stays `wiring.py`'s job.
>
> **R2 was amended on 2026-08-19** to carry this exception in its own text —
> see R2 above. *(This paragraph originally read "R2 stands unchanged", which
> that amendment made false. Corrected 2026-08-19.)* `SystemClock.now` is the
> single ambient-time call in `planner_core`, and
> `backend/core/tests/test_no_ambient_time.py` is the authority on exactly which
> call is allowed and which modules may reach for `SystemClock`. §1.2.2 relies on
> that guard in place of a directory boundary; its precise exemptions are not
> restated here, because every paraphrase of it has gone stale.

---

## Coverage map

| Frozen requirement | Covered by |
|---|---|
| `FR-MENU-01` | R10, R11, R12, R13, R14 |
| `FR-MENU-02` | R1, R2, R3, R4, R5, R6, R7, R8, R9, R20, R21, R22, R23 |
| `FR-UX-06` | R14, R15, R16 |
| `FR-AI-11` | R1, R2, R4, R5, R17, R18, R19, R20, R22, R23 |
| `FR-SHOP-05` | R1, R2, R4, R5, R17, R18, R19, R20, R22, R23 |

| `feature_list.json` acceptance criterion | Covered by |
|---|---|
| Clock port in `planner_core.ports`; no `datetime.now()` in domain code | R1, R2, R23 |
| `current_week` / `next_week` as ISO weeks (Mon–Sun) in Europe/Madrid | R4, R5, R6, R7, R8 |
| A week exposes its 7 days and, per day, lunch and dinner | R10, R11, R12, R13 |
| A week exposes its Monday–Sunday range for UI labelling | R15, R16 |
| Today-onward scoping: current week from today, next week whole | R17, R18, R19 |
| DST transitions and year boundaries covered by tests | R20, R21 |
| Tests use a fixed `FakeClock`; no real clock, no network | R22 |
