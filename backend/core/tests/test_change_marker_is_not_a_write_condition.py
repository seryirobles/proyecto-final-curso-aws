"""Source scans for the change marker (FR-RT-01): R7 and R12.

Both are negative claims about a set of modules, so no call site can prove
them — only a scan can. Built to the discipline of
`test_ports_are_storage_agnostic.py`: exhaustive over the modules it claims to
cover, with its own patterns checked against known-good and known-bad lines
first (design.md section 6).

R7 — no mutating port method accepts a caller-supplied expected-marker value,
so the marker can never become a `ConditionExpression` (G-88).
R12 — the marker name stays inside the four port modules; no other
`planner_core` module and no Lambda `src` module references it.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parent
CORE_SRC = TESTS_ROOT.parent / "src" / "planner_core"
BACKEND_ROOT = TESTS_ROOT.parent.parent

PORT_MODULES = (
    CORE_SRC / "ports" / "weeks.py",
    CORE_SRC / "ports" / "recipes.py",
    CORE_SRC / "ports" / "rules.py",
    CORE_SRC / "ports" / "shopping_list.py",
)

LAMBDA_SRC_ROOTS = (
    BACKEND_ROOT / "lambda_api" / "src",
    BACKEND_ROOT / "lambda_ai" / "src",
)

# Names that would let a caller pin the write to an expected marker value
# (design.md section 6). `current_version` is here so a parameter named after
# the read method is caught too — the read method itself is exempted below.
EXPECTED_VERSION_DENYLIST = frozenset(
    {
        "version",
        "expected_version",
        "current_version",
        "if_version",
        "expected_marca",
        "marca_cambio",
        "expected",
    }
)

MARKER_NAME = re.compile(r"\bmarca|\bchange_marker|\bcurrent_version\b")


def _method_param_names(method: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Every parameter name of a method except `self`."""
    args = method.args
    names = [
        arg.arg for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs) if arg.arg != "self"
    ]
    if args.vararg is not None:
        names.append(args.vararg.arg)
    if args.kwarg is not None:
        names.append(args.kwarg.arg)
    return names


def _expected_version_offenders(source: str, label: str) -> list[str]:
    """Report every `*Repository` method parameter that could carry an expected
    marker. `current_version` may take only `week` (design.md section 6)."""
    offenders: list[str] = []
    methods_seen = 0
    tree = ast.parse(source, filename=label)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or not node.name.endswith("Repository"):
            continue
        for method in node.body:
            if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            methods_seen += 1
            params = _method_param_names(method)
            if method.name == "current_version":
                if set(params) - {"week"}:
                    offenders.append(f"{label}:{node.name}.current_version params {params}")
                continue
            for name in params:
                if name in EXPECTED_VERSION_DENYLIST:
                    offenders.append(f"{label}:{node.name}.{method.name} param {name!r}")
    if methods_seen == 0:
        offenders.append(f"{label}: no *Repository methods found")
    return offenders


def _marker_hits(sources: list[Path]) -> list[tuple[Path, str]]:
    hits: list[tuple[Path, str]] = []
    for source in sources:
        for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
            if MARKER_NAME.search(line):
                hits.append((source, f"{source.name}:{number}: {line.strip()}"))
    return hits


def test_the_expected_version_scan_catches_a_planted_parameter() -> None:
    """A scan that flags nothing proves nothing: check it against mutants first —
    one on a mutating method, one widening `current_version` itself, so the
    scan's own `- {"week"}` exemption cannot be loosened without this test."""
    mutant = "class FooRepository:\n    def save(self, entry, expected_version: int) -> int: ...\n"
    assert _expected_version_offenders(mutant, "<mutant>")

    widened_read = (
        "class FooRepository:\n    def current_version(self, week, expected_version) -> int: ...\n"
    )
    assert _expected_version_offenders(widened_read, "<widened-read>")

    clean = (
        "class FooRepository:\n"
        "    def current_version(self, week) -> int: ...\n"
        "    def save(self, entry) -> int: ...\n"
    )
    assert _expected_version_offenders(clean, "<clean>") == []


def test_no_mutating_port_method_accepts_an_expected_version() -> None:
    """R7: the marker is never a write precondition — no port method takes one."""
    offenders: list[str] = []
    for module in PORT_MODULES:
        assert module.is_file(), module
        offenders += _expected_version_offenders(module.read_text(encoding="utf-8"), str(module))
    assert offenders == []


def test_the_marker_name_pattern_detects_what_it_claims_to() -> None:
    """A scan that matches nothing proves nothing: check the pattern first."""
    for hit in ("repo.current_version()", "def current_version(self)", "bump marcaCambio"):
        assert MARKER_NAME.search(hit), hit

    assert not MARKER_NAME.search("from planner_core.domain.recipe import Recipe")
    assert not MARKER_NAME.search("    def save(self, entry: LibraryRecipe) -> int: ...")


def test_the_change_marker_stays_inside_the_four_port_modules() -> None:
    """R12: no `planner_core` module outside the four ports, and no Lambda `src`
    module, references the marker."""
    scanned = sorted(CORE_SRC.rglob("*.py"))
    for root in LAMBDA_SRC_ROOTS:
        assert root.is_dir(), root
        scanned += sorted(root.rglob("*.py"))

    assert CORE_SRC / "application" / "live_weeks.py" in scanned
    permitted = set(PORT_MODULES)
    offenders = [detail for path, detail in _marker_hits(scanned) if path not in permitted]
    assert offenders == []
