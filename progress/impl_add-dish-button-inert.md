# add-dish-button-inert — implementation report

## Summary

Root cause per `issues/add-dish-button-inert/analysis.md`: "Añadir plato" only
recorded `authoringTarget` inside `useWeekPlanner` — no component ever
rendered the candidate authoring flow, and no code path ever `POST`ed to
`/v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates`. Two missing wires,
both in the frontend state/presentation layer, no backend fault.

## Fix

Matches `plan.md` § *Fix design* exactly (the two rejected alternatives —
holding `useRecipeAuthoring` inside `useWeekPlanner` directly, with or without
an `active` gate — are in `plan.md`, not repeated here; both broke 3 live
tests by polling the library on every week render).

1. `frontend/src/components/CandidateAuthoring.jsx` (new) — mounted only
   while `authoringTarget` is set, so its `useRecipeAuthoring({ mode:
   'candidate' })` instance (and the two `useLibraryPicker` polls inside it)
   exist only then. Renders `RecipeAuthoringForm` plus a
   `MESSAGES.RECIPE_DETAIL_CLOSE` button wired to `onClose`.
2. `frontend/src/hooks/useWeekPlanner.js` — added `candidatesUrl(weekId, day,
   slot)` and `submitCandidate(input)` (POSTs the §3.1 discriminated body
   `useRecipeAuthoring` already shapes, applies the response's ETag marker via
   `weekPoll.applyMutationMarker`, clears `authoringTarget` on success,
   `setError(toDetail(err))` on failure — same shape as `promoteDefinitive`/
   `clearDefinitive`). `mutateDefinitive` renamed `mutateWithMarker` (its
   generic apiFetch+marker helper is now shared by three mutations, not just
   the definitive-slot two — naming only, no behaviour change). `submitCandidate`
   added to the hook's return.
3. `frontend/src/components/WeekPlannerView.jsx` — destructures
   `authoringTarget`/`submitCandidate`/`closeCandidateAuthoring`, renders
   `<CandidateAuthoring onSubmit={submitCandidate} onClose=
   {closeCandidateAuthoring} />` when `authoringTarget` is non-null. The
   existing top-level `error` banner (already rendered) covers E4 — no new
   error-display code needed.

## Traceability

| `E<n>` (plan.md) | `FR-*` | Test |
|---|---|---|
| E1 — opens the three-method flow | FR-CAND-02 | "opens the three-method authoring flow when 'Añadir plato' is clicked" |
| E2 — POSTs the §3.1 discriminated body to the clicked slot | FR-CAND-01, FR-CAND-02 | "POSTs a library pick …", "POSTs a from-scratch recipe …" |
| E3 — applies the ETag marker, closes the form on success | FR-RT-01 | "applies the response ETag marker and closes the form after a successful add" |
| E4 — shows the rejected add's detail verbatim, keeps the form open | FR-UX-03 | "renders the rejected add's detail verbatim and keeps the form open" |

`issue_list.json`'s `covers` for issue 3 (`FR-CAND-01`, `FR-CAND-02`,
`FR-RT-01`, `FR-UX-03`) are all reachable through E1–E4 above.

## Test move and red→green evidence

Staged file moved verbatim (`diff` against the staged copy: empty):
`issues/add-dish-button-inert/tests/frontend/tests/components/
WeekPlannerView.candidateAuthoring.test.jsx` →
`frontend/tests/components/WeekPlannerView.candidateAuthoring.test.jsx`.

**Red**, before any code change (`cd frontend && npx vitest run
tests/components/WeekPlannerView.candidateAuthoring.test.jsx`): `1 file
failed, 5 failed (5)` — every failure `Unable to find an element with the
text: …` (`Elegir de la biblioteca` / `Escribir desde cero` / `Seleccionar`),
matching `plan.md` § *Red at triage* exactly (the click renders nothing).

**Green**, after the fix (same command): `1 file passed, 5 passed (5)`.

Full frontend suite (`cd frontend && npx vitest run`): **54 files passed,
360 passed (360)** (was 53/355 after issue 2 — +1 file/+5 tests, no existing
test changed). `npx eslint .` / `npx prettier --check .` clean. `./init.sh`:
fully green (818 backend passed, unaffected; ruff/mypy/prettier/eslint/vitest
all clean).

No staged test was edited, loosened, skipped or xfailed. `tasks.md` T1–T5 all
ticked. `issue_list.json`: no edit made by this implementer for issue 3 (status
was already `in_progress` at session start, per the batch dispatch).

---

## Scope extension 2026-09-23 — candidate edit and remove (E5–E10, T6–T13)

