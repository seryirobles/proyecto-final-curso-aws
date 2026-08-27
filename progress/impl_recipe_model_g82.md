# Implementation report — feature 4 `recipe_model`, G-82 amendment

> Implementer session, 2026-08-24. Scope: sync `IngredientCategory` to the
> six-member, single-axis vocabulary the human's gate decision `G-82`
> (`docs/gaps_and_resolutions.md` Part R) closed FR-RULE-04's ellipsis at,
> after the spec (`specs/recipe_model/{requirements,design,tasks}.md`) was
> already amended. `VEGETARIAN = "vegetarian"` -> `VEGETABLE = "vegetable"`;
> `EGGS = "eggs"` (already present in source) is now covered by tests and
> guards. Feature left `in_progress` — the reviewer closes it, not this agent.

---

## 1. Result

`./init.sh` -> **exit 0**, every gate green: `ruff format`, `ruff check`,
`mypy --strict`, `pytest` (**71 passed**, same count as before this change —
tests were edited in place, none added or removed), `prettier --check`,
`eslint`, `vitest` (frontend untouched).

`rg -i vegetarian backend/` -> **zero hits** (confirmed after clearing
`.mypy_cache`/`__pycache__`, which held one stale binary match each).

---

## 2. Files changed

| Path | Change |
|---|---|
| `backend/core/src/planner_core/domain/ingredient_category.py` | `VEGETARIAN = "vegetarian"` -> `VEGETABLE = "vegetable"`, declaration order unchanged (`EGGS` last). Docstring rewritten to state the six-member set and cite `G-82` alongside `G-69`; kept to a 3-line body per `docs/conventions.md` § *Comments*. First draft used an em dash, which failed R15 (ASCII-only guard) — replaced with a semicolon. |
| `backend/core/tests/domain/test_ingredient_category.py` | `test_the_ingredient_category_vocabulary_is_closed` now asserts all six codes/names in declaration order (added `vegetable`, `eggs`). `test_parse_category_resolves_every_code` now exercises all six codes. `test_parse_category_rejects_a_value_outside_the_list`'s existing values (`"MEAT"`, `" meat"`, `"dairy"`, `""`) were checked against the new six-member set — all four remain genuinely outside it, so left unchanged; `"vegetarian"` was deliberately **not** added as a rejected-value case, since the literal word would violate the zero-hits `rg -i vegetarian` check. |
| `backend/core/tests/test_shared_kernel_guards.py` | R8 guard regex `INGREDIENT_CATEGORY_VOCABULARY`: `MEAT\|FISH\|CARBOHYDRATE\|LEGUME\|VEGETARIAN` -> `MEAT\|FISH\|CARBOHYDRATE\|LEGUME\|VEGETABLE\|EGGS`. Self-test fixture line `'    VEGETARIAN: str = "vegetarian"'` -> `'    VEGETABLE: str = "vegetable"'`, still asserted to match the pattern so the guard's own self-test still proves it fires. |

No other file touched. `backend/core/src/planner_core/domain/recipe.py` needed
no change — it references `IngredientCategory` only by type, never by member
name. `prototypes/`, `frontend/`, `docs/frontend_prototype.md` and
`progress/review_recipe_model.md` were not touched, per the leader's
constraint.

---

## 3. Traceability

| `R<n>` (amended text, `specs/recipe_model/requirements.md`) | Test |
|---|---|
| R4 — closed enum is exactly `MEAT, FISH, CARBOHYDRATE, LEGUME, VEGETABLE, EGGS` | `test_the_ingredient_category_vocabulary_is_closed` |
| R5 — `parse_category` resolves every member's code | `test_parse_category_resolves_every_code` (all six codes, `"eggs"` and `"vegetable"` included) |
| R6 — rejects a value outside the list | `test_parse_category_rejects_a_value_outside_the_list` |
| R7 — `UnknownIngredientCategory` derives from `PlannerError` | `test_unknown_ingredient_category_is_a_planner_error` (unchanged, still passes) |
| R8 — no second category vocabulary anywhere in `planner_core` | `test_planner_core_has_one_ingredient_category_vocabulary` |
| R15 — ASCII-only shared kernel modules | `test_the_shared_kernel_modules_are_ascii_only` (this caught my own first-draft em dash) |

`FR-RULE-04` (amended enumeration) and `FR-LIB-03`/`FR-AI-04` (which reach the
set by reference, per `G-82`'s "deliberately not changed" note) all remain
reachable through the same R4–R8 chain the original feature 4 traceability
map (`progress/impl_recipe_model.md` §3) already established; nothing in that
map's shape changed, only the six concrete values it proves.

---

## 4. Something the spec did not fully anticipate

The task brief's own verification step (`rg -i vegetarian backend/` must be
zero) is stricter than a literal reading of "VEGETARIAN must not survive" —
it also forbids the lowercase word in prose. My first docstring draft wrote
"vegetarian was struck as a diet label, not an ingredient" to explain the
change, which would have failed that check; likewise my first test draft
added `"vegetarian"` to the rejected-values tuple to prove the old code is now
rejected. Both were rewritten to convey the same fact without the literal
string (docstring: "the earlier diet-label member was struck"; test: no
`"vegetarian"` literal at all, relying on R4/R5's exhaustive six-member
assertions to make the omission provable). Recorded here since the spec files
listed as authoritative do not mention this constraint explicitly — it came
from the leader's own reporting instructions.

---

## 5. Boundary checks

| Check | Result |
|---|---|
| Architecture §2 decisions | None taken; this change only executes the human's own `G-82` decision. |
| Frozen docs | None edited — `docs/requirements.md` and `docs/gaps_and_resolutions.md` were read-only inputs, already amended by the human before this session. |
| `feature_list.json` | Untouched; feature 4 stays `in_progress`. |
| Git | No `git add`/`commit`/other write command run. |
| Categories beyond six / `VEGETARIAN` under any spelling | None added; `rg -i vegetarian backend/` confirms zero hits. |
