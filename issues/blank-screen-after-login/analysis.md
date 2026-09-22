# blank-screen-after-login — analysis

## Defect, one sentence

`useSession.login` stores the API's wire role verbatim (`"user"` / `"admin"`),
while every consumer of `session.role` compares against the capitalised
vocabulary the mount probe synthesises (`"User"` / `"Admin"`), so after a
successful login `App` matches neither shell branch and renders `null`.

## Reproduction

Automated, at the App level (staged test
`frontend/tests/components/App.loginWireRole.test.jsx`, run from `frontend/`
with `npx vitest run`):

- `GET /v1/live-weeks` rejects (`SESSION_EXPIRED`) -> login screen, as expected.
- The login form is filled and submitted; `POST /v1/session` answers with the
  real payload `{"userId":"u-1","role":"user","passwordResetRequired":false}`.
- **Observed:** the rendered document is `<body><div /></body>` — an empty
  render, the reported blank screen.
- **Expected:** the meal-planning shell (nav + week view).

The payload is not assumed. Running the real login route against faked
repositories (`backend/lambda_api/tests/_helpers.py` + `planner_api.handler`):

```
user  200 {"userId": "u-1", "role": "user",  "passwordResetRequired": false}
admin 200 {"userId": "u-1", "role": "admin", "passwordResetRequired": false}
```

A manual refresh recovers because the mount probe never reads the wire role: it
*invents* one (`'User'` on 200, `'Admin'` on `FORBIDDEN`).

## Root cause

`frontend/src/hooks/useSession.js:46`

```js
: { status: 'authenticated', role: result.role, userId: result.userId },
```

`result.role` comes from `POST /v1/session`, whose value is `Role(StrEnum).value`
— `"user"` / `"admin"` (`backend/lambda_api/src/planner_api/routing.py:128`,
`backend/core/src/planner_core/domain/role.py:9-10`). The rest of the SPA reads
`session.role` in the vocabulary produced by `classifyProbeFailure`
(`useSession.js:15`) and the probe success path (`useSession.js:25`), i.e.
`'User'` / `'Admin'`:

- `frontend/src/components/App.jsx:85-86` — `isAdmin` / `isUser`, both false, so
  `App.jsx:166` returns `null`. That line's comment ("Unreachable: authenticated
  always carries a User or Admin role") is exactly the invariant the login path
  breaks.
- `frontend/src/hooks/useApp.js:14` — `navTargets` is empty, so even a rendered
  shell would carry no navigation.

The frontend has no single definition of the role wire vocabulary:
`frontend/src/domain/wireCodes.js` exists for precisely this purpose (it mirrors
the backend's closed vocabularies for units and ingredient categories) and does
not list roles.

Requirements violated: `FR-AUTH-06` (a user shall have access to all
meal-planning features — after login it has access to nothing) and `FR-AUTH-05`
(the admin's exclusive view, unreachable on the same path).

Why the report says "a user that does not need to change password": an account
with `passwordResetRequired: true` takes the other branch
(`useSession.js:44-45`), which sets no role at all, and after `setPassword` the
hook re-probes — so that path never reads the wire role and looks healthy.

## Blast radius

Same cause — a wire `role` read in the capitalised vocabulary — one other path:

- `frontend/src/components/AccountRow.jsx:53` (`account.role === 'Admin'`) and
  `:90` (`ROLE_LABELS[account.role] ?? account.role`). The accounts come from
  `GET /v1/users`, which encodes the identical lowercase value
  (`backend/lambda_api/src/planner_api/serialization.py:162`), and pass through
  `useAdminAccounts.js:25/41` unchanged. Every admin row therefore renders the
  raw English `"admin"` as its role badge (`FR-UX-01`, `FR-UX-03`, `FR-AUTH-12`)
  **and** shows the remove control, which `FR-AUTH-18` forbids for admin
  accounts. Not in the owner's report; found here, covered by E3/E4.

Nothing else in `frontend/src` reads a role (grep for `role` across
`frontend/src`): the remaining hits are comments and unrelated token names.

Why the live suites are green on a broken login: the fixtures in
`frontend/tests/hooks/useSession.test.js` feed `POST /v1/session` responses of
`{ role: 'User' }` / `{ role: 'Admin' }` — values the API never sends. The test
encodes the same misreading as the code, which is why it never caught it.

**Not related to issues 6 (`new-recipe-not-shown-in-library`) and 10
(`ui-not-reflecting-mutations`).** Those are "a mutation's result is not
refetched into the view"; this one never renders a view at all, and no refetch
would help — a full page reload is what recovers it, through a different code
path (the mount probe). No shared file, no shared fix.

## Classification

`defect` — the code violates `FR-AUTH-05` / `FR-AUTH-06` (and, in the blast
radius, `FR-AUTH-12`, `FR-AUTH-18`, `FR-UX-01`, `FR-UX-03`). No architecture
decision and no requirement lift is needed: the wire vocabulary is already
fixed by `docs/rest_api_contract.md` §2 and the backend `Role` enum.

Severity as reported (`high`) is correct: the application is unusable after a
normal login until the user thinks to reload.
