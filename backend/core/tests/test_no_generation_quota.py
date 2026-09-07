"""Source scan: no per-user generation counter or quota anywhere in the worker
use case or `planner_ai` (NFR-AI-01 / G-70 — the cap is global, enforced through
AWS cost tooling; the application stores and enforces no per-user quota, R19,
R20). A negative claim about a set of modules, so only a scan proves it —
mirrors `test_no_ambient_time.py`'s technique."""

from __future__ import annotations

import re
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parent
CORE_SRC = TESTS_ROOT.parent / "src" / "planner_core"
BACKEND_ROOT = TESTS_ROOT.parent.parent

WORKER_USE_CASE = CORE_SRC / "application" / "week_generation.py"
PLANNER_AI_SRC = BACKEND_ROOT / "lambda_ai" / "src"

# Per-user metering vocabulary, English and Castilian. The gate is a single
# deployment-wide boolean (design.md section 5) — none of these belong near it.
QUOTA_TERM = re.compile(
    r"quota|cuota|per[_-]?user|per[_-]?usuario|daily[_-]?limit|"
    r"generation[_-]?count|usage[_-]?count|contador|rate[_-]?limit",
    re.IGNORECASE,
)


def _hits(sources: list[Path]) -> list[str]:
    found: list[str] = []
    for source in sources:
        for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
            if QUOTA_TERM.search(line):
                found.append(f"{source}:{number}: {line.strip()}")
    return found


def test_the_quota_pattern_detects_what_it_claims_to() -> None:
    for banned in (
        "user_quota = 3",
        "self.generation_count += 1",
        "if per_user_limit_reached(user_id):",
        "cuota_diaria = 5",
    ):
        assert QUOTA_TERM.search(banned), banned
    assert not QUOTA_TERM.search("def is_generation_enabled(self) -> bool:")
    assert not QUOTA_TERM.search("targets.remaining_category_counts")


def test_the_worker_use_case_holds_no_per_user_quota() -> None:
    """R19, R20."""
    assert WORKER_USE_CASE.is_file(), WORKER_USE_CASE
    assert _hits([WORKER_USE_CASE]) == []


def test_planner_ai_holds_no_per_user_quota() -> None:
    """R19, R20 — the whole worker package."""
    assert PLANNER_AI_SRC.is_dir(), PLANNER_AI_SRC
    sources = sorted(PLANNER_AI_SRC.rglob("*.py"))
    assert sources, PLANNER_AI_SRC
    assert _hits(sources) == []
