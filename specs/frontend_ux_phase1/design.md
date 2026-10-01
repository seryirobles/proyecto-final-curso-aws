# frontend_ux_phase1 — design

Layer: all of this is `frontend/` (React, inline styles, hook-per-view). No backend,
no architecture §2 item touched. Components stay pure; logic (pending, submit guard,
scroll trigger) lives in hooks.

## 1. Scope and slice map

Plan ids are the audit's (`plan.md` §e). Slices ship **sequentially** (shared
`controlStyles.js` / `es-ES.js`), one implementer run + reviewer run each.

| Slice | Audit findings | Requirements | Plan slice |
|---|---|---|---|
| P1-A Focus ring | F04 | R1 | S1 |
| P1-B Quantity format | F15 | R2 | S4 (part) |
| P1-C Wrap and overflow | F02 F03 F05 F06 F07 | R3-R6 | S6 |
| P1-D Mobile input ergonomics | F18 F19 F20 | R7-R9 | S7 (part) / S18 (part) |
| P1-E Banner | F12 F13 | R34-R36, R39-R43 | S5 |
| P1-F Add forms in view | F01 | R10-R14 | S13 (without `<dialog>`) |
| P1-G Native forms: auth + admin | F08 F09 F10 (auth) | R15-R21, R25-R30 | S8 |
| P1-H Native forms: shopping, rules, authoring | F08 | R22-R24, R25-R27 | S9 |
| P1-I In-flight guard | F11 | R31-R33 | S10 |
| (cross-cutting) | - | R37, R38 | - |

Order: A, B, C, D, E, F, G, H, I. G introduces the shared submit helper; H and I reuse it.

## 2. Deferred (all P0/P1 OK but not in this spec, with reason)

- **F21** (`<dialog>` overlays, plan S11/S12): large, needs a jsdom stub and rewrites
  several existing tests. P1-F deliberately uses an in-flow form so it does not depend on it.
- **F17** (44 px targets): needs `size.control` tokens and a viewport decision (24 px desktop /
  44 px mobile) that the plan ties to `useViewport` (S15). Later phase.
- F14/F16/F36-F43 etc. are P2/P3: out of the P0/P1 cut.
- F46 hover, F26 active-nav border (OK but P2), F44/F45 contrast: CONV/REQ.

## 3. Files touched, per slice

**P1-A** `tokens/controlStyles.js` (drop `outline: 'none'` at ~l.143), `components/LibraryFilters.jsx` (l.53).
New test `tests/test_no_outline_override.test.js`: source scan of `src/**/*.{js,jsx}` for `/outline\s*:\s*['"]none/`, same pattern as `test_no_extra_accessibility.test.js` (detector self-test included).

**P1-B** `components/ShoppingListView.jsx` l.38: `{formatNumber(item.quantity)}` (`locale.js` already exports it).

**P1-C** `App.jsx` nav (`flexWrap: 'wrap'`, `gap`), `SummaryView.jsx` grid -> `repeat(auto-fill, minmax(min(100%, ${tokens.layout.summaryDayMin}), 1fr))`, row fixes in `RecipeAuthoringForm.jsx`, `RulesView.jsx`, `AdminAccountsView.jsx`, `AccountRow.jsx`, `ShoppingListView.jsx` (`ResyncScope`), `AiRecipePreview.jsx`; `boxSizing: 'border-box'` in `controlStyles.js` input styles, `LoginView.jsx`, `SetPasswordView.jsx`.
New token: `tokens/spacing.js` (or new `tokens/layout.js`, exported via `tokens/index.js`): `layout.summaryDayMin = '140px'`. Proposed value; implementer may tune after a real-browser check (plan S0).

**P1-D** `tokens/typography.js`: add `fontSize.input = '16px'` (same value as `fontSize.md` if that is 16 px; alias, not literal). Used in `controlStyles.js`, `LibraryFilters.jsx` (l.56, 65), `RecipeAuthoringForm.jsx` (l.62), auth inputs. `ShoppingListView.jsx` rows 32-36: `<label>` wrapping checkbox + name. `RecipeAuthoringForm.jsx`: visible `<label>` around ingredient name, quantity, tool, step inputs; texts in `messages/es-ES.js` (`INGREDIENT_NAME_LABEL`, `INGREDIENT_QUANTITY_LABEL`, `TOOL_LABEL`, `STEP_LABEL`). Placeholders stay. Visible, not visually-hidden: a hidden-label trick would need extra CSS and adds noise.

