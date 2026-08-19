# Review — feature 2 (week_calendar)

**Verdict:** CHANGES_REQUESTED

Reviewer pass, 2026-08-18. Nothing under `backend/` or `frontend/` was modified
by this review: the mutation exercise in §6 restored every file byte-identical,
verified with `diff`. No git write command was run. The feature was **not**
marked `done`.

**Read this first:** the *code* is correct and does not need to change. Every
required change below is a documentation or verification-bookkeeping item. The
domain logic, the layering, the tests and every quality gate are approved as
they stand — see §3 and §6, where eleven deliberate mutations were each caught
by a named test.

---

## 1. Requirement coverage (FR → R)

Source: `feature_list.json` feature 2 `covers`, against
`specs/week_calendar/requirements.md`.

- `FR-MENU-01`: [x] cited by R10, R11, R12, R13, R14
- `FR-MENU-02`: [x] cited by R1, R2, R3, R4, R5, R6, R7, R8, R9, R20, R21, R22
- `FR-UX-06`:   [x] cited by R14, R15, R16
- `FR-AI-11`:   [x] cited by R1, R2, R4, R5, R17, R18, R19, R20, R22
- `FR-SHOP-05`: [x] cited by R1, R2, R4, R5, R17, R18, R19, R20, R22

No orphan `R<n>`: every R1–R22 carries an `Implements:` line citing at least one
frozen id, and every cited id exists in `docs/requirements.md` (lines 57, 58,
110, 152, 181).

**The two shared ids are legitimately split, not silently swallowed.**
`design.md` §1 defers the rest of `FR-AI-11` to feature 10 and the rest of
`FR-SHOP-05` to feature 7, and `feature_list.json` confirms both features do
carry those ids in their own `covers` arrays (verified: feature 7 →
`FR-SHOP-05`, feature 10 → `FR-AI-11`, feature 20 → `FR-UX-06`). The deferral is
real.

One observation, not a defect of this feature (see F6): `FR-MENU-01` also has a
*presentation* clause ("shall **present** two live weeks"), and feature 2 is the
only feature citing it. Feature 20 `frontend_spa` does not. That is a
`feature_list.json` question for the human, not something this feature can fix.

---

## 2. Test traceability (R → test)

Verified by reading each test, not by trusting the map in
`progress/impl_week_calendar.md` §2. Module keys: `C` =
`backend/core/tests/domain/test_calendar.py`, `L` =
`backend/core/tests/application/test_live_weeks.py`, `P` =
`backend/core/tests/ports/test_clock.py`, `N` =
`backend/core/tests/test_no_ambient_time.py`.

- R1  (Clock port, aware datetime): [x] `P::test_fake_clock_satisfies_the_clock_port` — asserts `isinstance(clock, Clock)` **and** `utcoffset() == timedelta(0)`, so it is not a bare import check
- R2  (no ambient time in `planner_core`): [x] `N::test_planner_core_never_calls_an_ambient_clock`, `N::test_week_calendar_tests_never_call_an_ambient_clock`, plus the positive control `N::test_the_ambient_time_pattern_detects_what_it_claims_to`
- R3  (naive instant → `NaiveInstant`): [x] `C::test_civil_date_rejects_a_naive_instant` — covers both a bare naive value and the `OffsetlessTz` case where `tzinfo` is set but `utcoffset()` is `None`
- R4  (Madrid, not host zone): [x] `C::test_civil_date_uses_madrid_not_utc` — summer and winter midnight pairs
- R5  (offset independence): [x] `C::test_the_same_moment_in_any_offset_gives_the_same_civil_date` — `+00:00` / `+05:00` / `-08:00`, asserting one date, one week id, one scope
- R6  (current = ISO week containing today): [x] `C::test_current_week_is_the_iso_week_containing_today`
- R7  (next = following week): [x] `C::test_next_week_is_the_week_after_the_current_one`
- R8  (`<isoYear>-W<ww>`, zero-padded): [x] `C::test_week_id_uses_the_iso_year_and_pads_the_week_number` — also asserts `date.year` would give the wrong answer in both cases
- R9  (`InvalidIsoWeek`): [x] `C::test_a_week_number_absent_from_its_iso_year_is_rejected` — `(2027,53)`, `(2026,0)`, `(2026,54)` reject; `(2026,53)` accepted
- R10 (7 days Mon→Sun): [x] `C::test_a_week_has_seven_days_from_monday_to_sunday`
- R11 (day numbers 1..7): [x] `C::test_day_numbers_run_one_for_monday_to_seven_for_sunday` — asserts Sunday is 7 *and* that `date.weekday()` reports 6, which is the trap
- R12 (lunch=1, dinner=2, ordered): [x] `C::test_each_day_offers_lunch_then_dinner`
- R13 (14 slots, day-then-slot order): [x] `C::test_a_week_has_fourteen_slots_ordered_by_day_then_slot`
- R14 (single clock reading): [x] `L::test_live_weeks_come_from_a_single_clock_reading` — asserts `clock.readings == 1` against a counting `FakeClock`
- R15 (Monday–Sunday range): [x] `L::test_live_weeks_expose_each_week_date_range`, `C::test_week_date_range_runs_monday_to_sunday` (incl. `2026-W53` spanning two calendar years)
- R16 (enum, no user-facing text): [x] `L::test_live_week_labels_are_stable_identifiers`, `N::test_calendar_modules_contain_no_user_facing_text`
- R17 (current week from today onward): [x] `C::test_scope_drops_days_before_the_given_day`, `L::test_current_week_scopes_from_today_and_next_week_scopes_whole`
- R18 (next week whole): [x] `C::test_scope_keeps_the_whole_week_when_the_day_precedes_its_monday`
- R19 (both slots of today, whatever the hour): [x] `C::test_scope_keeps_both_slots_of_the_given_day` — Sunday 22:00 Madrid still scopes lunch **and** dinner
- R20 (DST days): [x] `C::test_spring_forward_sunday_stays_in_its_week`, `C::test_autumn_ambiguous_hour_resolves_to_one_date_and_week`
- R21 (ISO year vs calendar year, 53-week years): [x] `C::test_next_week_is_the_week_after_the_current_one`, `C::test_week_id_uses_the_iso_year_and_pads_the_week_number`, `C::test_week_date_range_runs_monday_to_sunday`
- R22 (`FakeClock` only, no real clock/network): [x] `P::test_fake_clock_satisfies_the_clock_port`, `N::test_week_calendar_tests_never_call_an_ambient_clock` — the latter also asserts every module touching `civil_date` / `resolve_live_weeks` mentions `FakeClock`

No `R<n>` rests on a test that merely asserts "nothing raised". Every one
asserts a concrete value.

---

## 3. Verification actually re-run (not taken from the report)

### 3.1 `./init.sh` from the repo root

```
── 5. Quality gates ────────────────────────────────────
[OK]    ruff format
[OK]    ruff check
[OK]    mypy
...........................                                              [100%]
27 passed in 0.10s
[OK]    pytest (unit + contract, no AWS)
[OK]    prettier --check
[OK]    eslint
[OK]    vitest

── 6. Summary ──────────────────────────────────────────
[OK]    Environment ready. You can start working.
EXIT=0
```

Section 4 also reported `[OK] feature_list.json valid (23 features - blocked: 9,
done: 1, in_progress: 1, pending: 12)`, `[OK] No agent-generated IaC or CI
files`, `[OK] Requirement coverage: all 103 FR/NFR ids covered by features`.

### 3.2 Backend gates individually, from `backend/`

```
$ uv run ruff format --check .
18 files already formatted

$ uv run ruff check .
All checks passed!

$ uv run mypy .
Success: no issues found in 18 source files

$ uv run pytest -q --collect-only
27 tests collected in 0.07s
```

The 27 collected tests were listed in full and match the spec task list
one-for-one: 4 in `application/test_live_weeks.py`, 17 in
`domain/test_calendar.py`, 1 in `ports/test_clock.py`, 4 in
`test_no_ambient_time.py`, plus the pre-existing `test_scaffold.py`. **The green
is explainable**: no hook was skipped, no config fell back to defaults, and the
count matches T14–T38 exactly.

### 3.3 Runtime closures — `tzdata` did not leak

```
$ uv export --package planner-api --no-dev
-e ./core
    # via planner-api
-e ./lambda_api

$ uv export --package planner-ai --no-dev
-e ./core
    # via planner-ai
-e ./lambda_ai

$ (both closures) | rg -i tzdata   ->   no match, rc=1
```

`backend/core/pyproject.toml` line 6 still reads `dependencies = []`. The
`tzdata` addition is confined to `backend/pyproject.toml` lines 13-16, inside
`[dependency-groups] dev`, with a justification comment citing `design.md` §7.
Approved by the human, and it stayed where it was approved.

### 3.4 The design's environment claims, re-verified independently

```
$ uv run python -VV
Python 3.13.13 (main, Apr 14 2026, 14:30:19) [MSC v.1944 64 bit (AMD64)]

$ uv run python -c "import time, zoneinfo, tzdata; ..."
tzset present: False
TZPATH: ()
tzdata file: ...\backend\.venv\Lib\site-packages\tzdata\__init__.py
Madrid: Europe/Madrid
```

So `design.md` §6.2 is right on the facts: `time.tzset` does not exist here and
`zoneinfo` has no system database to read, meaning a `TZ` sweep could not work
and would prove nothing if it appeared to. **No `TZ` sweep exists in the
suite** — `rg` over `backend/core/tests` finds no `TZ`, no `tzset`, no
`monkeypatch.setenv`. Timezone determinism is proved by construction, exactly as
the design promised, and §6 below shows the proof has teeth.

Also re-derived from scratch, since the whole ISO-year trap rests on them:
`date(2026,12,28).isocalendar()` -> `(2026, 53, 1)`; `date(2025,12,31)` ->
`(2026, 1, 3)`; `date(2027,1,1)` -> `(2026, 53, 5)`. The tests use the two dates
that actually demonstrate the trap.

---

## 4. Layering (`docs/architecture.md` §3.1)

Checked by reading every import line under `backend/core/src/planner_core/`:

- `domain/` imports `application/`, `ports/`, an adapter, a handler or an AWS SDK: **no**. `domain/calendar.py` imports only `dataclasses`, `datetime`, `enum`, `typing`, `zoneinfo` and `planner_core.domain.errors`. [x]
- `core` imports `boto3` / `botocore` / `planner_api` / `planner_ai`: **no** — `rg` over `core/src` and `core/tests` returns nothing. [x]
- `core` declares a runtime dependency: **no** — `dependencies = []`. [x]
- `planner_core` calls `datetime.now()` or any other ambient-time function: **no**. The only textual occurrences in the tree are the banned-pattern literals inside the guard module itself, which excludes itself from its own scan. [x]
- `application/` imports an adapter or a handler: **no** — `live_weeks.py` imports `domain/calendar` and `ports/clock`, nothing else. [x]
- An adapter imported outside its Lambda's `wiring.py`: **n/a**, no adapters exist yet. [x]

The human's 2026-08-18 ruling holds exactly as stated: `civil_date`,
`current_week`, `next_week` and `slots_from` all take a plain `date` or
`datetime`; `Clock` lives in `ports/`; only `resolve_live_weeks` in
`application/` reads it; `domain/` never imports `ports/`.

---

## 5. Invariants exercised (`docs/verification.md` Level 4)

The feature touches `docs/architecture.md` §4 invariant **7** — *"Weeks are ISO
weeks in `Europe/Madrid`. Monday–Sunday. Every user must agree on which week is
current."* — and it is the property, not a happy path, that is tested:

- Weeks are ISO weeks, not calendar weeks: [x] `test_week_id_uses_the_iso_year_and_pads_the_week_number` asserts the calendar year *would* give a different id, in one case a non-existent one.
- Monday–Sunday, one-based: [x] `test_day_numbers_run_one_for_monday_to_seven_for_sunday` asserts both the right answer and the wrong one `date.weekday()` gives.
- Europe/Madrid, neither the host zone nor UTC: [x] `test_civil_date_uses_madrid_not_utc` plus `test_the_same_moment_in_any_offset_gives_the_same_civil_date`. The second is the real property test: one absolute moment, three offsets, one answer.
- *Every user agrees*: [x] `test_live_weeks_come_from_a_single_clock_reading` (`readings == 1`) is the anti-disagreement assertion — two reads could straddle midnight and hand out a non-adjacent pair.
- The offset changes underfoot: [x] both DST tests, including the ambiguous 02:30 hour asserted as two distinct instants with different `utcoffset()` that must still land on one date and one week.

Invariants 4 (additive bulk ops) and 6 (definitive-only sourcing) belong to
features 10 and 7. This feature owns only the calendar clause and correctly does
not pretend otherwise.

The `slots_from` single-implementation rule that `design.md` §1 makes
non-negotiable for features 7 and 10 is honoured: one function, one call site in
`application/`, no second code path for the next week. Mutation M3 below proves
it is load-bearing — `>` instead of `>=` breaks four tests across both layers.

---

## 6. Anti-hollow-green: the mutation exercise, re-run by the reviewer

**The report's own seven mutations could not be verified.** They left no
artifact and are not reproducible from the report, so I did not accept them. I
ran **eleven** mutations of my own instead — each applied to a scratchpad-backed
copy, `pytest` run, then restored and `diff`-checked (`restored-ok` printed for
every one). Final state after the last restore: `27 passed`.

| # | Mutation | Result |
|---|---|---|
| M1 | `civil_date` returns `instant.date()` — Madrid conversion dropped | **5 failed**: `..._uses_madrid_not_utc`, `..._same_moment_in_any_offset...`, `..._current_week_is_the_iso_week...`, both DST tests |
| M2 | `WeekDay.day_number` reads `date.weekday()` | **1 failed**: `..._day_numbers_run_one_for_monday_to_seven...` |
| M3 | `slots_from` uses `>` instead of `>=` — today dropped | **4 failed**, incl. `..._scope_keeps_both_slots_of_the_given_day`, which is R19's guard |
| M4 | `following()` as `iso_week + 1` | **1 failed**, and it fails by *raising* `InvalidIsoWeek: 2026-W54` — the validation catches the overflow the design predicted |
| M5 | `week_id` unpadded | **3 failed** |
| M6 | `IsoWeek.containing` uses `day.year` instead of the ISO year | **2 failed**: `assert '2025-W01' == '2026-W01'` |
| M7 | `resolve_live_weeks` reads the clock twice | **1 failed**: `readings == 2` |
| M8 | `NaiveInstant` guard switched to `tzinfo is None` | **1 failed**: the `OffsetlessTz` case, which is exactly why the design chose `utcoffset()` |
| G1 | `datetime.now()` added inside `planner_core` | **4 failed**, incl. `test_planner_core_never_calls_an_ambient_clock` |
| G2 | `CURRENT = "semana actual"  # última` | **2 failed**: the ASCII scan *and* the enum-value test |
| G3 | `CURRENT = "Semana actual"` — unaccented, pure ASCII | **1 failed**: `test_live_week_labels_are_stable_identifiers` |

M4, M6 and M8 are not in the implementer's list, and all three were caught. M3
is the one I most wanted: R19 ("today's lunch is still in scope") is the kind of
rule that quietly rots, and it is genuinely pinned.

