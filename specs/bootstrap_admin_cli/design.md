# bootstrap_admin_cli — Design

> Feature 37 · tier 5. Read `requirements.md` first. Binding decision:
> `docs/gaps_and_resolutions.md` Part AF / `G-96`. Terraform, CI and the
> per-environment state keys are out of scope (human-owned).

## 1. Files touched and layers (`docs/architecture.md` §3)

| File | Layer | Change |
|---|---|---|
| `backend/core/src/planner_core/application/account_admin.py` | core application | add `bootstrap_admin`, `reset_admin_password`, `BootstrapOutcome`; `create_user` untouched |
| `backend/core/src/planner_core/ports/accounts.py` | core port | add `AccountAlreadyExists`, `NotAnAdmin`; add `reset_admin_credentials` to `AccountRepository` |
| `backend/core/tests/support/fakes.py` | test support | `FakeAccountRepository`: `create` raises `AccountAlreadyExists` on a taken id; implement `reset_admin_credentials` |
| `backend/lambda_api/src/planner_api/adapters/dynamo/accounts.py` | adapter | `create` becomes create-only with per-item reason mapping; add `reset_admin_credentials` |
| `backend/lambda_api/src/planner_api/provision_admin.py` | operator tool (not a handler) | new CLI, `main(argv) -> int` |
| `backend/lambda_api/src/planner_api/seed_local_data.py` | dev tool | admins via `bootstrap_admin`; delete `_create_admin` |
| `docs/local_development.md` §4 | docs | one short section (T9) |

No new dependency. Core stays dependency-free (R31).

## 2. Use cases (core, no actor role: authority is IAM)

```python
class BootstrapOutcome(Enum): CREATED = "created"; UNCHANGED = "unchanged"

def bootstrap_admin(user_id: str, username: str, password_hash: str, *,
                    accounts: AccountRepository, clock: Clock) -> BootstrapOutcome
def reset_admin_password(username: str, new_password_hash: str, *,
                         accounts: AccountRepository, clock: Clock) -> None
```

`bootstrap_admin`: `existing = accounts.get_by_username(username)`; Admin ->
`UNCHANGED`; non-Admin -> `UsernameAlreadyTaken`. Else
`validate_username(username, names)` (placeholder reservation), then
`accounts.create(AccountRecord(role=ADMIN, password_reset_required=True,
credentials_valid_since=clock.now(), ...))`. Hash is computed by the caller, as
with `create_user`; the use case never sees plaintext.

`reset_admin_password`: `get_by_username`; `None` -> `AccountNotFound`;
non-Admin -> `NotAnAdmin`; else `accounts.reset_admin_credentials(id, hash,
clock.now())`. The pre-read gives the distinct messages; the adapter condition
(R21) closes the race.

Exceptions: `AccountAlreadyExists(user_id)`, `NotAnAdmin(username)` are
`PlannerError` subclasses in `ports/accounts.py` beside `AccountNotFound`.

## 3. Adapter

`create`: `_table.put_action(item)` plus `ConditionExpression:
attribute_not_exists(SK)` on the `ID#` leg (the `NOMBRE#` leg already has it).
On `TransactionCanceledException`, read `response["CancellationReasons"]`
(index 0 = `ID#`, 1 = `NOMBRE#`): leg 1 `ConditionalCheckFailed` ->
`UsernameAlreadyTaken` (wins when both fail); else leg 0 ->
`AccountAlreadyExists`; anything else re-raised. `rename` keeps its own mapper.

`reset_admin_credentials`: `UpdateItem SET passHash, isPassReseteada=true,
validoDesde` with `ConditionExpression: attribute_exists(SK) AND #tipo = :admin`;
`ConditionalCheckFailedException` -> `AccountNotFound` (the use case's pre-read
already told missing from non-Admin; a race between pre-read and write just
refuses). It does not reuse `update_credentials`, which has no role guard.

## 4. CLI (`provision_admin.py`)

`python -m planner_api.provision_admin create|reset --env dev|stg|prod
--username U [--table T] [--password-stdin]`.

