# Issue 22 — Lambda context taken as injected dependencies

**Classification:** defect. No `G-xx` covers it; no architecture §2 item needed.

**Defect:** all four entry points alias `lambda_handler = handle`. AWS calls
`handler(event, context)`, so the `LambdaContext` lands in the `deps` slot;
`deps or build_…()` keeps it because it is truthy; the first dependency access
raises `AttributeError`.

**Reproduction** (local, with a context-shaped object):
- api `POST /v1/session`: 500 `INTERNAL_ERROR`, AttributeError `accounts`.
- authorizer: raises AttributeError `accounts` (`authorizer.py:62`).
- rollover: raises AttributeError `clock` (`scheduled.py:27`).
- ai: returns None; every record logged "Failed to process SQS record" and dropped.

**Root cause** (alias line / `or` line): `planner_api/handler.py` 113 / 77;
`authorizer.py` 77 / 59; `scheduled.py` 44 / 26; `planner_ai/handler.py` 123 / 115.
The alias is the cause; `or` instead of `is None` also discards a falsy injected
bundle. Introduced in a805aa5 (2026-09-06) and 1944822 (2026-09-07).

**Why it escaped:** ~66 test calls use `handle(event, deps)`, none `lambda_handler`;
`local_server.py` / `local_worker.py` call `handle` directly; with the staged tests
mypy reports 6 `arg-type` errors (it catches the bug once a typed caller exists);
no test ties the handler strings in `terraform/locals.tf` to code.

**Other `or` defaults:** `wiring.py:96,130` `config or EnvConfig()` has the same
shape but is harmless. Dependencies are rebuilt per invocation, which costs little
(secret cached per container, `secrets.py:13`; boto3 objects per operation,
`_table.py:49-59`).

**Blast radius:** all four deployed functions, every invocation.

**Designs compared:** (1) thin `lambda_handler(event, context)` wrappers + `is not None`
(recommended); (2) shared decorator — rejected, `planner_api`/`planner_ai` only share
`core`, which must not know the Lambda transport (architecture.md §3.1); (3)
module-level cached bundle — rejected, little gain, adds global state and a test
reset hook; (4) build deps in the wrapper, `deps` required — rejected, a wiring
failure becomes an unhandled 502 and the authorizer fetches the secret with no cookie.
Optional hardening: keyword-only `deps` (`handle(event, *, deps=None)`), touching ~66
call sites in ~20 test files plus `local_server.py` / `local_worker.py`.

**Suspected separate issues (not widened here):** S1 header-name case
(`Cookie`, `If-None-Match`) may 401 every protected route behind CloudFront/HTTP2;
S2 IAM role created outside Terraform, grants unverifiable from the repo; S3 AI
queue `ReportBatchItemFailures` vs a handler returning None; S4 boto3 client per call.
