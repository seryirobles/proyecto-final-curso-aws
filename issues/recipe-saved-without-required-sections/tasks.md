# recipe-saved-without-required-sections — tasks

- [x] T1 — Move the three staged files from `issues/recipe-saved-without-required-sections/tests/` to the destinations listed in `plan.md`, verbatim. Confirm red: 15 failed / 3 passed on the two backend modules, 4 failed / 1 passed on the frontend module. Covers: E1, E2, E3, E4, E5, E6.
- [x] T2 — Add `MissingIngredients`, `MissingTools`, `MissingProcedure` and `require_recipe_sections` to `backend/core/src/planner_core/domain/recipe.py`, and the three es-ES constants to `backend/core/src/planner_core/messages.py`. Do not touch `Recipe.__post_init__` (G-89). Covers: E1, E2, E3, E4.
- [x] T3 — Call `require_recipe_sections` in `decode_recipe` (`backend/lambda_api/src/planner_api/serialization.py`), before the `Recipe` is built. Covers: E1, E2, E3.
- [x] T4 — Map the three exceptions to `422` in `backend/lambda_api/src/planner_api/errors.py`, and add the matching rows to `docs/rest_api_contract.md` §4. Covers: E1, E2, E3.
- [x] T5 — Call `require_recipe_sections` in `validate_ai_recipe_output` and add the three exceptions to `validate_and_preview`'s `except` tuple (`backend/core/src/planner_core/domain/ai_output.py`). Covers: E4, E5.
- [x] T6 — Require a non-empty `ingredients`, `tools` and `procedure` in `canSubmit` for the `scratch` method (`frontend/src/hooks/useRecipeAuthoring.js`), replacing the `// no client validation` comment. Covers: E6.
- [x] T7 — Correct the live fixtures the fix makes red by adding the missing item; change no assertion. `plan.md` named four; the actual blast radius was wider (disclosed in `progress/impl_recipe_saved_without_required_sections.md`) — all corrected the same way. Covers: E7.
- [x] T8 — Run `./init.sh` green and record the E -> T -> test map in `progress/impl_recipe_saved_without_required_sections.md`. Covers: E1, E2, E3, E4, E5, E6, E7.

Scope extension (2026-09-23):

- [x] T9 — Move `issues/recipe-saved-without-required-sections/tests/frontend/tests/components/RecipeAuthoringForm.requiredSections.test.jsx` to `frontend/tests/components/RecipeAuthoringForm.requiredSections.test.jsx`, verbatim. Confirm red: 6 failed, each at the missing `RECIPE_AUTHORING_MISSING_*` key. Covers: E8.
- [x] T10 — Add `RECIPE_AUTHORING_MISSING_INGREDIENTS`, `RECIPE_AUTHORING_MISSING_TOOLS`, `RECIPE_AUTHORING_MISSING_PROCEDURE` to `frontend/src/messages/es-ES.js`, and in `ScratchFields` (`frontend/src/components/RecipeAuthoringForm.jsx`) render each as a `tokens.color.honey` span after that section's rows, before its *Añadir …* button, while the section is empty. No hook change. Covers: E8.
- [x] T11 — Re-run the moved file green (byte-identical to staged), keep `RecipeAuthoringForm.test.jsx`, `RecipeAuthoringForm.quantity.test.jsx`, `RecipeAuthoringForm.servingsBound.test.jsx` and `WeekPlannerView.candidateAuthoring.test.jsx` green, run `./init.sh` green, and extend the map in `progress/impl_recipe_saved_without_required_sections.md`. Covers: E7, E8.
