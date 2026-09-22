# ui-not-reflecting-mutations — analysis

## Defect, one sentence

Every mutation the SPA performs on a polled resource stores the marker the
write returned without applying the change to the snapshot it renders, so each
later conditional `GET` matches that marker, comes back `304`, and the view
keeps its pre-mutation contents until a reload — the reported library delete is
one of ten operations that behave this way.

## Reproduction

Automated, at the hook seam with the real `usePolling`/`createPollingEngine`
pair and only `globalThis.fetch` faked, since the defect is the interaction
between the mutation's `ETag` and the next conditional `GET`
(`docs/rest_api_contract.md` §6). Four staged files, eleven cases; 2026-09-22,
vitest 4.1.10:

```
cp issues/ui-not-reflecting-mutations/tests/frontend/tests/hooks/*.test.js frontend/tests/hooks/
cd frontend && npx vitest run tests/hooks/useLibrary.mutationVisibility.test.js ...
Test Files  4 failed (4)      Tests  10 failed | 1 passed (11)
```

The reported case, verbatim from the run:

```
× a confirmed delete removes the recipe from the rendered list (E1)
    expected [ 'r-1', 'r-2' ] to deeply equal [ 'r-2' ]
```

Each fixture asserts its pre-mutation state first, and that assertion passes
everywhere, so the failure is the stale snapshot specifically, not broken
wiring. The one pass is E11, the marker-jumped-by-more-than-one path — see
*The one path that works*, below. Copies deleted after the run; `frontend/`
and `backend/` unchanged.

## Root cause

`frontend/src/realtime/pollingEngine.js:133-137`, reached from ten call sites:

```js
applyMutationMarker(returnedMarker) {
  const resolved = resolveMutationMarker(snapshot.marker, returnedMarker);
  updateSnapshot({ marker: resolved.marker });
  if (resolved.refetch) pollNow(); // R26
}
```

`resolveMutationMarker` (lines 34-39) takes the R25 branch whenever the
returned marker is held+1 — which it always is for a client's own single write,
`ADD marcaCambio 1` (`docs/data_model.md` §1.1). The marker advances, **no
refetch is scheduled**, and no caller applies its own change to
`snapshot.data`. The engine now holds marker N+1 with the payload from marker
N. Every later poll sends `If-None-Match: "N+1"`
(`realtime/conditionalGet.js:9`), the server answers `304`
(`backend/lambda_api/src/planner_api/handler.py:85`), and
`pollingEngine.js:97` deliberately leaves `data` untouched. Only a reload
builds a fresh engine with `marker: null`.

The engine behaves as specified. `docs/rest_api_contract.md` §6, *Every
response carries the marker, including mutations*, licenses the skipped
refetch on one condition: the writer "**applies its own change locally**,
stores the returned marker, and its next poll `304`s instead of refetching
what it already has". **No hook does the first half** — the local-application
step was never built (`specs/frontend_spa/design.md` §4.2 shows the hand-off
as marker-only; `progress/impl_frontend_spa.md` lines 147-155).

This is the same root cause as **issue 6** (`new-recipe-not-shown-in-library`),
whose `analysis.md` diagnoses it at `useLibrary.js:42`. Not duplicated here:
issue 6 owns library **create** and **edit**; this issue owns the library
**delete** and the other eight operations, plus the audit below.

Note the asymmetry that makes this easy to misdiagnose: *other* users see the
change within one poll, because their held marker is older and they get a
`200`. Only the writer's own session is poisoned.

## The one path that works

E11 is green today and must stay green: when the returned marker is **not**
held+1 — someone else wrote concurrently — `resolveMutationMarker` keeps the
held marker and refetches (R26), and the view updates correctly. A fix that
repairs the common case by abandoning the marker discipline would turn every
poll into a full `200` and break `G-88` / `FR-RT-01`'s conditional-polling
design; E11 is the guard against that.

## Blast radius — audit of every mutating frontend operation

