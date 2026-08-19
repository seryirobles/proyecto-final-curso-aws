# week_calendar — Tasks

> Execute in order. Tick `[x]` as each completes.
> Concrete instants, dates and expected week ids are in `design.md` §8 — use
> those exact values, do not invent new ones.
> Read `design.md` §6.2 before writing a single test: **do not reach for a `TZ`
> environment sweep**, it is verified not to work here and proves nothing.

## Setup

- [x] T1 — Add `tzdata` to `[dependency-groups] dev` in `backend/pyproject.toml`
  (dev group only — **never** a runtime dependency of `planner-core`). Verify
  `uv run python -c "from zoneinfo import ZoneInfo; ZoneInfo('Europe/Madrid')"`
  succeeds, and that `uv export --package planner-api --no-dev` still resolves
  without it. Covers: R4.
- [x] T2 — Replace `backend/core/tests/support/.gitkeep` with
  `support/__init__.py`, and add `backend/core/tests/conftest.py` so `support`
  is importable from test modules in subdirectories. Covers: R22.

## Port and shared error base

- [x] T3 — Add `Clock` in `backend/core/src/planner_core/ports/clock.py`: a
  `@runtime_checkable` `Protocol` with `now() -> datetime`, documented as
  returning a **timezone-aware** value. Covers: R1.
- [x] T4 — Add `PlannerError` in
  `backend/core/src/planner_core/domain/errors.py`. This is the base class for
  every domain exception in features 3–13. Covers: R3, R9.
- [x] T5 — Add `FakeClock` in `backend/core/tests/support/fakes.py`: constructed
  from an explicit instant, with a `FakeClock.at("<iso-8601>")` helper. It never
  advances and never reads a real clock. Covers: R22.

## Domain — `planner_core/domain/calendar.py`

- [x] T6 — Add `MADRID = ZoneInfo("Europe/Madrid")`, `NaiveInstant`, and
  `civil_date(instant) -> date` converting through `MADRID`. Reject with
  `NaiveInstant` when `instant.utcoffset() is None` (**not** `tzinfo is None`).
  Covers: R3, R4, R5.
- [x] T7 — Add `MealSlot(IntEnum)` with `LUNCH = 1`, `DINNER = 2`, plus frozen
  `SlotRef(day, slot)` and `WeekDay(day)` whose `day_number` is a **derived
  property** reading `date.isocalendar().weekday`. Covers: R11, R12.
- [x] T8 — Add frozen `IsoWeek(iso_year, iso_week)` with `InvalidIsoWeek`
  validation in `__post_init__` (wrap the `ValueError` from
  `date.fromisocalendar`), and the derived properties `week_id`, `monday`,
  `sunday`, `date_range`, `days`, `slots`. `week_id` is
  `f"{iso_year}-W{iso_week:02d}"`. Covers: R8, R9, R10, R12, R13, R15.
- [x] T9 — Add `IsoWeek.containing(day)`, `current_week(today)`,
  `next_week(today)` and `IsoWeek.following()`. `following()` is
  `containing(self.monday + timedelta(days=7))` — never `iso_week + 1`.
  Covers: R6, R7, R21.
- [x] T10 — Add `slots_from(week, first_day) -> tuple[SlotRef, ...]` keeping the
  slots of days whose date is `>= first_day`, in day-then-slot order. Covers:
  R17, R18, R19.

## Application — `planner_core/application/live_weeks.py`

- [x] T11 — Add `LiveWeek(Enum)` with exactly `CURRENT = "current"` and
  `NEXT = "next"`. No Spanish, no display text. Covers: R16.
- [x] T12 — Add frozen `LiveWeeks(today, current_week, next_week)` with
  `week(which)`, `date_range(which)` and `slots_in_scope(which)`. Covers: R14,
  R15, R17, R18.
- [x] T13 — Add `resolve_live_weeks(clock) -> LiveWeeks` calling `clock.now()`
  **exactly once** and deriving everything from that single instant. Covers:
  R1, R14.

## Tests — port and guards

- [x] T14 — `backend/core/tests/ports/test_clock.py`:
  `test_fake_clock_satisfies_the_clock_port`. Covers: R1, R22.
