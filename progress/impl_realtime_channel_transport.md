# impl — realtime_channel_transport (feature 26)

`docs/verification.md` Level 3. Spec: `specs/realtime_channel_transport/`.
Covers `{FR-RT-01, FR-RT-02, FR-RT-03}`. All code/tests pre-existed in the
working tree from an earlier, unfinished session; this pass closed the SDD
gate (T25): fixed lint/format, verified every task against real code and
tests, checked off T1–T25 (incl. T24a/T24b), and wrote this report.

## Quality gates

| Gate | Result |
|---|---|
| `uv run ruff format --check .` / `ruff check .` / `mypy .` (backend/) | pass |
| `uv run pytest -q` (backend/) | **795 passed** |
| `npx prettier --check .` (frontend/) | pass (fixed 6 files) |
| `npx eslint .` (frontend/) | pass (fixed 1 config gap + 1 stale directive) |
| `npx vitest run` (frontend/) | 36 passed, 7 files |
| `./init.sh` (repo root) | `[OK] Environment ready` |

**Fixes made this pass** (mechanical, no design change):
- `frontend/eslint.config.js`: `globals` (lines 25-30) was missing `fetch` and
  `Event`, both legitimately used by this feature's browser-facing code
  (`src/realtime/conditionalGet.js`, `tests/hooks/usePolling.test.js`).
  Added both rather than special-casing files.
- `frontend/src/hooks/usePolling.js:33`: removed a now-stale
  `eslint-disable-next-line react-hooks/exhaustive-deps` — the dep array
  (`[url, config, createEngine]`) is already exhaustive, so the rule reports
  nothing and the directive itself was the only lint failure.
- `prettier --write` on the 6 files the gate flagged (formatting only).

## R → test (forward)

| R | Statement (short) | Test(s) |
|---|---|---|
| R1 | read marker before computing payload on conditional GET | `test_handler.py::test_a_matching_marker_304s_and_a_stale_marker_gets_the_full_week` (+ library/rules/shopping variants, `::test_week_summary_304s_on_a_matching_marker_without_reading_the_week`), `::test_a_current_marker_takes_the_unchanged_200_path` |
| R2 | marker match → `304` | same tests, asserts `statusCode == 304` |
| R3 | `304` echoes request's `If-None-Match` as `ETag` | `::test_a_matching_marker_304s_and_a_stale_marker_gets_the_full_week` (`ETag == f'"{current_marker}"'`) |
| R4 | marker mismatch → full `200` payload | `::test_a_current_marker_takes_the_unchanged_200_path` |
| R5 | `304` never computes the payload | `_NoExpensiveRead` wrapper in `test_handler.py` — raises if the wrapped port's expensive read (`get_week`/`list_all`/`get`/`list_items`) is called; all 4 pollable-route 304 tests use it |
| R6 | absent/malformed/`*`/multi-valued `If-None-Match` → full payload, no `304` attempt | `test_conditional_get.py::test_parse_if_none_match_only_accepts_a_single_quoted_integer` (parametrized: `None`, `"*"`, list, unquoted, non-numeric, empty → all `None`) |
| R7 | conditional-GET applies only to the 4 pollable `GET` routes | `test_routing_table.py::test_only_the_pollable_get_routes_carry_a_current_version_reader` |
| R8 | re-sync writes differing items in one transaction | `test_shopping_editing.py::test_resync_needing_three_new_items_bumps_the_marker_once_not_three_times`; contract `::test_save_items_bumps_the_marker_exactly_once_for_a_batch` |
| R9 | that transaction bumps `marcaCambio` exactly once | same two tests (assert `current_version()` advances by exactly 1) |
| R10 | no differing items → no bump | `test_shopping_list_repository_contract.py::test_save_items_with_an_empty_sequence_is_a_no_op` |
| R11 | `marcaCambio` never in the transaction's `ConditionExpression` | `test_change_marker_is_not_a_write_condition.py::test_no_adapter_conditions_a_write_on_the_change_marker` (exhaustive adapter-source scan, covers the new `save_items` line) |
| R12 | poll sends held marker as quoted `If-None-Match` | `conditionalGet.test.js::maps a 304 response...` (asserts header value), `::omits the header when no marker is held yet` |
| R13 | `304` leaves held data/marker unchanged | `pollingEngine.test.js::keeps data and marker on a 304 response`; `conditionalGet.test.js::maps a 304 response...` |
| R14 | `200` replaces held data/marker | `pollingEngine.test.js::replaces data and marker on a 200 response`; `conditionalGet.test.js::maps a 200 response...` |
| R15 | each resource's marker/failures/loss-flag independent | `pollingEngine.test.js::never shares state between two engine instances` |
| R16 | active interval while visible+focused | `pollingEngine.test.js::computeDelay > uses the active interval...` |
| R17 | background interval while hidden/blurred | `pollingEngine.test.js::computeDelay > uses the background interval...` |
| R18 | immediate poll on regaining focus | `pollingEngine.test.js::createPollingEngine > polls immediately when the tab regains foreground` |
| R19 | failure increments consecutive-failure count | `pollingEngine.test.js::flags connection loss after the failure threshold...` (drives the count up) |
| R20 | success resets failure count to 0 | same test (second phase, `shouldFail = false`) |
| R21 | doubling per consecutive failure, capped | `computeDelay > doubles the base delay once per consecutive failure`, `::caps the backoff at backoffCapMs` |
| R22 | jitter within configured ratio | `computeDelay > applies jitter within the configured ratio` |
| R23 | N consecutive failures → connection-loss indication | `flags connection loss after the failure threshold...` (`connectionLost === true`) |
| R24 | success while lost clears the indication | same test (`connectionLost === false` after recovery) |
| R25 | mutation marker == held+1 → store it | `resolveMutationMarker > stores the returned marker...`; `createPollingEngine > applyMutationMarker stores held+1...` |
| R26 | mutation marker mismatch → discard + refetch | `resolveMutationMarker > discards the returned marker...`; `createPollingEngine > applyMutationMarker discards a mismatched marker...` |