| Operation | Call site | UI updates? | Evidence |
|---|---|---|---|
| Library: create recipe (`POST`) | `useLibrary.js:42` | **No** | **Issue 6**, E1 — owned there |
| Library: edit recipe (`PUT`) | `useLibrary.js:42` | **No** | **Issue 6**, E2 — owned there |
| Library: delete recipe (`DELETE`) | `useLibrary.js:80` | **No** | E1 red: `expected [ 'r-1', 'r-2' ] to deeply equal [ 'r-2' ]` |
| Rules: save/upsert rule (`PUT`) | `useRules.js:93` | **No** | E2 red: `expected [] to deeply equal [ 'meat' ]` |
| Rules: delete rule (`DELETE`) | `useRules.js:114` | **No** | E3 red: `expected [ 'meat', 'fish' ] to deeply equal [ 'fish' ]` |
| Shopping list: add item (`POST`) | `useShoppingList.js:92` | **No** | E4 red: `expected [ 'Item i-1' ] to deeply equal [ 'Item i-1', 'lentejas' ]` |
| Shopping list: edit item (`PUT`) | `useShoppingList.js:92` | **No** | E5 red: `expected [ 2 ] to deeply equal [ 500 ]` |
| Shopping list: check / uncheck (`PATCH`) | `useShoppingList.js:110` | **No** | E6 red: the item never leaves the unchecked section |
| Shopping list: delete item (`DELETE`) | `useShoppingList.js:129` | **No** | E7 red: `expected [ 'i-1', 'i-2' ] to deeply equal [ 'i-2' ]` |
| Shopping list: re-sync (`POST`) | `useShoppingList.js:149` | **No** | E8 red: `expected [ 'i-1' ] to deeply equal [ 'i-1', 'auto-1' ]` |
| Week: promote definitive (`PUT`) | `useWeekPlanner.js:115` | **No** | E9 red: `expected null to be 'c-2'` |
| Week: clear definitive (`DELETE`) | `useWeekPlanner.js:140` | **No** | E10 red: `expected 'c-1' to be null` |
| Week: add candidate | — | n/a | **No such code path exists**: `openCandidateAuthoring` only sets state and nothing ever `POST`s a candidate — **issue 3** (`add-dish-button-inert`) |
| Week: edit / remove candidate | — | n/a | Same gap; not wired, **issue 3** territory |
| Accounts: create / rename / reset password / remove | `useAdminAccounts.js:58,84,107,124` | **Yes** | Each `await`s `refetch()` (`:22-30`), which replaces `accounts` wholesale. No marker; accounts is not one of `FR-RT-01`'s four polled resources. Proven by the live `frontend/tests/hooks/useAdminAccounts.test.js` |
| Session: log in / set password / log out | `useSession.js:39,52,59` | **Yes**, state set from the response | Not a polled resource. The blank screen after login is a separate render/transition fault — **issue 2** |
| Summary | `useSummary.js` | n/a | Read-only; no mutation |
| AI generation | — | n/a | Disabled stub (`useRecipeAuthoring.js:149`, `design.md` §1.3); feature 28 |

So: **ten operations fail, across four hooks and all four polled resources**;
two more would fail the moment issue 3 wires them, because candidate authoring
will reuse `useWeekPlanner`'s marker path; nothing outside the polling
transport is affected.

Requirements the ten violate, per resource: `FR-LIB-01` / `FR-LIB-02` (the
library view shows a recipe that no longer exists), `FR-RULE-02` /
`FR-RULE-06` (the rules list is the rule set), `FR-SHOP-01` / `FR-SHOP-02` /
`FR-SHOP-07` / `FR-SHOP-08` (the list displays every item; checking moves it
to the checked section), `FR-MENU-03` / `FR-CAND-05` / `FR-CAND-08` (the slot
shows its definitive), and `FR-RT-01` for the transport itself. Read
`FR-RT-01` precisely: its subject is *other* users, and they are in fact
served correctly; the writer's own stale view is caught by the per-resource
display requirements above, not by `FR-RT-01` alone.

## Classification

`defect` — the code violates the display requirements listed above and
breaches the condition `docs/rest_api_contract.md` §6 attaches to skipping the
post-mutation refetch. No `G-xx` sanctions a reload-to-see-your-own-write;
`G-88` decided polling as the real-time transport, not that a writer waits for
a reload.

Severity as reported: `high`. Not amended — it is every write in the app.