**On the self-reported ASCII limitation** (known-context item 4): G3 confirms it
and also bounds it. A pure-ASCII Spanish string *would* pass
`test_calendar_modules_contain_no_user_facing_text`, but it does **not** slip
through overall, because the only string-valued API this feature exposes is
`LiveWeek`, and `test_live_week_labels_are_stable_identifiers` asserts its exact
values. Combined with the fact that the feature emits no user-facing strings at
all, **this is acceptable and needs no change.** It should not be inherited
uncritically by a later feature that *does* emit text: what that will need is a
value-level assertion against the messages module, not a wider `isascii()`.

---

## 7. Findings

### Medium

**F1 — Actively wrong references: `progress/impl_week_calendar.md` §6 points the
human at two defects that are already fixed.**

- §6.1 (lines 261-268) says *"`docs/data_model.md` §2 **still carries** the
  factual error"* about `2026-12-28` -> `2027-W01`. It does not.
  `docs/data_model.md` line 75 has been corrected in the working tree and now
  cites both of the dates the design proposed, with an inline *"Corrected
  2026-08-18"* note.
- §6.2 (lines 269-271) says *"`docs/conventions.md` § Python style **still says
  3.12**"*. It does not. `docs/conventions.md` lines 30-35 now specify
  `>=3.13, <3.14` and the `backend/.python-version` pin.

This is precisely the failure mode `AGENTS.md` §3.1 names — *"closing an item
leaves stale references that are actively wrong, not merely dated"*. The report
is a live document addressed to the reviewer and the human; as written it asks
the human to redo work he has already done.

**F2 — The `Clock` port has no contract suite, so CHECKPOINTS C4 cannot be
ticked.** `backend/tests/contract/` is empty. `docs/verification.md` requires
*"for every port, one suite in `backend/tests/contract/` [that] runs against both
the in-memory fake and the real adapter"*, and calls a port with a fake but no
contract run *"only half-verified"*; C4 lists *"Every port has a contract
suite"*.

In fairness: the approved `design.md` §3 never planned one, no real `Clock`
adapter exists anywhere yet (adapters are Lambda-owned), and a suite
parametrized over a single implementation would assert nothing beyond what
`test_fake_clock_satisfies_the_clock_port` already asserts. The practical value
today is near zero — **but the gap must be recorded rather than discovered when
the first `SystemClock` lands.** Either add the suite now, or record an explicit
dated deferral naming the feature that will add it. Silence is the one option
that is not acceptable.

### Minor

**F3 — `planner_core/domain/errors.py` has no test module, and nothing asserts
the exception hierarchy.** C4 asks for *"at least one test module per source
module"*. Concretely: no test asserts that `NaiveInstant` and `InvalidIsoWeek`
are subclasses of `PlannerError`. That relationship is the entire point of the
base class — `docs/conventions.md` § *Error handling* has the handler layer
catching domain exceptions — and features 3-13 will all inherit from it. Two
`issubclass` assertions close it.

**F4 — Gate-time notes in `specs/week_calendar/design.md` now read as present
tense and are false.** §5's *"Note for the human at the spec gate"* (lines
257-280), §9 alternative A (*"The illustrative snippet in `docs/specs.md` shows
`current_week(clock)`"*, lines 468-475) and §10's *"`docs/conventions.md` … still
says 3.12"* (line 554) were all true at the gate and are all false now:
`docs/data_model.md`, `docs/specs.md` and `docs/conventions.md` have each since
been corrected. The *arguments* in §5 and §9 remain sound; only the citations
rot.

This is an approved spec, so I am **not** asking for a rewrite — retro-editing an
approved artifact is its own hazard. A one-line *"Resolved 2026-08-18"*
annotation on each of the three is the right weight, and the call is the human's.

**F5 — EARS: three requirements combine two `SHALL` clauses.** `docs/specs.md`
says *"Never combine several SHALLs in one requirement. Split instead."* R4
(`SHALL derive … and SHALL NOT use`), R8 (`SHALL identify … SHALL NOT use`) and
R22 (`SHALL provide a FakeClock … and the tests SHALL obtain`) each carry two.
This passed the human's spec gate, both halves of each are tested, and nothing is
left unverifiable as a result. Recorded for the next `spec_author` pass, not for
rework here.

### Informational

**F6 — `FR-MENU-01`'s presentation clause has no UI feature citing it.** Only
feature 2 lists it; feature 20 `frontend_spa` does not. `init.sh`'s coverage
check is satisfied (every id appears in some `covers`), so nothing is red — but
"shall **present** two live weeks" is not backend work. A `feature_list.json`
question for the human.

**F7 — `ruff`'s isort groups `support` as third-party** in the test modules, so
`from support.fakes import FakeClock` sits above the `planner_core` block. That
is `ruff --fix`'s own output and `docs/conventions.md` says not to hand-sort. The
implementer correctly declined to change shared config unilaterally. If the human
wants it grouped, it is a `known-first-party` setting in `backend/pyproject.toml`.

---

## 8. Tasks complete

All forty tasks in `specs/week_calendar/tasks.md` are `[x]`, and each was
verified against the artifact rather than against the tick:

- T1-T2 (setup): [x] — `tzdata` in the dev group only; `support/.gitkeep`
  deleted, `support/__init__.py` and `tests/conftest.py` present.
- T3-T5 (port, error base, fake): [x] — `Clock` is `@runtime_checkable` with
  `now() -> datetime`; `FakeClock.at()` helper and `readings` counter present.
- T6-T10 (domain): [x] — including the `utcoffset() is None` check T6 explicitly
  demands over `tzinfo is None`, `day_number` as a derived property, and
  `following()` built on date arithmetic rather than `iso_week + 1`.
- T11-T13 (application): [x] — `resolve_live_weeks` calls `clock.now()` exactly
  once, proved by M7.
- T14-T38 (tests): [x] — every test named in a task exists under that exact name;
  all 25 accounted for in the collected list.
- T39 (traceability map): [x] — present in `progress/impl_week_calendar.md` §2
  and independently confirmed correct in §2 of this review.
- T40 (`./init.sh` green): [x] — re-run here, exit 0.

No task is left `[ ]`, so no justification is owed.

---

## 9. Boundaries

- No new `*.tf` / `*.tfvars`: [x] — `init.sh` §4 also reports `[OK] No agent-generated IaC or CI files`.
- No new `.github/workflows/**`: [x]
- No architecture decision from `docs/architecture.md` §2 made silently: [x] — nothing here needs P2-P6. The `tzdata` runtime question brushes P6 and was handled exactly as the approved `design.md` §7 allows: dev group only, with the Lambda-vs-`core` placement flagged and left open.
- Frozen requirement docs unmodified: [x] — `git diff HEAD` over `docs/requirements.md`, `docs/app_user_stories.md`, `docs/coverage_analysis.md`, `docs/gaps_and_resolutions.md` and `docs/gaps_pending_stakeholders.md` is empty.
- `feature_list.json` untouched except `status: pending -> in_progress` for feature 2: [x] — verified by `git diff`. The implementer did **not** mark it `done`.
- No user-facing Spanish literal outside a messages module: [x] — verified by the ASCII scan, by the enum-value test, and by reading all four modules.
- No stray files: [x] — the untracked set is exactly the feature's own sources, tests, spec folder and report.

---

## 10. Checkpoints

- **C1 — The harness is complete:** [x] base files present, four docs present, five frozen docs unmodified, `./init.sh` exit 0.
- **C2 — State is coherent:** [x] exactly one `in_progress` (feature 2); all nine `blocked` features carry a non-empty `blocked_reason`; the one `done` feature has passing tests; `progress/current.md` describes this session and ends with *"Reviewer pass on feature 2. The implementer does not mark it `done`."*
- **C3 — The code respects the architecture:** [x] every sub-box verified in §4. Two Lambda packages, no more. No debug `print()`, no context-free TODO (`rg` finds neither). Every dependency traces to an approved `design.md` — `tzdata` to `specs/week_calendar/design.md` §7.
- **C4 — Verification is real:** [ ] — four boxes hold outright: `ruff check` clean, `mypy` clean with no `# type: ignore` anywhere in the tree, 27 tests green, and `core` tests running with no AWS, no network and no real clock. Two do not: **"Every port has a contract suite"** (F2 — `backend/tests/contract/` is empty and a port now exists) and **"at least one test module per source module"** (F3 — `domain/errors.py` has none).
- **C5 — The session closed properly:** [x] no suspicious untracked files; `progress/history.md` has the feature-1 entry; feature 2 correctly left `in_progress`. The final close-out entry is the human's to write.
- **C6 — Spec Driven Development:** [x] all three spec files present; strict EARS with the F5 nit; every `R<n>` cites an `FR-*`; every `FR-*` in `covers` reaches an `R<n>`; every `R<n>` reaches a concrete test; all tasks ticked; `init.sh` confirms all 103 ids covered with no unknown id.
- **C7 — Human-owned boundaries were respected:** [x] all five boxes, per §9.

---

## 11. Required changes

1. **Correct `progress/impl_week_calendar.md` §6.1 and §6.2** (F1). Both items
   are already resolved: `docs/data_model.md` line 75 was corrected on
   2026-08-18 and now cites 2025-12-31 -> `2026-W01` and 2027-01-01 ->
   `2026-W53`; `docs/conventions.md` lines 30-35 now specify Python 3.13 with a
   bounded range. Mark them resolved rather than deleting them — that the design
   flagged them and the human acted is worth keeping.
2. **Resolve the `Clock` contract-suite gap** (F2) so CHECKPOINTS C4 stops being
   half-empty. Either add contract coverage for the port under
   `backend/tests/contract/` now, or record an explicit dated deferral naming the
   feature that will add it alongside the first real adapter.
3. **Add a test module for `planner_core/domain/errors.py`** (F3) asserting
   `issubclass(NaiveInstant, PlannerError)` and
   `issubclass(InvalidIsoWeek, PlannerError)` — the property the handler layer
   will depend on, currently unasserted.

### Recommended, the human's call

4. Annotate the three gate-time notes in `specs/week_calendar/design.md` (§5,
   §9 A, §10) as *Resolved 2026-08-18* rather than rewriting them (F4).
5. Decide whether feature 20 should also cover `FR-MENU-01` (F6).

---

## 12. What could not be verified

- **The implementer's original seven mutations.** They left no artifact and are
  not reproducible from the report. I did not pass them along as established; I
  ran eleven of my own instead (§6), four of which the report does not list. The
  report's per-mutation failure *counts* therefore remain unconfirmed — my M2,
  for instance, broke one test where the report claims two, most likely because
  the report's version mutated `SlotRef.day_number` as well as `WeekDay`'s. The
  *conclusion* the report draws, that no gate here is hollow, is independently
  confirmed.
- **Behaviour on a host that has a system IANA database.** Every check above ran
  on this Windows machine, where `zoneinfo.TZPATH` is empty and `Europe/Madrid`
  resolves through the `tzdata` package. The `design.md` §7 deployment caveat —
  whether the Lambda runtime supplies the database or the Lambda packages must
  declare `tzdata` — remains open, is P6-adjacent, and is correctly left to the
  human.
- **SonarQube.** It runs in the project's quality pipeline and is not an agent's
  to invoke (`docs/verification.md` Level 1).

---
---

# Re-review — feature 2 (week_calendar), round two

**Verdict: APPROVED**

Reviewer pass 2, 2026-08-18. Everything above this line is the round-one record
and is **unchanged**. This section supersedes round one's verdict, its C4 line
and its section 11 "Required changes".

Nothing under `backend/` or `frontend/` was modified by this review. The one
mutation exercise below ran against a **copy** in the scratchpad, never the repo
(proved by the interpreter reporting the module path it actually imported). No
git write command was run. The feature was **not** marked `done`.

---

## R1. Findings from round one — verdict each

Every claim below was checked against the file, not against the hand-off
summary. That is the point of F1.

### F1 (Medium) — **CLOSED**

`progress/impl_week_calendar.md` section 6 items 1 and 2 are struck through and
marked **RESOLVED 2026-08-18, before this implementation ran** (lines 261-278).
Kept, not deleted, as recommended.

The mechanism is named where a future reader will trip over it: *"copied forward
from the design without re-reading the file, which is the `AGENTS.md` 3.1
trap"*. That is the part worth more than the correction itself.

The two underlying docs are genuinely correct — verified directly, not inferred:

- `docs/data_model.md` line 75 cites **2025-12-31 -> `2026-W01`** and
  **2027-01-01 -> `2026-W53`**, with an inline *"Corrected 2026-08-18"* note
  that states why 2026-12-28 was the wrong illustration. Correct.
- `docs/conventions.md` lines 30-35 specify `requires-python = ">=3.13, <3.14"`,
  the `backend/.python-version` pin, and that the upper bound is deliberate.
  Correct.

### F2 (Medium) — **CLOSED as a dated deferral**

`CHECKPOINTS.md` lines 48-60, sitting directly beneath the C4 line *"Every port
has a contract suite"* — so it is found by whoever next tries to tick that box,
which was the requirement. Round one offered exactly two acceptable outcomes,
*"add the suite now, or record an explicit dated deferral naming the feature
that will add it"*; this is the second, and it is the human's call to make.

Its factual claims were verified rather than accepted:

- *"`backend/tests/contract/` is empty"* — confirmed, it holds only `.gitkeep`.
- *"Feature 14 `persistence_ports` ... whose third acceptance criterion already
  requires a contract suite"* — confirmed **verbatim** in `feature_list.json`:
  *"A contract suite in backend/tests/contract exercises each port and is
  parametrized to run against any implementation (fake now, real adapter
  later)"*. The deferral is not inventing an owner; it attaches to work already
  scoped.

The two added constraints are what make it more than a note: it must cover
`Clock` **alongside** the persistence ports, and **the first `SystemClock` must
not land before it**. That second clause is what stops the gap being
rediscovered at the worst moment.

### F3 (Minor) — **CLOSED**

`backend/core/tests/domain/test_errors.py`, 3 tests, assessed on its merits:

- **It verifies lineage, it does not restate declarations.**
  `test_a_domain_error_raised_by_real_code_is_caught_by_the_base` provokes
  `IsoWeek(2026, 54)` through real code, catches it with `except PlannerError`,
  then asserts the caught value is an `InvalidIsoWeek`. That is the handler-layer
  behaviour, not an `issubclass` echo.
- **It fails if the inheritance breaks — confirmed independently.** I copied
  `core/src` and `core/tests` to the scratchpad, changed
  `class NaiveInstant(PlannerError)` to `(Exception)` and
  `class InvalidIsoWeek(PlannerError)` to `(Exception)` **in the copy**, and ran
  the module against it with `PYTHONPATH` pointed at the copy:

```
module from: ...\scratchpad\mut\src\planner_core\domain\calendar.py
FAILED test_every_domain_error_descends_from_planner_error
FAILED test_a_domain_error_raised_by_real_code_is_caught_by_the_base
E       planner_core.domain.calendar.InvalidIsoWeek: 2026-W54
2 failed, 1 passed in 0.54s
```

  This reproduces the implementer's A5 result exactly, including the
  escaping-exception failure mode. `test_planner_error_is_a_plain_exception`
  passing under the mutation is correct — it is a claim about the base alone,
  and the report says so rather than overclaiming.
  The repository copy is untouched: `calendar.py` lines 16 and 20 still read
  `(PlannerError)`.
- **Proportionate, no scope creep.** One new file. `git status` shows the
  untracked set is still exactly the feature's own artifacts — no new module, no
  opportunistic refactor. `mypy` went 18 -> 19 files, `pytest` 27 -> 30. Raising
  `NaiveInstant` directly rather than through `civil_date` is the right call and
  its reason (the `test_no_ambient_time.py` scan) is recorded in the module
  docstring.

### F4 (Minor) — **CLOSED**

All three gate-time notes in `specs/week_calendar/design.md` carry a one-line
*Resolved 2026-08-18* annotation and the arguments beneath are untouched — the
right weight for an approved artifact:

- Section 5, line 259 — the `docs/data_model.md` note, explicitly kept *"as the
  record of why the change was made"*.
- Section 9 alternative A, line 473. Its claim that *"`docs/specs.md` has since
  been corrected — its example no longer shows `current_week(clock)`"* is
  **true**: `docs/specs.md` line 131 now reads `current_week(today)`, and line
  145 carries the correction note.
- Section 10, line 562 — the Python 3.12 note.

### F6 (Informational) — **CLOSED**

`FR-MENU-01` is in feature 20 `frontend_spa`'s `covers` (`feature_list.json`
line 393). `init.sh` still reports all 103 ids covered. The presentation clause
now has a UI feature behind it.

