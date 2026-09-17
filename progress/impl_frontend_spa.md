# Implementation report — frontend_spa

## Shared infrastructure (T1–T13) — 2026-09-13

Scope: only `specs/frontend_spa/tasks.md`'s "Shared infrastructure" section
(T1–T13, lines 8–54). No later section (Week planner, Recipe detail, Library,
Rules, Shopping list, Summary, Auth screens) touched.

### Traceability

| Task | File(s) | `R<n>` |
|---|---|---|
| T1 | `frontend/src/api/client.js` | No `R<n>` (transport plumbing) |
| T2 | `frontend/tests/api/client.test.js` | No `R<n>` |
| T3 | `frontend/src/domain/labels.js` | R15 |
| T4 | `frontend/tests/domain/labels.test.js` | R15 |
| T4a | `frontend/src/domain/wireCodes.js` | No `R<n>` (mirrors backend vocabulary) |
| T5 | `frontend/src/hooks/useBreakpoint.js` | R17 |
| T6 | `frontend/tests/hooks/useBreakpoint.test.js` | R17 |
| T7 | `frontend/src/hooks/useConfirm.js` | R18 |
| T8 | `frontend/tests/hooks/useConfirm.test.js` | R18 |
| T9 | `frontend/src/components/ConfirmDialog.jsx`, `EmptyState.jsx`, `LoadingState.jsx` | R18, R19, R20 |
| T10 | `frontend/tests/components/ConfirmDialog.test.jsx`, `EmptyState.test.jsx`, `LoadingState.test.jsx` | R15, R18, R19, R20 |
| T11 | `frontend/src/components/WeekLabel.jsx` | R16, R21 |
| T12 | `frontend/tests/components/WeekLabel.test.jsx` | R16, R21 |
| T13 | `frontend/src/messages/es-ES.js` (+6 keys: `GENERIC_ERROR`, `CONFIRM_DIALOG_CONFIRM`, `CONFIRM_DIALOG_CANCEL`, `LOADING_STATE_DEFAULT`, `WEEK_LABEL_CURRENT`, `WEEK_LABEL_NEXT`) | R15 |

`FR-*` reachability (feature `covers` array, this slice only): FR-UX-01,
FR-UX-02, FR-UX-03, FR-UX-04, FR-UX-05, FR-UX-06 all reached via R15–R21
above. The remaining `covers` ids (FR-MENU-*, FR-CAND-*, FR-LIB-*, FR-UX-07)
belong to later sections of `tasks.md`, not dispatched this run.

### Test result

`npx vitest run` — **60/60 passed, 15 files** (7 new test files added:
`tests/api/client.test.js`, `tests/domain/labels.test.js`,
`tests/hooks/useBreakpoint.test.js`, `tests/hooks/useConfirm.test.js`,
`tests/components/ConfirmDialog.test.jsx`, `EmptyState.test.jsx`,
`LoadingState.test.jsx`, `WeekLabel.test.jsx` — 8 files, the count above
folds in the pre-existing 7). `./init.sh` full run green: 795 backend
pytest, ruff/mypy/prettier/eslint/vitest all pass.

### Deviations from the design.md pseudocode (both completing under-specified stubs, not new decisions)

1. **`ApiError` gained an explicit `this.detail = detail`.** design.md
   §4.1's snippet only calls `super(detail)` (setting `Error.message`), but
   §3's Files section and §4.1's own prose both name `detail` as one of
   `ApiError`'s four fields and say handlers read `error.detail` — the
   snippet was incomplete relative to its own spec text. Added the explicit
   assignment so both `error.message` and `error.detail` carry the value.
2. **`apiFetch` wraps `fetch()` in try/catch** to produce the
   `code: "NETWORK_ERROR"` `ApiError` T2 explicitly requires — the §4.1
   snippet omitted this branch even though T2 and §9's test strategy both
   describe it.

### Bug found in existing `frontend/eslint.config.js` (fixed, not part of T1–T13's file list but required for `./init.sh` §5 to stay green)

My first attempt to turn off `react/prop-types` (no TypeScript, no
`prop-types` dependency — nothing in `design.md`/`conventions.md`
authorizes adding one) added a second `rules:` key in the same flat-config
object literal that already spread `...react.configs.flat.recommended`.
Object-literal semantics: the later `rules:` key **replaces** the spread
one entirely rather than merging — this silently dropped all 22
`react/*` recommended rules, including `react/jsx-uses-vars`, which is what
tells `no-unused-vars` that a component imported and used only inside JSX
is "used". That broke lint for `src/main.jsx` and
`tests/PlaceholderView.test.jsx` too (both pre-existing, untouched by this
feature) — confirmed via `git status` that neither file is part of this
diff. Fixed by spreading `react.configs.flat.recommended.rules` into the
`rules:` object instead of replacing it:

```js
rules: {
  ...react.configs.flat.recommended.rules,
  'react/prop-types': 'off',
},
```

`npx eslint .` (whole project) is clean after the fix.

### Notes the spec didn't fully anticipate

- `docs/rest_api_contract.md` §2 gives `monday`/`sunday` as part of
  `GET /v1/live-weeks`'s response but doesn't state their JSON type.
  `WeekLabel.jsx` assumes an ISO date string (or a `Date`, since
  `new Date(x)` is idempotent on a `Date`) and converts via `new Date(...)`
  before calling `locale.js:formatDate`, which expects a `Date` instance.
- `UNIT_LABELS`/`CATEGORY_LABELS`/`SLOT_LABELS`/`DAY_LABELS` are the only
  four maps T3 lists; `design.md` §3's file inventory also mentions a
  `ROLE_LABELS` map for the Admin/User role labels — that belongs to the
  auth-screens section (§5a), not dispatched this run, so it was not added.
- No `frontend/src/locale.js` change was needed — it already existed
  (feature 1/26 scaffold) with the exact `formatDate`/`formatNumber` shape
  `design.md` and `tasks.md` T11 call for.

## Week planner + Recipe detail (T14–T21) — 2026-09-13

Scope: `specs/frontend_spa/tasks.md`'s "Week planner" (T14–T17) and "Recipe
detail" (T18–T21) sections only (lines 61–104). Built on the T1–T13 shared
infrastructure (reviewer-approved) without redoing it. No later section
(authoring flow, Library, Rules, Shopping list, Summary, App shell, Auth)
touched.

### Traceability

| Task | File(s) | `R<n>` |
|---|---|---|
| T14 | `frontend/src/hooks/useWeekPlanner.js` | R1, R2, R3, R18 |
| T15 | `frontend/src/components/WeekSwitcher.jsx`, `WeekPlannerView.jsx`, `DaySlot.jsx`, `MealCard.jsx` | R1, R2, R3, R19, R20 |
| T16 | `frontend/tests/hooks/useWeekPlanner.test.js` | R2, R3, R4/R5 wiring, R18, R19 |
| T17 | `frontend/tests/components/WeekPlannerView.test.jsx` | R1, R3 |
| T18 | `frontend/src/hooks/useRecipeDetail.js` | R4 |
| T19 | `frontend/src/components/RecipeDetailView.jsx` | R4 |
| T20 (partial) | `MealCard`/`DaySlot`/`WeekPlannerView` wiring `openDetail` | R5 (2 of 4 call sites — see limitation below) |
| T21 (partial) | `frontend/tests/hooks/useRecipeDetail.test.js`, `tests/components/RecipeDetailView.test.jsx`, `tests/components/WeekPlannerView.test.jsx` | R4, R5 (2 of 4 call sites) |

`FR-*` reachability this slice: `FR-MENU-01` (R1), `FR-MENU-04` (R4),
`FR-MENU-05` (R5), `FR-MENU-07` (R2, R3) all reached. `FR-CAND-05`/`-08`
(promote/clear outcome), `FR-CAND-04` (author display), `FR-CAND-07`
(snapshot semantics) are consumed-not-owned per `design.md` §1.2 — this
slice only calls the already-`done` endpoints, cited not claimed.

### T20/T21 limitation — Library/Summary wiring deferred (explicit, as briefed)

