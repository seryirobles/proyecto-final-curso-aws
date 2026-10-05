# frontend_ux_phase2 — design

Layer: all `frontend/` (React, inline styles, hook-per-view). No backend, no
`docs/architecture.md` §2 item touched. Components stay pure; the viewport tier,
selected day, hash sync and scroll effects live in hooks. Slices ship **sequentially**
(shared `controlStyles.js`, `es-ES.js`, `App.jsx`), one implementer run + reviewer run each.

## 1. Slice map

| Slice | Plan | Requirements |
|---|---|---|
| L1 viewport hook + tokens | S15 (part) | R1-R7 |
| L2 shell | S15 | R8-R21 |
| L3 summary | S16 | R22-R25 |
| L4 week grid | S17 (part) | R26-R28, R40 |
| L5 day strip + switcher | S17 | R29-R39, R54, R57 |
| L6 touch targets + rows | S18 | R41-R44 |
| L7 hash sync | S19 | R45-R53 |

R56 applies to every slice. Dependencies on plan Phase 3 (overlays, S11-S14): **none**.
Authoring forms stay the in-flow titled sections from phase 1. Two soft interactions,
both checked manually, not built here: (a) the fixed tab bar must paint **under** the
existing `position: fixed` overlays (`ConfirmDialog`, `RecipeDetailView`); the nav is
earlier in the DOM than `<main>`, so with no `z-index` the overlays paint above it and no
zIndex token is needed; (b) the recipe-detail sheet's `90vh` / safe-area problem (F24) stays
in Phase 3.

## 2. Tokens

- `tokens/breakpoints.js`: `BREAKPOINT = { tablet: 600, medium: 768, desktop: 1280 }`.
  `desktop` changes from 1024 to 1280; no code reads it today (verified by grep), the
  existing `useBreakpoint` test uses its own query string. Proposed, owner approves.
- `tokens/layout.js` (extends `LAYOUT`): `contentMax: '1200px'`, `tabBarHeight: '56px'`,
  `headerHeight: '56px'`, `dayStripHeight: '48px'`, `targetMobile: '44px'`,
  `targetDesktop: '24px'`, `listRowMobile: '48px'`. All proposed values.
- `tokens/controlStyles.js`: `targetStyle(viewport)` returns
  `{ minHeight, minWidth }` = `targetMobile` when `compact` or `narrow` (< 768 px), else `targetDesktop`.

## 3. Files touched

**L1** new `hooks/useViewport.js`, built on `useBreakpoint`:
```js
export function useViewport() {            // 'compact' | 'narrow' | 'medium' | 'wide'
  const tablet = useBreakpoint(`(min-width: ${tokens.breakpoint.tablet}px)`);
  const medium = useBreakpoint(`(min-width: ${tokens.breakpoint.medium}px)`);
  const desktop = useBreakpoint(`(min-width: ${tokens.breakpoint.desktop}px)`);
  return desktop ? 'wide' : medium ? 'medium' : tablet ? 'narrow' : 'compact';
}
```
Constants `VIEWPORT = { COMPACT, NARROW, MEDIUM, WIDE }` exported alongside, so views never
compare string literals. Tests mock `window.matchMedia` with a parser for `min-width`
(extend the `fakeMatchMedia` idiom of `tests/hooks/useBreakpoint.test.js`); default
`viewport` prop in each view is `'wide'`, so existing view tests do not change (same pattern
as `NO_PENDING`).

