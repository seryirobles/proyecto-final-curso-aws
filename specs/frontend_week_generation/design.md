# frontend_week_generation — Design

Layer: all `frontend/` (React, inline styles, hook-per-view, `docs/architecture.md` §3). No
`architecture.md` §2 item is decided here. Components stay pure; state, polling and request
shaping live in hooks. Which slots a run targets, the pin resolution and the rule satisfiability
stay server-side (§1.1): the client displays `targets` and `availableOptions`, it never derives them.

## 1. Files touched

New:
- `hooks/useWeekGeneration.js` — `useWeekGeneration({ active, weekId, designation, onSettled })`.
  State machine `closed | configuring | submitting | running | finished`; holds `mode`
  (default `'mix'`), `overrideDraft | null`, `targets`, `slotStatuses`, `error`, `runWeekId`.
  Returns `{ phase, isOpen, mode, setMode, overrideDraft, startOverride, setCategoryCount,
  setDisabledDays, open, close, submit, retrySlot, dismiss, targets, slots, skippedPins, error,
  rules, availableOptions }`. Reads `GET /v1/rules` through the existing `usePolling('/v1/rules',
  undefined, { enabled: isOpen })` (conditional GET, options stay fresh while open). Polls the
  generation on its own timer (`AI_POLL_INTERVAL_MS` from `useAiGeneration.js`, exported already):
  `GET /v1/generations/{id}` is **not** conditional-GET pollable (contract §3.6 last paragraph).
  A bumped run id makes late responses inert, the `useAiGeneration` idiom (R41 there). Submit and
  retry go through `usePendingGuard` (`submit`, `retry:<day>-<slot>`), the in-flight guard of phase 1.
- `components/WeekGenerationPanel.jsx` — presentational, in-flow titled `<section>` (like
  `CandidateAuthoring`), three sub-states: configuring, running/finished report. Pure function of props.
- `components/RuleOverrideEditor.jsx` — two dropdown editors (category count, disabled day),
  `selectStyle`, same shape as the `RulesView` forms but writing to a local draft, never a PUT.
- Tests, `tests/hooks/useWeekGeneration*.test.js`, `tests/components/WeekGenerationPanel*.test.jsx`,
  `RuleOverrideEditor.test.jsx`, `WeekPlannerView.generation.test.jsx`.

Changed:
- `hooks/useWeekPlanner.js` — calls `useWeekGeneration` and returns it as `generation`
  (`onSettled: weekPoll.refetchNow`). It runs in `App` on every render, so a run survives a tab or
  week switch (R40), exactly like the planner's own state; `active` gates only the rules poll.
- `components/WeekPlannerView.jsx` — "Generar semana" button below `WeekSwitcher`; week-level
  `EmptyState` above the grid when every slot `isEmpty` (R2); renders the panel when
  `generation.runWeekId` equals the displayed week (R41).
- `messages/es-ES.js` — new `WEEK_GEN_*` keys (§4). `domain/labels.js` — `MODE_LABELS` (data, like `UNIT_LABELS`).

Reused as is: `WeekLabel`, `Banner`, `EmptyState`, `LoadingState`, `useScrollIntoView`,
`usePendingGuard`, `handleFormSubmit`, `describeRule` and `computeRuleId` (`useRules.js`),
`weekGridColumns`, `targetStyle`, `selectStyle`, `primaryButtonStyle`, `secondaryButtonStyle`,
`cardStyle`, `headingStyle`, `CATEGORY_LABELS`, `DAY_LABELS`, `SLOT_LABELS`, `formatDate`.
No new component duplicates an existing one; `ConfirmDialog` is deliberately not reused (§7 alt. 1).

## 2. Request shaping

```js
// body -> POST /v1/generations   (no `attempt`, R19)
{ type: 'week', weekId, mode, ...(overrideDraft ? { ruleOverride: { categoryCounts, disabledDays } } : {}) }
// retry -> POST /v1/generations/{id}/slots/{day}/{slot}/retry   (contract §7 Q4, R37)
```
`weekId` is `liveWeeks[designation].weekId`, never computed (contract §2). `categoryCounts` is
`[{ category, count }]`, `disabledDays` is `number[]` (contract §3.5).

## 3. Panel states (per slot)

