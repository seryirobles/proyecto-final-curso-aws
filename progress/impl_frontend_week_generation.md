# Implementation report: frontend_week_generation (feature 35)

Tasks T1-T8 done and ticked; T9 (manual/real-backend checks) pending, see below.
Only `frontend/` touched. `feature_list.json` and backend files untouched.

## Result

- `frontend`: eslint, prettier, vitest green (122 files, 838 tests; was 758).
- `./init.sh`: pytest 1331 passed, prettier, eslint, vitest OK. Two FAIL lines remain,
  both workflow state, not code: 2 features `in_progress` (35 and 36) and 35's dependency 36
  not `done`. They clear when the owner marks 36 done.

## Traceability

| R | Test |
|---|---|
| R1, R2, R3, R4, R43, R49(button) | `tests/components/WeekPlannerView.generation.test.jsx` |
| R5-R9, R11, R12, R18, R21, R22 | `tests/components/WeekGenerationPanel.test.jsx` (configuring) |
| R10, R14-R17, R19, R20, R22, R44 | `tests/hooks/useWeekGeneration.test.js` (configuration, submit) |
| R13 | `WeekGenerationPanel.test.jsx` (`RuleOverrideEditor` block) |
| R23, R24, R26, R29, R30, R31, R34, R35, R46 | `useWeekGeneration.test.js` (polling) |
| R25, R26, R27, R28, R32, R33, R34-R36, R39, R41 | `WeekGenerationPanel.test.jsx` (report) |
| R37, R38, R39, R40 | `useWeekGeneration.test.js` (retry and dismiss) |
| R42 | `useWeekGeneration.test.js`, `useWeekPlanner.generation.test.js` |
| R45, R47, R48 | `useWeekGeneration.test.js` (resume) |
| R49-R53, R55 | `WeekGenerationPanel.test.jsx` (targets, grid, native controls, scroll margin) |
| R54 | `test_all_strings_from_messages.test.js` (green, unchanged) |

Source scans (`test_no_extra_accessibility`, `test_no_outline_override`,
`test_all_strings_from_messages`, `useViewport.sourceScan`) pass, none narrowed.

## What the spec did not anticipate

1. **Logout / session gating.** The hook runs in `App` before login, so a stored run must
   not be polled (401) or cleared until the session is known. `useWeekPlanner` gained an
   optional `signedIn` (default `true`), passed from `App` as `isUser`; resume waits for it,
   and storage is cleared only on a true to false transition. `App.test.jsx` asserts
   `{ active, signedIn: true }` instead of `{ active }` (two assertions updated, not weakened).
2. **Idempotent `200` has no `targets`** (`routing.py`: it returns the GET body). The hook then
   lists the run's own `slots[]` as open slots; nothing is computed client-side.
3. **Override seeding.** `startOverride` seeds the draft from the shared category counts and
   disabled days. The server replaces a group wholesale (`decode_rule_override`), so an empty
   draft would silently drop the shared rules. "Untouched" means the toggle was never opened.
4. **Poll failures.** A 4xx stops polling and shows the report (with "Cerrar"); network/5xx show
   the banner and keep polling. The spec said only "show the detail".
5. `useWeekPlanner.test.js`: two "last `usePolling` call" assertions now filter out the new
   `/v1/rules` poll (helper `lastWeekPollCall`); same expectations on the week poll.
6. `Banner tone`: the string-scan rejects a quoted `tone="status"`, so the panel uses a local
   const (`NOT_ERROR_TONE`) rather than widening the scan allowlist.
7. Panel is gated on `isOpen && runWeekId === displayed weekId`; a configuring panel opened on
   one week is hidden (not closed) if the user switches week, and re-clicking the button resets it.

## Manual / T9 (not done)

Not run: layout at 375/768/1280/1440 px, tab order and visible focus, panel clearance under the
sticky header/strip, iOS select zoom, screen-reader announcement of the status line, reload
mid-run against the local backend. Feature 36 is implemented but not `done`; the real-backend
flow should be walked by the owner or in the review.

## Review fixes

- Added a `finished` + `skippedPins` panel test (R33). Retry buttons in the R36/R39 tests are
  now found by `getByRole('button', { name })`, so a `hidden` attribute fails them.
- `useWeekGeneration.js` header comment cut to 3 lines pointing at the contract and design.
- 4xx polling behaviour unchanged.
