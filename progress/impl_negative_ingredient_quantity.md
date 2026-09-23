# impl_negative_ingredient_quantity

Issue 7. Covers both ingredient quantity (E1-E6) and servings (E7-E12, `G-91`
Part AA).

## Red at T1/T9

```
cd backend && uv run pytest core/tests/domain/test_ingredient_quantity.py \
  lambda_api/tests/test_ingredient_quantity_rejected.py \
  core/tests/domain/test_servings_count.py lambda_api/tests/test_servings_rejected.py -q
18 failed, 10 passed  (9/4 quantity + 9/6 servings, matches plan.md)

cd frontend && npx vitest run tests/hooks/useRecipeAuthoring.quantity.test.js \
  tests/components/RecipeAuthoringForm.quantity.test.jsx \
  tests/hooks/useRecipeAuthoring.servingsBound.test.js \
  tests/components/RecipeAuthoringForm.servingsBound.test.jsx
Test Files  4 failed (4)   Tests  18 failed | 3 passed (21)
```

## Fix

Both fields follow the existing `parse_estimated_minutes`/`InvalidEstimatedTime`
pattern (G-90) in `backend/core/src/planner_core/domain/recipe.py`:
- `InvalidIngredientQuantity`/`parse_quantity(value) -> float` — strictly `> 0`.
- `InvalidServings`/`parse_servings_count(value) -> int | None` — `None` passes,
  `<= 0` raises.

Wired at the two entry points named in `plan.md`: `ai_output.py`'s
`validate_ai_recipe_output` (both fields resolved, both exceptions added to
`validate_and_preview`'s catch tuple, E2/E3/E8/E9), and
`serialization.py`'s `decode_ingredient`/`parse_servings` (E1/E7). New
`errors.py` `_TABLE` rows: `InvalidIngredientQuantity` -> 422
`INVALID_INGREDIENT_QUANTITY`, `InvalidServings` -> 422 `INVALID_SERVINGS`.
Two new `messages.py` es-ES constants. `docs/rest_api_contract.md` §3 item 8
and §4 updated.

Frontend: `useRecipeAuthoring.js`'s `canSubmit` for `scratch` now blocks on
any ingredient row or `form.servings` holding a non-blank value that is not
strictly positive (blank stays issue 5's territory, E4/E10).
`RecipeAuthoringForm.jsx`: `min="0"` on both the quantity and *Comensales*
inputs (E6/E12); an inline `honey`-coloured warning (matching
`ConnectionLostBanner`/`SetPasswordView`'s established idiom) renders
`MESSAGES.RECIPE_AUTHORING_INVALID_QUANTITY`/`_SERVINGS` while that field is
non-blank and `<= 0` (E5/E11). No `role`/`aria-*` (R22).

**Superseded live test**, per `plan.md`'s table:
`RecipeAuthoringForm.servings.test.jsx`'s `bounds Comensales with no min or
max` case — dropped its `min` assertion (now contradicted by E12), kept the
`max` assertion, retitled, file header updated to note `min="0"` moved to
`RecipeAuthoringForm.servingsBound.test.jsx`. `test_recipe.py`'s
`test_recipe_accepts_any_servings_and_estimated_time_value` left unchanged,
as directed (constructor stays permissive by design).

## Traceability

| E<n> | FR-* | T<n> | Test |
|---|---|---|---|
| E1 | FR-SHOP-06, FR-SHOP-01, FR-LIB-03, FR-UX-03 | T4/T5 | `test_ingredient_quantity_rejected.py` |
| E2 | FR-AI-04, FR-LIB-03, FR-SHOP-06 | T3 | `test_ingredient_quantity.py::test_ai_output_validation_rejects_a_non_positive_quantity` |
| E3 | FR-AI-12 (G-48, G-66) | T3 | `test_ingredient_quantity.py::test_a_non_positive_quantity_surfaces_as_a_generation_failure` |
| E4 | FR-LIB-03, FR-CAND-03, FR-SHOP-06 | T6 | `useRecipeAuthoring.quantity.test.js` |
| E5 | FR-UX-03, FR-LIB-03, FR-CAND-03 | T7 | `RecipeAuthoringForm.quantity.test.jsx` |
| E6 | FR-UX-02, FR-LIB-03 | T6 | same file, "bounds the quantity stepper" |
| E7 | FR-LIB-03 (amended), FR-LIB-02, FR-CAND-03, FR-UX-03 | T12 | `test_servings_rejected.py` |
| E8 | FR-LIB-03 (amended), FR-AI-13 | T11 | `test_servings_count.py::test_ai_output_validation_rejects_a_non_positive_servings` |
| E9 | FR-AI-12 (G-48, G-66) | T11 | `test_servings_count.py::test_a_non_positive_servings_surfaces_as_a_generation_failure` |
| E10 | FR-LIB-03 (amended), FR-CAND-03 | T13 | `useRecipeAuthoring.servingsBound.test.js` |
| E11 | FR-UX-03, FR-LIB-03 (amended) | T13 | `RecipeAuthoringForm.servingsBound.test.jsx` |
| E12 | FR-UX-02, FR-LIB-03 (amended) | T13 | same file, "bounds the servings stepper" |

## Result

Backend: `uv run pytest -q -m "not aws and not docker"` — **931 passed**
(includes the 28 new/moved cases). `ruff format --check` / `ruff check` /
`mypy` clean. Frontend: `npx vitest run` — **423/423**. `npx eslint .` / `npx
prettier --check .` clean. `./init.sh` green.

`issue_list.json`/`feature_list.json` untouched by this implementer. Not
`done` — reviewer next (batched with the other five issues in this run).

## Fix round 1 — reviewer finding (comment ceiling)

`frontend/tests/components/RecipeAuthoringForm.servings.test.jsx:2-7` was a
6-line header comment (merged with issue 11's cross-references), over
`docs/conventions.md`'s 3-line ceiling. Cut to a single 3-line pointer,
content unchanged. `npx vitest run
tests/components/RecipeAuthoringForm.servings.test.jsx` — 3/3 still pass.
`./init.sh` green (949 backend / 436 frontend). No test edited or weakened.
