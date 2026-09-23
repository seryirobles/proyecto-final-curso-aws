# impl_stuck-loading-after-login

Issue 12. Both staged files (`App.loginLoadsWeek.test.jsx` and
`App.loginLoadsOtherViews.test.jsx`) were present under this issue, confirming
the **general fix** (all three hooks) was the approved scope — the specific
fix would have moved E3/E4 to a separate issue instead.

## Red at T1

```
cd frontend && npx vitest run tests/components/App.loginLoadsWeek.test.jsx tests/components/App.loginLoadsOtherViews.test.jsx
Test Files  2 failed (2)   Tests  4 failed (4)
```
Matches `plan.md`'s recorded red exactly.

## Fix

Same one-line pattern applied to all three hooks, mirroring
`useAdminAccounts.js:42-59`'s existing `if (!active) return undefined` /
deps `[active]` gate on their `live-weeks` (or `live-weeks`-derived) mount
effect:
- `useWeekPlanner.js` (T2) — also added `setError(null)` on success, so a
  stale pre-login `SESSION_EXPIRED` never survives into the logged-in render
  (E2).
- `useSummary.js` (T3) — same shape, same `setError(null)` addition.
- `useShoppingList.js` (T4) — same gate; its swallow-on-failure branch
  (`() => {}`) left untouched per `plan.md`.

`App.jsx` untouched — `active` already carries the "this shell/view is live"
signal into each hook.

## Collateral test correction (disclosed, not a staged test)

Two **pre-existing, non-staged** tests asserted that `usePolling` receives
the resolved week/summary URL even while `active: false` throughout the
render (`useWeekPlanner.test.js`/`useSummary.test.js`, both titled "active:
false reaches usePolling as enabled: false, App shell finding 1"). That was
only true because the old, ungated `live-weeks` effect read regardless of
`active` — exactly the defect this issue fixes. With the effect now gated,
`active: false` for the whole test means `live-weeks` never resolves, so the
URL argument is `null`. Updated both tests' expected first argument from the
literal URL string to `null`, kept the `enabled: false` assertion (still the
test's real subject) unchanged, and extended each title to name why. No
staged test touched; verified via `git diff` that the fixture inputs
(`apiFetch.mockResolvedValue`) are also unchanged.

## Traceability

| E<n> | FR-* | T<n> | Test |
|---|---|---|---|
| E1 | FR-AUTH-06, FR-AUTH-02, FR-MENU-01 | T2 | `App.loginLoadsWeek.test.jsx` "loads the week view instead of staying on the loading state" |
| E2 | FR-AUTH-06, FR-UX-05 | T2 | same file "does not show the pre-login session error..." |
| E3 | FR-SUM-01, FR-UX-06 | T3 | `App.loginLoadsOtherViews.test.jsx` "loads the summary view..." |
| E4 | FR-SHOP-05, FR-UX-06 | T4 | same file "labels the shopping-list resync scope..." |

## Result

`cd frontend && npx vitest run` — **435/435** (431 → 435: the 4 staged
cases). `npx eslint .` / `npx prettier --check .` clean. `./init.sh` green
(backend unaffected — no `backend/` file touched).

`issue_list.json`/`feature_list.json` untouched by this implementer. Not
`done` — reviewer next (batched with the other five issues in this run).

## Fix round 1 — reviewer finding (comment ceiling + stale claim)

`frontend/src/hooks/useShoppingList.js:41-45` was a 5-line comment whose
"one-time fetch" claim was wrong — this issue's own fix (gating on `active`)
makes the effect re-run every time the view becomes active, not once. Cut to
3 lines and corrected the claim; no logic changed. `./init.sh` green
(949 backend / 436 frontend).
