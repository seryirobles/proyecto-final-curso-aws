"""Source scans: no ambient clock anywhere in planner_core, no user-facing text either.

R2 is a negative claim about the whole package, so no single call site can prove
it. A scan of the sources is the only way to make it verifiable. This module
excludes itself from its own scans, since it is where the banned patterns are
spelled out.

R23 makes the same shape of claim about the tests and about core itself:
SystemClock is a default implementation shipped inside core
(docs/architecture.md section 1.2.2), so the control that keeps it out of the
test suite, and out of every core module but the one declaring it, has to be
mechanical -- a directory boundary only holds until someone types the import.

Two scans, therefore, not one. AMBIENT_TIME catches the banned calls; it cannot
catch `SystemClock()`, which calls none of them, so the ban on constructing the
real clock (docs/architecture.md section 3.1 rule 6) needs the separate
SYSTEM_CLOCK scan below.
"""

from __future__ import annotations

import re
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parent
CORE_SRC = TESTS_ROOT.parent / "src" / "planner_core"

AMBIENT_TIME = re.compile(
    r"datetime\s*\.\s*now"
    r"|datetime\s*\.\s*utcnow"
    r"|date\s*\.\s*today"
    r"|time\s*\.\s*time"
    r"|time\s*\.\s*localtime"
    r"|\.astimezone\(\s*\)"
)

# The default Clock implementation is the single sanctioned ambient-time call in
# planner_core: it ships beside the Protocol it satisfies because it adds no
# dependency (docs/architecture.md section 1.2.2). The allowance is one exact
# line in one exact module, so it cannot widen without this file changing.
# The same module is the one place in core allowed to name SystemClock at all,
# for the same reason: it is where the class is declared.
DEFAULT_CLOCK_SOURCE = CORE_SRC / "ports" / "clock.py"
DEFAULT_CLOCK_TEST = TESTS_ROOT / "ports" / "test_clock.py"

SANCTIONED_CALL = re.compile(r"\s*return datetime\.now\(UTC\)")

SYSTEM_CLOCK = re.compile(r"\bSystemClock\b")

FEATURE_MODULES = (
    CORE_SRC / "ports" / "clock.py",
    CORE_SRC / "domain" / "errors.py",
    CORE_SRC / "domain" / "calendar.py",
    CORE_SRC / "application" / "live_weeks.py",
)


def _offenders(sources: list[Path]) -> list[str]:
    offences: list[str] = []
    for source in sources:
        for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
            if source == DEFAULT_CLOCK_SOURCE and SANCTIONED_CALL.fullmatch(line):
                continue
            found = AMBIENT_TIME.search(line)
            if found:
                offences.append(f"{source}:{number}: {found.group(0)}")
    return offences


def _reaches(sources: list[Path]) -> list[str]:
    """Every line naming SystemClock, located. Shared by both SYSTEM_CLOCK scans."""
    found: list[str] = []
    for source in sources:
        for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
            if SYSTEM_CLOCK.search(line):
                found.append(f"{source}:{number}: {line.strip()}")
    return found


def test_the_ambient_time_pattern_detects_what_it_claims_to() -> None:
    """A scan that matches nothing proves nothing: check the pattern first."""
    for banned in (
        "datetime.now()",
        "datetime.utcnow()",
        "date.today()",
        "time.time()",
        "time.localtime()",
        "instant.astimezone()",
    ):
        assert AMBIENT_TIME.search(banned), banned

    assert not AMBIENT_TIME.search("instant.astimezone(MADRID)")
    assert not AMBIENT_TIME.search("clock.now()")


def test_the_sanctioned_call_allowance_is_one_exact_line_in_one_exact_module() -> None:
    """R23: the default Clock implementation is the only exception, and stays the only one."""
    lines = DEFAULT_CLOCK_SOURCE.read_text(encoding="utf-8").splitlines()

    assert lines, f"{DEFAULT_CLOCK_SOURCE} is empty"
    sanctioned = [line for line in lines if SANCTIONED_CALL.fullmatch(line)]
    assert len(sanctioned) == 1, sanctioned
    assert AMBIENT_TIME.search(sanctioned[0]), sanctioned[0]

    for adjacent in (
        "        return datetime.now()",
        "        return datetime.utcnow()",
        "        instant = datetime.now(UTC)",
        "        return datetime.now(UTC) + drift",
    ):
        assert not SANCTIONED_CALL.fullmatch(adjacent), adjacent


def test_planner_core_never_calls_an_ambient_clock() -> None:
    """R2: time enters planner_core through the Clock port or not at all."""
    sources = sorted(CORE_SRC.rglob("*.py"))

    assert sources, f"no planner_core sources found under {CORE_SRC}"
    assert CORE_SRC / "domain" / "calendar.py" in sources
    assert _offenders(sources) == []


