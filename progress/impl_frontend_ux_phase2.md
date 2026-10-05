# impl: frontend_ux_phase2 (first half, slices L1-L4, T1-T9, T11-T12, T14-T15)

Status: L1-L7 implemented (second half: T16-T20, T22-T24, T26-T29), awaiting reviewer.
Manual viewport checks T10, T13 (and T21+): NOT done, no browser in this run; boxes left unticked.

| R | Test |
|---|---|
| R1-R5 | tests/hooks/useViewport.test.js |
| R7 | tests/tokens.layout.test.js |
| R6 | tests/useViewport.sourceScan.test.js |
| R8-R16 | tests/components/App.shell.test.jsx |
| R17 | tests/hooks/useScrollToTop.test.js, App.shell |
| R18, R19 | tests/hooks/useDocumentTitle.test.js, App.shell |
| R20, R21 | tests/htmlMessages.test.js |
| R22-R25 | tests/components/SummaryView.viewport.test.jsx |
| R26-R28, R40 | tests/components/WeekPlannerView.grid.test.jsx |
| R56 | tests/test_all_strings_from_messages.test.js (green) |

Notes: tests/helpers/viewport.js (mockViewport) is new; the five App.* test files call it in
a beforeEach because App now calls useViewport. jsdom drops a bare `env()` value, so the nav's
safe-area padding is `calc(0 + env(safe-area-inset-bottom))`. mobileLayout.test.jsx (phase 1
R4) now passes viewport="medium" since wide is seven columns. Fixed header gets boxSizing.

Review fixes (L1-L4): deviation 2 reversed. Nav safe-area padding is now `calc(0px + env(safe-area-inset-bottom))` (unitless 0 is invalid in calc); App.shell test asserts the `0px` operand. New tests/components/App.viewportProp.test.jsx (R6: viewport reaches Week and Summary at 375 and 1440). The 3 mutants (unitless 0, each prop removal) die; App.jsx restored by cmp.

## Second half (L5-L7)

| R | Test |
|---|---|
| R29, R30, R31, R32, R33, R34, R35, R36, R57 | tests/components/DayStrip.test.jsx, tests/hooks/useDayStrip.test.js |
| R37-R39 | tests/components/WeekSwitcher.test.jsx (rewritten: arrows/title gone) |
| R41, R43 | tests/tokens.targetStyle.test.js, tests/components/touchTargets.week.test.jsx |
| R42, R43, R44 | tests/components/touchTargets.views.test.jsx, App.touchTargets.test.jsx |
| R45, R50 | tests/hooks/viewHash.test.js |
| R46-R52 | tests/hooks/useApp.hash.test.js |
| R53 | tests/noRoutingLibrary.sourceScan.test.js |
| R54 | tests/test_no_extra_accessibility.test.js (untouched, green) |

Notes: day strip buttons are always 44 px (strip renders only below 768 px). DaySlot
scrollMarginTop is unconditional. jsdom folds the calc to `calc(104px)`. Touch targets also
applied (beyond the list) to LibraryRecipePicker select buttons, AdminAccountsView create button
and the Library authoring-close button. Logout resets activeView to week; the R50 effect only
replaces the hash (set-state-in-effect lint forbids setState there). App.test.jsx and
App.viewportProp.test.jsx beforeEach now clear the hash (it persists across tests, R48).
Manual checks T10, T13, T21, T25, T30 not done (no browser); unticked. T31 not done.

Review fixes (L5-L7): DayStrip test now asserts the selected border colour is terra (unselected is not); the always-`line` mutant dies, DayStrip.jsx restored by cmp. useApp.js header cut to 2 lines. Gates green (691 tests).