Owner ruling *"fix all three now"*: the E1–E4 add path above is implemented
and reviewed and was **not touched** — verified via `git diff` on
`CandidateAuthoring.jsx`'s original lines, `useWeekPlanner.js`'s
`authoringTarget`/`submitCandidate`, and the untouched
`WeekPlannerView.candidateAuthoring.test.jsx`. This round is additive only:
candidate **edit** (`PUT`) and **remove** (`DELETE`) — the other two thirds
of `FR-CAND-01`, same root cause (`MealCard.jsx` never wired edit/remove
controls).

### Fix

Matches `plan.md` § *Fix design — edit and remove* exactly (rejected
alternatives — edit through the scratch tab only; resolving a library pick
client-side — are in `plan.md`, not repeated here).

1. `frontend/src/messages/es-ES.js` — `WEEK_PLANNER_EDIT_CANDIDATE: 'Editar'`,
   `WEEK_PLANNER_REMOVE_CANDIDATE: 'Eliminar'`,
   `CONFIRM_REMOVE_CANDIDATE: '¿Eliminar este plato de este hueco?'`.
2. `frontend/src/components/MealCard.jsx` — two new action buttons
   (`EditIcon`/`RemoveIcon`, same local-icon convention the file already
   uses for `CheckIcon`/`ClearIcon`), wired to new `onEdit`/`onRemove` props,
   rendered unconditionally (definitive meal included — `FR-CAND-05`).
3. `frontend/src/components/DaySlot.jsx` — passes
   `onEdit={() => onEdit(day, slotState.slot, candidate)}` and
   `onRemove={() => onRemove(day, slotState.slot, candidate.id)}` through,
   same shape as `onPromote`/`onClear`.
4. `frontend/src/hooks/useRecipeAuthoring.js` — optional `initialMethod`
   (defaults to `methods[0]`, so both existing callers are unaffected).
5. `frontend/src/components/CandidateAuthoring.jsx` — optional
   `initialRecipe` prop; when set, opens on `initialMethod: 'scratch'`
   seeded with that recipe (E5).
6. `frontend/src/hooks/useWeekPlanner.js` — new `candidateUrl()` helper
   (`candidatesUrl() + '/' + candidateId`); new `editingTarget` state (a
   **separate** state from `authoringTarget`, by design — keeps the live
   assertion `useWeekPlanner.test.js:128` on `authoringTarget` untouched);
   `openCandidateEdit`/`closeCandidateEdit`/`submitCandidateEdit` (PUT, same
   marker/error shape as `submitCandidate`); `removeCandidate`
   (`confirm.requestConfirm(MESSAGES.CONFIRM_REMOVE_CANDIDATE, …)` then
   DELETE + marker, same shape as `clearDefinitive`).
7. `frontend/src/components/WeekPlannerView.jsx` — wires the six new hook
   members through to `DaySlot` and mounts a second
   `<CandidateAuthoring initialRecipe={editingTarget.recipe} .../>` while
   `editingTarget` is non-null.
8. `backend/lambda_api/src/planner_api/routing.py`'s `_edit_candidate` — a
   body carrying `source` now resolves through the existing
   `_resolve_meal_source(body, deps)` (same function `_add_candidate` already
   uses); a body without one keeps the original
   `snapshot(decode_recipe(require_field(body, "recipe")))` path — no client
   break. `docs/rest_api_contract.md`'s `PUT …/candidates/{candidateId}` row
   now states it takes the same §3.1 body as `POST`.

### Traceability

| `E<n>` (plan.md) | `FR-*` | Test |
|---|---|---|
| E5 — edit opens the flow seeded with the meal's content | FR-CAND-01, FR-CAND-02 | "exposes the week-view edit and remove copy…", "opens the authoring flow seeded with the meal's content…" |
| E6 — PUT sends the §3.1 body to the meal's own endpoint | FR-CAND-01, FR-CAND-02, FR-CAND-05 | "PUTs the edited recipe…"; backend `test_editing_a_candidate_from_a_library_recipe_copies_its_content`, `…from_scratch_uses_the_manual_body`, `…still_accepts_the_bare_recipe_body`, `…with_an_unknown_library_recipe_is_not_found` |
| E7 — remove requires explicit confirmation | FR-UX-04 | "asks for confirmation before removing a meal…" |
| E8 — confirmed removal sends DELETE | FR-CAND-01 | "DELETEs the meal and applies the response ETag marker…" |
| E9 — edit/remove success applies the marker and closes the flow | FR-RT-01 | "applies the response ETag marker and closes the form after a successful edit"; "DELETEs the meal and applies the response ETag marker…" |
| E10 — a rejected edit/remove shows `detail` verbatim | FR-UX-03 | "renders a rejected edit's detail verbatim and keeps the form open"; "renders a rejected removal's detail verbatim" |

