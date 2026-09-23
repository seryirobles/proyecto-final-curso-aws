# impl_new-recipe-not-shown-in-library

Issue 6. Same root cause and engine fix as issue 10 (fixed first in this
batch); this issue's own scope is the library create/edit call site only.

## Red at T1

```
cp issues/new-recipe-not-shown-in-library/tests/frontend/tests/hooks/useLibraryMutationVisibility.test.js frontend/tests/hooks/
cd frontend && npx vitest run tests/hooks/useLibraryMutationVisibility.test.js
Test Files  1 failed (1)      Tests  2 failed | 1 passed (3)
```
Matches `plan.md`'s recorded red exactly (E1/E2 red, E3 green).

## Fix

T2/T3 (the `pollingEngine.js`/`usePolling.js`/`useLibraryPicker.js`
`refetchNow()` plumbing) were already delivered by issue 10's implementation
earlier in this same run — internal shape differs slightly from `plan.md`'s
literal "thread a `force` flag" (issue 10 used a shared `fetchAndApply(marker)`
helper instead), but the external contract `plan.md` specifies
(`refetchNow()` = unconditional fetch, `disposed`-guarded, scheduled polls
stay conditional, `applyMutationMarker` untouched) is identical. T4: one line
added in `useLibrary.js`'s `handleSubmit`, `picker.refetchNow()` after
`picker.applyMutationMarker(marker)` — covers both the `POST` (create) and
`PUT` (edit) paths, since both go through the same function.

`useLibrary.js:80` (delete) and the `useRules`/`useShoppingList`/
`useWeekPlanner` sites are issue 10's territory and were fixed there, not
here — verified via `git diff` that this session's issue-6-specific change is
exactly the one line above.

## Traceability

| E<n> | FR-* | T<n> | Test |
|---|---|---|---|
| E1 | FR-LIB-01, FR-LIB-02, FR-RT-01 | T4 | `useLibraryMutationVisibility.test.js` "E1: a recipe created..." |
| E2 | FR-LIB-02, FR-RT-01 | T4 | same file "E2: an edit made..." |
| E3 | FR-RT-01 | T2/T3 (guard, unchanged) | same file "E3: polling stays conditional..." — stays green |

## Result

`cd frontend && npx vitest run` — **402/402** (399 → 402: the 3 staged E1-E3
cases newly counted as this file's own pass, delta from issue 10's 399 is the
net of 1 new file's cases already present as red - now green, +... exact
delta: file was already present from the `cp` above, net +3 over issue 10's
running total since this file didn't exist before this issue's T1). `npx
eslint .` / `npx prettier --check .` clean. `./init.sh` green (backend
unaffected — no `backend/` file touched).

`issue_list.json`/`feature_list.json` untouched by this implementer. Not
`done` — reviewer next (batched with the other five issues in this run).
