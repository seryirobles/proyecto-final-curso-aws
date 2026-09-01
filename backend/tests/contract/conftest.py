"""sys.path wiring so contract tests can `from support.fakes import ...`, plus
the moto-backed AWS the real adapters run against (design.md section 9).

`backend/core/tests/conftest.py` puts `backend/core/tests` on `sys.path` only
for files pytest collects under that directory; `backend/tests/contract` is a
different tree (design.md section 6). `tests.contract.dynamo_contract` lives
here, not under `support/`, because it imports the AWS SDK, moto and planner_api
and must stay out of the planner-core member's test tree.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

_CORE_TESTS = Path(__file__).resolve().parents[2] / "core" / "tests"
if str(_CORE_TESTS) not in sys.path:
    sys.path.insert(0, str(_CORE_TESTS))


@pytest.fixture(autouse=True)
def _aws_backend() -> Iterator[None]:
    """Every contract test runs inside a fresh mocked AWS: the fake-backed
    parametrisations ignore it, the adapter-backed ones need it."""
    from tests.contract.dynamo_contract import aws_backend

    with aws_backend():
        yield
