"""sys.path wiring so contract tests can `from support.fakes import ...`.

`backend/core/tests/conftest.py` puts `backend/core/tests` on `sys.path` only
for files pytest collects under that directory; `backend/tests/contract` is a
different tree (design.md section 6).
"""

from __future__ import annotations

import sys
from pathlib import Path

_CORE_TESTS = Path(__file__).resolve().parents[2] / "core" / "tests"
if str(_CORE_TESTS) not in sys.path:
    sys.path.insert(0, str(_CORE_TESTS))
