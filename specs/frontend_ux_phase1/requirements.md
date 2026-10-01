# frontend_ux_phase1 — requirements

Source: `specs/frontend_ux_plan/plan.md` (audit, 2026-10-01), restricted to findings
tagged **OK**, severity **P0/P1**, that need no base stylesheet, no FR-UX-07 lift, no
bottom tab bar, day strip, hash sync, `danger` token or desktop week grid.
(Amended: FR-UX-07 was lifted by G-93; the error Banner uses its 1.4.3 / 4.1.3 subset.
A `danger` colour token is approved (Q6) but arrives in a later phase; it will replace
the `honey` edge, not the ink-on-honeySoft text pair.)
Finding ids `F<nn>` are the audit's. No new FR is invented: every R restates an
existing FR through the lens of the audit. Where no FR speaks to the behaviour,
the R cites the nearest FR and `design.md` §6 flags it.

`feature_list.json` has no entry for this work (not edited by the spec author).
The leader must add one (suggested name `frontend_ux_phase1`) before approval.

Gate: every R is native HTML + inline styles + existing tokens. The only aria/role use
is `role="alert"|"status"` on `Banner` (G-93); no `aria-*`/`tabIndex` (R37).

## Focus ring (F04)

## R1
Implements: FR-UX-07, FR-UX-02

The system SHALL render every text input, select and search input without an `outline` style override, leaving the browser-default focus ring.

## Number formatting (F15)

## R2
Implements: FR-UX-03, FR-SHOP-01

The system SHALL render each shopping-list item quantity through `formatNumber` (es-ES), so that 0.5 appears as "0,5".

## Mobile overflow (F02, F03, F05, F06, F07)

## R3
Implements: FR-UX-02

The system SHALL lay out the five navigation pills in a wrapping flex row, so that the page does not scroll horizontally at 375 px.

## R4
Implements: FR-UX-02

The system SHALL lay out the summary day columns as an `auto-fill` grid with a minimum column width taken from a layout token, instead of a fixed seven-column grid.

## R5
Implements: FR-UX-02

The system SHALL set `flexWrap: 'wrap'` on each of these rows: the recipe-method tabs, the ingredient row, the three rules forms, the admin create row, `AccountRow`, the shopping re-sync row and the AI-preview action row.

## R6
Implements: FR-UX-02

The system SHALL set `boxSizing: 'border-box'` on every text input and select, including the login and set-password inputs.

## Mobile input ergonomics (F18, F19, F20)

## R7
Implements: FR-UX-02

The system SHALL render text inputs, selects and the library search input at a font size of at least 16 px, taken from a typography token.

## R8
Implements: FR-SHOP-07, FR-UX-02

The system SHALL wrap each shopping-item checkbox and its item text in one `<label>`, so that tapping the text toggles the checkbox.

## R9
Implements: FR-CAND-03, FR-LIB-02, FR-UX-07

The system SHALL associate a `<label>` element with each ingredient name, ingredient quantity, tool and step input of the recipe authoring form.

## Add forms open in view (F01)

## R10
Implements: FR-CAND-01, FR-LIB-02, FR-SHOP-02, FR-UX-02

WHEN the candidate, library-recipe or shopping-item authoring form opens (add or edit), the system SHALL scroll that form into view.

## R11
Implements: FR-CAND-01, FR-UX-06

WHEN the candidate authoring form opens, the system SHALL show a title naming the target day and slot ("Añadir a lunes · Comida" for add, "Editar · lunes · Comida" for edit).

## R12
Implements: FR-LIB-02

WHEN the library authoring form opens, the system SHALL show the title "Nueva receta" for add or "Editar receta" for edit.

## R13
Implements: FR-SHOP-02

WHEN the shopping-item form opens, the system SHALL show the title "Añadir elemento" for add or "Editar elemento" for edit.

## R14
Implements: FR-CAND-01, FR-LIB-02, FR-SHOP-02

IF a polling refresh re-renders a view while its authoring form stays open, THEN the system SHALL scroll the form into view no additional time.

## Forms behave like forms (F08, F09)

## R15
Implements: FR-AUTH-02

The system SHALL render the login fields and submit button inside one `<form>` whose submit event invokes the login submit handler.

## R16
Implements: FR-AUTH-02

The system SHALL set `name`, `autoComplete` (`username` / `current-password`), `spellCheck={false}` and `autoCapitalize="none"` on the login inputs.

## R17
Implements: FR-AUTH-10

The system SHALL render the set-password fields and submit button inside one `<form>` whose submit event invokes the set-password submit handler.

## R18
Implements: FR-AUTH-10

The system SHALL set `name` and `autoComplete="new-password"` on both set-password inputs.

## R19
Implements: FR-AUTH-05

The system SHALL render the admin create-account fields and submit button inside one `<form>` whose submit event invokes the create handler.

## R20
Implements: FR-AUTH-05

The system SHALL set `autoComplete="off"` on the admin create username input and `autoComplete="new-password"` on its temporary-password input, with `spellCheck={false}` and `autoCapitalize="none"` on the username.