- [x] T15 — `backend/core/tests/test_no_ambient_time.py`:
  `test_planner_core_never_calls_an_ambient_clock` — scan every `.py` under
  `planner_core` for `datetime.now`, `datetime.utcnow`, `date.today`,
  `time.time`, `time.localtime`, and for a bare `.astimezone()` with no
  argument; assert none is present. Covers: R2.
  *(Amended 2026-08-19: T44 later added one sanctioned allowance for
  `SystemClock.now` — see R23. "None is present" describes T15 as originally
  written, not the module's behaviour today.)*
- [x] T16 — Same module: `test_week_calendar_tests_never_call_an_ambient_clock`
  — same scan over `backend/core/tests/`, allowing only `FakeClock`. Covers:
  R2, R22.
- [x] T17 — Same module:
  `test_calendar_modules_contain_no_user_facing_text` — assert the four modules
  added by this feature are ASCII-only, so no Castilian Spanish string can have
  leaked into backend domain code. Covers: R16.

## Tests — civil date and timezone (`tests/domain/test_calendar.py`)

- [x] T18 — `test_civil_date_rejects_a_naive_instant` — a naive `datetime`, and
  a `datetime` whose `tzinfo.utcoffset()` returns `None`, both raise
  `NaiveInstant`. Covers: R3.
- [x] T19 — `test_civil_date_uses_madrid_not_utc` — `2026-07-19T21:59:59+00:00`
  → 2026-07-19, and `2026-07-19T22:00:00+00:00` → **2026-07-20**; plus the
  winter pair `2026-01-18T22:59:59+00:00` / `2026-01-18T23:00:00+00:00`.
  Covers: R4.
- [x] T20 — `test_the_same_moment_in_any_offset_gives_the_same_civil_date` —
  `2026-07-19T22:00:00+00:00`, `2026-07-20T03:00:00+05:00` and
  `2026-07-19T14:00:00-08:00` all yield 2026-07-20 and `2026-W30`. Covers: R5.

## Tests — week identity (`tests/domain/test_calendar.py`)

- [x] T21 — `test_current_week_is_the_iso_week_containing_today` — the two
  boundary pairs of `design.md` §8.2 give `2026-W29` / `2026-W30` and
  `2026-W03` / `2026-W04`. Covers: R6.
- [x] T22 — `test_next_week_is_the_week_after_the_current_one` — including the
  53-week crossings `2026-W53 → 2027-W01`, `2020-W53 → 2021-W01` and the
  52-week crossing `2027-W52 → 2028-W01`. Covers: R7, R21.
- [x] T23 — `test_week_id_uses_the_iso_year_and_pads_the_week_number` —
  2025-12-31 → `"2026-W01"` (not `"2025-W01"`), 2027-01-01 → `"2026-W53"` (not
  `"2027-W53"`), and a single-digit week rendered as `W01`, never `W1`. Covers:
  R8, R21.
- [x] T24 — `test_a_week_number_absent_from_its_iso_year_is_rejected` —
  `IsoWeek(2026, 53)` is valid; `IsoWeek(2027, 53)`, `IsoWeek(2026, 0)` and
  `IsoWeek(2026, 54)` raise `InvalidIsoWeek`. Covers: R9.

## Tests — week shape (`tests/domain/test_calendar.py`)

- [x] T25 — `test_a_week_has_seven_days_from_monday_to_sunday`. Covers: R10.
- [x] T26 — `test_day_numbers_run_one_for_monday_to_seven_for_sunday` — assert
  Sunday is 7, which `date.weekday()` would report as 6. Covers: R11.
- [x] T27 — `test_each_day_offers_lunch_then_dinner` — two slots, values 1 and
  2, lunch first. Covers: R12.
- [x] T28 — `test_a_week_has_fourteen_slots_ordered_by_day_then_slot`. Covers:
  R13.
- [x] T29 — `test_week_date_range_runs_monday_to_sunday` — including
  `2026-W53`, whose range is **2026-12-28 → 2027-01-03** and therefore spans two
  calendar years. Covers: R15, R21.

## Tests — DST (`tests/domain/test_calendar.py`)

- [x] T30 — `test_spring_forward_sunday_stays_in_its_week` — the March rows of
  `design.md` §8.1: `2026-03-28T23:30Z` and `2026-03-29T01:30Z` both give
  2026-03-29 / `2026-W13`, and `2026-03-29T22:30Z` gives 2026-03-30 /
  `2026-W14`. Covers: R20.
- [x] T31 — `test_autumn_ambiguous_hour_resolves_to_one_date_and_week` — the
  October rows: `2026-10-24T23:30Z`, `2026-10-25T00:30Z` and
  `2026-10-25T01:30Z` all give 2026-10-25 / `2026-W43` (the last two render as
  the same `02:30` local wall time), and `2026-10-25T23:00Z` gives 2026-10-26 /
  `2026-W44`. Covers: R20.

## Tests — scoping (`tests/domain/test_calendar.py`)

- [x] T32 — `test_scope_drops_days_before_the_given_day` — reference instant
  `2026-07-16T10:00:00+00:00` (Thursday of `2026-W29`): 8 slots, first is
  2026-07-16 lunch. Covers: R17.
- [x] T33 — `test_scope_keeps_the_whole_week_when_the_day_precedes_its_monday` —
  the same reference day against `2026-W30`: 14 slots. Covers: R18.
- [x] T34 — `test_scope_keeps_both_slots_of_the_given_day` — and with the
  Sunday-evening instant `2026-07-19T20:00:00+00:00` (22:00 Madrid) the current
  week still scopes to Sunday **lunch and dinner**, 2 slots. Covers: R19.

## Tests — application (`tests/application/test_live_weeks.py`)

- [x] T35 — `test_live_weeks_come_from_a_single_clock_reading` — assert the
  `FakeClock` was consulted exactly once and that `next_week` is
  `current_week.following()`. Covers: R14.
- [x] T36 — `test_live_week_labels_are_stable_identifiers` — `LiveWeek` has
  exactly `CURRENT` and `NEXT`, valued `"current"` and `"next"`. Covers: R16.
- [x] T37 — `test_current_week_scopes_from_today_and_next_week_scopes_whole` —
  through `resolve_live_weeks(FakeClock.at("2026-07-16T10:00:00+00:00"))`:
  `slots_in_scope(CURRENT)` is 8 slots, `slots_in_scope(NEXT)` is 14. Covers:
  R14, R17, R18, R19.
- [x] T38 — `test_live_weeks_expose_each_week_date_range` — `CURRENT` →
  2026-07-13/2026-07-19, `NEXT` → 2026-07-20/2026-07-26. Covers: R15.

## Close-out

- [x] T39 — Record the `R<n> → test` map in
  `progress/impl_week_calendar.md` (`docs/verification.md` Level 3). Covers:
  R1–R22.
- [x] T40 — Run `./init.sh` and confirm every gate is green: `ruff format`,
  `ruff check`, `mypy --strict`, `pytest`. Covers: R1–R22.

## Review follow-up

- [x] T41 — Add `backend/core/tests/domain/test_errors.py`, the test module
  `planner_core/domain/errors.py` was missing (reviewer finding F3,
  `CHECKPOINTS.md` C4). Assert that `PlannerError` is a plain `Exception` and
  that `NaiveInstant` and `InvalidIsoWeek` descend from it — as a lineage and
  at a real raise site, so the handler layer can catch the family by its base.
  Covers: R3, R9.

## Post-approval addition — `SystemClock` (`docs/architecture.md` §1.2.2)

> Added 2026-08-18 by the human's decision that a port's dependency-free default
> implementation ships with the port. Nothing above is renumbered or altered.

- [x] T42 — Add `SystemClock` to
  `backend/core/src/planner_core/ports/clock.py`, beside the `Clock` `Protocol`
  it satisfies: `now()` returns `datetime.now(UTC)`, never `datetime.utcnow()`,
  which is naive and would be rejected by `civil_date`. Standard library only,
  so `planner-core` keeps zero runtime dependencies. Comment why the class sits
  in `ports/` rather than a Lambda package, citing `architecture.md` §1.2.2.
  Covers: R23.
- [x] T43 — `test_system_clock_satisfies_the_clock_port_and_returns_an_aware_instant`
  in `backend/core/tests/ports/test_clock.py`: `isinstance(SystemClock(), Clock)`
  holds against the `@runtime_checkable` `Protocol`, and `now()` returns a
  `datetime` whose `utcoffset()` is not `None`. The one place in the suite that
  may read a real clock. Covers: R23.
- [x] T44 — Extend `backend/core/tests/test_no_ambient_time.py` with the control
  §1.2.2 relies on in place of a directory boundary. Two parts, each self-tested
  first and each asserting its file list is non-empty, so neither can pass by
  matching nothing:
  `test_no_test_module_reaches_for_the_real_clock` — no test module names
  `SystemClock`, excluding `tests/ports/test_clock.py` and the guard module
  itself, with the exemption asserted to actually use it; and
  `test_the_sanctioned_call_allowance_is_one_exact_line_in_one_exact_module` —
  the ambient-time scan skips exactly one full line, `return datetime.now(UTC)`
  in `ports/clock.py`, and `clock.py` contains exactly one such line.
  Covers: R2, R23.
- [x] T45 — Run `./init.sh` and the backend gates, confirm `uv export --package
  planner-api --no-dev` and `--package planner-ai --no-dev` still resolve with
  no runtime dependency added, and append the `R23 → test` map plus the
  mutation evidence to `progress/impl_week_calendar.md`. Covers: R23.

## Post-review addition — review finding P3 (round five)

> Added 2026-08-19 to close review finding P3 in
> `progress/review_week_calendar.md`. Nothing above is renumbered or altered.

- [x] T46 — Extend `backend/core/tests/test_no_ambient_time.py` with
  `test_no_core_module_but_the_port_names_the_real_clock`: `SystemClock` is
  named nowhere under `planner_core` except `ports/clock.py`, which declares it.
  This is the second half of `docs/architecture.md` §3.1 rule 6 — *nothing in
  `domain/` or `application/` may construct it* — which was unenforced:
  `SYSTEM_CLOCK` was applied under `TESTS_ROOT` alone, and `AMBIENT_TIME`
  cannot match `SystemClock()`, so an `application/`-layer construction passed
  the whole suite. Same discipline as T44: the pattern is self-tested first
  against a construction, an import, a module-level default and an attribute
  reference; the scanned file list is asserted non-empty and to contain
  `application/live_weeks.py` and `domain/calendar.py`; and the exempt module is
  asserted to actually declare `SystemClock`, so the exemption cannot rot into a
  hole covering nothing. Reuses `SYSTEM_CLOCK` and the module's existing
  constants through a shared `_reaches` helper, which the T44 scan now uses too.
  Covers: R2, R23.
