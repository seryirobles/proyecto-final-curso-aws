"""CLI tests for planner_api.provision_admin against moto (feature 37, G-96)."""

from __future__ import annotations

import ast
import io
import logging
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

import pytest
from planner_api import provision_admin
from planner_api.adapters.dynamo import _table
from planner_api.adapters.dynamo.accounts import DynamoAccountRepository
from planner_core.application.authentication import authenticate
from planner_core.domain.role import Role
from planner_core.domain.session_policy import SessionExpired
from planner_core.ports.accounts import AccountRecord
from planner_core.ports.clock import SystemClock
from planner_core.ports.password_hasher import Pbkdf2PasswordHasher
from planner_core.ports.tokens import HmacTokenSigner
from support.fakes import FakeClock

_BASE = ["--env", "dev", "--table", "data", "--username"]
_PROD = ["--env", "prod", "--table", "data", "--username", "root"]
_STDIN_PW = "StdinPassw0rd!"


def _run(*argv: str, terminal: Any = None) -> int:
    if terminal is None:
        return provision_admin.main(list(argv))
    return provision_admin.main(list(argv), terminal=terminal)


def _tty(text: str) -> Any:
    return lambda: io.StringIO(text)


def _no_tty() -> TextIO:
    raise OSError("no tty")


def _items() -> list[dict[str, Any]]:
    return list(_table.table().scan()["Items"])


def _account(username: str) -> AccountRecord | None:
    return DynamoAccountRepository().get_by_username(username)


def _user(user_id: str, username: str) -> AccountRecord:
    return AccountRecord(user_id, username, Role.USER, "h", False, datetime(2026, 1, 1, tzinfo=UTC))


def test_create_writes_a_pending_admin_and_exits_zero() -> None:
    """R1, R2, R3, R4, R11 (both items present after the one transaction)."""
    before = datetime.now(UTC)

    assert _run("create", *_BASE, "root") == 0

    account = _account("root")
    assert account is not None
    assert (account.role, account.password_reset_required) == (Role.ADMIN, True)
    assert account.credentials_valid_since >= before
    assert {i["SK"] for i in _items()} == {f"ID#{account.user_id}", "NOMBRE#root"}


def test_create_rerun_is_a_no_op(capsys: pytest.CaptureFixture[str]) -> None:
    """R8."""
    _run("create", *_BASE, "root")
    snapshot = _items()
    capsys.readouterr()

    assert _run("create", *_BASE, "ROOT") == 0

    assert "exists, unchanged" in capsys.readouterr().out
    assert _items() == snapshot


def test_create_refuses_a_user_holding_the_name() -> None:
    """R9."""
    DynamoAccountRepository().create(_user("u1", "Ana"))
    snapshot = _items()

    assert _run("create", *_BASE, "ana") != 0
    assert _items() == snapshot


def test_create_refuses_the_placeholder_name() -> None:
    """R10."""
    assert _run("create", *_BASE, "Usuario Desconocido") != 0
    assert _items() == []


def test_generated_password_is_printed_once_and_works(
    capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
) -> None:
    """R12, R15, R18, R19."""
    with caplog.at_level(logging.DEBUG):
        assert _run("create", *_BASE, "root") == 0

    captured = capsys.readouterr()
    found = re.findall(r"shown once\): (\S+)", captured.out)
    assert len(found) == 1
    password = found[0]
    assert len(password) >= 24
    assert captured.out.count(password) == 1 and password not in captured.err
    assert password not in caplog.text
    account = _account("root")
    assert account is not None
    assert Pbkdf2PasswordHasher().verify(password, account.password_hash)
    assert password not in repr(_items())