def test_week_calendar_tests_never_call_an_ambient_clock() -> None:
    """R2, R22: the tests read time only from FakeClock, never from the host."""
    this_module = Path(__file__).resolve()
    sources = [path for path in sorted(TESTS_ROOT.rglob("*.py")) if path != this_module]

    assert sources, f"no test sources found under {TESTS_ROOT}"
    assert TESTS_ROOT / "domain" / "test_calendar.py" in sources
    assert _offenders(sources) == []

    users_of_time: list[Path] = []
    for path in sources:
        body = path.read_text(encoding="utf-8")
        if "civil_date" in body or "resolve_live_weeks" in body:
            users_of_time.append(path)
            assert "FakeClock" in body, path

    assert users_of_time


def test_calendar_modules_contain_no_user_facing_text() -> None:
    """R16: no Castilian Spanish can have leaked into backend domain code."""
    for module in FEATURE_MODULES:
        source = module.read_text(encoding="utf-8")
        assert source, f"{module} is empty"
        assert source.isascii(), f"{module} contains non-ASCII characters"


def test_the_system_clock_pattern_detects_what_it_claims_to() -> None:
    """A scan that matches nothing proves nothing: check the pattern first."""
    for reach in (
        "from planner_core.ports.clock import SystemClock",
        "from planner_core.ports.clock import Clock, SystemClock",
        "clock = SystemClock()",
        "DEFAULT_CLOCK = SystemClock()",
        "    monkeypatch.setattr(clock_module.SystemClock, 'now', stub)",
        "    def __init__(self, clock: Clock | None = None) -> None:  # SystemClock",
    ):
        assert SYSTEM_CLOCK.search(reach), reach

    assert not SYSTEM_CLOCK.search("clock = FakeClock.at('2026-07-16T10:00:00+00:00')")
    assert not SYSTEM_CLOCK.search("from planner_core.ports.clock import Clock")
    assert not SYSTEM_CLOCK.search("    def now(self) -> datetime:")


def test_no_test_module_reaches_for_the_real_clock() -> None:
    """R23: only the port's own test may touch SystemClock; every other module may not.

    This is the control that replaces a directory boundary, so it is enforced by
    scanning rather than by where the class sits (docs/architecture.md section
    1.2.2). The exempt module is asserted to use SystemClock, so the exemption
    cannot quietly become a hole covering nothing.
    """
    this_module = Path(__file__).resolve()
    exempt = {this_module, DEFAULT_CLOCK_TEST}
    sources = [path for path in sorted(TESTS_ROOT.rglob("*.py")) if path not in exempt]

    assert sources, f"no test sources found under {TESTS_ROOT}"
    assert TESTS_ROOT / "domain" / "test_calendar.py" in sources
    assert DEFAULT_CLOCK_TEST.is_file(), DEFAULT_CLOCK_TEST
    assert SYSTEM_CLOCK.search(DEFAULT_CLOCK_TEST.read_text(encoding="utf-8")), DEFAULT_CLOCK_TEST

    assert _reaches(sources) == []


def test_no_core_module_but_the_port_names_the_real_clock() -> None:
    """R2, R23: nothing in planner_core may reach for SystemClock but the module declaring it.

    Selecting a Clock is wiring.py's job, so no module under domain/ or
    application/ may construct one (docs/architecture.md section 3.1 rule 6).
    AMBIENT_TIME cannot see that violation -- `SystemClock()` calls none of the
    banned functions -- so the construction ban needs this scan, and the scan is
    stated as "names it" rather than "constructs it": an import or an attribute
    reference is reach enough to construct one on the next line. A mention in a
    comment is caught too, deliberately: prose about SystemClock belongs beside
    the class in ports/clock.py, or here, and this scan reads neither. The
    exempt module is asserted to declare SystemClock, so the exemption cannot
    quietly become a hole covering nothing.
    """
    sources = [path for path in sorted(CORE_SRC.rglob("*.py")) if path != DEFAULT_CLOCK_SOURCE]

    assert sources, f"no planner_core sources found under {CORE_SRC}"
    assert CORE_SRC / "application" / "live_weeks.py" in sources
    assert CORE_SRC / "domain" / "calendar.py" in sources
    assert DEFAULT_CLOCK_SOURCE.is_file(), DEFAULT_CLOCK_SOURCE

    named_in_exempt = [
        line.strip()
        for line in DEFAULT_CLOCK_SOURCE.read_text(encoding="utf-8").splitlines()
        if SYSTEM_CLOCK.search(line)
    ]
    assert named_in_exempt, DEFAULT_CLOCK_SOURCE
    assert any(line.startswith("class SystemClock") for line in named_in_exempt), named_in_exempt

    assert _reaches(sources) == []
