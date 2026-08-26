"""Tests for the AccountRepository port and its in-memory fake."""

from __future__ import annotations

import dataclasses

import pytest
from support.fakes import FakeAccountRepository

from planner_core.domain.username_policy import UsernameAlreadyTaken
from planner_core.ports.accounts import AccountNotFound, AccountRecord, AccountRepository


def _record(user_id: str, username: str) -> AccountRecord:
    return AccountRecord(
        user_id=user_id,
        username=username,
        role="member",
        password_hash="hash",
        password_reset_required=True,
    )


def test_account_record_is_frozen() -> None:
    """docs/conventions.md: every new frozen dataclass gets this test."""
    record = _record("u1", "Ana")
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.__setattr__("username", "Otra")


def test_fake_account_repository_satisfies_the_account_repository_port() -> None:
    assert isinstance(FakeAccountRepository(), AccountRepository)


def test_create_then_get_by_id_and_get_by_username_round_trip_with_fold() -> None:
    repo = FakeAccountRepository()
    account = _record("u1", "Ana Perez")
    repo.create(account)

    assert repo.get_by_id("u1") == account
    assert repo.get_by_username("ana perez") == account
    assert repo.get_by_username(" ANA PEREZ ") == account


def test_get_by_id_and_get_by_username_return_none_when_absent() -> None:
    repo = FakeAccountRepository()
    assert repo.get_by_id("missing") is None
    assert repo.get_by_username("nadie") is None


def test_list_all_returns_every_account() -> None:
    repo = FakeAccountRepository()
    repo.create(_record("u1", "Ana"))
    repo.create(_record("u2", "Beto"))
    assert set(repo.list_all()) == {_record("u1", "Ana"), _record("u2", "Beto")}


def test_create_raises_username_already_taken_on_folded_collision() -> None:
    repo = FakeAccountRepository()
    repo.create(_record("u1", "Ana"))
    with pytest.raises(UsernameAlreadyTaken):
        repo.create(_record("u2", "ana"))


def test_rename_releases_the_old_reservation_and_reserves_the_new_one() -> None:
    repo = FakeAccountRepository()
    repo.create(_record("u1", "Ana"))

    repo.rename("u1", "Beatriz")

    renamed = repo.get_by_id("u1")
    assert renamed is not None
    assert renamed.username == "Beatriz"
    assert repo.get_by_username("ana") is None
    assert repo.get_by_username("beatriz") is not None
    # The old name's reservation was released, so it can be taken again.
    repo.create(_record("u2", "Ana"))
    assert repo.get_by_id("u2") is not None


def test_rename_raises_account_not_found_for_a_missing_user() -> None:
    repo = FakeAccountRepository()
    with pytest.raises(AccountNotFound):
        repo.rename("missing", "Nueva")


def test_rename_raises_username_already_taken_when_the_new_name_collides() -> None:
    repo = FakeAccountRepository()
    repo.create(_record("u1", "Ana"))
    repo.create(_record("u2", "Beatriz"))
    with pytest.raises(UsernameAlreadyTaken):
        repo.rename("u1", "beatriz")


def test_update_credentials_round_trip() -> None:
    repo = FakeAccountRepository()
    repo.create(_record("u1", "Ana"))

    repo.update_credentials("u1", "new-hash", False)

    updated = repo.get_by_id("u1")
    assert updated is not None
    assert updated.password_hash == "new-hash"
    assert updated.password_reset_required is False


def test_update_credentials_raises_account_not_found_for_a_missing_user() -> None:
    repo = FakeAccountRepository()
    with pytest.raises(AccountNotFound):
        repo.update_credentials("missing", "hash", False)


def test_delete_removes_the_account_and_releases_its_reservation() -> None:
    repo = FakeAccountRepository()
    repo.create(_record("u1", "Ana"))

    repo.delete("u1")

    assert repo.get_by_id("u1") is None
    assert repo.get_by_username("ana") is None
    # The reservation was released, so the name is available again.
    repo.create(_record("u2", "Ana"))
    assert repo.get_by_id("u2") is not None


def test_delete_raises_account_not_found_for_a_missing_user() -> None:
    repo = FakeAccountRepository()
    with pytest.raises(AccountNotFound):
        repo.delete("missing")