def test_stdin_password_is_used_and_never_echoed(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """R13, R16, R18, R19."""
    monkeypatch.setattr(sys, "stdin", io.StringIO(_STDIN_PW + "\nignored\n"))

    with caplog.at_level(logging.DEBUG):
        assert _run("create", *_BASE, "root", "--password-stdin") == 0

    captured = capsys.readouterr()
    assert _STDIN_PW not in captured.out + captured.err + caplog.text
    account = _account("root")
    assert account is not None
    assert Pbkdf2PasswordHasher().verify(_STDIN_PW, account.password_hash)
    assert _STDIN_PW not in repr(_items())


def test_short_stdin_password_writes_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """R14."""
    monkeypatch.setattr(sys, "stdin", io.StringIO("short\n"))

    assert _run("create", *_BASE, "root", "--password-stdin") != 0
    assert _items() == []


def test_password_argument_is_rejected() -> None:
    """R17."""
    with pytest.raises(SystemExit) as exc:
        _run("create", *_BASE, "root", "--password", "foo")
    assert exc.value.code == 2


def test_reset_rotates_the_admin_and_ends_old_sessions() -> None:
    """R20, R24, R25."""
    _run("create", *_BASE, "root")
    first = _account("root")
    assert first is not None
    signer = HmacTokenSigner(b"k" * 32)
    token = signer.issue(first.user_id, first.credentials_valid_since)
    accounts = DynamoAccountRepository()
    clock = FakeClock(first.credentials_valid_since)
    authenticate(token, accounts=accounts, signer=signer, clock=clock)

    assert _run("reset", *_BASE, "root") == 0

    after = _account("root")
    assert after is not None
    assert after.password_hash != first.password_hash and after.password_reset_required
    with pytest.raises(SessionExpired):
        authenticate(token, accounts=accounts, signer=signer, clock=clock)


def test_reset_refuses_a_user_and_a_missing_name() -> None:
    """R22, R23."""
    DynamoAccountRepository().create(_user("u1", "Ana"))
    snapshot = _items()

    assert _run("reset", *_BASE, "Ana") != 0
    assert _run("reset", *_BASE, "ghost") != 0
    assert _items() == snapshot


def test_table_name_derived_from_env_and_overridable(monkeypatch: pytest.MonkeyPatch) -> None:
    """R26, R27."""
    monkeypatch.setenv("PLANNER_DATA_TABLE", "x")
    assert provision_admin.table_name("stg") == "lab-final-srobles-stg-data"
    assert provision_admin.table_name("stg", "mine") == "mine"
    _run("create", "--env", "stg", "--table", "mine", "--username", "root")
    assert os.environ["PLANNER_DATA_TABLE"] == "mine"


def test_unknown_env_is_a_usage_error_before_any_write() -> None:
    """R28."""
    with pytest.raises(SystemExit) as exc:
        _run("create", "--env", "qa", "--username", "root")
    assert exc.value.code == 2
    assert _items() == []


def test_prod_confirmation_right_name_proceeds_with_stdin_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R29 — with --password-stdin the prompt still goes to the terminal."""
    monkeypatch.setattr(sys, "stdin", io.StringIO(_STDIN_PW + "\n"))

    code = _run("create", *_PROD, "--password-stdin", terminal=_tty("prod\n"))

    assert code == 0
    assert _account("root") is not None


def test_prod_wrong_confirmation_writes_nothing() -> None:
    """R30."""
    assert _run("create", *_PROD, terminal=_tty("stg\n")) != 0
    assert _items() == []


def test_prod_without_a_terminal_writes_nothing(capsys: pytest.CaptureFixture[str]) -> None:
    """R35."""
    assert _run("create", *_PROD, terminal=_no_tty) != 0
    assert "terminal" in capsys.readouterr().err
    assert _items() == []


def test_no_handler_or_route_imports_provision_admin() -> None:
    """R33."""
    root = Path(provision_admin.__file__).parent
    offenders = []
    for path in root.rglob("*.py"):
        if path.name == "provision_admin.py":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or "", *(a.name for a in node.names)]
            else:
                continue
            if any("provision_admin" in n for n in names):
                offenders.append(path.name)
    assert offenders == []


def test_seed_creates_its_admins_through_bootstrap_admin() -> None:
    """R34 — active admin1 ends non-pending, pending admin2 stays pending; rerun is safe."""
    from planner_api import seed_local_data as seed

    accounts = DynamoAccountRepository()
    hasher = Pbkdf2PasswordHasher()
    clock = SystemClock()
    admins = [a for a in seed._ACCOUNTS if a.role is Role.ADMIN]
    for _ in range(2):
        for a in admins:
            seed._seed_account(a, accounts=accounts, hasher=hasher, clock=clock)

    assert not hasattr(seed, "_create_admin")
    active, pending = (accounts.get_by_id(a.user_id) for a in admins)
    assert active is not None and active.role is Role.ADMIN and not active.password_reset_required
    assert pending is not None and pending.password_reset_required
