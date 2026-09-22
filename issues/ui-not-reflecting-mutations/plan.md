# ui-not-reflecting-mutations — plan

## Expected behaviour

One rule, stated once per operation so the human can approve them separately.
In every statement, "without a page reload" means within the same session, with
no dependence on the next scheduled poll.

### E1
Implements: `FR-LIB-01`, `FR-LIB-02`

WHEN a recipe is deleted from the library view, the system SHALL remove that
recipe from the library view's list without a page reload.

### E2
Implements: `FR-RULE-02`, `FR-RULE-06`

WHEN a rule is saved from the rules view, the system SHALL show that rule in
the rules view's list without a page reload.

### E3
Implements: `FR-RULE-02`, `FR-RULE-06`

WHEN a rule is deleted from the rules view, the system SHALL remove that rule
from the rules view's list without a page reload.

### E4
Implements: `FR-SHOP-01`, `FR-SHOP-02`

WHEN an item is added from the shopping-list view, the system SHALL show that
item in the list without a page reload.

### E5
Implements: `FR-SHOP-01`, `FR-SHOP-02`

WHEN an item is edited from the shopping-list view, the system SHALL show the
edited values in the list without a page reload.

### E6
Implements: `FR-SHOP-07`, `FR-SHOP-08`

WHEN an item is checked from the shopping-list view, the system SHALL move that
item to the checked section without a page reload.

### E7
Implements: `FR-SHOP-01`, `FR-SHOP-02`

WHEN an item is deleted from the shopping-list view, the system SHALL remove
that item from the list without a page reload.

### E8
Implements: `FR-SHOP-03`, `FR-SHOP-06`

WHEN a re-sync is run from the shopping-list view, the system SHALL show the
items it produced without a page reload.

### E9
Implements: `FR-MENU-03`, `FR-CAND-05`

WHEN a candidate is promoted to definitive from the week planner, the system
SHALL show it as the slot's definitive without a page reload.

### E10
Implements: `FR-MENU-03`, `FR-CAND-08`

WHEN a slot's definitive is cleared from the week planner, the system SHALL
show the slot without a definitive without a page reload.

### E11
Implements: `FR-RT-01` (`G-88`)

WHEN a mutation returns a marker that is not the held marker plus one, the
system SHALL discard the returned marker and refetch the resource.

## Fix design

Layer: the SPA only (`docs/architecture.md` §3). No backend change — the API
already returns the new marker, the new payload and a correct `304`; the client
poisons its own cache.

**This issue and issue 6 share one fix.** Issue 6's `plan.md` already specifies
the engine change (a `force` flag through `poll`/`pollNow`, exported as
`refetchNow()`, threaded through `usePolling` and `useLibraryPicker`) and
applies it at `useLibrary.js:42`. This plan adds **the same one-line call at
the nine remaining call sites**, and nothing else.

| File | Change |
|---|---|
| `frontend/src/realtime/pollingEngine.js` | *(issue 6)* `refetchNow()` = an unconditional poll (`fetchResource(null)`), with the existing `disposed` guard. Scheduled polls stay conditional. |
| `frontend/src/hooks/usePolling.js` | *(issue 6)* return `refetchNow` alongside `applyMutationMarker`. |
| `frontend/src/hooks/useLibraryPicker.js` | *(issue 6)* pass `refetchNow` through. |
| `frontend/src/hooks/useLibrary.js:80` | Call `picker.refetchNow()` after `applyMutationMarker(marker)` in `remove`. E1. |
| `frontend/src/hooks/useRules.js:93,114` | Same call after both `applyMutationMarker`s. E2, E3. |
| `frontend/src/hooks/useShoppingList.js:92,110,129,149` | Same call after all four. E4–E8. |
| `frontend/src/hooks/useWeekPlanner.js:115,140` | Same call after both. E9, E10. |

`applyMutationMarker`'s R25/R26 behaviour is not changed, so E11 and
`frontend/tests/realtime/pollingEngine.test.js:206` stay green. If issue 6 is
declined and this one approved, its engine/`usePolling`/`useLibraryPicker` rows
move into this changeset unchanged — they are three files and no behaviour
overlap.

No new dependency, no new message string, no backend or doc change.

### Rejected alternatives

**Apply each mutation's response body to the polled snapshot locally** — the
literal optimistic path of `docs/rest_api_contract.md` §6. Cheapest in
requests. Rejected because it needs per-resource merge logic at ten call sites,
and for the shopping list (`FR-SHOP-06` outstanding amounts) and the week plan
that logic is server-derived state recomputed in the client, which
`docs/conventions.md` § *Separation of concerns* forbids.

