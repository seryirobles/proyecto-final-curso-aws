# servings-and-time-inputs-not-numeric — implementation report

## Summary

Root cause per `issues/servings-and-time-inputs-not-numeric/analysis.md`: the
from-scratch form's *Comensales* input was `type="text"` and
`buildManualRecipe` passed `form.servings` through unconverted, so the API
received a string (blank posts `""`); `decode_recipe` had no wire-type parse
for `servings`, so a bad value was *persisted* rather than rejected — a blank
`servings` stores an unreadable `numeroComensales` and later 500s on read.

**Split issue, followed exactly per the leader's note and `plan.md`/
`analysis.md`:** the *Comensales* half is the defect above — fixed. The
*Tiempo estimado* half is `not_a_defect` per `G-85` (Part U)/`FR-LIB-03` —
freeform, informational, no validation, no unit convention stated anywhere.
`estimated_time` was **not** numeric-ified; the staged tests (E5, E7) lock
its current free-text behaviour and were not touched beyond being moved
verbatim into place.

## Fix

Matches `plan.md` § *Fix design* exactly (rejected alternatives — backend
coercion instead of rejection; frontend-only fix — are logged there, not
repeated here).

1. `frontend/src/components/RecipeAuthoringForm.jsx` — *Comensales* input
   changed `type="text"` → `type="number"` `step="1"`, no `min`/`max` added
   (issue 7 owns value-range policing). *Tiempo estimado* untouched
   (`type="text"`).
2. `frontend/src/hooks/useRecipeAuthoring.js` — `buildManualRecipe` now maps
   `servings` to `null` when blank, `Number(form.servings)` otherwise (same
   transport-cast pattern the line below already applies to
   `ingredient.quantity`). `estimatedTime` passes through unchanged.
3. `backend/lambda_api/src/planner_api/serialization.py` — new
   `parse_servings(value)`: `None` stays `None`; an `int` (excluding `bool`,
   which Python treats as an `int` subclass) passes through; anything else
   raises `MalformedRequest` (400, contract §4). Wired into `decode_recipe`.
   `Recipe`/`core` untouched — the domain stays permissive about the *value*
   (`G-85`), confirmed by `backend/core/tests/domain/test_recipe.py` staying
   green unmodified.

**Corrected, not staged, per `plan.md`'s explicit instruction** (both asserted
the old buggy payload, not test behaviour this issue exists to lock):
- `frontend/tests/hooks/useRecipeAuthoring.test.js:55` — expected body
  `servings: '4'` → `servings: 4`.
- `frontend/tests/hooks/useLibrary.test.js:187` — expected body
  `servings: '2'` → `servings: 2`. Line 162 (a *form state* assertion, not
  the built request body) was left as `'2'` — the controlled input still
  holds a string, per `plan.md`'s explicit carve-out.

**One incidental fix, not part of the staged plan:** `RecipeAuthoringForm`'s
new `step="1"` attribute tripped `frontend/tests/
test_all_strings_from_messages.test.js`'s R15 hardcoded-copy scan (a real
false positive — `step` is an HTML increment, never rendered text, same class
as the existing `width`/`height`/`cx`/`cy`/`r` entries). Added `'step'` to
that guard's `SAFE_ATTR_NAMES` allowlist, no scan-logic change.

## Traceability

| `E<n>` | `FR-*` | Test |
|---|---|---|
| E1 — submitted `servings` is a JSON integer | FR-LIB-03, FR-LIB-02, FR-CAND-03 | `useRecipeAuthoring.servings.test.js` "sends servings as a number …", "re-sends an edited recipe servings as a number …" |
| E2 — blank *Comensales* sends `servings: null` | FR-LIB-03 | `useRecipeAuthoring.servings.test.js` "sends servings as null when the field is left empty" |
| E3 — *Comensales* is a numeric, step-1 control | FR-LIB-03, FR-UX-02 | `RecipeAuthoringForm.servings.test.jsx` "renders Comensales as a numeric control stepping by one", "keeps Comensales a controlled field reporting its value" |
| E4 — no min/max on *Comensales* (G-85) | FR-LIB-03 | `RecipeAuthoringForm.servings.test.jsx` "bounds Comensales with no min or max" (green before and after — held, not newly made to pass) |
| E5 — *Tiempo estimado* stays free text (G-85) | FR-LIB-03 | `RecipeAuthoringForm.servings.test.jsx` "keeps Tiempo estimado a free-text control", "accepts a free-text Tiempo estimado value …" (green before and after — held) |
| E6 — a non-integer/non-null `servings` write is rejected | FR-LIB-03 | `test_serialization_servings.py::test_decode_recipe_rejects_an_empty_string_servings`, `…rejects_a_servings_that_is_not_an_integer[4/cuatro/4.5/True/[]]` |
| E7 — `estimatedTime` is stored as the client's string, unchanged (G-85) | FR-LIB-03, FR-AI-13 | `test_serialization_servings.py::test_decode_recipe_keeps_estimated_time_as_the_clients_free_text`; `useRecipeAuthoring.servings.test.js` "sends estimatedTime as the typed free text …", "never parses estimatedTime into a number" (green before and after — held) |

`issue_list.json`'s `covers` for issue 4 (`FR-LIB-03`, `FR-LIB-02`,
`FR-CAND-03`, `FR-UX-02`) are all reachable through E1–E7 above.

## Test moves and red→green evidence

Staged files moved verbatim (`diff` against the staged copies: empty):
- `.../tests/backend/lambda_api/tests/test_serialization_servings.py` → `backend/lambda_api/tests/test_serialization_servings.py`
- `.../tests/frontend/tests/components/RecipeAuthoringForm.servings.test.jsx` → `frontend/tests/components/RecipeAuthoringForm.servings.test.jsx`
- `.../tests/frontend/tests/hooks/useRecipeAuthoring.servings.test.js` → `frontend/tests/hooks/useRecipeAuthoring.servings.test.js`

**Red**, before any code change:
- Frontend (`npx vitest run tests/hooks/useRecipeAuthoring.servings.test.js
  tests/components/RecipeAuthoringForm.servings.test.jsx`): `2 files failed,
  4 failed | 6 passed (10)` — string-vs-number/text-vs-number mismatches.
- Backend (`uv run pytest lambda_api/tests/test_serialization_servings.py
  -q`): `6 failed, 5 passed`, all six `DID NOT RAISE MalformedRequest`.

Both match `plan.md` § *Red result at triage* exactly.

**Green**, after the fix: the three staged files, plus
`useRecipeAuthoring.test.js`, `useLibrary.test.js`,
`RecipeAuthoringForm.test.jsx`, `test_serialization.py`,
`core/tests/domain/test_recipe.py` — all pass (48 frontend / 47 backend
tests across those files).

Full suites: frontend `npx vitest run` — **56 files passed, 370 passed
(370)** (was 54/360 after issue 3 — +2 files for the 2 new staged frontend
tests, +10 tests: 6 from `useRecipeAuthoring.servings.test.js` + 4 from
`RecipeAuthoringForm.servings.test.jsx`; the backend-side staged test doesn't
count here). Backend `uv run pytest -q -m "not aws and not docker"` — **829
passed, 8 deselected** (was 818 — +11, the new staged
`test_serialization_servings.py`). `npx eslint .` / `npx prettier --check .`
/ `uv run ruff format --check .` / `uv run ruff check .` / `uv run mypy .`
all clean. `./init.sh`: fully green.

No staged test was edited, loosened, skipped or xfailed. `tasks.md` T1–T6
all ticked. `issue_list.json`: no edit made by this implementer for issue 4
(status was already `in_progress` at session start, per the batch dispatch).
