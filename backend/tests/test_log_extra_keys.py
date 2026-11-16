"""No `extra=` key collides with what the JSON log format writes itself, or with a
LogRecord attribute, which raises at the log call."""

from __future__ import annotations

import ast
import logging
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
_LOG_METHODS = {"debug", "info", "warning", "error", "exception", "critical", "log"}
# docs: lambda/latest/dg/python-logging.html, the JSON format's own keys.
_JSON_KEYS = {
    "timestamp",
    "level",
    "message",
    "logger",
    "requestId",
    "stackTrace",
    "errorType",
    "errorMessage",
    "location",
}
_RECORD_ATTRIBUTES = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}


def _extra_arguments() -> list[ast.expr]:
    found: list[ast.expr] = []
    for source in sorted(_BACKEND.glob("*/src/**/*.py")):
        for node in ast.walk(ast.parse(source.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in _LOG_METHODS
            ):
                found.extend(kw.value for kw in node.keywords if kw.arg == "extra")
    return found


def _literal_keys() -> set[str]:
    keys: set[str] = set()
    for extra in _extra_arguments():
        assert isinstance(extra, ast.Dict), f"extra must be a literal dict, line {extra.lineno}"
        for key in extra.keys:
            assert isinstance(key, ast.Constant), f"extra key must be literal, line {extra.lineno}"
            keys.add(str(key.value))
    return keys


def test_the_scan_finds_the_known_keys() -> None:
    """E8 - guards the scan itself: a miss would make the next test vacuous."""
    assert {"method", "resource", "status", "weekId", "idPeticionIA"} <= _literal_keys()


def test_no_extra_key_collides_with_the_json_format_or_the_log_record() -> None:
    """E8."""
    assert _literal_keys() & (_JSON_KEYS | _RECORD_ATTRIBUTES) == set()