`design.md`'s Screens table only lists 2 of tasks.md's 4 named `openDetail`
call sites as this slice's own: a day's candidates and a slot's definitive
meal, both served by the *same* `MealCard.jsx` (an `isDefinitive` prop picks
the "clear" vs. "promote" control, not a separate component) — both reach
`WeekPlannerView`'s single `openDetail` prop, which is
`useWeekPlanner.openDetail` unmodified end to end
(`WeekPlannerView.test.jsx`'s "clicking a meal card…" and "…definitive meal
card…" cases assert this). `SummaryView` and `LibraryView` do not exist yet
— they are separate, later `tasks.md` sections (T29/T39, not dispatched this
run) — so their two call sites cannot be wired. Each will call the same
`useRecipeDetail`/`normalizeRecipeDetail` pair this slice built when it is
their turn; nothing here needs to change for that. `tasks.md` T20/T21 are
left unchecked with a "Partial" note (mirrors T13's existing pattern),
not marked done.

### Design decisions made to complete under-specified parts of `design.md`

1. **`MealCard` is reused for both roles** (a regular candidate and the
   slot's definitive meal) rather than building a second component —
   `design.md` §3's file list only names one `MealCard.jsx`, and R5 groups
   "a day's candidates" and "a slot's definitive meal" as two *places*, not
   two components.
2. **`apiFetch` gained an additive `onHeaders` option** (`client.js`,
   `{ onHeaders }`, called with the raw `Response.headers` on both a 200
   and a 204, before the function returns) — needed to read the mutation's
   `ETag` for `usePolling`'s `applyMutationMarker` per `design.md` §4.2,
   which the T1-built `apiFetch` did not yet expose. Backward compatible:
   no existing caller passes it, `client.test.js`'s existing assertions are
   untouched, one new case added. `useWeekPlanner`'s `promoteDefinitive`/
   `clearDefinitive` read the marker this way and call
   `weekPoll.applyMutationMarker(marker)` (design.md §4.2's hand-off).
3. **`WeekPlannerView` is a pure, props-driven component**, not a component
   that calls `useWeekPlanner()` itself — `conventions.md`'s hook/component
   split and T17's own test ("renders … for a given week payload") both
   require passing a week payload in as a prop, testable without the App
   shell. The (later, not-yet-built) App shell section is expected to
   mount `<WeekPlannerView {...useWeekPlanner()} />`; nothing here
   presumes how.
4. **`useRecipeDetail`'s effect keys on `source`'s primitive fields, never
   `source` itself.** A caller may pass a fresh object literal every render
   (`useWeekPlanner`'s `{ recipe: normalizeRecipeDetail(candidate) }`, and
   every test here) — depending on the wrapper's identity re-ran the effect
   on every render and looped (`setState` → re-render → new literal →
   effect again), reproduced as a real `JS heap out of memory` crash before
   the fix. Fixed by extracting `weekId`/`day`/`slot`/`candidateId`/
   `recipeId`/`heldRecipe` and depending on those.
5. **`isLoading` is a derived comparison (`fetched.key !== requestKey`),
   not its own state field set synchronously in the effect.** The first
   version called `setState({ isLoading: true })` synchronously at the top
   of the effect body, which `eslint-plugin-react-hooks`'s
   `set-state-in-effect` rule (already enabled project-wide) flags as a
   cascading-render smell — fixed by keying the fetched result to the
   request that produced it and deriving `isLoading` from whether the
   current request's key matches.
6. **`openCandidateAuthoring(day, slot)` records `{ weekId, day, slot }`**
   (not just `day`/`slot`) as `authoringTarget` — read `design.md` §5.1 per
   the dispatch brief; the future `RecipeAuthoringForm`'s `onSubmit` needs
   `weekId` to build the `POST …/slots/{slot}/candidates` URL, and
   `useWeekPlanner` already has it. Purely additive to the T14 task text
   ("exposed/callable correctly").

### Test result

`npx vitest run` — **84/84 passed, 19 files** (4 new: `useWeekPlanner.test.js`,
`useRecipeDetail.test.js`, `WeekPlannerView.test.jsx`,
`RecipeDetailView.test.jsx`; `client.test.js` extended with one case for the
new `onHeaders` option). `./init.sh` full run green: **795 backend pytest**
(unchanged — no `backend/` file touched), ruff/mypy/prettier/eslint/vitest
all pass.

### Notes the spec didn't fully anticipate

- `Candidate.author` (`backend/core/.../domain/candidate.py`) is a plain
  `str`, not a `{userId, displayName}` object — confirmed against the
  domain type and `encode_candidate`/`_encode_library_entry`
  (`serialization.py`/`routing.py`), not assumed from the wire-shape
  example in `rest_api_contract.md` §3.1 (which only shows an `AccountRecord`
  encoding elsewhere in that same doc). `MealCard`/`normalizeRecipeDetail`
  render/carry it as a string.
- The week read (`GET /v1/weeks/{weekId}`, `routing.py::_get_week`) already
  returns **every** candidate's full recipe snapshot per slot, not a
  name/category summary — so `openDetail` from the week view never needs a
  network round-trip; it is always the "already-held recipe" branch of
  `useRecipeDetail`. The fetch-by-id branch (T18's other half) is exercised
  today only by its own unit tests, pending Library/Summary's later wiring.
- `@testing-library/react`'s automatic `afterEach(cleanup)` does not
  register in this project (`vite.config.js` sets `globals: false`, and RTL's
  auto-cleanup hooks a *global* `afterEach`) — the two new component test
  files call `cleanup()` explicitly. Pre-existing component test files
  (`ConfirmDialog.test.jsx` etc.) never hit this because none of them
  render overlapping text across multiple `it()` blocks; flagging here in
  case a later section's test file needs the same explicit `afterEach(cleanup)`.

## Fix round 1 (reviewer findings on T14–T21) — 2026-09-13

Four findings, all in `useWeekPlanner.js`/`useRecipeDetail.js` plus their
test files. No other section touched. `tasks.md` T14–T21 notes unchanged
(fix round, not new task completion).

1. **`applyMutationMarker` mutant.** Added a marker-propagation test each
   for `promoteDefinitive`/`clearDefinitive`: `apiFetch` invokes its
   `onHeaders` callback with a real `Headers({ ETag: '"20"' })`, asserts
   `weekPoll.applyMutationMarker` was called with the parsed `20`. Mutant
   (deleting each `applyMutationMarker(marker)` call) **re-applied by hand,
   both failed, both restored and pass** — confirmed kill, not just
   suite-green.
2. **`useRecipeDetail` dep-array mutant.** Added
   `expect(apiFetch).toHaveBeenCalledTimes(1)` to the candidate-by-id test.
   Mutant (dep array reverted to `[source]`) **re-applied by hand — failed
   with `expected … 1 times, but got 5061 times`** (the runaway loop the
   review's probe measured), fix restored, passes.
3. **Missing `ApiError` catch (design.md §4.1) at all 4 call sites.** Each
   hook now catches a rejection, stores `error.detail` verbatim (never
   composed), and clears it on the next success. **Chosen shape:** a plain
   `error: string | null` field on the hook's return value — no existing
   error-state convention in the codebase to match (`usePolling.js` only
   exposes `connectionLost`, not an error string), so this is the new
   baseline later sections (Library/Rules/Shopping list/Summary) should
   reuse. `useWeekPlanner` also exposes `detailError: detail.error`
   (the composed `useRecipeDetail` instance's own error, distinct from
   the week/mutation `error`). 4 new test cases (one per call site) reject
   `apiFetch` with an `ApiError` and assert the field. **Not done this
   round:** wiring `error`/`detailError` into `WeekPlannerView.jsx`/
   `RecipeDetailView.jsx`'s markup — the finding's own call-site list and
   the task's test-coverage checklist are both hook-level only; rendering
   it needs a `RecipeDetailView.jsx` restructure (recipe-less error render)
   that reads as a new decision, not this round's 4 named fixes. Flagged
   for the next section/fix round that touches these two view files.
   **Closed 2026-09-13:** `WeekPlannerView.jsx` renders `error` as a plain
   `<p>` (same style as `EmptyState`/`LoadingState`'s text pattern) and now
   mounts `RecipeDetailView` on `detail || detailError`, not `detail` alone.
   `RecipeDetailView.jsx` gains an `error` prop: recipe-less + error renders
   the close button plus the error text instead of `null`. No new color
   token — reuses `tokens.color.ink`/`ink2`. 3 new tests: 1 in
   `RecipeDetailView.test.jsx`, 2 in `WeekPlannerView.test.jsx` (own-error,
   detail-fetch-error-without-recipe). `npx vitest run` 93 passed, `npx
   eslint .` clean.
4. **Comment length.** Both flagged comments in `useRecipeDetail.js` (the
   file banner and the effect-deps comment) cut to 3 lines, pointing at
   this file's own "Design decisions" section above instead of reproducing
   the reasoning.

### Test result

`npx vitest run` — **90/90 passed, 19 files** (84 → 90: 2 marker-mutant
tests, 3 error tests in `useWeekPlanner.test.js`, 1 call-count regression +
1 error test in `useRecipeDetail.test.js`). `./init.sh` full run green:
**795 backend pytest** (unchanged), ruff/mypy/prettier/eslint/vitest all
pass.

## The shared authoring flow (T22–T24) — 2026-09-13

Scope: `specs/frontend_spa/tasks.md`'s "The shared authoring flow" section
(T22–T24, lines 117–137) only. Built on T1–T21 (reviewer-approved) without
redoing it. No later section (Library recipe picker, Rules, Shopping list,
Summary, App shell, Auth) touched.

### Traceability

| Task | File(s) | `R<n>` |
|---|---|---|
| T22 | `frontend/src/hooks/useRecipeAuthoring.js` | R6, R7, R8 |
| T23 (partial) | `frontend/src/components/RecipeAuthoringForm.jsx` | R6, R7, R8, R20 |
| T24 | `frontend/tests/hooks/useRecipeAuthoring.test.js` | R6, R7, R8 |
| (component test, no task number) | `frontend/tests/components/RecipeAuthoringForm.test.jsx` | R6, R7, R8, R20 |

`FR-*` reachability this slice: `FR-CAND-02` (R6), `FR-CAND-03` (R7, R8) both
reached. `AI_GENERATION_UNAVAILABLE` es-ES key added to `messages/es-ES.js`
per the dispatch brief, plus the rest of this slice's own field/tab labels.

### T23 — library-tab embed deferred (explicit, as briefed)

`LibraryRecipePicker` does not exist yet — it is built in T25/T26, a later
section (`tasks.md` lines 141–147). `RecipeAuthoringForm`'s `library` tab (for
`mode: "candidate"` only, per R8) renders a selectable placeholder
(`MESSAGES.RECIPE_AUTHORING_LIBRARY_PENDING`, `"Selector de recetas de la
biblioteca pendiente de implementar."`) instead of the real picker. `tasks.md`
T23 is left unchecked with a "Partial" note, same convention as T13/T20/T21 —
stays open until T25/T26 land and the embed replaces the placeholder.

### Design decisions made to complete under-specified parts of `design.md`

1. **`useRecipeAuthoring`'s `onSubmit` receives the assembled body, not a
   completion callback.** §5.1's pseudocode signature is exactly `{ mode,
   onSubmit }` — no endpoint/URL parameter. Candidate submissions need a
   day/slot/weekId-specific URL (`POST …/slots/{slot}/candidates`); library
   submissions need a different, fixed one (`POST /v1/library/recipes`,
   `rest_api_contract.md` §3.1). Since the hook has no way to know either
   target and the pseudocode adds none, `submit()` builds the `{source:
   "manual"|"library", ...}` body and hands it to the caller's `onSubmit` —
   the caller (a later section: `useWeekPlanner`/`useLibrary`, neither
   dispatched this run) owns the actual `apiFetch` call and knows which URL
   to use. This matches `useConfirm`'s own precedent (hook exposes intent,
   caller wires the actual mutation).
2. **`canSubmit` for `scratch` is always `true` (no client validation)** —
   the dispatch brief's own framing ("validation-free per `FR-LIB-03`/G-85,
   freeform text inputs for servings/estimatedTime") is read as covering the
   whole manual form, not just those two fields; the server is the single
   source of truth for what a valid recipe is. `canSubmit` for `library` is
   gated on a selected `libraryRecipeId` (structural completeness — nothing
   to submit otherwise — not business validation); `ai` is always `false`
   per design.md §1.3.
3. **Ingredient `quantity` is cast with `Number(...)` only at submit-body
   assembly**, not stored as a number in form state. `rest_api_contract.md`
   §3.1's example shows `quantity` as a JSON number (unlike `servings`/
   `estimatedTime`, which design.md §5.1 explicitly calls freeform text) —
   this is wire-type compliance, a one-line cast, not a computed value.
4. **The `ai` tab's spec-input fields render both `ingredients` and `tools`
   free-text areas** (design.md §1.3's first variant, "ingredients + tools");
   the second variant ("a reference recipe + notes") needs
   `LibraryRecipePicker` for the reference-recipe field, per T27's own
   listing of that field as a `LibraryRecipePicker` reuse site — deferred
   alongside the `library` tab, same reason.

### Test result

`npx vitest run` — **107/107 passed, 21 files** (90 → 107: 17 new — 5 in
`useRecipeAuthoring.test.js`, 9 in `RecipeAuthoringForm.test.jsx`, plus the
suite recount includes the new files themselves). `./init.sh` full run
green: **795 backend pytest** (unchanged), ruff/mypy/prettier/eslint/vitest
all pass. `npx prettier --write` also reformatted `WeekPlannerView.jsx`
(untouched by this slice's logic — a pre-existing, whitespace-only drift
from the Week planner slice; diff confirmed single-line-wrap-only before
applying) since `./init.sh` §5 checks `prettier --check .` project-wide.

## Fix round 1 (reviewer findings on T22–T24) — 2026-09-13

Three findings on `RecipeAuthoringForm.jsx`/`RecipeAuthoringForm.test.jsx`:

1. **AI submit `disabled` untested** — split the assertion out of the
   existing "does not render..." test into its own
   `'the ai tab submit control is disabled (design.md section 1.3)'` test.
   Confirmed KILL: removing `disabled` from the AI-tab submit button
   (`RecipeAuthoringForm.jsx` line ~171) fails the new test; restoring it
   passes.
2. **Tab-order test didn't assert order** — `'renders a tab per method, in
   order'` now reads the first three buttons via `getAllByRole('button')`
   and asserts their text sequence, not just presence. Confirmed KILL:
   reversing `methods.map` to `[...methods].reverse().map` fails the test;
   restoring it passes.
3. **Comment-length ceiling** — trimmed the 7/8-line banners in
   `useRecipeAuthoring.js` and `RecipeAuthoringForm.jsx` to 3 lines each,
   pointing at this file's "The shared authoring flow" section instead of
   reproducing the reasoning inline.

Also corrected `progress/current.md`'s new-keys count for this slice: 23, not
24 (22 `RECIPE_AUTHORING_*` + `AI_GENERATION_UNAVAILABLE`).

### Test result

`npx vitest run` — **108/108 passed, 21 files** (107 → 108: one test split
into two). `npx eslint .` clean. `./init.sh` fully green (795 backend
pytest, ruff/mypy/prettier/eslint/vitest all pass).

## Library recipe picker + Library view (T25–T31) — 2026-09-13

Scope: `specs/frontend_spa/tasks.md`'s "Library recipe picker + Library
view" section (T25–T31, lines 145–172) only. Built on T1–T24
(reviewer-approved) without redoing it. No later section (Rules, Shopping
list, Summary, App shell, Auth) touched.

### Traceability

| Task | File(s) | `R<n>` |
|---|---|---|
| T25 | `frontend/src/hooks/useLibraryPicker.js` | R11, R13, R14 |
| T26 | `frontend/src/components/LibraryRecipePicker.jsx` | R11, R13 |
| T27 (partial) | `useRecipeAuthoring.js` (2 `useLibraryPicker` instances), `RecipeAuthoringForm.jsx` (embeds in `library`/`ai` tabs) | R12 (2 of 3 call sites) |
| T28 | `frontend/src/hooks/useLibrary.js` | R9, R10, R18 |
| T29 | `frontend/src/components/LibraryView.jsx` | R9, R10, R19 |
| T30 | `frontend/tests/hooks/useLibraryPicker.test.js`, `useLibrary.test.js` | R9, R11, R13, R14, R18 |
| T31 | `frontend/tests/components/LibraryRecipePicker.test.jsx` | R11, R12 (2 of 3 sites), R13 |
| T20/T21 (partial, extended) | `LibraryView.jsx`'s rows now reach `useLibrary.openDetail` | R5 (3 of 4 call sites — see below) |

`FR-*` reachability this slice: `FR-LIB-01` (R9), `FR-LIB-02` (R10),
`FR-LIB-04` (R11, R12, R13, R14) all reached.

### T27 — 2 of 3 `LibraryRecipePicker` call sites wired (explicit, as briefed)

`RulesView` does not exist yet (T32/T33, a later section) so its pin-recipe
field cannot be wired. The 2 sites this slice wires both live inside
`RecipeAuthoringForm`/`useRecipeAuthoring`:

1. **The `library` method tab** — the placeholder from T23
   (`MESSAGES.RECIPE_AUTHORING_LIBRARY_PENDING`) is replaced by a real
   `<LibraryRecipePicker>` embed; that message key is removed (dead after
   the swap, confirmed no other reference).
2. **The `ai` tab's reference-recipe field** — design.md §1.3 describes the
   stub's spec-input shape as "ingredients + tools, or a reference recipe +
   notes"; only the first half existed after T22/T23. Added
   `referenceRecipeId`/`selectReferenceRecipe` state and an `aiSpec.notes`
   field, both wired to a second `<LibraryRecipePicker>` embed. Still a
   stub — `canSubmit` stays `false` for `ai` regardless (design.md §1.3),
   so this field is spec-input only, never submitted.

`tasks.md` T27/T31 are left unchecked with a "Partial" note (T13/T20/T21/T23
convention) — T27 stays open until T33/T34 (Rules view) wire the third site.

### T20/T21 — extended to 3 of 4 call sites

Building `LibraryView.jsx` naturally lands its named `openDetail` call
site: `useLibrary` composes `useRecipeDetail` (T18) the same way
`useWeekPlanner` already does, and `LibraryView`'s recipe rows call
`useLibrary.openDetail(recipe)`. `tasks.md` T20/T21 notes updated in place
(week planner slice's "2 of 4" → this slice's "3 of 4"); `SummaryView` is
the one remaining site, left for its own later section.

### Design decisions made to complete under-specified parts of `design.md`

1. **`useRecipeAuthoring` composes `useLibraryPicker` internally**, not the
   component. design.md §5's Screens table maps `RecipeAuthoringForm` to
   exactly one hook (`useRecipeAuthoring`, "Polls: none"); the same
   composition precedent `useWeekPlanner`→`useRecipeDetail` already set
   (§4.2's shared-hook pattern) applies here — the orchestrating hook owns
   nested shared-hook instances and threads their props down, keeping
   `RecipeAuthoringForm`/`LibraryRecipePicker` pure functions of props.
   Two separate `useLibraryPicker()` instances (`libraryPicker`,
   `referencePicker`) rather than one shared instance, since a user may
   filter each independently while switching tabs.
2. **`useRecipeAuthoring.test.js` now mocks `usePolling.js`.** Composing
   `useLibraryPicker` means every `renderHook` in that file would otherwise
   issue a real, unmocked `fetch('/v1/library/recipes')` in jsdom — slow,
   non-deterministic, and outside this hook's own concern. Mocked the same
   way `useWeekPlanner.test.js` already mocks it project-wide.
3. **The library delete pin-cascade (`rest_api_contract.md` §3.4,
   `409 PIN_RULES_AFFECTED` → `?confirmCascade=true` retry) is not
   special-cased.** Not named in `requirements.md`/`design.md`/`tasks.md`
   anywhere for this feature; `useLibrary.remove` sends a plain `DELETE`
   gated by `useConfirm` (R18) and surfaces any rejection — including this
   one — as `error.detail` verbatim (R15), same as every other mutation.
   Adding the two-step retry flow would be a new UI decision this spec
   doesn't authorize.
4. **`useLibrary`'s edit form does not pre-fill from the existing recipe.**
   `openEdit(recipe)` sets `editingId` so `submit` targets `PUT
   /v1/library/recipes/{id}`, but `useRecipeAuthoring`'s manual-form state
   always starts empty (§5.1's pseudocode takes no seed-value parameter).
   Re-typing the full recipe to edit it is a known limitation, not a
   silent gap — flagged here for a future round rather than inventing a
   seeding API `design.md` doesn't specify.

### Test result

`npx vitest run` — **135/135 passed, 27 files** (108 → 135: 27 new —
`useLibraryPicker.test.js` (6), `useLibrary.test.js` (11),
`LibraryRecipePicker.test.jsx` (8), plus 2 new/updated cases in
`useRecipeAuthoring.test.js` and `RecipeAuthoringForm.test.jsx` each).
`npx eslint .` clean after adding `URLSearchParams: 'readonly'` to
`frontend/eslint.config.js`'s globals (same list as `Headers`/`fetch` —
it was missing, not previously needed by any file). `./init.sh` fully
green: **795 backend pytest** (unchanged, no `backend/` file touched),
ruff/mypy/prettier/eslint/vitest all pass.

## Library slice — Fix round 1 (7 reviewer findings) — 2026-09-13

Scope: the 7 findings raised on T25–T31 above. No other `frontend_spa`
section touched.

| Finding | Fix | File(s) |
|---|---|---|
| F1 (blocking, real bug) | `useLibraryPicker` polls the fixed unfiltered `GET /v1/library/recipes` (`usePolling` never sees a filtered URL, so its engine never tears down on a keystroke); `name`/`category` filter the already-polled list client-side. | `useLibraryPicker.js` |
| F2 (blocking) | `usePolling` gained an `enabled` option gating `start()`/`dispose()` only (the engine itself is always created, cheap). `useRecipeAuthoring` passes `enabled: method === 'library'` / `'ai'` to its two `useLibraryPicker` instances — at most one poll live at a time, and the `library`-method picker never polls in `mode: "library"` (no such method exists, R8). | `usePolling.js`, `useRecipeAuthoring.js` |
| F3 (blocking, surviving mutant) | Extended the `ai`-never-submits test to select a reference recipe + set `aiSpec.notes` first. | `useRecipeAuthoring.test.js` |
| F4 (blocking, real bug — data loss) | `useRecipeAuthoring` takes an `initialRecipe` param; `recipeToForm` (inverse of `buildManualRecipe`) seeds `form` from it, re-seeding via a render-time comparison (not an effect — same technique as `useRecipeDetail`'s request-keyed `isLoading`) whenever the edited recipe's identity changes. `useLibrary` now holds the whole `editingRecipe`, not just its id, and passes it through. | `useRecipeAuthoring.js`, `useLibrary.js` |
| F5 (blocking) | Added a submit button to the `library` tab (`LibraryMethodFields`), wired to the same `submit`/`canSubmit` props `scratch`'s button already uses. | `RecipeAuthoringForm.jsx` |
| F6 (minor) | Extracted the duplicated name/category filter markup into `LibraryFilters.jsx`; both `LibraryRecipePicker` and `LibraryView` render it instead of a hand copy. | `LibraryFilters.jsx` (new), `LibraryRecipePicker.jsx`, `LibraryView.jsx` |
| F7 (minor) | `progress/current.md`'s "17 new `es-ES.js` keys" corrected to the real 14 (12 library-slice keys + 2 authoring-flow keys added alongside the `ai` reference-recipe field; `AI_GENERATION_UNAVAILABLE` predates this slice). | `progress/current.md` |

Also corrected `specs/frontend_spa/tasks.md` T25's wording (F1 — no longer
describes a filtered-URL poll) and `design.md` line 293's Screens-table row
to match. T23/T27/T28/T29 re-checked against the new code: all remain
honestly ticked/partial — none of F1–F6 changed what those tasks claim to
cover, only how it's implemented underneath.

### F2 design note

The brief's suggested seam was moving `useLibraryPicker()` calls into
`RecipeAuthoringForm`'s per-tab sub-components. Used an `enabled` flag on
`usePolling`/`useLibraryPicker` instead — same net effect (never more than
one live poll, the dead one in `mode: "library"` never starts) without
moving hook ownership out of `useRecipeAuthoring` or touching the four
existing prop-driven component tests. `useRecipeAuthoring` still returns
`libraryPicker`/`referencePicker` unchanged in shape.

### New test files

`LibraryFilters.test.jsx`, `LibraryView.test.jsx` (neither existed before -
`LibraryView.jsx` had no dedicated test file; `LibraryView.test.jsx` also
carries the F1 focus-loss regression test, since that's the actual
`isLoading`-gated call site the bug manifested at).

### F1 verification (real regression, not just a unit assertion)

`LibraryView.test.jsx`'s new test mounts `LibraryView` off a real
`useLibrary()`/`useLibraryPicker()`/`usePolling()` chain (only `fetch`
mocked) and types 8 characters into the name filter one at a time,
asserting after every keystroke that `getByLabelText` still resolves to
the *same* input node. Confirmed load-bearing by hand: reverting
`useLibraryPicker.js` to the old filtered-URL poll made this exact test
fail (`Unable to find a label with the text of: Buscar por nombre` — the
view had dropped back to `LoadingState`, unmounting the input), then
restored.

### F3 mutation-kill confirmation

Hand-applied the named mutant (`useRecipeAuthoring.js`'s `ai` branch of
`canSubmit`: `return false` → `return referenceRecipeId != null`) —
`useRecipeAuthoring.test.js`'s extended test failed
(`expected true to be false`), confirming it now kills the mutant.
Reverted; suite green again.

### Test result

`npx vitest run` — **149/149 passed, 26 files** (135 → 149: 2 new files
— `LibraryFilters.test.jsx` (3), `LibraryView.test.jsx` (3) — plus new/
extended cases in `useLibraryPicker.test.js`, `useLibrary.test.js`,
`useRecipeAuthoring.test.js`, `RecipeAuthoringForm.test.jsx`).
`npx eslint .` clean. `./init.sh` fully green — **795 backend pytest**
(unchanged), ruff/mypy/prettier/eslint/vitest all pass.

## Library slice — Fix round 2 (8 reviewer findings) — 2026-09-13

Scope: the 8 findings raised on fix round 1 above. Finding 2 is a real,
pre-existing bug in `pollingEngine.js` (feature 26, `done`) — feature 20's
`enabled` toggle just made it reachable through normal user action
(switching authoring tabs mid-fetch); fixed in place, same convention as
the eslint.config.js fixes earlier this feature.

| Finding | Fix | File(s) |
|---|---|---|
| F1 (blocking, surviving mutant) | `gates each picker...` test now asserts the ORDERED `[libraryCall, referenceCall]` pair (`[true, false]` then `[false, true]`), not a sorted, identity-blind one. | `useRecipeAuthoring.test.js` |
| F2 (blocking, real pre-existing bug) | `createPollingEngine` gained a `disposed` flag, set in `dispose()`; `scheduleNext()` is a no-op once set, so an in-flight request's `finally` block can no longer re-arm a disposed engine. | `pollingEngine.js` |
| F3 (blocking, test gap) | 3 new `usePolling` tests: `enabled: false` never calls `start`; `false -> true` calls `start` once; `true -> false` calls `dispose` once. | `usePolling.test.js` |
| F4 (mechanical) | T30's wording corrected to match T25's (client-side filter over the unfiltered poll, not a query-string update). | `specs/frontend_spa/tasks.md` |
| F5 (mechanical) | §5.1 pseudocode now shows the real `{ mode, onSubmit, initialRecipe }` signature + the re-seed-on-identity-change note. | `specs/frontend_spa/design.md` |
| F6 (mechanical, 3-line ceiling) | Trimmed 3 over-length comments, each now points at this file's "Library slice — Fix round 1" instead of reproducing it. | `useLibraryPicker.js`, `useRecipeAuthoring.js`, `usePolling.js` |
| F7 (mechanical) | T31 un-ticked, "Partial (2 of 3 sites)" note added — same convention as T13/T20/T21/T27. | `specs/frontend_spa/tasks.md` |
| F8 (nit) | Removed the now-unused `URLSearchParams` eslint global (grep-verified no reference remains in `frontend/src` or `frontend/tests`). | `eslint.config.js` |

Also added a short pointer note in `specs/realtime_channel_transport/design.md`
next to `createPollingEngine`'s pseudocode documenting the `disposed` guard —
feature 26's own status/spec are otherwise untouched (owner's call whether
to reopen it).

### F1 mutation-kill confirmation

Hand-swapped the two `enabled:` expressions in `useRecipeAuthoring.js`
(library <-> ai) — the corrected test failed (`expected [false, true] to
deeply equal [true, false]`). Reverted; suite green again.

### F2 regression test verification

Added a test to `pollingEngine.test.js`: `start()`, `dispose()` while the
fetch promise is still pending, then resolve it. Reverting the `disposed`
guard (dropping the `if (disposed) return;` line) made the test fail
(`expected "vi.fn()" to be called 1 times, but got 2 times` — the disposed
engine re-armed and fired a second fetch after a 4x interval advance).
Restored; suite green again.

### Test result

`npx vitest run` — **153/153 passed, 26 files** (149 → 153: 1 new case in
`pollingEngine.test.js`, 3 new cases in `usePolling.test.js`). `npx eslint .`
clean. `./init.sh` fully green — **795 backend pytest** (unchanged),
ruff/mypy/prettier/eslint/vitest all pass.

## Library slice — Fix round 3 (regression, silent polling death) — 2026-09-13

**Root cause confirmed.** `usePolling.js` memoized its engine on
`[url, config, createEngine]` - `enabled` was never a dependency. Fix round
2's `disposed` flag (`pollingEngine.js`) is permanent by design (`dispose()`
sets it, `scheduleNext()` no-ops forever after). Because the memo key never
changed across an `enabled: true -> false -> true` cycle, `usePolling`
disposed then restarted the SAME poisoned engine: `start()` still fires one
immediate `poll()` (it has no `disposed` guard), but the `finally` block's
`scheduleNext()` call silently no-ops, so the engine polls exactly once more
and then dies - reachable in production by switching the `useRecipeAuthoring`
picker tab `library -> ai -> library`.

**Fix.** `usePolling` now tracks `generation` state that bumps only on a
`false -> true` `enabled` transition (React's documented "adjust state
during render" pattern via `useState`, not `useRef` - this project's eslint
config's `react-hooks/refs` rule forbids ref reads/writes during render).
`generation` is in the `useMemo` dependency array as a deliberate
cache-busting key the factory doesn't read, so re-enabling always builds a
brand-new, non-disposed engine instead of reusing the dead one.
`eslint-disable-next-line react-hooks/exhaustive-deps` on that one line,
justified inline - the alternative (building the engine inside the effect
instead of `useMemo`, discussed and dropped) caused the existing "config"
argument passed as a fresh object literal per test render to retrigger the
effect on every render, an unrelated instability that isn't present in real
call sites (callers already pass a stable `config`).

**Non-blocking note also fixed.** `pollNow()` (used by both
`applyMutationMarker` and the visibility-regain path) had no `disposed`
guard - a stale `applyMutationMarker` closure over an already-disposed
engine could still fire a fetch. Added the same one-line guard
`scheduleNext()` already had.

**Test gap closed.** Added
`'resumes real polling after an enabled true -> false -> true cycle'` to
`usePolling.test.js`, against the REAL `createPollingEngine` (not the fake
used by the file's other tests) - the bug only reproduces through the real
`disposed`/`scheduleNext` interaction. Confirmed by hand: reverting the
`generation`-based memo key back to `[url, config, createEngine]` makes the
test fail `expected 3, got 2` (one immediate poll from the doomed engine's
`start()`, then silence) - exactly the bug's signature. Also added
`'applyMutationMarker on a disposed engine does not fire a stray fetch'` to
`pollingEngine.test.js`; reverting the `pollNow()` guard makes it fail
`expected 1, got 2`.

### Test result

`npx vitest run` — **155/155 passed, 26 files** (153 → 155: 1 new case in
`pollingEngine.test.js`, 1 new case in `usePolling.test.js`). `npx eslint .`
clean. `./init.sh` fully green - **795 backend pytest** (unchanged),
ruff/mypy/prettier/eslint/vitest all pass. Re-ran `useWeekPlanner.test.js`,
`useLibraryPicker.test.js`, `useLibrary.test.js`, `useRecipeAuthoring.test.js`
individually alongside the two changed files - 69/69 pass, no regressions.

**Fix round 4 (comment trims only).** Trimmed 3 over-length comments (`usePolling.js`,
`usePolling.test.js` x2) to ≤3 lines, pointing at this section instead of reproducing it — no logic change, 155/155, `npx eslint .` clean.

## Rules view (T32–T34) — 2026-09-14

Scope: only `specs/frontend_spa/tasks.md`'s "Rules view" section (T32–T34,
lines 188–205). No later section (Shopping list, Summary, App shell, Auth)
touched. Built on the reviewer-approved T1–T31 — closes T31's deferred 3rd
`LibraryRecipePicker` call site (the pin-recipe field).

### Traceability

| Task | File(s) | `R<n>` |
|---|---|---|
| T32 | `frontend/src/hooks/useRules.js` | R18; consumes `FR-RULE-01…07` (features 6/27, no `R<n>`) |
| T33 | `frontend/src/components/RulesView.jsx` | R12, R19 |
| T34 | `frontend/tests/hooks/useRules.test.js`, `frontend/tests/components/RulesView.test.jsx`, +1 test in `LibraryRecipePicker.test.jsx` (3rd site) | R12, R15, R18, R19 |
| T31 (completed) | `LibraryRecipePicker.test.jsx` un-ticked "Partial" → done | R12 |

`GET /v1/rules` polled unfiltered — no query params, so the library slice's
filtered-URL bug (fix round 1, F1) does not apply here by construction.
`error`/`connectionLost` follow the established `error: string | null` shape.

### Design decisions filling spec gaps

1. **No `recipeName` on the wire.** `rest_api_contract.md`/`data_model.md`
   describe a pin rule carrying a read-time-resolved `recipeName`, but the
   real, `done` implementation (`serialization.py::encode_rule`,
   `rule_editing.read_rules`) never adds it — `_list_rules` calls the same
   `encode_rule` a `PUT` echoes, which for `PinRule` returns only
   `{type, day, slot, recipeId}`. Built against the real wire shape, not the
   aspirational doc: `RulesView` resolves a pin's display name by
   cross-referencing `useLibraryPicker`'s already-polled recipe list
   (`recipeId -> name`), a pure display lookup, not business logic — no
   second network call, no duplicated satisfiability/aggregation logic.
2. **No separate "Editar" flow with prefill.** `PUT /v1/rules/{ruleId}` is a
   blind upsert keyed by the rule's own natural id (`rest_api_contract.md`
   names it "Añadir o editar regla" — one operation). A row-level "Editar"
   button that pre-fills a rule's *identity* fields (category / day+slot)
   editable would let a user silently orphan the original rule by changing
   the identity and re-submitting to a *different* `ruleId` — the same bug
   class as the library slice's F4 (edit not pre-filling), inverted: here
   the risk is an edit path that pre-fills identity fields as *mutable*.
   Sidestepped by construction: one add/edit form per rule type, always
   selecting identity fresh; the existing-rule list is read-only display +
   remove only. Documented so a future session doesn't "fix" this by adding
   row-level edit with identity pre-fill.
3. **`RULE_COUNT_OPTIONS` = 1..14, not a free `<input type="number">`.** T33
   requires "dropdown-only… never free text" for every rule field including
   count, but the domain places no upper bound on `count` beyond physical
   slot capacity. 14 = `Object.keys(DAY_LABELS).length *
   Object.keys(SLOT_LABELS).length` (7 days × 2 slots) — a structural bound
   already rendered elsewhere in this SPA (the week grid), not a
   satisfiability decision (that stays server-side, `FR-RULE-07`). Starts at
   1, not 0 — a 0-count rule is a no-op better expressed via the existing
   remove control.
4. **Disabled-day rules offer no "edit" control**, only add/remove — a
   `DisabledDay` carries no field beyond its own identity (`day`), so there
   is nothing to mutate once created.

### Test result

`npx vitest run` — **172/172 passed, 28 files** (155 → 172: 7 new cases in
`useRules.test.js`, 9 new cases in `RulesView.test.jsx`, 1 new case in
`LibraryRecipePicker.test.jsx` closing T31's 3rd site). `npx eslint .`
clean (fixed a `react-hooks/exhaustive-deps` warning on `useRules.js`'s
grouping `useMemo`s by memoizing `rules` itself off `poll.data`).
`npx prettier --check .` clean after one `--write` pass on the 4 new files.
`./init.sh` fully green — **795 backend pytest** (unchanged),
ruff/mypy/prettier/eslint/vitest all pass.

## Rules view — Fix round 1 (6 reviewer findings) — 2026-09-14

Scope: the 6 findings on T32–T34 above. No other `frontend_spa` section
touched.

| Finding | Fix | File(s) |
|---|---|---|
| F1 (blocking, surviving mutant) | Replaced the overlapping-fixture assertion with the composed row label itself (`'lunes · Comida · Tortilla'`); the fixture no longer seeds `picker.recipes` (only `picker.allRecipes`), so the label can't pass by accidental overlap with the picker's own list. | `RulesView.test.jsx` |
| F2 (blocking, surviving mutant) | New test: exactly 1 `textbox` role on the page (the picker's own `LibraryFilters` search box, asserted by accessible name) and 6 `combobox` roles — every rule-defining field is a `<select>`. | `RulesView.test.jsx` |
| F3 (mechanical, comment ceiling) | Trimmed 3 over-length banners (`useRules.js`, `RulesView.jsx`, `LibraryRecipePicker.test.jsx`) to ≤3 lines, pointing at this section instead of reproducing the reasoning. | `useRules.js`, `RulesView.jsx`, `LibraryRecipePicker.test.jsx` |
| F4 (mechanical) | T27 ticked; note rewritten to record 3-of-3 sites wired (was stuck at "2 of 3, stays open until T33"). | `specs/frontend_spa/tasks.md` |
| F5 (mechanical, bookkeeping) | `progress/current.md`'s "19 new keys" corrected to 17 (16 `RULES_*` + `CONFIRM_REMOVE_RULE`). | `progress/current.md` |
| F6 (real UX defect) | `useLibraryPicker` now exposes `allRecipes` (the unfiltered polled list) alongside its existing filtered `recipes`; `RulesView.recipeName()` resolves pin display names from `allRecipes` instead of `recipes`, so typing in the pin picker's own search box no longer churns already-displayed pin rows back to raw ids. Purely additive — `RecipeAuthoringForm.jsx`/`LibraryRecipePicker.jsx` both spread `{...picker}` into a component that destructures only its named props, so the new field is inert there; `useLibrary.js` destructures specific fields, unaffected. | `useLibraryPicker.js`, `RulesView.jsx` |

### F1/F2 mutation-kill confirmation

**F1** — hand-reverted `recipeName()` to `return recipeId;`. Both the
corrected pin-name test and the new F6 regression test failed (`Unable to
find an element with the text: lunes · Comida · Tortilla`). Restored;
suite green again.

**F2** — hand-swapped the category-count `<select>` for a plain
`<input type="text">`. The new dropdown-only test failed (`expected […] to
have a length of 1 but got 2`). Restored; suite green again.

### F6 regression coverage

New test: a pin rule with `picker.filters.name` set and `picker.recipes`
empty (simulating the picker's own search excluding that recipe) still
renders the resolved name from `allRecipes`, not the raw id.

### Test result

`npx vitest run` — **174/174 passed, 28 files** (172 → 174: 2 new cases in
`RulesView.test.jsx`, F1 and F2). `npx eslint .` clean. `./init.sh` fully
green — **795 backend pytest** (unchanged), ruff/mypy/prettier/eslint/vitest
all pass. Re-ran `useLibraryPicker.test.js`, `LibraryRecipePicker.test.jsx`,
`useRecipeAuthoring.test.js`, `RecipeAuthoringForm.test.jsx`, `useLibrary.test.js`
individually — 51/51 pass, no regressions from the additive `allRecipes` field.

## Shopping list view (T35–T37) — 2026-09-14

Scope: only `specs/frontend_spa/tasks.md`'s "Shopping list view" section
(T35–T37, lines 203–224). No later section (Summary, App shell, Auth)
touched. Built on the reviewer-approved T1–T34.

### Traceability

| Task | File(s) | `R<n>` |
|---|---|---|
| T35 | `frontend/src/hooks/useShoppingList.js` | R18, R20; consumes `FR-SHOP-01…10` (features 7/8/27, no `R<n>` for aggregation/re-sync semantics) |
| T36 | `frontend/src/components/ShoppingListView.jsx` | R19, R20, R21 |
| T37 | `frontend/tests/hooks/useShoppingList.test.js`, `frontend/tests/components/ShoppingListView.test.jsx` | R18, R19, R20, R21 |

`FR-*` reachability this slice: `FR-UX-04` (R18), `FR-UX-05` (R19, R20),
`FR-UX-06` (R21) all reached — the same three already reached by earlier
sections, so no new feature-`covers` id becomes reachable here; `FR-SHOP-*`
themselves are cited-not-owned (features 7, 8, 27 own the aggregation/
re-sync domain logic — this slice only displays results and calls the
already-`done` endpoints).

### Design decisions filling spec gaps

1. **`useShoppingList` fetches `GET /v1/live-weeks` once (not polled)**,
   mirroring `useWeekPlanner`'s own one-time fetch — needed to feed the
   resync button's `WeekLabel` scope copy (design.md section 5: "the
   shopping re-sync trigger... week-scoped per `FR-SHOP-05`"). Not a new
   poll: design.md's Screens table lists only `usePolling(GET
   /v1/shopping-list)` for this view, and a one-time fetch doesn't add one.
2. **The resync button renders both a `current` and a `next` `WeekLabel`**,
   not one. `FR-SHOP-05`'s scope is "current week from today onward plus
   the whole next week" (`rest_api_contract.md` section 3.3) — a single
   week designation would misstate the actual scope, which the backend
   computes and this component only labels (no client-side date math).
3. **A live-weeks fetch failure only hides the scope label** (`liveWeeks`
   stays `null`, `ResyncScope` renders no `WeekLabel`s) rather than setting
   the hook's `error` field — the shopping list itself, its poll, and the
   resync button all still function; a decorative label failing is not the
   same failure class as a mutation failing.
4. **Edit pre-fills the item form from the real item** (`itemToDraft`,
   mirroring `useLibrary`'s F4 fix) — `openEdit(item)` seeds `draft` from
   `item.name`/`quantity`/`unit` before opening the form, so saving an edit
   without changes round-trips the real values instead of overwriting with
   blanks.
5. **No retry logic exists for the `409 SHOPPING_LIST_LOCK_HELD` case** —
   `resync`'s `catch` sets `error` to the caught `ApiError.detail` (already
   es-ES, per `rest_api_contract.md` section 3.3's "the client does not
   auto-retry") and returns; nothing schedules a second call. `T37`'s test
   asserts exactly one `/v1/shopping-list/resync` call after the rejection.

### Test result

`npx vitest run` — **198/198 passed, 32 files** (174 → 198: 12 new cases in
`useShoppingList.test.js` + 12 new cases in `ShoppingListView.test.jsx`, both
new files). `npx eslint .` clean. `npx prettier --check .` clean after one
`--write` pass on the two new files. `./init.sh` fully green — **795 backend
pytest** (unchanged, no `backend/` file touched), ruff/mypy/prettier/eslint/
vitest all pass.

## Shopping list view — Fix round 1 (6 reviewer findings) — 2026-09-14

Scope: the 6 findings on T35–T37 above. No other `frontend_spa` section
touched.

| Finding | Fix | File(s) |
|---|---|---|
| M1 (blocking, surviving mutant) | Edit test now asserts the full PUT body (`{name, quantity, unit}`) against the fixture's real values, not just `method: 'PUT'`. | `useShoppingList.test.js` |
| M2 (blocking, surviving mutant) | New test scopes `within()` each section's `<ul>` (found via each heading's `nextElementSibling`) and asserts each item lands only in its own section. | `ShoppingListView.test.jsx` |
| M3 (blocking, surviving mutant) | 409 test now uses `vi.useFakeTimers()` + `vi.advanceTimersByTimeAsync(60_000)` before asserting exactly one resync call — no longer just a synchronous count. | `useShoppingList.test.js` |
| M4 (blocking, real bug per the finding) | `resync`'s `finally { setIsResyncing(false) }` was already present in the committed code (no source change needed) — added the missing test asserting `isResyncing === false` after a 409 rejection. | `useShoppingList.test.js` |
| Decision 2 (real UX bug — copy) | `SHOPPING_LIST_RESYNC_SCOPE_LABEL` reworded to `'Se resincronizará desde hoy hasta el final de la semana próxima:'` (states the true `FR-SHOP-05` scope up front, so the current-week `WeekLabel`'s full Monday–Sunday range no longer overstates what's in scope); new `SHOPPING_LIST_RESYNC_SCOPE_CONNECTOR` (`'y'`) rendered between the two `WeekLabel`s so they no longer read jammed together. `WeekLabel.jsx` itself untouched. | `es-ES.js`, `ShoppingListView.jsx` |
| Decision 3 (test gap) | New test rejects the live-weeks fetch and asserts `liveWeeks === null` **and** `error === null`, plus that the list and resync still work. | `useShoppingList.test.js` |

### Mutation-kill confirmation (M1–M4)

Each mutant hand-applied, run against its named test, confirmed failing, then reverted:
- M1: hardcoded `quantity: 1` on the edit path → new body assertion failed on the wrong quantity.
- M2: swapped `uncheckedItems.map`/`checkedItems.map` → new `within()` assertions failed (`arroz` not found in its scoped list).
- M3: added a `setTimeout(...resync POST..., 1000)` inside the catch → call-count assertion failed (`2` vs expected `1`) after `advanceTimersByTimeAsync`.
- M4: moved `setIsResyncing(false)` out of `finally` into the success branch only → new `isResyncing === false` assertion failed (`true` vs expected `false`).

### Test result

`npx vitest run` — **200/200 passed, 30 files** (198 → 200: 1 new case in
`ShoppingListView.test.jsx` (M2) + 1 new case in `useShoppingList.test.js`
(decision 3); the M1/M3/M4 findings extended existing tests in place rather
than adding new ones). `npx eslint .` clean. `npx prettier --check .` clean
after one `--write` pass. `./init.sh` fully green — **795 backend pytest**
(unchanged), ruff/mypy/prettier/eslint/vitest all pass.

## Summary view (T38–T40) — 2026-09-14

Scope: `specs/frontend_spa/tasks.md` lines 226–239 only. Built on the
reviewer-approved T1–T37 (Shopping list slice, done). Closes T20/T21's
deferred 4th `openDetail` call site — `SummaryView`'s meal rows — the last
of the 4 named sites (`MealCard` regular + definitive, `LibraryView`'s rows,
`SummaryView`'s rows).

### Design decision made within spec bounds

The Screens table (`design.md` §5) cites only **R5, R21** for `SummaryView`
— not R2/R3 (the week-switcher requirement, scoped to `FR-MENU-07`). T38's
own task text lists no `switchWeek`/`designation` output either, unlike
T14's. `useSummary` therefore fetches `GET /v1/live-weeks` once and polls
only the **current** live week's summary, with no switch control — this
follows the coverage table literally rather than inventing a second
switcher UI `design.md` does not ask for. `FR-SUM-01`'s "current or next"
phrasing describes the view type's general capability, not a mandated
in-screen control for this feature's `R<n>` set.

### Files

| File | Purpose |
|---|---|
| `frontend/src/hooks/useSummary.js` | `usePolling(GET /v1/weeks/{weekId}/summary)` for the current live week; `buildSummaryViewModel` regroups the backend's definitive-only `meals` array into the full 7×2 grid (empty cells stay `null`); composes `useRecipeDetail` for `openDetail`/`detail`/`closeDetail` (T18, same as `useWeekPlanner`/`useLibrary`). |
| `frontend/src/components/SummaryView.jsx` | Read-only grid (`DAY_LABELS`/`SLOT_LABELS`), `WeekLabel` header, `EmptyState` when `summary.isEmpty`, `LoadingState` before the first data, `RecipeDetailView` opened via the shared opener. |
| `frontend/src/messages/es-ES.js` | +2 keys: `SUMMARY_VIEW_TITLE`, `SUMMARY_VIEW_EMPTY`. |
| `frontend/tests/hooks/useSummary.test.js` | 5 cases (new file). |
| `frontend/tests/components/SummaryView.test.jsx` | 7 cases (new file). |

### Traceability

| `R<n>` | Covered by |
|---|---|
| R5 (recipe detail reachable from the summary) | `useSummary.test.js` "openDetail resolves to a normalized recipe via the shared opener"; `SummaryView.test.jsx` "clicking a meal calls openDetail with that candidate, same opener pattern as T21" |
| R19 (empty state) | `useSummary.test.js` "zero definitives sets the empty-state flag"; `SummaryView.test.jsx` "zero definitives sets the empty-state flag" |
| R21 (week label: designation + Monday–Sunday range) | `SummaryView.test.jsx` "renders the WeekLabel header with the current designation and range" |
| No new `R<n>` (T38) — consumes `FR-SUM-01`/`-03` (feature 5, done) | `useSummary.test.js` "fetches live-weeks once and polls the current week summary" |

`FR-SUM-01`/`-03` are consumed, not owned (feature 5's `week_plan_model`
owns them) — same convention as every other consumed-FR row in this
feature's Screens table.

### Mutation-kill confirmation (grouping membership, Shopping list M2 lesson)

`buildSummaryViewModel`'s slot key was hand-mutated from
`` `${entry.day}-${entry.slot}` `` to a fixed `` `1-${entry.slot}` `` (every
meal collapses onto day 1). `useSummary.test.js`'s "groups a definitive meal
under its exact day and slot" test **failed** as expected (day 3's slot
stayed `null`); reverted, full suite re-run green.

### Test result

`npx vitest run` — **212/212 passed, 32 files** (200 → 212: 5 new cases in
`useSummary.test.js` + 7 new cases in `SummaryView.test.jsx`, both new
files). `npx eslint .` clean. `npx prettier --check .` clean after one
`--write` pass on the 3 new files. `./init.sh` fully green — **795 backend
pytest** (unchanged, no `backend/` file touched), ruff/mypy/prettier/eslint/
vitest all pass.

`specs/frontend_spa/tasks.md`: T38/T39/T40 ticked `[x]`. **T20 and T21
flipped from their "3 of 4"/Partial notes to fully `[x]`, no partial note
remaining** — all 4 named `openDetail` call sites now exist and are tested.

### Fix round 1 (reviewer findings, 2026-09-14)

- **Finding 1** — added one `within()`-scoped test to `SummaryView.test.jsx`
  asserting the day-3 column renders the meal AND its slot label ("Cena"),
  and the day-2 column doesn't. Kills the slot-label swap mutant
  (`SLOT_LABELS[slotState.slot]` → other slot) and the day off-by-one mutant
  (`DAY_LABELS[day.day]` → `DAY_LABELS[(day.day % 7) + 1]`) — hand-applied
  each separately, saw the new test fail, reverted both.
- **Finding 2** — trimmed `useSummary.js`'s banner from 4 lines to 3,
  pointing here instead of reproducing the polling/designation rationale.
- `npx vitest run` — **213/213 passed, 32 files** (212 → 213: 1 new case).
  `npx eslint .` clean. `./init.sh` fully green.

## App shell (T41–T45) — 2026-09-14

Scope: `specs/frontend_spa/tasks.md` lines 237–257 only. Built on the
reviewer-approved T1–T40 (all 7 meal-planning views). Explicitly excludes
the auth screens section (T46+, `design.md` §5a) — `useApp.js` has no
session/role awareness; T48/T49 extend it later.

### Design decision: how `ConnectionLostBanner` gets a single `connectionLost`

Verified the convention holds across all 5 view hooks — `useWeekPlanner`,
`useLibrary`, `useRules`, `useShoppingList`, `useSummary` each return a
top-level `connectionLost` boolean (grep-confirmed, one line per hook).
`App.jsx` calls all 5 every render (Rules of Hooks forbid a *different* hook
per branch across renders — that constraint is about hook order within one
component, not about what each hook does internally), then picks
`{ week, library, rules, shoppingList, summary }[activeView].connectionLost`
and passes that single boolean into one `<ConnectionLostBanner>` call site.
`ConnectionLostBanner` itself stays a plain presentational component
(`connectionLost` in, `MESSAGES.CONNECTION_LOST` or `null` out) — no
per-view special-casing needed.

Each hook takes an `active` flag threaded down to its own poll(s) — see
"Fix round 1" below for the mechanism and the measured before/after.

### Files

| File | Purpose |
|---|---|
| `frontend/src/hooks/useApp.js` | `activeView` state (`useState('week')`), `navigateTo(view)`. No auth. |
| `frontend/src/components/App.jsx` | Nav strip (`WeekSwitcher.jsx`'s active/inactive `terraSoft` button pattern, reused), the active view's component, one `ConnectionLostBanner`. |
| `frontend/src/components/ConnectionLostBanner.jsx` | `connectionLost` in, `MESSAGES.CONNECTION_LOST` (`honeySoft` background — the palette's warning accent per `design.md` line 175) or `null` out. |
| `frontend/src/messages/es-ES.js` | +6 keys: `NAV_WEEK`, `NAV_LIBRARY`, `NAV_RULES`, `NAV_SHOPPING_LIST`, `NAV_SUMMARY`, `CONNECTION_LOST`. |
| `frontend/src/main.jsx` | Mounts `App` instead of `PlaceholderView` (`PlaceholderView.jsx` itself untouched, feature 1's scaffold record). |
| `frontend/tests/hooks/useApp.test.js` | 2 cases (new file). |
| `frontend/tests/components/App.test.jsx` | 4 cases (new file) — hooks and the 5 view components are mocked so this file tests only `App.jsx`'s own wiring (which view mounts, which poll feeds the banner), not each view's own rendering (already covered by that view's own test file). |
| `frontend/tests/components/ConnectionLostBanner.test.jsx` | 2 cases (new file). |

### Traceability

| `R<n>` | Covered by |
|---|---|
| No `R<n>` (T41) — pure navigation plumbing, `design.md` §7 | `useApp.test.js` both cases |
| No `R<n>` (T42) — wires `FR-RT-03` (feature 26, done, this feature's job per its design §8) | `ConnectionLostBanner.test.jsx` both cases; `App.test.jsx` "renders the connection-lost banner when the ACTIVE view reports connectionLost" + "does not render the banner when a non-active view is the one reporting connectionLost" |

No new `covers` entry — `FR-RT-03` is consumed here, not owned; feature 20's
`covers` array only holds `FR-MENU/CAND/LIB/UX` ids. This slice only adds
the SPA-side test proving the wire-up, same "consumed, not owned" convention
as every other row in `design.md` §1.2.

### Mutation-kill confirmation

Two hand-applied mutants, both reverted after confirming failure:
1. `App.jsx`'s active-view lookup pinned to `['week']` instead of
   `[activeView]` — `App.test.jsx`'s "does not render the banner when a
   non-active view..." case failed as expected (clicking into `library`
   with `library`'s `connectionLost: true` no longer showed the banner).
2. `ConnectionLostBanner.jsx`'s guard flipped (`if (connectionLost) return
   null`) — both of its own test cases failed as expected.

### Test result

`npx vitest run` — **221/221 passed, 35 files** (213 → 221: 8 new cases
across the 3 new test files). `npx eslint .` clean. `npx prettier --check .`
clean. `npx vite build` succeeds (56 modules, no runtime import errors) —
first time the SPA mounts `App` instead of `PlaceholderView`. `./init.sh`
fully green — **795 backend pytest** (unchanged, no `backend/` file
touched), ruff/mypy/prettier/eslint/vitest all pass.

`specs/frontend_spa/tasks.md`: T41–T45 ticked `[x]`.

### Nothing the spec didn't anticipate

T41–T45 matched the design cleanly; the only judgment call was the
unconditional-hook-calls tradeoff above, which the spec doesn't mention
either way.

## App shell — Fix round 1 (5 reviewer findings) — 2026-09-14

Scope: the 5 findings raised on the App shell section above.

| Finding | Fix | File(s) |
|---|---|---|
| F1 (BLOCKING, real defect, measured) | Each of the 5 view hooks now takes `{ active = true }`, threaded to every `usePolling`/`useLibraryPicker` call inside; `useRecipeAuthoring` also takes `active` and ANDs it with its own `method`-based picker gates. `App.jsx` passes `{ active: activeView === '<view>' }` per hook instead of no arguments. | `useWeekPlanner.js`, `useLibrary.js`, `useRules.js`, `useShoppingList.js`, `useSummary.js`, `useRecipeAuthoring.js`, `App.jsx` |
| F2 (BLOCKING) | `weekUrl`/`summaryUrl` now gate `enabled` too (`enabled: url !== null && active`) — no more `fetch(null)` before `/v1/live-weeks` resolves. | `useWeekPlanner.js`, `useSummary.js` |
| F3 (mechanical) | Corrected the false "Rules of Hooks forbid a per-view hook" rationale everywhere it appeared — the constraint is about hook order within one component, not about gating what a hook does internally. | `App.jsx` banner, this file's "App shell" section, `progress/current.md` |
| F4 (mechanical, 3-line ceiling) | Trimmed `App.jsx`'s 7-line banner to 3 lines, pointing at this section. | `App.jsx` |
| F5a (nit) | `App.jsx` now derives `NAV_ITEMS` from `useApp.js`'s `VIEWS` export instead of a second hardcoded view list. | `App.jsx` |
| F5b (mechanical) | Corrected this file's `FR-RT-03` sentence above (consumed, not owned - not in `covers`). | `progress/impl_frontend_spa.md` |

### F1 proof (re-measured with the reviewer's approach)

New `App.polling.test.jsx`: real hooks (only the fetch boundary mocked),
fake timers, `App` mounted with the default `week` view active, timers
advanced 60s. Result: `/v1/weeks/2026-W34` polled repeatedly (3 times at
jsdom's 30s background interval — `document.hasFocus()` is `false` by
default in jsdom, so `isBackgrounded` is true); `/v1/library/recipes`,
`/v1/rules`, `/v1/shopping-list`, and `/v1/weeks/2026-W34/summary` were
**never called** (0 requests) — the 4 inactive views' polling loops never
start. Also added: `App.test.jsx` asserts `active: true`/`active: false`
reach exactly the right hooks on mount and after navigation; each of the 5
view hooks (plus `useRecipeAuthoring`) gained its own `active -> enabled`
unit test, reusing the Library slice's `enabled`-test pattern.

### Test result

`npx vitest run` — **232/232 passed, 37 files** (221 → 232: 11 new cases
across `useWeekPlanner.test.js` (+2), `useSummary.test.js` (+2),
`useLibrary.test.js` (+1), `useRules.test.js` (+1), `useShoppingList.test.js`
(+1), `useRecipeAuthoring.test.js` (+1), `App.test.jsx` (+2), and the new
`App.polling.test.jsx` (+1)). `npx eslint .` clean. `npx prettier --check .`
clean. `./init.sh` fully green — **795 backend pytest** (unchanged, no
`backend/` file touched), ruff/mypy/prettier/eslint/vitest all pass.

Re-ran the 5 view-hook suites, `App.test.jsx`, `useApp.test.js`,
`useRecipeAuthoring.test.js`, and `useLibraryPicker.test.js` individually
(86 tests) — zero regressions from threading `active` through.

`specs/frontend_spa/tasks.md`: T41–T45 remain ticked (fix round, no new task).

### Fix round 2 (comment trims) — 2026-09-14

Trimmed the two over-length comments the reviewer flagged: `useRecipeAuthoring.js`'s
5-line block and `App.polling.test.jsx`'s 4-line banner, both now ≤3 lines and
pointing here. Also tightened `App.polling.test.jsx`'s assertion from
`toBeGreaterThan(1)` to `toBe(3)` (stable across 5 runs). `npx vitest run` —
232/232. `npx eslint .` clean.

## Auth screens, first half — session probe, nav gating, login, set-password (T46–T53) — 2026-09-14

Scope: only `specs/frontend_spa/tasks.md`'s "Auth screens" section, **T46–T53**
(lines 259–298). T54 (self-password-change scan), and the admin-accounts /
App.jsx render-branch wiring (T55–T60, a separate dispatch) are explicitly out
of scope — not touched. Built on the reviewer-approved T1–T45.

### Traceability

| Task | File(s) | `R<n>` |
|---|---|---|
| T46 | `frontend/src/hooks/useSession.js` | R23, R25, R27, R32 |
| T47 | `frontend/tests/hooks/useSession.test.js` | R23, R25, R26, R27, R32 |
| T48 | `frontend/src/hooks/useApp.js` (extended) | R30, R31 |
| T49 | `frontend/tests/hooks/useApp.test.js` (extended) | R30, R31 |
| T50 | `frontend/src/hooks/useLoginForm.js`, `frontend/src/components/LoginView.jsx` | R24, R25, R29 |
| T51 | `frontend/tests/hooks/useLoginForm.test.js`, `frontend/tests/components/LoginView.test.jsx` | R24, R25, R29 |
| T52 | `frontend/src/hooks/useSetPasswordForm.js`, `frontend/src/components/SetPasswordView.jsx` | R26, R27 |
| T53 | `frontend/tests/hooks/useSetPasswordForm.test.js`, `frontend/tests/components/SetPasswordView.test.jsx` | R26, R27 |

`FR-*` reachability this slice: each `R23`–`R32` cites an `FR-AUTH-*` id owned
by feature 15/16 (`FR-AUTH-01/-02/-03/-04/-05/-06/-09/-10`), same
"consumed, not owned"-style citation `design.md` section 1.1 describes for
the auth-screens fold — none of these ids are in feature 20's own `covers`
array (`requirements.md`'s coverage-check footnote already documents this).

### `useApp.js`'s gating design — additive, not blocking (deviation worth flagging)

T48 reads as "the five targets are reachable only when authenticated User".
Implemented as an **additive** `navTargets` field (`VIEWS` when gated open,
`[]` otherwise) rather than making `navigateTo` itself refuse a call: `App.jsx`
(untouched this run, per the brief) still renders its nav strip unconditionally
off the `VIEWS` constant and calls `navigateTo` directly — gating `navigateTo`
against `session.status` would silently break `App.test.jsx`'s existing,
reviewer-approved synchronous `fireEvent.click` assertions, since those never
await `useSession`'s mount-time probe. `navTargets` is the seam T59 (App.jsx's
real render-branch wiring) is expected to consume instead of the raw `VIEWS`
import. `App.test.jsx`/`App.polling.test.jsx` needed one addition each: the
former now mocks `useSession.js` (matching its own stated intent of testing
"only App.jsx's own job"); the latter already mocked `apiFetch` broadly enough
to cover `useSession`'s new internal call without changes.

### `useSession.js`'s error-handling design

`login`/`setPassword`/`logout` do not catch — they let a rejection propagate,
matching `design.md` section 5a's own pseudocode. Each consuming view hook
(`useLoginForm`, `useSetPasswordForm`) owns its own `error: string | null`
state and a local `toDetail()` catch, the same per-call-site convention
`useShoppingList.js`/`useWeekPlanner.js` already established (fix round 1
finding 3, "no existing centralised error-state convention to match"). Kept
consistent rather than inventing a second shape inside `useSession` itself,
whose own three mutating calls each need a different reaction to failure
(inline field error vs. nothing) that a shared `error` slot could not express.

### Session probe classification kept mutation-resistant by construction

`classifyProbeFailure` is a named, standalone function with one `if` per
outcome (`PASSWORD_RESET_PENDING` → pending, `FORBIDDEN` → Admin, else →
anonymous) rather than a nested ternary — hand-mutated the `FORBIDDEN` branch's
role from `'Admin'` to `'User'` and `useApp.js`'s `session.role === 'User'`
check to `true`; both killed by `useSession.test.js`/`useApp.test.js`
respectively (test output in this session's transcript), then reverted.

### Test result

`npx vitest run` — **263/263 passed, 47 files** (232 → 263: 31 new — 9 in
`useSession.test.js`, 5 in `useLoginForm.test.js`, 3 in `LoginView.test.jsx`,
6 in `useSetPasswordForm.test.js`, 5 in `SetPasswordView.test.jsx`, 3 new in
`useApp.test.js`). `npx eslint .` clean. `npx prettier --check .` clean (one
`--write` pass on the two new hook test files). `./init.sh` fully green —
**795 backend pytest** (unchanged, no `backend/` file touched),
ruff/mypy/prettier/eslint/vitest all pass.

### Messages added

10 new keys in `frontend/src/messages/es-ES.js`'s new "Auth screens" block:
`LOGIN_VIEW_TITLE`, `LOGIN_USERNAME_LABEL`, `LOGIN_PASSWORD_LABEL`,
`LOGIN_SUBMIT`, `SET_PASSWORD_VIEW_TITLE`, `SET_PASSWORD_NEW_LABEL`,
`SET_PASSWORD_CONFIRM_LABEL`, `SET_PASSWORD_MISMATCH`, `SET_PASSWORD_SUBMIT`,
`SET_PASSWORD_CANCEL`. `LOGIN_USERNAME_LABEL`/`PASSWORD_LABEL`/`SUBMIT` and
the set-password field labels are mined verbatim from the prototype's Login
and "Nueva contraseña" screens (`Sobremesa.dc.html` lines 66–110, per
`design.md` section 5a's own citation); `LOGIN_VIEW_TITLE`/`SET_PASSWORD_MISMATCH`
are new, uncontradicted copy (the prototype's brand mark "Sobremesa" isn't
this product's identity; no client-side mismatch copy exists in the prototype
to mine, since it only shows a server-side `pwError`).

### What T54–T60 still owe (explicitly not started here)

`T54`'s mechanical no-self-password-change scan, `AdminAccountsView` +
`useAdminAccounts.js` (R33–R37), `App.jsx`'s logout control (R32's control
itself — `useApp.js` now exposes `logout`, but no button calls it yet), and
the render-branch wiring in `App.jsx` that actually mounts `LoginView`/
`SetPasswordView`/`AdminAccountsView` off `session.status`/`role` instead of
the always-on 5-view shell.

## Auth screens — Fix round 1 (4 reviewer findings) — 2026-09-14

1. **Password masking (blocking, security).** Added a `type` assertion per
   password field: `LoginView.test.jsx` (login password),
   `SetPasswordView.test.jsx` (new-password and confirm, both asserted in one
   test). Hand-flipped each `type="password"` to `type="text"` in
   `LoginView.jsx`/`SetPasswordView.jsx`, confirmed the new assertion fails,
   reverted — all three mutants now KILL.
2. **`design.md` ordering claim (docs-only).** Section 5a's "R23's mechanism"
   paragraph wrongly claimed `PASSWORD_RESET_PENDING` fires before the role
   check for either role. `handler.py`'s `handle()` checks
   `spec.requires_role` first, `password_reset_required` second — corrected
   the paragraph to state the real precedence. **Flagged limitation for the
   owner:** an Admin with a pending reset gets `403 FORBIDDEN` from the role
   check (`GET /v1/live-weeks` requires `Role.USER`), which `useSession.js`'s
   probe misclassifies as `authenticated(Admin)` rather than
   `passwordResetPending` — reachable only via the mount-time probe path
   (login's own response carries `passwordResetRequired` directly and is
   handled correctly). Bounded: the backend still rejects every admin action
   for that account regardless of this misclassification, but such an admin
   can never reach the set-password screen without a fresh login. Fixing it
   properly needs either a backend response-shape change (features 15/16,
   already `done`) or a different probe strategy — neither is this slice's
   call; flagging for the owner to decide whether it's worth a future gap.
   Added a 3-line pointer comment next to `classifyProbeFailure` in
   `useSession.js`.
3. **T48 over-ticked (mechanical).** Un-ticked; added the same "Partial —
   built and tested at the hook level, no consumer until T59" note this
   feature already uses for T13/T20/T21/T23/T27/T31.
4. **Comment ceiling (mechanical).** Trimmed `useSession.js`, `useApp.js`,
   `useSetPasswordForm.js` header comments to ≤3 lines each, pointing at this
   section instead of reproducing the reasoning.

Test result: `npx vitest run` — **265/265 passed, 41 files** (263 → 265: the
two new masking assertions). `npx eslint .` clean.

## Auth screens, second half (T54–T60) — 2026-09-14

Scope: `specs/frontend_spa/tasks.md`'s remaining Auth-screens tasks
(T54–T60), plus finally closing T48 (the render-branch consumer the first
half's review left open). Built on the reviewer-approved T1–T53.

### Traceability

| Task | File(s) | `R<n>` |
|---|---|---|
| T48 (closed) | `frontend/src/components/App.jsx` | R30, R31 |
| T54 | `frontend/tests/test_no_self_password_change.test.js` | R28 |
| T55 | `frontend/src/hooks/useAdminAccounts.js` | R18, R35 |
| T56 | `frontend/src/components/AdminAccountsView.jsx`, `AccountRow.jsx`, `frontend/src/domain/labels.js` (+`ROLE_LABELS`) | R33, R34, R36, R37, R19, R20 |
| T57 | `frontend/tests/hooks/useAdminAccounts.test.js`, `tests/components/AdminAccountsView.test.jsx`, `AccountRow.test.jsx`, `tests/domain/labels.test.js` (+`ROLE_LABELS` case) | R18, R33, R34, R35, R36, R37 |
| T58 | `frontend/src/components/App.jsx` (logout button, both shells) | R32 |
| T59 | `frontend/tests/components/App.test.jsx` (extended) | R23, R26, R30, R31, R32 |
| T60 | `frontend/src/messages/es-ES.js` (+13 keys: `APP_LOGOUT` + 12 `ADMIN_ACCOUNTS_*`) | R15 |

Fix round 1 finding 5 (bookkeeping): T60's message-key count was mis-reported
as 15 — the 2 role labels (`Admin`/`User`) shown per row live as values in
`ROLE_LABELS`, `frontend/src/domain/labels.js` (T56 row above), a different
module from `es-ES.js`, not `es-ES.js` keys themselves.

`FR-*` reachability (feature `covers` array — this slice adds no new `FR-*`
beyond what T46–T53 already reached; R30/R31/R32/R33/R34/R35/R36/R37 all cite
`FR-AUTH-01/-05/-06/-09/-12/-18` as already recorded in `requirements.md`).

### Design decisions / deviations from the literal task text

1. **`useSession.js` gained `userId` on the `login()` branch (additive).**
   Design.md §5a's own `AdminAccountsView` row (line 599) already assumes an
   "acting admin" prop sourced from session, needed for R37's self-row
   hiding — but T46's built `useSession.js` never captured it (the mount
   probe's `GET /v1/live-weeks` response carries no `userId` at all; only
   `POST /v1/session`'s login response does, per `routing.py::_login`).
   Fixed by reading `result.userId` into the `authenticated` branch of
   `login()` only. Purely additive: `toEqual`'s undefined-property handling
   meant neither existing `useSession.test.js` assertion needed to change:
   one new test proves it flows through. **Known limitation, same class as
   the existing R23 probe gap**: a page reload as an already-authenticated
   Admin (no fresh `login()` this session) leaves `session.userId`
   `undefined`, so the reset-password control shows on every row including
   the admin's own; the server still rejects that specific call with
   `Forbidden` (`admin_set_password`), same generic error surfacing every
   other mutation uses. No data loss, no crash, bounded.
2. **`GET /v1/users/{userId}` path param, not `{username}`.** The dispatch
   brief's task text said `PATCH .../{username}`; the actual, frozen
   contract (`rest_api_contract.md` line 116, `routing.py` line 800) and
   design.md §5a both use `{userId}`. Implemented against the real contract.
3. **T54's literal filename doesn't run.** `test_no_self_password_change.js`
   (no `.test.` infix) never matches `vite.config.js`'s
   `include: ['tests/**/*.test.{js,jsx}']` — the spec text borrowed the
   backend's `test_*.py` pytest convention, which Vitest's own glob does
   not mirror. Named `test_no_self_password_change.test.js` instead so the
   guard actually executes; `tasks.md` T54 notes the correction.
4. **T57's "all four controls... for an ordinary row (R34)"** — R34 names
   four actions (create, rename, reset, remove); create is view-level (the
   form above the list), not per-row. Interpreted as: with one ordinary
   fixture row, all four of R34's named controls are present somewhere on
   the screen (`AdminAccountsView.test.jsx` asserts the create form's two
   fields + button; `AccountRow.test.jsx` asserts rename/reset/remove
   render for an ordinary row).
5. **T60's 3 fallback-caption codes.** No new message keys added for
   `INVALID_CREDENTIALS`/`PASSWORD_TOO_SHORT`/`USERNAME_ALREADY_TAKEN` — every
   error path in this slice (and every prior one) renders `err.detail`
   verbatim, already es-ES from the backend (design.md §5a: "same generic
   pattern... no new mechanism"). Adding client-side duplicates would drift
   from `planner_core.messages`, the actual source of that text.
6. **Rename/reset-password state lives in the hook, one row open at a
   time** (`renamingId`/`resettingId` + a single shared draft each),
   mirroring `useShoppingList.js`'s `editingItem`/`draft` idiom rather than
   per-row local component state — keeps `AccountRow.jsx` a pure function
   of props, matching every other row component in this feature (`ItemRow`,
   `RuleRow`).
7. **`useAdminAccounts.js`'s mount effect inlines its own `apiFetch(...).then()`**
   rather than calling the memoized `refetch` callback — `react-hooks/set-state-in-effect`
   flags a named async setState-caller invoked from an effect body;
   `useShoppingList.js`'s live-weeks read already uses the same inline
   shape for the same reason. `refetch` itself is unchanged and still used,
   unmodified, by all four mutations.
8. **`App.jsx`'s render branch is `if`-chained, not a lookup table**: each
   of `loading`/`anonymous`/`passwordResetPending` returns immediately;
   Admin/User are two more, mutually exclusive `if` blocks; a trailing
   `return null` documents the branch as otherwise unreachable rather than
   silently falling through. A dedicated test now covers the `loading`
   branch too (previously untested — the mutation probe below caught the
   gap while checking for fallthrough).

### Mutation probes (hand-applied, all confirmed killed, then reverted)

1. `AccountRow.jsx`'s `isOwnRow` (`===` → `!==`): 3/7 `AccountRow.test.jsx`
   cases failed (R37).
2. `AccountRow.jsx`'s `isAdminRow` (`===` → `!==`): 4/7 cases failed (R36).
3. `App.jsx`'s `isAdmin` collapsed onto the same condition as `isUser`
   (`role === 'Admin'` → `role === 'User'`): 8/12 `App.test.jsx` cases
   failed (R30/R31/R32 render-branch mapping).
4. `App.jsx`'s `loading` branch deleted: the new loading-state test failed,
   falling through to an unstyled empty `<div />` (confirms no silent
   fallthrough to the wrong shell) — this surfaced a genuine pre-mutation
   gap (no test covered the `loading` branch at all), fixed by adding the
   test before probing.

### Sanity check

`npx vite build` — 64 modules transform cleanly, confirming the real import
graph (`App.jsx` → `LoginView`/`SetPasswordView`/`AdminAccountsView` →
`AccountRow` → hooks) resolves with no circular/missing-import errors. No
live backend was available in this environment to exercise the actual
`anonymous → LoginView → POST /v1/session` network round-trip; the
render-branch logic itself is proven by `App.test.jsx`'s 4 new
session-status cases plus the 2 mutation probes above.

### Test result

`npx vitest run` — **294/294 passed, 45 files** (265 → 294: +29 — 1
`labels.test.js` case (`ROLE_LABELS`), 1 `useSession.test.js` case
(`userId`), 7 `App.test.jsx` cases (loading/anonymous/passwordResetPending/
Admin/User render branches + 2 logout cases), 7 `useAdminAccounts.test.js`,
7 `AccountRow.test.jsx`, 5 `AdminAccountsView.test.jsx`, 1
`test_no_self_password_change.test.js`). `npx eslint .` clean, `npx prettier
--check .` clean, `./init.sh` fully green (795 backend, ruff/mypy/prettier/
eslint/vitest).

### Fix round 1 (5 reviewer findings) — 2026-09-14

**Finding 1 (BLOCKING, real bug, security-relevant): R37 failed UNSAFE (open)
after a page reload, now fails CLOSED.** Root cause (reviewer-verified):
`useSession.js`'s mount-time probe (`GET /v1/live-weeks`) response carries no
`userId` field (`rest_api_contract.md` confirmed), so after a reload (not a
fresh `login()` — and with a 30-day session cookie this is the *dominant*
admin state, not an edge case) `session.userId` is `undefined`.
`AccountRow.jsx`'s old `account.userId === actingUserId` check was then
`false` for every row, showing reset-password on every row, including the
acting admin's own — the exact R37 violation. Fixed:
`isOwnRow = actingUserId == null || account.userId === actingUserId` — unknown
identity now hides reset on every row (safe default) instead of showing it on
every row (unsafe default). New `AccountRow.test.jsx` case
("hides reset-password on every row when actingUserId is not yet known")
covers it; hand-reverted to the old `===`-only check, confirmed the new case
**fails** (control renders), restored, confirmed passing again.

**This is a frontend-only mitigation, not the underlying fix.** The SPA still
has no reliable way to learn the acting admin's `userId` after a reload —
that needs a `rest_api_contract.md` change (adding `userId` to the probe
response) or a different identity-sourcing mechanism, out of scope here,
flagged to the owner separately (not touched: neither `backend/` nor
`rest_api_contract.md`). **Known limitation, visible not silent:** a reloaded
Admin session now sees reset-password hidden on ALL rows — including rows it
legitimately should be able to reset — until it logs in fresh (which
populates `userId` via `login()`'s response). This is a usability tradeoff
(some legitimate resets now require a fresh login first), not a security one
— the fail-closed default is the correct choice given the alternative was an
active R37 violation reachable by the dominant admin session state.
`useSession.js`'s banner now points here instead of restating this.

**Finding 2 (BLOCKING, surviving mutant): `App.jsx`'s
`actingUserId={session.userId}` wiring had no test.** `App.test.jsx`'s
`AdminAccountsView` mock now renders `actingUserId` into its marker text
(`` `ADMIN_ACCOUNTS_VIEW_MARKER:${actingUserId}` ``); the Admin-shell test
asserts the resolved value (`admin-1`). Hand-deleted the prop assignment in
`App.jsx`, confirmed the test **fails** (`...MARKER:undefined` rendered
instead), restored, confirmed passing.

**Finding 3 (BLOCKING, 2 surviving mutants): `saveRename`/`remove` had no
refetch-after-mutation coverage.** Design.md §9 / T55 require every mutation
to refetch the list; only `create`'s refetch was asserted. Added
`toHaveBeenCalledTimes` + `toHaveBeenLastCalledWith('/v1/users')` assertions
to both existing tests. Hand-deleted `await refetch()` from `saveRename` (own
test **fails**: 2 calls instead of 3, restored) and from `remove` (own test
**fails**: 1 call instead of 2, restored) in `useAdminAccounts.js`.

**Finding 4 (mechanical, comment ceiling):** 6 over-length comments trimmed
to the 3-line ceiling, each now pointing here instead of restating reasoning:
`App.jsx`, `useAdminAccounts.js`, `useSession.js`, `App.test.jsx`,
`useAdminAccounts.test.js`, `test_no_self_password_change.test.js`.

**Finding 5 (mechanical, bookkeeping):** this file's T60 row and
`progress/current.md` both said "15 new `es-ES.js` keys" for T54–T60; the
real count is 13 (`APP_LOGOUT` + 12 `ADMIN_ACCOUNTS_*`). The other 2 are
`ROLE_LABELS`'s values in `frontend/src/domain/labels.js` — a different
module, not `es-ES.js` keys. Both docs corrected.

`npx vitest run` 295/295 (294→295: +1, `AccountRow.test.jsx`'s fail-closed
case; findings 2/3 extended existing tests' assertions rather than adding new
cases). `npx eslint .` clean, `./init.sh` fully green (795 backend,
ruff/mypy/prettier/eslint/vitest). No `backend/` file touched, no
`rest_api_contract.md` edit, `feature_list.json` untouched. Still
`in_progress` — reviewer verification next.

## Cross-cutting mechanical guards + Gate (T61–T63) — 2026-09-14

Scope: only `specs/frontend_spa/tasks.md` lines 351–365 (T61–T63) — the
feature's final section. Built on the reviewer-approved T1–T60. **This is
the last implementer run for feature 20**; all tasks T1–T63 are now ticked.

### Traceability

| Task | File(s) | `R<n>` |
|---|---|---|
| T61 | `frontend/tests/test_no_extra_accessibility.test.js` | R22 |
| T62 | `frontend/tests/test_all_strings_from_messages.test.js` | R15 |
| T63 | `./init.sh` gate | n/a (verification, not a new `R<n>`) |

`FR-UX-07` (R22) and `FR-UX-01`/`FR-UX-03` (R15) — the last two `covers`
ids not yet mechanically enforced — are now reached.

### T61/T62 filename convention

Named `*.test.js`, not the tasks.md-literal `test_*.js` — same
`vite.config.js` `include: ['tests/**/*.test.{js,jsx}']` glob mismatch
T54 already hit (`test_no_self_password_change.test.js`); this run reused
that established fix rather than re-discovering it.

### Both guards passed clean on first run — no violation found

Scanned `frontend/src` and `frontend/src/components` by hand before writing
either test (`rg` for `aria-|role=|tabIndex|axe|react-aria` and for
non-attribute, non-import, non-comment double-quoted literals) — zero hits
in both cases, confirmed by the guards themselves once written. 60 tasks and
20+ review rounds held the line; no real violation surfaced.

### T62 scan design

`design.md` section 9 targets "a double-quoted string literal inside JSX
text content" — distinct from an attribute value (`type="button"`,
`designation="current"`, both letter-bearing but not user copy) and from
import-specifier/comment text (both contain quoted substrings too, e.g.
`LibraryFilters.jsx`'s header comment). The scanner strips block comments,
line comments, `import` lines, and `attr="value"` assignments first, then
flags any remaining quoted literal whose content has a letter or digit.
Self-verified against a synthetic `<button type="button">{cond ? "Sí" :
MESSAGES.CANCEL}</button>` fixture (catches the ternary literal, not the
`type` attribute) before trusting it against real source.

### Test result

`npx vitest run` — **299/299 passed** (295→299: 2 new test files, 2 cases
each — one self-verifying the scan pattern, one running it against the
real tree). `npx eslint .` clean. `./init.sh` fully green: ruff, mypy,
**795 backend pytest** (untouched by this feature), prettier, eslint,
vitest all pass.

### Feature 20 `frontend_spa` — implementation-complete

All of T1–T63 are done. Every `R<n>` in `specs/frontend_spa/requirements.md`
traces to a concrete test (per-section traceability tables above); every
`FR-*` in feature 20's `covers` array is reached via those `R<n>`s. Status
left `in_progress` — `done` is the owner's alone, after a final
comprehensive review. `feature_list.json` untouched by this run.

## T62 — Fix round 1 (reviewer finding: vacuous guard) — 2026-09-14

**Root cause (confirmed real).** `.prettierrc.json` sets `singleQuote:
true`, so `prettier --check`'s gate forces every non-JSX-attribute string
literal in this codebase to single quotes. T62's original
`STRING_LITERAL = /"([^"\\]|\\.)*"/g` only matched double-quoted literals —
after prettier, that set is empty by construction. It also never scanned
bare JSX text nodes (`<p>Texto</p>`, no quotes at all).

**Reviewer's cited violation — checked, not present.** The brief named
`EmptyState.jsx`'s `{message || 'No hay nada que mostrar todavia'}` as a
live, currently-shipped R15 violation. Read the file, its 9 call sites, and
`EmptyState.test.jsx`: the real, current `EmptyState.jsx` is
`<p ...>{message}</p>` — no fallback, no such string, no `EMPTY_STATE_DEFAULT`
key anywhere in `es-ES.js`. Grepped every `.jsx` under `src/components` for
bare-letter JSX text and for a Spanish-looking quoted phrase outside
`MESSAGES.*` — zero hits before this round's fix (confirmed again by the
corrected guard's clean run below). No file changed for this item; item 2 of
the dispatch brief does not apply to the tree as it stands.

**Guard rewritten** (`frontend/tests/test_all_strings_from_messages.test.js`).
Quote-agnostic and JSX-aware, scoped to each component's `return` JSX only
(so plain-JS string literals elsewhere in the file — role comparisons,
CSS values, view-name keys — are never in scope):

1. Extract each `return <expr>;`/`return (<expr>);` block (`looksLikeJsxReturn`
   rejects a helper like `return { display: 'flex' };` — not markup).
2. Strip `attr={...}` (balanced) and `attr="..."` — JSX attribute values.
3. Split the remainder into top-level `{...}` spans (children expression
   containers) vs. surrounding markup, recursively (nested JSX-in-expression,
   e.g. a `.map()` callback, gets the same treatment).
4. Flag a string literal inside a span only when it sits in a *rendering*
   position — right after `?`, `:`, `||`, `??`, `&&`, `=>`, or at the very
   start of the span — never after a comparison operator (`===`/`!==`/
   `==`/`!=`), so `activeView === 'week' ? <Foo/> : null` is not flagged.
5. Flag bare text between two adjacent sibling tags (via a real `<Tag ...>`
   regex, not a naive `>...<` scan — `.length > 0`'s `>` is not a tag
   boundary); a gap containing `(`/`)` is ternary/JS syntax joining two
   *different* branches, not shared text, and is excluded.

**Mutation-verified against both of the reviewer's named classes** (hand-planted,
confirmed FAIL, reverted, confirmed PASS again):
(a) `EmptyState.jsx`'s `{message}` → `{message || 'No hay nada que mostrar
todavia'}` — caught. (b) `LoadingState.jsx`'s `{message}` → bare text
`Lista vacia: anade un elemento` — caught.

**False-positive sweep against the real tree.** Before landing the fix,
the naive version flagged 4 real false positives: `App.jsx`'s `headerStyle()`
helper (a plain object-literal `return`, not JSX — fixed by step 1's
`looksLikeJsxReturn` filter) and `.length > 0 ? (...)`-shaped ternaries in
`DaySlot.jsx`/`RulesView.jsx`/`SummaryView.jsx` (the naive `>...<` scan
mistook `.length >` for a tag close — fixed by steps 4/5's tag-regex +
paren exclusion). Final run: 0 offenders across the real
`frontend/src/components/**/*.jsx` tree, including every legitimate
single-quoted CSS/role/state-key literal ('flex', 'Admin', 'week', etc.).

**Docs corrected** (mirrors the Library slice's F4/F5 pattern):
`specs/frontend_spa/design.md` §9 and `specs/frontend_spa/tasks.md` T62 both
said "double-quoted" — both now describe the real quote-agnostic +
bare-JSX-text guard.

### Test result

`npx vitest run` **301/301** (299→301: 2 new self-check cases —
rendering-position-literal detection, comparison-operand exclusion — added
to the 2 pre-existing cases in this file). `npx eslint .` clean (one
`no-unused-vars` fix on an unused regex-match capture). `npx prettier
--check .` clean. `./init.sh` fully green — **795 backend pytest**
(unchanged, no `backend/` file touched), ruff/mypy/prettier/eslint/vitest
all pass. `feature_list.json` untouched.

## T62 — Fix round 2 (adversarial mutation probe, 5 findings) — 2026-09-14

Scope: `frontend/tests/test_all_strings_from_messages.test.js` only. No
other `frontend_spa` section touched.

| Finding | Fix | File(s) |
|---|---|---|
| F1 (blocking, real gap) | Replaced the blanket `attr="..."` exclusion with `SAFE_ATTR_NAMES` (`type`, `className`, `id`, `key`, `htmlFor`, `name`, `href`, `src`, `data-testid`, `role`, `designation`, `value` — catalogued from every real attribute name in `frontend/src/components/**/*.jsx`, none of which currently carries letter-bearing text). `scanAttributeStrings` flags any other quoted, letter-bearing attribute value as a hardcoded prop-text pass-through. | test file |
| F2 (blocking, real gap) | Added `TEMPLATE_LITERAL` matching alongside `STRING_LITERAL` in the shared `findRenderPositionLiterals` helper; `hasStaticContent` strips `${...}` interpolations first so a pure-interpolation template (e.g. `` `${a}-${b}` ``, `RulesView.jsx:114`'s real usage) is never flagged, only one with a hardcoded text segment. | test file |
| F3 (real gap, fixed) | Added `collectConstInitializers` (maps every top-level `const NAME = <expr>;` in the file to its initializer text) and resolve it when `scanRegion` finds a bare `{name}` expression container matching a known const — the exact `WeekLabel.jsx`-shape mutation class. Scoped narrowly (exact bare-identifier match only, not ternary branches referencing an identifier) to avoid reintroducing the `headerStyle()`/`.length > 0` false-positive classes fix round 1 already fixed. | test file |
| F4 (mechanical) | Trimmed the 10-line file header to 3 lines, pointing at this section instead of reproducing the round-1 narrative. | test file |
| F5 (optional, fixed at low risk) | Narrowed the bare-text paren exclusion: a gap is now only excluded when it carries a ternary/arrow operator (`?`, `:`, `=>`) *alongside* a paren — real JS syntax like `) : (` or `.map((x) => (` (`DaySlot.jsx`'s real shape) — not any paren anywhere. `<p>Cantidad (unidades)</p>`-style prose with a parenthetical aside is no longer exempted. | test file |

Also updated `specs/frontend_spa/design.md` §9 and `specs/frontend_spa/tasks.md`
T62's wording to describe all 3 new detection paths (F1/F2/F3) and the F5
tightening.

### Mutation-kill confirmation (real tree, hand-planted/reverted, not just fixtures)

- **Original mutant (a)** — `EmptyState.jsx`'s `{message}` →
  `{message || 'No hay nada que mostrar todavia'}`: still caught. Reverted,
  confirmed byte-identical to backup.
- **Original mutant (b)** — `LoadingState.jsx`'s `{message}` → bare text:
  still caught. Reverted, confirmed byte-identical.
- **F1 mutant** — `ShoppingListView.jsx`'s
  `<EmptyState message={MESSAGES.SHOPPING_LIST_VIEW_EMPTY} />` →
  `<EmptyState message="Todavia no hay elementos en la lista de la compra." />`:
  caught. Reverted, confirmed byte-identical.
- **F2/F3 mutant (combined)** — `WeekLabel.jsx`'s
  `designationLabel`'s `MESSAGES.WEEK_LABEL_CURRENT` branch → `` `Semana actual` ``
  (a template literal AND the const-above-return shape at once): caught.
  Reverted, confirmed byte-identical.
- **F3 mutant (isolated, non-template)** — same branch →
  `'Semana actual'` (plain string): caught. Reverted, confirmed
  byte-identical.

All 4 backups diffed clean against the restored files after every plant/revert
cycle (`diff` — no output).

### Test result

`npx vitest run tests/test_all_strings_from_messages.test.js` **12/12**
(10→12: 8 new self-check cases — F1 detect + F1 allowlist negative, F2
detect + F2 pure-interpolation negative, F3 detect + F3 MESSAGES-only
negative, F5 detect + F5 ternary/map-gap negative). Full suite `npx vitest
run` **309/309, 47 files** (301→309). `npx eslint .` clean. `npx prettier
--check .` clean (one `--write` pass on this file, line-wrap only).
`./init.sh` fully green — **795 backend pytest** (unchanged, no `backend/`
file touched), ruff/mypy/prettier/eslint/vitest all pass. `feature_list.json`
untouched.

## T62 — Fix round 3 (braced-attribute copy, real gap) — 2026-09-14

Scope: `frontend/tests/test_all_strings_from_messages.test.js` only.

**Finding (blocking, real gap).** Round 2's `SAFE_ATTR_NAMES` allowlist only
ever ran against *quoted* (`attr="..."`) values via `scanAttributeStrings`.
`stripAttributeExpressions` deleted the entire contents of every `attr={...}`
braced value BEFORE anything scanned it, so a braced prop was invisible to
the guard — and since a conditional prop value can only ever be written with
braces, this is the more common real shape once any conditional logic is
involved. `<EmptyState message={...} />` / `<LoadingState message={...} />`
is the dominant copy-passing pattern in this tree (9 `EmptyState` call
sites, catalogued via `rg -n "\w+=\{" frontend/src/components -g "*.jsx"`,
370 hits).

**Catalogued every real braced-attribute shape first** (per the dispatch
brief) before changing detection logic: every non-member-expression braced
value in the real tree is either `style={{...}}`/`style={cond ? {...} :
undefined}` (object literal) or an `on*={...}` handler (arrow function/bare
callback identifier) — no custom prop anywhere carries an object or function
value. This grounded the exclusion rule instead of guessing.

**Fix.** `stripAttributeExpressions` now takes a `violations` array. Before
stripping each `attr={...}` span, it extracts the attribute name (regex
against the accumulated output right before `={`) and the inner text, and —
unless the name is in `SAFE_ATTR_NAMES`, is `style`, or matches
`EVENT_HANDLER_ATTR` (`/^on[A-Z]/`), or the inner text (trimmed) matches
`NON_COPY_ATTR_VALUE` (`^\{` object literal, or an arrow/`function` body) —
calls `findRenderPositionLiterals(inner, violations)`, the same helper
already used for JSX-children `{...}` spans. A bare string/template literal
as the whole value, or one in a ternary/fallback branch, matches
`RENDER_POSITION_SUFFIX`'s `^` (start-of-expression) or `?`/`:`/`||`/`??`
alternatives exactly as an ordinary rendering-position span does — no new
detection path was needed, only removing the blanket pre-strip that hid the
braced form from the existing one. The tag itself still comes out of
`stripAttributeExpressions` with `attr=` and no braces, so `TAG`/
`splitTopLevelBraces` downstream stay unaffected (tag atomicity preserved).

**Why the name+shape exclusion, not just a shape check.** The dispatch
brief's own pitfall: `style={{ color: tokens.color.ink2 }}` structurally
resembles a ternary (`:` inside) and its values (`'flex'`, hex colors) are
not text. Excluding by name (`style`, `on*`) first means the shape check
(`NON_COPY_ATTR_VALUE`) only has to guard the case a non-excluded attribute
name is directly assigned an object/function — not currently present in the
tree, but a defensive backstop matching the brief's requested distinction.

### Self-check test cases added

Three new cases in the `describe` block: a bare braced string
(`message={'...'}`), a braced ternary with one hardcoded branch
(`message={cond ? '...' : MESSAGES.X}`), and a negative case proving a
`style={{...}}` object literal + an `onClick={() => onSave('x')}` arrow body
are both still ignored even though each contains a quoted string
internally.

### Mutation-kill confirmation (real tree, hand-planted/reverted)

Both exact mutants named by the reviewer, on `ShoppingListView.jsx`'s
`<EmptyState message={MESSAGES.SHOPPING_LIST_VIEW_EMPTY} />` (file-copy
backup before each, `diff` after revert confirmed byte-identical):

- → `message={'Todavia no hay elementos en la lista de la compra.'}` —
  **caught** (`strayLiterals` reported the exact quoted string).
- → `message={items.length ? 'Sin elementos pendientes' :
  MESSAGES.SHOPPING_LIST_VIEW_EMPTY}` — **caught** (reported
  `'Sin elementos pendientes'`).

All 5 previously-fixed mutants re-verified still caught (each hand-planted
individually on a fresh copy of its file, run, reverted, `diff`-confirmed
byte-identical before the next):

- `EmptyState.jsx`'s `{message}` → `{message || 'No hay nada que mostrar
  todavia'}` (round 1, original mutant a) — caught.
- `LoadingState.jsx`'s `{message}` → bare text `Lista vacia: anade un
  elemento` (round 1, original mutant b) — caught.
- `ShoppingListView.jsx`'s `EmptyState` → the quoted-string form (round 2,
  F1 mutant) — caught.
- `WeekLabel.jsx`'s `designationLabel`'s `MESSAGES.WEEK_LABEL_CURRENT`
  branch → `` `Semana actual` `` (round 2, F2/F3 combined mutant) — caught.
- Same branch → `'Semana actual'` (round 2, F3 isolated mutant) — caught.

**Zero-false-positive sweep.** Full `npx vitest run` against the real
`frontend/src/components/**/*.jsx` tree (no mutants applied): 0 offenders.

**Mechanical.** Trimmed `scanRegion`'s 4-line header comment to 3 lines
(ceiling, `docs/conventions.md`).

### Test result

`npx vitest run` **312/312** (309→312: 3 new self-check cases — braced
bare-string detect, braced ternary-branch detect, style-object +
event-handler negative). `npx eslint .` clean. `npx prettier --check .`
clean (one `--write` pass, line-wrap only on the new test cases).
`./init.sh` fully green — **795 backend pytest** (unchanged, no `backend/`
file touched), ruff/mypy/prettier/eslint/vitest all pass. `feature_list.json`
untouched.

## Closing cleanup (2026-09-14) — feature complete

Two mechanical items to close out T1–T63: the `stripAttributeExpressions`
header comment above (4 lines) trimmed to 3, pointing at this section
instead of restating the reasoning. `specs/frontend_spa/tasks.md` T13
ticked `[x]` — `es-ES.js` now has 145 keys across every section, and this
guard (verified sound across 4 review passes: fix rounds 1–3 plus the
zero-false-positive sweep above) is the proof no component sources copy
outside it.

Every `T<n>` in `specs/frontend_spa/tasks.md` is now `[x]`. `npx vitest run`
312/312. `./init.sh` fully green. Feature 20 `frontend_spa` is genuinely,
fully implementation-complete. `feature_list.json` untouched.

## Reopen 2026-09-14 — RulesView consumes recipeName from the API directly

Backend (feature 27) now resolves and returns a pin rule's `recipeName` on
`GET /v1/rules` (was documented, never implemented — see
`progress/impl_rest_api_persistence_and_services.md`'s matching reopen
entry). The client-side workaround this feature's "Rules view (T32–T34)"
section built to compensate — `RulesView.jsx`'s local `recipeName()`
cross-referencing `useLibraryPicker`'s `allRecipes` — is now redundant for
that purpose and removed. `RulesView.jsx` reads `rule.recipeName` straight
off each pin.

**`useLibraryPicker.js` untouched** — `allRecipes` stays exported, per
instruction not to remove it. Note for the record: a grep across
`frontend/src` found no other current consumer of `.allRecipes` outside
`useLibraryPicker.js` itself (`LibraryRecipePicker.jsx` only destructures
the filtered `recipes`, `useLibrary.js` doesn't expose it) — the "still
used by `RecipeAuthoringForm.jsx`'s picker embeds" premise didn't hold in
the code as it stands today; left as-is since removing it wasn't asked for
and it's harmless dead surface.

`RulesView.test.jsx`: the two tests that exercised the old cross-reference
(`'renders a pin rule resolving its recipe name from the picker'`, the
finding-6 filter-immunity test) now seed `recipeName` directly on the pin
fixture instead of `picker.allRecipes`, asserting the same composed row
label. `useRules.test.js`'s grouping test gained a `recipeName` assertion
proving the field passes through the hook unchanged.

Mutation check: reverted `rule.recipeName` back to `rule.recipeId` in
`RulesView.jsx` — both affected tests failed as expected; reverted back,
suite green.

`npx vitest run` **312/312** (unchanged count — 2 tests rewritten in place,
1 assertion added, no new file). `npx eslint .` clean. Quality gates
(798 backend, ruff/mypy/prettier/eslint/vitest) all green; `./init.sh` §4
guardrails report the expected multi-`in_progress` state from the leader's
reopen scope (16/20/27 at once), not a code issue. `feature_list.json`
untouched — still `in_progress`, per the leader's reopen scope.

## Reopen 2026-09-16 — Visual design system, Tier A foundation tokens (T64–T71) — DONE

Scope: only `specs/frontend_spa/tasks.md`'s reopened "Tier A — foundation
tokens" section (T64–T71). Tiers B–F (T72–T94) not touched, per explicit
dispatch scope; `RecipeAuthoringForm.jsx`'s AI-tab stub untouched (feature
28's territory, design.md §10.6).

### Traceability

| Task | File(s) | `R<n>` |
|---|---|---|
| T64 | `frontend/src/tokens/fontFamily.js` | No `R<n>` |
| T65 | `frontend/src/assets/fonts/*.woff2` (5 files), `frontend/src/fonts.js` | No `R<n>` |
| T66 | `frontend/src/main.jsx` | No `R<n>` |
| T67 | `frontend/src/tokens/borderRadius.js` | No `R<n>` |
| T68 | `frontend/src/tokens/shadow.js` | No `R<n>` |
| T69 | `frontend/src/tokens/index.js` | No `R<n>` |
| T70 | `frontend/index.html` | No `R<n>` |
| T71 | `frontend/src/components/App.jsx` (`rootShellStyle()`) | No `R<n>` (extends T42/T58) |

Design.md §10.0 is explicit: this reopen adds no new `FR-*`/`R<n>` — it
elaborates feature 20's own already-approved acceptance criterion 3. No new
test files: pure token modules (`fontFamily.js`, `borderRadius.js`,
`shadow.js`) follow the established, untested pattern of `colors.js`/
`spacing.js`/`typography.js`/`breakpoints.js` (none of the four has a test
file either), and `tasks.md`'s own Tier A task list — unlike the paired
implementation/test tasks in "Shared infrastructure" (T1/T2, T3/T4, ...) —
names no test task for T64–T71.

### Font assets — real files, not placeholders

The 5 `.woff2` files are genuine, verified font binaries (`file(1)`
confirms "Web Open Font Format (Version 2)" for each), fetched directly
from `fonts.gstatic.com`'s "latin" static subset (covers the full Spanish
accented-character range, U+0000-00FF) — a build-time asset fetch, not the
runtime CDN `<link>` design.md §10.1/§10.7 rejects:

- Baloo 2 600: `.../s/baloo2/v23/wXK0E3kTposypRydzVT08TS3JnAmtdjEyppo_lc.woff2`
- Baloo 2 700: `.../s/baloo2/v23/wXK0E3kTposypRydzVT08TS3JnAmtdj9yppo_lc.woff2`
- Nunito 400: `.../s/nunito/v32/XRXI3I6Li01BKofiOc5wtlZ2di8HDLshdTQ3jw.woff2`
- Nunito 600: `.../s/nunito/v32/XRXI3I6Li01BKofiOc5wtlZ2di8HDGUmdTQ3jw.woff2`
- DM Mono 400: `.../s/dmmono/v16/aFTU7PB1QTsUX8KYthqQBA.woff2`

Network egress happened to be available in this sandbox run; had it not
been, this task would have needed empty placeholder files with the
limitation flagged, per the leader's dispatch brief. It was not needed.

### Design deviation (disclosed)

`fonts.js` resolves each asset via `new URL('./assets/fonts/....woff2',
import.meta.url)` instead of design.md §10.1's literal
`/src/assets/fonts/....woff2` string. The literal path only resolves in
Vite's dev server (which serves `/src` directly); after `npx vite build`
it 404s, since Vite hashes and relocates assets into `dist/assets/`.
`new URL(..., import.meta.url)` is Vite's documented way to reference a
static asset from JS and is what makes the build emit and hash the file at
all — verified: `npx vite build` output lists all 5 hashed `.woff2` files
under `dist/assets/`. Not an architecture decision (still a plain top-level
JS module, no new dependency, no CSS surface) — a correctness fix to the
pseudocode, disclosed rather than silently substituted.

Also added `FontFace`/`URL` to `frontend/eslint.config.js`'s browser
globals (both previously absent, would otherwise trip `no-undef`).

### T71 — App.jsx root wrapper

The current `App.jsx` has two structurally separate root `<div>`s (Admin
shell, User shell), not literally one universal wrapper — the
`loading`/`anonymous`/`passwordResetPending` branches return `LoadingState`/
`LoginView`/`SetPasswordView` directly with no wrapping div at all.
Restructuring those three branches into a shared wrapper is Tier C's job
(T79/T80 style `LoginView`/`SetPasswordView` card containers), not this
task's "extends T42/T58" scope, so left untouched. Applied the foundation
(`fontFamily`, `background`, `color`, `minHeight`) to both existing
wrappers via one shared `rootShellStyle()` helper instead of duplicating
the object literal twice.

### Test result

`npx vitest run` — **312/312 passed, 47 files** (unchanged — no new test
files, per the "no test task named" reasoning above). `npx eslint .`
clean. `npx prettier --check .` clean (one `--write` on `index.html`,
Prettier's own hex-case normalization). `npx vite build` succeeds, 5 hashed
font assets emitted. `./init.sh` fully green: 808 backend (unchanged, this
reopen touches no `backend/` file), ruff/mypy/prettier/eslint/vitest all
pass. `feature_list.json` untouched — still `in_progress`. `tasks.md`
T64–T71 ticked. Reviewer next; Tiers B–F remain for later implementer runs.

## Reopen 2026-09-16 — Tier B, shared primitives (T72–T78)

Scope: only `tasks.md`'s Tier B (T72–T78) — `EmptyState.jsx`,
`LoadingState.jsx`, `ConfirmDialog.jsx`, `ConnectionLostBanner.jsx`,
`WeekLabel.jsx`, `WeekSwitcher.jsx`, `App.jsx`'s nav shell (header +
nav strip, not its root wrapper — Tier A's job, closed). No Tier C–F
screen component touched.

### Traceability

| Task | File(s) | `R<n>` |
|---|---|---|
| T72 | `EmptyState.jsx` (dashed-border card), `LoadingState.jsx` (shimmer bar) + new `hooks/useLoadingShimmer.js` | R19, R20 |
| T73 | `ConfirmDialog.jsx` (backdrop + card + heading title) | R18 |
| T74 | `ConnectionLostBanner.jsx` (honey/honeySoft palette + radius.sm) | no new `R<n>` (consumes FR-RT-03) |
| T75 | `WeekLabel.jsx` (two-tier: heading designation / label range) | R16, R21 |
| T76 | `WeekSwitcher.jsx` (arrow-flanked, replaces the two labeled buttons) | R2, R3 |
| T77 | `App.jsx` (`headerStyle`, `navButtonStyle`, new `logoutButtonStyle`) | no new `R<n>` (R30/R31/R32 already covered) |
| T78 | `tests/components/LoadingState.test.jsx`, `ConfirmDialog.test.jsx`, `WeekLabel.test.jsx` (extended); `tests/hooks/useLoadingShimmer.test.js` (new) | R16, R18, R19, R20, R21 |

`FR-*` reachability: unchanged from prior sections — this tier adds no new
`R<n>` beyond what T72–T77's table already cites (all already reached in
earlier `impl_frontend_spa.md` sections' `covers` accounting).

### Design decisions (disclosed)

**T72 — shimmer needs a hook, not component state.** The task's "driven by
a state tick in the existing hook" has no literal referent — `LoadingState`
never had a hook. Per `docs/conventions.md`'s hook/component split (state
lives in a hook, component stays a pure function), added
`frontend/src/hooks/useLoadingShimmer.js`: a `useState`/`useEffect`
`globalThis.setInterval` toggling a boolean every 600ms (`globalThis.*`,
not the bare global, matching `realtime/pollingEngine.js`'s existing
convention so `eslint`'s browser-globals list needs no new entry). The
shimmer bar is a `data-testid="loading-shimmer"` `<div>` swapping
`tokens.color.surface2`/`surface` — no CSS `@keyframes` (no-stylesheet
rule).

**T73 — backdrop alpha.** `tokens.color.ink` has no alpha channel; used the
same literal-rgba-derived-from-ink technique `tokens/shadow.js` already
established (`rgba(40, 51, 31, 0.45)`, 3-line comment pointing at the
precedent) rather than inventing a new token axis for one call site.

**T76 — WeekSwitcher restructured, not just recolored.** "Circular arrow
buttons... fixed square dimensions" cannot hold two lines of text (a
designation heading plus a date-range label), which rules out simply
rounding the two existing label-buttons' corners. Read the prototype's own
markup for this exact control
(`prototypes/wireframe/Sobremesa.dc.html:130-133`): two 30×30 icon buttons
(SVG chevrons) flanking one two-line week label — mined for the layout
*idiom*, not ported. Reimplemented as two `tokens.radius.pill`, fixed
32×32 arrow buttons (plain `‹`/`›` glyphs — punctuation only, so the
`test_all_strings_from_messages.test.js` mechanical scan's own
`HAS_CONTENT` check does not flag them, and no `aria-label` was added, per
`FR-UX-07`/G-62's accessibility-scope exclusion) flanking a single active
`WeekLabel`. `onSwitch('current'|'next')`'s signature is unchanged — R2/R3
behaviour is identical, only the affordance is redrawn. The muted arrow
(`tokens.color.ink3`) is the one already pointing at the displayed week (a
no-op click), mirroring the prototype's `prevCol`/`nextCol` logic.
**Known gap, not fixed here:** `WeekSwitcher.jsx` had no dedicated test
file before this reopen (only indirect coverage via
`WeekPlannerView.test.jsx`'s button-count invariant, unaffected by this
restructure since the button count is still 2). `tasks.md` T78 explicitly
scopes this run to "no new behavioural assertions", so no new test file was
added — flagged for the reviewer/owner rather than silently expanded.

**T75 collateral fix (not a Tier C/D touch):** the two-tier `WeekLabel`
restructure turns its old single joined-string render (`"<designation> ·
<range>"`) into two separate text nodes, which breaks 2 pre-existing
assertions that queried the old combined string:
`WeekLabel.test.jsx` (in scope, updated) and
`ShoppingListView.test.jsx`'s one resync-scope test (out of Tier B scope,
but a mechanical selector fix only — `ShoppingListView.jsx` itself
untouched, no shopping-list business logic touched).

### Test result

`npx vitest run` — **317/317 passed, 49 files** (312→317: 3 new cases in
extended files + 2 in the new `useLoadingShimmer.test.js` file). `npx
eslint .` clean, `npx prettier --check .` clean, `npx vite build` succeeds
(6 chunks incl. fonts, no import-graph break). `./init.sh` fully green: 808
backend (unchanged, no `backend/` file touched), ruff/mypy/prettier/eslint/
vitest all pass. `feature_list.json` untouched — still `in_progress`.
`tasks.md` T72–T78 ticked. Reviewer next; Tiers C–F (T79–T94) remain for
later implementer runs.

## Tier B — Fix round (5 reviewer findings) — 2026-09-16

Scope: the 5 findings on T72–T78 above. No other section touched.

| Finding | Fix | File(s) |
|---|---|---|
| 1 (blocking, no test file) | New `WeekSwitcher.test.jsx`: back/forward arrows call `onSwitch` with distinct args; `designation="next"` renders the next week's `WeekLabel` (designation + its own range), asserting the current week's designation/range are absent. | `tests/components/WeekSwitcher.test.jsx` (new) |
| 2 (blocking, FR-UX-06/G-57 regression) | Added a `title` on each arrow button naming the target week's designation + Monday–Sunday range (`switchTitle()`, built from `MESSAGES.WEEK_LABEL_CURRENT`/`NEXT` + `formatDate`), covering the week not currently displayed. Confirmed `title` is not one of `test_no_extra_accessibility.test.js`'s banned patterns before adding it. | `WeekSwitcher.jsx` |
| 3 (required, stray colour literal) | Added `tokens.color.backdrop` (`ink` at low alpha, same derivation `shadow.js` already uses) to `colors.js`; `ConfirmDialog.jsx` now references it instead of the inline `rgba(...)`. | `tokens/colors.js`, `ConfirmDialog.jsx` |
| 4 (mechanical, comment ceiling) | Trimmed the 4-line comment to 1 line, same claim. | `tests/components/ShoppingListView.test.jsx` |
| 5 (minor, dropped assertion) | Restored the date-range assertion alongside the designation assertion in the "next" case. | `tests/components/WeekLabel.test.jsx` |

### Mutation-kill confirmation (hand-verified, both named mutants)

Backed up `WeekSwitcher.jsx` by file copy (not `git checkout`, per
mutation-testing safety convention) before applying either mutant.

1. **`onSwitch('current')` → `onSwitch('next')`** on the back-arrow button:
   new test's first assertion failed (`expected … called with … 'current' …
   received … 'next'`). Reverted from backup; `git diff --stat` unchanged
   (53 lines, matching pre-mutation).
2. **`liveWeeks[designation]` → `liveWeeks.current`**: with `designation="next"`,
   the rendered `WeekLabel` showed `"Semana próxima"` (designation prop
   passed through unmutated) paired with the *current* week's range —
   new test's `getByText(nextRange)` failed to find it. Exactly the
   `FR-UX-06`/`G-57` hazard. Reverted from backup; `git diff --stat`
   unchanged.

### Test result

`npx vitest run` — **320/320 passed, 51 files** (317 → 320: 3 new
`WeekSwitcher.test.jsx` cases). `npx eslint .` clean, `npx prettier --check .`
clean. `./init.sh` fully green — **808 backend pytest** (unchanged, no
`backend/` file touched), ruff/mypy/prettier/eslint/vitest all pass.
`feature_list.json` untouched — still `in_progress`. Tiers C–F (T79–T94)
remain for later implementer runs.

## Tier C — auth screens (T79–T80a) — 2026-09-16

Scope: `LoginView.jsx`, `SetPasswordView.jsx` only (design.md §10.6,
tasks.md T79/T80/T80a). No prop, handler, or validation logic touched —
pure restyle, same `useLoginForm.js`/`useSetPasswordForm.js` contracts.

Both views gained a page wrapper (`tokens.color.paper` background,
`tokens.fontFamily.body`, centred) around a card (`tokens.color.surface`,
1px `tokens.color.line` border, `tokens.radius.md`, `tokens.shadow.md`,
max-width 420px) — mined from the prototype's card idiom
(`Sobremesa.dc.html:67-113`). Per-file additions, cited where they extend
beyond the tasks' literal "card + input/button" wording, per the
leader's dispatch brief comparing against the prototype:

- **Monogram badge**: a decorative, non-interactive 58×58 `tokens.radius.md`
  square in `tokens.color.terra`, showing `MESSAGES.APP_TITLE.charAt(0)` —
  derives its letter from the existing `APP_TITLE` key rather than adding a
  new hardcoded brand string (verified: `test_all_strings_from_messages.
  test.js` and `test_no_extra_accessibility.test.js` both pass unchanged,
  since it is a JS expression, not a literal, and adds no ARIA/role/tabIndex).
- **Font tokens**: `tokens.fontFamily.heading` (title), `.label` (field
  labels, uppercase, mined from the prototype's `DM Mono` label style), `.body`
  (inputs, buttons) — closing "no font tokens applied".
- **Inputs**: `tokens.color.line2` border, `tokens.color.surface2`
  background, `tokens.radius.sm`, `tokens.space.sm` padding.
- **Submit button**: `tokens.color.terra` background, `tokens.radius.sm`,
  `tokens.shadow.sm`, full width.
- **Login-only dashed footer** (`Sobremesa.dc.html:84`): new
  `MESSAGES.LOGIN_NO_REGISTRATION_NOTE` key ("Sin registro público. Las
  cuentas las crea el administrador."), rendered under a `1px dashed
  tokens.color.line` top border — reinforces R29 (no self-registration
  control), no new `R<n>` (design.md §10.0, a copy/styling completion, not
  new behaviour).
- **`SetPasswordView`'s mismatch treatment**: reused the honey/honeySoft
  warning idiom `ConnectionLostBanner.jsx` (T74) already established,
  instead of inventing a new error colour outside the 18-token palette.
- **Cancel button**: ghost-styled (`transparent` background, `tokens.color.
  ink3` text, no border) instead of a bare default button.

The generic `error` prop's paragraph (`{ color: tokens.color.ink }`, no
padding) was left exactly as before in both views — that convention is
identical across every other view in this feature (`AdminAccountsView`,
`LibraryView`, `WeekPlannerView`, `SummaryView`, `ShoppingListView`,
`RulesView`) and was not named as a Tier C gap; changing it here would be
an uninvited cross-cutting change.

### Traceability

| Task | Covers | Test proof |
|---|---|---|
| T79 | R24, R25, R29 | `LoginView.test.jsx` (5 cases, unmodified selectors — username/password/submit render, password `type="password"`, error renders, no registration control) |
| T80 | R26, R27, R28 | `SetPasswordView.test.jsx` (6 cases, unmodified selectors — renders only while pending, fields + Cancelar render, both fields masked, mismatch copy conditional, error renders, submit disabled while `canSubmit` is false) |
| T80a | (test-only task) | Both test files ran unmodified against the new markup and passed — the implicit `<label>` wrapping still associates each `<span>` + `<input>` pair, so no selector needed updating |

No new `R<n>` (design.md §10.0). Every `FR-AUTH-*` id these two views
render (`FR-AUTH-02`, `-03`, `-04`, `-10`) was already covered by R24–R29
before this run; this pass changes no behaviour those tests assert.

### Test result

`npx vitest run` **320/320** (unchanged — no test case added or removed,
matching Tier B's "no new behavioural assertions" convention for a
styling-only pass). `npx eslint .` / `npx prettier --check .` clean, `npx
vite build` succeeds (69 modules, 6 asset chunks). `./init.sh` fully green:
**808 backend** (untouched), ruff/mypy/prettier/eslint/vitest. `tasks.md`
T79/T80/T80a ticked. `feature_list.json` untouched — still `in_progress`.
Reviewer next; Tiers D–F (T81–T94) remain for later implementer runs.

## Tier C — fix round 1 (3 reviewer findings) — 2026-09-16

`onClick={submit}`/`onClick={cancel}` were already present in both files on
disk (confirmed via `git diff` against the pre-Tier-C commit) — the wiring
itself needed no code change, only regression coverage that would have
caught it going missing.

| Finding | Fix | File(s) |
|---|---|---|
| F1 (blocking) | Added a click-invokes-`submit` test. Hand-verified: deleting `onClick={submit}` failed the new test; restored, `git diff` shows only the restored line. | `LoginView.test.jsx` |
| F2 (blocking) | Added a click-invokes-`cancel` test (Cancelar) plus a click-invokes-`submit` test for the same screen's submit button (was wired but untested, same class). Hand-verified the `cancel` mutant the same way. | `SetPasswordView.test.jsx` |
| F3 (mechanical) | Trimmed both 4-line file headers back to 3, folding the §10.6 pointer onto the existing §5a line. | `LoginView.jsx`, `SetPasswordView.jsx` |

### Test result

`npx vitest run` — **323/323 passed, 50 files** (320 → 323: 3 new click
regression tests). `./init.sh` fully green — **808 backend pytest**
(unchanged), ruff/mypy/prettier/eslint/vitest all pass.

## Tier D — planning screens (T81–T84) — 2026-09-16

Scope: `WeekPlannerView.jsx`, `DaySlot.jsx`, `MealCard.jsx`,
`RecipeDetailView.jsx` only. No handler/prop signature changed on any of
the four files — verified by re-reading each diff for `onPromote`/
`onClear`/`onOpenDetail`/`onAddCandidate` call sites after the restyle
(the reopen's own named regression class, from Tier B's `WeekSwitcher` bug).

### Traceability

| Task | File(s) | Covers | Test proof |
|---|---|---|---|
| T81 | `DaySlot.jsx`, `WeekPlannerView.jsx` | R1, R19, R20 | `WeekPlannerView.test.jsx` (8 cases, unmodified) — 7×2 grid shape, empty-slot/loading text, promote/clear wiring all still assert against the restyled markup |
| T82 (Partial) | `MealCard.jsx` | R4, R5 | Same file — click-openDetail-with-candidate and clear-not-promote assertions pass unmodified; IA badge not implemented, see gap below |
| T83 | `RecipeDetailView.jsx` | R4, R5 | `RecipeDetailView.test.jsx` (4 cases, unmodified) — ingredient/tool/step/servings/time text nodes preserved verbatim, close-click wiring intact |
| T84 | `frontend/tests/components/*`, `test_all_strings_from_messages.test.js` | (test-only) | See below |

No new `R<n>` (design.md §10.0, same as every prior tier this reopen).

### T82 gap: no "IA" badge (disclosed, not invented around)

Checked three layers before concluding this is a real gap, not an oversight:

1. `docs/rest_api_contract.md` §3.1/3.2 — a candidate's wire shape carries
   only `author: {userId, displayName}`, always a human.
2. `backend/core/src/planner_core/domain/candidate.py` —
   `Candidate.author: str`, resolved via `resolve_author()` to a known user
   id or `UNKNOWN_USER_ID`, never an AI sentinel.
3. `frontend/src/hooks/useWeekPlanner.js` / `buildWeekViewModel` — no
   `source`/`isAI` field passed through anywhere.

The prototype's own model sets `meal.author = 'IA'` for generated content
(`Sobremesa.dc.html:966`) — that idiom has no real-system equivalent to
mine. Adding one needs either a backend data-model field (out of a
frontend-only tier, and an architecture/data-model call not an
implementer's to make) or a fabricated client heuristic (excluded by hard
rule). Left undone; `tasks.md` T82 is `[x] (Partial)`.

### Deliberately not added

- **Backdrop-click-to-close** on `RecipeDetailView`'s new sheet (the
  prototype's own `onClick={closeRecipe}` on the overlay): a new
  interaction path, not a style, and outside "styling completion" scope.
  The close button remains the only way to dismiss it.
- **Icon-only** promote/clear/close buttons: kept the existing `MESSAGES`
  text alongside each new SVG icon so every existing text-based test
  assertion (and the handler it proves) needed zero changes.

### Mechanical guard fix (T84)

`test_all_strings_from_messages.test.js`'s R15 scan flagged the new inline
`<svg>` icons' geometry attributes (`width`, `height`, `viewBox`, `fill`,
`stroke`, `strokeWidth`, `strokeLinecap`, `strokeLinejoin`, `d`) as
hardcoded prop text — a real false positive (these are the first `<svg>`
elements anywhere in `frontend/src/components/`). Added all 9 to
`SAFE_ATTR_NAMES`; no scan-logic change.

### Test result

`npx vitest run` **323/323** (unchanged count — `WeekPlannerView.test.jsx`
and `RecipeDetailView.test.jsx` both passed **unmodified** against the
restyled markup, matching T80a's outcome; no `DaySlot.test.jsx`/
`MealCard.test.jsx` exist, same pre-existing gap as `WeekSwitcher.jsx`'s,
Tier B). `npx eslint .` clean, `npx prettier --check .` clean (one
`--write`, `RecipeDetailView.jsx`), `npx vite build` succeeds. `./init.sh`
fully green: 808 backend (untouched), ruff/mypy/prettier/eslint/vitest.
`tasks.md` T81/T83/T84 ticked, T82 ticked `(Partial)`. `feature_list.json`
untouched — still `in_progress`. Reviewer next; Tiers E–F (T85–T94) remain
for later implementer runs.

## Tier D — fix round 1 (5 reviewer findings) — 2026-09-16

Scope: the 5 findings on T81–T84 above (test-coverage gaps plus one doc
correction). No other section touched; no handler/prop signature changed.

| Finding | Fix | File(s) |
|---|---|---|
| 1 (surviving mutant) | New `DaySlot.test.jsx` test clicks the promote control, asserts `onPromote` called with `(day, slot, candidateId)`. | `DaySlot.test.jsx` (new) |
| 2 (surviving mutant) | New `WeekPlannerView.test.jsx` test asserts all 7 `DAY_LABELS` entries render distinctly. | `WeekPlannerView.test.jsx` |
| 3 (real coverage gap, T81's new logic) | New `DaySlot.test.jsx` covers all 3 `dayStatus()` branches plus the definitive-over-candidates precedence case. | `DaySlot.test.jsx` (new) |
| 4 (surviving mutant) | New `RecipeDetailView.test.jsx` test clicks close in the error (no-recipe) branch, asserts `onClose` fires. | `RecipeDetailView.test.jsx` |
| 5 (doc inaccuracy) | T84's note corrected: `dayStatus()` + 3 new message keys were real new behaviour, not covered by "no new behavioural assertions"; now records the fix round's added coverage. | `specs/frontend_spa/tasks.md` |

### Mutation-kill confirmation (hand-applied, one at a time, each reverted after)

1. `MealCard.jsx` promote button: `onClick={onPromote}` → `onClick={onClear}`.
   `DaySlot.test.jsx`'s promote test failed (`expected … called with […] Number
   of calls: 0`). Reverted.
2. `WeekPlannerView.jsx`: `day={day.day}` → `day={1}` (hardcoded).
   `WeekPlannerView.test.jsx`'s day-indexing test failed (`getByText` found
   multiple elements for day 1's label, none for the others). Reverted.
3. `DaySlot.jsx`'s `dayStatus()`: swapped the candidates/definitive check
   order. Both the definitive-branch test and the precedence test failed.
   Reverted.
4. `RecipeDetailView.jsx`'s error branch: `onClose={onClose}` →
   `onClose={() => {}}`. The new error-branch close test failed (`expected …
   called 1 times, but got 0 times`). Reverted.

`git diff` confirmed each of the 4 source files identical to before the
hand-verify cycle (edit + exact revert, no residual change).

### Test result

`npx vitest run` — **330/330 passed, 53 files** (323 → 330: new
`DaySlot.test.jsx` (5 cases — empty/candidates/definitive/precedence/promote),
1 new `WeekPlannerView.test.jsx` day-indexing case, 1 new
`RecipeDetailView.test.jsx` error-close case). `./init.sh` fully green:
**808 backend pytest**
(unchanged), ruff/mypy/prettier/eslint/vitest all pass. `feature_list.json`
untouched — still `in_progress`.

## Tier E — library (T85–T88) — 2026-09-16

Scope: only `specs/frontend_spa/tasks.md`'s Tier E section (T85–T88,
`design.md` §10.6) — `LibraryView.jsx`, `LibraryRecipePicker.jsx`,
`LibraryFilters.jsx`, `RecipeAuthoringForm.jsx` (non-AI parts only). Built on
the reviewer-approved Tiers A–D. No other component touched.

### Traceability

| Task | File(s) | `R<n>` |
|---|---|---|
| T85 (Partial) | `LibraryView.jsx`, `LibraryRecipePicker.jsx`, `domain/labels.js` (+`CATEGORY_COLORS`) | R9, R10, R11, R12 (styling completion, partial — see gap below) |
| T86 | `LibraryFilters.jsx` | R11, R13, R14 (styling completion) |
| T87 | `RecipeAuthoringForm.jsx` | R6, R7, R8 (styling completion) |
| T88 | `tests/components/LibraryView.test.jsx`, `LibraryRecipePicker.test.jsx` (unmodified, passed as-is), `RecipeAuthoringForm.test.jsx` | same `R<n>` as above, plus the T22 stub-regression guard |

`FR-*` reachability (this slice): `FR-LIB-01` (R9), `FR-LIB-02` (R10),
`FR-LIB-04` (R11, R12, R13, R14), `FR-CAND-02` (R6), `FR-CAND-03` (R7, R8) —
all already reached by R6–R14 per `requirements.md`'s existing coverage
table (270-274); this reopen adds no new `R<n>` (design.md §10.0).

## Tier E — Fix round 1 (4 reviewer findings) — 2026-09-16

Scope: the 4 findings on T85–T88 above. No other section touched.

| Finding | Fix | File(s) |
|---|---|---|
| 1 (blocking, surviving mutant) | Edit-button test now targets the second card (`[1]` → `RECIPE_B`), matching the sibling remove-button test's pattern. | `LibraryView.test.jsx` |
| 2 (blocking, surviving mutant) | Select test converted to a second-card assertion (`[1]` → `'r-2'`). | `LibraryRecipePicker.test.jsx` |
| 3 (blocking, test gap) | New test: `selectedRecipeId: 'r-2'` renders `LIBRARY_PICKER_SELECTED` once and `LIBRARY_PICKER_SELECT` on the other card. | `LibraryRecipePicker.test.jsx` |
| 4 (mechanical, comment ceiling) | Trimmed 3 over-length banners to ≤3 lines, pointing at this section; also corrected `labels.js`'s `CATEGORY_COLORS` comment wording (6 categories, 5 accent tokens + `eggs`'s neutral `ink2`, not "5 solid accent tokens"). | `LibraryView.jsx`, `RecipeAuthoringForm.jsx`, `domain/labels.js` |

### Mutation-kill confirmation (hand-applied, one at a time, each reverted after)

1. `LibraryView.jsx`'s edit button: `openEdit(recipe)` → `openEdit(recipes[0])`. Corrected test failed (expected `RECIPE_B`, got `RECIPE_A`). Reverted.
2. `LibraryRecipePicker.jsx`'s select button: `onSelect(recipe.id)` → `onSelect(recipes[0].id)`. Corrected test failed (expected `'r-2'`, got `'r-1'`). Reverted.
3. `LibraryRecipePicker.jsx`: `isSelected = recipe.id === selectedRecipeId` → `isSelected = false`. New test failed (`LIBRARY_PICKER_SELECTED` not found). Reverted.

All three `git diff`-confirmed byte-identical to pre-mutant state after revert.

### Test result

`npx vitest run` — **336/336 passed, 51 files** (335 → 336: 1 new
selected-state test). `./init.sh` fully green: **808 backend pytest**
(unchanged), ruff/mypy/prettier/eslint/vitest all pass.

### Real gap found, disclosed not faked (T85, same wall as T82)

The prototype's library card (`Sobremesa.dc.html:234`) has an `r.isAI`
badge. No equivalent exists in the real system: `Recipe`
(`backend/core/src/planner_core/domain/recipe.py`) carries no origin field,
and neither `docs/data_model.md` nor `docs/rest_api_contract.md` persists
one. Implementing it would mean inventing a data-model field — an
architecture decision out of this run's authority. Left undone; `tasks.md`
T85 marked `[x] (Partial)`, same convention as T82.

### Design decisions (disclosed)

1. **`CATEGORY_COLORS`** (new, `domain/labels.js`): a decorative-only
   category-dot colour per `Recipe.category`, mined from the prototype's
   `r.catColor`. Only 5 non-neutral accent tokens exist in the 18-colour
   palette (`terra`, `terraDeep`, `olive`, `aub`, `honey`) for 6 categories —
   `eggs` reuses the neutral `ink2`. Arbitrary assignment, no domain
   meaning, stored as token *key names* (not resolved colours) so
   `domain/labels.js` stays free of a `tokens` dependency.
2. **Icon-with-text, not icon-only** (`LibraryView.jsx`'s edit/remove
   buttons): same choice T82 made for `MealCard.jsx` — keeps every existing
   `MESSAGES.LIBRARY_VIEW_EDIT`/`_REMOVE` text-based assertion valid with no
   test change needed, and no accessibility surface added (R22 guard).
3. **`RecipeAuthoringForm.jsx`'s `AiStubFields` left byte-for-byte
   untouched** — only its tab-bar button (`tabStyle`, now branching on
   `method === 'ai'` for the `--aub` accent) was touched, per design.md
   §10.6 and feature 28's split.
4. Prototype's separate "Ver" button (`Sobremesa.dc.html:239`) not added —
   the existing click-the-name-to-open-detail handler already satisfies
   `FR-MENU-05`; a second control doing the same thing would be new
   behaviour, not styling completion.

### Guard-file fix (mechanical, same class as T84)

`test_all_strings_from_messages.test.js`'s `SAFE_ATTR_NAMES` extended with
`cx`/`cy`/`r` — `LibraryFilters.jsx`'s new `SearchIcon`'s `<circle>` is the
first use of these SVG geometry attributes in the codebase; same false
positive T84 already fixed for `d`/`viewBox`/etc, not a new violation class.

### Mutation-kill confirmation (hand-applied, one at a time, each reverted after)

1. `LibraryView.jsx`'s remove icon-button: `remove(recipe.id)` →
   `remove(recipes[0].id)` (always removes the first card regardless of
   which one was clicked). The new "remove icon-button" test failed
   (`expected … called with ['r-2']`, got `['r-1']`). Reverted, `git diff`
   confirmed byte-identical.
2. `RecipeAuthoringForm.jsx`'s tab click: `setMethod(m)` → hardcoded
   `setMethod('scratch')`. The existing "clicking a tab calls setMethod"
   test failed (`expected … called with ['ai']`, got `['scratch']`).
   Reverted, `git diff` confirmed byte-identical.

### Test result

`npx vitest run` — **335/335 passed, 51 files** (330 → 335: 4 new
`LibraryView.test.jsx` cases exercising the card-grid's openDetail/openEdit/
remove/openAdd wiring directly via props — mirroring
`WeekPlannerView.test.jsx`'s pattern, since the file's existing tests only
exercised the real `useLibrary` hook, not per-recipe click wiring; 1 new
`RecipeAuthoringForm.test.jsx` T88 guard case). Both `LibraryFilters.test.jsx`
and `LibraryRecipePicker.test.jsx` passed **unmodified** against the new
markup (same T80a/T84 outcome — the `<label>`-wraps-`<input>`/`<select>`
structure was preserved through the restyle, so `getByLabelText`/
`getByRole('textbox')`/`closest('select')` all still resolve). `npx eslint .`
clean, `npx prettier --check .` clean (one `--write`, line-wrap only),
`npx vite build` succeeds. `./init.sh` fully green: 808 backend (untouched),
ruff/mypy/prettier/eslint/vitest. `tasks.md` T85 (Partial)/T86/T87/T88
ticked. `feature_list.json` untouched — still `in_progress`. Reviewer next;
Tier F (T89–T94) awaits a separate implementer run.

## Tier F — summary / shopping / rules / admin (T89–T94) — 2026-09-16, closes the reopen

Scope: only `specs/frontend_spa/tasks.md`'s Tier F section (T89–T94, lines
529–557) — `SummaryView.jsx`, `ShoppingListView.jsx`, `RulesView.jsx`,
`AdminAccountsView.jsx`/`AccountRow.jsx`, tests, and the closing `./init.sh`
gate. Built on the reviewer-approved Tiers A–E. No `R<n>` added (design.md
§10.0 applies unchanged — pure styling completion).

`SummaryView.jsx`: each definitive-meal row (previously a bare `<p>`+button)
became a card (`tokens.radius.md`/`shadow.sm`) carrying a "definitiva" pill
reusing `MESSAGES.WEEK_PLANNER_DEFINITIVE_BADGE` and the same
`olive`/`oliveSoft` treatment `MealCard.jsx` (T82) uses — unconditional here
since every summary entry already is the definitive meal (`useSummary.js`'s
`buildSummaryViewModel`, backend's `candidate.py` only ever returns
definitives). `ShoppingListView.jsx`: `ItemRow`'s checked style gained
`textDecoration: 'line-through'` alongside the existing `ink3` dimming; the
unchecked/checked sections each got a card container
(`sectionCardStyle`/`sectionHeadingStyle`/`listStyle` constants).
`RulesView.jsx`: the three rule-type sections (count/pin/disable) each
wrapped in a card (`ruleGroupStyle`/`ruleGroupHeadingStyle`) — grouping
extends to the whole section (list + add-controls), not just the list, since
splitting them would separate a rule's remove control from its own add form
visually. `AdminAccountsView.jsx`/`AccountRow.jsx`: an avatar-circle
(2-letter initials, `tokens.radius.pill`, colour keyed off `isAdminRow` —
`terraSoft`/`terra` for Admin, `oliveSoft`/`olive` for User, no image
dependency) plus role and pending-reset badges (`badgeStyle` constant,
`tokens.radius.pill`), replacing the plain-text role/pending spans; each row
also gained the same card shape as every other restyled list item this
reopen (`tokens.radius.md`/`shadow.sm`).

### R36/R37 — deliberately untouched

Per the dispatch brief's explicit warning (this exact conditional class has
surfaced real bugs twice already — Auth screens fix round 1 finding 1, the
fail-open `isOwnRow` bug): `isOwnRow`/`isAdminRow` in `AccountRow.jsx` were
read, never edited. `git diff` confirms zero `-`/`+` lines touching either
`const` or either `{!isOwnRow ? ... }`/`{!isAdminRow ? ... }` guard — only
style attributes changed around them. All 7 pre-existing `AccountRow.test.jsx`
cases (including the fail-closed R37 case) pass **unmodified**.

### Handler-binding self-check (T89–T92, mutation-class review)

Every prior Tier F-adjacent round (D, E) found a restyle that silently
rebound or dropped a handler's argument, always invisible to a test that
only ever exercised row/item `[0]`. Checked via `git diff` before finishing:

- `SummaryView.jsx`: `onClick={() => openDetail(slotState.candidate)}` —
  no diff line at all (unaffected by the new wrapping `<div>`'s reindent).
- `ShoppingListView.jsx`: `onToggle={setChecked}` / `onEdit={openEdit}` /
  `onRemove={remove}` passed to `ItemRow` — identical before/after, only
  reindented under the new section `<div>`.
- `RulesView.jsx`: `onRemove={() => remove(rule)}` on every `RuleRow` call
  site (×3) — identical before/after, only reindented.
- `AdminAccountsView.jsx`/`AccountRow.jsx`: zero `onClick`/`onOpen*`/`onSave*`
  diff lines anywhere — only `style` objects and the new avatar/badge markup
  were added.

### New tests: SECOND-row/item targeting (not selector-only, disclosed deviation)

`tasks.md` T93's literal text ("selector-only ... no new behavioural
assertions") is the general Tier F-adjacent convention; the dispatch brief
overrode it for this tier specifically, citing the repeated wrong-row-bound
mutant pattern. Added, per restyled list:

- `SummaryView.test.jsx`: two meals in different day/slots; clicking the
  second calls `openDetail` with that meal, not the first.
- `ShoppingListView.test.jsx`: two unchecked items; edit/remove on the
  second `getAllByText(...)` [1] target that item, not the first. Plus a
  direct `textDecoration` assertion (checked vs. unchecked).
- `RulesView.test.jsx`: two category-count rules; remove on the second
  targets that rule, not the first.
- `AdminAccountsView.test.jsx`: two accounts; rename and remove on the
  second row each target that account, not the first.
- `AccountRow.test.jsx`: one structural addition (avatar renders initials);
  the 7 existing R33/R34/R36/R37 cases untouched.

These test the same requirements (R5, R18, R34) already covered, just with a
harder 2-row fixture — no new `R<n>` invented.

### Guard-file fix (mechanical, R22)

`AccountRow.jsx`'s avatar span initially carried `aria-hidden="true"` —
`test_no_extra_accessibility.test.js` (R22, FR-UX-07/G-62: no accessibility
work beyond browser defaults) correctly flagged it. Removed; the avatar is
purely decorative styling, the same exclusion `MealCard.jsx`'s icons and
`DaySlot.jsx`'s status pill already respect.

### Test result

`npx vitest run` — **343/343 passed, 51 files** (336 → 343: 7 new cases —
1 Summary, 1 Shopping second-row + 1 strikethrough pair, 1 Rules, 2 Admin,
1 AccountRow avatar). `./init.sh` fully green: 808 backend (untouched),
ruff/mypy/prettier/eslint/vitest.

### Traceability

| Task | File(s) | `R<n>` |
|---|---|---|
| T89 | `SummaryView.jsx` | R5, R21 (styling completion) |
| T90 | `ShoppingListView.jsx` | R19, R20, R21 (styling completion) |
| T91 | `RulesView.jsx` | R12, R19 (styling completion) |
| T92 | `AdminAccountsView.jsx`, `AccountRow.jsx` | R33, R34, R36, R37 (styling completion) |
| T93 | `frontend/tests/components/{SummaryView,ShoppingListView,RulesView,AdminAccountsView,AccountRow}.test.jsx` | R5, R12, R18, R19, R20, R21, R33, R34, R36, R37 |
| T94 | `./init.sh` gate | closes T64–T94 |

`tasks.md` T89–T94 all ticked — **this closes the entire 2026-09-16
reopen (T64–T94)**. `feature_list.json` untouched — still `in_progress`.
Reviewer next.

## Tier F — fix round (3 reviewer findings, test-coverage only) — 2026-09-16

Scope: the 3 findings on T89–T94's Tier F review — all unguarded per-row
binding gaps, no source change (reviewer confirmed the handler wiring is
correct on disk).

1. `AdminAccountsView.test.jsx`: two-account reset-password binding test
   (R34) — second row's control calls `openReset(accountB)`, not `accountA`.
2. `ShoppingListView.test.jsx`: two-unchecked-item checkbox binding test —
   second row's checkbox calls `setChecked(itemB, true)`, not `itemA`.
3. `RulesView.test.jsx`: pin-rule removal assertion (previously untested) +
   a second-row `disabledDays` removal test (cheap, done per the brief).

All 3 mutants named in the brief hand-applied, confirmed each new test fails
alone, reverted (`git diff` on the 3 source files shows no change). `npx
vitest run` — **347/347 passed, 51 files** (343 → 347). `./init.sh` fully
green: 808 backend pytest, ruff/mypy/prettier/eslint/vitest all pass. This
closes the entire T64–T94 reopen. Reviewer next.

## Fix round: unstyled native controls (post-hoc, T64–T94 reopen) — 2026-09-16

Owner's manual browser QA found a gap no automated review round caught: a
card wrapper got Tier B–F styling but the native controls inside it stayed
at browser defaults. Not a new task — no `tasks.md` T-number re-ticked, this
corrects incomplete work already claimed under T89–T92.

Audited beyond the brief's 4 named `<select>` files for the same "container
styled, controls forgotten" shape across every component. Bugged:
`RulesView.jsx`, `ShoppingListView.jsx`, `AccountRow.jsx`,
`AdminAccountsView.jsx`. Already correct (checked, untouched):
`RecipeAuthoringForm.jsx`, `LibraryFilters.jsx`, and every other component
with a `<button>`/`<select>` (`LoginView`, `SetPasswordView`,
`RecipeDetailView`, `LibraryRecipePicker`, `DaySlot`, `SummaryView`,
`App.jsx`, `MealCard`, `WeekSwitcher`, `ConfirmDialog`, `LibraryView`).

New `frontend/src/domain/controlStyles.js`: `selectStyle`/`inputStyle`
(alias — prototype line 257-259 gives inputs and selects the same visual
treatment), `primaryButtonStyle(disabled)`, `secondaryButtonStyle`,
`ghostButtonStyle`, `dashedAddButtonStyle` (unused this round — no bare "add
rule" affordance exists on the real `RulesView`, kept for the next file that
needs it), `listResetStyle`, `listRowStyle`, `accentDotStyle(color)`.
Consolidates a pattern 4 files needed near-identically, same reasoning as
`RecipeAuthoringForm.jsx`'s pre-existing local `fieldInputStyle`/
`rowButtonStyle` constants (left untouched, already correct).

| Value matched | Prototype reference |
|---|---|
| `<select>`/input border/background/radius/padding/weight/outline | `Sobremesa.dc.html:257-259` (shopping draft form) |
| Rule-group `<select>` | `Sobremesa.dc.html:314, 328-336, 350-354` |
| Primary button (filled `terra`) | `Sobremesa.dc.html:260, 378` |
| Secondary/cancel button (outlined `line-2`/`ink-2`) | `Sobremesa.dc.html:340` |
| List row (flex, space-between, `border-top` separator) | `Sobremesa.dc.html:312` |
| Rule-group accent dot | `Sobremesa.dc.html:310, 323, 347` |

`RulesView.jsx`'s 3 rule-group headings wrapped in a new local
`RuleGroupHeading` (accent dot + `<h3>`): category-count → `olive`,
pin → `honey` (matches the prototype's "Comidas fijas de biblioteca" using
honey), disabled-day → `aub` (exact match, prototype's "Días sin
generación" group). No exact 9-10px radius or 7-11px padding token exists on
the 4-step/6-step scales (`design.md` §10.2) — used `radius.sm` (8px) and
`${space.xs} ${space.sm}` as the nearest fit; no new token added.

Only `style` props added to elements that already had their `value`/
`onChange`/`onClick`/`disabled` wiring — verified via `git diff` that no
prop besides `style` changed on any control in the 4 files.

| Requirement | Covered by |
|---|---|
| R12 (rules), R19 (rule-type sections) | `RulesView.jsx` restyle, `RulesView.test.jsx` unchanged (all 13 cases still pass — no selector relied on markup shape) |
| R20, R21 (shopping list) | `ShoppingListView.jsx` restyle, `ShoppingListView.test.jsx` unchanged |
| R33, R34, R36, R37 (admin accounts) | `AccountRow.jsx`/`AdminAccountsView.jsx` restyle, both test files unchanged (`AdminAccountsView.test.jsx`'s `container.querySelectorAll('input'|'select')` counts unaffected by `style`) |

`npx vitest run` — **347/347 passed, 51 files** (unchanged — pure styling
pass, no test added/removed/broken). `npx eslint .` clean, `npx prettier
--check .` clean (one `--write` on `RulesView.jsx`). Backend untouched
(verified `git status` shows zero `backend/` changes from this round).
`feature_list.json`/`docs/` untouched. Reviewer next.

## Native-controls restyle — Fix round 2 (8 reviewer findings) — 2026-09-16

| Finding | Fix | File(s) |
|---|---|---|
| F1 (real gap, surviving mutant) | New test asserting `savePin` fires on that button's click, not `saveCategoryCount`/`saveDisabledDay`. | `RulesView.test.jsx` |
| F2 (real gap, surviving mutant) | Extended the single-button disabled assertion to all 3 save buttons (category count, pin, disabled day). | `RulesView.test.jsx` |
| F3 (real gap, closes FR-SHOP-08 hole) | New test: unchecking an already-checked item calls `setChecked(item, false)`. | `ShoppingListView.test.jsx` |
| F4 | Local `listStyle` replaced by the shared `listResetStyle` import (already used elsewhere). | `ShoppingListView.jsx` |
| F5 | New `cardStyle`/`headingStyle` exports; `ruleGroupStyle`/`sectionCardStyle`/`AccountRow`'s `<li>`/`AdminAccountsView`'s create-form `<div>` all spread `cardStyle`; `ruleGroupHeadingStyle`/`sectionHeadingStyle` both replaced by `headingStyle`; `AdminAccountsView`'s account-list `<ul>` spreads `listResetStyle`. | `controlStyles.js`, `RulesView.jsx`, `ShoppingListView.jsx`, `AccountRow.jsx`, `AdminAccountsView.jsx` |
| F6 | Removed unused `dashedAddButtonStyle` (grep-confirmed zero call sites). | `controlStyles.js` |
| F7 | Header banner cut to 3 lines, pointing at this section instead of reproducing the prototype line-number table (still in `design.md` §10.6) or the fix history (still above). | `controlStyles.js` |
| F8 | Relocated `domain/controlStyles.js` → `tokens/controlStyles.js` — `domain/` is vocabulary only (`labels.js`'s role); no existing "shared component style" location outside `tokens/`, so it joins the other per-concern token files there. All 4 importers updated. | `tokens/controlStyles.js` (new), `domain/controlStyles.js` (removed) |

### Mutation-kill confirmation (F1/F2/F3)

Hand-applied each named mutant, confirmed the new/extended test failed, reverted:
- F1: `onClick={savePin}` → `onClick={saveDisabledDay}` on the pin save
  button — `'clicking the pin save button…'` failed (`called 0 times`).
- F2: removed `disabled={!canSavePin}` from the pin save button —
  `'every save control is disabled…'` failed (`expected false to be true`).
- F3: `onToggle(item, !item.checked)` → `onToggle(item, true)` — `'toggling
  an already-checked item…'` failed (asserted `false`, got `true`).

### Test result

`npx vitest run` — **349/349 passed, 51 files** (347 → 349: the 2 new tests
above; F2 extends an existing test, no new file). `npx eslint .` clean,
`npx prettier --check .` clean. `./init.sh` §5 fully green — 809 backend
pytest (unchanged, no `backend/` file touched), ruff/mypy/prettier/eslint/
vitest all pass. §4's "2 features in in_progress" failure (`ai_lambda`,
`frontend_spa`) predates this round and is outside its scope — no
`feature_list.json` edit made.
