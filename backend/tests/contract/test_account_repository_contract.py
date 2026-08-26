"""Contract suite for AccountRepository: one suite, run against every registered
implementation (R9). Today: the fake alone; a real adapter appends its factory
later (design.md section 5)."""

from __future__ import annotations

import pytest
from planner_core.domain.username_policy import UsernameAlreadyTaken
from planner_core.ports.accounts import AccountNotFound, AccountRecord
from support.fakes import FakeAccountRepository

IMPLEMENTATIONS = [FakeAccountRepository]


def _record(user_id: str, username: str) -> AccountRecord:
    return AccountRecord(
        user_id=user_id,
        username=username,
        role="member",
        password_hash="hash",
        password_reset_required=True,
    )


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_create_then_get_by_id_and_get_by_username_round_trip(
    repository_factory: type[FakeAccountRepository],
) -> None:
    repo = repository_factory()
    account = _record("u1", "Ana Perez")

    repo.create(account)

    assert repo.get_by_id("u1") == account
    assert repo.get_by_username("ana perez") == account


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_create_raises_username_already_taken_on_folded_collision(
    repository_factory: type[FakeAccountRepository],
) -> None:
    repo = repository_factory()
    repo.create(_record("u1", "Ana"))

    with pytest.raises(UsernameAlreadyTaken):
        repo.create(_record("u2", "ana"))


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_rename_releases_the_old_reservation(
    repository_factory: type[FakeAccountRepository],
) -> None:
    repo = repository_factory()
    repo.create(_record("u1", "Ana"))

    repo.rename("u1", "Beatriz")

    assert repo.get_by_username("ana") is None
    repo.create(_record("u2", "Ana"))
    assert repo.get_by_id("u2") is not None


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_update_credentials_round_trip(repository_factory: type[FakeAccountRepository]) -> None:
    repo = repository_factory()
    repo.create(_record("u1", "Ana"))

    repo.update_credentials("u1", "new-hash", False)

    updated = repo.get_by_id("u1")
    assert updated is not None
    assert updated.password_hash == "new-hash"
    assert updated.password_reset_required is False


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_delete_removes_the_account(repository_factory: type[FakeAccountRepository]) -> None:
    repo = repository_factory()
    repo.create(_record("u1", "Ana"))

    repo.delete("u1")

    assert repo.get_by_id("u1") is None


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_operations_on_a_missing_user_raise_account_not_found(
    repository_factory: type[FakeAccountRepository],
) -> None:
    repo = repository_factory()

    with pytest.raises(AccountNotFound):
        repo.rename("missing", "Nueva")
    with pytest.raises(AccountNotFound):
        repo.update_credentials("missing", "hash", False)
    with pytest.raises(AccountNotFound):
        repo.delete("missing")
