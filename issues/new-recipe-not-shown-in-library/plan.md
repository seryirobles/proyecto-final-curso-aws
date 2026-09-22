# new-recipe-not-shown-in-library — plan

## Expected behaviour

### E1
Implements: `FR-LIB-01`, `FR-LIB-02`, `FR-RT-01`

WHEN a recipe is created from the library view, the system SHALL show that
recipe in the library view's recipe list without a page reload.

### E2
Implements: `FR-LIB-02`, `FR-RT-01`

WHEN a library recipe is edited from the library view, the system SHALL show the
edited content in the library view's recipe list without a page reload.

### E3
Implements: `FR-RT-01`

WHEN the library view polls after a mutation of its own has been reflected, the
system SHALL send the marker returned by that mutation as `If-None-Match`.

## Fix design

Layer: the SPA only (`docs/architecture.md` §3). No backend change — the API
already returns the new marker, the new payload and a correct `304`; the client
is what poisons its own cache.

The root cause is that a self-write leaves the engine holding marker N+1 with
marker N's payload. The smallest change that removes it is to give the polling
engine an **unconditional** refetch and call it at the mutation site, so the
post-write `GET` carries no `If-None-Match` and comes back `200` with the new
list. Additive throughout: `applyMutationMarker`'s R25/R26 behaviour is not
changed, and no existing test changes.

| File | Change |
|---|---|
| `frontend/src/realtime/pollingEngine.js` | Thread a `force` flag through `poll`/`pollNow` (`fetchResource(force ? null : snapshot.marker)`), and export `refetchNow()` = `pollNow(true)` with the existing `disposed` guard. Keep the scheduled poll conditional: `setTimeoutFn(() => poll(), delay)`. |
| `frontend/src/hooks/usePolling.js` | Return `refetchNow: engine.refetchNow` alongside `applyMutationMarker`. |
| `frontend/src/hooks/useLibraryPicker.js` | Pass `refetchNow` through, beside `applyMutationMarker`. |
| `frontend/src/hooks/useLibrary.js` | In `handleSubmit` (line 42), after `picker.applyMutationMarker(marker)`, call `picker.refetchNow()`. |

`useLibrary.js:80` (delete) and the `useRules` / `useShoppingList` /
`useWeekPlanner` call sites listed in `analysis.md` § *Blast radius* take the
same one-line call, but they belong to **issue 10**; leaving them out keeps the
two changesets separable. If the human prefers one sweep, issue 10's implementer
adds the same line at those sites — no further engine work is needed.

No new dependency. No message string added.

### Rejected alternatives

**Apply the mutation's response body to the polled snapshot locally** — the
literal optimistic path of `docs/rest_api_contract.md` §6. It is the cheapest in
requests and works for the library, whose `POST`/`PUT` response is exactly a list
row. Rejected because it needs per-resource merge logic at every call site, and
for the shopping list and the week plan that logic is server-derived state
recomputed in the client, which `docs/conventions.md` § *Separation of concerns*
forbids.

**Make `applyMutationMarker` itself always refetch**, dropping R25's no-refetch
shortcut. Fewest lines, and it would fix every call site at once. Rejected
because it invalidates the existing assertion `applyMutationMarker stores held+1
without an extra fetch` (`frontend/tests/realtime/pollingEngine.test.js:206`),
i.e. it rewrites a done feature's proof instead of adding to it.

## Test plan

One staged file, all three cases in it.

| Staged | Destination |
|---|---|
| `issues/new-recipe-not-shown-in-library/tests/frontend/tests/hooks/useLibraryMutationVisibility.test.js` | `frontend/tests/hooks/useLibraryMutationVisibility.test.js` |

It mounts `useLibrary` with the real `usePolling`/`createPollingEngine` and fakes
only `globalThis.fetch`, with a fake API that bumps its marker by one per write
and answers `304` on a matching `If-None-Match` — the exact mechanics of
`docs/rest_api_contract.md` §6.

| `E<n>` | Test | At triage |
|---|---|---|
| E1 | `E1: a recipe created from the library view appears in it without a reload` | **RED** — `expected [ 'Lentejas' ] to deeply equal [ 'Lentejas', 'Tortilla' ]`: the post-`POST` polls all `304` on the marker the `POST` returned |
| E2 | `E2: an edit made from the library view appears in it without a reload` | **RED** — `expected [ 'Lentejas' ] to deeply equal [ 'Lentejas estofadas' ]`, same cause on the `PUT` path |
| E3 | `E3: polling stays conditional on the post-mutation marker` | **GREEN, and must stay green** — guards against a "fix" that abandons the marker and turns every poll into a full `200` (`G-88`, `FR-RT-01`) |

Run at triage on 2026-09-21 (`vitest 4.1.10`): `2 failed | 1 passed (3)`. The
fixture's pre-assertion — the list shows `['Lentejas']` after the first poll —
passes in all three, so the red is the stale list, not broken wiring. The copy
used for the run was deleted; `frontend/` and `backend/` were left unchanged.

Regression suites the fix must leave green: `frontend/tests/realtime/pollingEngine.test.js`,
`frontend/tests/hooks/usePolling.test.js`, `frontend/tests/hooks/useLibrary.test.js`,
`frontend/tests/components/App.polling.test.jsx`.
