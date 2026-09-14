# frontend_spa — Requirements

> Feature 20 · tier 4. Translates the 16 `FR-*` ids in this feature's
> `feature_list.json` `covers` array into EARS requirements. Several other
> `FR-*` ids are **rendered by this SPA but owned (covered, tested) by earlier
> features** — `design.md` §1 names each one explicitly as "consumed, not
> owned", the pattern already established on `specs/ai_lambda/design.md`
> (`FR-CAND-04` cited-not-owned). This file writes no `R<n>` for those; doing
> so would re-claim traceability another feature already carries.
>
> **Fold, 2026-09-13 (owner ruling on the spec-gate questions):** Login, the
> mandatory set-password step, and the admin account-management view are
> **in scope**. `R23`–`R37` implement the `FR-AUTH-*` ids these three screens
> render — all owned by feature 15 `auth_flow` (domain) and feature 16
> `rest_api_lambda` (the `/v1/session*` and `/v1/users*` routes, both
> `done`). Same convention as `FR-CAND-04` above: each `Implements:` line
> cites the `FR-AUTH-*` id, none is added to `covers`. `depends_on` is
> unchanged (`[16, 26]`) — feature 16 alone already owns every route these
> screens call; feature 15 is reached transitively through it, never
> directly.

## R1
Implements: FR-MENU-01

The system SHALL render each live week (current and next) as seven days
(Monday–Sunday), each day holding a lunch slot and a dinner slot.

## R2
Implements: FR-MENU-07

The system SHALL provide a control that switches the displayed live week
between the current week and the next week.

## R3
Implements: FR-MENU-07

WHEN the user switches the displayed live week, the system SHALL render the
selected week through the same week-view component already used for the
other live week.

## R4
Implements: FR-MENU-04

WHEN a user clicks a displayed meal, the system SHALL open a recipe detail
view showing its ingredients with quantities, tools, procedure, estimated
time, and number of servings.

## R5
Implements: FR-MENU-05

The system SHALL make the recipe detail view (R4) reachable from every place
a meal is rendered: a day's candidates, a slot's definitive meal, the weekly
summary, and the library.

## R6
Implements: FR-CAND-02

WHEN a user adds or edits a candidate meal, the system SHALL offer exactly
three authoring methods: picking an existing library recipe, writing a new
recipe from scratch, or generating one with AI.

## R7
Implements: FR-CAND-03

WHEN a user adds or edits a library recipe, the system SHALL offer the
"write from scratch" and "generate with AI" authoring methods used for
candidate authoring (R6).

## R8
Implements: FR-CAND-03

The system SHALL NOT offer the "pick an existing library recipe" authoring
method when authoring a library recipe.

## R9
Implements: FR-LIB-01

The system SHALL display every recipe in the shared library regardless of
its author.

## R10
Implements: FR-LIB-02

The system SHALL allow a user to add, edit, or remove a library recipe using
the authoring methods of R7.

## R11
Implements: FR-LIB-04

The system SHALL provide a search-by-name control for library recipes in the
library view.

## R12
Implements: FR-LIB-04

The system SHALL provide the same search-by-name control as R11 in every
other flow where a user picks an existing library recipe: candidate
library-pick authoring, the AI reference-recipe picker, and a rule's
pin-recipe picker.

## R13
Implements: FR-LIB-04

The system SHALL provide a filter by ingredient category in the library
view.

## R14
Implements: FR-LIB-04

The system SHALL NOT offer any library filter other than the name search
(R11) and the ingredient-category filter (R13).

## R15
Implements: FR-UX-01, FR-UX-03

The system SHALL render every user-facing string — including validation,
error, and system messages — in Castilian Spanish, sourced from the single
frontend messages module.

## R16
Implements: FR-UX-03

WHEN displaying a date or a number, the system SHALL format it with
`Intl.DateTimeFormat` / `Intl.NumberFormat` pinned to the `es-ES` locale
constant.

## R17
Implements: FR-UX-02

WHERE a layout requires a genuine breakpoint, the system SHALL derive the
applicable layout state from `window.matchMedia` rather than a value
hard-coded in a component.

## R18
Implements: FR-UX-04

IF a user initiates a destructive action — removing a library recipe, a
candidate, a shopping-list item, a rule, or a user account, or
replacing/clearing a slot's definitive meal — THEN the system SHALL require
an explicit confirmation before performing it.

## R19
Implements: FR-UX-05

WHILE a view has no content to display (an empty library, a day with no
candidates, an empty shopping list), the system SHALL render a defined empty
state with guidance.

## R20
Implements: FR-UX-05

