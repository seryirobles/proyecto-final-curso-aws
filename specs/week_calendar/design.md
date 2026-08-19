# week_calendar — Design

> Feature 2 · tier 1 · pure `planner_core`
> Read `requirements.md` first. This document records the technical decisions
> taken before any code is written, per `docs/specs.md`.

## 0. The invariant this feature exists to protect

`docs/architecture.md` §4 invariant 7:

> **Weeks are ISO weeks in `Europe/Madrid`. Monday–Sunday. Every user must
> agree on which week is current.**

Every decision below is subordinate to that sentence. "Every user must agree"
is what forbids the host timezone from entering the computation, what forbids
storing a "this week is current" flag (`docs/data_model.md` §2: the id is
*derived from the clock, never stored as state*), and what makes a single
shared scoping function — rather than one per consumer — non-negotiable.

---

## 1. Scope boundary — what this feature owns of each `FR-*`

Two of the five covered requirements are also claimed by later features.
Getting this line wrong is what bites in feature 7 and feature 10, so it is
drawn explicitly.

| Requirement | Owned **here** | Deferred to |
|---|---|---|
| `FR-MENU-01` | The shape of a live week: 7 days Monday→Sunday, 2 slots per day, the ordering, the numbering. | Slot *contents* (candidates, definitive) — **feature 5 `week_plan_model`** (`FR-MENU-03`). |
| `FR-MENU-02` | Everything. Current/next week identity, the `Europe/Madrid` ISO-week computation, the `Clock` port. | — |
| `FR-UX-06` | The **data** the label needs: the current/next distinction as an enum, and the Monday–Sunday date range per live week. | The es-ES rendering of that label, its placement in every week view / summary / week-scoped action — **feature 20 `frontend_spa`**. This feature produces **no user-facing strings**. |
| `FR-AI-11` | **Only the calendar clause**: "for the current week, only slots from the current day onward (Europe/Madrid) are targeted". | Everything else in `FR-AI-11` — disabled days, pin resolution, skipping slots that already hold a definitive, the definitive-outranks-pin rule and its report, final-state category counting, additive semantics — **feature 10 `generation_request`** (`G-71`, `G-18`, `G-45`). |
| `FR-SHOP-05` | **Only the scope clause**: "the current week from the current day onward (Europe/Madrid) plus the whole next week". | Definitive-only sourcing and the aggregation itself — **feature 7 `shopping_aggregation`** (`G-04`, `G-52`). |

**The reusable artefact.** Both deferred features consume the same function,
`slots_from(week, first_day)`. `docs/conventions.md` § *Frontend conventions*
names the exact failure this prevents: *"Two implementations of 'which slots are
in scope' is exactly how the current-week-from-today rule (`FR-AI-11`,
`FR-SHOP-05`) silently diverges."* Features 7 and 10 must call it, never
re-derive it.

**Elegance worth noting:** the current-week and next-week rules are not two
branches. `slots_from(week, today)` keeps the slots of days `>= today`. For the
next week, `today` is always before its Monday, so all fourteen slots survive —
R18 falls out of R17 by construction rather than by a second code path.

---

## 2. Layering

`docs/architecture.md` §3 describes `domain/` as *"Pure logic. No IO, no AWS
SDK, no framework, **no clock**."* and lists `clock` among the `ports/`
protocols. §3.1 rule 1 forbids `domain/` importing from `ports/`.

So the split is:

| Piece | Layer | Why |
|---|---|---|
| `Clock` protocol | `planner_core/ports/` | §3 lists it there. |
| Calendar maths — civil date, ISO week, days, slots, scoping | `planner_core/domain/` | Pure functions of a `datetime` / `date`. |
| Reading the clock and handing the instant to the domain | `planner_core/application/` | The only place the two meet. |

Consequence: **domain functions take an instant or a date, never a `Clock`.**
The application service reads the clock once (R14) and passes the resulting
civil date down.

---

## 3. Files

### Created

