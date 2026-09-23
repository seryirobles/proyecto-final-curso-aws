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

---

**Scope extension, 2026-09-22** (owner: *"fix all three now"*). `analysis.md`
§ *Blast radius* recorded candidate **edit** and **remove** as the same missing
wiring, out of the original scope; they are now in it. E1–E4 above are
implemented and reviewed — E5–E10 are additive and must not change them.

### E5
Implements: `FR-CAND-01`, `FR-CAND-02`

WHEN a user activates the edit control of a meal in the week view, the system
SHALL open the candidate authoring flow seeded with that meal's current recipe
content and offering its three methods.

### E6
Implements: `FR-CAND-01`, `FR-CAND-02`, `FR-CAND-05`

WHEN the seeded authoring flow is submitted, the system SHALL send the
`rest_api_contract.md` §3.1 discriminated body as `PUT
/v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates/{candidateId}` for the
meal whose control was activated.

### E7
Implements: `FR-UX-04`

WHEN a user activates the remove control of a meal, the system SHALL request an
explicit confirmation before issuing any request.

### E8
Implements: `FR-CAND-01`

WHEN the removal is confirmed, the system SHALL send `DELETE
/v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates/{candidateId}` for that
meal.

### E9
Implements: `FR-RT-01`

WHEN a candidate edit or removal succeeds, the system SHALL apply the
response's `ETag` marker to the week poll and close the authoring flow.

### E10
Implements: `FR-UX-03`

IF a candidate edit or removal is rejected, THEN the system SHALL display the
error's `detail` verbatim without closing an open authoring flow.

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

## Fix design — edit and remove (E5–E10, scope extension)

Same layers. One backend line joins the frontend work, because `PUT` today
accepts only a bare `{"recipe": …}` body while `FR-CAND-02` gives edit the same
three methods as add.

| File | Layer | Change |
|---|---|---|
| `frontend/src/messages/es-ES.js` | messages | `WEEK_PLANNER_EDIT_CANDIDATE: 'Editar'`, `WEEK_PLANNER_REMOVE_CANDIDATE: 'Eliminar'`, `CONFIRM_REMOVE_CANDIDATE: '¿Eliminar este plato de este hueco?'`. |
| `frontend/src/components/MealCard.jsx` | component | Two more action buttons next to promote/clear, wired to `onEdit` / `onRemove`; rendered for a definitive meal too (`FR-CAND-05`: it edits like any candidate). |
| `frontend/src/components/DaySlot.jsx` | component | Pass `onEdit={() => onEdit(day, slotState.slot, candidate)}` and `onRemove={() => onRemove(day, slotState.slot, candidate.id)}` through to `MealCard`, same shape as `onPromote`/`onClear`. |
| `frontend/src/components/WeekPlannerView.jsx` | component | Destructure `openCandidateEdit`, `removeCandidate`, `editingTarget`, `submitCandidateEdit`, `closeCandidateEdit`; hand the first two to `DaySlot`; render `<CandidateAuthoring initialRecipe={editingTarget.recipe} onSubmit={submitCandidateEdit} onClose={closeCandidateEdit} />` while `editingTarget` is non-null. |
| `frontend/src/components/CandidateAuthoring.jsx` | component | Accept an optional `initialRecipe`; pass it plus `initialMethod: 'scratch'` when editing, so the form opens on the meal's own content instead of the library tab. |
| `frontend/src/hooks/useRecipeAuthoring.js` | hook | Optional `initialMethod`, defaulting to `methods[0]` — three tokens, no behaviour change for the two existing callers. |
| `frontend/src/hooks/useWeekPlanner.js` | hook | New `editingTarget` state + `openCandidateEdit(day, slot, candidate)` / `closeCandidateEdit`; `submitCandidateEdit(input)` = `mutateWithMarker(candidateUrl, { method: 'PUT', body: input })` then marker + clear, `setError(toDetail(err))` on failure; `removeCandidate(day, slot, candidateId)` = `confirm.requestConfirm(MESSAGES.CONFIRM_REMOVE_CANDIDATE, …DELETE…)`, the same shape as `clearDefinitive`. |
| `backend/lambda_api/src/planner_api/routing.py` | lambda_api | `_edit_candidate`: when the body carries a `source`, resolve it through the existing `_resolve_meal_source(body, deps)`; otherwise keep today's `snapshot(decode_recipe(require_field(body, "recipe")))`. |
| `docs/rest_api_contract.md` | doc | The `PUT …/candidates/{candidateId}` row states it takes the same §3.1 body as `POST` (both are `AP13`, *Editar o añadir comida*). |

