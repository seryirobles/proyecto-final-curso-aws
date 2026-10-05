# frontend_ux_phase2 — requirements

Source: `specs/frontend_ux_plan/plan.md` Phase 4 (S15-S19), with owner decisions Q3
(bottom tab bar), Q4 (day strip), Q5 (hash sync), Q7 (week grid) and FR-UX-07 as amended
by G-93. Finding ids `F<nn>` are the audit's.

No new FR is invented. Every R restates `FR-UX-02` (responsive site) or `FR-UX-06` /
`FR-UX-07` through the lens of the plan. No FR speaks to URL state; R45-R53 cite
`FR-UX-02` (mobile Back button) and `design.md` §6 flags it.

Out of scope: base stylesheet (Q1, no `design.md` exception written yet, so no `@media`,
`:hover`, `:focus-visible`), `danger` token (Q6), overlays (plan S11-S14), "today"
highlight (no FR, frontend must not compute the current week; see `design.md` §6).
Phase 1 work (Banner, native forms, pending guard, titled add-forms, focus ring) is not
repeated.

Viewport tiers (names are this spec's): `compact` < 600 px, `narrow` 600-767,
`medium` 768-1279, `wide` >= 1280.

`feature_list.json` has no entry yet (leader adds it, suggested name `frontend_ux_phase2`).

## Viewport hook (S15)

## R1
Implements: FR-UX-02

WHILE the viewport width is below 600 px, the system SHALL make `useViewport` return `'compact'`.

## R2
Implements: FR-UX-02

WHILE the viewport width is 600 px to 767 px, the system SHALL make `useViewport` return `'narrow'`.

## R3
Implements: FR-UX-02

WHILE the viewport width is 768 px to 1279 px, the system SHALL make `useViewport` return `'medium'`.

## R4
Implements: FR-UX-02

WHILE the viewport width is 1280 px or more, the system SHALL make `useViewport` return `'wide'`.

## R5
Implements: FR-UX-02

WHEN the viewport width crosses a tier threshold, the system SHALL update the value returned by `useViewport` without remounting the component that called it.

## R6
Implements: FR-UX-02

The system SHALL call `useViewport` once, in `App`, and pass its result to the views as a `viewport` prop.

## R7
Implements: FR-UX-02

The system SHALL take the 600, 768 and 1280 thresholds from the breakpoint tokens.

## Shell (S15)

## R8
Implements: FR-UX-02

WHILE the viewport is `compact` and a User is authenticated, the system SHALL render the five navigation buttons in a `<nav>` fixed to the bottom edge of the screen.

## R9
Implements: FR-UX-02

WHILE the viewport is not `compact` and a User is authenticated, the system SHALL render the five navigation buttons as a row of pills below the header.

## R10
Implements: FR-UX-07

The system SHALL render each bottom tab bar button as a decorative icon above a visible text label, so that the button's accessible name is that text.

## R11
Implements: FR-UX-07

The system SHALL give each bottom tab bar button a minimum height of at least 48 px, taken from a layout token.

## R12
Implements: FR-UX-02

The system SHALL pad the bottom of the tab bar by `env(safe-area-inset-bottom)`.

## R13
Implements: FR-UX-02

WHILE the tab bar is shown, the system SHALL pad the bottom of `<main>` by at least the tab bar height, so that no content is hidden behind it.

## R14
Implements: FR-UX-07

The system SHALL mark the active navigation button with bold text and a `terra` border in addition to its background, in both nav layouts (F26, WCAG 1.4.11).

## R15
Implements: FR-UX-02

The system SHALL keep the header stuck to the top of the viewport while the page scrolls, in the User and Admin shells.

## R16
Implements: FR-UX-02

The system SHALL centre `<main>` content within a maximum width taken from a layout token (`contentMax`).

## R17
Implements: FR-UX-02

WHEN the active view changes, the system SHALL scroll the window to the top.

## R18
Implements: FR-UX-02

WHILE a User is authenticated, the system SHALL set `document.title` to the active view's navigation label followed by " · " and the application title.

## R19
Implements: FR-UX-02

WHILE no User is authenticated, the system SHALL set `document.title` to the application title.

## R20
Implements: FR-UX-02

The system SHALL include `viewport-fit=cover` in the viewport meta tag of `index.html`.

## R21
Implements: FR-UX-02

The system SHALL set the body margin of `index.html` to zero.

## Summary (S16)

## R22
Implements: FR-UX-02

WHILE the viewport is `compact`, the system SHALL lay out the summary days as a single column.

## R23
Implements: FR-UX-02

WHILE the viewport is `narrow` or `medium`, the system SHALL lay out the summary days as an `auto-fill` grid whose minimum column width is `layout.summaryDayMin`.

## R24
Implements: FR-UX-02

WHILE the viewport is `wide`, the system SHALL lay out the summary days as seven equal columns.

## R25
Implements: FR-SUM-01

The system SHALL render each slot that has no definitive meal as its slot label followed by "—", in every summary layout.

## Week view (S17)

## R26
Implements: FR-UX-02

WHILE the viewport is `wide`, the system SHALL lay out the seven day cards in one row of seven equal columns, Monday to Sunday.

## R27
Implements: FR-UX-02

WHILE the viewport is `medium`, the system SHALL lay out the day cards in a four-column grid, so that they wrap as 4 + 3.

## R28
Implements: FR-UX-02

WHILE the viewport is `compact` or `narrow`, the system SHALL lay out the day cards in a single column.

## R29
Implements: FR-UX-02

WHILE the viewport is `compact` or `narrow`, the system SHALL render a day strip of seven buttons above the day cards.

## R30
Implements: FR-UX-02

WHILE the viewport is `medium` or `wide`, the system SHALL NOT render the day strip.

## R31
Implements: FR-UX-02

The system SHALL label the day strip buttons with the visible three-letter day names Lun, Mar, Mié, Jue, Vie, Sáb, Dom in Monday-to-Sunday order.

## R32
Implements: FR-UX-07

The system SHALL give each day strip button a width of at least `layout.targetMobile` (44 px) that does not shrink, so that the three-letter label fits at 375 px (7 x 44 px + 6 gaps of 4 px + 2 x 8 px padding = 348 px).

## R57
Implements: FR-UX-02

WHILE the day strip buttons do not fit the viewport width, the system SHALL let the strip scroll horizontally instead of wrapping or shrinking its buttons.

## R33
Implements: FR-UX-02

WHEN a day strip button is activated, the system SHALL scroll that day's card into view.

## R34
Implements: FR-UX-02

WHEN a day strip button is activated, the system SHALL mark that button as selected with bold text and a `terra` border.

## R35
Implements: FR-UX-02

WHILE the day strip is shown, the system SHALL keep it stuck below the header while the page scrolls.

## R36
Implements: FR-UX-02

WHILE the day strip is shown, the system SHALL give each day card a scroll margin equal to the header height plus the strip height, so that a scrolled-to card is not hidden behind them.

## R37
Implements: FR-UX-06

The system SHALL render the week switcher as two buttons, one for the current week and one for the next, each showing its designation and its Monday-Sunday date range.

## R38
Implements: FR-UX-06

The system SHALL highlight the week switcher button of the displayed week with bold text and a `terra` border.

## R39
Implements: FR-UX-06

WHEN a week switcher button is activated, the system SHALL call the week switch handler with that button's designation.

## R40
Implements: FR-UX-05

The system SHALL render an empty slot's message as a single compact line without the dashed empty-state box.

## Touch targets and list rows (S18)

## R41
Implements: FR-UX-07

WHILE the viewport is `compact` or `narrow` (below 768 px), the system SHALL give every button of `MealCard`, `DaySlot`, the day strip and the week switcher a minimum height and width of `layout.targetMobile` (44 px).

## R42
Implements: FR-UX-07

WHILE the viewport is `compact` or `narrow`, the system SHALL give every button of the Summary recipe link, `ShoppingListView`, `RulesView`, `LibraryView`, `AccountRow` and the logout control a minimum height and width of `layout.targetMobile`.

## R43
Implements: FR-UX-07

WHILE the viewport is `medium` or `wide` (768 px or more), the system SHALL give every button listed in R41 and R42 a minimum height and width of at least `layout.targetDesktop` (24 px).

## R44
Implements: FR-UX-07

WHILE the viewport is `compact` or `narrow`, the system SHALL give each shopping-list item row a minimum height of `layout.listRowMobile` (48 px).

## View URL sync (S19)

## R45
Implements: FR-UX-02

The system SHALL map the views `week`, `library`, `rules`, `shoppingList` and `summary` to the hashes `#/semana`, `#/biblioteca`, `#/reglas`, `#/compra` and `#/resumen`.

## R46
Implements: FR-UX-02

WHEN an authenticated User navigates to a different view, the system SHALL add a history entry (`history.pushState`) whose hash is that view's hash.

## R47
Implements: FR-UX-02

WHEN an authenticated User navigates to the view already active, the system SHALL NOT add a history entry.

## R48
Implements: FR-UX-02

WHEN the app starts with a known view hash in the URL, the system SHALL make that view the initial active view.

## R49
Implements: FR-UX-02

WHEN a `popstate` event fires, the system SHALL set the active view to the one named by the current URL hash.

## R50
Implements: FR-UX-02

IF the URL hash is empty or names no known view, THEN the system SHALL set the active view to `week` and replace the hash with `#/semana` without adding a history entry.

## R51
Implements: FR-UX-02

WHILE the session is not an authenticated User, the system SHALL NOT write to the URL hash.

## R52
Implements: FR-UX-02

WHEN a User logs out, the system SHALL remove the view hash from the URL without adding a history entry.

## R53
Implements: FR-UX-02

The system SHALL NOT import a routing library.

## Guards (cross-cutting)

## R54
Implements: FR-UX-07

The system SHALL pass `tests/test_no_extra_accessibility.test.js` unchanged from its phase 1 contract (no `aria-*`, no `tabIndex`, no `role` other than `status`/`alert`), so that the tab bar, day strip and week switcher rely on visible text only.

## R55
(removed: the `aria-label` allowance was dropped by the owner ruling Q-B, 2026-10-02; number kept so later ids do not shift.)

## R56
Implements: FR-UX-01, FR-UX-03

The system SHALL source every new user-visible string (short tab labels, three-letter day names, "—", title separator) from the messages catalogue, so that `tests/test_all_strings_from_messages.test.js` stays green.