`covers` on issue 3 is unchanged (`FR-CAND-01`/`-02` already read "add, edit,
or remove" / "adding/editing"); `FR-UX-04` is newly reachable through E7.

### Test move and red→green evidence

Staged files moved verbatim (`diff` against the staged copies: empty):
- `issues/add-dish-button-inert/tests/frontend/tests/components/WeekPlannerView.candidateEditRemove.test.jsx` → `frontend/tests/components/WeekPlannerView.candidateEditRemove.test.jsx`
- `issues/add-dish-button-inert/tests/backend/lambda_api/tests/test_candidate_edit_sources.py` → `backend/lambda_api/tests/test_candidate_edit_sources.py`

**Red**, before any code change:
- Frontend (`npx vitest run tests/components/WeekPlannerView.candidateEditRemove.test.jsx`): `1 file failed, 8 failed (8)` — matches `plan.md` exactly (7× "Unable to find an element with the text: Editar/Eliminar", 1× `expected undefined to be 'Editar'`).
- Backend (`uv run pytest lambda_api/tests/test_candidate_edit_sources.py -q`): `2 failed, 2 passed` — both `library`-arm cases `assert 400 == 200`/`assert 400 == 404`, matching `plan.md` exactly.

**Green**, after the fix: frontend `2 files passed, 13 passed (13)` (the new
8 plus the untouched add-path 5); backend `4 passed`.

Full suites: frontend `npx vitest run` — **57 files passed, 378 passed
(378)** (was 56/370 after issue 5 — +1 file/+8 tests). Backend `uv run
pytest -q -m "not aws and not docker"` — **850 passed, 8 deselected** (was
846 — +4, the new staged file). `uv run ruff format --check .` / `uv run
ruff check .` / `uv run mypy .` / `npx eslint .` / `npx prettier --check .`
all clean. `./init.sh`: fully green.

No staged test was edited, loosened, skipped or xfailed — `git diff
issues/add-dish-button-inert/tests/` is empty. No test from T1–T5 changed
(`WeekPlannerView.candidateAuthoring.test.jsx` untouched, still 5/5 green).
`tasks.md` T6–T13 all ticked. `issue_list.json`: no edit made by this
implementer.

---

## Fix round 1 — reviewer finding, E6/FR-CAND-05 coverage gap

Reviewer verdict on the scope-extension round: `CHANGES_REQUESTED`, one
finding. `plan.md` § *Fix design — edit and remove* requires Editar/Eliminar
to render for a definitive meal too (`FR-CAND-05`), but no test proved it —
mutation testing confirmed: wrapping both buttons in `{!isDefinitive && ...}`
at `MealCard.jsx:170-185` left the whole suite (60 files, 384 tests) green,
because the one staged fixture only ever set `definitiveId: null`.

Fixed by adding one test case to `frontend/tests/components/
WeekPlannerView.candidateEditRemove.test.jsx` (additive; the byte-identical
add-scope file, `WeekPlannerView.candidateAuthoring.test.jsx`, was not
touched) — `mockPolls()` gained a `week = WEEK` default parameter (backward
compatible, every existing call site unchanged) plus a new `DEFINITIVE_WEEK`
fixture (same slot, `definitiveId: 'c1'`). The new test renders with
`mockPolls(DEFINITIVE_WEEK)`, asserts both `Editar`/`Eliminar` are present,
then exercises both to completion (edit → `PUT`, remove → confirm → `DELETE`)
— the same functional depth the existing candidate-scope tests use.

**Mutant re-verification, live in `MealCard.jsx`:** reintroduced
`{!isDefinitive && (...)}` around both buttons, ran the extended file —
**1 failed, 8 passed** (only the new test failed, on `findByText(EDIT)`
timing out — the mutant hides both controls for a definitive meal). Reverted
immediately; `git diff frontend/src/components/MealCard.jsx` afterward is
character-for-character the pre-mutant state (re-read and compared, not
`git checkout` — the file also carries this round's own prior, legitimate
E5–E10 changes that a checkout would have erased).

`npx vitest run`: **60 files passed, 385 passed** (384→385, the one new
case). `npx eslint .` / `npx prettier --check .` clean. `./init.sh`: fully
green (903 backend unaffected). No staged test touched. `issue_list.json`:
no edit made by this implementer.
