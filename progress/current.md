# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

- **Feature in progress:** 13 — `rollover_job_logic`
- **Started:** 2026-08-26
- **Agent:** spec_author (launching)

## Plan

Feature 12 (`ai_output_validation`) is `done` and committed (`78b4600`), tree
clean. `./init.sh` reports feature 13 — `rollover_job_logic` (tier 1,
`sdd: true`, depends_on [8] `shopping_list_state`, pending) as the next
actionable feature.

Covers FR-MENU-06, FR-MENU-08, FR-ARCH-01, FR-ARCH-02, FR-SHOP-09: the
five-step week rollover as a pure, re-runnable (idempotent) state
transition — archive the ending week, snapshot the shopping list, promote
next to current, initialize a new empty next week, clean bought items.

Per SDD flow: spec_author writes
`specs/rollover_job_logic/{requirements,design,tasks}.md`, sets status to
`spec_ready`, then STOP for human approval gate.

## Log

- Leader: confirmed feature 12 done/committed, archived session to
  `history.md`, ran `./init.sh` (green, 277 tests) — next actionable
  feature confirmed as 13.
- spec_author: launched against `FR-MENU-06`, `FR-MENU-08`, `FR-ARCH-01`,
  `FR-ARCH-02`, `FR-SHOP-09`.

- spec_author: `spec_ready -> specs/rollover_job_logic/`. R1-R13 in new
  `domain/rollover.py`: `ArchivedWeek`, `RolloverResult`, `archive_week`,
  `promote_next_to_current`, `init_empty_next_week`, `roll_over` — the
  five-step transition as one pure, total, deterministic function reusing
  `shopping.unchecked_items` for cleanup (no reimplementation). 5 rejected
  alternatives (§6), two gate questions (§7). Mid-session it ran a full
  `json.dump` rewrite of `feature_list.json` (would have reformatted the
  whole file), caught it, ran `git checkout -- feature_list.json` to
  discard, self-reported doing so *before* checking `git status` first —
  redid the edit as a minimal one-line `Edit`. Leader verified: HEAD was
  already at `78b4600` with `feature_list.json` clean before spec_author
  touched it, and the post-session diff is exactly the intended one-line
  status change — nothing lost. Noting this as a near-miss, not an incident.

## Gate questions for the human (specs/rollover_job_logic/design.md §7)

1. **`FR-MENU-08`'s "safely retryable after partial failure," read as "pure
   deterministic recompute" rather than literal crash-between-steps
   simulation — accepted at this tier?** `domain/` has no IO to be
   interrupted mid-write (`docs/architecture.md` §3), so nothing here can
   leave a partial value; `roll_over` either returns one complete result or
   nothing. Same treatment `shopping_list_state` already gave `FR-SHOP-10`'s
   serialization clause. spec_author recommends accepting it here, with a
   **fuller** test (an actual persisted write interrupted and retried)
   belonging to whichever feature 14+ persistence feature first gives
   `roll_over` a real IO-bearing caller. If rejected: this feature is
   blocked — there's no smaller fix available at this tier without smuggling
   persistence machinery (a step-cursor) into `domain/`.

2. **Should `RolloverResult` carry the new current/next weeks' `IsoWeek`
   identities, or leave the caller to derive them via
   `IsoWeek.following`?** No `FR-*` requires it either way. spec_author
   recommends leaving it out (rejected alternative E) — the caller already
   has what it needs.

- Human: approved both as recommended — pure-recompute interpretation of
  `FR-MENU-08` accepted; `IsoWeek` identities left off `RolloverResult`
  (no change from spec). Status set to `in_progress`.
- implementer: launching against `specs/rollover_job_logic/`.

**Feature in progress: 13 — rollover_job_logic**
**Plan:** tasks T1..T9 from `specs/rollover_job_logic/tasks.md`.

- implementer: T1-T9 done. New `backend/core/src/planner_core/domain/rollover.py`
  (`ArchivedWeek`, `RolloverResult`, `archive_week`, `promote_next_to_current`,
  `init_empty_next_week`, `roll_over`) matching design.md §4 verbatim, plus
  `backend/core/tests/domain/test_rollover.py` (17 tests, R1-R13). `./init.sh`
  green: 294 passed (was 277). No deviation from spec. Report:
  `progress/impl_rollover_job_logic.md`. Awaiting reviewer.
- reviewer: CHANGES_REQUESTED — 1 finding, everything else clean (coverage,
  traceability, mutants, signatures, layering, language). Surviving mutant:
  `@dataclass(frozen=True)` → `@dataclass` on `RolloverResult`
  (`rollover.py:26`) — no frozen-instance test existed for it, unlike
  `ArchivedWeek`.
- implementer: added `test_rollover_result_is_frozen` mirroring
  `test_archived_week_is_frozen`, cited against R3. Confirmed by hand: applied
  the named mutant, the new test failed as expected
  (`DID NOT RAISE FrozenInstanceError`); reverted `rollover.py` to
  byte-identical (`git diff` empty); `./init.sh` green, 295 passed (was 294).
  Report updated: `progress/impl_rollover_job_logic.md`. Awaiting reviewer.
- human (sign-off review): caught a stale doc pointer — `archive_week`'s
  docstring in the shipped source cited "design.md section 5" for why
  steps 1+2 collapse into one function; that's the idempotency section, not
  the reasoning (§6, rejected alternative D). Originated in `design.md`'s own
  §4 code block (copied verbatim per SDD discipline); human fixed the spec
  directly, asked implementer to match it in the shipped source.