## R21
Implements: FR-AUTH-05

The system SHALL render the `AccountRow` rename and reset-password inputs each inside a `<form>` whose submit event invokes the existing rename or reset handler.

## R22
Implements: FR-SHOP-02

The system SHALL render the shopping-item add/edit fields and submit button inside one `<form>` whose submit event invokes the item submit handler.

## R23
Implements: FR-RULE-03

The system SHALL render each of the three rules add forms inside its own `<form>` whose submit event invokes that form's existing save handler.

## R24
Implements: FR-CAND-02, FR-CAND-03

The system SHALL render the recipe authoring fields and submit button inside one `<form>` whose submit event invokes the existing save handler.

## R25
Implements: FR-AUTH-02, FR-CAND-03, FR-SHOP-02

IF a form's submit event fires while its submit is disabled, THEN the system SHALL ignore it.

## R26
Implements: FR-AUTH-02, FR-CAND-03, FR-SHOP-02

WHEN a form's submit event fires while submission is allowed, the system SHALL call `preventDefault` on it before invoking the handler.

## R27
Implements: FR-CAND-03, FR-UX-02

The system SHALL give every non-submit `<button>` inside a `<form>` the attribute `type="button"`.

## Pending state (F10, F11)

## R28
Implements: FR-AUTH-02

WHILE a login request is in flight, the system SHALL show the login submit button with a busy label ending in "…" ("Entrando…").

## R29
Implements: FR-AUTH-10

WHILE a set-password request is in flight, the system SHALL show the submit button with a busy label ending in "…" ("Guardando…").

## R30
Implements: FR-UX-02

WHILE a submit button is disabled, the system SHALL render it with reduced opacity and a `not-allowed` cursor.

## R31
Implements: FR-UX-05

WHILE a guarded mutation is in flight, the system SHALL expose a `pending` flag from the owning hook for that action.

## R32
Implements: FR-CAND-01, FR-LIB-02, FR-SHOP-02, FR-RULE-03, FR-AUTH-05

WHEN a guarded mutation is invoked while the same action is already pending, the system SHALL return without issuing a second request.

## R33
Implements: FR-UX-05

WHILE a guarded mutation is pending, the system SHALL disable the button that triggers it.

## Error banner (F12, F13)

Anchor: FR-UX-07 as amended by G-93 (WCAG 1.4.3 text contrast, 4.1.3 status
messages). Contrast ratios computed with the WCAG relative-luminance formula from
`tokens/colors.js`: `honey` on `honeySoft` = 2.28:1 (fails; today's Week/Library
errors); `ink` on `honeySoft` = 11.03:1; `ink2` on `honeySoft` = 4.82:1.

## R34
Implements: FR-UX-07 (G-93, 4.1.3)

WHEN a form submit or mutation fails, the system SHALL render its error in the shared `Banner` with `role="alert"`.

## R35
Implements: FR-UX-07 (G-93, 1.4.3)

The system SHALL colour `Banner` error text with the `ink` token (#28331F) on a `honeySoft` (#F8E9C6) background, a pair whose computed contrast ratio is 11.03:1 (at least 4.5:1).

## R36
Implements: FR-UX-07 (G-93, 4.1.3)

WHEN a view shows an error, the system SHALL render the `Banner` adjacent to the form or control group whose action failed (directly above its form while an authoring or inline form is open, otherwise directly below the view heading).

## R39
Implements: FR-UX-07 (G-93, 4.1.3)

WHERE a view shows a non-error result message, the system SHALL render it in the shared `Banner` with `role="status"`.

## R40
Implements: FR-UX-01, FR-UX-03, FR-UX-07

The system SHALL take the text of every `Banner` message from the messages catalogue, never from a string literal in a component.

## R41
Implements: FR-UX-07 (G-93, 1.4.1 intent)

The system SHALL convey an error in `Banner` by more than colour: a 4 px solid `honey` left edge and a leading catalogue label (`ERROR_PREFIX`, "Error:").

## R42
Implements: FR-UX-07 (G-93, 1.4.3)

The system SHALL replace these eight error renderings with `Banner`: plain text in `RulesView.jsx:98`, `ShoppingListView.jsx:184`, `SummaryView.jsx:30`, `AdminAccountsView.jsx:59`, `LoginView.jsx:126`, `SetPasswordView.jsx:145`, and `honey` on `honeySoft` in `WeekPlannerView.jsx:44-55`, `LibraryView.jsx:109-121`.

## R43
Implements: FR-UX-07 (G-93, 4.1.3)

IF a view has no error, THEN the system SHALL render no `Banner` and no `role="alert"` element for it.

## Guards

## R37
Implements: FR-UX-07

The system SHALL keep `frontend/src/**/*.jsx` free of `aria-*`, `tabIndex`, accessibility-library imports and any `role` other than `"status"` and `"alert"`.

## R38
Implements: FR-UX-01, FR-UX-03

The system SHALL define every new user-facing string (titles, busy labels, field labels) in the messages module.
