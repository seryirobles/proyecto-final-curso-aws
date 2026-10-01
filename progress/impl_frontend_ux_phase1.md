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

## Slices F-I (T14-T32)

| R | Test |
|---|---|
| R10, R14 | tests/hooks/useScrollIntoView.test.js, tests/components/addFormsInView.test.jsx |
| R11, R12, R13 | tests/components/addFormsInView.test.jsx |
| R15-R21, R25, R28-R30 | tests/components/nativeForms.auth.test.jsx |
| R22-R24, R27 | tests/components/nativeForms.content.test.jsx |
| R25, R26 | tests/hooks/formSubmit.test.js |
| R31, R32 | tests/hooks/pendingGuard.test.js, tests/hooks/pendingGuard.hooks.test.js |
| R33 | tests/components/pendingDisabled.test.jsx |

Notes: shopping/library scroll key is 'edit'|'new' (views get no edit id), so switching
edit target without closing does not re-scroll. useScrollIntoView calls scrollIntoView
optionally (jsdom lacks it). SAFE_ATTR_NAMES in test_all_strings_from_messages gained
autoComplete and autoCapitalize. Library/Shopping remove and rule remove buttons: rule-row
remove is not wired to pending. The AI generate button stays type="button" (not a save).
Pin form includes the picker search input, so Enter there submits the pin form when valid.

Review fixes (F-I): RecipeAuthoringForm submit/generate buttons now apply the shared `disabledStyle` when disabled (R30); RuleRow remove is disabled from `pending.has('remove:<ruleId>')` (R33, `computeRuleId` now exported from useRules.js); tests in pendingDisabled.test.jsx; this supersedes the "rule-row remove not wired" note above. NO_PENDING moved below the imports in ShoppingListView.jsx.