### F5 (Minor) — **OPEN, the human's decision, not re-opened here**

R4 (line 47), R8 and R22 (line 161) still carry two `SHALL` clauses each,
unmodified. Round one already recorded this as *"for the next `spec_author`
pass, not for rework here"*; both halves of each are tested and nothing is left
unverifiable. Noted, no new recommendation.

### F7 (Informational) — **OPEN, untouched**

The `ruff` isort grouping of `support` is unchanged. It needs a shared-config
decision. Noted, no new recommendation.

---

## R2. Tasks

- T1-T40: [x] — unchanged from round one, verified not renumbered or reworded.
- **T41: [x]** — appended under a new *Review follow-up* heading at the end of
  `specs/week_calendar/tasks.md` (lines 169-176), citing finding F3 and
  `CHECKPOINTS.md` C4, and covering **R3, R9** — the same two `R<n>` that T4
  already cites for `errors.py`. No new requirement was invented.

Nothing above T41 was altered: the file still reads T1 at line 11 through T40 at
line 166, with the same headings and the same `Covers:` lines.

---

## R3. Gates re-run by the reviewer

`./init.sh` from the repo root — **exit 0**:

```
[OK]    feature_list.json valid (23 features - blocked: 9, done: 1, in_progress: 1, pending: 12)
[OK]    Specs present for every non-pending sdd feature
[OK]    No agent-generated IaC or CI files
[OK]    Requirement coverage: all 103 FR/NFR ids covered by features
...
[OK]    ruff format
[OK]    ruff check
[OK]    mypy
..............................                                           [100%]
30 passed in 0.12s
[OK]    pytest (unit + contract, no AWS)
[OK]    prettier --check
[OK]    eslint
[OK]    vitest
[OK]    Environment ready. You can start working.
EXIT=0
```

From `backend/`, each gate individually:

```
$ uv run ruff format --check .   ->  19 files already formatted
$ uv run ruff check .            ->  All checks passed!
$ uv run mypy .                  ->  Success: no issues found in 19 source files
$ uv run pytest -q               ->  30 passed in 0.12s
```

**30 as expected**, and the delta is explainable: 27 plus the 3 tests of
`test_errors.py`, with 18 -> 19 files in `ruff format` and `mypy` accounting for
the single new module. No gate was skipped, no count is unaccounted for.

---

## R4. New instances of the F1 failure mode — searched for, none blocking

Every factual claim written in the last round was re-checked against its target
file. All of them hold: the `CHECKPOINTS.md` deferral (contract dir empty,
feature 14's criterion verbatim), the three `design.md` annotations (including
the `docs/specs.md` correction they assert), the struck `impl` section 6 items,
and the addendum's A2-A5 numbers. **No new actively-wrong reference was
introduced.**

Three dated-not-wrong items, informational, no action required:

1. `progress/impl_week_calendar.md` line 4 still reads *"Tasks: T1-T40, all
   ticked"*. There are now 41. This sits above the addendum's explicit
   "everything above this line is the original report and is unchanged"
   demarcation, and A3 states T41 plainly, so it is marked historical rather
   than misleading — that demarcation is the correct pattern and is why this is
   not an F1 repeat. Worth knowing only because a header is the most-read line
   in a file.
2. `progress/current.md` line 12 says *"Tasks T1..T40"* in the Plan; the Log
   below it (lines 40-47) records the F3 follow-up and T41 accurately, and the
   Next step correctly reads *"Human sign-off ... The implementer does not mark
   it `done`."*
3. `specs/week_calendar/design.md` line 282 says the two ISO-year dates are
   *"used as test cases below (T21)"*; in `tasks.md` they are **T23**
   (`test_week_id_uses_the_iso_year_and_pads_the_week_number`). A pre-existing
   cross-reference slip in the approved design, not introduced this round, and
   the test does exist under the right name.

---

## R5. Boundaries — re-verified

- No new `*.tf` / `*.tfvars` / `.github/workflows/**`: [x] — `git status` finds
  none and `init.sh` reports `[OK] No agent-generated IaC or CI files`.
- Frozen requirement docs unmodified: [x] — `git diff HEAD` over all five is
  empty.
- `feature_list.json` diff is exactly two lines: [x] — feature 2
  `pending -> in_progress`, and `FR-MENU-01` added to feature 20. **Feature 2 is
  not marked `done`.**
- No architecture decision from section 2 made silently: [x] — the C4 deferral
  is a *verification* scheduling decision recorded in the open, and it was the
  human's, not an agent's.
- No stray files: [x] — the untracked set outside `backend/` is only
  `progress/impl_week_calendar.md`, `progress/review_week_calendar.md` and
  `specs/week_calendar/`.
- Reviewer wrote no code: [x].

---

## R6. Checkpoints — round two

- **C1 — The harness is complete:** [x]
- **C2 — State is coherent:** [x] one `in_progress`; `progress/current.md`
  describes this session including the follow-up round.
- **C3 — The code respects the architecture:** [x] unchanged from round one; the
  only new file is a test module importing `planner_core.domain` alone.
- **C4 — Verification is real:** [x] — with one sub-box deliberately open.
  `ruff check` clean, `mypy` clean with no `# type: ignore`, 30 tests green, no
  AWS / network / real clock. *"At least one test module per source module"* now
  **holds** — F3 closed it. *"Every port has a contract suite"* remains
  unticked, but **by a dated, owner-assigned deferral recorded at the checkpoint
  itself**, which is precisely the remedy F2 demanded. That is scheduled debt
  owned by feature 14, not an unverified claim by feature 2.
- **C5 — The session closed properly:** [x] the final close-out entry remains
  the human's to write.
- **C6 — Spec Driven Development:** [x] all 41 tasks ticked; every `FR-*` in
  `covers` reaches an `R<n>`; every `R<n>` reaches a concrete test; the F5 EARS
  nit is recorded and open by the human's choice.
- **C7 — Human-owned boundaries were respected:** [x]

---

## R7. Required changes

**None.** All three round-one required changes are closed, and both recommended
items were actioned. F5 and F7 are open by explicit decision and neither blocks
this feature.

Feature 2 is left `in_progress`. **The human closes it.**

---
---

# Re-review — feature 2 (week_calendar), round three

**Verdict: CHANGES_REQUESTED**

Reviewer pass 3, 2026-08-18. Everything above this line is the round-one and
round-two record and is **unchanged**. This section supersedes round two's
verdict.

Nothing under `backend/` or `frontend/` was modified. The fourteen mutations in
§T3 ran against a **copy** in the scratchpad; the repository sources were
confirmed byte-identical afterwards (`diff -r -x __pycache__` over `core/src`
and `core/tests` reported no difference). No git write command was run.
`specs/week_calendar/requirements.md` was not edited. The feature was **not**
marked `done`.

**Read this first: the code is right and the guards are real.** `SystemClock` is
correct, the enforcement §1.2.2 rests on survived every attack I could think of
(§T3), and every gate is green with 34 tests. The single finding is a
**documentation-consistency** one — the one the human asked me to rule on, plus
four more instances of it that this round of edits missed.

---

## T1. The ruling on R2 — it is false as written

### The claim

`specs/week_calendar/requirements.md:63-65`:

> The system SHALL NOT call `datetime.now`, `datetime.utcnow`, `date.today`,
> `time.time`, `time.localtime` or any other ambient-time function **anywhere in
> the `planner_core` package**.

`backend/core/src/planner_core/ports/clock.py:43` is inside the `planner_core`
package and reads `return datetime.now(UTC)`. **R2 is falsified by the code it
governs.** Not ambiguous, not merely imprecise: the requirement states a
universal, and a counter-example ships in the same distribution.

### Does R23's note adequately scope it? No — for three independent reasons

R23's note (`requirements.md:211-215`) says *"R2 stands unchanged, with one line
of one module as its sanctioned exception"*, and `design.md:596` repeats *"R2
still holds."* Neither claim rescues R2, because:

1. **It breaks a hard rule of `docs/specs.md`, not a stylistic preference.**
   `docs/specs.md:73` — *"Each requirement MUST be verifiable by at least one
   concrete test."* R2 as written has **no** such test.
   `test_planner_core_never_calls_an_ambient_clock` verifies *R2 minus the
   exception*, because `_offenders()` at `test_no_ambient_time.py:54` skips the
   line. The strongest statement any test in the suite proves is strictly weaker
   than the one R2 makes. That is the definition of an unverifiable requirement,
   and it is the one thing `docs/specs.md` says a requirement may not be.

2. **The traceability chain routes readers past the note, not through it.** The
   chain is `FR-* -> R<n> -> T<n> -> test`. A reader arriving from `FR-MENU-02`
   lands on R2 and on its tests. Nothing on that path passes through R23. R23 is
   a *different* requirement, cited by different tasks, and its note is the only
   place in the repository where the carve-out is stated as a carve-out rather
   than asserted away.

3. **`AGENTS.md` §3.1 names exactly this failure**: *"Closing an architecture
   item leaves stale references that are actively wrong, not merely dated."*
   §1.2.2 was closed on 2026-08-18; R2 is one of its stale references. The
   correction pattern the project has already accepted twice — the struck-through
   `impl` §6 items, the *Resolved 2026-08-18* annotations in `design.md` — was
   applied to five other artifacts this round and not to this one.