Vocabulary is the contract's §3.5 as fixed by feature 36: slot `pending|running|done|error`, run
`pending|running|completed|partial|failed`, `error: { code, message }`. Pinned slots are not in `slots[]`.

| Server fact | Row shows |
|---|---|
| in `targets.pinnedSlots` | "Plato fijado" (filled at submit) |
| open slot with no `slots[]` entry, or `pending`/`running` | "Generando…" |
| slot `done` | "Listo" |
| slot `error` | `error.message` verbatim + "Reintentar" |
| in `targets.skippedPins` | separate report block, not a slot row (R31-R33) |

Progress count = open slots that are `done` or `error`, over `targets.openSlots.length`. Polling stops on
`completed`/`partial`/`failed`; a retry `202` returns the GET body (run back to `running`), so polling
restarts. `error.code` is never used for display (the message is already es-ES); it is not branched on.

**Retry on `insufficient_library_recipes` is shown, like any `error`.** The contract allows it, and it is
useful when the user adds recipes to the library (Library tab) in the meantime; if the library has not changed
it fails again with the same message. Hiding it for that code would add a client rule the contract does not
state, and a plain-language message ("…añade recetas a la biblioteca o usa el modo mixto") comes from the server.

**Resume (R44-R48).** `sessionStorage` key `planner.weekGeneration` holds `{ generationId, weekId, targets }`
(tab-scoped, so no cross-user leak after logout in another tab; cleared on logout and on terminal status).
Access goes through a tiny `readStoredRun/writeStoredRun/clearStoredRun` trio in the hook file, each wrapped in
try/catch. On mount with a stored run the hook enters `running` and polls; the first GET fills the rows.

## 4. UX decisions

Guidelines fetched 2026-10-11 from the Vercel Web Interface Guidelines `command.md` (fetch
succeeded, 8 KB). The owner rulings of phases 1–2 override it where noted: `test_no_extra_accessibility`
bans `aria-*`, `tabIndex` and any `role` other than `status`/`alert` (G-93); hover, focus-visible
styling and reduced motion are deferred until the planned global stylesheet exists.

