# stuck-loading-after-login — analysis

## Defect, one sentence

`useWeekPlanner` reads `GET /v1/live-weeks` exactly once, when `App` first mounts — before anyone is logged in — so on a session-less start that read fails `SESSION_EXPIRED`, `liveWeeks` stays `null`, and after a successful login nothing ever reads it again: the week view renders `LoadingState` ("Cargando…") forever.

## Reproduction

Automated, at the App level with the real hooks (staged `frontend/tests/components/App.loginLoadsWeek.test.jsx`; only `apiFetch` and `fetch` are stubbed): every read rejects `SESSION_EXPIRED` until `POST /v1/session` answers `{"role":"user","passwordResetRequired":false}`.

- **Observed:** shell and nav render, the main area shows `Cargando…` indefinitely; no `live-weeks` read is issued after login.
- **Expected:** the week grid (14 slots) for the current week.

Control: the same assertions with a valid session from mount (no login step) pass — the defect is only on the cold-start → login path. A reload recovers because the fresh mount runs its one read with the new cookie.

Matches the owner's `local_server.py` log: `live-weeks` 403s ("expired session", `authorizer.py:59`) *before* login, `POST /v1/session 200`, then no request. Four hooks read `live-weeks` at mount (`useSession` probe, `useWeekPlanner`, `useShoppingList`, `useSummary`), doubled by `<StrictMode>` (`main.jsx`) in dev. Those pre-login 403s are correct authorizer behaviour, not the defect; the lone `GET /` 403 (no cookie) is not from the SPA's hooks.

## Root cause

`frontend/src/hooks/useWeekPlanner.js:77-90` — the `live-weeks` effect has deps `[]` and ignores the hook's own `active` flag:

```js
useEffect(() => {
  let cancelled = false;
  apiFetch('/v1/live-weeks').then(...);
  ...
}, []);
```

`App.jsx:90` calls `useWeekPlanner({ active: isUser && activeView === 'week' })` on every render from the very first one, while `session.status` is still `loading`/`anonymous` (Rules of Hooks; `App.jsx:88-89` says `active` is what keeps each hook's fetch off until its shell is live). `active` gates only the week poll (`:97`), whose URL is derived from `liveWeeks` — so it stays `null` too. Symptom surfaces at `WeekPlannerView.jsx:40` (`isLoading` = `liveWeeks === null || week === null`, `useWeekPlanner.js:242`), which also hides the stale pre-login `error` set at `:84`.

Violates `FR-AUTH-06` / `FR-AUTH-02` (after a successful login the user reaches no meal-planning feature) and `FR-MENU-01` (the live weeks are never presented). `FR-UX-05` asks for a loading state for *slow* operations, not an unending one.

## Relation to issue 2 (`blank-screen-after-login`)

**Different root cause, same user path; issue 2 masked this one.** Issue 2 is the wire-role mismatch at `useSession.js:46`, which made `App` render `null` after login, so `WeekPlannerView` never mounted. Its fix (`roleFromWire`, now at `useSession.js:47` in the working tree) is what the owner is running: the "next screen" appearing is the User shell that issue 2 restored. Issue 2's fix is correct and not incomplete in its own scope — its App test stubs `useWeekPlanner` (`App.loginWireRole.test.jsx:15`), and no `E` in its plan covers data loading. Neither fix substitutes for the other; this one must land on top of issue 2.

Not related to issues 6 / 10 (mutation results not refetched): this is a read that never re-runs on session change, not a mutation.

## Blast radius

Same cause — a mount-once `live-weeks` read with deps `[]` that ignores `active` — in two more hooks. **Neither is in the report**; both were unreachable to test while the week view was stuck. **Open scope question for the human: general fix (all three hooks) or specific fix (week view only, the other two as a separate issue)?**

- `frontend/src/hooks/useSummary.js:43-56` — identical pattern; after a cold login the summary view is also stuck on `Cargando…` (`FR-SUM-01`, `FR-UX-06`). Staged test E3 red.
- `frontend/src/hooks/useShoppingList.js:44-55` — swallows the failure; the list itself loads (its poll is `active`-gated), but the resync scope never shows its week labels (`ShoppingListView.jsx:58`; `FR-SHOP-05`, `FR-UX-06`). Staged test E4 red.

Not affected: `useAdminAccounts.js:42-59` already gates its read on `active` (deps `[active]`) — the pattern the fix follows. `useLibrary`/`useRules` read nothing outside their `active`-gated polls.

Observation, not in scope: `WeekPlannerView.jsx:40` / `SummaryView.jsx:26` check `isLoading` before `error`, so a genuine `live-weeks` failure while logged in would also show `Cargando…` rather than the error (`R15`). Not needed to fix this issue.

## Classification

`defect` — violates `FR-AUTH-06`, `FR-AUTH-02`, `FR-MENU-01` (and, in the blast radius, `FR-SUM-01`, `FR-SHOP-05`, `FR-UX-06`). No requirement lift, no architecture decision. Severity `high` stands: after a normal login the app is unusable until a reload.