The mitigating argument, that retro-editing an approved spec is its own hazard
(round one's F4 reasoning), **does not apply here.** `requirements.md` was
already amended post-approval in this same round: R23, its note, and rows in both
coverage tables. The amendment touched the file and chose to record the exception
against a *different* requirement than the one it modifies. Amending R2 in that
same amendment is not a new hazard — it is finishing the one already under way.

### The recommended fix — amend R2's text (the human decides; I did not edit it)

One `SHALL NOT`, zero new `SHALL`, no new requirement, no renumbering:

```markdown
## R2
Implements: FR-MENU-02, FR-AI-11, FR-SHOP-05

The system SHALL NOT call `datetime.now`, `datetime.utcnow`, `date.today`,
`time.time`, `time.localtime` or any other ambient-time function anywhere in
the `planner_core` package, except in the single statement of `SystemClock.now`
in `planner_core.ports.clock` that implements the `Clock` port (R23).
```

Checked against the rules that apply to it: EARS **ubiquitous** pattern with a
scope qualifier; **one** `SHALL NOT` and no `SHALL`, so it does **not** join
R4/R8/R16/R22 as a fifth accepted deviation; it cites R23, so the two stay linked
in both directions; and its text becomes exactly as narrow as `SANCTIONED_CALL`
at `test_no_ambient_time.py:38`, which is the property the test actually proves.
A dated note beneath it, in the pattern already used for R23, would carry the
*why*.

**Alternatives considered and rejected:**

- *Leave R2 and rely on R23's note.* That is the status quo, and it is the
  defect.
- *Split it: R2 keeps the prohibition, a new R24 states the exception.* Adds a
  fifth `SHALL` requirement citing the same three frozen ids, and an exception is
  not a behaviour to require — it is a qualifier on a prohibition. Strictly
  worse.
- *Broaden the exclusion to "outside `planner_core.ports`".* **Actively
  dangerous.** It would legalise any future ambient call anywhere under `ports/`,
  which is precisely the widening the guard exists to prevent. The requirement
  must never be looser than the test.

---

## T2. The same defect in four more places — missed by this round's edits

R2 is not the only unqualified absolute §1.2.2 invalidated. `AGENTS.md` §3.1
prescribes the remedy directly: *"After closing one, grep its name across
`docs/`, `AGENTS.md` and `feature_list.json`."* That grep was not run — and three
of the five sites below sit in files this round **did** edit.

| Site | Text | Status |
|---|---|---|
| `docs/architecture.md:277` (§3.1 rule 6) | *"Time is a **port**, never `datetime.now()` inside `core`"* | **False.** And §1.2.2 explicitly invokes this rule (*"which §3.1 rule 6 exists to prevent"*), so the document contradicts itself: rule 3 was amended for §1.2.2, rule 6 was not. |
| `docs/architecture.md:407` (§6 *What NOT to do*) | *"Do not call `datetime.now()` inside `core`. Inject a clock port."* | **False.** |
| `CHECKPOINTS.md:33` (C3) | *"[ ] No `datetime.now()` inside `planner_core`."* | **False**, and this file *was* edited this round — the C4 deferral was amended, this box six lines above it was not. As written it instructs the next reviewer to fail C3. |
| `.claude/agents/reviewer.md:31` | *"Does `planner_core` call `datetime.now()`? -> reject."* | **False**, and normative: it instructed me to reject this feature outright. |
| `.claude/agents/implementer.md:55-56` | *"`core` … never calls `datetime.now()`. Adapters live in the Lambda packages"* | **False**, and it carries the *"adapters are Lambda-owned"* framing the `CHECKPOINTS.md` amendment already identified as the wrong reasoning. |

`feature_list.json:66` and `requirements.md:231` both say *"no domain code calls
`datetime.now()`"* — scoped to **domain**, and `ports/clock.py` is not domain.
Those two are **correct as written** and need no change. `docs/verification.md:89`
(*"Mocking `datetime.now()` -> inject a `Clock` port"*) is about mocking, not call
sites. **Correct**, no change.

---

## T3. The `SystemClock` guard — attacked, not assumed

§1.2.2's justification is that *"enforcement is mechanical rather than
geographic."* If the guard can be defeated, the architecture decision loses its
basis, so I tried to defeat it. Fourteen mutations, each applied to a scratchpad
copy, run, then reverted; final state `34 passed`, sources verified identical to
the repository.

**Sanctioned-call allowance — cannot broaden:**

| # | Mutation to `ports/clock.py` | Result |
|---|---|---|
| G4 | a second class whose body is an identical `return datetime.now(UTC)` | **1 failed** — `..._allowance_is_one_exact_line_in_one_exact_module`, on `2 == len([...])` |
| G5 | `return datetime.now()` (naive) | **2 failed** — the allowance test **and** `test_planner_core_never_calls_an_ambient_clock` |
| G6 | `instant = datetime.now(UTC)` then `return instant` | **2 failed** (same pair) |
| G7 | `return datetime.now(UTC) + timedelta(0)` | **2 failed** (same pair) |
| G8 | `return datetime.utcnow()` | **2 failed** (same pair) |
| G9 | trailing whitespace on the sanctioned line | **2 failed** (same pair) |

Every near-miss the brief named is caught, and each **fails closed**: losing the
`fullmatch` costs the exemption, so the line immediately becomes an offender. The
allowance cannot silently widen without editing `SANCTIONED_CALL` at
`test_no_ambient_time.py:38`, which is a visible change to the guard itself.

**`SystemClock` reach — the exemption cannot silently widen:**

| # | Mutation | Result |
|---|---|---|
| G10 | new test module: `from planner_core.ports.clock import SystemClock` | **1 failed** — `test_no_test_module_reaches_for_the_real_clock` |
| G11 | module-qualified: `from planner_core.ports import clock` then `clock.SystemClock()` | **1 failed** (same) |
| G12 | test module calls `datetime.now(UTC)` itself, bypassing `SystemClock` | **1 failed** — `test_week_calendar_tests_never_call_an_ambient_clock` |
| G13 | `tests/conftest.py` reaches for it | **1 failed** |
| G14 | `tests/support/fakes.py` reaches for it | **1 failed** |
| G15 | delete `tests/ports/test_clock.py` — exemption points at nothing | **1 failed** — `DEFAULT_CLOCK_TEST.is_file()` at line 160 |
| G16 | exempt module keeps its name but stops using `SystemClock` — a hollow exemption | **1 failed** — the `SYSTEM_CLOCK.search(...)` assertion at line 161 |

G15 and G16 are the ones that answer the brief. The exemption is a **single
hard-coded path** (`DEFAULT_CLOCK_TEST`, line 36) asserted both to exist and to
actually contain `SystemClock`. It cannot decay into a hole covering nothing, and
it cannot be extended to a second module without editing the guard.
`planner_core/ports/__init__.py` re-exports nothing, so there is no second import
path to the class either.

**`SystemClock` semantics:**

| # | Mutation | Result |
|---|---|---|
| G18 | `datetime.now(UTC).replace(tzinfo=None)` — naive | **3 failed**, incl. `test_system_clock_satisfies_the_clock_port_and_returns_an_aware_instant` on `utcoffset() is not None` |
| G19 | `datetime.now(timezone(timedelta(hours=2)))` — aware but not UTC | **3 failed** (same test, on `utcoffset() == timedelta(0)`) |

`clock.py:43` is `datetime.now(UTC)`; `utcnow()` appears nowhere in the tree
except as a banned literal inside the guard and as a warning in prose. The test
is not a "nothing raised" test: it asserts `isinstance` against the
`@runtime_checkable` `Protocol`, `isinstance(instant, datetime)`,
`utcoffset() is not None`, **and** `utcoffset() == timedelta(0)`.

**§1.2.2's basis holds.** The mechanical control is genuinely stronger than the
directory boundary it replaces — G13 and G14 prove it reaches `conftest.py` and
`support/fakes.py`, which a `tests/` layout convention never would.

### Two bounded limitations — recorded, no change required

1. **Deliberate obfuscation evades it.** G17 —
   `getattr(clock, "System" + "Clock")` in a new test module — **passed, 35 tests
   green.** No text scan can beat string concatenation, and there is no
   *accidental* form of this: the failure mode the guard defends against is
   someone typing the import, and that is caught. Recorded on the same footing as
   round one's ASCII limitation: real, bounded, not worth a different mechanism.
2. **Scope is `backend/core/tests/` only.** `TESTS_ROOT` (line 19) is the `core`
   test root, so `backend/tests/contract/` and the Lambda packages' `tests/` are
   not scanned. That is **correct** — §1.2.2's stated objection is about `core`
   tests, and a future `Clock` contract suite must instantiate `SystemClock` —
   but whoever writes that suite should know the guard will not be watching.

---

## T4. R23 — one `SHALL`, not a fifth deviation

Counted mechanically across every requirement rather than by eye — the method
`requirements.md:22-28` says produced the R16 correction:

```
R1 1 · R2 1 · R3 1 · R5-R7 1 · R9-R15 1 · R17-R21 1 · R23 1
R4 3 · R8 3 · R16 3 · R22 3      <- 2 real SHALLs + 1 inside the "Two SHALLs" note
```

**R23 carries exactly one `SHALL`.** The trailing *"which returns … and imports
nothing outside the Python standard library"* is a relative clause qualifying the
thing provided, not a second obligation. The accepted-deviation set stays
R4/R8/R16/R22 — no fifth entry, and the rule newly added to
`.claude/agents/spec_author.md` was honoured.

---

## T5. Tasks, coverage and traceability

- **T42-T45 appended, nothing renumbered.** T1 is still at line 11, T40 at 166,
  T41 at 171 — identical to the round-two record. T42-T45 sit under a new heading
  at line 178, *"Post-approval addition — `SystemClock`"*, carrying the same
  dated demarcation the earlier addenda used.
- **All 45 tasks are `[x]`.** No `[ ]` anywhere, so no justification is owed.
- **Coverage map updated for R23**: `FR-MENU-02`, `FR-AI-11` and `FR-SHOP-05`
  each gained `R23`, and the acceptance-criterion table's *"Clock port in
  `planner_core.ports`"* row now reads `R1, R2, R23`. All three ids exist in
  `docs/requirements.md`. No new `FR-*` is claimed and none is orphaned.
- **R23 -> test**, verified by reading the tests rather than the map:
  `test_system_clock_satisfies_the_clock_port_and_returns_an_aware_instant`
  (concrete assertions, pinned by G18/G19),
  `test_no_test_module_reaches_for_the_real_clock` (pinned by G10-G16),
  `test_the_system_clock_pattern_detects_what_it_claims_to` (positive control),
  and `test_the_sanctioned_call_allowance_is_one_exact_line_in_one_exact_module`
  (pinned by G4-G9).
- **R1-R22 -> test**: unchanged from round one §2, re-confirmed by the full suite
  passing with no existing test modified.

---

## T6. Gates re-run by the reviewer

`./init.sh` from the repo root — **exit 0**:

```
[OK]    feature_list.json valid (23 features - blocked: 9, done: 1, in_progress: 1, pending: 12)
[OK]    Specs present for every non-pending sdd feature
[OK]    No agent-generated IaC or CI files
[OK]    Requirement coverage: all 103 FR/NFR ids covered by features
[OK]    ruff format / ruff check / mypy
..................................                                       [100%]
34 passed in 0.05s
[OK]    prettier --check / eslint / vitest
[OK]    Environment ready. You can start working.
EXIT=0
```

From `backend/`, each gate individually:

```
$ uv run ruff format --check .   ->  19 files already formatted
$ uv run ruff check .            ->  All checks passed!
$ uv run mypy .                  ->  Success: no issues found in 19 source files
$ uv run pytest -q               ->  34 passed in 0.06s
```

**34 as expected, and the delta is explainable**: 30 + 1 (T43) + 3 (T44). The
file counts stay at 19 for both `ruff format` and `mypy` — correct, because
`SystemClock` went into an **existing** module and its test into an **existing**
test module. No new source file, no gate skipped, no count unaccounted for.

Runtime closures — **no dependency added**:

```
$ uv export --package planner-api --no-dev   ->  -e ./core  (via planner-api) + -e ./lambda_api
$ uv export --package planner-ai  --no-dev   ->  -e ./core  (via planner-ai)  + -e ./lambda_ai
```

`backend/core/pyproject.toml` still reads `dependencies = []`. `SystemClock`
imports only `UTC` and `datetime` from the standard library, so §1.2.2's central
claim — *"a default implementation by definition adds none"* — is confirmed on
the artifact, not on the argument.

---

## T7. New staleness introduced by this round

Beyond the five sites in §T2, which are the substantive instance:

**Informational, no action required:**

1. `progress/history.md:724` records *"the first `SystemClock` must not land
   before it"* — a constraint the `CHECKPOINTS.md` amendment explicitly retracted
   and which `SystemClock` has now violated by design. `history.md` is an
   append-only archive of closed sessions, and the live document
   (`CHECKPOINTS.md` lines 58-70) names and corrects that reasoning where the box
   is actually ticked. Archival, not misleading. A one-line *"Superseded
   2026-08-18 by `docs/architecture.md` §1.2.2"* pointer would be generous, not
   owed.
2. `progress/impl_week_calendar.md:4` still reads *"Tasks: T1-T40"*; there are now
   45. Same demarcation as round two — the header sits above an explicit
   *"everything above this line is unchanged"* boundary, and Addendum 2 §B3 states
   T42-T45 plainly. Carried forward unchanged from round two's R4.

**Checked and clean:**

- `progress/current.md` is accurate and current: it describes this round, lists
  T42-T45 with correct outcomes, records 30 -> 34, and its Next step correctly
  reads *"Feature 2 stays `in_progress`"*.
- Every factual claim in Addendum 2 was checked against its target. The three
  added guard tests, the four-test delta, the `19 files` counts, the export
  closures, the "nothing renumbered" claim and the R23 `SHALL` count all hold.
- `docs/conventions.md:120-125` (*Packaging conventions*) states the new rule
  accurately and cites §1.2.2. `docs/architecture.md:224-228` (the tree) and §3.1
  rule 3 both carry it. Those three edits are correct — it is the four siblings in
  §T2 that were missed.

---

## T8. Layering, boundaries and invariants

**Layering (`docs/architecture.md` §3.1)** — re-read every import under
`planner_core/`:

- `domain/` imports `application/`, `ports/`, an adapter, a handler or an AWS SDK:
  **no**. Unchanged; `SystemClock` is imported by nothing in `core`.
- `core` imports `boto3` / `planner_api` / `planner_ai`: **no**.
- `core` declares a runtime dependency: **no** — `dependencies = []`, confirmed by
  both `uv export` closures.
- `application/` imports an adapter or a handler: **no**.
- An adapter imported outside its Lambda's `wiring.py`: **n/a** — and §1.2.2's
  whole point is that `SystemClock` is **not** an adapter. Nothing in
  `planner_core` constructs one; selection stays `wiring.py`'s job.
- `planner_core` calls `datetime.now()`: **yes, once**, at `clock.py:43` —
  **permitted by `docs/architecture.md` §1.2.2** and by no other document. See
  §T2: rule 6 and three other sites still forbid it in writing.

**Invariants (`docs/architecture.md` §4)** — this round touches none. Invariant 7
(ISO weeks in `Europe/Madrid`, every user agrees) is exercised exactly as round
one §5 recorded; no existing test was modified and all 30 still pass.

**Boundaries:**

- No new `*.tf` / `*.tfvars` / `.github/workflows/**`: [x] — `git status` finds
  none; `init.sh` reports `[OK] No agent-generated IaC or CI files`.
- Frozen requirement docs unmodified: [x] — `git diff HEAD` over all five is
  empty.
- No architecture decision from §2 made silently: [x] — §1.2.2 is a **human**
  decision, dated, recorded in §1 (*Decided*), with its reasoning, its precedents
  and its reversal condition. It is not a P1-P7 item. The agents applied it; they
  did not make it.
- `feature_list.json` diff is still exactly two lines: [x] — feature 2
  `pending -> in_progress`, `FR-MENU-01` added to feature 20. **Feature 2 is not
  marked `done`.**
- No user-facing Spanish literal outside the messages module: [x] —
  `test_calendar_modules_contain_no_user_facing_text` covers `ports/clock.py` (it
  is in `FEATURE_MODULES`, line 43) and passes.
- Reviewer wrote no code and did not edit `requirements.md`: [x].

---

## T9. Checkpoints — round three

- **C1 — The harness is complete:** [x]
- **C2 — State is coherent:** [x] one `in_progress`; `progress/current.md` is
  accurate and describes this round.
- **C3 — The code respects the architecture:** [x] **under `docs/architecture.md`
  §1.2.2**, which is the authoritative text. Every box holds on the artifact. The
  box *"No `datetime.now()` inside `planner_core`"* (`CHECKPOINTS.md:33`) is
  ticked here **only because §1.2.2 supersedes its wording** — as written the box
  is now false and would force a rejection. Correcting it is required change 2; I
  am not editing `CHECKPOINTS.md` beyond this record.
- **C4 — Verification is real:** [x] with the one sub-box deliberately open.
  `ruff check` clean, `mypy` clean with no `# type: ignore`, 34 tests green, no
  AWS and no network. *"At least one test module per source module"* holds —
  `ports/clock.py` has `tests/ports/test_clock.py`. *"Every port has a contract
  suite"* stays unticked under the amended, dated deferral to feature 14; the
  amendment correctly removed the "must not land before it" clause and gave the
  real reason — two dependency-free implementations make a parametrized suite
  near-vacuous today.
- **C5 — The session closed properly:** [x] the final close-out is the human's.
- **C6 — Spec Driven Development:** [ ] — all 45 tasks ticked, every `FR-*` in
  `covers` reaches an `R<n>`, every `R<n>` reaches a concrete test, R23 is clean
  EARS with one `SHALL`. **But `docs/specs.md:73` — every requirement verifiable
  by a concrete test — does not hold for R2 as written** (§T1). This is the box
  the finding closes on.
- **C7 — Human-owned boundaries were respected:** [x]

---

## T10. Required changes

1. **Amend R2's text in `specs/week_calendar/requirements.md:63-65`** to name the
   single exception, with the exact wording in §T1. One `SHALL NOT`, no new
   `SHALL`, no renumbering, no fifth accepted deviation. A dated note beneath it —
   in R23's own pattern — would carry the *why*. **The human's decision; I did not
   edit the file.**
2. **Amend the four sibling absolutes in §T2** — `docs/architecture.md:277`
   (§3.1 rule 6) and `:407` (§6), `CHECKPOINTS.md:33` (C3), and
   `.claude/agents/reviewer.md:31` plus `.claude/agents/implementer.md:55-56`.
   Rule 6 is the urgent one: §1.2.2 cites it by number while contradicting it,
   inside the same document. `feature_list.json:66`, `requirements.md:231` and
   `docs/verification.md:89` are correct as written — do not touch them.

### Recommended, the human's call

3. Rename `test_planner_core_never_calls_an_ambient_clock`
   (`test_no_ambient_time.py:96`). Its docstring is precise — *"time enters
   `planner_core` through the `Clock` port or not at all"* — and remains true,
   since `SystemClock` **is** the port. The **name** is the part that asserts a
   universal the code no longer satisfies, and a test name is read far more often
   than its docstring. Something like
   `test_planner_core_calls_no_ambient_clock_outside_the_default_clock`. Not
   blocking: unlike R2, no rule requires a test name to be a specification.
4. Note the guard's `backend/core/tests/` scope (§T3 limitation 2) wherever
   feature 14's contract suite gets planned, so its author is not surprised that
   `SystemClock` is unguarded there.

---

## T11. What could not be verified

- **Deliberate obfuscation of the `SystemClock` import** is out of reach of any
  text scan (§T3, G17). Bounded and recorded, not fixable by a better regex.
- **Behaviour on a host with a system IANA database** — unchanged from round one;
  every check here ran on Windows with `zoneinfo.TZPATH` empty.
- **SonarQube** — pipeline-owned, not an agent's to invoke.

Feature 2 is left `in_progress`. **The human closes it.**

---
---

# Re-review — feature 2 (week_calendar), round four

**Verdict: CHANGES_REQUESTED**

Reviewer pass 4, 2026-08-19. Everything above this line is the round-one to
round-three record and is **unchanged**. This section supersedes round three's
verdict.

Nothing under `backend/`, `frontend/` or `specs/week_calendar/requirements.md`
was modified by this review. No git write command was run. The feature was
**not** marked `done`.

**Read this first: all six items from round three are genuinely closed.** R2 is
amended and correct, the four sibling absolutes are amended and correct, and the
`docs/verification.md:89` judgement call is right. Every gate is green at 34
tests, and `backend/` is byte-for-byte the round-three tree.

The verdict turns on **one clause added by this round's own fix**. The second
half of the amended `.claude/agents/reviewer.md` sentence states a new absolute
that shipped, approved code falsifies — the exact failure mode the round was
chartered to close, reintroduced inside the closing edit. It is a one-clause
change.

---

## Q1. The six items — verified independently, all six closed

Read from the files, not from the hand-off.

### 1. `specs/week_calendar/requirements.md:62-65` — **CLOSED, correct**

R2 now reads:

> The system SHALL NOT call `datetime.now`, `datetime.utcnow`, `date.today`,
> `time.time`, `time.localtime` or any other ambient-time function anywhere in
> the `planner_core` package, except the single `SystemClock.now` call in
> `planner_core/ports/clock.py` required by R23.

Checked against every constraint round three §T1 attached to the fix:

- **Exactly one `SHALL NOT`, zero `SHALL`.** Counted mechanically across all 23
  requirements, not by eye. The raw count reports R2 with two `SHALL NOT`
  occurrences; the second is the meta-mention *"Still one `SHALL NOT`"* inside
  the amendment note at line 76 — the same artefact the R4/R8/R16/R22 counts
  show. The normative sentence carries one. **No fifth accepted deviation**: the
  list at lines 18-20 still reads R4, R8, R16, R22 and was not touched.
- **It cites R23**, so the two stay linked in both directions.
- **It is not looser than the test.** R2 names `SystemClock.now` in one module;
  `test_no_ambient_time.py:38` `SANCTIONED_CALL` allows one full line matching
  `return datetime.now(UTC)` in `clock.py`, and
  `test_the_sanctioned_call_allowance_is_one_exact_line_in_one_exact_module`
  asserts `clock.py` holds exactly one such line (round three G4). Requirement
  and guard are the same width.
- **The rejected alternative was not taken.** Nothing broadens to
  `planner_core.ports`; the carve-out names one file and one method.
- The dated note carries the *why* and names the `AGENTS.md` §3.1 mechanism,
  which is the part worth more than the correction itself.

### 2. `docs/architecture.md:277-286` (§3.1 rule 6) — **CLOSED, correct**

Rule 6 now states the prohibition, then *"One sanctioned exception (§1.2.2,
added 2026-08-19)"*, names `SystemClock.now` in `planner_core/ports/clock.py` as
*"the single ambient-time call permitted in `core`"*, and adds the constraint
that *"nothing in `domain/` or `application/` may construct it — selecting a
`Clock` is `wiring.py`'s job"*. The self-contradiction round three called the
urgent one is gone: §1.2.2 cites rule 6 by number, and rule 6 now agrees with it.

