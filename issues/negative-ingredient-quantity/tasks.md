# negative-ingredient-quantity — tasks

- [ ] T1 — Move the four staged files from `issues/negative-ingredient-quantity/tests/` to the destinations listed in `plan.md`, verbatim. Confirm red: 9 failed / 4 passed on the two backend modules, 3 failed / 1 passed on `useRecipeAuthoring.quantity.test.js`, 6 failed on `RecipeAuthoringForm.quantity.test.jsx`. Covers: E1, E2, E3, E4, E5, E6.
- [ ] T2 — Add `InvalidIngredientQuantity` and `parse_quantity` to `backend/core/src/planner_core/domain/recipe.py`, and the es-ES constant to `backend/core/src/planner_core/messages.py`. Covers: E1, E2.
- [ ] T3 — Resolve the quantity through `parse_quantity` in `validate_ai_recipe_output`, and add the new exception to `validate_and_preview`'s `except` tuple, in `backend/core/src/planner_core/domain/ai_output.py`. Covers: E2, E3.
- [ ] T4 — Resolve the quantity through `parse_quantity` in `decode_ingredient` (`backend/lambda_api/src/planner_api/serialization.py`). Covers: E1.
- [ ] T5 — Map the exception to `422` / `INVALID_INGREDIENT_QUANTITY` in `backend/lambda_api/src/planner_api/errors.py`, and add the matching row to `docs/rest_api_contract.md` section 4. Covers: E1.
- [ ] T6 — Require every ingredient row to satisfy `Number(quantity) > 0` in `canSubmit` for the `scratch` method (`frontend/src/hooks/useRecipeAuthoring.js`), and add `min="0"` to the quantity input (`frontend/src/components/RecipeAuthoringForm.jsx`). Covers: E4, E6.
- [ ] T7 — Add `RECIPE_AUTHORING_INVALID_QUANTITY` to `frontend/src/messages/es-ES.js` (same text as the backend constant) and render it inside an ingredient row while that row's quantity is non-blank and not greater than zero (`frontend/src/components/RecipeAuthoringForm.jsx`). No `role`/`aria-*`. Covers: E5.
- [ ] T8 — Run `./init.sh` green and record the E -> T -> test map in `progress/impl_negative_ingredient_quantity.md`. Covers: E1, E2, E3, E4, E5, E6.
