# impl: frontend_ux_phase1 (first half, slices A-E, T1-T13b)

Status: implemented, awaiting reviewer. Slices F-I (T14+) not started.

| R | Test |
|---|---|
| R1 | tests/test_no_outline_override.test.js |
| R2 | tests/components/ShoppingListView.quantity.test.jsx |
| R3 | tests/components/App.test.jsx (nav wrap) |
| R4, R5, R6 | tests/components/mobileLayout.test.jsx |
| R7, R8, R9 | tests/components/inputErgonomics.test.jsx |
| R34, R39, R41, R43 | tests/components/Banner.test.jsx |
| R35 | tests/bannerContrast.test.js |
| R34, R36, R40, R42, R43 | tests/components/errorBanner.test.jsx (8 views) |
| R37 | tests/test_no_extra_accessibility.test.js (narrowed) |
| R38 | tests/test_all_strings_from_messages.test.js (green) |

T8 (manual 375/768/1440 px check): NOT done. No browser was available in this
run, so overflow is verified by style assertions only. `layout.summaryDayMin`
stays at the approved 140px, untuned.

Update: Admin rename/reset failures now render a Banner at the top of the open AccountRow (owner ruling a); the view-level Banner is suppressed while a row form is open. Rules and the Admin create form keep the Banner below the heading (always-visible forms). This supersedes the Admin part of deviation 3.