| Path | Contents |
|---|---|
| `backend/core/src/planner_core/ports/clock.py` | `Clock` protocol. |
| `backend/core/src/planner_core/domain/errors.py` | `PlannerError` base (`docs/conventions.md` § *Error handling*). First domain module in the repo, so the base class is established here for features 3–13. |
| `backend/core/src/planner_core/domain/calendar.py` | `MADRID`, `MealSlot`, `SlotRef`, `WeekDay`, `IsoWeek`, `civil_date`, `current_week`, `next_week`, `slots_from`, `NaiveInstant`, `InvalidIsoWeek`. |
| `backend/core/src/planner_core/application/live_weeks.py` | `LiveWeek`, `LiveWeeks`, `resolve_live_weeks`. |
| `backend/core/tests/conftest.py` | Makes `support` importable from test modules in subdirectories (pytest inserts a `conftest.py`'s directory on `sys.path` under the default `prepend` import mode). |
| `backend/core/tests/support/__init__.py` | Replaces the current `.gitkeep`; turns `support` into a package. |
| `backend/core/tests/support/fakes.py` | `FakeClock`. |
| `backend/core/tests/ports/test_clock.py` | R1, R22. |
| `backend/core/tests/domain/test_calendar.py` | R3–R13, R17–R21. |
| `backend/core/tests/application/test_live_weeks.py` | R14–R19. |
| `backend/core/tests/test_no_ambient_time.py` | R2. |

### Modified

None. No `pyproject.toml` runtime dependency changes — see §7 for the one
**dev-group** addition being proposed.

---

## 4. Signatures

### `planner_core/ports/clock.py`

```python
@runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime:
        """Return the present instant as a timezone-aware datetime."""
```

The port's contract is *aware*, not *UTC*: an adapter returning
`datetime.now(UTC)` and one returning an aware `Europe/Madrid` value are both
valid, and the domain converts either correctly (R5). A naive value is a
contract violation and is rejected loudly (R3).

`@runtime_checkable` exists so `isinstance(FakeClock(...), Clock)` is a real
assertion in `test_clock.py`; mypy strict does the structural checking that
matters.

### `planner_core/domain/errors.py`

```python
class PlannerError(Exception):
    """Base class for domain errors."""
```

### `planner_core/domain/calendar.py`

```python
MADRID: Final = ZoneInfo("Europe/Madrid")


class NaiveInstant(PlannerError):
    """Raised when an instant carries no UTC offset."""


class InvalidIsoWeek(PlannerError):
    """Raised when a week number does not exist in its ISO year."""


class MealSlot(IntEnum):
    LUNCH = 1
    DINNER = 2


@dataclass(frozen=True)
class SlotRef:
    day: date
    slot: MealSlot

    @property
    def day_number(self) -> int: ...       # date.isocalendar().weekday, 1..7


@dataclass(frozen=True)
class WeekDay:
    day: date

    @property
    def day_number(self) -> int: ...
    @property
    def slots(self) -> tuple[SlotRef, SlotRef]: ...


@dataclass(frozen=True)
class IsoWeek:
    iso_year: int
    iso_week: int

    def __post_init__(self) -> None: ...   # raises InvalidIsoWeek

    @property
    def week_id(self) -> str: ...          # "2026-W53"
    @property
    def monday(self) -> date: ...
    @property
    def sunday(self) -> date: ...
    @property
    def date_range(self) -> tuple[date, date]: ...
    @property
    def days(self) -> tuple[WeekDay, ...]: ...     # 7
    @property
    def slots(self) -> tuple[SlotRef, ...]: ...    # 14

    def following(self) -> IsoWeek: ...


def civil_date(instant: datetime) -> date: ...     # raises NaiveInstant
def current_week(today: date) -> IsoWeek: ...
def next_week(today: date) -> IsoWeek: ...
def slots_from(week: IsoWeek, first_day: date) -> tuple[SlotRef, ...]: ...
```

Entities are `@dataclass(frozen=True)` per `docs/conventions.md` § *Python
style*. `day_number` and `week_id` are **derived properties, never constructor
arguments**, so no caller can build an inconsistent one — that is the whole
mitigation for the two traps in §5.

### `planner_core/application/live_weeks.py`

```python
class LiveWeek(Enum):
    CURRENT = "current"
    NEXT = "next"


@dataclass(frozen=True)
class LiveWeeks:
    today: date
    current_week: IsoWeek
    next_week: IsoWeek

    def week(self, which: LiveWeek) -> IsoWeek: ...
    def date_range(self, which: LiveWeek) -> tuple[date, date]: ...
    def slots_in_scope(self, which: LiveWeek) -> tuple[SlotRef, ...]: ...


def resolve_live_weeks(clock: Clock) -> LiveWeeks: ...
```

`resolve_live_weeks` reads the clock **once** (R14). Two separate reads could
straddle midnight on a Sunday and return a `current`/`next` pair that is not
adjacent — precisely the disagreement invariant 7 forbids.

`LiveWeek.CURRENT` / `.NEXT` carry no Spanish text (R16). The es-ES rendering
of "semana actual" / "semana siguiente" belongs to the frontend messages module
(feature 20, `FR-UX-01`, `FR-UX-03`).

### Exceptions

| Exception | Base | Raised when |
|---|---|---|
| `PlannerError` | `Exception` | never directly; base for all domain errors |
| `NaiveInstant` | `PlannerError` | `civil_date` receives an instant whose `utcoffset()` is `None` |
| `InvalidIsoWeek` | `PlannerError` | `IsoWeek` is constructed with a non-existent week number |

No function in this feature returns `None` to signal failure
(`docs/architecture.md` §4 invariant 12).

---

## 5. Key-format traps honoured (`docs/data_model.md` §2)

This feature is where those formats are actually computed, so the traps are
handled here once instead of in every consumer.

1. **`idSemana` uses the ISO week-numbering year.** `IsoWeek.iso_year` comes
   from `date.isocalendar().year`, never `date.year`. `week_id` formats
   `f"{iso_year}-W{iso_week:02d}"` — zero-padded, because keys sort as bytes
   and `W9` would sort after `W10`.
2. **`numeroDia` is `date.isocalendar().weekday`, not `date.weekday()`.** The
   two differ by one, and mixing them lands Sunday in the next week's
   partition *while passing every test written on a Monday*. Mitigated by
   making `day_number` a derived property with exactly one implementation, and
   by the explicit Sunday-is-7 test (T16).
3. **`numeroComida`: lunch = 1, dinner = 2**, one-based to match `numeroDia`.
   `MealSlot` is an `IntEnum` so the stored value is the enum value itself.
4. **The week id is derived, never stored as state.** Nothing in this feature
   persists "which week is current"; `resolve_live_weeks` recomputes it from
   the clock every time. That is what makes rollover cheap (feature 13).

### Note for the human at the spec gate — a factual error in `docs/data_model.md` §2

> **Resolved 2026-08-18.** The human corrected `docs/data_model.md` line 75; it
> now cites the two dates named below. The analysis that follows was true at the
> spec gate and is kept as the record of why the change was made.

The `idSemana` section illustrates the ISO-year trap with:

> ⚠ They differ at year boundaries: **2026-12-28 belongs to `2027-W01`**.

**That example is wrong.** 2026 is a 53-week ISO year (1 January 2026 is a
Thursday), so `date(2026, 12, 28).isocalendar()` is `(2026, 53, 1)` —
2026-12-28 belongs to **`2026-W53`**, and its calendar year and ISO year agree.
It does not demonstrate the trap.

The **rule** the section states is correct and load-bearing — use
`date.isocalendar()[0]`, never `date.year`. Only the illustrating date is
wrong, so this is a documentation defect, not a blocker. Two dates that do
demonstrate the trap, both verified:

| Date | Calendar year | ISO week id | What `date.year` would produce |
|---|---|---|---|
| 2025-12-31 | 2025 | `2026-W01` | `2025-W01` — off by a full year |
| 2027-01-01 | 2027 | `2026-W53` | `2027-W53` — a week that does not exist |

Both are used as test cases below (T21). `docs/data_model.md` is outside this
agent's mandate, so the example has been left untouched for the owner to
correct.

---

## 6. Timezone strategy, and the verification trap

### 6.1 The mechanism

`zoneinfo.ZoneInfo("Europe/Madrid")` from the standard library, bound once to a
module-level `MADRID` constant. `civil_date(instant)` is
`instant.astimezone(MADRID).date()`.

**The host's local timezone must never enter the computation.** Concretely,
the following are banned in `planner_core` and in this feature's tests:

> *Amended 2026-08-19.* R23 later added `SystemClock`, so this list is no longer
> absolute: one line, `return datetime.now(UTC)` in `ports/clock.py`, is
> sanctioned (§11, `docs/architecture.md` §1.2.2). Everything else below stands.
> `backend/core/tests/test_no_ambient_time.py` is the authority.

- `datetime.now()`, `datetime.utcnow()`, `date.today()`, `time.time()`,
  `time.localtime()` — ambient clock (R2);
- `astimezone()` with **no argument** — silently converts to the host zone;
- `datetime.fromtimestamp(x)` without `tz=` — same problem;
- `datetime.astimezone()` applied to a naive value — Python assumes the host
  zone instead of raising (R3 exists so this cannot happen unnoticed).

R3's check is `instant.utcoffset() is None`, **not** `instant.tzinfo is None`:
a `tzinfo` whose `utcoffset()` returns `None` is still a naive value, and the
`tzinfo is None` check would wave it through.

### 6.2 Why the tests do not sweep timezones — read this before "improving" them

The obvious verification is "run the suite under five different `TZ` values".
**It proves close to nothing, and on this machine it does not run at all.**
Verified here:

- `time.tzset` does not exist on Windows (`hasattr(time, "tzset")` → `False`),
  so Python cannot re-read `TZ` after start-up at all.
- In the shell/Node environment on this machine, only `TZ=UTC` takes effect;
  any IANA zone name silently falls back to `Europe/Madrid` — which is the very
  answer the test is trying to prove, so the sweep would pass for the wrong
  reason.

Even where a sweep *does* work, it tests the host's configuration rather than
the code. **Timezone correctness is proved by construction instead:**

1. The only source of time is the `Clock` port (R1), and the tests inject a
   `FakeClock` built from an **explicit ISO-8601 instant with an explicit
   offset** (R22). No ambient state is manipulated, so none can be
   accidentally relied upon.
2. A source scan asserts no ambient-time call exists in `planner_core` or in
   this feature's tests (R2, T13). This is the negative claim acceptance
   criterion 1 makes, and a scan is the only way to make it verifiable.
   *(Amended 2026-08-19: R23 added one sanctioned call — see §11. The scan is
   the authority on which.)*
3. **The offset-independence test (R5, T14)** is the positive proof: the same
   absolute moment expressed as `+00:00`, `+05:00` and `-08:00` must yield the
   same civil date, the same week and the same scope. A computation that
   leaked the host zone, or that used the wall-clock fields instead of the
   instant, cannot pass all three.
4. **The Madrid-versus-UTC boundary pair (T15)** is the proof that the
   conversion is not a no-op: `2026-07-19T22:00:00+00:00` is Sunday
   2026-W29 in UTC but **Monday 2026-07-20, week 2026-W30** in Madrid. An
   implementation that skipped the conversion returns the wrong week here.

### 6.3 Interpretation note for the reviewer

`docs/verification.md` says `core` tests must run with *"no AWS, no network, no
filesystem"*. Two things in this design touch the filesystem in a way that is
**not** the IO that rule is about, and both are called out so they are not
mistaken for violations:

- `ZoneInfo` reads the platform IANA database once at import. It is a standard
  library data lookup, and it is the mechanism `FR-MENU-02` mandates by naming
  `Europe/Madrid`.
- The R2 source scan reads `planner_core`'s own `.py` files. It inspects the
  artefact under test, not an external system.

---

## 7. Dependency proposal — `tzdata`, dev group only

**Verified on this machine:** `ZoneInfo("Europe/Madrid")` raises
`ZoneInfoNotFoundError`. Windows ships no IANA time-zone database, and CPython
falls back to the `tzdata` PyPI package, which is not currently installed. The
feature cannot even be tested here without it.

**Proposal:** add `tzdata` to the **`[dependency-groups] dev`** list in
`backend/pyproject.toml`.

- It does **not** become a runtime dependency of `planner-core`. Feature 1's
  acceptance criterion — *"`backend/core` is distribution `planner-core` with
  ZERO runtime dependencies"* — and `docs/conventions.md` § *Packaging* both
  hold, unchanged.
- `uv export --package planner-api --no-dev` and `--package planner-ai --no-dev`
  are unaffected, so the closure check feature 1 established still means what
  it meant.
- `docs/architecture.md` §1.3 requires any tool outside its table to be
  justified in an approved `design.md`. This is that justification; the human
  approves or rejects it at the normal spec gate.

**Deployment caveat, flagged not decided.** At runtime the tz database must
exist on the Lambda host. The AWS-managed Python runtimes (Amazon Linux) ship
`/usr/share/zoneinfo`, so no runtime dependency is needed there. If the human
would rather not depend on that, the fix is to add `tzdata` to
`backend/lambda_api/pyproject.toml` and `backend/lambda_ai/pyproject.toml` —
**never to `core`**. Which of the two applies depends on the packaging/runtime
choice, which is P6 (deployment topology) and human-owned; this feature does
not need it decided, because the dev-group addition is sufficient for tier 1.

---

## 8. Concrete test instants

Acceptance criterion 6 asks for DST transitions and year boundaries. Naming the
dates is part of the design, not left to the implementer. Every value below was
computed with `zoneinfo` and `date.isocalendar()` and is reproduced verbatim.

### 8.1 Madrid DST transitions

Spain changes offset on the **last Sunday of March** (CET +01:00 → CEST +02:00)
and the **last Sunday of October** (CEST → CET). Both are **Sundays — the last
day of an ISO week**, which is exactly where a wrong offset flips the answer
into the wrong week.

| Instant (UTC) | Madrid local | Civil date | Week |
|---|---|---|---|
| `2026-03-28T23:30:00+00:00` | `2026-03-29T00:30+01:00` | 2026-03-29 (Sun) | `2026-W13` |
| `2026-03-29T01:30:00+00:00` | `2026-03-29T03:30+02:00` | 2026-03-29 (Sun) | `2026-W13` |
| `2026-03-29T22:30:00+00:00` | `2026-03-30T00:30+02:00` | 2026-03-30 (Mon) | `2026-W14` |
| `2026-10-24T23:30:00+00:00` | `2026-10-25T01:30+02:00` | 2026-10-25 (Sun) | `2026-W43` |
| `2026-10-25T00:30:00+00:00` | `2026-10-25T02:30+02:00` | 2026-10-25 (Sun) | `2026-W43` |
| `2026-10-25T01:30:00+00:00` | `2026-10-25T02:30+01:00` | 2026-10-25 (Sun) | `2026-W43` |
| `2026-10-25T23:00:00+00:00` | `2026-10-26T00:00+01:00` | 2026-10-26 (Mon) | `2026-W44` |

Rows 5 and 6 are the **ambiguous local hour**: two distinct instants that both
render as `02:30` local. They must produce the same date and week, and the
code must never need to disambiguate — because it converts *from* the instant,
never *to* it.

Rows 3 and 7 are the **week flip on the transition day itself**: the DST change
and the Sunday→Monday rollover happen within the same 24 hours.

### 8.2 Week boundary at Madrid midnight

| Instant (UTC) | Madrid local | Civil date | Week |
|---|---|---|---|
| `2026-07-19T21:59:59+00:00` | `2026-07-19T23:59:59+02:00` | 2026-07-19 (Sun) | `2026-W29` |
| `2026-07-19T22:00:00+00:00` | `2026-07-20T00:00:00+02:00` | 2026-07-20 (Mon) | `2026-W30` |
| `2026-01-18T22:59:59+00:00` | `2026-01-18T23:59:59+01:00` | 2026-01-18 (Sun) | `2026-W03` |
| `2026-01-18T23:00:00+00:00` | `2026-01-19T00:00:00+01:00` | 2026-01-19 (Mon) | `2026-W04` |

Summer and winter pairs, so the offset actually used is +02:00 in one and
+01:00 in the other. This is `G-57`'s "around midnight Sunday the words change
meaning while the dates do not", made executable.

### 8.3 ISO year boundaries and 53-week years

| Civil date | Calendar year | Week id | Next week |
|---|---|---|---|
| 2025-12-30 | 2025 | `2026-W01` | `2026-W02` |
| 2025-12-31 | 2025 | `2026-W01` | `2026-W02` |
| 2026-12-28 | 2026 | `2026-W53` | `2027-W01` |
| 2026-12-31 | 2026 | `2026-W53` | `2027-W01` |
| 2027-01-01 | 2027 | `2026-W53` | `2027-W01` |
| 2027-01-03 | 2027 | `2026-W53` | `2027-W01` |
| 2020-12-31 | 2020 | `2020-W53` | `2021-W01` |
| 2021-01-01 | 2021 | `2020-W53` | `2021-W01` |
| 2027-12-27 | 2027 | `2027-W52` | `2028-W01` |

Notable ranges: `2026-W53` spans **2026-12-28 → 2027-01-03**, a week whose
Monday and Sunday are in different calendar years, and whose date range
(R15, `FR-UX-06`) therefore has to be right for the UI label to make sense.

Validation cases for R9: `IsoWeek(2026, 53)` is valid; `IsoWeek(2027, 53)`,
`IsoWeek(2026, 0)` and `IsoWeek(2026, 54)` all raise `InvalidIsoWeek`.

### 8.4 Today-onward scoping

Reference instant `2026-07-16T10:00:00+00:00` → Madrid `2026-07-16T12:00+02:00`
→ Thursday, day 4 of `2026-W29` (2026-07-13 → 2026-07-19).

| Case | Expected |
|---|---|
| current week scope | 8 slots: Thu/Fri/Sat/Sun × lunch, dinner |
| next week scope | 14 slots, `2026-W30`, 2026-07-20 → 2026-07-26 |
| first in-scope slot | 2026-07-16 lunch — **today's lunch is in scope** (R19) |
| Monday instant `2026-07-13T05:00:00+00:00` | current week scope = all 14 slots |
| Sunday instant `2026-07-19T20:00:00+00:00` (22:00 local) | current week scope = 2 slots (Sunday lunch + dinner) — R19 again: late in the evening still includes that day's lunch |

---

## 9. Rejected alternatives

**A. Pass the `Clock` into the domain functions — `current_week(clock)`.**
Rejected. *(**Resolved 2026-08-18:** the human confirmed this rejection as a
ruling binding on all of tier 1, and `docs/specs.md` has since been corrected —
its example no longer shows `current_week(clock)`. The reasoning below stands as
written; only its citation of that snippet is now historical.)* `docs/architecture.md` §3 describes `domain/` as *"Pure logic. No IO,
no AWS SDK, no framework, **no clock**"*, and §3.1 rule 1 forbids `domain/`
importing from `ports/`. The illustrative snippet in `docs/specs.md` shows
`current_week(clock)` in `domain/calendar.py`; it is an example of EARS and
task formatting, not a layering ruling, and the architecture document is
authoritative. Domain takes an instant or a date; the application layer owns
the port.

**B. Compute "today" from the UTC date.**
Rejected, and demonstrably wrong: `2026-07-19T22:00:00+00:00` is Sunday in UTC
and Monday 2026-07-20 in Madrid — a different ISO week. For two hours every
summer night (one in winter) this implementation would put every user in the
previous week, breaking invariant 7 exactly when the rollover job runs.

**C. Hand-roll a `Europe/Madrid` `tzinfo` from the EU DST rule to avoid the
`tzdata` dependency.**
Rejected. The rule (last Sunday of March / October) is legislation, not
arithmetic — the EU has an open, repeatedly deferred proposal to abolish
seasonal changes. Hard-coding it puts a political decision inside
`planner_core.domain` where no test can detect that it went stale, in exchange
for avoiding a **test-only** dependency. `zoneinfo` is the standard library's
answer to this and is what `FR-MENU-02` implies by naming an IANA zone.

**D. Make `tzdata` a runtime dependency of `planner-core`.**
Rejected. It would break feature 1's *zero runtime dependencies* guarantee for
`core`, which is the property that keeps tier 1 architecture-independent. If
the deployment host turns out to lack the tz database, the dependency belongs
in the **Lambda** packages (§7), never in `core`.

**E. Prove timezone correctness with a `TZ` environment sweep.**
Rejected on verified evidence — see §6.2. `time.tzset` does not exist on
Windows, and in this environment only `TZ=UTC` takes effect while every IANA
name silently falls back to `Europe/Madrid`, so the sweep would pass for the
wrong reason. Correctness is proved by construction through the `Clock` port,
the offset-independence test and the Madrid-versus-UTC boundary pair.

**F. Compute the next week as `iso_week + 1`.**
Rejected. ISO years have 52 or 53 weeks — 2026 has 53 — so the increment
overflows once every five or six years and produces a week that does not
exist. `following()` is `IsoWeek.containing(self.monday + timedelta(days=7))`:
date arithmetic, then re-derivation, so 52-week and 53-week years need no
special case at all.

**G. Derive `numeroDia` from `date.weekday()`.**
Rejected — `docs/data_model.md` §2 documents this as a trap: `weekday()` is
zero-based, `isocalendar().weekday` is one-based, and mixing them lands Sunday
in the next week's partition *while passing every test written on a Monday*.

**H. Scope the current week at slot granularity — drop today's lunch once it is
past midday.**
Rejected. `FR-AI-11` and `FR-SHOP-05` both say *"from the current day
onward"*, and `G-45`'s reasoning is about days that *"can never be cooked"*,
not about elapsed meals. Slot-granular scoping would also need a "when is lunch
over" threshold that no requirement supplies — inventing one is exactly what
`docs/specs.md` forbids. R19 pins the day-granular reading with a test.

**I. Store a "this week is current" flag or a week entity.**
Rejected. `docs/data_model.md` §2: the week id is *"derived from the clock,
never stored as state. That is what makes rollover cheap — no week data moves;
weeks simply stop being current."* A stored flag also reintroduces the
disagreement invariant 7 forbids, since two readers could see different flag
values mid-update.

**J. Add `IsoWeek.from_id("2026-W53")` now.**
Rejected as scope creep. Nothing in this feature parses a week id; the read
path that needs it arrives with **feature 14 `persistence_ports`**, and it
belongs in the same review as the item shapes it deserialises. Noted here so
feature 14 adds it rather than re-deriving the format.

---

## 10. Boundary checks

- **`docs/architecture.md` §2 (pending, human-owned):** nothing in this design
  needs P2, P3, P4, P5 or P6. The `tzdata` runtime question *touches* P6 but
  does not require it decided — §7 explains why the dev-group addition is
  sufficient for tier 1.
- **§2.1 items (unit list, ingredient categories, servings count):** none are
  touched by this feature. No values are proposed.
- **Frozen docs:** none modified. The `docs/data_model.md` §2 error in §5 is
  reported, not patched.
- **User-facing strings:** none. This feature is pure backend domain logic;
  `FR-UX-06`'s Castilian Spanish labelling is feature 20's.
- **Python version:** the workspace pins 3.13 (`backend/pyproject.toml`,
  `requires-python = ">=3.13, <3.14"`), while `docs/conventions.md` § *Python
  style* still says 3.12. Doc drift only — nothing in this design depends on
  the difference. Flagged for the owner. *(**Resolved 2026-08-18:**
  `docs/conventions.md` now states 3.13 with the bounded range and the
  `.python-version` pin.)*

---

## 11. Post-approval addition — `SystemClock` (2026-08-18)

Appended after this design was approved, implemented and reviewed. **Nothing
above is amended**; this section records what was added and why.

§4 declared `Clock` as a `Protocol` and left every implementation to the
consumer, because the architecture had no rule saying where a *real* one
belongs. The human closed that on 2026-08-18 in `docs/architecture.md` §1.2.2:
**a port's dependency-free default implementation ships with the port.** So
`SystemClock` lives in `planner_core/ports/clock.py`, beside the `Protocol` it
satisfies — a default implementation, not an adapter. An implementation only
becomes an adapter, and only then moves into a Lambda package, when it pulls in
an external dependency.

```python
# planner_core/ports/clock.py
class SystemClock:
    def now(self) -> datetime: ...   # datetime.now(UTC) — aware, never utcnow()
```

What this does **not** change:

- **`planner-core` still declares zero runtime dependencies.** A default
  implementation adds none by definition; the `uv export` closures for both
  Lambdas are unchanged (`§7`).
- **No `planner_core` module constructs one.** `resolve_live_weeks` still takes
  its `Clock` as a parameter, so every existing test still drives it with the
  `FakeClock` of R22. Choosing the concrete implementation stays `wiring.py`'s
  job, by environment (`docs/conventions.md` § *Packaging conventions*).
- **R2 still holds.** The one exception is a single full line —
  `return datetime.now(UTC)` in `ports/clock.py` — and the scan in
  `backend/core/tests/test_no_ambient_time.py` allows that line and no other,
  in that module and no other. §1.2.2 leans on that scan, and on its assertion
  about which test modules may name `SystemClock`, precisely because a directory
  boundary would only hold until someone typed the import. *(Amended 2026-08-19:
  this sentence read "no test module names `SystemClock`". The guard exempts the
  port's own test — which is required to construct one — so the absolute
  overstated the control §1.2.2 depends on. The module is the authority; its
  exemptions are deliberately not restated here.)*

The reason the class exists at all rather than being written per Lambda is the
`datetime.utcnow()` footgun: it returns a **naive** value that `civil_date`
rejects with `NaiveInstant`, and it is deprecated from Python 3.12. Two Lambdas
each writing their own three-line clock is two chances to trip it.

