# new-recipe-not-shown-in-library — tasks

- [x] T1 — Move `issues/new-recipe-not-shown-in-library/tests/frontend/tests/hooks/useLibraryMutationVisibility.test.js` to `frontend/tests/hooks/useLibraryMutationVisibility.test.js`, byte-identical; run it and confirm E1 and E2 fail on the stale-list assertion and E3 passes. Covers: E1, E2, E3.
- [x] T2 — Add an unconditional refetch to `frontend/src/realtime/pollingEngine.js`: thread `force` through `poll`/`pollNow` so a forced poll calls `fetchResource(null)`, keep the scheduled poll conditional, and export `refetchNow()` guarded by `disposed`. Covers: E1, E2, E3.
  (Already delivered by issue 10, fixed first in this batch — `fetchAndApply(marker)`
  refactor + `refetchNow()` = `fetchAndApply(null)`, same guarantee, different
  internal shape than `plan.md`'s literal `force` flag.)
- [x] T3 — Expose `refetchNow` from `frontend/src/hooks/usePolling.js` and pass it through `frontend/src/hooks/useLibraryPicker.js`. Covers: E1, E2.
  (Already delivered by issue 10.)
- [x] T4 — Call `picker.refetchNow()` after the successful create/edit in `handleSubmit`, `frontend/src/hooks/useLibrary.js`. Covers: E1, E2.
- [x] T5 — Run `frontend`'s full suite and `./init.sh`; confirm `pollingEngine.test.js`, `usePolling.test.js`, `useLibrary.test.js` and `App.polling.test.jsx` are unchanged and green, and that E3 is still green. Covers: E1, E2, E3.
- [x] T6 — Record the `FR → E → T → test` map in `progress/impl_new-recipe-not-shown-in-library.md`, noting that `useLibrary.js`'s delete site and the `useRules`/`useShoppingList`/`useWeekPlanner` sites are deliberately untouched and belong to issue 10. Covers: E1, E2, E3.
