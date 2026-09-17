# Verification — How to prove the work functions

> Golden rule: **the agent does not say "it works", it demonstrates it.**
> Every feature ends with executable evidence, not assertions.

## Level 1 — Quality gates (mandatory)

All four must be green before anything is `done`, run from the `backend/`
workspace root so every member is covered:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy .
uv run pytest -q          # default: unit + contract tiers, no AWS marker
```

`./init.sh` runs all of them. SonarQube runs in the project's quality pipeline
and is not an agent's responsibility to invoke.

The frontend has its **own** gate, over `frontend/` only — `prettier --check`,
`eslint` and `vitest run`, added by feature 1 `project_scaffold`. It has no
type-checking step: the SPA is plain JavaScript, so there is no `mypy`
counterpart by design (`docs/conventions.md` § *Frontend conventions*).

## Test tiers

The suite is tiered so "mock locally, real in AWS" is verifiable, not hopeful:

| Tier | Location | Touches AWS? | Runs in `init.sh`? |
|---|---|---|---|
| **Unit** | each member's `tests/` | No | Yes (default) |
| **Contract** | `backend/tests/contract/` | No — runs the port suite against the **fake** | Yes (default) |
| **Contract (live)** | same suite, marked `@pytest.mark.aws` | Yes — runs it against the **real adapter** | No — opt-in |
| **Docker (local)** | `backend/lambda_api/tests/`, marked `@pytest.mark.docker` | No — hits DynamoDB Local via Docker, not real AWS | No — opt-in |

- Live-AWS tests are marked `@pytest.mark.aws` and excluded from the default
  `pytest` run (registered in `pyproject.toml`, deselected via
  `-m "not aws and not docker"`).
- Docker-local tests are marked `@pytest.mark.docker`, excluded the same way
  (`-m "not aws and not docker"`), and prove the real adapter/HTTP wiring
  against actual DynamoDB Local wire behaviour, which moto can diverge from
  subtly. Run `docker compose up -d` then `uv run pytest -m docker`; they skip
  cleanly if the container isn't running.
- CI runs the AWS tier explicitly (`uv run pytest -m aws`) against real
  components, with credentials CI provides — never an agent, never `init.sh`.
- **The contract suite is one suite, two backends.** It is parametrized over
  every implementation of a port — the in-memory fake and the real adapter — so
  a green fake tier actually means the local stand-in is faithful. A port that
  has a fake but no live-contract run is only half-verified.

## Level 2 — Unit tests (mandatory)

Every public function in `backend/` has at least one test that:

1. Covers the happy path.
2. Covers at least one failure path, if the function can fail.

`core` tests must pass with **no AWS, no network, no filesystem** — only a fixed
clock and in-memory fakes. If a `core` test needs more than that, the code is in
the wrong layer (`docs/architecture.md` §3).

## Level 3 — Requirement traceability (mandatory for `"sdd": true`)

The chain `FR-* → R<n> → test` must be complete in both directions:

- Every `FR-*` in the feature's `covers` array appears in some `R<n>`.
- Every `R<n>` in `specs/<name>/requirements.md` maps to at least one concrete
  test in the relevant member's `tests/`.

The `implementer` records the map in `progress/impl_<name>.md`. The `reviewer`
verifies it and **rejects on any gap**.

## Level 4 — Invariant checks

Some requirements are behavioural properties, not single code paths. Where a
feature touches one of the invariants in `docs/architecture.md` §4, the tests
must exercise the property, not just the happy path:

| Invariant | What the test must actually show |
|---|---|
| Idempotency (`FR-AI-08`, `FR-SHOP-10`, `FR-MENU-08`) | Run the operation **twice**; assert the second run changes nothing. |
| Re-runnable after partial failure (`FR-MENU-08`, `G-61`) | Interrupt mid-sequence, re-run, assert no double-archive / double-cleanup. |
| Never undo the user's reality (`G-32`, `G-77`, `G-73`) | Check an item, force a recompute that raises the requirement above it, assert the checked item is **byte-for-byte untouched** and that a **new unchecked item** appears carrying the remainder — not the gross amount. |
| Additive bulk ops (`FR-AI-11`, `G-18`) | Pre-populate candidates and a definitive, generate, assert nothing was removed. |
| Snapshots (`FR-CAND-07`, `G-05`) | Add a recipe to a week, edit the library entry, assert the week is unchanged. |
| Normalised matching (`G-56`) | Assert `"Tomate"`, `"tomate "` and `"tomáte"` aggregate as one item. |

A test that only asserts "no exception was raised" does not count as coverage.

## Level 5 — Mutation testing (`reviewer`-owned)

Levels 1–4 prove a test **exists** and **runs**. They cannot prove it would
**notice**. A suite that asserts the code does what it does is green, traceable
and worthless.

**This level belongs to the `reviewer`, not the `implementer`.** It is the one
part of the pipeline that edits source deliberately: plant one small defect,
run the tests, require a failure, revert. The full procedure and its rules are
in `.claude/agents/reviewer.md` § *Mutation testing* — that file is the
authority, this section only says whose job it is and why the job exists.

Two consequences worth stating here:

- An `implementer` never runs mutation testing and is never asked to. Writing
  tests that survive it is their job; proving they do is not.
- A surviving mutant is `CHANGES_REQUESTED`, and the fix is a **new test** —
  never a change to the mutated line, which was reverted anyway.

## Anti-patterns (do not do)

- ❌ "I added the endpoint, it should work." → no executable test.
- ❌ A test that only checks the function does not raise. → assert the concrete result.
- ❌ `unittest.mock.patch` on our own code. → inject a fake through a port.
- ❌ Mocking `datetime.now()`. → inject a `Clock` port.
- ❌ A unit or default-tier test that requires AWS credentials or the network.
  (Live-AWS tests are allowed only in the opt-in `@pytest.mark.aws` tier.)
- ❌ Marking a feature `done` without `./init.sh` passing.
- ❌ Weakening or `# type: ignore`-ing a mypy error instead of fixing the type.

## Final check before closing

```bash
./init.sh      # must end with [OK] Environment ready
```

If `./init.sh` is red, **do not** mark anything `done`. Record the blocker in
`progress/current.md` and set the feature to `blocked` in `feature_list.json`.
