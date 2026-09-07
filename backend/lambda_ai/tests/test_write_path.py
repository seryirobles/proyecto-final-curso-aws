"""R7: a generated whole-week candidate is persisted only through the
WeekRepository port. A negative claim about a set of modules — only a scan
proves it (specs/ai_lambda/design.md section 12)."""

from __future__ import annotations

import re
from pathlib import Path

_AI_SRC = Path(__file__).resolve().parents[1] / "src" / "planner_ai"
_DYNAMO = _AI_SRC / "adapters" / "dynamo"
_WEEK_ADAPTER = _DYNAMO / "weeks.py"
_WORKER_USE_CASE = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "src"
    / "planner_core"
    / "application"
    / "week_generation.py"
)

_RAW_WRITE = re.compile(r"put_item|update_item|transact_write|batch_writer")
_WEEK_KEY = re.compile(r"SEMANA#")


def test_the_patterns_detect_what_they_claim_to() -> None:
    assert _RAW_WRITE.search("table.put_item(")
    assert _WEEK_KEY.search('f"SEMANA#{week.week_id}"')
    assert not _RAW_WRITE.search("weeks.save_slot(week, slot, contents)")


def test_the_worker_use_case_makes_no_raw_persistence_call() -> None:
    """week_generation.py orchestrates ports only — no DynamoDB verb, no week key."""
    assert _WORKER_USE_CASE.is_file(), _WORKER_USE_CASE
    body = _WORKER_USE_CASE.read_text(encoding="utf-8")
    assert not _RAW_WRITE.search(body)
    assert not _WEEK_KEY.search(body)


def test_only_the_dynamo_adapters_issue_raw_writes_in_planner_ai() -> None:
    offenders = [
        f"{path.name}:{number}: {line.strip()}"
        for path in sorted(_AI_SRC.rglob("*.py"))
        if _DYNAMO not in path.parents
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if _RAW_WRITE.search(line)
    ]
    assert offenders == []


def test_the_week_key_is_named_only_by_the_week_adapter() -> None:
    assert _WEEK_ADAPTER.is_file(), _WEEK_ADAPTER
    offenders = [
        path.name
        for path in sorted(_AI_SRC.rglob("*.py"))
        if path != _WEEK_ADAPTER and _WEEK_KEY.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []
