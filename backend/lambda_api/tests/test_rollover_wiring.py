"""The rollover wires only weeks, shopping, archive and clock; same style as
test_authorizer_wiring.py (issue authorizer-builds-full-dependency-graph)."""

from __future__ import annotations

import os
import subprocess
import sys


def test_rollover_wiring_needs_no_queue_or_secret_and_loads_neither_adapter() -> None:
    """Fresh interpreter, so other tests' imports cannot hide a load."""
    drop = {"GENERATION_QUEUE_URL", "SESSION_SECRET_ARN", "SESSION_SECRET_KEY"}
    env = {k: v for k, v in os.environ.items() if k not in drop}
    script = (
        "import sys\n"
        "from planner_api import scheduled, wiring\n"
        "deps = wiring.build_rollover_dependencies()\n"
        "assert deps.clock is not None and deps.archive is not None\n"
        "print('planner_api.adapters.sqs' in sys.modules,"
        " 'planner_api.adapters.secrets' in sys.modules)\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", script], env=env, capture_output=True, text=True, check=False
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "False False"
