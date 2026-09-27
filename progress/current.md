# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

- **Feature 29:** `done` (owner marked it, no longer in progress).
- **Issue in progress:** 1 `rule-creation-400-invalid-request` — fixed,
  reviewed, **APPROVED** (0 findings, 0 mutants survived), `reviewed: true`
  set, awaiting the owner's `done`
- **Started:** 2026-09-27
- **Agent:** _—_

## Plan

Feature 28 `single_recipe_generation` marked `done` by the owner (2026-09-27).
`sdd: true`: `spec_author`, then stop at the human gate. After 29:
30 `library_delete_pin_cascade_ui` (also `sdd: true`, same pattern).

## Log

- 2026-09-27: `spec_author` wrote `specs/rules_dropdown_constraints_wiring/`
  (requirements.md R1-R12, design.md, tasks.md). Proposes `GET /v1/rules`
  gain a sibling `availableOptions` object (`maxCountByCategory`,
  `daysAvailableForPin`, `daysAvailableToDisable`), read verbatim off the
  existing pure functions in `rules.py` — no new domain logic. Backend:
  one `encode_available_options()` in `serialization.py` + one field in
  `routing.py`'s `_list_rules`. Frontend: narrows `useRules.js`'s count/
  pin-day/disable-day drafts to the API-reported options, drops the stale
  `RULE_COUNT_OPTIONS` constant; category select and pin's slot select stay
  unconstrained (no pure function bounds them). Feature 27's 422
  `UNSATISFIABLE_RULE_SET` path is untouched. `feature_list.json` id 29:
  `pending` → `spec_ready` (verified: `git diff` touched only that field).

- 2026-09-27: `implementer` completed T1-T10. Backend:
  `serialization.py::encode_available_options`, wired into `routing.py`'s
  `_list_rules`. Frontend: `useRules.js` derives `categoryCountOptions`/
  `pinDayOptions`/`disabledDayOptions` from `availableOptions`, drops
  `RULE_COUNT_OPTIONS`; `RulesView.jsx` renders the three selects from the
  new props. `./init.sh` green (1036 backend + 472 frontend tests).
  See `progress/impl_rules_dropdown_constraints_wiring.md`.

- 2026-09-27: reviewer CHANGES_REQUESTED — 2 surviving mutants in
  `setCategoryCountCategory` (`useRules.js`). Added one test covering the
  "keep the draft" branch at the exact-max boundary
  (`useRules.test.js::changing category keeps a count draft the new
  category still covers, including at its exact max`). Both named mutants
  now killed (verified, reverted). `./init.sh` frontend gate green (473
  tests).

- 2026-09-27: cheap re-verification (reviewer re-applied only the 2 named
  mutants, both now killed) → **APPROVED**, 0 findings.

- 2026-09-27: owner reported issue 1 (`PUT /v1/rules/{id}` → 400 "La
  solicitud no es válida", any rule type, found testing feature 29) →
  logged to `issue_list.json` (`reported`) → `issue_triager` launched to
  find root cause and stage tests in `issues/rule-creation-400-invalid-request/`.

- 2026-09-27: triage complete, `pending`. **Not a feature 29 regression** —
  `computeRuleId` (`useRules.js:16-19`) has built ids with an unencoded `#`
  since feature 20 (`80e34a8`, 2026-09-14); the `#` is a URL fragment
  delimiter, so the browser sends only the part before it (`PUT
  /v1/rules/cat`), and the server compares it to the full id and 400s.
  Server also never percent-decodes `{ruleId}`, so even a correctly
  encoded URL would still fail. Rule create has never worked from the
  browser since feature 20. `covers`: FR-RULE-03, -04, -06. Classification:
  `defect`. Root cause, tests, repro, fix design in
  `issues/rule-creation-400-invalid-request/{analysis,plan,tasks}.md`.
  **Open scope question (owner):** rule delete is broken by the identical
  cause but was never reported (no rule could be created to delete one) —
  general fix (encode+decode both PUT and DELETE, one shared helper) vs.
  specific fix (PUT only, delete spun out as its own issue).

- 2026-09-27: owner answered both — **general fix** (PUT + DELETE, one
  shared encode/decode fix) and **go**. `issue_list.json` id 1:
  `pending` → `approved` → `in_progress` (leader, targeted edits).
  `implementer` launched against `issues/rule-creation-400-invalid-request/`'s
  plan: `handler.py:77` percent-decodes `pathParameters`; `useRules.js:109`
  and `:132` wrap `computeRuleId(rule)` in `encodeURIComponent`.

- 2026-09-27: `implementer` completed T1-T5. Staged tests moved verbatim
  (confirmed byte-identical), 6 backend + 4 frontend reproduction tests
  red before the fix. Backend: `handler.py` percent-decodes each
  `pathParameters` value (`urllib.parse.unquote`) before routing — one
  site covers PUT, DELETE and the local server. Frontend: `useRules.js`
  wraps `computeRuleId(rule)` in `encodeURIComponent(...)` in both the PUT
  and DELETE URL builds. Corrected the stale pre-fix-URL literals named in
  `plan.md`: `useRules.test.js` lines 67, 86, 103, 122 and
  `useRules.mutationVisibility.test.js:37`. `./init.sh` green (1043
  backend + frontend suites). See
  `progress/impl_rule-creation-400-invalid-request.md`.

- 2026-09-27: reviewer APPROVED — 0 findings, 0 mutants survived. Verified
  the two issue-specific requirements `docs/issues.md` adds for bug fixes:
  moved tests byte-identical to staged originals, and reverting either half
  of the fix (`handler.py`'s `unquote`, either `encodeURIComponent` wrap)
  makes the reproduction tests fail again. T9 truncated-id guard stayed
  green throughout. `issue_list.json` id 1: `reviewed: true` set (leader,
  targeted edit); `status` stays `in_progress` per `docs/issues.md` (only
  the human moves it to `done`).

## Next step

Owner: mark issue 1 `done` and commit (fix + feature 29 together, or
separately — your call). Then next: feature 30
`library_delete_pin_cascade_ui` (`sdd: true`, spec_author → human gate).
