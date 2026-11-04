"""Contract suite for AccountRepository: one suite, run against the in-memory
fake and the moto-backed DynamoDB adapter (docs/architecture.md section 3.2)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from planner_core.domain.role import Role
from planner_core.domain.username_policy import UsernameAlreadyTaken
from planner_core.ports.accounts import (
    AccountAlreadyExists,
    AccountNotFound,
    AccountRecord,
    AccountRepository,
)
from support.fakes import FakeAccountRepository

from tests.contract.dynamo_contract import dynamo_account_repository

IMPLEMENTATIONS: list[Callable[[], AccountRepository]] = [
    FakeAccountRepository,
    dynamo_account_repository,
]

VALID_SINCE = datetime(2026, 1, 1, tzinfo=UTC)


def _record(user_id: str, username: str) -> AccountRecord:
    return AccountRecord(
        user_id=user_id,
        username=username,
        role=Role.USER,
        password_hash="hash",
        password_reset_required=True,
        credentials_valid_since=VALID_SINCE,
    )


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_create_then_get_by_id_and_get_by_username_round_trip(
    repository_factory: Callable[[], AccountRepository],
) -> None:
    repo = repository_factory()
    account = _record("u1", "Ana Perez")

    repo.create(account)

    assert repo.get_by_id("u1") == account
    assert repo.get_by_username("ana perez") == account


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_create_raises_username_already_taken_on_folded_collision(
    repository_factory: Callable[[], AccountRepository],
) -> None:
    repo = repository_factory()
    repo.create(_record("u1", "Ana"))

    with pytest.raises(UsernameAlreadyTaken):
        repo.create(_record("u2", "ana"))


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_rename_releases_the_old_reservation(
    repository_factory: Callable[[], AccountRepository],
) -> None:
    repo = repository_factory()
    repo.create(_record("u1", "Ana"))

    repo.rename("u1", "Beatriz")

    assert repo.get_by_username("ana") is None
    repo.create(_record("u2", "Ana"))
    assert repo.get_by_id("u2") is not None

    # The account row itself carries the new name — pins the `#nombreUsuario`
    # alias target in the adapter's rename Update (docs/data_model.md 5.2).
    renamed = repo.get_by_id("u1")
    assert renamed is not None and renamed.username == "Beatriz"
    assert repo.get_by_username("beatriz") == renamed


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_update_credentials_round_trip(repository_factory: Callable[[], AccountRepository]) -> None:
    repo = repository_factory()
    repo.create(_record("u1", "Ana"))
    new_valid_since = datetime(2026, 2, 1, tzinfo=UTC)

    repo.update_credentials("u1", "new-hash", False, new_valid_since)

    updated = repo.get_by_id("u1")
    assert updated is not None
    assert updated.password_hash == "new-hash"
    assert updated.password_reset_required is False
    assert updated.credentials_valid_since == new_valid_since


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_revoke_credentials_sets_valido_desde(
    repository_factory: Callable[[], AccountRepository],
) -> None:
    repo = repository_factory()
    repo.create(_record("u1", "Ana"))
    revoked_at = datetime(2026, 3, 1, tzinfo=UTC)

    repo.revoke_credentials("u1", revoked_at)

    updated = repo.get_by_id("u1")
    assert updated is not None
    assert updated.credentials_valid_since == revoked_at


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_delete_removes_the_account(repository_factory: Callable[[], AccountRepository]) -> None:
    repo = repository_factory()
    repo.create(_record("u1", "Ana"))

    repo.delete("u1")

    assert repo.get_by_id("u1") is None


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_operations_on_a_missing_user_raise_account_not_found(
    repository_factory: Callable[[], AccountRepository],
) -> None:
    repo = repository_factory()

    with pytest.raises(AccountNotFound):
        repo.rename("missing", "Nueva")
    with pytest.raises(AccountNotFound):
        repo.update_credentials("missing", "hash", False, VALID_SINCE)
    with pytest.raises(AccountNotFound):
        repo.delete("missing")
    with pytest.raises(AccountNotFound):
        repo.revoke_credentials("missing", VALID_SINCE)


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_create_with_a_taken_id_raises_and_keeps_the_first_record(
    repository_factory: Callable[[], AccountRepository],
) -> None:
    """R6."""
    repo = repository_factory()
    first = _record("u1", "Ana")
    repo.create(first)

    with pytest.raises(AccountAlreadyExists):
        repo.create(_record("u1", "Beatriz"))

    assert repo.get_by_id("u1") == first
    assert repo.get_by_username("beatriz") is None
    assert len(repo.list_all()) == 1


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_create_folded_name_collision_leaves_everything_unchanged(
    repository_factory: Callable[[], AccountRepository],
) -> None:
    """R7 — also when the id collides too, the name conflict wins."""
    repo = repository_factory()
    first = _record("u1", "Ana")
    repo.create(first)

    with pytest.raises(UsernameAlreadyTaken):
        repo.create(_record("u2", " ANA"))
    with pytest.raises(UsernameAlreadyTaken):
        repo.create(_record("u1", "ana"))

    assert repo.list_all() == (first,)
    assert repo.get_by_username("ana") == first


def _admin(user_id: str, username: str) -> AccountRecord:
    return AccountRecord(
        user_id=user_id,
        username=username,
        role=Role.ADMIN,
        password_hash="old",
        password_reset_required=False,
        credentials_valid_since=VALID_SINCE,
    )


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_reset_admin_credentials_sets_hash_pending_and_marker(
    repository_factory: Callable[[], AccountRepository],
) -> None:
    """R20, R24 (the marker advance is what authenticate checks)."""
    repo = repository_factory()
    repo.create(_admin("a1", "root"))
    later = datetime(2026, 6, 1, tzinfo=UTC)

    repo.reset_admin_credentials("a1", "new", later)

    after = repo.get_by_id("a1")
    assert after is not None
    assert (after.password_hash, after.password_reset_required) == ("new", True)
    assert after.credentials_valid_since == later
    assert after.role is Role.ADMIN


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_reset_admin_credentials_refuses_a_user_and_a_missing_id(
    repository_factory: Callable[[], AccountRepository],
) -> None:
    """R21, R22, R23."""
    repo = repository_factory()
    user = _record("u1", "Ana")
    repo.create(user)

    with pytest.raises(AccountNotFound):
        repo.reset_admin_credentials("u1", "new", VALID_SINCE)
    with pytest.raises(AccountNotFound):
        repo.reset_admin_credentials("missing", "new", VALID_SINCE)

    assert repo.get_by_id("u1") == user
    assert repo.get_by_id("missing") is None