**L2** `components/App.jsx`: call `useViewport()` once (R6); sticky header with
`minHeight: layout.headerHeight` (`position: 'sticky', top: 0`); `<nav>` becomes a tab bar
(`position: 'fixed', bottom: 0, left/right: 0`, `paddingBottom: env(safe-area-inset-bottom)`,
five buttons with an inline `<svg>` decorative icon over the label) when `compact`, else the
existing pill row. New `components/NavIcons.jsx` (five small svgs; no aria, no role).
`NAV_SHOPPING_LIST_SHORT: 'Compra'` in `es-ES.js` (the full "Lista de la compra" does not
fit five across at 375 px); the other four labels are reused. `main` wrapper:
`maxWidth: layout.contentMax, margin: '0 auto'`, bottom padding `tabBarHeight` plus safe
area when `compact`. Active nav style: `fontWeight: 700` + `border: 1px solid terra`.
New `hooks/useDocumentTitle.js` (`useEffect` sets `document.title`) and
`hooks/useScrollToTop.js` (`useEffect` on `activeView`, skips first mount, calls
`window.scrollTo(0, 0)`). Title template message `DOCUMENT_TITLE(view, app)` =
`` `${view} · ${app}` ``. `index.html`: `viewport-fit=cover` and `margin: 0` in the existing
inline body style; this is the only part of plan S2 pulled in (needed for R12 to take
effect). `color-scheme`, `theme-color` and favicon stay out. `tests/htmlMessages.test.js`
extended.

**L3** `SummaryView.jsx` takes `viewport`: `compact` -> `gridTemplateColumns: '1fr'`;
`narrow`/`medium` -> the existing `auto-fill` / `summaryDayMin` grid; `wide` ->
`repeat(7, minmax(0, 1fr))`. Empty slots render slot label + `SUMMARY_EMPTY_SLOT = '—'`
(new catalogue entry). The "Definitivo" badge is left as is.

**L4** `WeekPlannerView.jsx` takes `viewport`; pure helper `weekGridColumns(viewport)` in
`tokens/controlStyles.js` (style only, no domain logic): `wide` `repeat(7, minmax(0,1fr))`,
`medium` `repeat(4, minmax(0,1fr))`, else `'minmax(0, 1fr)'`. `DaySlot.jsx`: empty slot
renders `WEEK_PLANNER_EMPTY_SLOT` in a plain `<p>` (message kept, so FR-UX-05 guidance text
stays; the add button directly below is the action) instead of `EmptyState`.

