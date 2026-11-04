"""Operator CLI: create the first Admin of an environment, or reset one's
password (G-96, feature 37). Not a handler: run it under your own AWS
credentials, `python -m planner_api.provision_admin create|reset --env dev`."""

from __future__ import annotations

import argparse
import os
import secrets
import sys
import uuid
from collections.abc import Callable
from typing import TextIO

from planner_core.application.account_admin import (
    BootstrapOutcome,
    bootstrap_admin,
    reset_admin_password,
)
from planner_core.domain.errors import PlannerError
from planner_core.domain.password_policy import validate_password
from planner_core.ports.clock import SystemClock
from planner_core.ports.password_hasher import Pbkdf2PasswordHasher

_ENVS = ("dev", "stg", "prod")


def _say(text: str, *, err: bool = False, end: str = "\n") -> None:
    # A repo test bans the builtin print in src; this is the operator's console.
    stream = sys.stderr if err else sys.stdout
    stream.write(text + end)
    stream.flush()


def table_name(env: str, override: str | None = None) -> str:
    return override if override else f"lab-final-srobles-{env}-data"


def open_terminal() -> TextIO:
    """The controlling terminal, never stdin (R29); OSError when there is none."""
    return open("CONIN$" if sys.platform == "win32" else "/dev/tty", encoding="utf-8")


def _confirm_prod(opener: Callable[[], TextIO]) -> bool:
    try:
        terminal = opener()
    except OSError:
        _say("error: --env prod needs a controlling terminal; none is available", err=True)
        return False
    with terminal:
        _say("Type the environment name (prod) to confirm: ", err=True, end="")
        typed = terminal.readline().strip()
    if typed != "prod":
        _say("error: confirmation did not match; nothing written", err=True)
        return False
    return True


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="provision_admin", description=__doc__)
    parser.add_argument("command", choices=("create", "reset"))
    parser.add_argument("--env", required=True, choices=_ENVS)
    parser.add_argument("--username", required=True)
    parser.add_argument("--table", help="Table name, in place of the one derived from --env.")
    parser.add_argument(
        "--password-stdin",
        action="store_true",
        help="Read the password from the first line of stdin instead of generating one.",
    )
    return parser


def main(argv: list[str] | None = None, *, terminal: Callable[[], TextIO] = open_terminal) -> int:
    args = _parser().parse_args(argv)  # usage errors exit 2 before any AWS call (R28)

    if args.env == "prod" and not _confirm_prod(terminal):
        return 1

    generated = not args.password_stdin
    password = secrets.token_urlsafe(18) if generated else sys.stdin.readline().rstrip("\r\n")
    if not generated:
        try:
            validate_password(password)
        except PlannerError:
            _say("error: password from stdin is too short; nothing written", err=True)
            return 1
    password_hash = Pbkdf2PasswordHasher().hash(password)

    # _table reads this at import, so bind it before the adapter import (R26, R27).
    os.environ["PLANNER_DATA_TABLE"] = table_name(args.env, args.table)
    from planner_api.adapters.dynamo.accounts import DynamoAccountRepository

    accounts = DynamoAccountRepository()
    clock = SystemClock()
    try:
        if args.command == "create":
            outcome = bootstrap_admin(
                uuid.uuid4().hex, args.username, password_hash, accounts=accounts, clock=clock
            )
            if outcome is BootstrapOutcome.UNCHANGED:
                _say(f"Admin '{args.username}' exists, unchanged")
                return 0
            done = f"Admin '{args.username}' created"
        else:
            reset_admin_password(args.username, password_hash, accounts=accounts, clock=clock)
            done = f"Admin '{args.username}' password reset"
    except PlannerError as exc:
        _say(f"error: {type(exc).__name__} for '{args.username}'; nothing written", err=True)
        return 1

    _say(done)
    if generated:
        _say(f"Temporary password (shown once): {password}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
