# new-recipe-not-shown-in-library — analysis

## Defect, one sentence

After a successful `POST /v1/library/recipes` the library view stores the
mutation's `ETag` as its held polling marker without ever applying the created
recipe to the data it renders, so every subsequent conditional `GET` matches
that marker and returns `304`, and the list stays on its pre-mutation contents
until a reload discards the marker.

## Reproduction

Automated, at the hook seam with a real polling engine and only the network
faked — staged as
`issues/new-recipe-not-shown-in-library/tests/frontend/tests/hooks/useLibraryMutationVisibility.test.js`.

```
cp issues/new-recipe-not-shown-in-library/tests/frontend/tests/hooks/useLibraryMutationVisibility.test.js \
   frontend/tests/hooks/
cd frontend && npx vitest run tests/hooks/useLibraryMutationVisibility.test.js
```

Observed (2026-09-21, vitest 4.1.10):

```
× E1: a recipe created from the library view appears in it without a reload
    expected [ 'Lentejas' ] to deeply equal [ 'Lentejas', 'Tortilla' ]
× E2: an edit made from the library view appears in it without a reload
    expected [ 'Lentejas' ] to deeply equal [ 'Lentejas estofadas' ]
✓ E3: polling stays conditional on the post-mutation marker
```

Expected: the created/edited recipe is in `recipes` after the mutation resolves
and 60 s of polling. The fixture's own pre-assertion (`['Lentejas']` after the
first poll) passes, so the failure is the stale list specifically, not broken
wiring. E3 passing is part of the evidence: the client is provably sending
`If-None-Match: "42"` — the marker its own write produced — which is exactly why
the server answers `304` and the new row never arrives.

The copy was deleted after the run; `frontend/` and `backend/` are unchanged.

## Root cause

`frontend/src/hooks/useLibrary.js:42`

```js
picker.applyMutationMarker(marker); // design.md section 4.2
```

The library view's rendered data has exactly one source: the polling engine's
snapshot (`useLibraryPicker.js:33-38` → `poll.data?.recipes`). `handleSubmit`
never touches that snapshot; it only hands the engine the marker the mutation
returned.

`frontend/src/realtime/pollingEngine.js:133-137` then takes the R25 branch
(`resolveMutationMarker`, lines 34-39): the returned marker is held+1 — which it
always is for a client's own single write, `ADD marcaCambio 1`
(`docs/data_model.md` §1.1) — so it is stored and **no refetch is scheduled**.
The engine now holds marker N+1 with the payload from marker N. Every later poll
sends `If-None-Match: "N+1"` (`realtime/conditionalGet.js:9`), the server answers
`304` (`backend/lambda_api/src/planner_api/handler.py:85`), and
`pollingEngine.js:97` deliberately leaves `data` untouched. The stale list is now
permanent: only a page reload builds a fresh engine with `marker: null` — the
manual refresh in the report.

The engine behaves as specified; the call site's use of it is wrong.
`docs/rest_api_contract.md` §6, *Every response carries the marker, including
mutations*, licenses the skipped refetch on one condition: "the writer **applies
its own change locally**, stores the returned marker, and its next poll `304`s
instead of refetching what it already has." No frontend hook does the first half.
`specs/frontend_spa/design.md` §4.2 shows the hand-off as marker-only, and the
local application was never built — `progress/impl_frontend_spa.md` lines 147-155.

Violates `FR-LIB-01` (the view must show all recipes in the shared library; it
shows a list missing one) and `FR-RT-01` (shared-library changes reflected in
real time). Note the asymmetry that makes this easy to misdiagnose: *other* users
see the new recipe within one poll, because their held marker is older and they
get a `200`. Only the writer's own session is poisoned.

## Blast radius

Every `applyMutationMarker` call site, because none of them applies its own
change locally — the cause is the pattern, not this one line:

| Call site | Operations |
|---|---|
| `useLibrary.js:42` | library create (`POST`) and edit (`PUT`) — **this issue** |
| `useLibrary.js:80` | library delete — **issue 10**, same cause |
| `useRules.js:93,114` | rule save, rule delete |
| `useShoppingList.js:92,110,129,149` | add item, check/uncheck, edit, delete |
| `useWeekPlanner.js:115,140` | promote definitive, clear definitive |

Not affected: `useAdminAccounts`, `useSession`, `useSummary` (no
`applyMutationMarker`; the summary is read-only).

Cross-reference, not duplicated here: **issue 10** (`ui-not-reflecting-mutations`)
reports the delete symptom and asks for the audit of all operations — the table
above is that audit's input, and a fix at the engine/`usePolling` seam closes both
issues at once. **Issue 2** (`blank-screen-after-login`) is a render/session
transition with no mutation marker in its path; treat it as unrelated unless its
own triage finds otherwise.

## Classification

`defect` — the code violates `FR-LIB-01` and `FR-RT-01`, and violates the
condition `docs/rest_api_contract.md` §6 attaches to skipping the post-mutation
refetch. No `G-xx` sanctions a reload-to-see-your-own-write; `G-88` decided
polling as the real-time transport, not that a writer waits for a reload.
