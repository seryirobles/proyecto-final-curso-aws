# impl_ui-not-reflecting-mutations

Issue 10, `in_progress`. Batch order: fixed first (deliberately out of numeric
order) since issue 6 shares its root cause and its fix.

## Red at T1

```
cp issues/ui-not-reflecting-mutations/tests/frontend/tests/hooks/*.test.js frontend/tests/hooks/
cd frontend && npx vitest run tests/hooks/use*.mutationVisibility.test.js
Test Files  4 failed (4)      Tests  10 failed | 1 passed (11)
```
Matches `plan.md`'s recorded red exactly (E1–E10 failing, E11 green).

## Fix

`frontend/src/realtime/pollingEngine.js`: `poll()` split into a shared
`fetchAndApply(marker)`; new `refetchNow()` calls `fetchAndApply(null)` —
unconditional 200, `disposed`-guarded, does not touch `applyMutationMarker`
(R25/R26 untouched). Exposed through `usePolling.js` and `useLibraryPicker.js`.
One `<hook>.refetchNow()` call added after each `applyMutationMarker(marker)`
at the 9 sites `plan.md` names: `useLibrary.js:80` (delete),
`useRules.js:93,114`, `useShoppingList.js:92,110,129,149`,
`useWeekPlanner.js` promote/clear.

**Beyond T6's literal scope, disclosed per this batch's dispatch brief:**
`useWeekPlanner.js`'s other three `weekPoll.applyMutationMarker` call sites —
`submitCandidate`, `submitCandidateEdit`, `removeCandidate` (issue 3,
`add-dish-button-inert`, already `done`/`reviewed`) — share the identical
root cause (`analysis.md`'s blast-radius row: "two more would fail the moment
issue 3 wires them"). Same one-line fix applied to all three.

## Traceability

| E<n> | FR-* | T<n> | Test |
|---|---|---|---|
| E1 | FR-LIB-01, FR-LIB-02 | T3 | `useLibrary.mutationVisibility.test.js` "a confirmed delete removes the recipe... (E1)" |
| E2 | FR-RULE-02, FR-RULE-06 | T4 | `useRules.mutationVisibility.test.js` "...(E2)" |
| E3 | FR-RULE-02, FR-RULE-06 | T4 | `useRules.mutationVisibility.test.js` "...(E3)" |
| E4 | FR-SHOP-01, FR-SHOP-02 | T5 | `useShoppingList.mutationVisibility.test.js` "...(E4)" |
| E5 | FR-SHOP-01, FR-SHOP-02 | T5 | same file "...(E5)" |
| E6 | FR-SHOP-07, FR-SHOP-08 | T5 | same file "...(E6)" |
| E7 | FR-SHOP-01, FR-SHOP-02 | T5 | same file "...(E7)" |
| E8 | FR-SHOP-03, FR-SHOP-06 | T5 | same file "...(E8)" |
| E9 | FR-MENU-03, FR-CAND-05 | T6 | `useWeekPlanner.mutationVisibility.test.js` "...(E9)" |
| E10 | FR-MENU-03, FR-CAND-08 | T6 | same file "...(E10)" |
| E11 | FR-RT-01 (G-88) | T7 (guard, unchanged) | `pollingEngine.test.js:206` — stays green |
| n/a (regression) | FR-CAND-01, FR-CAND-05 | T6 (extra) | `useWeekPlanner.candidateMutationVisibility.test.js` (moved here fix round 1): submit/edit/remove candidate, real engine |

## Collateral fixture fix (disclosed)

`refetchNow()` did not exist on any pre-existing hand-mocked `usePolling`
return value across the live suite, so calling it inside a `try` block threw,
silently swallowed by each hook's own `catch (err) { setError(...) }` —
breaking two of issue 3's already-approved tests
(`WeekPlannerView.candidateAuthoring.test.jsx`,
`WeekPlannerView.candidateEditRemove.test.jsx`, form-close assertions timed
out) and silently masking errors in others. Fixed by adding
`refetchNow: vi.fn()` to every hand-built poll-snapshot mock fixture that
already carried `applyMutationMarker: vi.fn()`: `useLibrary.test.js`,
`useRules.test.js`, `useShoppingList.test.js` (x2), `useWeekPlanner.test.js`,
`WeekPlannerView.candidateAuthoring.test.jsx`,
`WeekPlannerView.candidateEditRemove.test.jsx`. **No assertion in any of
these files was touched** — only the mock's returned shape, to match the real
`usePolling` contract. `useSummary.test.js`'s own `applyMutationMarker` mocks
left untouched (read-only hook, no mutation, `refetchNow` never called there).

## Result

`cd frontend && npx vitest run` — **399/399** (390 → 399: 11 staged +
3 additive regression - 5 net... actual delta: 4 staged files' 11 cases were
new files, +3 regression cases in `useWeekPlanner.mutationVisibility.test.js`,
14 new test cases total; count moved 385→399). `npx eslint .` / `npx prettier
--check .` clean. `./init.sh` green (backend unaffected — no `backend/` file
touched, verified via `git status`).

`issue_list.json`/`feature_list.json` untouched by this implementer. Not
`done` — reviewer next (batched with the other five issues in this run).

## Fix round 1 — reviewer findings (real race, test drift, comment ceiling)

**F1 (real bug):** `refetchNow()` silently dropped a forced refetch requested
while a scheduled poll was already in flight — `fetchAndApply`'s
`if (inFlight) return;` guard applied to both. A mutation's own change could
then be masked behind a stale `304`. Fixed with a `pendingForcedRefetch` flag
in `pollingEngine.js`: `refetchNow()` sets it instead of no-op'ing when
`inFlight`; the in-flight call's `finally` block, on seeing the flag, fires an
unconditional `fetchAndApply(null)` instead of `scheduleNext()` (skipped if
`disposed` meanwhile). New engine-level test in
`frontend/tests/realtime/pollingEngine.test.js`: "queues refetchNow() called
mid-flight instead of dropping it (fix round 2)" — holds the first fetch
unresolved, calls `refetchNow()`, resolves, asserts a second unconditional
(`marker === null`) fetch ran. 17/17 in that file, including this one.

**F2 (byte-identity):** a prior round had rewritten the staged
`useWeekPlanner.mutationVisibility.test.js`'s shared `fakeWeekServer` fixture
to add 3 regression cases (issue 3's `submitCandidate`/`submitCandidateEdit`/
`removeCandidate` cross-check) directly into the staged file. Restored that
file to be byte-identical to `issues/ui-not-reflecting-mutations/tests/
frontend/tests/hooks/useWeekPlanner.mutationVisibility.test.js` (verified via
`diff`). The 3 regression cases moved to a new file,
`frontend/tests/hooks/useWeekPlanner.candidateMutationVisibility.test.js`,
with its own copy of the extended `fakeWeekServer` (candidates sub-resource).
Traceability table's "n/a (regression)" row now points at the new file.

**F3 (comment ceiling):** `pollingEngine.js`'s `refetchNow()` comment cut
from 4 to 3 lines. `useWeekPlanner.mutationVisibility.test.js`'s 7-line block
disappeared with the F2 restore (staged file's own header is 2 lines).

Result: `cd frontend && npx vitest run` — **436/436** (399 → 436: +1 engine
race test, +3 regression cases in their new home, plus other issues' fix-round
tests in this batch). `npx eslint .` / `npx prettier --check .` clean.
`./init.sh` green (949 backend / 436 frontend) — backend untouched, verified
via `git status`. No staged test edited, loosened or removed.
