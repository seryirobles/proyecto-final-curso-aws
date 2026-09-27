# Implementation report — feature 30 `library_delete_pin_cascade_ui`

## Files changed

- `frontend/src/messages/es-ES.js` — two new keys, `LIBRARY_REMOVE_PIN_CASCADE_WARNING`
  and `LIBRARY_REMOVE_PIN_CASCADE_CONFIRM` (T1).
- `frontend/src/hooks/useLibrary.js` — factored `deleteRecipe(recipeId, { confirmCascade })`;
  added local `formatPin`/`composeCascadeMessage` helpers; `remove`'s catch
  block special-cases `err.code === 'PIN_RULES_AFFECTED'` to re-arm the
  existing `confirm` instance with the cascade prompt and retry thunk (T2, T3).
- `frontend/tests/hooks/useLibrary.pinCascade.test.js` — new (T4).
- `specs/library_delete_pin_cascade_ui/tasks.md` — T1-T5 ticked.

No file under `backend/` touched — `git diff --stat -- backend/` is empty.

## Traceability — FR → R<n> → T<n> → test

| FR-* (cited, not in `covers`) | R<n> | T<n> | Test |
|---|---|---|---|
| FR-RULE-07 | R1 | T3 | `useLibrary.pinCascade.test.js` — "a 409 opens a second confirmation..." |
| FR-RULE-07, FR-UX-01, FR-UX-03 | R2 | T1, T2 | same test — asserts `pending.message` contains `'domingo'` and `'Comida'` |
| FR-RULE-07 | R3 | T2, T3 | same test — asserts retry URL `.../recipes/r-1?confirmCascade=true` and 2 DELETE calls |
| FR-RULE-07, FR-UX-04 | R4 | T3 | "cancelling the second confirmation issues no retry..." — 1 DELETE call, recipe present |
| FR-RULE-07 | R5 | T2, T3 | direct assertion added in the R1/R2/R3/R6 test: `deleteCalls[0][0] === '/v1/library/recipes/r-1'` (no `confirmCascade` on the first attempt) |
| FR-RULE-07 | R6 | T2 | "a 409 opens..." test — `recipes` no longer contains `r-1` after the cascade retry + poll settle |
| FR-RULE-07, FR-UX-01, FR-UX-03 | R7 | T3 | "a non-cascade rejection sets error to detail verbatim..." + "the cascade retry's own rejection sets error to detail verbatim, recipe untouched" (covers the retry's own failure explicitly named by T3) + pre-existing `useLibrary.test.js` R15 case (regression guard, untouched) |

### Reviewer round 1 — CHANGES_REQUESTED, addressed

One surviving mutant: `remove`'s cascade-retry catch (`setError(toDetail(retryErr))`
→ `setError(null)`) went undetected because no test made the `?confirmCascade=true`
retry itself fail. Added
`"the cascade retry's own rejection sets error to detail verbatim, recipe untouched (T3)"`
to `useLibrary.pinCascade.test.js` (a 404 `NOT_FOUND` on the cascade retry;
asserts `error === 'X'` and the recipe stays listed). Also added the optional
direct R5 assertion (first DELETE URL carries no `confirmCascade`) in the
existing R1/R2/R3/R6 test. Manually reproduced the named mutant, confirmed it
now fails the new test, then reverted — mutant killed.

Rules-view propagation (acceptance criterion 4's "disappears from... the
rules view") is out of scope per design.md §5 — no new code, covered by
feature 26's existing polling tests.

## Test results

`./init.sh`: all green (re-run after the round-1 fix).
- Backend: 1043 passed, 8 deselected (unchanged — no backend file touched).
- Frontend: full Vitest suite green, including the 4
  `useLibrary.pinCascade.test.js` tests and the pre-existing
  `useLibrary.test.js` (R15/R18) and `useLibrary.mutationVisibility.test.js`
  suites.
- `git diff --stat -- backend/` — empty (acceptance criterion 1).
- Named mutant (`setError(toDetail(retryErr))` → `setError(null)` in the
  cascade-retry catch) manually reproduced and confirmed killed by the new
  test, then reverted.
