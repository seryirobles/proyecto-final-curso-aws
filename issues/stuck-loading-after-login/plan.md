# stuck-loading-after-login — plan

## Expected behaviour

- **E1** — WHEN a user logs in on an SPA that mounted with no valid session, the
  SPA SHALL present the week view for the current live week without a page
  reload.
  *Implements:* `FR-AUTH-06`, `FR-AUTH-02`, `FR-MENU-01`.
- **E2** — WHEN that week view loads, the SPA SHALL NOT display an error
  produced by a read attempted before the login.
  *Implements:* `FR-AUTH-06`, `FR-UX-05`.
- **E3** — WHEN a user logs in on an SPA that mounted with no valid session and
  opens the summary, the SPA SHALL present the summary of the current live week
  without a page reload.
  *Implements:* `FR-SUM-01`, `FR-UX-06`. *(Blast radius — general fix only.)*
- **E4** — WHEN a user logs in on an SPA that mounted with no valid session and
  opens the shopping list, the SPA SHALL label the resync scope with the current
  and next week.
  *Implements:* `FR-SHOP-05`, `FR-UX-06`. *(Blast radius — general fix only.)*

If the human picks the **specific** fix, E3/E4 and their staged file move to a
new issue.

## Fix design

Layer: frontend view hooks only (`docs/architecture.md` §3). No backend change,
no new dependency.

1. `frontend/src/hooks/useWeekPlanner.js:77-90` — gate the `live-weeks` effect
   on `active`, exactly as `useAdminAccounts.js:42-59` already does:
   `if (!active) return undefined;` at the top, deps `[active]`, and
   `setError(null)` on success. Before login `active` is false, so no read is
   made and no stale error is set; the login flips it true and the read runs
   with the new cookie. It also re-reads after logout → login.
2. *(General fix)* `frontend/src/hooks/useSummary.js:43-56` — same change.
3. *(General fix)* `frontend/src/hooks/useShoppingList.js:44-55` — same change
   (the swallow-on-failure branch stays).

`App.jsx` stays untouched; `active` already encodes "this shell and this view
are live" (`App.jsx:88-95`).

**Rejected — re-read `live-weeks` when `session` changes.** Needs the session
passed into each view hook, coupling them to the auth state machine, when
`active` already carries exactly that signal.

**Rejected — remount the User shell on login (`key` on a wrapper).** The hooks
live in `App` itself, not in a child, so this means restructuring `App` into a
new component — a refactor, not a fix.

## Test plan

Written and run at triage. Destinations mirror the staged paths; both are new
files.

| Staged file | Destination | Covers |
|---|---|---|
| `tests/frontend/tests/components/App.loginLoadsWeek.test.jsx` | `frontend/tests/components/App.loginLoadsWeek.test.jsx` | E1 (reproduction), E2 |
| `tests/frontend/tests/components/App.loginLoadsOtherViews.test.jsx` | `frontend/tests/components/App.loginLoadsOtherViews.test.jsx` | E3, E4 (blast radius) |

Both drive the real `App` and real hooks; only `apiFetch` and `fetch` are
stubbed. Every read rejects `SESSION_EXPIRED` until `POST /v1/session`
succeeds, reproducing the owner's log.

### Red observed at triage

`cd frontend && npx vitest run tests/components/App.loginLoadsWeek.test.jsx
tests/components/App.loginLoadsOtherViews.test.jsx`
→ **2 files failed, 4 failed | 0 passed (4)**.

| Test | Result today | Reason |
|---|---|---|
| `loads the week view instead of staying on the loading state` (E1) | FAIL | no `Añadir plato`; DOM shows `Cargando…` |
| `does not show the pre-login session error …` (E2) | FAIL | same — the grid never loads |
| `loads the summary view …` (E3) | FAIL | no `Resumen de la semana`; DOM shows `Cargando…` |
| `labels the shopping-list resync scope …` (E4) | FAIL | resync button renders, `Semana próxima` label absent |

Control run (not staged): the same four assertions with a valid session from
mount and no login step — **4 passed**, so the red comes from the cold-start →
login path alone. The live tree was restored after both runs (`git status
--porcelain` identical apart from `issues/stuck-loading-after-login/`).
