# recipe-saved-without-required-sections — tasks

- [ ] T1 — Move the three staged files from `issues/recipe-saved-without-required-sections/tests/` to the destinations listed in `plan.md`, verbatim. Confirm red: 15 failed / 3 passed on the two backend modules, 4 failed / 1 passed on the frontend module. Covers: E1, E2, E3, E4, E5, E6.
- [ ] T2 — Add `MissingIngredients`, `MissingTools`, `MissingProcedure` and `require_recipe_sections` to `backend/core/src/planner_core/domain/recipe.py`, and the three es-ES constants to `backend/core/src/planner_core/messages.py`. Do not touch `Recipe.__post_init__` (G-89). Covers: E1, E2, E3, E4.
- [ ] T3 — Call `require_recipe_sections` in `decode_recipe` (`backend/lambda_api/src/planner_api/serialization.py`), before the `Recipe` is built. Covers: E1, E2, E3.
- [ ] T4 — Map the three exceptions to `422` in `backend/lambda_api/src/planner_api/errors.py`, and add the matching rows to `docs/rest_api_contract.md` §4. Covers: E1, E2, E3.
- [ ] T5 — Call `require_recipe_sections` in `validate_ai_recipe_output` and add the three exceptions to `validate_and_preview`'s `except` tuple (`backend/core/src/planner_core/domain/ai_output.py`). Covers: E4, E5.
- [ ] T6 — Require a non-empty `ingredients`, `tools` and `procedure` in `canSubmit` for the `scratch` method (`frontend/src/hooks/useRecipeAuthoring.js`), replacing the `// no client validation` comment. Covers: E6.
- [ ] T7 — Correct the four live fixtures listed in `plan.md` § *Live fixtures the fix makes red* by adding the missing item; change no assertion. Covers: E7.
- [ ] T8 — Run `./init.sh` green and record the E -> T -> test map in `progress/impl_recipe_saved_without_required_sections.md`. Covers: E1, E2, E3, E4, E5, E6, E7.
