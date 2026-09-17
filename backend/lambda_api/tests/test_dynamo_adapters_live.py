"""Real-adapter round trip against DynamoDB Local (docs/verification.md
"Docker (local)" tier) - proves the wiring against actual wire behaviour,
which moto can diverge from subtly."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from _docker_fixtures import docker_dynamodb as docker_dynamodb  # re-exported fixture
from planner_core.domain.role import Role
from planner_core.ports.accounts import AccountRecord

from planner_api.adapters.dynamo import _table
from planner_api.adapters.dynamo.accounts import DynamoAccountRepository

pytestmark = pytest.mark.docker

VALID_SINCE = datetime(2026, 1, 1, tzinfo=UTC)

# Captured at collection time, before any fixture runs - the pre-patch
# baseline the reviewer's leak-fix regression test below pins against.
_ORIGINAL_ENDPOINT_URL = _table._ENDPOINT_URL
_ORIGINAL_CONFIG = _table._CONFIG


def _record(user_id: str, username: str) -> AccountRecord:
    return AccountRecord(
        user_id=user_id,
        username=username,
        role=Role.USER,
        password_hash="hash",
        password_reset_required=True,
        credentials_valid_since=VALID_SINCE,
    )


def test_create_then_get_by_id_and_get_by_username_round_trip(docker_dynamodb: None) -> None:
    # Unique per run - the container is long-lived (-inMemory clears on
    # restart only), so a fixed id/username would collide across runs.
    suffix = uuid.uuid4().hex
    repo = DynamoAccountRepository()
    account = _record(f"u-{suffix}", f"Ana Perez {suffix}")

    repo.create(account)

    assert repo.get_by_id(f"u-{suffix}") == account
    assert repo.get_by_username(f"ana perez {suffix}") == account


def test_docker_dynamodb_patches_the_table_endpoint(docker_dynamodb: None) -> None:
    """While the fixture is active, `_table` must point at DynamoDB Local."""
    assert _table._ENDPOINT_URL != _ORIGINAL_ENDPOINT_URL


def test_docker_dynamodb_reverts_the_table_endpoint_after_teardown() -> None:
    """No fixture requested - runs after the test above and proves function
    scope actually undoes the patch instead of leaking it into the next
    moto-backed contract test (docs/local_development.md)."""
    assert _table._ENDPOINT_URL == _ORIGINAL_ENDPOINT_URL
    assert _table._CONFIG is _ORIGINAL_CONFIG
