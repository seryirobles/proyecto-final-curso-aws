"""`docker_dynamodb` fixture: opt-in DynamoDB Local backend for the
`@pytest.mark.docker` tier (docs/verification.md "Test tiers"). Not
`conftest.py` (mypy collision); scope rationale: docs/local_development.md."""

from __future__ import annotations

import os
import socket
from urllib.parse import urlsplit

import pytest
from botocore.config import Config

DEFAULT_ENDPOINT = "http://localhost:8000"


def _reachable(endpoint: str) -> bool:
    parts = urlsplit(endpoint)
    try:
        with socket.create_connection((parts.hostname, parts.port), timeout=1.5):
            return True
    except (OSError, TypeError):
        return False


@pytest.fixture
def docker_dynamodb(monkeypatch: pytest.MonkeyPatch) -> None:
    endpoint = os.environ.get("DYNAMODB_ENDPOINT_URL", DEFAULT_ENDPOINT)
    if not _reachable(endpoint):
        pytest.skip("DynamoDB Local not running - `docker compose up -d`")

    monkeypatch.setenv("DYNAMODB_ENDPOINT_URL", endpoint)
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "local")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "local")
    monkeypatch.setenv("SESSION_SECRET_KEY", "docker-tier-test-secret")
    monkeypatch.setenv("GENERATION_QUEUE_URL", "http://local-fake-queue")

    # _table module-level state is frozen at first import, which happens
    # during collection - patch it directly instead of relying on env (see
    # docs/local_development.md and _table.py lines 20-32).
    from planner_api.adapters.dynamo import _table

    monkeypatch.setattr(_table, "_ENDPOINT_URL", endpoint)
    monkeypatch.setattr(
        _table, "_CONFIG", Config(connect_timeout=2, read_timeout=2, retries={"max_attempts": 1})
    )

    _table.create_data_table()