### 3. `docs/architecture.md:414-416` (§6 *What NOT to do*) — **CLOSED, correct**

*"Do not call `datetime.now()` inside `core`. Inject a clock port. The lone
exception is `SystemClock.now` in `planner_core/ports/clock.py`, the port's
default implementation (§1.2.2, §3.1 rule 6) — do not add a second."* Narrow,
cross-referenced, and the *"do not add a second"* clause carries the width.

### 4. `CHECKPOINTS.md:33-36` (C3) — **CLOSED, correct and tickable**

*"No `datetime.now()` inside `planner_core`, except the one sanctioned
`SystemClock.now` call in `ports/clock.py` (`docs/architecture.md` §1.2.2, §3.1
rule 6). `backend/core/tests/test_no_ambient_time.py` checks this mechanically —
a green suite ticks the box."* This is better than the minimum asked: it names
the mechanical check, so the box has an objective tick condition rather than a
reviewer's reading. C3 is ticked below on that basis, not on round three's
"§1.2.2 supersedes the wording" workaround.

### 5. `.claude/agents/reviewer.md:31-36` — **first half CLOSED; second half is finding N1**

Lines 31-34 are correct and explicit: reject an ambient call *"anywhere other
than the one sanctioned `SystemClock.now` line in `ports/clock.py`"*, and *"That
single call … is permitted by `docs/architecture.md` §1.2.2 — **do not reject
it.**"* That is the trap round three named, defused.

Line 35 adds a **new** one. See §Q3.

### 6. `.claude/agents/implementer.md:55-59` — **CLOSED, correct**

*"It calls `datetime.now()` in exactly one sanctioned place — `SystemClock.now`
in `planner_core/ports/clock.py`, the `Clock` port's default implementation
(§1.2.2). Do not add a second, and do not construct a `SystemClock` inside
`domain/` or `application/`."* The construction prohibition is scoped to the two
layers that must not construct it, which is the correct scope and does **not**
catch `tests/ports/test_clock.py`. Note this for §Q3: `implementer.md` got the
same clause right, `reviewer.md` did not.

### `docs/verification.md:89` — **I agree it needed no change**

