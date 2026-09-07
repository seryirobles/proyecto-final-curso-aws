"""Source scans for the persistence and hand-off ports: no storage-technology
leakage (R7), no AWS SDK import anywhere this feature touches (R10).

R7 and R10 are negative claims about a whole set of modules, so no single call
site can prove either — only a scan of the sources can. Built to the same
discipline as `test_no_ambient_time.py`: exhaustive over the modules it claims
to cover, and its own patterns are checked against known-good and known-bad
lines first.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parent
CORE_SRC = TESTS_ROOT.parent / "src" / "planner_core"
BACKEND_ROOT = TESTS_ROOT.parent.parent
CONTRACT_TESTS = BACKEND_ROOT / "tests" / "contract"

PORT_MODULES = (
    CORE_SRC / "ports" / "accounts.py",
    CORE_SRC / "ports" / "recipes.py",
    CORE_SRC / "ports" / "weeks.py",
    CORE_SRC / "ports" / "rules.py",
    CORE_SRC / "ports" / "shopping_list.py",
    CORE_SRC / "ports" / "archive.py",
    CORE_SRC / "ports" / "generation_queue.py",
    CORE_SRC / "ports" / "ai_provider.py",
    CORE_SRC / "ports" / "generation_gate.py",
)
FAKES_MODULE = TESTS_ROOT / "support" / "fakes.py"

ALLOWED_TOP_LEVEL_MODULES = frozenset(sys.stdlib_module_names) | {"__future__", "planner_core"}

# Stdlib storage/persistence modules are technically "stdlib" but are exactly
# the leakage R7 forbids, so they are rejected regardless of allowlist membership.
DENYLIST_STORAGE_MODULES = frozenset({"sqlite3", "dbm", "shelve"})

# A port may import planner_core.domain/ports only (design.md section 2's
# ports row); planner_core.application or the bare package are out of scope.
ALLOWED_PLANNER_CORE_PREFIXES = ("planner_core.domain", "planner_core.ports")

AWS_SDK_NAME = re.compile(r"\bboto3\b|\bbotocore\b")


def _imported_module_names(module: Path) -> set[str]:
    """Every module a file imports, as the full dotted name — `x.y` for both
    `import x.y` and `from x.y import z` — not just its top-level segment."""
    tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                names.add(node.module)
    return names


def _top_level_imports(module: Path) -> set[str]:
    """Every top-level module name a file imports (the root of each dotted import)."""
    return {name.split(".")[0] for name in _imported_module_names(module)}


def test_the_aws_sdk_pattern_detects_what_it_claims_to() -> None:
    """A scan that matches nothing proves nothing: check the pattern first."""
    for banned in ("import boto3", "from botocore.exceptions import ClientError", "boto3.client"):
        assert AWS_SDK_NAME.search(banned), banned

    assert not AWS_SDK_NAME.search("from planner_core.domain.recipe import Recipe")
    assert not AWS_SDK_NAME.search("# no AWS SDK adapter belongs here")


def test_port_signatures_use_only_domain_and_stdlib_types() -> None:
    """R7: every port module imports only stdlib or sibling planner_core modules."""
    assert PORT_MODULES, "no port modules listed"
    for module in PORT_MODULES:
        assert module.is_file(), module
        full_names = _imported_module_names(module)

        offenders = {name.split(".")[0] for name in full_names} - ALLOWED_TOP_LEVEL_MODULES
        assert not offenders, f"{module} imports outside domain/stdlib: {offenders}"

        storage_offenders = {name.split(".")[0] for name in full_names} & DENYLIST_STORAGE_MODULES
        assert not storage_offenders, f"{module} imports a storage technology: {storage_offenders}"

        planner_core_offenders = {
            name
            for name in full_names
            if name.split(".")[0] == "planner_core"
            and not name.startswith(ALLOWED_PLANNER_CORE_PREFIXES)
        }
        assert not planner_core_offenders, (
            f"{module} imports planner_core outside domain/ports: {planner_core_offenders}"
        )


def test_no_aws_sdk_import() -> None:
    """R10: no port module, fake, or contract test names an AWS SDK.

    `dynamo_contract.py` is exempt: it is the deliberate moto/boto3 bridge that
    lets the real adapters run the fake-authored suites (design.md section 9)."""
    contract_files = (p for p in CONTRACT_TESTS.rglob("*.py") if p.name != "dynamo_contract.py")
    sources = [*PORT_MODULES, FAKES_MODULE, *sorted(contract_files)]
    assert FAKES_MODULE in sources
    assert any(path.name.endswith("_contract.py") or path.name == "conftest.py" for path in sources)

    offenders = [str(path) for path in sources if AWS_SDK_NAME.search(path.read_text("utf-8"))]
    assert offenders == []