- **Table binding.** `adapters/dynamo/_table.py` reads `PLANNER_DATA_TABLE` at
  import. `main` therefore sets `os.environ["PLANNER_DATA_TABLE"]` (R26/R27)
  *before* lazily importing the adapter; no `_table.py` change. Profile and
  region come from `AWS_PROFILE` / `AWS_DEFAULT_REGION`; `DYNAMODB_ENDPOINT_URL`
  is honoured as everywhere else (this is how tests and DynamoDB Local reach it).
- **Password.** Generated: `secrets.token_urlsafe(18)` (24 chars, above
  `MIN_LENGTH` 10). Stdin: `sys.stdin.readline().rstrip("\n")`, then
  `validate_password`. Hash with `Pbkdf2PasswordHasher`. Printed after a
  successful write only, one `print` to stdout; the module imports no `logging`
  and has no logger, so nothing can log it (R18). No `--password` option exists,
  so argparse rejects one with exit 2 (R17).
- **Prod confirmation.** Before any write, `--env prod` prompts for the env
  name on the controlling terminal (`open("/dev/tty")`, `open("CONIN$")` on
  Windows), so `--password-stdin` is unaffected. No `--confirm` flag exists.
  The terminal open failing (`OSError`) -> exit 1 with a "no terminal" error
  (R35); mismatch -> exit 1 (R30). The terminal opener is a small injectable
  function so tests can supply a fake tty.
- **Exit codes.** 0 created / unchanged / reset; 1 refusal (clash, non-Admin,
  missing target, short password, bad confirmation); 2 usage. Messages go to
  stderr (refusals) or stdout; they contain the username, never the password.
- **Bootstrap id.** `uuid.uuid4().hex`, the same generator `routing.py` uses
  for users. A fixed id (like `UNKNOWN_USER_ID = "unknown-user"`) was weighed
  and rejected below.

## 5. `seed_local_data`

Admin branch of `_seed_account` calls `bootstrap_admin` with the hash of
`_TEMP_PASSWORD` and the seed's fixed id (`admin1`/`admin2`, local only), then
`set_password` when the seed wants the account active, exactly like the User
branch. `UNCHANGED` goes to `_reseed_active`, as `UsernameAlreadyTaken` does
today. The real-AWS "skip admins" guard stays: the seed must never create a
real Admin with a documented password.

## 6. Tests (tiers per `docs/verification.md`)

- Unit (`backend/core/tests/application/test_account_admin.py`), fake repo:
  R2-R4, R8-R10, R20, R22-R23, R31, R32.
- Contract (`backend/tests/contract/test_account_repository_contract.py`, fake
  and moto): R5-R7 (id collision leaves the first record intact; folded-name
  collision), R21 (reset refuses a User, missing id), R24 (`reset`, then
  `authenticate` with a pre-reset token raises `SessionExpired`).
- CLI (`backend/tests/contract/test_provision_admin.py`, moto via
  `aws_backend()`): R1, R8, R11, R12-R19 (capture stdout/stderr/`caplog` and
  scan every stored item for the password; `--password foo` -> `SystemExit(2)`),
  R25-R30, R35 (fake tty: right name, wrong name, unavailable; prod with `--password-stdin` still prompts on the tty), R33 (AST scan of `planner_api` for imports of `provision_admin`).
- `seed_local_data` existing tests stay green (R34).

## 7. Rejected alternatives

1. **Fixed bootstrap id (e.g. `"admin"`, like `unknown-user`).** Gives
   idempotence from the `ID#` key alone, but the no-op case is decided by
   username anyway (R8), and a predictable id adds nothing for an account whose
   credentials are not id-derived. uuid4 matches every other account.
2. **Widen `update_credentials` with a role guard instead of a new port method.**
   Fewer methods, but every existing caller (`set_password`, `admin_set_password`)
   would pass a role they do not care about; a dedicated `reset_admin_credentials`
   keeps the Admin-only condition out of the shared path.
3. **`--password` flag (or env var) for scripted runs.** Simplest for CI, but it
   leaks into shell history, `ps` and process environments, violating `G-96`
   (2); `--password-stdin` covers scripting.
