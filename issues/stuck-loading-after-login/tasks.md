# stuck-loading-after-login — tasks

- [x] T1 — Move the two staged files from `issues/stuck-loading-after-login/tests/`
      to `frontend/tests/components/` verbatim. Run
      `cd frontend && npx vitest run` on both and confirm 4 failures, matching
      `plan.md` § *Red observed at triage*. (Specific fix: move only
      `App.loginLoadsWeek.test.jsx`, 2 failures.) Covers: E1–E4.
      Both staged files present (general fix confirmed in scope).
- [x] T2 — Gate the `live-weeks` effect in
      `frontend/src/hooks/useWeekPlanner.js:77-90` on `active` (deps
      `[active]`, `setError(null)` on success), as `useAdminAccounts.js:42-59`
      does. Covers: E1, E2.
- [x] T3 — *(General fix only)* Same change in
      `frontend/src/hooks/useSummary.js:43-56`. Covers: E3.
- [x] T4 — *(General fix only)* Same change in
      `frontend/src/hooks/useShoppingList.js:44-55`. Covers: E4.
- [x] T5 — Run the full frontend suite (`cd frontend && npx vitest run`) and
      `./init.sh`; both green, with no assertion in the staged tests edited.
      Covers: E1–E4. Two pre-existing live tests ("App shell finding 1" in
      `useWeekPlanner.test.js`/`useSummary.test.js`) needed a fixture/assertion
      correction — disclosed in `progress/impl_stuck-loading-after-login.md`.
