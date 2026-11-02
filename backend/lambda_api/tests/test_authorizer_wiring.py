"""The authorizer wires only accounts, signer and clock; see
issues/authorizer-builds-full-dependency-graph/plan.md."""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

from planner_api import authorizer

_METHOD_ARN = "arn:aws:execute-api:eu-west-1:123:abc/prod/GET/v1/weeks/2026-W33"


def test_authorizer_denies_a_bad_token_without_a_generation_queue_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """E1 — reproduction: today build_dependencies() raises KeyError here."""
    monkeypatch.delenv("GENERATION_QUEUE_URL", raising=False)
    monkeypatch.delenv("SESSION_SECRET_ARN", raising=False)
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret-key")
    event = {"methodArn": _METHOD_ARN, "headers": {"Cookie": "session=not-a-token"}}

    result = authorizer.handle(event)

    assert result["policyDocument"]["Statement"][0]["Effect"] == "Deny"


def test_importing_and_running_the_authorizer_never_loads_the_sqs_adapter() -> None:
    """E2 — fresh interpreter, so other tests' imports cannot hide it."""
    env = {k: v for k, v in os.environ.items() if k != "GENERATION_QUEUE_URL"}
    env.pop("SESSION_SECRET_ARN", None)
    env["SESSION_SECRET_KEY"] = "test-secret-key"
    script = (
        "import sys\n"
        "from planner_api import authorizer\n"
        "event = {'methodArn': 'arn:x', 'headers': {'Cookie': 'session=bad'}}\n"
        "authorizer.handle(event)\n"
        "print('planner_api.adapters.sqs' in sys.modules)\n"
    )
    done = subprocess.run(
        [sys.executable, "-c", script], env=env, capture_output=True, text=True, check=False
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "False"