- implementer: fixed `rollover.py`'s `archive_week` docstring to cite
  "section 6, rejected alternative D" (three lines, under ruff's 100-char
  limit, matching the spec's split). Content-only, no test/behavior change.
  `./init.sh` green, 295 passed (unchanged). Awaiting reviewer.
- human (sign-off review, second finding): `roll_over`'s docstring body ran
  5 lines and bundled two justifications (unchecked_items reuse + retry-
  safety pointer), violating `docs/conventions.md`'s "three lines is the
  ceiling" rule for comments. Also originated in `design.md`'s §4 code block
  (human fixed the spec directly).
- implementer: trimmed `roll_over`'s docstring to 2 lines, dropping the
  unchecked_items-reuse justification (already at design.md §6, alternative
  C) and keeping only the retry-safety pointer (design.md §5). Content-only.
  `./init.sh` green, 295 passed (unchanged). Awaiting reviewer.

- reviewer: launched against `progress/impl_rollover_job_logic.md`,
  `rollover.py`, `test_rollover.py`, mutation testing included; specifically
  pointed at the recurring frozen-instance-test gap and the language check.

- reviewer: CHANGES_REQUESTED. 1 finding, 1 mutant survived — `RolloverResult`
  (R3) is `frozen=True` but, like `ArchivedWeek` next to it, only its
  field-shape is tested; a mutant dropping `frozen=True` survived against
  the full 294-test suite. **Third feature in a row with this exact gap**
  (`ai_prompt_builder`, `ai_output_validation`, now this) — reviewer
  explicitly recommends making "every new `@dataclass(frozen=True)` gets its
  own frozen-instance test" a standing rule in implementer briefs rather
  than relying on reviewer to catch it each time. Everything else clean:
  coverage, traceability, all other mutants killed, design §4 signatures
  verbatim, rejected alternative E honoured (no `IsoWeek` fields), no
  modified files beyond what was claimed, layering, and the language check
  (no user-facing string in `rollover.py` at all — only a stdlib
  `FrozenInstanceError`). Tree restored, gates reverified green.
- Leader: sending the finding back to the implementer — one missing test.
  No design change. Noting the standing rule for future implementer briefs
  in this project: state frozen-instance-test coverage explicitly per new
  frozen dataclass, don't leave it implicit.

- reviewer: APPROVED. Named mutant re-applied and killed by the new test;
  source confirmed byte-identical to pre-fix. `./init.sh` green: 295 tests.
- Leader: codified the recurring finding as a standing convention —
  `docs/conventions.md`'s Tests section now states explicitly that every new
  `@dataclass(frozen=True)` needs its own frozen-instance test, citing all
  three features that hit this gap.

- Leader: verified the docstring fix byte-for-byte directly. Content-only,
  no test/behavior implication, so no reviewer re-run needed for this one.

- Human: marked feature 13 `done` again, then caught a second real defect
  on sign-off: `roll_over`'s docstring body runs 5 lines and bundles two
  justifications (why step 5 reuses `unchecked_items`, and where the
  retry-safety analysis lives), violating `docs/conventions.md`'s Comments
  section — "Three lines is the ceiling," one short claim + pointer, never
  reproduce the reasoning. Leader verified the exact wording and confirmed
  the same defect sits in `design.md`'s own §4 code block (second time this
  has happened on this feature). Status reverted to `in_progress`.
- Leader: fixed `design.md` directly — dropped the `unchecked_items`-reuse
  justification entirely (already spelled out in full at §6, rejected
  alternative C; no need to echo it here), kept only the retry-safety claim
  + pointer, body now 2 lines. Sending the matching fix to the implementer
  for `rollover.py`.
- implementer: fixed. `./init.sh` green, 295 tests unchanged.
- Leader: verified byte-for-byte, then proactively re-read the whole file —
  every remaining docstring checked against the 3-line ceiling and, where
  present, its `design.md` section pointer checked for accuracy. All clean;
  test file's comments are all single-line. No third round expected.

## Next step

Ready for human sign-off: review `specs/rollover_job_logic/`,
`backend/core/src/planner_core/domain/rollover.py`,
`backend/core/tests/domain/test_rollover.py`, and
`progress/impl_rollover_job_logic.md`. Marking `done` and committing are
human-only.

- Human: marked feature 13 `done`, then caught a real defect on sign-off
  review: `rollover.py`'s `archive_week` docstring ("see design.md section 5
  on why these two collapse") points at the wrong section — §5 is the
  idempotency discussion, not the step-collapse reasoning. The correct
  pointer is §6, rejected alternative D, which is exactly that reasoning.
  Leader verified: the mislabel originates in `design.md`'s own §4 code
  block (the approved spec), not an implementer deviation — the
  implementation copied it verbatim, correctly per SDD discipline. Status
  reverted to `in_progress`.
- Leader: fixed the spec directly (`specs/rollover_job_logic/design.md`,
  not backend/frontend — mine to correct): reference now reads "see section
  6, rejected alternative D, on why these two collapse", split across two
  lines to keep the real `rollover.py` docstring under ruff's 100-char line
  length once fixed. Sending the matching fix to the implementer for
  `rollover.py` itself.
