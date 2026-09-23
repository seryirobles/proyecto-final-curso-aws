# add-dish-button-inert — tasks

- [x] T1 — Move `issues/add-dish-button-inert/tests/frontend/tests/components/WeekPlannerView.candidateAuthoring.test.jsx` to `frontend/tests/components/` verbatim; run it and confirm all 5 cases fail with "Unable to find an element with the text: Elegir de la biblioteca" and friends. Covers: E1, E2, E3, E4.
- [x] T2 — Add `frontend/src/components/CandidateAuthoring.jsx`: `useRecipeAuthoring({ mode: 'candidate', onSubmit })` + `RecipeAuthoringForm` + a `MESSAGES.RECIPE_DETAIL_CLOSE` button calling `onClose`. Covers: E1.
- [x] T3 — Add `candidatesUrl()` and `submitCandidate(input)` to `frontend/src/hooks/useWeekPlanner.js` (POST the §3.1 body, `applyMutationMarker` the response ETag, clear `authoringTarget`, `setError(toDetail(err))` on failure) and return `submitCandidate`. Covers: E2, E3, E4.
- [x] T4 — Render `<CandidateAuthoring>` from `frontend/src/components/WeekPlannerView.jsx` while `authoringTarget` is non-null, wired to `submitCandidate` / `closeCandidateAuthoring`. Covers: E1, E2.
- [x] T5 — Run the full frontend suite plus `eslint`/`prettier`, then `./init.sh`; the 5 staged cases pass and no existing test changed. Covers: E1, E2, E3, E4.

Scope extension 2026-09-22 (owner: "fix all three now") — candidate edit and
remove. T1–T5 are done and reviewed; do not revisit them.

- [x] T6 — Move `issues/add-dish-button-inert/tests/frontend/tests/components/WeekPlannerView.candidateEditRemove.test.jsx` and `issues/add-dish-button-inert/tests/backend/lambda_api/tests/test_candidate_edit_sources.py` to their destinations verbatim; confirm 8 frontend cases fail ("Unable to find an element with the text: Editar"/"Eliminar", plus "expected undefined to be 'Editar'") and 2 of the 4 backend cases fail (`assert 400 == 200`, `assert 400 == 404`). Covers: E5, E6, E7, E8, E9, E10.
- [x] T7 — Add `WEEK_PLANNER_EDIT_CANDIDATE: 'Editar'`, `WEEK_PLANNER_REMOVE_CANDIDATE: 'Eliminar'` and `CONFIRM_REMOVE_CANDIDATE: '¿Eliminar este plato de este hueco?'` to `frontend/src/messages/es-ES.js`. Covers: E5, E7.
- [x] T8 — Render the two new action buttons in `frontend/src/components/MealCard.jsx` (`onEdit`, `onRemove`), for a definitive meal as well as a candidate (`FR-CAND-05`), and pass them per candidate from `frontend/src/components/DaySlot.jsx`. Covers: E5, E7.
- [x] T9 — Add `initialMethod` (defaulting to `methods[0]`) to `frontend/src/hooks/useRecipeAuthoring.js`, and an optional `initialRecipe` prop to `frontend/src/components/CandidateAuthoring.jsx` that opens the form on the from-scratch tab seeded with that recipe. Covers: E5.
- [x] T10 — Add `editingTarget` + `openCandidateEdit` / `closeCandidateEdit` / `submitCandidateEdit` (PUT `…/candidates/{candidateId}`, apply the ETag marker, clear the target) and `removeCandidate` (confirm-gated DELETE, apply the marker) to `frontend/src/hooks/useWeekPlanner.js`; leave `authoringTarget` and `submitCandidate` exactly as they are. Covers: E6, E7, E8, E9, E10.
- [x] T11 — Wire the new hook members through `frontend/src/components/WeekPlannerView.jsx`, mounting `<CandidateAuthoring initialRecipe={…} />` while `editingTarget` is non-null. Covers: E5, E6, E9, E10.
- [x] T12 — In `_edit_candidate` (`backend/lambda_api/src/planner_api/routing.py`), resolve a body carrying `source` through the existing `_resolve_meal_source(body, deps)`, keeping the bare `{"recipe": …}` path for bodies without one; state the same on the `PUT …/candidates/{candidateId}` row of `docs/rest_api_contract.md` §2. Covers: E6.
- [x] T13 — Run the full backend and frontend suites plus `ruff`/`mypy`/`eslint`/`prettier`, then `./init.sh`; the 12 new cases pass, and no test from T1–T5 or any other live suite changed. Covers: E5, E6, E7, E8, E9, E10.
