# bootstrap_admin_cli — Requirements

> Feature 37 · tier 5 · `sdd: true`
> Covers: `FR-AUTH-07`, `FR-AUTH-08`, `FR-AUTH-18`
> Notation: strict EARS (`docs/specs.md`). Exactly one `SHALL` per `R<n>`
> (counted mechanically). Decision record: `G-96` (Part AF).

## Purpose in one sentence

An operator-run CLI creates the first Admin once per environment (create-only,
no-op on rerun) and rotates an existing Admin's credential (`reset`), under the
operator's own AWS credentials, with the password shown once and never stored.

## Scope note — `FR-AUTH-10` and `FR-AUTH-11` are cited though absent from `covers`

`FR-AUTH-08` (amended) says a re-seeded credential is temporary per
`FR-AUTH-11` and reaches only the set-password step of `FR-AUTH-10`; R3, R4
and R19 pin exactly that and cite them. No requirement is added.

## Create

**R1** — When `create` runs for a username that no account holds, the CLI SHALL write the `ID#` and `NOMBRE#` items in one `TransactWriteItems`.
Implements: FR-AUTH-07

**R2** — The account written by `create` SHALL have `tipo` equal to `ADMIN`.
Implements: FR-AUTH-07, FR-AUTH-18

**R3** — The account written by `create` SHALL have `isPassReseteada` equal to `true`.
Implements: FR-AUTH-08, FR-AUTH-10, FR-AUTH-11

**R4** — The account written by `create` SHALL have `validoDesde` equal to the time of the write.
Implements: FR-AUTH-11

**R5** — The `create` transaction SHALL guard both Put legs with `attribute_not_exists(SK)`.
Implements: FR-AUTH-07

**R6** — When an `ID#` item with the same id already exists, `DynamoAccountRepository.create` SHALL raise `AccountAlreadyExists` and leave every existing item unchanged.
Implements: FR-AUTH-07

**R7** — When the folded `NOMBRE#` reservation already exists, `DynamoAccountRepository.create` SHALL raise `UsernameAlreadyTaken` and leave every existing item unchanged.
Implements: FR-AUTH-07

**R8** — When `create` runs for a username already held by an Admin, the CLI SHALL exit 0, print "exists, unchanged" and write nothing.
Implements: FR-AUTH-07

**R9** — When `create` runs for a username held by a non-Admin account, the CLI SHALL exit non-zero and write nothing.
Implements: FR-AUTH-18

**R10** — When `create` runs for the reserved placeholder name, the CLI SHALL exit non-zero and write nothing.
Implements: FR-AUTH-07

**R11** — When `create` succeeds, the CLI SHALL exit 0.
Implements: FR-AUTH-07

## Password handling (create and reset)

**R12** — Where `--password-stdin` is absent, the CLI SHALL generate the password with `secrets.token_urlsafe(18)` in memory.
Implements: FR-AUTH-08, FR-AUTH-11

**R13** — Where `--password-stdin` is present, the CLI SHALL read the password from the first line of standard input.
Implements: FR-AUTH-08

**R14** — When a password read from standard input is shorter than `password_policy.MIN_LENGTH`, the CLI SHALL exit non-zero and write nothing.
Implements: FR-AUTH-08, FR-AUTH-11

**R15** — When the CLI generated the password and the write succeeded, the CLI SHALL print it to standard output exactly once.
Implements: FR-AUTH-08

**R16** — Where `--password-stdin` is present, the CLI SHALL NOT print the password.
Implements: FR-AUTH-08

**R17** — The CLI SHALL NOT accept the password as a command-line argument.
Implements: FR-AUTH-08

**R18** — The CLI SHALL NOT write the password to any log record.
Implements: FR-AUTH-08

**R19** — The CLI SHALL persist only the PBKDF2 hash of the password, in no item attribute in plaintext.
Implements: FR-AUTH-08, FR-AUTH-11

## Reset

**R20** — When `reset` runs for an existing Admin, the CLI SHALL set `passHash`, `isPassReseteada` (`true`) and `validoDesde` (the time of the write) in one `UpdateItem`.
Implements: FR-AUTH-08, FR-AUTH-11

**R21** — The `reset` `UpdateItem` SHALL carry the condition `attribute_exists(SK) AND tipo = ADMIN`.
Implements: FR-AUTH-08, FR-AUTH-18

**R22** — When `reset` targets a non-Admin account, the CLI SHALL exit non-zero and leave the account unchanged.
Implements: FR-AUTH-18

**R23** — When `reset` targets a username no account holds, the CLI SHALL exit non-zero and write nothing.
Implements: FR-AUTH-08

**R24** — When `reset` completes, `authenticate` SHALL reject a token issued before the reset.
Implements: FR-AUTH-08, FR-AUTH-11

**R25** — When `reset` succeeds, the CLI SHALL exit 0.
Implements: FR-AUTH-08

## Target and safety

**R26** — The CLI SHALL derive its table name as `lab-final-srobles-<env>-data` from `--env`.
Implements: FR-AUTH-07

**R27** — Where `--table` is present, the CLI SHALL use its value as the table name in place of the derived one.
Implements: FR-AUTH-07

**R28** — If `--env` is not one of `dev`, `stg` or `prod`, then the CLI SHALL exit with a usage error before any AWS call.
Implements: FR-AUTH-07

**R29** — Where `--env` is `prod`, the CLI SHALL read the typed env name from the controlling terminal, never from standard input, before any write.
Implements: FR-AUTH-18

**R30** — If the prod confirmation does not equal `prod`, then the CLI SHALL exit non-zero and write nothing.
Implements: FR-AUTH-18

**R35** — If `--env` is `prod` and no controlling terminal is available, then the CLI SHALL exit non-zero with an error naming the missing terminal and write nothing.
Implements: FR-AUTH-18

## Boundaries

**R31** — The `bootstrap_admin` and `reset_admin_password` use cases SHALL take no actor role, in `planner_core.application`, importing no AWS SDK.
Implements: FR-AUTH-18

**R32** — `create_user` SHALL continue to create only `Role.USER` accounts.
Implements: FR-AUTH-18

**R33** — No Lambda handler or route module SHALL import `planner_api.provision_admin`.
Implements: FR-AUTH-18

**R34** — The local seed script SHALL create its Admin accounts through `bootstrap_admin`.
Implements: FR-AUTH-07, FR-AUTH-18

## Traceability to acceptance criteria

| Acceptance criterion | R |
|---|---|
| Second create changes nothing, exits 0 | R8 |
| create never overwrites `ID#` / `NOMBRE#` | R5, R6, R7 |
| reset refuses non-Admin, ends sessions | R21, R22, R23, R24 |
| Password never in argv, logs or stored item | R17, R18, R19 |