**Make `applyMutationMarker` itself always refetch**, dropping R25. One line,
fixes all ten at once. Rejected because it deletes a proven behaviour of a
`done` feature (`pollingEngine.test.js:206`, R25) instead of adding to it, and
it removes the only path that distinguishes a self-write from a concurrent one.

## Test plan

| Staged | Destination |
|---|---|
| `issues/ui-not-reflecting-mutations/tests/frontend/tests/hooks/useLibrary.mutationVisibility.test.js` | `frontend/tests/hooks/useLibrary.mutationVisibility.test.js` |
| `issues/ui-not-reflecting-mutations/tests/frontend/tests/hooks/useRules.mutationVisibility.test.js` | `frontend/tests/hooks/useRules.mutationVisibility.test.js` |
| `issues/ui-not-reflecting-mutations/tests/frontend/tests/hooks/useShoppingList.mutationVisibility.test.js` | `frontend/tests/hooks/useShoppingList.mutationVisibility.test.js` |
| `issues/ui-not-reflecting-mutations/tests/frontend/tests/hooks/useWeekPlanner.mutationVisibility.test.js` | `frontend/tests/hooks/useWeekPlanner.mutationVisibility.test.js` |

Each mounts the real hook with the real `usePolling`/`createPollingEngine` and
fakes only `globalThis.fetch`, with a server that bumps its marker by one per
write and answers `304` on a matching `If-None-Match` — the mechanics of
`docs/rest_api_contract.md` §6. Each settles **10 ms**, far below one poll
interval, so a fix that merely waits for the next scheduled poll does not pass.

| `E<n>` | Test | At triage |
|---|---|---|
| E1 | `a confirmed delete removes the recipe from the rendered list (E1)` (reproduction of the report) | **RED** — `expected [ 'r-1', 'r-2' ] to deeply equal [ 'r-2' ]` |
| E2 | `a saved category-count rule appears in the rendered list (E2)` | **RED** — `expected [] to deeply equal [ 'meat' ]` |
| E3 | `a confirmed rule delete drops it from the rendered list (E3)` | **RED** — `expected [ 'meat', 'fish' ] to deeply equal [ 'fish' ]` |
| E4 | `an added item appears in the rendered list (E4)` | **RED** — `expected [ 'Item i-1' ] to deeply equal [ 'Item i-1', 'lentejas' ]` |
| E5 | `an edited quantity is shown on the item (E5)` | **RED** — `expected [ 2 ] to deeply equal [ 500 ]` |
| E6 | `checking an item moves it to the checked section (E6)` | **RED** — the item stays unchecked |
| E7 | `a confirmed remove drops the item from the rendered list (E7)` | **RED** — `expected [ 'i-1', 'i-2' ] to deeply equal [ 'i-2' ]` |
| E8 | `a re-sync shows the ingredients it added (E8)` | **RED** — `expected [ 'i-1' ] to deeply equal [ 'i-1', 'auto-1' ]` |
| E9 | `promoting a candidate shows it as the definitive of the slot (E9)` | **RED** — `expected null to be 'c-2'` |
| E10 | `a confirmed clear empties the definitive of the slot in the grid (E10)` | **RED** — `expected 'c-1' to be null` |
| E11 | `a delete whose marker jumps by more than one still refreshes the list (E11)` | **GREEN, and must stay green** |

### Red result at triage (2026-09-22)

Copied to the destinations, run, deleted; the live tree was left as found
(`git status --porcelain` clean apart from `issue_list.json` and `issues/`).

```
cd frontend && npx vitest run tests/hooks/use*.mutationVisibility.test.js
Test Files  4 failed (4)      Tests  10 failed | 1 passed (11)
```

Every failure is the stale snapshot; each fixture's pre-mutation assertion
passes first, so the wiring is sound and the list is what is wrong.

Regression suites the fix must leave green:
`frontend/tests/realtime/pollingEngine.test.js`,
`frontend/tests/hooks/usePolling.test.js`,
`frontend/tests/hooks/useLibrary.test.js`,
`frontend/tests/hooks/useRules.test.js`,
`frontend/tests/hooks/useShoppingList.test.js`,
`frontend/tests/hooks/useWeekPlanner.test.js`,
`frontend/tests/components/App.polling.test.jsx`.