**L5** new `hooks/useDayStrip.js`:
```js
export function useDayStrip() { return { registerDay, scrollToDay, selectedDay } }
// registerDay(day) -> ref callback; scrollToDay(day) sets selectedDay and calls
// refs[day]?.scrollIntoView({ block: 'start', behavior: 'smooth' })
```
New `components/DayStrip.jsx` (seven `<button type="button">`, text from
`DAY_SHORT_LABELS`, no aria, `position: 'sticky'`, `top: layout.headerHeight`,
`height: dayStripHeight`). Strip is a nowrap flex row with `overflowX: 'auto'`, `gap: space.xs`,
`padding: space.sm`; each button `flex: 'none'`, `minWidth: targetMobile` (44 px): 7 x 44 + 6 x 4 +
2 x 8 = 348 px, so it fits at 375 and 360 px and scrolls horizontally below that (R32, R57). `DaySlot` gets `cardRef` and
`scrollMarginTop = headerHeight + dayStripHeight` (CSS calc string built from tokens).
`WeekSwitcher.jsx` rewritten as two segment buttons, each containing `WeekLabel`; the arrow
glyphs and the `title` hack go (their hidden-on-touch week identity was FR-UX-06's gap).
`DAY_SHORT_LABELS` in `domain/labels.js` (Lun, Mar, Mié, Jue, Vie, Sáb, Dom; string data like
`DAY_LABELS`). `tests/test_no_extra_accessibility.test.js` is NOT modified (R54).

**L6** `targetStyle(viewport)` applied in `MealCard`, `DaySlot`, `DayStrip`, `WeekSwitcher`,
`SummaryView`, `ShoppingListView`, `RulesView`, `LibraryView`, `AccountRow` and the logout
button in `App`. Views pass `viewport` down (`WeekPlannerView` -> `DaySlot` -> `MealCard`).
Shopping row: `minHeight: listRowMobile` when `compact`; the checkbox label wrap is phase 1.
`App` passes `viewport` to Summary, Week, Library, Rules, Shopping and Admin.

**L7** new `hooks/viewHash.js` (pure): `VIEW_SLUGS`, `viewToHash(view)`,
`hashToView(hash)` (returns `null` when unknown). `hooks/useApp.js`: initial
`activeView = hashToView(window.location.hash) ?? 'week'`; `navigateTo(view)` sets state
and, only when `isAuthenticatedUser` and `view !== activeView`, calls
`history.pushState(null, '', viewToHash(view))`; an effect adds a `popstate` listener
(only while an authenticated User) that sets `activeView = hashToView(location.hash) ??
'week'`; an effect for an authenticated User with an empty/unknown hash calls
`history.replaceState(null, '', viewToHash('week'))` (R50); logout wrapper calls
`history.replaceState(null, '', location.pathname + location.search)` (R52). Slugs are
bare strings in a `.js` hook file, outside the component-scoped
`test_all_strings_from_messages` scan; they are identifiers, not copy.

## 4. Exceptions

None. `hashToView` returns `null` for unknown input; `useApp` falls back to `week`.

## 5. Test approach (Vitest + RTL, no snapshots)

Hook tests first: `useViewport` (mock `matchMedia` for each tier and a change event),
`useDayStrip` (ref stub, `scrollIntoView` mock), `viewHash`, `useApp` with `history`
spies (`vi.spyOn(history, 'pushState')`) plus `window.dispatchEvent(new PopStateEvent(...))`,
`useDocumentTitle`, `useScrollToTop` (`window.scrollTo = vi.fn()`). RTL for markup shape
per `viewport` prop: nav placement, tab button accessible names via
`getByRole('button', { name })`, `toHaveStyle` for grid columns, `position`, `minHeight`,
`paddingBottom`. jsdom has no layout, no `scrollIntoView`, no `scrollTo`: stub them in the
slice tests that need them. Source-scan test for R6 (`useViewport(` only in `App.jsx`)
and R53 (no `react-router` / `history` package import). Real-browser check
(375 / 768 / 1280 / 1440 px) is a manual task per layout slice, recorded in
`progress/impl_frontend_ux_phase2.md`.

## 6. Owner rulings 2026-10-02

- Q-A: active tab, day and week are visual-only (bold + `terra` border); no `aria-current`/`aria-pressed`.
- Q-B: day strip uses three-letter visible labels, no `aria-label`; `test_no_extra_accessibility` stays as phase 1 left it. Min button width 44 px, strip scrolls horizontally below 348 px.
- Q-C: no "today" highlight or scroll-to-today.
- Q-D: 44 px targets below 768 px (`compact` + `narrow`); 24 px from 768 px up.
- Q-E: empty slot keeps the full message in one compact line.
- Q-F: URL slugs `semana`, `biblioteca`, `reglas`, `compra`, `resumen`; cites FR-UX-02; `desktop: 1280` token change accepted.
- Q-G: summary shows 7 columns from 1280 px.
- Not covered (needs the Q1 stylesheet): hover, focus-visible styling, reduced motion, media queries.

## 7. Rejected alternatives

1. **Call `useBreakpoint` per component (or CSS `@media` via the Q1 stylesheet).**
   Per-component calls add many `matchMedia` subscriptions and make views impure; the
   stylesheet exception is approved in principle (Q1) but not written. One `useViewport` in
   `App` passed as a prop keeps components pure and testable by prop.
2. **Highlight the day strip's current day with an `IntersectionObserver` while the user
   scrolls.** It reads nicely but jsdom lacks it, it adds an effect with teardown to test,
   and there is no requirement for it. Tap-to-select state in `useDayStrip` is enough.
3. **Sync the hash by assigning `location.hash` and listening to `hashchange`.** Simpler,
   but the owner chose the History API; `pushState` does not fire `hashchange`, so it also
   avoids a double state update, and `popstate` covers Back/Forward uniformly.