`authoringTarget` (the add path) is deliberately left untouched — a separate
`editingTarget` keeps the live assertion
`expect(result.current.authoringTarget).toEqual({ weekId, day, slot })`
(`useWeekPlanner.test.js:128`) green, and keeps the reviewed add work intact.
**No live test changes for E5–E10.**

### Rejected alternatives (E5–E10)

1. **Edit through the from-scratch tab only**, leaving `PUT` as it is. Frontend
   only, zero backend risk — but the library and AI tabs would then 400 on
   edit, so `FR-CAND-02` ("when adding/**editing**… one of three authoring
   methods") would stay half-unmet and the user would meet a raw error.
2. **Resolve a library pick client-side** (`GET` the recipe, `PUT` its content).
   Also frontend only, but it re-introduces exactly what §3.1 rejects for the
   add path: a tamperable, extra-round-trip client copy instead of the
   server-side one.

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

## Test plan — edit and remove (E5–E10, scope extension)

Staged, additive; the E1–E4 file above is already live and must not be touched.

| Staged file | Destination |
|---|---|
| `issues/add-dish-button-inert/tests/frontend/tests/components/WeekPlannerView.candidateEditRemove.test.jsx` | `frontend/tests/components/WeekPlannerView.candidateEditRemove.test.jsx` |
| `issues/add-dish-button-inert/tests/backend/lambda_api/tests/test_candidate_edit_sources.py` | `backend/lambda_api/tests/test_candidate_edit_sources.py` |

| Test | Covers |
|---|---|
| exposes the week-view edit and remove copy through MESSAGES | E5, E7 (reproduction) |
| opens the authoring flow seeded with the meal's content when "Editar" is clicked | E5 (reproduction) |
| PUTs the edited recipe to the meal's own candidate endpoint | E6 |
| applies the response ETag marker and closes the form after a successful edit | E9 |
| renders a rejected edit's detail verbatim and keeps the form open | E10 |
| asks for confirmation before removing a meal and sends nothing until it is confirmed | E7 (reproduction) |
| DELETEs the meal and applies the response ETag marker once the removal is confirmed | E8, E9 |
| renders a rejected removal's detail verbatim | E10 |
| `test_editing_a_candidate_from_a_library_recipe_copies_its_content` | E6 |
| `test_editing_a_candidate_from_scratch_uses_the_manual_body` | E6 |
| `test_editing_a_candidate_still_accepts_the_bare_recipe_body` | regression (no client break) |
| `test_editing_a_candidate_with_an_unknown_library_recipe_is_not_found` | E6 |

**Red at triage** (2026-09-22, copied to the destinations, run, deleted; tree
left as found):

- `cd frontend && npx vitest run tests/components/WeekPlannerView.candidateEditRemove.test.jsx`
  → **Test Files 1 failed (1), Tests 8 failed (8)**. Seven are
  `TestingLibraryElementError: Unable to find an element with the text: Editar`
  / `: Eliminar` — the meal card carries no edit or remove control at all, the
  cause in `analysis.md` § *Blast radius*; the eighth is
  `expected undefined to be 'Editar'` (the copy does not exist either).
- `cd backend && uv run pytest lambda_api/tests/test_candidate_edit_sources.py -q`
  → **2 failed, 2 passed**: both `library`-arm cases fail `assert 400 == 200`
  / `assert 400 == 404` (`PUT` rejects the §3.1 body for want of a `recipe`
  key); the `manual` and bare-`{recipe}` cases pass today and must stay green.
- `uv run mypy .` (whole backend workspace, staged file in place): clean.
  `ruff format --check` / `ruff check` / `eslint` / `prettier --check`: clean.
