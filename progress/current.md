# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

- **Feature in progress:** 10 — `generation_request`
- **Started:** 2026-08-26
- **Agent:** spec_author (launched)

## Plan

Feature 9 — `password_policy` — is `done` and committed (`e7ef8f3`), tree
clean. `./init.sh` reports feature 10 — `generation_request` (tier 1,
`sdd: true`, depends_on [6] `rules_model`, done) as the next actionable
feature.

Covers FR-AI-03 (three generation modes: library-only / AI-only / mix),
FR-AI-05 (effective rules = shared rules + optional per-run override, shared
rules untouched), FR-AI-08 (idempotency key from week + slots + effective
rules), FR-AI-11 (target-slot resolution: exclude disabled days, resolve
pinned slots, skip slots already holding a definitive — an existing
definitive outranks a pin and the skipped pin is reported, today-onward
scoping for the current week, category counts describe the week's final
state so existing meals count toward the total).

Per SDD flow: spec_author writes `specs/generation_request/{requirements,design,tasks}.md`,
sets status to `spec_ready`, then STOP for human approval gate.

## Log

- Leader: confirmed feature 9 done/committed, archived session to
  `history.md`, ran `./init.sh` (green, 193 tests) — next actionable
  feature confirmed as 10.
- spec_author: launched against FR-AI-03, FR-AI-05, FR-AI-08, FR-AI-11.

- spec_author: `spec_ready -> specs/generation_request/`. R1-R24, 3 gate
  questions in `design.md` §9. Leader verified `resolve_targets`/
  `idempotency_key`/`build_plan`'s dependencies (`definitive`,
  `SlotContents`, `slots_from`, `apply_override`, `RuleSet`, etc.) against
  the actual code in `domain/{candidate,calendar,rules}.py` — signatures
  match, not guessed.
- Human answered the 3 gate questions: Q1 (SHA-256/canonical JSON) and Q2
  (definitive-only category counts) approved as designed. Q3 overturned the
  recommendation — `mode` SHOULD be part of the idempotency key (switching
  modes over an otherwise-identical request must count as a new request,
  not a duplicate).
- Leader: Q3 requires revising `idempotency_key`'s signature (add `mode`
  as a 4th component), R16 (same-key test must now hold `mode` constant
  too), a new requirement for "different mode -> different key", R24's
  `build_plan` composition (pass `request.mode` through), the coverage map,
  and design.md §6's payload description + gate question 3's resolution
  note. Sent back to spec_author.

- spec_author: revised. R1-R25 (R16 reworded, R24 updated, R25 new — "same
  week/targets/rules, different mode -> different key"). Leader verified
  the revision (coverage map, §9 gate question 3's decision history kept
  visible, not silently rewritten).
- Human approved. `feature_list.json` set to `in_progress` before launching
  the implementer.
- implementer: launched against `specs/generation_request/`.

- implementer: T1-T11 done. `domain/generation.py` and
  `tests/domain/test_generation.py` created. `./init.sh` green: 218 tests
  (193 -> 218, +25). Report: `progress/impl_generation_request.md`.

- reviewer: CHANGES_REQUESTED. 14 mutants planted, 12 killed, 2 survived —
  both real gaps in `idempotency_key` test coverage, not cosmetic: (1) no
  test varies pin *order* between two rule sets, so the `pins` sort in the
  hash payload is untested despite the test's own name claiming it; (2) no
  test varies `targets.pinned_slots` alone, so two genuinely different
  requests (a pinned slot free vs. that same slot already holding a
  definitive, same `open_slots` either way since `skipped_pins` isn't
  hashed) could collide on one idempotency key — undetected key collision,
  the exact failure mode FR-AI-08 exists to prevent. Also: T12 in
  `tasks.md` left unticked despite `./init.sh` having actually passed
  (reported in `progress/impl_generation_request.md`); minor — R6/R7
  (`PinnedTarget`/`SkippedPin`) lack the frozen-instance assertion R2/R8/R20
  have.
- Leader: sent all 4 findings back to the implementer — the 2 real ones are
  a straightforward "add the missing test scenario", not a design change.

- implementer: all 4 findings fixed. Both mutants re-applied and confirmed
  caught by the new tests, then reverted (tree clean). T12 ticked. Finding
  4 (optional frozen-instance tests) also done. `./init.sh` green: 221
  tests (218 -> 221, +3).

## Next step

Ready for human sign-off: review `specs/generation_request/`,
`backend/core/src/planner_core/domain/generation.py`,
`backend/core/tests/domain/test_generation.py` and
`progress/impl_generation_request.md`. Marking `done` and committing are
human-only.
