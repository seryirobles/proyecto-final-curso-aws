# add-dish-button-inert — analysis

## Defect, one sentence

"Añadir plato" only records `authoringTarget` inside `useWeekPlanner`: no
component ever renders the candidate authoring flow and no code path ever
`POST`s to `…/slots/{slot}/candidates`, so the click changes nothing on
screen and nothing in the database.

## Reproduction

Reproduced by test, against the current tree (no running environment needed):
the staged file copied to
`frontend/tests/components/WeekPlannerView.candidateAuthoring.test.jsx`, driven
through the real `useWeekPlanner` + `WeekPlannerView` pair (`usePolling` and
`apiFetch` mocked, as in the existing `useWeekPlanner.test.js`):

```
cd frontend && npx vitest run tests/components/WeekPlannerView.candidateAuthoring.test.jsx
Test Files  1 failed (1)      Tests  5 failed (5)
```

Observed: after clicking the day-3 / lunch "Añadir plato" button the DOM is
unchanged — `Unable to find an element with the text: Elegir de la biblioteca`
(likewise `Escribir desde cero`, `Generar con IA`), and `apiFetch` is never
called with a candidates URL. Expected: the three-method authoring flow opens
(`FR-CAND-02`) and submitting it adds the candidate (`FR-CAND-01`).

The click handler itself is wired and does fire — the already-green
`useWeekPlanner.test.js` case *"openCandidateAuthoring records the target
day/slot/weekId"* proves the state is set. The chain breaks after that.

## Root cause

Two halves of one missing wiring, both in the frontend presentation/state
layer (`docs/architecture.md` §3):

1. `frontend/src/components/WeekPlannerView.jsx:15-30` — the destructured prop
   list has no `authoringTarget`, and the returned JSX (lines 33-77) never
   renders `RecipeAuthoringForm`. `App.jsx:156` spreads the whole hook
   (`<WeekPlannerView {...weekPlanner} />`), so `authoringTarget` and
   `closeCandidateAuthoring` do arrive and are silently dropped.
2. `frontend/src/hooks/useWeekPlanner.js:92-96` — `openCandidateAuthoring` only
   calls `setAuthoringTarget`. The hook holds no `useRecipeAuthoring` instance
   and no submit handler; its return (lines 150-169) exposes no way to add a
   candidate. Compare `useLibrary.js:32-58`, which does exactly this for the
   library and works.

The endpoint this should call exists and is implemented:
`POST /v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates`
(`docs/rest_api_contract.md` §3.1, table row at line 127;
`backend/lambda_api/src/planner_api/routing.py:824`). No backend fault.

Violated requirements: **`FR-CAND-01`** (a user shall be able to add candidate
meals for any day/slot) and **`FR-CAND-02`** (the three authoring methods),
expressed as `R6` in `specs/frontend_spa/requirements.md`. Feature 20 claims
`FR-CAND-02` in its `covers` and is marked `done`.

How it slipped through: `specs/frontend_spa/tasks.md` T14/T15 wired the
*opener* only, and `progress/impl_frontend_spa.md:180` records the intent
("the future `RecipeAuthoringForm`'s `onSubmit` needs `weekId`") — but no task
ever mounted that form in the week view. T22/T23 built
`useRecipeAuthoring({ mode: 'candidate' })`, which to this day has **zero**
production call sites.

Not a deliberate resolution: `docs/gaps_and_resolutions.md` removes neither
`FR-CAND-01` nor `-02`, and the AI method being a disabled stub
(`specs/frontend_spa/design.md` §1.3, feature 28) concerns only the third tab,
which is rendered.

## Blast radius

- `useRecipeAuthoring` with `mode: 'candidate'` is dead code today — grep shows
  `useLibrary.js:53` (`mode: 'library'`) as the only caller. The fix gives it
  its first real call site; the `library` method's picker embed (`R12`) is
  exercised for the first time from this flow.
- `closeCandidateAuthoring` (`useWeekPlanner.js:96`) is likewise unreferenced.
- **Adjacent, same cause, out of scope:** the week view also offers no candidate
  **edit** (`PUT …/candidates/{id}`) and no candidate **remove**
  (`DELETE …/candidates/{id}`) — `MealCard.jsx:56` carries only
  detail/promote/clear — so the other two thirds of `FR-CAND-01` are equally
  unreachable. The report names the add button; this issue fixes only the add
  path. **Recommend the human open a separate issue for candidate edit/remove.**
- No other view shares the bug: library, rules and shopping all mount their
  authoring/editing UI.
- Constraint measured while prototyping (in a scratch copy; repo untouched):
  putting `useRecipeAuthoring` *inside* `useWeekPlanner` adds two
  `useLibraryPicker` → `usePolling` calls to every week render and breaks three
  existing live tests (`useWeekPlanner.test.js`'s two `toHaveBeenLastCalledWith`
  assertions, and `App.polling.test.jsx`'s idle-view-stays-flat case). See
  `plan.md` § *Rejected alternatives*.

## Classification

`defect` — built code violates frozen `FR-CAND-01` and `FR-CAND-02`.

Severity: reported **high**; confirmed high. Putting a dish into the week is
the application's primary action and it is unreachable from the UI.