**P1-E** New `components/Banner.jsx`: `Banner({ tone = 'error', children })` returns null when `children` is falsy (R43). `tone: 'error'` renders `role="alert"` (R34) with a leading `ERROR_PREFIX` ("Error:") label (R41); `tone: 'result'` renders `role="status"` (R39) without prefix. Style: `color: tokens.color.ink` on `backgroundColor: tokens.color.honeySoft` (11.03:1, R35), `borderLeft: 4px solid tokens.color.honey`, radius/space tokens. `children` is always a catalogue string passed by the view (R40); Banner holds no text of its own except the prefix, which is also a catalogue entry.
Replaces eight renderings (audit F12/F13, `plan.md` §b), R42: plain body-ink `<p>` in `RulesView.jsx:98`, `ShoppingListView.jsx:184`, `SummaryView.jsx:30`, `AdminAccountsView.jsx:59`, `LoginView.jsx:126`, `SetPasswordView.jsx:145` (six, not five: F13 lists Login and Set-password too), and `honey`-on-`honeySoft` (2.28:1) in `WeekPlannerView.jsx:44-55`, `LibraryView.jsx:109-121`.
Placement (R36): views have one `error` state, so the rule is: while an authoring/inline form is open (`authoringTarget`/`editingTarget` in Week, authoring block in Library, item form in Shopping, create/rename/reset in Admin, rule forms in Rules) the Banner renders directly above that form; otherwise directly below the view heading. Login and Set-password: directly above the submit button. No hook state is added; position derives from the form-open state the view already has. **Owner ruling (2026-10-01): per-form placement is final for phase 1; per-field errors are a later phase** (needs per-field hook state; the Banner stays as the form-level summary).
`danger` token (Q6, approved, later phase) will change the `honey` edge only; the text pair stays ink/honeySoft. `ConnectionLostBanner.jsx` untouched (already ink on honeySoft, FR-RT-03). Inline validation `honey` text (F14) is P2: untouched.
Narrowing `tests/test_no_extra_accessibility.test.js` is part of this slice (G-93 leaves it to the implementer): `ROLE_ATTR` becomes "any `role=` other than `status`/`alert`", `ARIA_ATTR` and `TAB_INDEX` stay banned, detector self-test updated (R37).

**P1-F** New `hooks/useScrollIntoView.js`: `useScrollIntoView(ref, key)` runs `ref.current?.scrollIntoView({ block: 'start', behavior: 'smooth' })` in an effect keyed on `key`, where `key` is the identity of the open target (day+slot+id, `'new'`, edited id), not the object, so a poll that rebuilds the week does not refire (R14). Wrapper `<section ref>` with `<h3>` title in `CandidateAuthoring.jsx` (receives the target; day/slot labels via `labels.js` + `DAY_LABELS`), in `LibraryView.jsx` (authoring block l.205-216) and `ShoppingListView.jsx` (l.232-241). Titles are message functions/templates in `es-ES.js` (`ADD_CANDIDATE_TITLE(day, slot)`, `EDIT_CANDIDATE_TITLE`, `NEW_RECIPE_TITLE`, `EDIT_RECIPE_TITLE`, `ADD_SHOPPING_ITEM_TITLE`, `EDIT_SHOPPING_ITEM_TITLE`). Refs are the allowed DOM-access idiom (conventions). Existing `authoringTarget`/`editingTarget` state is reused; no hook state is added for the scroll.

**P1-G** New `hooks/formSubmit.js`: `export function handleFormSubmit(event, canSubmit, action)`: `event.preventDefault(); if (!canSubmit) return; action();` (R25, R26). Components wrap: `<form onSubmit={(e) => handleFormSubmit(e, canSubmit, submit)}>`. Touches `LoginView.jsx`, `SetPasswordView.jsx`, `AdminAccountsView.jsx`, `AccountRow.jsx`; submit buttons become `type="submit"`, all other buttons keep `type="button"` (R27). Attributes per R16/R18/R20. `controlStyles.primaryButtonStyle(disabled)` and the login/set-password local submit styles get `opacity: 0.5`-style disabled treatment via a token (`tokens.opacity.disabled`, proposed `0.55`) and `cursor: 'not-allowed'`, so the inline `backgroundColor` no longer hides disabled (R30). Busy labels `LOGIN_SUBMITTING = 'Entrando…'`, `SET_PASSWORD_SUBMITTING = 'Guardando…'` selected from the existing `isSubmitting` of `useLoginForm` / `useSetPasswordForm`. Rationale for ignoring on disabled (R25): the spec'd disabled-until-valid gating (e.g. set-password mismatch) stays; a form submit via Enter in browsers is already blocked by a disabled default button, but `fireEvent.submit` and some engines bypass it, so the guard lives in code.

