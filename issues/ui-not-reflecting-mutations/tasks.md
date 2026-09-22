# ui-not-reflecting-mutations — tasks

- [ ] T1 — Move the four staged files from
  `issues/ui-not-reflecting-mutations/tests/frontend/tests/hooks/` to
  `frontend/tests/hooks/`, verbatim. Confirm red: **10 failed | 1 passed (11)**,
  with the messages recorded in `plan.md`. Covers: E1–E10.
- [ ] T2 — If issue 6 has not already landed: add `refetchNow()` to
  `frontend/src/realtime/pollingEngine.js` (unconditional fetch, `disposed`
  guard, scheduled polls left conditional) and expose it through
  `usePolling.js` and `useLibraryPicker.js`. Do not change
  `applyMutationMarker`. Covers: E1–E10 (enabler), E11 (unchanged).
- [ ] T3 — Call `refetchNow()` after `applyMutationMarker` in
  `useLibrary.js:80` (delete). Covers: E1.
- [ ] T4 — Same in `useRules.js:93` and `:114`. Covers: E2, E3.
- [ ] T5 — Same in `useShoppingList.js:92`, `:110`, `:129`, `:149`.
  Covers: E4, E5, E6, E7, E8.
- [ ] T6 — Same in `useWeekPlanner.js:115` and `:140`. Covers: E9, E10.
- [ ] T7 — Confirm E11 and the regression suites listed in `plan.md` are green,
  run `./init.sh` green, and record the `E<n>` -> `T<n>` -> test map in
  `progress/impl_ui-not-reflecting-mutations.md`. Note there which of issue 6's
  files this changeset already contains, so the two are not applied twice.
