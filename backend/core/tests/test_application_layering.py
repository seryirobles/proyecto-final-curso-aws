"""Source/signature scans for feature 27's use cases: `planner_core` imports no
AWS SDK and no Lambda package (R5), and every use-case signature holds only
ports and plain values — no HTTP, event or AWS type (R30).

Negative claims about a set of modules, so only a scan proves them. Built to the
discipline of `test_ports_are_storage_agnostic.py`.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import re
import typing
from collections.abc import Callable
from pathlib import Path

CORE_SRC = Path(__file__).resolve().parent.parent / "src" / "planner_core"

BANNED_IMPORT = re.compile(r"\bboto3\b|\bbotocore\b|\bplanner_api\b|\bplanner_ai\b")

USE_CASE_MODULES = (
    "planner_core.application.week_editing",
    "planner_core.application.library_editing",
    "planner_core.application.shopping_editing",
    "planner_core.application.rule_editing",
    "planner_core.application.generation_submission",
)

# Top-level modules a use-case signature may draw a type from: planner_core
# itself, plus a short stdlib set for plain values.
ALLOWED_ANNOTATION_ROOTS = frozenset(
    {"builtins", "planner_core", "datetime", "collections", "typing"}
)


def _imports(module: Path) -> set[str]:
    tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names.add(node.module)
    return names


def test_the_banned_import_pattern_detects_what_it_claims_to() -> None:
    for banned in (
        "import boto3",
        "from botocore.exceptions import X",
        "import planner_api.wiring",
    ):
        assert BANNED_IMPORT.search(banned), banned
    assert not BANNED_IMPORT.search("from planner_core.ports.weeks import WeekRepository")


def test_planner_core_imports_no_aws_sdk_and_no_lambda_package() -> None:
    """R5."""
    sources = sorted(CORE_SRC.rglob("*.py"))
    assert CORE_SRC / "application" / "generation_submission.py" in sources
    offenders = [
        f"{path.name}: {name}"
        for path in sources
        for name in _imports(path)
        if BANNED_IMPORT.search(name)
    ]
    assert offenders == []


def _annotation_types(func: Callable[..., object]) -> list[type]:
    hints = typing.get_type_hints(func)
    found: list[type] = []
    for hint in hints.values():
        found.extend(_flatten(hint))
    return found


def _flatten(hint: object) -> list[type]:
    origin = typing.get_origin(hint)
    if origin is None:
        return [hint] if isinstance(hint, type) else []
    out: list[type] = []
    for arg in typing.get_args(hint):
        out.extend(_flatten(arg))
    return out


def test_use_case_signatures_hold_only_ports_and_plain_values() -> None:
    """R30: every public use-case parameter/return type comes from planner_core
    or the small plain-value stdlib set."""
    offenders: list[str] = []
    for module_name in USE_CASE_MODULES:
        module = importlib.import_module(module_name)
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if func.__module__ != module_name or name.startswith("_"):
                continue
            for annotated in _annotation_types(func):
                if annotated.__module__.split(".")[0] not in ALLOWED_ANNOTATION_ROOTS:
                    offenders.append(
                        f"{module_name}.{name}: {annotated!r} from {annotated.__module__}"
                    )
    assert offenders == []
