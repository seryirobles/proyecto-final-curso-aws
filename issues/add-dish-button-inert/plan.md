# add-dish-button-inert — plan

## Expected behaviour

### E1
Implements: `FR-CAND-02`

WHEN a user activates "Añadir plato" for a day and slot, the system SHALL open
the candidate authoring flow offering exactly its three methods (library pick,
from scratch, AI).

### E2
Implements: `FR-CAND-01`, `FR-CAND-02`

WHEN a user submits the candidate authoring flow, the system SHALL send the
`rest_api_contract.md` §3.1 discriminated body as `POST
/v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates` for the day and slot
whose button was activated.

### E3
Implements: `FR-RT-01`

WHEN the candidate `POST` succeeds, the system SHALL apply the response's
`ETag` marker to the week poll and close the authoring flow.

### E4
Implements: `FR-UX-03`

IF the candidate `POST` fails, THEN the system SHALL display the error's
`detail` verbatim and keep the authoring flow open.

## Fix design

Frontend only (presentation + view-state layers, `docs/architecture.md` §3).
No backend change, no new message key, no new dependency.

| File | Change |
|---|---|
| `frontend/src/components/CandidateAuthoring.jsx` (new) | Calls `useRecipeAuthoring({ mode: 'candidate', onSubmit })` and renders `RecipeAuthoringForm` plus a `MESSAGES.RECIPE_DETAIL_CLOSE` button wired to `onClose`. Mounted only while a slot is being authored, so its two `useLibraryPicker` instances exist — and poll — only then. |
| `frontend/src/hooks/useWeekPlanner.js` | Add `candidatesUrl(weekId, day, slot)` and `submitCandidate(input)`: `apiFetch(..., { method: 'POST', body: input, onHeaders })`, then `weekPoll.applyMutationMarker(marker)`, `setError(null)`, `setAuthoringTarget(null)`; `catch` → `setError(toDetail(err))` (same shape as `promoteDefinitive`). Export `submitCandidate`. |
| `frontend/src/components/WeekPlannerView.jsx` | Destructure `authoringTarget`, `submitCandidate`, `closeCandidateAuthoring`; render `<CandidateAuthoring onSubmit={submitCandidate} onClose={closeCandidateAuthoring} />` when `authoringTarget` is non-null. |

`App.jsx` already spreads the whole hook into the view — no change there.

Prototyped in a scratch copy of `frontend/` (repo untouched): the five staged
tests pass and the full suite stays green (`Test Files 52 passed, Tests 354
passed`), `eslint`/`prettier` clean.

### Rejected alternatives

1. **Hold `useRecipeAuthoring` in `useWeekPlanner`** (mirroring `useLibrary`)
   and render `<RecipeAuthoringForm {...authoring} />` from the view. Measured:
   the staged tests pass, but the hook's two `useLibraryPicker` instances then
   call `usePolling('/v1/library/recipes')` on every week render — three
   existing tests fail (`useWeekPlanner.test.js` × 2 on
   `toHaveBeenLastCalledWith`, `App.polling.test.jsx`'s idle-views-stay-flat)
   and the week view polls the library with no form open.
2. **Same, gated with `active: authoringTarget !== null`.** Stops the wasted
   polling, but the extra `usePolling(...)` call still happens on every week
   render, so the two `toHaveBeenLastCalledWith` assertions still fail. Keeping
   a live test green is worth one small presentational component.

## Test plan

Staged, mirroring its destination:

| Staged file | Destination |
|---|---|
| `issues/add-dish-button-inert/tests/frontend/tests/components/WeekPlannerView.candidateAuthoring.test.jsx` | `frontend/tests/components/WeekPlannerView.candidateAuthoring.test.jsx` |

Driven through the real `useWeekPlanner` + `WeekPlannerView` pair with
`usePolling` and `apiFetch` mocked — it asserts user-visible behaviour and the
outgoing request, not any particular internal prop name.

| Test | Covers |
|---|---|
| opens the three-method authoring flow when "Añadir plato" is clicked | E1 (reproduction) |
| POSTs a library pick to the clicked slot's candidates endpoint | E2 |
| POSTs a from-scratch recipe as the manual source body | E2 |
| applies the response ETag marker and closes the form after a successful add | E3 |
| renders the rejected add's detail verbatim and keeps the form open | E4 |

**Red at triage** (2026-09-21, copy run then deleted):
`npx vitest run tests/components/WeekPlannerView.candidateAuthoring.test.jsx`
→ `Test Files 1 failed (1)  Tests 5 failed (5)`. Every failure is
`TestingLibraryElementError: Unable to find an element with the text: …`
(`Elegir de la biblioteca`, `Escribir desde cero`, `Seleccionar`) — i.e. the
click renders nothing, exactly the cause in `analysis.md`.

No existing test needs to change: the whole live suite (`npx vitest run`,
51 files) is green today and stays green under the fix above.
