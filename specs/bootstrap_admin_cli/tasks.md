# bootstrap_admin_cli — Tasks

> Feature 37. Order matters; each step ends green (`./init.sh`) before the next.

- [x] **T1** Port: add `AccountAlreadyExists`, `NotAnAdmin`, `AccountRepository.reset_admin_credentials`; extend `FakeAccountRepository` (id collision, reset). _R6, R21, R22_
- [x] **T2** Use cases `bootstrap_admin`, `reset_admin_password`, `BootstrapOutcome` in `account_admin.py`; unit tests (fake repo), incl. `create_user` stays User-only and core imports no AWS SDK. _R2, R3, R4, R8, R9, R10, R20, R22, R23, R31, R32_
- [x] **T3** Adapter: make `DynamoAccountRepository.create` create-only with per-item cancellation reason mapping; contract tests for id collision, folded-name collision, no overwrite. _R5, R6, R7_
- [x] **T4** Adapter: `reset_admin_credentials` with `attribute_exists(SK) AND tipo = ADMIN`; contract tests (User refused, missing, session revoked via `authenticate`). _R20, R21, R22, R23, R24_
- [x] **T5** `provision_admin.py`: argparse (`create|reset`, `--env`, `--username`, `--table`, `--password-stdin`), table binding before lazy adapter import, exit codes. _R1, R11, R25, R26, R27, R28_
- [x] **T6** Password handling: generation, stdin read and length check, single print, no logging, no argv option, hash-only persistence; tests capturing stdout/stderr/`caplog` and scanning stored items. _R12, R13, R14, R15, R16, R17, R18, R19_
- [x] **T7** Prod confirmation read from the controlling terminal (injectable opener; refuse when none), and refusal paths; CLI tests with a fake tty incl. prod + `--password-stdin`, plus create no-op rerun, User clash, placeholder name, reset refusals. _R8, R9, R10, R29, R30, R35_
- [x] **T8** Import-boundary test (no handler/route imports `provision_admin`) and `seed_local_data` admin branch via `bootstrap_admin`; existing seed tests stay green. _R33, R34_
- [x] **T9** Add one short section to `docs/local_development.md` §4 (usage, `AWS_PROFILE`, `--password-stdin`, prod terminal confirmation; update the sentence saying admins are written directly via the repository). _R34_
- [x] **T10** Run `./init.sh`; log the result in `progress/current.md`. _all_