| Decision | Choice | Justification |
|---|---|---|
| Entry point | `primaryButtonStyle` button "Generar semana" right under `WeekSwitcher`, above the grid; not added to Summary (owner 2026-10-12) | Guideline "`<button>` for actions"; "Specific button labels". Precedent: `SUMMARY_EDIT_WEEK` shortcut sits right after the heading. Week-scoped action next to the week label keeps the week unambiguous (FR-UX-06). |
| Empty week | `EmptyState` above the grid: "…añade un plato o genera la semana" | Guideline "Handle empty states"; G-25 wording; `EmptyState` precedent in every view. |
| Container | In-flow titled `<section>` above the grid, scrolled into view, not a modal | Precedent: phase 1 P1-F authoring forms are in-flow sections; phase 2 §1 says overlays are Phase 3 and F24 (90vh sheet, safe area) is open. Guideline "`overscroll-behavior: contain` in modals" is avoided by not adding a modal. |
| Mode picker | Native radio group in a `<fieldset><legend>`, three labelled options each with a one-line description, `mix` preselected | Guideline "Checkboxes/radios: label + control share single hit target"; "Semantic HTML before ARIA" (a `fieldset` needs no ARIA, so the G-93 ban holds). |
| Mode copy | "Solo mis recetas" (library_only): "Usa únicamente recetas de la biblioteca; los huecos que no pueda cubrir quedan con error." · "Solo con IA" (ai_only): "Genera recetas nuevas para todos los huecos." · "Mixto (recomendado)" (mix): "Usa primero las recetas de la biblioteca y genera con IA solo las que falten." | G-94; guideline "Specific button labels"/"Error messages include fix/next step". Wording is a proposal for the approval gate. |
| Rule display | Read-only list via `describeRule` | FR-AI-05 "displaying the current general rules"; reuses the Rules view wording. |
| Override control | Disclosure button "Editar reglas solo para esta generación" revealing `RuleOverrideEditor` (selects + "Añadir"/"Quitar" like `RulesView`) | FR-AI-05/FR-RULE-03 dropdown-only; guideline "Form controls need `<label>`"; options from `availableOptions` (FR-RULE-07, no client re-derivation). Copy states "no cambia las reglas compartidas". |
| Confirmation | The panel's explicit primary button "Generar semana" is the confirmation prompt (owner 2026-10-12); the panel states week, rules, mode and that nothing existing is overwritten | FR-AI-05. Guideline "Destructive actions need confirmation" does not apply: the run only adds (FR-AI-11). |
| Submit state | Button disabled via `usePendingGuard`, label "Generando la semana…" while in flight | Guideline "Submit button stays enabled until request starts; spinner during request" and "Loading states end with `…`"; phase 1 R31–R32 double-tap guard (FR-AI-08). |
| Progress | `weekGridColumns(viewport)` grid of day cards, each with its two slot rows; `role="status"` text "3 de 14 huecos listos" | Guideline "Async updates need `aria-live="polite"`" → `role="status"` is the only live region the repo allows (G-93, FR-UX-07 4.1.3). Same grid as the week keeps the mental model (phase 2 L4). |
| Retry | "Reintentar" `secondaryButtonStyle` button in the failed row only; disabled while in flight | G-19 "per-slot retry"; guideline "Error messages include fix/next step". |
| Skipped-pin report | `Banner tone="status"` listing "Lunes · Comida: la regla fijada no se ha aplicado porque ya hay un plato definitivo", persistent until "Cerrar" | FR-AI-11 "reported, never applied silently". `Banner` ink-on-honeySoft with edge, not colour-only (phase 1 R34–R43). |
| Errors | Submit/poll/retry failures: `Banner` (`role="alert"`) inside the panel, directly above the buttons; slot failures inline in their row | Phase 1 R36 per-form placement; guideline "Errors inline next to fields". Server `detail` shown verbatim (existing rule, `useAiGeneration` `toDetail`). |
| Kill-switch / cap | No client logic: slot message from the server (`AI_GENERATION_UNAVAILABLE`, FR-AI-12/NFR-AI-01) shown verbatim | Issue 13 analysis: "The frontend hides nothing: it shows the server's `detail` / `result.error.message` as-is". |
| Loading | `LoadingState` message "Cargando las reglas…" while the rules poll has no data; shimmer reused | FR-UX-05; guideline "Loading states end with `…`". |
| Keyboard + focus | Native controls only, DOM order = visual order; no `autoFocus`, no focus trap, no `tabIndex`; panel `scrollIntoView` with `scrollMarginTop = headerHeight + dayStripHeight` | Guideline "`autoFocus` sparingly… avoid on mobile"; "Sticky headers must not cover the focused element"; "Never `outline: none`" (`test_no_outline_override`). Focus return after "Cerrar" is the browser default. |
| Touch targets | `targetStyle(viewport)` on every button, radio label and select; 44 px under 768 px, 24 px above | Guideline "`touch-action: manipulation`" is a stylesheet item deferred with the stylesheet; target size is FR-UX-07 2.5.8 and phase 2 Q-D. |
| Responsive tiers | compact/narrow: one column, panel full width; medium: 4 columns; wide: 7 (via `weekGridColumns`). Selects use `tokens.fontSize.input` so iOS does not zoom | Phase 2 L4; phase 1 R7 zoom rule. |
| es-ES copy | Sentence case ("Generar semana"), verbs in the infinitive like "Generar receta"; counts as numerals via `formatNumber`; "…" not "..."; dates via `formatDate` | Guideline "Use `Intl.*`", "Numerals for counts", "Active voice"; the "Title Case" guideline is English-specific and the catalogue uses sentence case (FR-UX-03). |
| URL state | Panel/run state is **not** in the hash; the in-flight run lives in `sessionStorage` | Guideline "URL reflects state" is met for the view (`#/semana`, phase 2 L7); a run id is transient and per-tab, so it is stored, not shared by link. |

