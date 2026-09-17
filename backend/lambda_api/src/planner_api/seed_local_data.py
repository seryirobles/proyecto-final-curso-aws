"""Dev-only tool: seeds local DynamoDB with 4 test accounts for manual app
testing (`docs/local_development.md`) — no `feature_list.json` entry, no spec,
same category as `local_server.py`. Run via
`uv run python -m planner_api.seed_local_data` from `backend/lambda_api/`."""

from __future__ import annotations

import argparse
import logging
import os
from dataclasses import dataclass

from planner_core.application.account_admin import create_user
from planner_core.application.authentication import set_password
from planner_core.domain.authentication_guards import SetPasswordNotPending
from planner_core.domain.role import Role
from planner_core.domain.username_policy import UsernameAlreadyTaken, validate_username
from planner_core.ports.accounts import AccountRecord
from planner_core.ports.clock import SystemClock
from planner_core.ports.password_hasher import Pbkdf2PasswordHasher

from planner_api.adapters.dynamo._table import create_data_table
from planner_api.adapters.dynamo.accounts import DynamoAccountRepository

logger = logging.getLogger("planner_api.seed_local_data")

# >= password_policy.MIN_LENGTH (10); create_user itself never validates the
# password it is handed (only set_password does), but every credential here
# stays real-policy-shaped anyway so none of these accounts is a bad example.
_TEMP_PASSWORD = "TempPass1234"


@dataclass(frozen=True)
class _SeedAccount:
    user_id: str
    username: str
    role: Role
    password_reset_required: bool
    password: str  # what the account can currently log in with


_ACCOUNTS = (
    _SeedAccount("user1", "user1", Role.USER, False, "UserActive1234"),
    _SeedAccount("user2", "user2", Role.USER, True, _TEMP_PASSWORD),
    _SeedAccount("admin1", "admin1", Role.ADMIN, False, "AdminActive1234"),
    _SeedAccount("admin2", "admin2", Role.ADMIN, True, _TEMP_PASSWORD),
)


def _create_admin(
    account: _SeedAccount,
    *,
    accounts: DynamoAccountRepository,
    hasher: Pbkdf2PasswordHasher,
    clock: SystemClock,
) -> None:
    # account_admin.create_user hardcodes role=Role.USER: an Admin-role account
    # can never be created through the application (R9, R31 — by construction,
    # design.md section 5). This mirrors what create_user does internally and
    # stands in for the "IaC re-seed" provisioning path it defers to
    # (architecture.md invariant 8), for local dev only.
    validate_username(account.username, (a.username for a in accounts.list_all()))
    # Unlike create_user (R11), nothing forces this record pending — so it is
    # built already in its target state, real password included, and needs no
    # follow-up set_password translation step.
    password = _TEMP_PASSWORD if account.password_reset_required else account.password
    accounts.create(
        AccountRecord(
            user_id=account.user_id,
            username=account.username,
            role=Role.ADMIN,
            password_hash=hasher.hash(password),
            password_reset_required=account.password_reset_required,
            credentials_valid_since=clock.now(),
        )
    )


def _reseed_active(
    account: _SeedAccount,
    *,
    accounts: DynamoAccountRepository,
    hasher: Pbkdf2PasswordHasher,
) -> str:
    """A prior run can die between creation and set_password, leaving an
    "-active" account stuck on the temp password. Retry set_password here;
    SetPasswordNotPending (not UsernameAlreadyTaken) is the real "done" signal."""
    if account.password_reset_required:
        return "already seeded"
    try:
        set_password(account.user_id, account.password, accounts=accounts, hasher=hasher)
    except SetPasswordNotPending:
        pass
    return "already seeded"


def _seed_account(
    account: _SeedAccount,
    *,
    accounts: DynamoAccountRepository,
    hasher: Pbkdf2PasswordHasher,
    clock: SystemClock,
) -> str:
    try:
        if account.role is Role.USER:
            create_user(
                Role.ADMIN,
                account.user_id,
                account.username,
                hasher.hash(_TEMP_PASSWORD),
                accounts=accounts,
                clock=clock,
            )
            # create_user hardcodes pending=True (R11) — translate to the
            # seed's target state here; _create_admin needs no such step.
            if not account.password_reset_required:
                set_password(account.user_id, account.password, accounts=accounts, hasher=hasher)
        else:
            _create_admin(account, accounts=accounts, hasher=hasher, clock=clock)
    except UsernameAlreadyTaken:
        return _reseed_active(account, accounts=accounts, hasher=hasher)

    return "created"


def _log_summary(results: list[tuple[_SeedAccount, str]]) -> None:
    logger.info("Seeded accounts:")
    for account, status in results:
        pending = "yes" if account.password_reset_required else "no"
        logger.info(
            "  username=%-20s role=%-5s reset_pending=%-3s password=%r  [%s]",
            account.username,
            account.role.value,
            pending,
            account.password,
            status,
        )


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow running without DYNAMODB_ENDPOINT_URL set (same as SEED_FORCE=1).",
    )
    args = parser.parse_args(argv)

    endpoint = os.environ.get("DYNAMODB_ENDPOINT_URL")
    forced = args.force or os.environ.get("SEED_FORCE") == "1"
    if not endpoint and not forced:
        logger.error(
            "Refusing to run: DYNAMODB_ENDPOINT_URL is not set, which risks "
            "writing fake test accounts into a real AWS table. Pass --force or "
            "set SEED_FORCE=1 to seed anyway."
        )
        return 1

    accounts_to_seed: tuple[_SeedAccount, ...] = _ACCOUNTS
    if not endpoint:
        logger.warning("DYNAMODB_ENDPOINT_URL is not set — seeding against real AWS.")
        # --force covers only the 2 User accounts: a real Admin account with a
        # hardcoded, documented password is never worth the convenience.
        logger.warning("Admin seeding is local-only — skipping the 2 Admin accounts.")
        accounts_to_seed = tuple(a for a in _ACCOUNTS if a.role is not Role.ADMIN)
    else:
        logger.info("Seeding local DynamoDB at %s", endpoint)

    create_data_table()
    accounts = DynamoAccountRepository()
    hasher = Pbkdf2PasswordHasher()
    clock = SystemClock()

    results: list[tuple[_SeedAccount, str]] = []
    for account in accounts_to_seed:
        status = _seed_account(account, accounts=accounts, hasher=hasher, clock=clock)
        results.append((account, status))

    _log_summary(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
