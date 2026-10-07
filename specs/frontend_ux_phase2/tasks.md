# frontend_ux_phase2 — tasks

Sequential slices; each ends with `npm test` green (incl. `test_no_extra_accessibility`,
`test_all_strings_from_messages`) and a reviewer run. Read before write; prefer Edit.
Tests first within each slice. Every layout slice ends with a manual check at
375 / 768 / 1280 / 1440 px, recorded in `progress/impl_frontend_ux_phase2.md`.

## L1 Viewport hook + tokens
- [x] T1 — Hook tests for `useViewport` with a `min-width` `matchMedia` mock: one test per tier at its boundary values (599/600, 767/768, 1279/1280) and one for a change event without remount. Covers: R1, R2, R3, R4, R5.
- [x] T2 — Update `tokens/breakpoints.js` (`medium: 768`, `desktop: 1280`) and add the `layout.js` tokens from `design.md` §2; token value test. Covers: R7.
- [x] T3 — Add `hooks/useViewport.js` and `VIEWPORT` constants. Covers: R1, R2, R3, R4, R5, R7.
- [x] T4 — Source-scan test: `useViewport(` appears only in `components/App.jsx` and its own file. Covers: R6.

## L2 Shell
- [x] T5 — Add messages (`NAV_SHOPPING_LIST_SHORT`, `DOCUMENT_TITLE`). Covers: R10, R18, R56.
- [x] T6 — Hook tests: `useDocumentTitle` (User -> "Semana · Planificador semanal"; anonymous -> app title), `useScrollToTop` (not on mount, once per view change, `window.scrollTo` stub). Covers: R17, R18, R19.
- [x] T7 — App RTL per `viewport` (mock `matchMedia`): `compact` nav has `position: fixed`, `bottom: 0`, `paddingBottom` containing `env(safe-area-inset-bottom)`, five buttons found by `getByRole('button', { name })`, min height >= 48 px; non-compact nav is in the top row below the header; main has bottom padding only when `compact`, `maxWidth` contentMax; header `position: sticky` in User and Admin shells; active button bold + terra border in both layouts. Covers: R8, R9, R10, R11, R12, R13, R14, R15, R16.
- [x] T8 — `htmlMessages.test.js` assertions: `viewport-fit=cover`, body margin 0. Covers: R20, R21.
- [x] T9 — Implement: `NavIcons.jsx`, `App.jsx` shell, `useDocumentTitle.js`, `useScrollToTop.js`, `index.html`. Covers: R6, R8-R21.
- [ ] T10 — Manual check at 375/768/1280/1440 px: tab bar vs. overlays (`ConfirmDialog`, recipe detail paint above it), content not hidden behind the bar, iOS safe area. Covers: R8-R16.

## L3 Summary
- [x] T11 — Message `SUMMARY_EMPTY_SLOT`. Tests (RTL, `viewport` prop): `compact` single column, `narrow`/`medium` `auto-fill` with `summaryDayMin`, `wide` seven columns; an empty slot shows its label and "—" in each layout. Covers: R22, R23, R24, R25, R56.
- [x] T12 — Implement in `SummaryView.jsx`; pass `viewport` from `App`. Covers: R22, R23, R24, R25.
- [ ] T13 — Manual check at 375/768/1280/1440 px. Covers: R22, R23, R24.

## L4 Week grid
- [x] T14 — RTL (`viewport` prop): grid columns for `wide` (7), `medium` (4), `compact`/`narrow` (1); empty slot renders a `<p>` with the message and no dashed box. Covers: R26, R27, R28, R40.
- [x] T15 — Implement `weekGridColumns`, `WeekPlannerView` and `DaySlot` empty-slot change; update existing `DaySlot`/`WeekPlannerView` tests that expect the `EmptyState` box. Covers: R26, R27, R28, R40.

## L5 Day strip + week switcher
- [x] T16 — Add `DAY_SHORT_LABELS` to `domain/labels.js`; hook test for `useDayStrip` (`scrollToDay` calls `scrollIntoView` on the registered node and sets `selectedDay`). Covers: R31, R33, R34.
- [x] T17 — Confirm `tests/test_no_extra_accessibility.test.js` is untouched and green with the new components (no aria, no tabIndex, no extra role). Covers: R54.
- [x] T18 — RTL: strip rendered only for `compact`/`narrow`; seven buttons in Monday-Sunday order with visible labels Lun Mar Mié Jue Vie Sáb Dom and no `aria-label`; each button `minWidth` 44 px, `flex: none`, strip `overflowX: auto`, no wrap; tapping one calls `scrollIntoView` (stub) and styles it selected; sticky `top` and card `scrollMarginTop` style assertions. Covers: R29, R30, R31, R32, R33, R34, R35, R36, R57.
- [x] T19 — RTL `WeekSwitcher`: two buttons, each with designation and range; displayed week highlighted; click calls `onSwitch` with its designation. Update `WeekSwitcher.test.jsx` (arrows/`title` gone). Covers: R37, R38, R39.
- [x] T20 — Implement `useDayStrip.js`, `DayStrip.jsx`, `DaySlot` `cardRef`/`scrollMarginTop`, `WeekSwitcher.jsx`, `WeekPlannerView.jsx`. Covers: R29-R39.
- [ ] T21 — Manual check at 375/768/1280/1440 px: strip stays under the header while scrolling, tap lands on the day without being covered, switcher legible at 375 px. Covers: R29-R39.