**P1-H** `ShoppingListView.jsx`, `RulesView.jsx` (3 forms), `RecipeAuthoringForm.jsx`: wrap in `<form>`, reuse `handleFormSubmit`. Audit every `<button>` inside the new forms and set `type="button"` unless it is the submit (R27; test scans the markup of each form for stray default-type buttons).

**P1-I** Hooks `useWeekPlanner`, `useLibrary`, `useShoppingList`, `useRules`, `useAdminAccounts`, `useRecipeAuthoring` (+ `useLoginForm`/`useSetPasswordForm` already track `isSubmitting`; leave). Add a tiny shared helper `hooks/pendingGuard.js`: `createPendingGuard()` returns `{ run(key, fn) , isPending(key) }` backed by a `useRef` Set plus `useState` mirror so a second `run(key)` in the same tick no-ops (ref, not state, decides: state updates are async and two taps in one tick would both pass). Guarded actions: candidate create/edit submit, promote/clear definitive, recipe save/delete, shopping item add/edit/remove and re-sync, rule save, admin create/rename/reset, authoring save. Checkbox toggle is NOT guarded (idempotent and optimistic). Hooks return `pending` (`pending.has('submitCandidate')` or per-key accessor); components pass it to `disabled` and show the busy label where one exists (R33).

## 4. Signatures

```js
// hooks/formSubmit.js
export function handleFormSubmit(event, canSubmit, action) {}   // pure
// hooks/useScrollIntoView.js
export function useScrollIntoView(ref, key) {}                  // effect hook
// hooks/pendingGuard.js
export function usePendingGuard() { return { run, isPending } } // run(key, asyncFn) -> Promise|undefined
// components/Banner.jsx
export function Banner({ tone, children }) {}   // tone: 'error' | 'result'
```

No exceptions added. API errors keep flowing through each hook's existing `error`
state; `Banner` only presents it.

## 5. Test approach (Vitest + RTL, no snapshots)

Hook tests first (`pendingGuard`, `handleFormSubmit`, scroll key stability via
`renderHook` + a ref stub). RTL for markup shape: `container.querySelector('form')`,
`fireEvent.submit(form)` -> handler called once; `getByLabelText` for R9 and R8
(`userEvent.click(getByText(name))` toggles); `toHaveStyle` for `flexWrap`,
`boxSizing`, `opacity`, `fontSize`; attribute assertions for autocomplete.
jsdom has no layout and no `scrollIntoView`: stub `Element.prototype.scrollIntoView =
vi.fn()` in the P1-F tests only; overflow requirements are verified by style
assertion, with the real-browser check as the plan's S0/manual matrix (375 px, 768 px,
1440 px, iOS Safari for R7 zoom). `test_no_extra_accessibility` and
`test_all_strings_from_messages` run on every slice (R37, R38).

## 6. Flags for the owner at the approval gate

- Banner requirements (R34-R36, R39-R43) are anchored in FR-UX-07 as amended by G-93
  (1.4.3, 4.1.3); this spec uses `role="alert"|"status"` only and no `aria-*`.
- R9 (labels) and R8 (label-wrap) use native `<label>`, not ARIA, so they fit FR-UX-07 as
  restoring browser defaults. Same reasoning for R1 (focus ring) and R15-R24 (`<form>`).
- No `feature_list.json` entry exists for this spec; the leader owns adding it.
- Values approved by the owner: `layout.summaryDayMin = 140px`,
  `fontSize.input = 16px`, `opacity.disabled = 0.55`.

## 7. Rejected alternatives

1. **Wait for the `<dialog>` `Overlay` (plan S11-S13) and fix F01 there.** It would give
   Escape, focus return and a proper modal for free, but it makes the P0 fix depend on a
   large cross-cutting rewrite that breaks several existing tests. An in-flow titled
   form plus scroll-into-view fixes the P0 now; the overlay can replace the wrapper later.
2. **Guard double-submit with component-local `useState` (`isSubmitting`) per button.**
   It duplicates the logic in ~10 components and `setState` is async, so two taps in one
   tick still both pass. A ref-backed guard in the hook is testable by two rapid
   `submit()` calls -> one `apiFetch`.
3. **Make Enter work by adding `onKeyDown` handlers to inputs, keeping `type="button"`.**
   It avoids touching markup but reimplements implicit submission badly (IME composition,
   multi-field order) and does not give password managers the form they look for
   (F09). Native `<form>` is the browser default FR-UX-07 relies on.
