# CHECKPOINTS — Final-state evaluation

> In multi-agent systems you do not evaluate the path, you evaluate the
> destination. These are the objective checkpoints a judge (human or AI) uses to
> decide whether the project is healthy.

## C1 — The harness is complete

- [ ] The base files exist: `AGENTS.md`, `CLAUDE.md`, `CHECKPOINTS.md`,
      `init.sh`, `feature_list.json`, `issue_list.json`, `progress/current.md`.
- [ ] The five docs exist: `docs/architecture.md`, `docs/conventions.md`,
      `docs/specs.md`, `docs/issues.md`, `docs/verification.md`.
- [ ] The five frozen requirement docs are **unmodified**: `docs/requirements.md`,
      `docs/app_user_stories.md`, `docs/coverage_analysis.md`,
      `docs/gaps_and_resolutions.md`, `docs/gaps_pending_stakeholders.md`.
- [ ] `./init.sh` exits with code 0.

## C2 — State is coherent

- [ ] At most one feature is `in_progress` in `feature_list.json`.
- [ ] Every `blocked` feature has a non-empty `blocked_reason`.
- [ ] Every `done` feature has associated passing tests.
- [ ] `progress/current.md` is either empty or describes the active session —
      no leftovers from previous sessions.

## C3 — The code respects the architecture

- [ ] `planner_core/domain/` imports nothing from `application/`, `ports/`, an
      adapter, a handler, or any AWS SDK.
- [ ] `core` imports no AWS SDK and no Lambda package, and declares **zero**
      runtime dependencies.
- [ ] `planner_core/application/` never imports an adapter or a handler.
- [ ] No `datetime.now()` inside `planner_core`, except the one sanctioned
      `SystemClock.now` call in `ports/clock.py` (`docs/architecture.md` §1.2.2,
      §3.1 rule 6). `backend/core/tests/test_no_ambient_time.py` checks this
      mechanically — a green suite ticks the box.
- [ ] There are exactly two Lambda packages: `lambda_api` and `lambda_ai`.
- [ ] Adapters are imported only by their Lambda's `wiring.py`, selected by
      environment.
- [ ] Every dependency in every `pyproject.toml` traces to an approved `design.md`.
- [ ] No stray debug `print()`, no context-free TODOs.

## C4 — Verification is real

- [ ] `uv run ruff check .` is clean (from `backend/`).
- [ ] `uv run mypy .` is clean, with no new `# type: ignore`.
- [ ] `uv run pytest -q` shows > 0 tests, all green (default tiers, no AWS).
- [ ] `core` tests run with no AWS, no network, no real clock.
- [ ] Each member's `tests/` has at least one test module per source module.
- [ ] Every port has a contract suite; live-AWS runs are marked `@pytest.mark.aws`.
      > **Deferral, 2026-08-18 — the `Clock` port (feature 2 `week_calendar`).**
      > `backend/tests/contract/` is empty and this box stays unticked
      > deliberately. **Feature 14 `persistence_ports` adds the suite**, whose
      > third acceptance criterion already requires *"a contract suite in
      > `backend/tests/contract` … parametrized to run against any
      > implementation (fake now, real adapter later)"*. It must cover `Clock`
      > alongside the persistence ports. Recorded because the alternative —
      > silence — means discovering the gap when the persistence adapters
      > arrive. Raised as F2 in `progress/review_week_calendar.md`.
      >
      > *Amended 2026-08-18.* The original note justified the deferral with *"no
      > real `Clock` adapter exists yet — adapters are Lambda-owned"* and
      > required that *"the first `SystemClock` must not land before it"*. **That
      > reasoning was wrong.** `docs/architecture.md` §3.1 rule 3 scopes Lambda
      > ownership to adapters that import an external dependency; a `SystemClock`
      > imports nothing. The human decided on 2026-08-18 that a port's
      > dependency-free **default implementation** ships beside its `Protocol` in
      > `planner_core/ports/` (`docs/architecture.md` §1.2.2), so `SystemClock`
      > lands with feature 2 and this deferral does not gate it. The deferral
      > itself still stands: with `Clock` and `SystemClock` both dependency-free,
      > a contract suite parametrized over them adds little beyond
      > `test_fake_clock_satisfies_the_clock_port`, and the real value arrives
      > when feature 14 brings implementations that genuinely differ.
      >
      > *Amended 2026-11-09.* Feature 14 landed `backend/tests/contract/`, one
      > suite per port with an external-dependency adapter. The four ports
      > whose only real implementation is a stdlib default in `ports/` —
      > `Clock`, `ConfigPort`, `PasswordHasher`, `TokenSigner` — still have
      > none, so this box stays unticked for them. The review file cited above
      > no longer exists (review files are banned, `AGENTS.md` §3.1).

## C5 — The session closed properly

- [ ] No suspicious untracked files (`*.tmp`, `__pycache__`, `.venv` outside
      `.gitignore`).
- [ ] `progress/history.md` has an entry for the last session.
- [ ] The last feature worked on is in its correct state.

## C6 — Spec Driven Development

- [ ] Every `"sdd": true` feature in `spec_ready`, `in_progress` or `done` has
      its `specs/<name>/` folder with all three files.
- [ ] `requirements.md` uses strict EARS (see `docs/specs.md`).
- [ ] Every `R<n>` cites at least one `FR-*` / `NFR-*` id.
- [ ] Every `FR-*` in the feature's `covers` array appears in some `R<n>`.
- [ ] Every `R<n>` is covered by at least one concrete test in the relevant
      member's `tests/`.
- [ ] Every `done` `"sdd": true` feature has all its tasks ticked `[x]`.
- [ ] Every `FR-*`/`NFR-*` id defined in `docs/requirements.md` is covered by at
      least one feature's `covers` array, and no `covers` cites an unknown id
      (enforced by `init.sh`).

## C7 — Human-owned boundaries were respected

- [ ] **No `*.tf` / `*.tfvars` files were generated by an agent.**
- [ ] **No `.github/workflows/**` files were generated by an agent.**
- [ ] No architecture decision from `docs/architecture.md` §2 was silently made
      — anything that needed one is `blocked` with the reason recorded.
- [ ] No requirement was invented: every `R<n>` traces to an existing `FR-*`.
- [ ] The frozen requirement docs were not edited.

---

**How to use this file:** a reviewer agent (`.claude/agents/reviewer.md`) walks
every checkbox, marks `[x]` or `[ ]`, and refuses to close the session if any
box in C1–C7 is empty.
