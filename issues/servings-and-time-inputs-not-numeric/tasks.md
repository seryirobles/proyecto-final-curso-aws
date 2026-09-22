# servings-and-time-inputs-not-numeric — tasks

- [ ] T1 — Move the three staged files from `issues/servings-and-time-inputs-not-numeric/tests/`
  to the destinations listed in `plan.md` § *Test plan*, verbatim. Confirm red:
  4 frontend failures and 6 backend failures, with the messages recorded in
  `plan.md` § *Red result at triage*. Covers: E1, E2, E3, E6.
- [ ] T2 — In `buildManualRecipe` (`frontend/src/hooks/useRecipeAuthoring.js`),
  send `servings` as an integer, or `null` when the field is blank. Leave
  `estimatedTime` passing through untouched. Covers: E1, E2, E7.
- [ ] T3 — In `frontend/src/components/RecipeAuthoringForm.jsx`, render
  *Comensales* as `type="number"` with `step="1"` and no `min`/`max`; leave
  *Tiempo estimado* as `type="text"`. Covers: E3, E4, E5.
- [ ] T4 — In `decode_recipe`
  (`backend/lambda_api/src/planner_api/serialization.py`), accept `servings`
  only as an integer or `null`; anything else raises `MalformedRequest`. Do not
  touch `Recipe` — the domain stays permissive about the value (`G-85`).
  Covers: E6.
- [ ] T5 — Correct the two live tests that assert the old payload shape
  (`frontend/tests/hooks/useRecipeAuthoring.test.js:55`,
  `frontend/tests/hooks/useLibrary.test.js:187`) to the contract shape. Do not
  edit any staged test.
- [ ] T6 — Run `./init.sh` green and record the `E<n>` -> `T<n>` -> test map in
  `progress/impl_servings-and-time-inputs-not-numeric.md`.
