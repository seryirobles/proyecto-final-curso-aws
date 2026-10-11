# frontend_week_generation — Requirements

> Feature 35 · tier 3 · frontend-only. `feature_list.json` `covers` is empty; the
> ids below are the ones the feature's description and acceptance criteria name
> (the `single_recipe_generation` / `library_delete_pin_cascade_ui` precedent).
> Source of truth: `docs/rest_api_contract.md` §3.5 (+ §7 Q3, Q4), FR-AI-03/-04/-05/-08/-09/-11/-12,
> FR-RULE-05, FR-UX-01/-03/-05/-06/-07, NFR-AI-01, US12, US13, G-18, G-19, G-25, G-45, G-93, G-94.
> FR-AI-04 is enforced server-side (`architecture.md` §1.1); the client only passes
> the override and shows the outcome. FR-AI-10 (preview) belongs to single-recipe
> generation and is not touched.

## Scope

In: the week view's entry point, the configuration/confirmation panel, the submit,
the per-slot progress, the skipped-pin report, per-slot failure and retry, resuming a
run after a reload.
Out: any `backend/` change; the single-recipe flow; a list of other users' runs; any
cost information.
Depends on feature 36 `week_generation_backend` (live `slots[]`, run statuses, per-slot
retry route, mode semantics G-94). These requirements follow `rest_api_contract.md` §3.5
as that feature fixes it. Owner decisions of 2026-10-12 are in `design.md` §9.

## Entry point and empty week

## R1
Implements: FR-AI-03, US12

WHILE a live week is displayed in the week view, the system SHALL show a "Generar semana" button directly below the week switcher.

## R2
Implements: FR-UX-05 (G-25)

WHILE every slot of the displayed week has no candidate, the system SHALL show an empty-state message above the day cards that names generating the week as one way to fill it.

## R3
Implements: FR-AI-05

WHEN the user activates the "Generar semana" button, the system SHALL open the generation panel for the displayed week.

## R4
Implements: FR-AI-09, FR-AI-08

WHILE a generation run is submitting or in progress, the system SHALL disable the "Generar semana" button.

## Configuration and confirmation panel

## R5
Implements: FR-AI-05, FR-UX-06

The generation panel SHALL display the target week's designation and its Monday–Sunday date range.

## R6
Implements: FR-AI-11 (G-45)

WHERE the target week is the current week, the generation panel SHALL state that only days from today onward are generated.

## R7
Implements: FR-AI-11 (G-18)

The generation panel SHALL state that existing candidates and definitive meals are not overwritten and that a slot holding a definitive meal is skipped.

## R8
Implements: FR-AI-03 (G-94)

The generation panel SHALL offer exactly three modes (`library_only`, `ai_only`, `mix`) as a single-choice radio group with es-ES labels.

## R9
Implements: FR-AI-03 (G-94)

The generation panel SHALL show a one-line es-ES description beside each mode.

## R10
Implements: FR-AI-03 (G-94)

WHEN the generation panel opens, the system SHALL preselect the `mix` mode.

## R11
Implements: FR-AI-05, FR-AI-04

The generation panel SHALL list the current shared general rules in es-ES.

## R12
Implements: FR-AI-05, FR-RULE-05

The generation panel SHALL offer a control that reveals editors for the rules of this run only.

## R13
Implements: FR-AI-05, FR-RULE-03, FR-RULE-07

The rule editors SHALL use dropdown-only controls whose options come from the `availableOptions` of `GET /v1/rules`.

## R14
Implements: FR-RULE-05

WHEN the user leaves the rule editors untouched, the submitted body SHALL omit `ruleOverride`.

## R15
Implements: FR-RULE-05

WHEN the user has edited the rule editors, the submitted body SHALL carry `ruleOverride` with `categoryCounts` and `disabledDays`.

## R16
Implements: FR-RULE-05

The system SHALL NOT call any `/v1/rules` write endpoint when a run override is edited or submitted.

## R17
Implements: FR-RULE-05

WHEN the generation panel closes, the system SHALL discard the unsubmitted override draft.

## R18
Implements: FR-AI-05

WHEN the user activates the panel's "Generar semana" confirm button, the system SHALL submit the run.

## Submit

## R19
Implements: FR-AI-03, FR-AI-08

WHEN the run is submitted, the system SHALL send `POST /v1/generations` with `type: "week"`, the displayed week's `weekId` from `GET /v1/live-weeks`, and the chosen `mode`.

## R20
Implements: FR-AI-08

The submitted body SHALL NOT contain an `attempt` field.

## R21
Implements: FR-AI-08

WHILE the submit request is in flight, the system SHALL disable the confirm button.

## R22
Implements: FR-AI-12, FR-RULE-07

IF the submit is rejected, THEN the system SHALL keep the panel open and show the server's `detail` in an error banner.

## Progress

## R23
Implements: FR-AI-12 (G-19)

WHEN the submit answers `202`, the system SHALL poll `GET /v1/generations/{generationId}` on a short fixed interval until the run `status` is `completed`, `partial` or `failed`.