Wiring-only (T24/T24b, no independent `R<n>` logic): `usePolling.test.js`'s
4 tests prove `useSyncExternalStore` wiring, the DOM `visibilitychange`
listener reaching a real `document` event, and `start()`/`dispose()`
lifecycle — R12–R26's decision logic is proven above, at the engine/module
level, per `design.md` §7/§9's gate ruling.

## test → R (reverse), backend only (frontend table above is already 1:1)

| Test module | R |
|---|---|
| `backend/lambda_api/tests/test_conditional_get.py` | R6 |
| `backend/lambda_api/tests/test_handler.py` (5 tests, 4 rewritten fix round 1) | R1–R5 |
| `backend/lambda_api/tests/test_routing_table.py` (1 new test) | R7 |
| `backend/core/tests/application/test_shopping_editing.py` (1 new test) | R8, R9 |
| `backend/tests/contract/test_shopping_list_repository_contract.py` (2 new tests) | R8, R9, R10 |
| `backend/core/tests/test_change_marker_is_not_a_write_condition.py` (existing exhaustive scan, no new test needed) | R11 |

`FR-RT-01` → R1–R15 (backend + poll/mutation wire format); `FR-RT-02` → R25,
R26; `FR-RT-03` → R16–R24. All three `covers` entries traced, no gap.

## Tasks → status

All of T1–T24, T24a, T24b, T25 (`specs/realtime_channel_transport/tasks.md`)
verified against existing code/tests and checked off `[x]`. No task required
new code beyond the lint/format fixes above — the feature's logic already
matched `design.md`.

## Notes — what this pass found, not anticipated by a fresh implementer

1. **The session that wrote this feature never finished its own bookkeeping.**
   Code and tests were complete and green (mypy/ruff/pytest all passed
   already); only `tasks.md` checkboxes, this report, and the frontend
   lint/format gate were left open. Backend was already fully clean.
2. **Data-loss incident, disclosed for the record:** at the start of this
   session an agent mistake (a `Write` to `progress/current.md` without
   reading it first) overwrote that file's content. It had shown as
   uncommitted (`M`) in git status, meaning it held edits never staged —
   git has no blob of them, so they are **not recoverable**. The file has
   been restored to its last committed (`HEAD`) state; a short note of this
   incident plus the gate-closure entry has been appended there. Nothing in
   `specs/`, task checkboxes, or this report was affected — this file is the
   only casualty, and it is process bookkeeping, not source or spec content.

## Fix round 1 — 2026-09-12 (reviewer CHANGES_REQUESTED, 2 findings)

**M-A** — every 304-path test exercised a resource stuck at its initial `0`
marker, so a reader wired to a constant `0` was indistinguishable from a
correct one. Rewrote the 4 pollable-route tests in `test_handler.py`
(weeks/library/rules/shopping — `test_week_summary_...` shares the same
`week_editing.poll_marker` wiring, left as-is) to write first, then assert
`304` on the new marker and `200` (full payload) on the stale `"0"`. This
caught a real bug, not just a test gap: **`library_editing.py::poll_marker`
returned a literal `0`**, never `recipes.current_version()` — fixed.
Re-verified: mutating `week_editing.poll_marker` and (separately)
`library_editing.poll_marker` to `return 0` — both now **killed** (the
rewritten tests fail with a 500/`AssertionError` from the `_NoExpensiveRead`
guard, since the stale-marker `304` branch wrongly fires). Reverted by hand.

**M-B** — `usePolling.test.js`'s T24b case only dispatched
`visibilitychange`, leaving the hook's `blur`/`focus` DOM wiring (R17/R18)
untested. Added a case dispatching real `window` `blur` then `focus` events
against the captured `visibilitySource`. Re-verified: deleting the
`blur`/`focus` listener pair from `domVisibilitySource` — **killed**
(assertion failure, spy called 0 times instead of 2). Reverted by hand.

`./init.sh` green — **795 backend tests**, vitest **36 passed, 7 files**
(35→36; one new case). No `feature_list.json` change, no commit.
