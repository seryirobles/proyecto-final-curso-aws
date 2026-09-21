# Issue workflow

> The bug-fix twin of `docs/specs.md`. Features start from a frozen requirement;
> issues start from something that is **already built and wrong**. Everything
> after the human gate is the same machinery as the feature flow.

## Files

| File | Holds |
|---|---|
| `issue_list.json` | The issue backlog and each issue's status. Sibling of `feature_list.json` |
| `issues/<name>/analysis.md` | Root cause, evidence, blast radius |
| `issues/<name>/plan.md` | Expected behaviour `E1…` (each citing `FR-*`), fix design, test plan |
| `issues/<name>/tasks.md` | Ordered `T<n>` checklist; the implementer ticks `[x]` |
| `issues/<name>/tests/` | **The tests that define "solved"**, written by the triager, mirroring their destination paths |

`<name>` is the issue's `name` slug in `issue_list.json`. The human hands over
issues in batches; the `leader` appends them to `issue_list.json` as `reported`.

## Issue states

| State | Meaning |
|---|---|
| `reported` | Raw report, untriaged. `issue_triager` acts first. |
| `pending` | Triaged: `issues/<name>/` written. **Awaiting the human's go / no-go. No code is touched.** |
| `approved` | Human said go. Queued; the `leader` promotes one at a time. |
| `in_progress` | `implementer` working from `plan.md` + `tasks.md`. |
| `done` | Fix green, `reviewer` approved, session closed. Human-only mark. |
| `wontfix` | Human said no. Reason in `resolution`. Only the human sets it. |
| `blocked` | Stuck. Reason in `blocked_reason` and `progress/current.md`. |

```
reported → [issue_triager] → pending → ⏸ HUMAN go/no-go → approved → in_progress → [implementer → reviewer] → done
                                                        ↘ wontfix
```

## The human gate

The automated flow stops **once**: when every `reported` issue has been triaged
and sits at `pending`. The human reads `issues/<name>/` and answers per issue —
**all, some, or none**. The `leader` maps the answer: `go` → `approved`,
`no` → `wontfix`, anything else stays `pending`. From there the flow is the
feature flow: one issue `in_progress` at a time, `implementer`, then `reviewer`
without asking.

**One `in_progress` across both lists.** An issue and a feature are never
in progress together. While any issue is `approved`, the `leader` does not start
a `pending` feature unless the human says to.

## analysis.md

- **Defect, one sentence** — the broken chain, not the remedy.
- **Reproduction** — exact command or steps and the observed vs expected result.
  Say if you could not reproduce; do not guess a cause.
- **Root cause** — `file:line`. Distinguish the cause from where the symptom
  surfaces. Name the requirement or `G-xx` the code violates.
- **Blast radius** — other callers/paths sharing the cause. Say if none.
- **Classification** — one of: `defect` (code violates a frozen requirement),
  `spec_gap` (requirement is silent or contradictory → `blocked`, frozen docs
  need a human lift), `arch_pending` (needs `docs/architecture.md` §2 →
  `blocked`), `not_a_defect` (behaviour is a deliberate resolution; cite the
  `G-xx`; leave it `pending` and let the human decide).

## plan.md

- **Expected behaviour** — EARS statements `E1…`, same rules as `docs/specs.md`
  (one `SHALL` each, no soft verbs), each with `Implements:` citing the
  `FR-*`/`NFR-*` the bug violates. Never invent a requirement: no citable id
  means `spec_gap`.
- **Fix design** — files touched, layer per `docs/architecture.md` §3, and the
  smallest change that removes the root cause. At most **two** rejected
  alternatives, 2–3 sentences each. No new dependency.
- **Test plan** — every `E<n>` maps to a concrete test **already written** by
  the triager in `issues/<name>/tests/`. It **must** include a *reproduction
  test* that fails on the current code for the reason in `analysis.md`, and
  regression tests for the blast-radius paths. `plan.md` lists each staged file
  -> its destination, and records the red result observed at triage.

## The staged tests

The triager writes them; the implementer does not get to redefine "solved".

- **Staged, not live.** Failing tests in the live suites would break
  `./init.sh`, so they wait in `issues/<name>/tests/` mirroring their destination
  path (`issues/<name>/tests/backend/core/tests/test_x.py` ->
  `backend/core/tests/test_x.py`).
- **Frozen once approved.** The implementer moves them to the destination
  **verbatim** and makes them pass by changing application code. Editing an
  assertion, loosening a fixture, or adding a skip/xfail is not allowed; if a
  test is wrong, the implementer stops and reports — the fix is a new triage,
  not a quiet edit.
- **Additive tests are fine.** The implementer may add tests beyond the staged
  ones (edge cases the fix reveals); it may not remove or weaken any.
- **Red at triage.** The triager runs them against the broken code and records
  which fail and why. A test green on broken code proves nothing.

## tasks.md

Same shape as a feature's, citing `E<n>` instead of `R<n>`. The first task is
always moving the staged tests to their destinations and confirming the
reproduction test is **red**; then the fix; then the rest.

```markdown
- [ ] T1 — Move staged tests into `core/tests/`; confirm `test_shopping_total_ignores_removed_items` fails. Covers: E1.
- [ ] T2 — Filter removed items in `aggregate()` in `core/src/planner_core/domain/shopping.py`. Covers: E1.
```

## Traceability

```
FR-xxx-nn  →  E<n>  →  T<n>  →  test
```

Same three directions as `docs/specs.md` § *Traceability*, with `E<n>` for
`R<n>`, and the issue's `covers` array for the feature's. The implementer
records the map in `progress/impl_<name>.md`. The reviewer additionally requires
that reverting the fix makes the reproduction test fail (a mutation of the fix
itself) and that the moved tests are **byte-identical** to the staged ones.