## R24
Implements: FR-AI-11

The system SHALL NOT compute which slots a run targets on the client.

## R25
Implements: FR-AI-12, FR-AI-11

WHEN the submit answers `202`, the system SHALL show one progress row per slot of `targets.openSlots` and `targets.pinnedSlots`, labelled with the day and slot in es-ES.

## R26
Implements: FR-AI-12 (G-19)

WHILE an open slot has no `slots[]` entry or its entry is `pending` or `running`, the system SHALL show that slot's row as in progress with a loading message ending in "…".

## R27
Implements: FR-AI-12, FR-UX-07 (4.1.3)

WHILE a run is in progress, the system SHALL announce the count of slots that are `done` or `error` against the count of open slots in a `role="status"` region.

## R28
Implements: FR-AI-11

WHEN a slot is pinned, the system SHALL show its row as filled with the pinned meal.

## R29
Implements: FR-AI-09, FR-AI-12

WHEN some slots are `error` and others `done`, the system SHALL keep showing the `done` slots.

## R30
Implements: FR-AI-11

WHEN a run becomes terminal, the system SHALL refetch the displayed week so the new candidates appear.

## Skipped pins

## R31
Implements: FR-AI-11, FR-AI-12 (G-18)

WHEN the submit response lists `skippedPins`, the system SHALL show a report naming the day and slot of each skipped pin.

## R32
Implements: FR-AI-11

The skipped-pin report SHALL state that the pin was not applied because the slot already holds a definitive meal.

## R33
Implements: FR-AI-11

The skipped-pin report SHALL stay visible until the user closes the run report.

## Failure and retry

## R34
Implements: FR-AI-12, NFR-AI-01

WHEN a slot is `error`, the system SHALL show that slot's `error.message` verbatim in its row, whatever its `error.code`.

## R35
Implements: FR-AI-12, FR-UX-03

IF an `error` slot carries no message, THEN the system SHALL show the generic es-ES error message.

## R36
Implements: FR-AI-12 (G-19)

WHEN a slot is `error`, the system SHALL show a "Reintentar" button in that slot's row only, including when its `error.code` is `insufficient_library_recipes`.

## R37
Implements: FR-AI-12

WHEN the user activates a slot's "Reintentar" button, the system SHALL call `POST /v1/generations/{generationId}/slots/{day}/{slot}/retry` with no body.

## R38
Implements: FR-AI-12

WHEN a retry answers `202`, the system SHALL show that slot as in progress and resume polling.

## R39
Implements: FR-AI-12

WHILE a slot's retry request is in flight, the system SHALL disable that slot's "Reintentar" button.

## R40
Implements: FR-AI-12

IF a polling or retry request fails, THEN the system SHALL show the server's `detail` in an error banner inside the panel.

## R41
Implements: FR-AI-12

WHEN a run is terminal, the system SHALL show a "Cerrar" button that dismisses the run report.

## Navigation, week binding and resume

## R42
Implements: FR-AI-09, FR-UX-06

WHEN the user switches the displayed week or the active tab during a run, the system SHALL keep polling that run.

## R43
Implements: FR-UX-06

WHILE a run's week differs from the displayed week, the system SHALL NOT render that run's panel.

## R44
Implements: FR-AI-12

WHEN the submit answers `202`, the system SHALL store the `generationId`, the `weekId` and the `targets` in `sessionStorage`.

## R45
Implements: FR-AI-12

WHEN the application loads with a stored run, the system SHALL resume polling that run and show its progress.

## R46
Implements: FR-AI-12

WHEN a run's `status` becomes `completed`, `partial` or `failed`, the system SHALL remove the stored run.

## R47
Implements: FR-AI-12

IF reading or writing `sessionStorage` throws, THEN the system SHALL run the generation flow without persistence.

## R48
Implements: FR-AI-12

IF a resumed run answers `404`, THEN the system SHALL remove the stored run without showing an error.

## UX, accessibility, locale

## R49
Implements: FR-UX-07 (2.5.8), FR-UX-02

The system SHALL give every button, radio label and select in the panel the minimum touch-target size from `targetStyle(viewport)`.

## R50
Implements: FR-UX-02 (frontend_ux_phase2)

The progress area SHALL use `weekGridColumns(viewport)` for its column layout.

## R51
Implements: FR-UX-07 (2.4.7)

The panel SHALL use only native `button`, `input[type=radio]`, `select` and `label` elements and no outline override.

## R52
Implements: FR-UX-07 (4.1.3)

The system SHALL render every panel error in the shared `Banner` with `role="alert"`.

## R53
Implements: FR-UX-07 (frontend_ux_phase2 L5 scroll margin)

WHEN the panel opens, the system SHALL scroll it into view with a scroll margin equal to the sticky header plus day strip heights.

## R54
Implements: FR-UX-01, FR-UX-03

The system SHALL take every panel string from the `MESSAGES` catalogue and every date through `formatDate`.

## R55
Implements: FR-UX-07 (4.1.2)

The system SHALL give every form control in the panel a visible text label.
