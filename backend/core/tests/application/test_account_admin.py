"""Tests for admin account management (FR-AUTH-03, -05, -07, -12, -13, -18)."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime

import pytest
from support.fakes import FakeAccountRepository, FakeClock, FakeRecipeRepository

import planner_core.application.account_admin as account_admin
import planner_core.application.authentication as authentication
from planner_core.application.account_admin import (
    admin_set_password,
    create_user,
    list_accounts,
    remove_user,
    rename_user,
)
from planner_core.domain.authorization import Forbidden
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Recipe
from planner_core.domain.role import Role
from planner_core.domain.username_policy import UsernameAlreadyTaken
from planner_core.ports.accounts import AccountRecord
from planner_core.ports.recipes import LibraryRecipe

CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def _account(
    *,
    user_id: str = "u1",
    username: str = "Ana",
    role: Role = Role.USER,
) -> AccountRecord:
    return AccountRecord(
        user_id=user_id,
        username=username,
        role=role,
        password_hash="hash",
        password_reset_required=False,
        credentials_valid_since=CREATED_AT,
    )


def test_create_user_by_non_admin_raises_forbidden() -> None:
    """R7."""
    accounts = FakeAccountRepository()
    clock = FakeClock.at("2026-01-02T00:00:00+00:00")

    with pytest.raises(Forbidden):
        create_user(Role.USER, "u1", "Nueva", "hash", accounts=accounts, clock=clock)


def test_create_user_never_accepts_an_admin_role() -> None:
    """R9."""
    assert "role" not in inspect.signature(create_user).parameters


def test_account_admin_exposes_no_self_registration_operation() -> None:
    """R6 — the module's public surface has exactly the five admin-gated
    operations design.md section 1 names; no account-creation entry point
    exists that a caller could reach without supplying an actor_role."""
    own_functions = {
        name
        for name, member in inspect.getmembers(account_admin, inspect.isfunction)
        if member.__module__ == account_admin.__name__ and not name.startswith("_")
    }
    assert own_functions == {
        "create_user",
        "rename_user",
        "admin_set_password",
        "remove_user",
        "list_accounts",
    }
    assert "actor_role" in inspect.signature(create_user).parameters


def test_create_user_rejects_a_taken_username() -> None:
    """R8."""
    accounts = FakeAccountRepository()
    accounts.create(_account())
    clock = FakeClock.at("2026-01-02T00:00:00+00:00")

    with pytest.raises(UsernameAlreadyTaken):
        create_user(Role.ADMIN, "u2", "ana", "hash", accounts=accounts, clock=clock)


def test_create_user_sets_password_reset_required_true() -> None:
    """R11."""
    accounts = FakeAccountRepository()
    clock = FakeClock.at("2026-01-02T00:00:00+00:00")

    created = create_user(Role.ADMIN, "u1", "Nueva", "hash", accounts=accounts, clock=clock)

    assert created.password_reset_required is True
    assert created.role is Role.USER
    assert accounts.get_by_id("u1") == created


def test_rename_user_by_non_admin_raises_forbidden() -> None:
    """R7."""
    accounts = FakeAccountRepository()
    accounts.create(_account())

    with pytest.raises(Forbidden):
        rename_user(Role.USER, "u1", "Beatriz", accounts=accounts)


def test_admin_set_password_sets_pending_flag_and_advances_the_marker() -> None:
    """R18, R19."""
    accounts = FakeAccountRepository()
    target = _account(user_id="u2")
    accounts.create(target)
    clock = FakeClock.at("2026-02-01T00:00:00+00:00")

    admin_set_password(
        Role.ADMIN, "admin-1", target, "new-temp-hash", accounts=accounts, clock=clock
    )

    updated = accounts.get_by_id("u2")
    assert updated is not None
    assert updated.password_hash == "new-temp-hash"
    assert updated.password_reset_required is True
    assert updated.credentials_valid_since == clock.instant


def test_admin_set_password_on_another_admin_is_permitted() -> None:
    """R29."""
    accounts = FakeAccountRepository()
    target = _account(user_id="u2", role=Role.ADMIN)
    accounts.create(target)
    clock = FakeClock.at("2026-02-01T00:00:00+00:00")

    admin_set_password(
        Role.ADMIN, "admin-1", target, "new-temp-hash", accounts=accounts, clock=clock
    )

    updated = accounts.get_by_id("u2")
    assert updated is not None
    assert updated.password_hash == "new-temp-hash"


def test_admin_set_password_authorizes_any_admin_actor_identically() -> None:
    """R10 — FR-AUTH-07: authorization keys off Role.ADMIN alone, so a second,
    distinct admin account is authorized for the same operation exactly like
    the first, with no per-admin distinction anywhere in the guard."""
    accounts = FakeAccountRepository()
    target = _account(user_id="u2")
    accounts.create(target)
    clock = FakeClock.at("2026-02-01T00:00:00+00:00")

    admin_set_password(Role.ADMIN, "admin-1", target, "hash-a", accounts=accounts, clock=clock)
    after_first = accounts.get_by_id("u2")
    assert after_first is not None

    admin_set_password(Role.ADMIN, "admin-2", after_first, "hash-b", accounts=accounts, clock=clock)
    after_second = accounts.get_by_id("u2")

    assert after_first.password_hash == "hash-a"
    assert after_second is not None
    assert after_second.password_hash == "hash-b"


def test_authentication_exposes_no_self_service_password_change_operation() -> None:
    """R13 — the only password-changing operation is the mandatory
    set-password step; no separate self-service change-password op exists
    for an already-authenticated account."""
    own_functions = {
        name
        for name, member in inspect.getmembers(authentication, inspect.isfunction)
        if member.__module__ == authentication.__name__ and not name.startswith("_")
    }
    assert own_functions == {
        "login",
        "authenticate",
        "logout",
        "set_password",
        "require_password_set",
    }


def test_admin_set_password_on_self_raises_forbidden() -> None:
    """R30."""
    accounts = FakeAccountRepository()
    target = _account(user_id="admin-1", role=Role.ADMIN)
    accounts.create(target)
    clock = FakeClock.at("2026-02-01T00:00:00+00:00")

    with pytest.raises(Forbidden):
        admin_set_password(
            Role.ADMIN, "admin-1", target, "new-temp-hash", accounts=accounts, clock=clock
        )


def test_remove_user_deletes_the_account_and_calls_no_content_repository() -> None:
    """R21, R22 — a pre-populated content repository, untouched by the call:
    remove_user's signature has no content-repository parameter to pass one
    through, so nothing it authored can be reached, let alone deleted."""
    accounts = FakeAccountRepository()
    target = _account(user_id="u2")
    accounts.create(target)
    content_repository = FakeRecipeRepository()
    content_repository.save(
        LibraryRecipe(
            id="r1",
            recipe=Recipe(
                name="Lentejas",
                ingredients=(),
                tools=(),
                procedure=(),
                category=IngredientCategory.LEGUME,
            ),
            author="u2",
        )
    )
    entries_before = dict(content_repository.entries)

    remove_user(Role.ADMIN, target, accounts=accounts)

    assert accounts.get_by_id("u2") is None
    assert content_repository.entries == entries_before


def test_remove_user_on_an_admin_account_raises_forbidden() -> None:
    """R31."""
    accounts = FakeAccountRepository()
    target = _account(user_id="u2", role=Role.ADMIN)
    accounts.create(target)

    with pytest.raises(Forbidden):
        remove_user(Role.ADMIN, target, accounts=accounts)

    assert accounts.get_by_id("u2") is not None


def test_list_accounts_by_non_admin_raises_forbidden() -> None:
    """R20."""
    accounts = FakeAccountRepository()

    with pytest.raises(Forbidden):
        list_accounts(Role.USER, accounts=accounts)


def test_list_accounts_returns_username_role_and_pending_status() -> None:
    """R20."""
    accounts = FakeAccountRepository()
    accounts.create(_account(user_id="u1", username="Ana"))
    accounts.create(_account(user_id="u2", username="Beto", role=Role.ADMIN))

    listed = list_accounts(Role.ADMIN, accounts=accounts)

    assert {(a.username, a.role, a.password_reset_required) for a in listed} == {
        ("Ana", Role.USER, False),
        ("Beto", Role.ADMIN, False),
    }
