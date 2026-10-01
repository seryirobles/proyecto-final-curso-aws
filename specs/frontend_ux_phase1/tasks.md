# frontend_ux_phase1 — tasks

Sequential slices; each ends with `npm test` green (incl. `test_no_extra_accessibility`,
`test_all_strings_from_messages`) and a reviewer run. Read before write; prefer Edit.
Tests first within each slice.

## P1-A Focus ring
- [ ] T1 — Add `tests/test_no_outline_override.test.js` (source scan + detector self-test). Covers: R1.
- [ ] T2 — Remove `outline: 'none'` from `tokens/controlStyles.js` and `LibraryFilters.jsx`. Covers: R1.

## P1-B Quantity format
- [ ] T3 — RTL test: quantity 0.5 renders "0,5". Covers: R2.
- [ ] T4 — `ShoppingListView.jsx`: render `formatNumber(item.quantity)`. Covers: R2.

## P1-C Wrap and overflow
- [ ] T5 — Add `layout.summaryDayMin` token, export via `tokens/index.js`. Covers: R4.
- [ ] T6 — Style tests (`toHaveStyle`): nav `flexWrap`, summary `auto-fill` grid, each R5 row `flexWrap`, inputs `boxSizing`. Covers: R3, R4, R5, R6.
- [ ] T7 — Apply wrap/grid/boxSizing changes in `App.jsx`, `SummaryView.jsx`, `RecipeAuthoringForm.jsx`, `RulesView.jsx`, `AdminAccountsView.jsx`, `AccountRow.jsx`, `ShoppingListView.jsx`, `AiRecipePreview.jsx`, `controlStyles.js`, `LoginView.jsx`, `SetPasswordView.jsx`. Covers: R3, R4, R5, R6.
- [ ] T8 — Manual check 375/768/1440 px, record in `progress/impl_frontend_ux_phase1.md`. Covers: R3, R4, R5.

## P1-D Mobile input ergonomics
- [ ] T9 — Add `fontSize.input` token; add label messages in `es-ES.js`. Covers: R7, R9, R38.
- [ ] T10 — Tests: input `fontSize`; clicking item text toggles checkbox; `getByLabelText` finds ingredient name/qty, tool, step. Covers: R7, R8, R9.
- [ ] T11 — Apply font size in `controlStyles.js`, `LibraryFilters.jsx`, `RecipeAuthoringForm.jsx`, auth inputs; `<label>`-wrap shopping rows; label the authoring inputs. Covers: R7, R8, R9.

## P1-E Banner
- [ ] T12 — Test `Banner` (null when empty; ink/honeySoft/honey style) and per-view test that each error renders inside it, none when no error. Covers: R34, R35, R36.
- [ ] T13 — Add `components/Banner.jsx`; replace the error `<p>` in the 8 views. Covers: R34, R35, R36.

## P1-F Add forms in view
- [ ] T14 — Add title messages to `es-ES.js`. Covers: R11, R12, R13, R38.
- [ ] T15 — Hook test `useScrollIntoView`: called once on open, not again when the target object is rebuilt with the same key. Covers: R10, R14.
- [ ] T16 — Add `hooks/useScrollIntoView.js`. Covers: R10, R14.
- [ ] T17 — RTL (stub `scrollIntoView`): Week add/edit shows title with day + slot and scrolls; Library new/edit title; Shopping add/edit title. Covers: R10, R11, R12, R13.
- [ ] T18 — Wrap the forms in a titled `<section ref>` in `CandidateAuthoring.jsx`, `LibraryView.jsx`, `ShoppingListView.jsx`. Covers: R10, R11, R12, R13, R14.

## P1-G Native forms: auth + admin
- [ ] T19 — Test `handleFormSubmit`: preventDefault always; action only when allowed. Covers: R25, R26.
- [ ] T20 — Add `hooks/formSubmit.js`. Covers: R25, R26.
- [ ] T21 — Add `opacity.disabled` token and busy-label messages. Covers: R28, R29, R30, R38.
- [ ] T22 — RTL: login and set-password `<form>` submit calls handler; Enter-equivalent submit ignored when disabled; attributes (`name`, `autoComplete`, `spellCheck`, `autoCapitalize`); busy labels; disabled style. Covers: R15, R16, R17, R18, R25, R28, R29, R30.
- [ ] T23 — RTL: admin create form and `AccountRow` rename/reset forms submit + autocomplete attributes. Covers: R19, R20, R21.
- [ ] T24 — Implement in `LoginView.jsx`, `SetPasswordView.jsx`, `AdminAccountsView.jsx`, `AccountRow.jsx`, `controlStyles.primaryButtonStyle`; other buttons `type="button"`. Covers: R15-R21, R26, R27, R28, R29, R30.

## P1-H Native forms: shopping, rules, authoring
- [ ] T25 — RTL: shopping item form, the 3 rules forms and the recipe authoring form each submit via `fireEvent.submit`; markup scan: every non-submit button in each form has `type="button"`. Covers: R22, R23, R24, R25, R27.
- [ ] T26 — Wrap forms and fix button types in `ShoppingListView.jsx`, `RulesView.jsx`, `RecipeAuthoringForm.jsx`. Covers: R22, R23, R24, R27.

## P1-I In-flight guard
- [ ] T27 — Hook test `usePendingGuard`: two same-tick `run('k')` -> one fn call; different keys independent; `isPending` true while running, false after reject. Covers: R31, R32.
- [ ] T28 — Add `hooks/pendingGuard.js`. Covers: R31, R32.
- [ ] T29 — Hook tests per hook (`useWeekPlanner`, `useLibrary`, `useShoppingList`, `useRules`, `useAdminAccounts`, `useRecipeAuthoring`): two rapid calls to each guarded action -> one `apiFetch`. Covers: R32.
- [ ] T30 — Wire guard and expose `pending` in the six hooks. Covers: R31, R32.
- [ ] T31 — RTL: trigger buttons disabled while pending. Wire `disabled={pending...}` in the views. Covers: R33.

## Close-out
- [ ] T32 — Run full frontend suite; confirm `test_no_extra_accessibility` and `test_all_strings_from_messages` green; write the R -> test table in `progress/impl_frontend_ux_phase1.md`. Covers: R37, R38.
