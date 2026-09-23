# blank-screen-after-login — tasks

- [x] T1 — Move the three staged files from `issues/blank-screen-after-login/tests/`
      to their destinations verbatim (`frontend/tests/components/App.loginWireRole.test.jsx`,
      `frontend/tests/components/AdminAccountsView.wireRole.test.jsx`, and
      `frontend/tests/hooks/useSession.test.js`, which **replaces** the existing
      file). Run `cd frontend && npx vitest run` on the three and confirm 7
      failures, matching `plan.md` § *Red observed at triage*. Covers: E1–E4.
- [x] T2 — Add `ROLE_FROM_WIRE` + `roleFromWire()` to
      `frontend/src/domain/wireCodes.js`, citing `planner_core/domain/role.py`
      as the source of truth. Covers: E1, E2, E3, E4.
- [x] T3 — Apply `roleFromWire` to the login response in
      `frontend/src/hooks/useSession.js:46`; leave `probe` and
      `classifyProbeFailure` untouched. Covers: E1, E2.
- [x] T4 — Apply `roleFromWire` to each account as it enters state in
      `frontend/src/hooks/useAdminAccounts.js` (both the mount effect and
      `refetch`). Covers: E3, E4.
- [x] T5 — Run the full frontend suite (`cd frontend && npx vitest run`) and
      `./init.sh`; both green, with no assertion in the staged tests edited.
      Covers: E1–E4.