## L6 Touch targets + list rows
- [x] T22 — Add `targetStyle(viewport)` to `controlStyles.js` with unit test. Covers: R41, R42, R43.
- [x] T23 — RTL per component (`compact` and `narrow` -> 44 px min height and width on every button; `medium` and `wide` -> 24 px): `MealCard`, `DaySlot`, `DayStrip`, `WeekSwitcher`, `SummaryView`, `ShoppingListView`, `RulesView`, `LibraryView`, `AccountRow`, `App` logout; shopping row `minHeight` 48 px when `compact`. Covers: R41, R42, R43, R44.
- [x] T24 — Apply `targetStyle` and thread the `viewport` prop (`WeekPlannerView` -> `DaySlot` -> `MealCard`; `App` -> every view). Covers: R41, R42, R43, R44.
- [ ] T25 — Manual measurement in DevTools at 375 px (44 px) and 1280/1440 px (>= 24 px) for every listed control. Covers: R41, R42, R43, R44.

## L7 View URL sync
- [x] T26 — Unit tests for `viewHash` (five slugs both ways, `null` for unknown/empty). Covers: R45, R50.
- [x] T27 — `useApp` hook tests with `history.pushState`/`replaceState` spies and `PopStateEvent`: push on change, no push for the same view, initial view from hash, popstate updates the view, unknown/empty hash replaces with `#/semana` (no push) [superseded by T32: now `#/resumen`], no writes for anonymous/Admin/password-reset sessions, logout clears the hash. Covers: R46, R47, R48, R49, R50, R51, R52.
- [x] T28 — Source-scan test: no `react-router`/routing-library import in `src/`. Covers: R53.
- [x] T29 — Implement `hooks/viewHash.js` and the `useApp.js` changes. Covers: R45-R52.
- [ ] T30 — Manual check: Back/Forward, refresh keeps the view, deep link `#/reglas`, at 375 px and 1440 px. Covers: R46-R50.

## Wrap-up
- [ ] T31 — Run the full `npm test`, and record the traceability table (R -> test) plus the manual-check results (375/768/1280/1440 px) in `progress/impl_frontend_ux_phase2.md`. Covers: R56.

## L8 Summary as default view + shortcut (owner change 2026-10-05; Covers listed per task)
- [x] T32 — Hook tests first in `tests/hooks/useApp.test.js`: empty/unknown hash gives `summary` and `replaceState` with `#/resumen` (no push); `#/semana` still opens `week`; logout resets the view to `summary`; Admin/anonymous/password-reset still never write the hash. Update the existing cases that expect `week`/`#/semana`. Covers: R58, R59, R48, R51.
- [x] T33 — Add `SUMMARY_EDIT_WEEK` to `es-ES.js`. Covers: R60, R56.
- [x] T34 — `SummaryView` RTL: shortcut button present with the catalogue text directly after the h2 in loaded, empty and error states and calls `onEditWeek` once; `compact`/`narrow` -> 44 px min size, `medium`/`wide` -> 24 px; styled with `primaryButtonStyle(false)` (background `terra`); no `aria-*`/`role` attribute. Covers: R60, R61, R62, R63, R64, R65.
- [x] T35 — App-level RTL (User session): lands on summary with `#/resumen`; clicking the shortcut shows the week view and calls `pushState` once with `#/semana`; clicking it again from week is not offered. Covers: R58, R62.
- [x] T36 — Implement `useApp.js` default and logout reset, `SummaryView.jsx`, `App.jsx` wiring. Update the existing tests listed in `design.md` §6a that assumed `week` as default. Covers: R58-R65.
- [ ] T37 — Manual check at 375/768/1280/1440 px: shortcut visible under the heading without scrolling, not clipped, Back from week returns to summary. Record in `progress/impl_frontend_ux_phase2.md`. Covers: R60-R64.

## L9 Nav order: Resumen first (owner ruling 2026-10-05)
Sequencing: do NOT implement until the reviewer has finished L8; both touch `useApp.js`, `App.jsx` and the same tests.
- [x] T38 — Tests first: `useApp` `VIEWS`/`navTargets` equal `['summary','week','library','rules','shoppingList']` for a User and `[]` for Admin; App RTL at `compact` (tab bar) and `wide` (pills): button names in DOM order Resumen, Semana, Biblioteca, Reglas, Compra / Lista de la compra; Admin shell renders no nav. Update existing assertions of the old order in the files listed in `design.md` §6a. Covers: R66, R67, R68.
- [x] T39 — Reorder `VIEWS` in `hooks/useApp.js`; confirm `App.jsx` renders from `navTargets` with no second list. Covers: R66, R67, R68.
- [ ] T40 — Manual check at 375/768/1280/1440 px: tab bar and pill order, active-state styling still correct. Record in `progress/impl_frontend_ux_phase2.md`. Covers: R67, R68.