WHILE an operation that can be slow is in progress, the system SHALL render
a defined loading state.

## R21
Implements: FR-UX-06

WHILE displaying a week view, a week summary, or an action scoped to one
live week, the system SHALL display that week's designation (current/next)
and its Monday–Sunday date range.

## R22
Implements: FR-UX-07

The system SHALL NOT implement any accessibility affordance beyond the
browser's own defaults: no custom ARIA annotations, no custom
keyboard-navigation scheme, no contrast adjustment.

## R23
Implements: FR-AUTH-09

WHEN the application loads, the system SHALL determine whether the browser
already holds an authenticated session before rendering any other view.

## R24
Implements: FR-AUTH-02

WHILE no authenticated session exists, the system SHALL render a login
screen with a username field, a password field, and a submit control.

## R25
Implements: FR-AUTH-02

WHEN a user submits the login screen, the system SHALL call the login
endpoint with the entered username and password.

## R26
Implements: FR-AUTH-10

WHEN a login response or the session-existence check of R23 indicates the
account's password reset is pending, the system SHALL render the
set-password screen instead of the account's role-based view.

## R27
Implements: FR-AUTH-10

WHEN a user submits the set-password screen, the system SHALL call the
set-password endpoint with the entered new password.

## R28
Implements: FR-AUTH-04

The system SHALL NOT provide any control for changing an authenticated
account's own password other than the set-password screen of R26/R27.

## R29
Implements: FR-AUTH-03

The system SHALL NOT provide a self-registration control.

## R30
Implements: FR-AUTH-01, FR-AUTH-05

WHEN the authenticated role is Admin, the system SHALL render the admin
account-management view as the only navigable view.

## R31
Implements: FR-AUTH-06

WHEN the authenticated role is User, the system SHALL NOT render the admin
account-management view or any navigation control to it.

## R32
Implements: FR-AUTH-09

The system SHALL provide a logout control, reachable from every
authenticated view, that calls the logout endpoint.

## R33
Implements: FR-AUTH-12

The system SHALL render, in the admin account-management view, a list of
every account showing its username, its role, and whether its password
reset is pending.

## R34
Implements: FR-AUTH-05, FR-AUTH-12

The system SHALL provide, from the admin account-management view, controls
to create an account, rename an account, reset an account's password, and
remove an account.

## R35
Implements: FR-AUTH-18

The system SHALL NOT offer a role selector in the account-creation control.

## R36
Implements: FR-AUTH-18

The system SHALL NOT offer a removal control on an admin-role account's
row.

## R37
Implements: FR-AUTH-04, FR-AUTH-18

The system SHALL NOT render a reset-password control on the acting admin's
own row in the admin account list.

---

## Coverage check

| `FR-*` (covers array) | `R<n>` |
|---|---|
| FR-MENU-01 | R1 |
| FR-MENU-04 | R4 |
| FR-MENU-05 | R5 |
| FR-MENU-07 | R2, R3 |
| FR-CAND-02 | R6 |
| FR-CAND-03 | R7, R8 |
| FR-LIB-01 | R9 |
| FR-LIB-02 | R10 |
| FR-LIB-04 | R11, R12, R13, R14 |
| FR-UX-01 | R15 |
| FR-UX-02 | R17 |
| FR-UX-03 | R15, R16 |
| FR-UX-04 | R18 |
| FR-UX-05 | R19, R20 |
| FR-UX-06 | R21 |
| FR-UX-07 | R22 |

Every `SHALL`/`SHALL NOT` count is 1 per `R<n>`, checked mechanically before
finalizing (the `week_calendar` R4/R8/R16/R22 lesson, `docs/specs.md`).

### `FR-AUTH-*` — cited, not in `covers` (2026-09-13 fold, see the note at the
top of this file)

| `FR-*` (owned by feature 15/16, `done`) | `R<n>` |
|---|---|
| FR-AUTH-01 | R30 |
| FR-AUTH-02 | R24, R25 |
| FR-AUTH-03 | R29 |
| FR-AUTH-04 | R28, R37 |
| FR-AUTH-05 | R30, R34 |
| FR-AUTH-06 | R31 |
| FR-AUTH-09 | R23, R32 |
| FR-AUTH-10 | R26, R27 |
| FR-AUTH-12 | R33, R34 |
| FR-AUTH-18 | R35, R36, R37 |

`FR-AUTH-07/-08/-11/-13/-14/-16` render nothing of their own in this SPA
(bootstrap provisioning, session-invalidation bookkeeping, the "unknown
user" reattribution, the 30-day expiry clock) — `design.md` §5a names them
as consumed-silently, same as `FR-CAND-05`/`-08` in the table above.
