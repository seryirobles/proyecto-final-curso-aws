# negative-ingredient-quantity — tasks

- [x] T1 — Move the four staged files from `issues/negative-ingredient-quantity/tests/` to the destinations listed in `plan.md`, verbatim. Confirm red: 9 failed / 4 passed on the two backend modules, 3 failed / 1 passed on `useRecipeAuthoring.quantity.test.js`, 6 failed on `RecipeAuthoringForm.quantity.test.jsx`. Covers: E1, E2, E3, E4, E5, E6.
- [x] T2 — Add `InvalidIngredientQuantity` and `parse_quantity` to `backend/core/src/planner_core/domain/recipe.py`, and the es-ES constant to `backend/core/src/planner_core/messages.py`. Covers: E1, E2.
- [x] T3 — Resolve the quantity through `parse_quantity` in `validate_ai_recipe_output`, and add the new exception to `validate_and_preview`'s `except` tuple, in `backend/core/src/planner_core/domain/ai_output.py`. Covers: E2, E3.
- [x] T4 — Resolve the quantity through `parse_quantity` in `decode_ingredient` (`backend/lambda_api/src/planner_api/serialization.py`). Covers: E1.
- [x] T5 — Map the exception to `422` / `INVALID_INGREDIENT_QUANTITY` in `backend/lambda_api/src/planner_api/errors.py`, and add the matching row to `docs/rest_api_contract.md` section 4. Covers: E1.
- [x] T6 — Require every ingredient row to satisfy `Number(quantity) > 0` in `canSubmit` for the `scratch` method (`frontend/src/hooks/useRecipeAuthoring.js`), and add `min="0"` to the quantity input (`frontend/src/components/RecipeAuthoringForm.jsx`). Covers: E4, E6.
- [x] T7 — Add `RECIPE_AUTHORING_INVALID_QUANTITY` to `frontend/src/messages/es-ES.js` (same text as the backend constant) and render it inside an ingredient row while that row's quantity is non-blank and not greater than zero (`frontend/src/components/RecipeAuthoringForm.jsx`). No `role`/`aria-*`. Covers: E5.
- [x] T8 — Run `./init.sh` green and record the E -> T -> test map in `progress/impl_negative_ingredient_quantity.md`. Covers: E1, E2, E3, E4, E5, E6.

Servings extension (`G-91`, Part AA, landed 2026-09-23):

- [x] T9 — Move the four `servings` staged files to the destinations in `plan.md`, verbatim. Confirm red: 9 failed / 6 passed on the two backend modules, 9 failed / 2 passed on the two `servingsBound` frontend files. Covers: E7, E8, E9, E10, E11, E12.
- [x] T10 — Add `InvalidServings` and `parse_servings_count` to `backend/core/src/planner_core/domain/recipe.py`, and `INVALID_SERVINGS` to `backend/core/src/planner_core/messages.py`. Covers: E7, E8.
- [x] T11 — Resolve `servings` through `parse_servings_count` in `validate_ai_recipe_output` and catch `InvalidServings` in `validate_and_preview` (`backend/core/src/planner_core/domain/ai_output.py`); update its G-85 docstring. Covers: E8, E9.
- [x] T12 — Call `parse_servings_count` from `parse_servings` after the type check (`serialization.py`); map `InvalidServings` to `422` / `INVALID_SERVINGS` in `errors.py`; update `docs/rest_api_contract.md` sections 3 (item 8) and 4. Covers: E7.
- [x] T13 — `canSubmit` for `scratch` also requires a blank or strictly positive `form.servings` (`useRecipeAuthoring.js`); `min="0"` on the *Comensales* input and the `RECIPE_AUTHORING_INVALID_SERVINGS` warning inside its label (`RecipeAuthoringForm.jsx`, `es-ES.js`). No `role`/`aria-*`. Covers: E10, E11, E12.
- [x] T14 — Supersede the live `bounds Comensales with no min or max` case as `plan.md` directs, then `./init.sh` green and extend the E -> T -> test map. Covers: E7, E8, E9, E10, E11, E12.
