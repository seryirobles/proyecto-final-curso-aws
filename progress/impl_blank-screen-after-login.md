# blank-screen-after-login — implementation report

## Summary

Root cause per `issues/blank-screen-after-login/analysis.md`: `useSession.login`
stored the API's wire role verbatim (`"user"` / `"admin"`, `Role` StrEnum),
while `App.jsx` and `useApp.js` compared `session.role` against the
capitalised vocabulary the mount probe synthesises (`'User'` / `'Admin'`).
Neither shell branch matched, so `App.jsx:166` fell through to `return null`
— the reported blank screen. Same mismatch, second path: `useAdminAccounts.js`
passed `GET /v1/users`' wire roles straight into state, so `AccountRow.jsx`
rendered the raw `admin`/`user` string as a badge and mis-gated the remove
control.

## Fix

Layer: frontend only, no backend change, no new dependency — matches
`plan.md`'s "Fix design" (rejected alternatives: SPA-wide lowercase adoption,
case-insensitive comparison — both logged in `plan.md`, not repeated here).

1. `frontend/src/domain/wireCodes.js` — added `ROLE_FROM_WIRE` (`{admin:
   'Admin', user: 'User'}`) and `roleFromWire(wireRole)`, next to `UNITS`/
   `INGREDIENT_CATEGORIES`, citing `planner_core/domain/role.py`.
2. `frontend/src/hooks/useSession.js:46` (now :47) — `login`'s success branch
   applies `roleFromWire(result.role)`. `probe`, `classifyProbeFailure`,
   `useApp.js`, `App.jsx` untouched.
3. `frontend/src/hooks/useAdminAccounts.js` — new local `withRoleMapped(users)`
   helper, applied at both places an account list enters state: the mount
   effect and `refetch`. `AccountRow.jsx` and `ROLE_LABELS` untouched.

## Traceability

| `E<n>` (plan.md) | `FR-*` | Test |
|---|---|---|
| E1 — user login mounts the meal-planning shell, no reload | FR-AUTH-06, FR-AUTH-02 | `App.loginWireRole.test.jsx` "mounts the meal-planning shell …"; `useSession.test.js` "login and the mount probe agree on the role of the same User account" |
| E2 — admin login mounts the admin shell, no reload | FR-AUTH-05 | `App.loginWireRole.test.jsx` "mounts the admin shell …"; `useSession.test.js` "login with passwordResetRequired false authenticates with the returned role" (admin case) + "login also carries the response userId through" |
| E3 — admin account rows show the es-ES role label, never the wire value | FR-AUTH-12, FR-UX-01, FR-UX-03 | `AdminAccountsView.wireRole.test.jsx` "labels each role in Castilian Spanish" |
| E4 — no remove control on an admin row | FR-AUTH-18, FR-AUTH-13 | `AdminAccountsView.wireRole.test.jsx` "remove control on the user row only" |

All 8 `covers` ids on issue 2 in `issue_list.json` (`FR-AUTH-02`,
`FR-AUTH-05`, `FR-AUTH-06`, `FR-AUTH-12`, `FR-AUTH-13`, `FR-AUTH-18`,
`FR-UX-01`, `FR-UX-03`) are reachable through E1–E4 above.

## Test moves and red→green evidence

Staged files moved verbatim (`diff` against the staged copies: empty):

- `issues/blank-screen-after-login/tests/frontend/tests/components/App.loginWireRole.test.jsx` → `frontend/tests/components/App.loginWireRole.test.jsx`
- `issues/blank-screen-after-login/tests/frontend/tests/components/AdminAccountsView.wireRole.test.jsx` → `frontend/tests/components/AdminAccountsView.wireRole.test.jsx`
- `issues/blank-screen-after-login/tests/frontend/tests/hooks/useSession.test.js` → `frontend/tests/hooks/useSession.test.js` (replaces the pre-existing file, byte-identical to the staged copy)

**Red** (`cd frontend && npx vitest run tests/hooks/useSession.test.js
tests/components/App.loginWireRole.test.jsx
tests/components/AdminAccountsView.wireRole.test.jsx`), before any code
change: `3 files failed, 7 failed | 9 passed (16)` — matches `plan.md` §
*Red observed at triage* exactly (App rendering `<body><div/></body>` on
both roles; `useSession` returning `'admin'`/`'user'` where `'Admin'`/
`'User'` was expected; the pending-password-change test still passing as
the untouched boundary).

**Green**, after the fix (same command): `3 files passed, 16 passed (16)`.

Full frontend suite (`cd frontend && npx vitest run`): **53 files passed,
355 passed (355)**. `./init.sh`: fully green (`818 passed, 8 deselected`
backend, unaffected by this frontend-only change; ruff/mypy/prettier/
eslint/vitest all clean).

No staged test was edited, loosened, skipped or xfailed — `git diff
issues/blank-screen-after-login/tests/` is empty. `tasks.md` T1–T5 all
ticked. `issue_list.json` untouched by this session.