Catalogue keys (proposed): `WEEK_GEN_BUTTON`, `WEEK_GEN_PANEL_TITLE`, `WEEK_GEN_MODE_LEGEND`,
`WEEK_GEN_MODE_LIBRARY`, `WEEK_GEN_MODE_AI`, `WEEK_GEN_MODE_MIX`, `WEEK_GEN_CURRENT_NOTE`,
`WEEK_GEN_MODE_*_HELP` (three), `WEEK_GEN_RULES_TITLE`, `WEEK_GEN_OVERRIDE_TOGGLE`, `WEEK_GEN_OVERRIDE_NOTE`,
`WEEK_GEN_KEPT_NOTE` ("No se sobrescribe ningún plato existente"), `WEEK_GEN_CONFIRM`, `WEEK_GEN_SUBMITTING`, `WEEK_GEN_PROGRESS(done,total)`, `WEEK_GEN_SLOT_PINNED`,
`WEEK_GEN_SLOT_RUNNING`, `WEEK_GEN_SLOT_DONE`, `WEEK_GEN_RETRY`, `WEEK_GEN_SKIPPED_TITLE`,
`WEEK_GEN_SKIPPED_ITEM(day,slot)`, `WEEK_GEN_CLOSE`, `WEEK_GEN_EMPTY_WEEK`.

## 5. Exceptions

`ApiError` from the client is surfaced as `err.detail` (`toDetail`); anything else is `GENERIC_ERROR`.
No new exception class. A `409`/`422` on submit keeps the panel open and the draft intact.

## 6. Dependency

Feature 35 `depends_on` 36 `week_generation_backend`, which delivers the live `slots[]`, the run statuses
(`pending|running|completed|partial|failed`), the per-slot retry route with `404 GENERATION_NOT_FOUND`,
`404 GENERATION_SLOT_NOT_FOUND`, `409 SLOT_NOT_RETRYABLE`, and the mode semantics of G-94. This UI is specified
against that contract; the real-backend check (T9) runs once 36 is done. The contract and the backend are not edited here.

## 7. Rejected alternatives

1. **Reuse `ConfirmDialog` (modal) with a long body.** It renders a bare message and two buttons with no scroll
   limit and no title; a mode picker, a rules list and a dropdown editor in it would overflow a 375 px
   viewport, which is the open F24 problem. It would also stop the user seeing the week behind it while reading rules.
   The in-flow panel matches the authoring-form precedent.
2. **Show progress inside each `DaySlot` card.** It uses the day cards the user already scans, but `DaySlot`/`MealCard`
   would take new props and states, the skipped-pin report and the "n de m" status would still need a home, and the
   cards are not visible on the compact tier when the strip scrolls. A panel grid with the same columns gives the
   mapping without touching the cards.
3. **Refactor `useAiGeneration`'s poll loop into a shared helper.** It would remove about 20 duplicated lines, but the
   single-recipe hook is `done`, covered by many tests, and its result handling differs (one record, a preview). The
   week hook keeps its own small loop and reuses only the exported interval; unification can follow later.

## 8. Test approach (Vitest + RTL, no snapshots, existing setup)

Hook tests first with a stubbed `apiFetch` (pattern: `useLibrary.pinCascade.test.js`): body shape per mode, `ruleOverride`
present/absent, no `attempt`, no `/v1/rules` write, skipped pins from the 202, polling stops when terminal and on
unmount/week switch, retry path, sessionStorage resume/clear/throwing storage (R44-R48), refetch on terminal, rejected submit keeps the panel open. Component tests per
`viewport` prop: button placement, radio group, labels, `targetStyle`, `weekGridColumns`, `role="status"`/`alert`,
retry only in failed rows. Source scans stay green (`test_no_extra_accessibility`, `test_no_outline_override`,
`test_all_strings_from_messages`). **Only manual/visual:** layout at 375 / 768 / 1280 / 1440 px, tab order and visible
focus, panel not hidden under the sticky header/strip, iOS select zoom, screen-reader announcement of the status line,
the real flow against the local backend once feature 36 is done. Recorded in `progress/impl_frontend_week_generation.md`.

## 9. Owner decisions (2026-10-12)

1. Backend first: feature 36 `week_generation_backend`; 35 depends on it. No fake-server substitute.
2. Slot vocabulary is the contract's (`pending|running|done|error`, `error{code,message}`).
3. Run statuses `pending|running|completed|partial|failed`; polling stops on the last three.
4. Modes per G-94; `mix` preselected (use existing recipes first, AI tops up).
5. The panel's own confirm button is the FR-AI-05 confirmation prompt; no extra modal.
6. The in-flight run is kept in `sessionStorage` and resumed after a reload.
7. No cost information anywhere in the UI.
8. `ruleOverride` as proposed; a server `422 UNSATISFIABLE_RULE_SET` is shown in the banner.
9. No entry point in the Summary view.

Open: none new.
