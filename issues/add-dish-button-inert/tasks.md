# add-dish-button-inert — tasks

- [ ] T1 — Move `issues/add-dish-button-inert/tests/frontend/tests/components/WeekPlannerView.candidateAuthoring.test.jsx` to `frontend/tests/components/` verbatim; run it and confirm all 5 cases fail with "Unable to find an element with the text: Elegir de la biblioteca" and friends. Covers: E1, E2, E3, E4.
- [ ] T2 — Add `frontend/src/components/CandidateAuthoring.jsx`: `useRecipeAuthoring({ mode: 'candidate', onSubmit })` + `RecipeAuthoringForm` + a `MESSAGES.RECIPE_DETAIL_CLOSE` button calling `onClose`. Covers: E1.
- [ ] T3 — Add `candidatesUrl()` and `submitCandidate(input)` to `frontend/src/hooks/useWeekPlanner.js` (POST the §3.1 body, `applyMutationMarker` the response ETag, clear `authoringTarget`, `setError(toDetail(err))` on failure) and return `submitCandidate`. Covers: E2, E3, E4.
- [ ] T4 — Render `<CandidateAuthoring>` from `frontend/src/components/WeekPlannerView.jsx` while `authoringTarget` is non-null, wired to `submitCandidate` / `closeCandidateAuthoring`. Covers: E1, E2.
- [ ] T5 — Run the full frontend suite plus `eslint`/`prettier`, then `./init.sh`; the 5 staged cases pass and no existing test changed. Covers: E1, E2, E3, E4.
