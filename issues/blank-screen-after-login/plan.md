# blank-screen-after-login — plan

## Expected behaviour

- **E1** — WHEN `POST /v1/session` returns `passwordResetRequired: false` for an
  account whose role is `user`, the SPA SHALL mount the meal-planning shell
  without a page reload.
  *Implements:* `FR-AUTH-06`, `FR-AUTH-02`.
- **E2** — WHEN `POST /v1/session` returns `passwordResetRequired: false` for an
  account whose role is `admin`, the SPA SHALL mount the admin account-management
  shell without a page reload.
  *Implements:* `FR-AUTH-05`.
- **E3** — WHEN the admin account list renders a row, the SPA SHALL display that
  account's role as its Castilian Spanish label, never as the wire value.
  *Implements:* `FR-AUTH-12`, `FR-UX-01`, `FR-UX-03`.
- **E4** — WHEN the admin account list renders a row whose role is `admin`, the
  SPA SHALL NOT offer the remove control on that row.
  *Implements:* `FR-AUTH-18`, `FR-AUTH-13`.

## Fix design

Layer: frontend only (`docs/architecture.md` §3; the backend already sends the
contracted value). No new dependency, no backend change.

1. `frontend/src/domain/wireCodes.js` — add the role wire vocabulary and the
   one-way mapping to the SPA's internal role names, next to `UNITS` and
   `INGREDIENT_CATEGORIES`, which that module exists to mirror:

   ```js
   export const ROLE_FROM_WIRE = { admin: 'Admin', user: 'User' };
   export function roleFromWire(wireRole) {
     return ROLE_FROM_WIRE[wireRole] ?? null;
   }
   ```

   One line of comment citing the backend source of truth
   (`planner_core/domain/role.py`), same form as the existing header.

2. `frontend/src/hooks/useSession.js:46` — apply it to the login response:
   `role: roleFromWire(result.role)`. This is the root-cause line; `probe`,
   `classifyProbeFailure`, `useApp.js` and `App.jsx` stay untouched, so the
   internal vocabulary keeps exactly one definition.

3. `frontend/src/hooks/useAdminAccounts.js:25` and `:41` — map the list the
   same way where it enters state:
   `setAccounts(result.users.map((a) => ({ ...a, role: roleFromWire(a.role) })))`.
   A shared local helper inside the hook avoids repeating the expression twice.
   The hook is the right layer: the component stays a pure function of its props
   and `AccountRow.jsx` / `ROLE_LABELS` need no change.

**Rejected — adopt the lowercase wire vocabulary throughout the SPA.** Arguably
purer (`wireCodes.js` adds no new value elsewhere), but it rewrites
`useSession.js` ×3, `useApp.js`, `App.jsx` ×2, `AccountRow.jsx`, the
`ROLE_LABELS` keys and the fixtures of five live test files. Far larger than the
defect, and it would mean editing tests that are green and correct today.

**Rejected — normalise case-insensitively (`String(role).toLowerCase()` compared
both ways).** Hides the mismatch instead of removing it, and accepts values the
contract never defines; the next vocabulary drift would again pass silently.

## Test plan

Written and run at triage. Destinations mirror the staged paths.

| Staged file | Destination | Covers |
|---|---|---|
| `tests/frontend/tests/components/App.loginWireRole.test.jsx` | `frontend/tests/components/App.loginWireRole.test.jsx` | E1, E2 (reproduction) |
| `tests/frontend/tests/hooks/useSession.test.js` | `frontend/tests/hooks/useSession.test.js` (**replaces** the existing file) | E1, E2 |
| `tests/frontend/tests/components/AdminAccountsView.wireRole.test.jsx` | `frontend/tests/components/AdminAccountsView.wireRole.test.jsx` | E3, E4 (blast radius) |

`useSession.test.js` is a replacement, not a new file: its three login fixtures
carried `role: 'User'` / `'Admin'`, values the API never sends, which is why the
suite stayed green on a broken login. The replacement keeps every existing test
and assertion, corrects those three fixtures to the real wire values, and adds
one test asserting that login and the mount probe agree on the role of the same
account. Nothing is removed or weakened.

### Red observed at triage

`cd frontend && npx vitest run tests/hooks/useSession.test.js
tests/components/App.loginWireRole.test.jsx
tests/components/AdminAccountsView.wireRole.test.jsx`
→ **3 files failed, 7 failed | 9 passed (16)**.

| Test | Result today | Reason |
|---|---|---|
| `App … mounts the meal-planning shell …` (E1) | FAIL | rendered document is `<body><div /></body>` — the blank screen |
| `App … mounts the admin shell …` (E2) | FAIL | same empty render |
| `App … still routes a pending password change …` | PASS | that branch never reads the wire role (boundary, guards the fix) |
| `useSession … login and the mount probe agree …` (E1) | FAIL | `role: 'user'` received, `'User'` expected |
| `useSession … login with passwordResetRequired false …` (E2) | FAIL | `role: 'admin'` received, `'Admin'` expected |
| `useSession … login also carries the response userId …` | FAIL | same, plus proves `userId` must survive the mapping |
| `useSession` — the other 8 tests (probe, setPassword, logout) | PASS | unchanged paths |
| `AdminAccounts … labels each role in Castilian Spanish` (E3) | FAIL | `Administrador` not found; the row renders the raw `admin` |
| `AdminAccounts … remove control on the user row only` (E4) | FAIL | two remove controls render, one of them on the admin row |

The live tree was restored after the run: the two new files were deleted and
`frontend/tests/hooks/useSession.test.js` was restored byte-identical
(`git diff frontend/` empty).