*"❌ Mocking `datetime.now()`. → inject a `Clock` port."* Read in its context
(lines 84-91, an anti-pattern list whose neighbour is *"`unittest.mock.patch` on
our own code → inject a fake through a port"*), the prohibited act is
`mock.patch`-ing the clock, and the prescribed remedy is the `Clock` port.
`SystemClock` **is** that port's implementation, injected through it — it is the
remedy, not the violation. The line would only need changing if it read *"do not
call `datetime.now()`"*, and it does not. **Leave it.**

---

## Q2. Mechanical sweep — the list was still incomplete

Run as `AGENTS.md` §3.1 prescribes, over `docs/`, `CHECKPOINTS.md`, `AGENTS.md`,
`CLAUDE.md`, `.claude/`, `specs/`, `progress/`, `feature_list.json` and
`init.sh`, on two independent patterns — the ambient-time function names and
`SystemClock` — rather than by re-reading anyone's list.

**Correct as written, confirmed, no change (round three's rulings hold):**

- `feature_list.json:66` — *"no domain code calls `datetime.now()`"*. Scoped to
  **domain**; `ports/clock.py` is not domain. Correct.
- `specs/week_calendar/requirements.md:247` — coverage-table row *"no
  `datetime.now()` in domain code"*. Same scoping. Correct.
- `docs/verification.md:89` — see Q1. Correct.
- `docs/conventions.md:119-125` — about **dependencies**, not ambient time, and
  it cites §1.2.2. Correct.
- `docs/architecture.md:229` (the tree annotation) and `:117`, `:138-145`
  (§1.2.2 body) — correct on the placement rule.
- `progress/history.md`, `progress/review_project_scaffold.md:49`,
  `progress/impl_week_calendar.md` — append-only archives of closed sessions.
  Archival, not live. No action.

**Checked and clean:** `AGENTS.md` and `CLAUDE.md` contain no statement of the
rule at all. `init.sh` contains none. `docs/specs.md` mentions `Clock` only in
its worked example.

**Not correct — three sites the previous three rounds all missed.** Each is the
same shape as R2: a universal stated in prose that shipped, sanctioned code
falsifies.

**N1 — `.claude/agents/reviewer.md:35`.** *"Do reject … any construction of
`SystemClock` outside `wiring.py`."* `backend/core/tests/ports/test_clock.py:32`
reads `clock = SystemClock()`. That construction is **required** by T43 and R23,
and `test_no_ambient_time.py:161` asserts that module *must* contain
`SystemClock` or the guard fails (round three G16). **Normative, and it
instructs the next reviewer to reject approved code.** Detailed in §Q3.

**N2 — `docs/architecture.md:146-148` (§1.2.2) and `:286` (§3.1 rule 6).**
*"asserts that no test module imports `SystemClock`"* and *"asserts no test
module reaches for `SystemClock`"*. The guard exempts two modules by name —
`test_no_ambient_time.py:154`, `exempt = {this_module, DEFAULT_CLOCK_TEST}` —
and its own docstring reads *"only the port's own test may touch `SystemClock`"*.
§1.2.2's answer to the central objection against putting a real clock in `core`
rests entirely on this control; describing it as total **overstates the
load-bearing claim of the architecture decision itself**.

**N3 — `specs/week_calendar/requirements.md:224`.** R23's note still says *"R2
stands unchanged, with one line of one module as its sanctioned exception."* R2
**was** changed, on 2026-08-19, twenty lines above in the same file. The
substance is right; the word *"unchanged"* was made false by this round's own
edit.

**Same class, lower weight — spec artefacts, the F4 annotate precedent applies:**

- `specs/week_calendar/design.md:296-300` (§6.1) — *"the following are banned in
  `planner_core` and in this feature's tests: `datetime.now()`, … — ambient clock
  (R2)"*.
- `specs/week_calendar/design.md:330` (§6.2) — *"A source scan asserts no
  ambient-time call exists in `planner_core` or in this feature's tests"*.
- `specs/week_calendar/design.md:601` — *"the new assertion that no test module
  names `SystemClock`"* — the N2 wording, in the spec.
- `specs/week_calendar/tasks.md:69-73` (T15) — *"assert none is present"*.
- `specs/week_calendar/requirements.md:231` — the N2 wording, in R23's note.

All five are corrected **within their own file** by a dated post-approval
addendum (`design.md` §11 lines 594-601, `tasks.md` T44 lines 195-203). That is
weaker than round three demanded of R2, but R2 was blocking for a reason that
does not transfer: `docs/specs.md:73` makes a *requirement* unverifiable if no
test proves its exact statement. No rule imposes that on design prose or on a
task description. Recommended, the human's call — one-line *Amended 2026-08-19*
annotations, not rewrites.

---

## Q3. N1 in full — the clause this round added

`.claude/agents/reviewer.md:31-36`, as it now stands:

> - Does `planner_core` call `datetime.now()` anywhere **other than** the one
>   sanctioned `SystemClock.now` line in `ports/clock.py`? → reject. That single
>   call is the port's default implementation and is permitted by
>   `docs/architecture.md` §1.2.2 — **do not reject it.** Do reject a second
>   ambient call anywhere in `core`, **or any construction of `SystemClock`
>   outside `wiring.py`.**

The bolded final clause is a universal. Its counter-example ships in the same
commit, is mandated by an approved requirement, and is asserted by the guard:

```python
# backend/core/tests/ports/test_clock.py:32
clock = SystemClock()
```

```python
# backend/core/tests/test_no_ambient_time.py:160-161
assert DEFAULT_CLOCK_TEST.is_file(), DEFAULT_CLOCK_TEST
assert SYSTEM_CLOCK.search(DEFAULT_CLOCK_TEST.read_text(encoding="utf-8")), DEFAULT_CLOCK_TEST
```

So the suite **fails** if `test_clock.py` stops constructing `SystemClock`, while
`reviewer.md` says to reject it for doing so. A reviewer following the definition
literally rejects a test the suite cannot pass without — which is, word for word,
what round three §T2 said about the sentence this clause replaced.

Three reasons this is not pedantry:

1. **It is normative and addressed to an agent**, which reads its definition
   literally by construction. Prose ambiguity a human would resolve charitably is
   not resolved charitably here.
2. **Round three explicitly refused the charitable reading** for R2 — *"Not
   ambiguous, not merely imprecise: the requirement states a universal, and a
   counter-example ships in the same distribution."* Applying a softer standard
   to the fix than to the defect would make the ruling arbitrary.
3. **`implementer.md` got it right in the same edit** — *"do not construct a
   `SystemClock` inside `domain/` or `application/`."* The correct scope is
   already written down, in the sibling file, from the same round. This is a
   slip, not a judgement call.

The fix is one clause. The sanctioned construction sites are
`tests/ports/test_clock.py` (present, required) and `wiring.py` (future). The
prohibition actually meant is on `domain/` and `application/` — exactly what
`implementer.md` says.

---

## Q4. Overcorrection — none found

The exception is still **exactly one line in one module** everywhere it is now
stated. Each amended wording, read for what it would *permit* rather than for
what it says:

| Site | Width it grants |
|---|---|
| `requirements.md:62-65` | one named method, one named file |
| `architecture.md:280-286` | *"the single ambient-time call permitted in `core`"*, plus a construction ban on `domain/` + `application/` |
| `architecture.md:414-416` | *"the lone exception … do not add a second"* |
| `CHECKPOINTS.md:33-36` | *"the one sanctioned … call"*, tick condition delegated to the mechanical guard |
| `reviewer.md:31-34` | *"the one sanctioned … line"*, plus *"reject a second ambient call anywhere in `core`"* |
| `implementer.md:56-59` | *"exactly one sanctioned place … do not add a second"* |

No wording says *"in `ports/`"*, *"in a default implementation"*, or anything
else category-shaped that a future module could claim. The rejected alternative
from round three §T1 — broadening the carve-out to `planner_core.ports` — was
not taken anywhere. Every site names the file.

One adjacent line deserves an explicit verdict, since it is the only plausible
widening vector: `docs/conventions.md:119-125` says a port's dependency-free
default implementation *"lives in `planner_core/ports/` … and is not a smell"*.
That licenses a future default implementation to sit in `ports/`, but it says
nothing about ambient time, and §3.1 rule 6 independently caps ambient time at
one call in `core`. **Not a widening.** No change.

Two of this round's edits are in fact *narrower* than they had to be, and both
are improvements: rule 6 and `implementer.md` each added the
"nothing in `domain/` or `application/` may construct it" clause, which no
round-three finding asked for and which closes the obvious next leak.

---

## Q5. Gates re-run — actual output

`./init.sh` from the repo root — **exit 0**:

```
── 4. feature_list.json, specs and guardrails ──────────
[OK]    feature_list.json valid (23 features - blocked: 9, done: 1, in_progress: 1, pending: 12)
[OK]    Specs present for every non-pending sdd feature
[OK]    No agent-generated IaC or CI files
[OK]    Requirement coverage: all 103 FR/NFR ids covered by features
[OK]    Next actionable feature: 3 - text_and_units

── 5. Quality gates ────────────────────────────────────
[OK]    ruff format
[OK]    ruff check
[OK]    mypy
..................................                                       [100%]
34 passed in 0.05s
[OK]    pytest (unit + contract, no AWS)
[OK]    prettier --check
[OK]    eslint
[OK]    vitest

── 6. Summary ──────────────────────────────────────────
[OK]    Environment ready. You can start working.
EXIT=0
```

From `backend/`, each gate individually:

```
$ uv run ruff format --check .   ->  19 files already formatted
$ uv run ruff check .            ->  All checks passed!
$ uv run mypy .                  ->  Success: no issues found in 19 source files
$ uv run pytest -q               ->  34 passed in 0.06s
```

**34 as expected**, and the three counts that make the green explainable are
identical to round three: 34 tests, 19 files in `ruff format`, 19 in `mypy`. No
gate skipped, nothing unaccounted for.

---

## Q6. `backend/` unchanged — verified three ways

1. **No `.py` under `backend/core` has an mtime on or after 2026-08-19.**
   `find backend/core -name "*.py" -newermt "2026-08-19 00:00"` returns nothing.
2. **The tracked diff is identical to round three.** `git diff HEAD --stat --
   backend/ frontend/` reports `backend/core/tests/support/.gitkeep` (deleted),
   `backend/pyproject.toml` (+4, the `tzdata` dev entry) and `backend/uv.lock`
   (+10). The untracked set is the same twelve paths.
3. **The gate counts are unchanged** — 34 / 19 / 19, see Q5.

The files with a 2026-08-19 mtime are exactly `docs/architecture.md`,
`CHECKPOINTS.md`, `.claude/agents/implementer.md`, `.claude/agents/reviewer.md`
and `specs/week_calendar/requirements.md` (plus this review). **A
docs-and-agent-definitions round only, as stated.**

---

## Q7. Traceability, tasks and boundaries — re-confirmed, no regression

- **FR → R**: all five ids in feature 2's `covers` still reach an `R<n>`; the
  coverage map at lines 236-241 is unchanged and correct. No orphan `R<n>`.
- **R → test**: unchanged from round three §T5. No test module was modified this
  round (Q6), so every mapping still holds — R2's included, and R2's is now
  *stronger*: `test_planner_core_never_calls_an_ambient_clock` proves exactly
  what R2 states rather than something weaker, which is what closes the
  round-three defect.
- **Tasks**: 45 `[x]`, 0 `[ ]`, counted mechanically. No renumbering.
- **Layering**: unchanged; round three §T8 stands. The one `datetime.now()` in
  `planner_core` is `clock.py:43`, now permitted by `architecture.md` §1.2.2,
  §3.1 rule 6 and §6, by `CHECKPOINTS.md` C3 and by R2 — **all five in
  agreement**, which was the whole point of the round.
- **Invariants**: this round touches none. Invariant 7 is exercised exactly as
  round one §5 recorded.
- No new `*.tf` / `*.tfvars` / `.github/workflows/**`: [x] — `git status` finds
  none; `init.sh` reports `[OK] No agent-generated IaC or CI files`.
- Frozen requirement docs unmodified: [x] — `git diff HEAD` over all five is
  empty.
- `feature_list.json` diff is still exactly two lines: [x] — feature 2
  `pending -> in_progress`, `FR-MENU-01` added to feature 20. **Feature 2 is not
  marked `done`.**
- No architecture decision from §2 made silently: [x] — §1.2.2 remains the
  human's dated decision; this round only propagated its wording.
- Reviewer wrote no code, and edited neither `requirements.md`, `backend/` nor
  `frontend/`: [x].
- **F5** (EARS: R4/R8/R16/R22 carry two `SHALL`s) — **still open by the human's
  choice, not re-opened.** The mechanical count above confirms R2 did **not**
  join them. **F7** (`ruff` isort groups `support` as third-party) — **still
  open, untouched.** Status noted only.

---

## Q8. Checkpoints — round four

- **C1 — The harness is complete:** [x]
- **C2 — State is coherent:** [x] one `in_progress`; nine `blocked`, each with a
  reason; `progress/current.md` accurate.
- **C3 — The code respects the architecture:** [x] — and for the first time **on
  the box's own wording**, not by invoking §1.2.2 over it. `CHECKPOINTS.md:33`
  now names the exception and delegates the tick to `test_no_ambient_time.py`,
  which is green.
- **C4 — Verification is real:** [x] with the one sub-box deliberately open.
  `ruff check` clean, `mypy` clean with no `# type: ignore`, 34 green, no AWS, no
  network. *"Every port has a contract suite"* stays unticked under the amended,
  dated, owner-assigned deferral to feature 14.
- **C5 — The session closed properly:** [x] the final close-out is the human's.
- **C6 — Spec Driven Development:** [x] — **round three's rejection is closed.**
  All 45 tasks ticked; every `FR-*` in `covers` reaches an `R<n>`; every `R<n>`
  reaches a concrete test; and `docs/specs.md:73` now **holds for R2**, because
  its text and `SANCTIONED_CALL` describe the same set.
- **C7 — Human-owned boundaries were respected:** [x]

No checkpoint is red. **N1 is not a checkpoint failure** — it is a defect in the
reviewer's own operating instructions, which no checkpoint covers. It blocks
because an agent definition that mandates rejecting approved code will be obeyed.

---

## Q9. Required changes

1. **Fix `.claude/agents/reviewer.md:35` (N1).** Replace *"or any construction of
   `SystemClock` outside `wiring.py`"* with the scope `implementer.md:58` already
   uses correctly — construction inside `domain/` or `application/`. The
   sanctioned construction sites are `backend/core/tests/ports/test_clock.py`
   (present, required by T43/R23 and asserted by the guard at
   `test_no_ambient_time.py:161`) and `wiring.py` (future). As written, the clause
   tells the next reviewer to reject a test the suite cannot pass without.
2. **Correct the two `docs/architecture.md` statements of the guard's scope
   (N2)** — `:146-148` in §1.2.2 and `:286` in §3.1 rule 6. Both say the scan
   asserts *no* test module reaches for `SystemClock`; it exempts
   `tests/ports/test_clock.py` and the guard module itself
   (`test_no_ambient_time.py:154`). Naming the exemption **strengthens** §1.2.2's
   argument rather than weakening it: the exemption is asserted non-hollow — the
   exempt module *must* contain `SystemClock`, line 161 — which is precisely the
   property a directory boundary cannot offer. Round three's reasoning for rule 6
   applies unchanged: the document must not state an absolute its own control
   does not enforce.

### Recommended, the human's call

3. **`specs/week_calendar/requirements.md:224` (N3)** — *"R2 stands unchanged"*
   was made false by the amendment twenty lines above. One clause, e.g. *"R2 now
   states this exception directly (amended 2026-08-19)"*.
4. **Annotate the five spec-artefact absolutes** in the F4 pattern rather than by
   rewriting: `design.md:296-300`, `:330`, `:601`, `tasks.md:69-73` (T15) and
   `requirements.md:231`. Each is already corrected by a dated addendum in its
   own file; a one-line forward pointer at the absolute would stop a reader of
   §6.1 concluding the ban is total.
5. Round three's recommendations 3 (rename
   `test_planner_core_never_calls_an_ambient_clock`) and 4 (record the guard's
   `backend/core/tests/` scope wherever feature 14's contract suite is planned)
   remain **open and unactioned**. Still non-blocking. Recommendation 3 is weaker
   now than when it was written: the name and R2 diverged for the same reason,
   and the human chose to fix the text rather than the name — a defensible call,
   since no rule makes a test name a specification.

---

## Q10. What could not be verified

- **Deliberate obfuscation of the `SystemClock` import** — round three G17. Out
  of reach of any text scan. Bounded and recorded, not fixable by a better regex.
- **Behaviour on a host with a system IANA database** — unchanged from round one;
  every check here ran on Windows with `zoneinfo.TZPATH` empty.
- **SonarQube** — pipeline-owned, not an agent's to invoke.

Feature 2 is left `in_progress`. **The human closes it.**

---
---

# Re-review — feature 2 (week_calendar), round five

**Verdict: APPROVED**

Reviewer pass 5, 2026-08-19. Everything above this line is the round-one to
round-four record and is **unchanged**. This section supersedes round four's
verdict.

Nothing under `backend/`, `frontend/` or `specs/week_calendar/requirements.md`
was modified by this review. The single mutation in §P3 ran against a
**scratchpad copy**, never the repository. No git write command was run. The
feature was **not** marked `done`.

**Read this first: N1, N2, N3 and all five spec artefacts are genuinely closed,
and the pointer-not-paraphrase strategy is the right call.** One factual
over-claim survives in `docs/architecture.md` §3.1 rule 6 (§P3). It is a single
clause, it blocks nothing, and I am **not** rejecting on it. **This work has
converged — my recommendation is to stop the doc-consistency cycle here.**

---

## P1. The three findings and the five artefacts — verified from the files

### N1 — `.claude/agents/reviewer.md:31-42` — **CLOSED**

The clause *"or any construction of `SystemClock` outside `wiring.py`"* is gone.
The bullet no longer enumerates anything: it names
`backend/core/tests/test_no_ambient_time.py` as **the authority**, says not to
reject on ambient-time or `SystemClock`-placement grounds while it passes, and
lists the four ways the guard itself could be weakened (exemption widened,
allowance loosened, self-check deleted, ambient call added outside what it
permits). Those four map one-for-one onto real assertions in the module —
`exempt` at line 155 and the `is_file()` / `SYSTEM_CLOCK.search` pair at 160-161,
`SANCTIONED_CALL` at 38 with the four adjacent near-misses at 87-93, the two
pattern self-checks, and `_offenders()` at 50-59. **The pointer is actionable,
not vague**: a reviewer diffing the guard has a concrete checklist, and it cannot
go stale because it describes the guard's *structure*, not its contents. The
parenthetical recording why it is a pointer is the part that stops round six
re-introducing a paraphrase.

### N2 — `docs/architecture.md:146-155` and `:284-294` — **CLOSED**

The wording *"asserts that no test module imports `SystemClock`"* is gone from
both sites. §1.2.2 now says the guard is **the authority** on both the sanctioned
ambient-time call and which modules may reach for `SystemClock`, followed by an
explicit *"Deliberately not restated here … **Read the module.**"* Rule 6 carries
the same sentence at 292-294. The self-contradiction and the overstatement are
both gone.

### N3 — `specs/week_calendar/requirements.md:227-234` — **CLOSED**

R23's note now records that **R2 was amended on 2026-08-19**, states in a
parenthesis that the paragraph originally read *"R2 stands unchanged"* and that
the amendment made it false, and defers the exemptions to the guard rather than
restating them. R2 itself (62-66, with its 68-81 note) is untouched from round
four and still correct.

### The five spec artefacts — **all annotated, none rewritten**

- `design.md:299-302` (§6.1) — dated block above the banned list: one line in
  `ports/clock.py` is sanctioned, everything else below stands, guard is the
  authority.
- `design.md:338-339` (§6.2) — *"Amended 2026-08-19: R23 added one sanctioned
  call — see §11. The scan is the authority on which."*
- `design.md:609-613` (§11) — the *"no test module names `SystemClock`"*
  sentence now carries its correction inline and says the exemptions are
  deliberately not restated.
- `tasks.md:74-76` (T15) — *"None is present"* is marked as describing T15 as
  originally written, not the module's behaviour today.
- `requirements.md:227-234` — same as N3.

Each is one dated line or block; the arguments beneath are untouched. That is the
F4 precedent applied correctly.

### The two judged-correct non-changes — **I agree with both**

- **`tasks.md:198-208` (T44)** — agreed, a false positive of a line-based grep.
  Lines 202-204 state the exclusion *in the same sentence* as the absolute:
  *"excluding `tests/ports/test_clock.py` and the guard module itself, with the
  exemption asserted to actually use it"*. It is more accurate than the guard's
  own docstring. Editing it would have made it worse.
- **`docs/verification.md:89`** — agreed, unchanged from round four's ruling. It
  prohibits `mock.patch`-ing the clock, and `SystemClock` is the prescribed
  remedy, not the violation.

---

## P2. The strategy, judged on its merits — sound, and no gap was opened

The question the brief poses is the right one: did removing paraphrases leave a
rule with **no** authoritative statement anywhere? I checked every rule the
deleted prose used to carry. The answer is **no** for all of them.

| Rule formerly paraphrased | Where it is authoritatively stated now |
|---|---|
| Ambient time is banned in `core` | `requirements.md` R2 (normative and tested); `architecture.md` §3.1 rule 6, first sentence; `CHECKPOINTS.md:33-36` |
| The one exception, `SystemClock.now` in `ports/clock.py` | R2, §1.2.2, rule 6, §6 lines 422-424, `CHECKPOINTS.md:33-36`, `implementer.md:56-58` — six sites, every one naming the single file |
| Which exact call is allowed | `test_no_ambient_time.py:38` and the test at 78-93 — the only place, by design |
| Which test modules may name `SystemClock` | `test_no_ambient_time.py:155,160-161` — the only place, by design |
| Nothing in `domain/` or `application/` constructs one | `architecture.md` §3.1 rule 6; `implementer.md:58-59`; `design.md:600-603` |

The last row matters: that is the rule the deleted `reviewer.md` clause mangled,
and it **survives in prose** in three places, correctly scoped. Removing the
paraphrase did not orphan it. Nothing became unstated; two things became
unrestated, which is exactly the intent.

`reviewer.md` still gives a reviewer enough to act on — see §P1, N1. It is
strictly more actionable than what it replaced, because "reject if the guard was
weakened" is checkable against a diff, whereas "reject `datetime.now()` in
`planner_core`" required the reviewer to already know the exception before
reading the line.

---

## P3. The one thing this round did not close — minor, **not blocking**

`docs/architecture.md:289-292` (§3.1 rule 6) claims a mechanical enforcement that
does not exist:

> Nothing in `domain/` or `application/` may construct it — selecting a `Clock`
> is `wiring.py`'s job — and `backend/core/tests/test_no_ambient_time.py`
> **enforces both halves mechanically**.

The natural referents of *both halves* are the sanctioned-call permission and the
construction ban. The guard enforces the first. It does **not** enforce the
second: `SYSTEM_CLOCK` is applied only under `TESTS_ROOT`
(`test_no_ambient_time.py:146-169`), never to `CORE_SRC`, and `AMBIENT_TIME` does
not match `SystemClock()`.

Verified, not reasoned. `backend/core/src` and `backend/core/tests` were copied
to the scratchpad; in the **copy**, `application/live_weeks.py` gained
`from planner_core.ports.clock import Clock, SystemClock` and a module-level
`DEFAULT_CLOCK = SystemClock()`. Running the copy's suite against the copy's
sources:

```
PYTHONPATH=[copy]/src uv run pytest [copy]/tests -q
..................................  [100%]
34 passed in 0.22s
```

An `application/`-layer construction of the real clock — the exact thing rule 6
forbids in the sentence that claims mechanical enforcement — passes the whole
suite. The repository was not touched; only the copy was mutated.

**Why this is minor and why I am not rejecting on it:**

1. **No code violates the rule.** `SystemClock` is named in exactly three files
   (`ports/clock.py:24`, `tests/ports/test_clock.py:9,32`, and the guard);
   nothing in `planner_core` constructs one.
2. **It is not normative against an agent.** Unlike N1, it instructs nobody to
   reject correct code. Its worst effect is a reader over-trusting a control.
3. **The rule itself is stated correctly in three places** (§P2, last row), and
   `implementer.md:58-59` — the file governing the agent who could actually
   introduce the violation — states it with no enforcement claim attached.
4. **Round four inspected rule 6 and passed it** (§Q1.2, §Q4). The clause is not
   fresh churn from this round, whose edits reworked the *tail* of rule 6.

The fix, if the human wants one, is two words: *"enforces both halves
mechanically"* becomes *"enforces the ambient-time half mechanically; the
construction ban is a review rule"*. **My recommendation is to leave it**, or to
fold it into whatever next touches that file. It is not worth a round six. The
alternative worth doing one day is extending the guard to scan `CORE_SRC` for
`SystemClock` outside `ports/clock.py` — four lines that would make the sentence
true rather than make the sentence smaller. That belongs to whichever feature
first writes a `wiring.py`, not here.

---

## P4. Mechanical sweep — clean apart from §P3

Two patterns (the ambient-time function names, and `SystemClock`) over `docs/`,
`CHECKPOINTS.md`, `AGENTS.md`, `CLAUDE.md`, `.claude/`, `specs/`,
`feature_list.json` and `init.sh`. Every hit judged, not assumed:

- `CHECKPOINTS.md:33-36` — *"checks **this** mechanically"*, where *this* is the
  `datetime.now()` box. **True**: the guard checks exactly that. Correct.
- `implementer.md:56-59` — correct scope, no enforcement claim. Correct.
- `architecture.md:146-155` (§1.2.2), `:236` (the tree), `:422-424` (§6) —
  correct.
- `requirements.md:63-81` (R2), `:210-234` (R23), `:250` (coverage row) and
  `feature_list.json:66` — correct; the last two are scoped to *domain*.
- `design.md:86,107,299-305,333-339,575-613` and `tasks.md:69-79,181-212` —
  correct after this round's annotations.
- `conventions.md:119-125` — about dependencies, not ambient time. Correct.
- `verification.md:89` — about mocking. Correct.
- `AGENTS.md`, `CLAUDE.md`, `init.sh` — no statement of the rule at all.
- `progress/history.md`, `progress/impl_week_calendar.md`,
  `progress/review_project_scaffold.md` — append-only archives of closed
  sessions. No action, as in rounds three and four.

**Nothing new was introduced this round** beyond the §P3 clause, and every claim
the new annotations make was checked against its target file.

---

## P5. Gates re-run — actual output

`./init.sh` from the repo root — **exit 0**:

```
[OK]    feature_list.json valid (23 features - blocked: 9, done: 1, in_progress: 1, pending: 12)
[OK]    Specs present for every non-pending sdd feature
[OK]    No agent-generated IaC or CI files
[OK]    Requirement coverage: all 103 FR/NFR ids covered by features
[OK]    ruff format / ruff check / mypy
..................................                                       [100%]
34 passed in 0.06s
[OK]    prettier --check / eslint / vitest
[OK]    Environment ready. You can start working.
EXIT=0
```

From `backend/`, each gate individually:

```
uv run ruff format --check .   ->  19 files already formatted
uv run ruff check .            ->  All checks passed!
uv run mypy .                  ->  Success: no issues found in 19 source files
uv run pytest -q               ->  34 passed in 0.05s
```

**34 / 19 / 19 — identical to rounds three and four.**

**`backend/` unchanged this round, verified two ways.**
`find backend -name "*.py" -newermt "2026-08-19 00:00"` returns nothing, and
`git diff HEAD --stat -- backend/ frontend/` is still the same three entries
(`tests/support/.gitkeep` deleted, `pyproject.toml` +4, `uv.lock` +10) with the
same untracked set. The files touched after round four's write are exactly
`docs/architecture.md`, `.claude/agents/reviewer.md` and
`specs/week_calendar/{requirements,design,tasks}.md`. **A docs-and-spec-prose
round only, as stated.**

---

## P6. Traceability, tasks, invariants, boundaries — re-confirmed

- **FR to R**: `FR-MENU-01` to R10-R14; `FR-MENU-02` to R1-R9 and R20-R23;
  `FR-UX-06` to R14-R16; `FR-AI-11` and `FR-SHOP-05` to R1, R2, R4, R5, R17-R20,
  R22, R23. All five covered; no orphan among the 23 requirements.
- **R to test**: unchanged — no test module was modified (§P5). R2's mapping
  remains the strong one from round four:
  `test_planner_core_never_calls_an_ambient_clock` plus
  `test_the_sanctioned_call_allowance_is_one_exact_line_in_one_exact_module`
  prove exactly what R2 states.
- **Tasks**: counted mechanically — **45 `[x]`, 0 `[ ]`**. No renumbering.
- **Layering**: unchanged. The one `datetime.now()` in `planner_core`
  (`ports/clock.py:43`) is permitted by R2, §1.2.2, rule 6, §6 and
  `CHECKPOINTS.md` C3 — all in agreement. `domain/` imports no `ports/`; `core`
  declares `dependencies = []`; no adapter exists.
- **Invariants**: this round touches none. Invariant 7 is exercised exactly as
  round one §5 recorded.
- **Boundaries**: no `*.tf` / `*.tfvars` / `.github/workflows/**` (`init.sh`
  agrees); frozen docs unmodified (`git diff HEAD` empty over all five);
  `feature_list.json` diff still exactly two lines and feature 2 **not** `done`;
  no §2 architecture decision made silently; the reviewer wrote no code and
  edited neither `requirements.md` nor `backend/`.
- **F5** (R4/R8/R16/R22 carry two `SHALL`s) and **F7** (`ruff` isort grouping of
  `support`) remain open by the human's choice. Round three's recommendations 3
  (test rename) and 4 (record the guard's `backend/core/tests/` scope for feature
  14) remain unactioned and non-blocking.

---

## P7. Checkpoints — round five

- **C1 — The harness is complete:** [x]
- **C2 — State is coherent:** [x] one `in_progress`; nine `blocked`, each with a
  reason; `progress/current.md` accurate.
- **C3 — The code respects the architecture:** [x] on the box's own wording;
  `test_no_ambient_time.py` is green, which is the tick condition the box names.
- **C4 — Verification is real:** [x] with *"every port has a contract suite"*
  deliberately open under the dated, owner-assigned deferral to feature 14.
- **C5 — The session closed properly:** [x] the final close-out is the human's.
- **C6 — Spec Driven Development:** [x] 45/45 tasks ticked; every `FR-*` reaches
  an `R<n>`; every `R<n>` reaches a concrete test; `docs/specs.md:73` holds for
  R2.
- **C7 — Human-owned boundaries were respected:** [x]

---

## P8. Has this converged? — yes

Plainly: **yes, and it should stop here.**

- Round three found a *requirement* falsified by shipped code. Blocking, and
  correctly so: `docs/specs.md:73` made R2 unverifiable.
- Round four found a *normative agent instruction* to reject code the suite
  cannot pass without. Blocking, and correctly so.
- Round five finds **one adjectival over-claim in one sentence of one document**,
  which no code violates, which instructs nobody to do anything wrong, and which
  round four already saw and passed.

That is a converging series, not churn. The reason it converged is the change of
strategy: rounds three and four fixed prose by writing prose, and each
restatement was a new claim needing its own verification. This round deleted the
restatements and pointed at the mechanical check instead. **The strategy is
correct and should be the standing pattern** — note that the §P3 residue is
itself a leftover *paraphrase of enforcement*, the last surviving instance of the
pattern this round removed everywhere else.

The implementation has been green and correct since round two. No further
documentation round is warranted. **Required changes: none.**

---

## P9. What could not be verified

- **Deliberate obfuscation of the `SystemClock` import** — round three G17,
  unchanged. Out of reach of any text scan.
- **Behaviour on a host with a system IANA database** — every check here ran on
  Windows with `zoneinfo.TZPATH` empty.
- **SonarQube** — pipeline-owned, not an agent's to invoke.
- **Which round introduced the §P3 clause.** All doc edits are uncommitted, so no
  per-round diff exists. Round four's quotations of rule 6 suggest the clause
  predates this round, but that could not be proved from the artifacts, and the
  verdict does not depend on it.

Feature 2 is left `in_progress`. **The human closes it.**

---
---

# Re-review — feature 2 (week_calendar), round six

**Verdict: APPROVED**

Reviewer pass 6, 2026-08-19. Everything above this line is the round-one to
round-five record and is **unchanged**. This section supersedes round five's
verdict and closes **P3**.

Nothing under `backend/`, `frontend/`, `specs/` or `docs/` was modified by this
review. The ten mutations in §S2 ran against **scratchpad copies**, never the
repository; the copies were deleted afterwards and all eight `planner_core`
sources checksum identically to Addendum 3's table (§S5). No git write command
was run. The feature was **not** marked `done`.

**Read this first: P3 is closed, and closed the better way.** The guard now
enforces the half it did not. I reproduced my own round-five mutation against it
and it fails; I attacked the new scan nine further ways and it held or failed
closed every time. `./init.sh` is green at 35. **Nothing remains that blocks
marking feature 2 `done`.**

---

## S1. The judgement the human asked for — the override was right, and my recommendation was the weaker call

Plainly: **the human was right, and I was wrong about the remedy.**

I was not wrong about the *severity*. P3 was minor, non-blocking, and round five
was correctly an APPROVAL — no code violated the rule, the clause instructed
nobody to do anything wrong, and I would classify it the same way again. That
part stands.

I was wrong about the **fix**, for three reasons I can now state with evidence:

1. **I mis-framed it.** I called it "a documentation over-claim". The more
   accurate framing is *an enforcement gap in the control that an architecture
   decision names as its answer to the central objection against it*. §1.2.2
   lines 143-149 do not merely mention the guard — they trade a directory
   boundary for it: *"a directory boundary only works until someone types the
   import"*. My own mutation was someone typing the import, into
   `application/`, and the mechanical control that replaced the boundary did not
   see it. Under my recommended fix, §1.2.2's justification would have kept
   resting on a control with a hole in exactly the layer the boundary used to
   protect. That is a materially different thing from a stale adjective, and I
   filed it as the latter.

2. **The doc fix loses to the test fix on the project's own converged strategy.**
   Round five's §P8 concluded that the reason the cycle converged was
   *pointer-not-paraphrase*: stop restating rules in prose, point at the
   mechanical check. My recommended wording — *"enforces the ambient-time half
   mechanically; the construction ban is a review rule"* — is a **new
   paraphrase of enforcement**, the exact species round five had just finished
   deleting from five other sites. It would have needed re-verification the day
   anyone touched the guard. What shipped instead deleted the gap rather than
   the claim, and left nothing new to go stale. I noted this myself in §P3
   (*"make the sentence true rather than make the sentence smaller"*) and then
   recommended the smaller sentence anyway.

3. **My deferral had no owner and no trigger.** §P3 said the guard extension
   *"belongs to whichever feature first writes a `wiring.py`, not here"*. That
   feature is unidentified in `feature_list.json`, and unlike the C4
   contract-suite deferral it would have carried no dated owner and no
   acceptance criterion to attach to — an unenforced note in a review file. The
   cost of doing it now was one test function, one shared helper, zero
   production lines and one round. The cost of deferring it was a second
   scheduled-debt item weaker than the one the project already has.

**Was it worth a round?** Yes — and the honest measure is what the round bought:
a false claim in an architecture document became true, an approved decision's
stated basis became real, and the test count went 34 to 35 with no production
change. Judged against rounds three and four, which each spent a round making
prose agree with prose, this is the cheapest round of the six and the only one
that added enforcement rather than wording.

Two things I will not soften, since the brief asked for honesty and not
agreement:

- **Stopping after round five would not have been negligent.** Nothing was
  broken, nothing was blocked, and a reviewer who stopped there would not have
  approved a defect. The override was a judgement call between two defensible
  options, not a rescue.
- **The human picked the better of the two**, and the reason is structural, not
  taste: one option removes a hazard permanently, the other renames it.

---

## S2. The guard, attacked — ten mutations, my own P3 case first

Method: `backend/core/{src,tests}` copied to the session scratchpad; each
mutation applied to a **fresh copy**; run from `backend/` as
`PYTHONPATH=<copy>/src uv run pytest <copy>/tests -q`. The repository was never
mutated — `CORE_SRC` is derived from `TESTS_ROOT.parent`, so the copy's tests
scan the copy's sources, which is what makes this exercise meaningful. Copies
deleted afterwards; §S5 proves the repository is byte-identical.

Baseline on the untouched copy: **35 passed**.

### The round-five mutation, reproduced against the new guard

`application/live_weeks.py` in the copy gained
`from planner_core.ports.clock import SystemClock` and a module-level
`DEFAULT_CLOCK = SystemClock()` — the exact §P3 mutation.

```
FAILED test_no_ambient_time.py::test_no_core_module_but_the_port_names_the_real_clock
E   AssertionError: assert ['...live_weeks.py:65: from planner_core.ports.clock import SystemClock', ...] == []
1 failed, 34 passed
```

**Exactly one test fails, and it is the new one.** In round five this same
mutation passed the whole suite at 34. The failure names the file, the line
number and the offending text. Independently reproduced, not accepted from the
hand-off — and the "exactly one" is itself the evidence that T46 is the only
thing standing between the repository and that violation.

### Can the ban be evaded?

| # | Mutation | Result |
|---|---|---|
| A1 | Aliased import in `domain/` — `from planner_core.ports.clock import SystemClock as _RealClock` | **1 failed** — the alias does not hide the name |
| A2 | Re-export through `ports/__init__.py` — `from planner_core.ports.clock import SystemClock` plus `__all__` | **1 failed** — `ports/__init__.py` is itself scanned, so the second import path is closed at its source |
| A10 | Named only in a `domain/` docstring, never constructed | **1 failed** — deliberate, and the test's docstring says so |
| A3 | `getattr(_cm, "System" + "Clock")()` in `application/` | **35 passed** — evades, see §S3 |

A2 is the one the brief asked about specifically. There is no re-export hole:
`planner_core/ports/__init__.py` is inside `CORE_SRC.rglob("*.py")` and is not
the exempt path, so creating the alias trips the guard before anyone can use it.

### Does it fail closed?

| # | Mutation | Result |
|---|---|---|
| A4 | `ports/clock.py` deleted | **suite red.** Run against the guard module alone, the new test fails on `assert DEFAULT_CLOCK_SOURCE.is_file()` (line 206) **before** the `read_text` at line 210 — an assertion, not a crash |
| A5 | Exempt module stops **declaring** — `class HostClock` plus `SystemClock = HostClock` | **1 failed** — the `line.startswith("class SystemClock")` assertion fires. An alias is not a declaration |
| A6 | Declaration moved to a new `ports/system_clock.py`, `clock.py` re-imports it | **3 failed** — the new test, the allowance test and the ambient scan. Relocating the class cannot relocate the exemption |
| A7 | `application/live_weeks.py` renamed away | **failed** — the `in sources` assertion on the named file fires |
| A8 | Every core `.py` deleted but `clock.py`, so the scanned set is empty | **failed** — `assert sources` fires with *"no planner_core sources found"* |
| A9 | Exemption repointed: `DEFAULT_CLOCK_SOURCE` changed to `domain/calendar.py` | **3 failed** |

A9 is the strongest structural property and it is worth naming, because it was
not designed for — it falls out of the reuse. `DEFAULT_CLOCK_SOURCE` is a
**single constant shared by both scans**: the ambient-time allowance and the
`SystemClock` exemption point at the same path. Moving the exemption to shelter a
different module therefore breaks the allowance test as well, and moving it to a
module that has no `return datetime.now(UTC)` line breaks it twice over. **The
exemption cannot be repointed quietly; it can only be repointed loudly.**
Combined with A5 (the exempt module must *declare* the class, not merely mention
or alias it) and A4 (it must exist), the one hole in the scan is pinned from
three directions.

**Can the exemption widen?** Only by editing `test_no_ambient_time.py` itself —
adding a second path, or turning `!= DEFAULT_CLOCK_SOURCE` into a set membership.
That is a visible diff to the guard, and it is precisely case one of the four
weakening modes `.claude/agents/reviewer.md` already tells the next reviewer to
reject. **The pointer written in round five covers the control added in round six
without amendment** — the pointer strategy earning its keep one round after it
was adopted.

---

## S3. Two bounded limitations — recorded, unchanged in kind, no action

1. **String-concatenated `getattr` evades the source scan too** (A3). This is
   round three's G17, which was proved on the *test* side; it holds identically
   on the *source* side, for the same reason — no text scan beats
   `"System" + "Clock"`. It is unchanged in kind and adds no new exposure: the
   failure mode the guard defends against is someone **typing the import**, and
   A1, A2 and the P3 case prove that is caught. There is no accidental form of
   A3. Recorded on the same footing as the ASCII limitation of round one.
2. **The scan is wider than rule 6's prose, in the safe direction.** Rule 6 says
   *"nothing in `domain/` or `application/` may construct it"*; the guard bans
   **naming** it **anywhere under `planner_core` except `ports/clock.py`**. A
   superset, deliberately (T46 says so). The one consequence worth knowing: a
   future second port shipping its own default implementation could not
   reference `SystemClock` from its module without a visible guard edit. That is
   correct behaviour today — nothing should reference it — and the day it is
   wrong, the edit is exactly the kind a reviewer is instructed to inspect. **No
   action.**

Neither is a finding. Both are noted so a later feature does not rediscover them
as surprises.

---

## S4. Rule 6's sentence — accurate now, in full

`docs/architecture.md:289-292`:

> Nothing in `domain/` or `application/` may construct it — selecting a `Clock`
> is `wiring.py`'s job — and `backend/core/tests/test_no_ambient_time.py`
> enforces both halves mechanically.

Round five read *both halves* as **the sanctioned-call permission and the
construction ban**, and rejected the sentence because only the first was
enforced. Under that reading the sentence is now **true without qualification**:

| Half | Enforced by |
|---|---|
| The ambient-time ban and its single sanctioned call | `test_planner_core_never_calls_an_ambient_clock` + `test_the_sanctioned_call_allowance_is_one_exact_line_in_one_exact_module` (round three G4-G9) |
| The construction ban | `test_no_core_module_but_the_port_names_the_real_clock` (§S2 above) |

I also checked the **less natural** parse a pedantic reader could take — that
*both halves* means the two clauses of the preceding sentence, *"nothing in
`domain/` or `application/` may construct it"* and *"selecting a `Clock` is
`wiring.py`'s job"*. It survives that too. The second clause sits inside em
dashes as an appositive: it restates the first from the positive side rather
than adding an obligation, and its enforceable content — **no `core` module
selects the clock** — is exactly what the new scan asserts. Nothing could
mechanically compel a not-yet-written `wiring.py` to do the selecting, and the
sentence does not claim otherwise.

**Confirming the reading the human asked me to confirm: yes.** Rule 6's sentence
was false when written and is now true, so leaving `docs/architecture.md`
unedited is correct — and better than editing it would have been, because the
sentence now needs no dated annotation, no correction note and no forward
pointer. The file's mtime confirms it was not touched: `docs/architecture.md`
last changed 2026-08-19 00:20:54, before round five's own write at 00:33:50.

---

## S5. Scope of the change — test guard only

Files modified after round five's review write (00:33:50), by mtime:

```
00:39:57  specs/week_calendar/tasks.md
00:40:23  backend/core/tests/test_no_ambient_time.py
00:43:47  progress/impl_week_calendar.md
00:43:56  progress/current.md
```

**Exactly the four the brief names.** No other file under `backend/`,
`frontend/`, `specs/` or `docs/` has an mtime after round five.

`planner_core/` production code is byte-identical. All eight sources checksummed
from the repository after my mutation exercise, against Addendum 3's table:

```
7b0dbe35...39b562a   planner_core/__init__.py                match
85861c2b...6d8aeba   planner_core/application/__init__.py    match
d133c5d4...f0f4b2e   planner_core/application/live_weeks.py  match
0549c359...31ee72d   planner_core/domain/__init__.py         match
e87c761e...939b813e  planner_core/domain/calendar.py         match
e6b34da3...2afdbd915 planner_core/domain/errors.py           match
bb01537b...a68360530 planner_core/ports/clock.py             match
f7eceb3e...6bcfa713c planner_core/ports/__init__.py          match
```

All eight match. `live_weeks.py` — the file both the implementer and I mutated —
is `d133c5d4...f0f4b2e`, unchanged. `git status --porcelain` shows the same
tracked and untracked set as round five, with no new path.

---

## S6. Gates re-run — actual output

`./init.sh` from the repository root — **exit 0**:

```
[OK]    feature_list.json valid (23 features - blocked: 9, done: 1, in_progress: 1, pending: 12)
[OK]    Specs present for every non-pending sdd feature
[OK]    No agent-generated IaC or CI files
[OK]    Requirement coverage: all 103 FR/NFR ids covered by features
[OK]    Next actionable feature: 3 - text_and_units
[OK]    ruff format / ruff check / mypy
...................................                                      [100%]
35 passed in 0.05s
[OK]    pytest (unit + contract, no AWS)
[OK]    prettier --check / eslint / vitest
[OK]    Environment ready. You can start working.
EXIT=0
```

From `backend/`, each gate individually:

```
uv run ruff format --check .   ->  19 files already formatted
uv run ruff check .            ->  All checks passed!
uv run mypy .                  ->  Success: no issues found in 19 source files
uv run pytest -q               ->  35 passed in 0.06s
```

**35 / 19 / 19, and the delta is explainable**: 34 + 1, with the file counts
unchanged at 19 for both `ruff format` and `mypy` because the new test went into
an **existing** module and no source file was added. Expected 35, got 35. No gate
skipped, no count unaccounted for.

---

## S7. Staleness introduced by this round — none

Every claim written this round was checked against its target file.

**`tasks.md` T46 (lines 218-233) — accurate in every clause.** Checked one by
one: the diagnosis (*"`SYSTEM_CLOCK` was applied under `TESTS_ROOT` alone, and
`AMBIENT_TIME` cannot match `SystemClock()`"*) matches the round-five module
exactly; *"the pattern is self-tested first against a construction, an import, a
module-level default and an attribute reference"* — all four are present at
lines 152-158; *"the scanned file list is asserted non-empty and to contain
`application/live_weeks.py` and `domain/calendar.py`"* — lines 203-205, and
A7/A8 prove both assertions fire; *"the exempt module is asserted to actually
declare `SystemClock`"* — line 214, proved by A5; *"a shared `_reaches` helper,
which the T44 scan now uses too"* — lines 70-77 and 184. The dated demarcation
(*"Nothing above is renumbered or altered"*) is true: T1 through T45 are
unchanged, verified against the round-five record.

**`progress/impl_week_calendar.md` Addendum 3 — every factual claim verified.**
The eight checksums match mine (§S5). Its four-mutation table is consistent with
my ten — I reproduced its headline case and its exemption-rot case independently
and got the same outcomes. The *"pre-change, 34 passed"* row is corroborated by
round five's own §P3 result. Its "For the leader" note 1 reaches the same
conclusion about rule 6 that I reach in §S4, and correctly did not act on it.

**`progress/current.md`** describes this round accurately, records 34 to 35, and
its Next step correctly reads *"Feature 2 stays `in_progress`"*.

**`docs/architecture.md`, `CHECKPOINTS.md`, `.claude/agents/*.md`,
`requirements.md`, `design.md`** — untouched this round (§S5) and re-checked for
claims the new test could have invalidated. None found, and two are now *more*
true than they were: §1.2.2 lines 146-149 (*"scans the sources mechanically and
is the authority on both the sanctioned ambient-time call and which modules may
reach for `SystemClock`"*) now covers `CORE_SRC` as well as `TESTS_ROOT`; and
`design.md:599` (*"No `planner_core` module constructs one"*) was a statement of
fact and is now a mechanically enforced one. `design.md:360` (*"The R2 source
scan reads `planner_core`'s own `.py` files"*) remains correct. T44's description
of *"two parts"* describes what T44 added and is not an absolute about the
module's current contents — the same reading round five applied to T15.

**Carried forward, unchanged, informational:**
`progress/impl_week_calendar.md:4` still reads *"Tasks: T1-T40"*; there are now
46. Fourth round with the same demarcated header. No action, as before.

---

## S8. Traceability, tasks, layering, invariants, boundaries

- **FR to R**: unchanged. `FR-MENU-01` to R10-R14; `FR-MENU-02` to R1-R9 and
  R20-R23; `FR-UX-06` to R14-R16; `FR-AI-11` and `FR-SHOP-05` to R1, R2, R4, R5,
  R17-R20, R22, R23. All five ids in `covers` reach an `R<n>`; no orphan among
  the 23.
- **R to test**: unchanged and, for R2, **strengthened**.
  `test_no_core_module_but_the_port_names_the_real_clock` is a fourth concrete
  test behind R2 (*no ambient time anywhere in `planner_core` except the one
  sanctioned call*), and it is the first that makes the *construction* route to a
  violation unreachable. R23 gains it too. No existing test was modified — the 34
  that passed in round five still pass.
- **Not a "nothing raised" test.** It asserts a computed list equals `[]` and
  reports file, line and offending text when it does not; it asserts three
  membership and non-emptiness preconditions on its own input; and it asserts a
  structural property of its exempt module. Ten mutations exercised it, nine were
  caught or failed closed.
- **Tasks**: counted mechanically — **46 `[x]`, 0 `[ ]`**. Nothing renumbered.
- **Layering** (`docs/architecture.md` §3.1): unchanged, and now enforced one
  notch harder. `domain/` imports no `application/`, `ports/`, adapter, handler
  or AWS SDK; `core` imports no `boto3` and no Lambda package; `core` declares
  `dependencies = []`; `application/` imports no adapter or handler; no adapter
  exists. The single `datetime.now()` in `planner_core` is `ports/clock.py:43`,
  permitted by R2, §1.2.2, §3.1 rule 6, §6 and `CHECKPOINTS.md` C3 — all five in
  agreement. **Per `.claude/agents/reviewer.md`,
  `backend/core/tests/test_no_ambient_time.py` is the authority and it passes;
  the guard was strengthened this round, not weakened, so there is nothing here
  to reject on.**
- **Invariants** (§4): this round touches none. Invariant 7 (ISO weeks in
  `Europe/Madrid`, Monday to Sunday, every user agrees on the current week) is
  exercised exactly as round one §5 recorded — the property, not a happy path.
- **Boundaries**: no new `*.tf`, `*.tfvars` or `.github/workflows/**` (`init.sh`
  agrees); frozen requirement docs unmodified; `feature_list.json` diff still
  exactly two lines and **feature 2 is not `done`**; no §2 architecture decision
  made silently — §1.2.2 remains the human's dated decision and this round only
  made its stated control real; no user-facing Spanish outside the messages
  module; the reviewer wrote no code and edited nothing under `backend/`,
  `frontend/`, `specs/` or `docs/`.
- **F5** (R4/R8/R16/R22 carry two `SHALL`s) and **F7** (`ruff` isort grouping of
  `support`) remain open by the human's explicit choice. Round three's
  recommendations 3 (rename `test_planner_core_never_calls_an_ambient_clock`) and
  4 (record the guard's scope for feature 14) remain unactioned and non-blocking.
  Recommendation 4 is now **partly overtaken**: the guard covers `CORE_SRC` as
  well as `backend/core/tests/`, so the only unscanned areas left are
  `backend/tests/contract/` and the Lambda packages' `tests/`.

---

## S9. Checkpoints — round six

- **C1 — The harness is complete:** [x] base files present, the four working docs
  present, the five frozen docs unmodified, `./init.sh` exit 0.
- **C2 — State is coherent:** [x] exactly one `in_progress`; nine `blocked`, each
  with a non-empty reason; the one `done` feature has passing tests;
  `progress/current.md` describes this session.
- **C3 — The code respects the architecture:** [x] on the box's own wording —
  `test_no_ambient_time.py` is green, which is the tick condition
  `CHECKPOINTS.md:33-36` names, and it now checks strictly more than it did.
- **C4 — Verification is real:** [x] with *"every port has a contract suite"*
  deliberately open under the dated, owner-assigned deferral to feature 14.
  `ruff check` clean, `mypy` clean with no `# type: ignore`, 35 green, no AWS, no
  network, and no real clock outside the one sanctioned test.
- **C5 — The session closed properly:** [x] no suspicious untracked files; the
  final close-out entry is the human's to write.
- **C6 — Spec Driven Development:** [x] 46/46 tasks ticked; every `FR-*` in
  `covers` reaches an `R<n>`; every `R<n>` reaches a concrete test;
  `docs/specs.md:73` holds for R2 and R23.
- **C7 — Human-owned boundaries were respected:** [x] no IaC, no CI, no frozen
  doc touched, no §2 decision made by an agent, feature 2 left `in_progress`.

---

## S10. Required changes

**None.**

P3 is closed. No finding was opened this round — and none was manufactured to
justify it. The two items in §S3 are recorded limitations, not defects; the
carried-forward header line in §S7 is the same informational note as rounds two
through five.

**Is anything left that blocks marking feature 2 `done`? No. Nothing remains.**
Unambiguously: requirement coverage is complete, every `R<n>` has a concrete test
that a mutation can break, all 46 tasks are ticked, layering holds, invariant 7
is exercised as a property, every boundary is intact, and every gate is green at
35 / 19 / 19 with `./init.sh` at exit 0. The only open items in the entire
six-round record — F5, F7, round three's recommendations 3 and 4, and the C4
contract-suite deferral — are each open **by the human's own recorded decision**,
and none is owned by feature 2.

Feature 2 is left `in_progress`. **The human closes it, and it is ready to be
closed.**

---

## S11. What could not be verified

- **Deliberate obfuscation** of the `SystemClock` name (§S3 item 1, round three
  G17). Out of reach of any text scan, on both the source and the test side.
  Bounded and recorded.
- **Behaviour on a host with a system IANA database** — every check across all
  six rounds ran on Windows with `zoneinfo.TZPATH` empty and `Europe/Madrid`
  resolving through the `tzdata` dev dependency. Unchanged, and P6-adjacent.
- **SonarQube** — pipeline-owned, not an agent's to invoke.
