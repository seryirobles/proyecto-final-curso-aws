# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

- **Feature in progress:** 9 — `password_policy`
- **Started:** 2026-08-26
- **Agent:** spec_author (launched)

## Plan

Feature 8 — `shopping_list_state` — is `done` and committed (`48df9af`), tree
clean. `./init.sh` reports feature 9 — `password_policy` (tier 1, `sdd: true`,
depends_on [1] done) as the next actionable feature.

Covers FR-AUTH-15 (NIST 800-63B password policy: min length 10, up to at
least 64 chars, no composition rules, no forced rotation, blocklist including
common Spanish-language passwords) and FR-AUTH-17 (username uniqueness among
active accounts, reserved unknown-user placeholder name).

Per SDD flow: spec_author writes `specs/password_policy/{requirements,design,tasks}.md`,
sets status to `spec_ready`, then STOP for human approval gate.

## Log

- Leader: confirmed feature 8 done/committed, archived stale `current.md`
  entry to `history.md`, ran `./init.sh` (green, 182 tests) — next actionable
  feature confirmed as 9.
- spec_author: launched against FR-AUTH-15, FR-AUTH-17.
- spec_author: `spec_ready -> specs/password_policy/`. R1-R9 (FR-AUTH-15:
  R1-R6, FR-AUTH-17: R7-R9), FR-UX-03 cited via the assignment
  `specs/text_and_units/design.md` §6/§10 pre-flagged. Design creates
  `planner_core/messages.py` (first backend es-ES messages module) plus
  `domain/password_policy.py` and `domain/username_policy.py`. 3 gate
  questions raised in `design.md` §8. `feature_list.json` set to
  `spec_ready`.

- Human reviewed the 3 gate questions: Q1 (messages.py) and Q3 (no max
  length) approved. Q2 (blocklist content) escalated into a scope
  discussion — human decided to drop the breached-password blocklist from
  the MVP entirely rather than ship a thin hand-curated list (reasoning: a
  domain-pure, zero-IO, zero-dependency module can't hold a real corpus; a
  small literal would be barely better than the English-only list G-60
  already rejected; the right shape is an injectable check fed by a real
  corpus later, once an adapter layer exists).
- Leader: this required amending frozen `FR-AUTH-15` (blocklist clause is
  load-bearing text, not a design choice). Owner gave explicit, scoped
  authorization ("strip this from the MVP"). Edited `docs/requirements.md`
  (FR-AUTH-15, struck inline, not deleted) and `docs/gaps_and_resolutions.md`
  (new Part S, `G-83`, amends G-30/G-60) per the project's established
  "fresh, explicit lift" pattern (same shape as Parts I-R). `feature_list.json`
  feature 9 acceptance list and description updated to match; blocklist
  acceptance bullets removed, `note` field records the deferral.
- `specs/password_policy/` (R1-R9, design.md, tasks.md) now predates this
  amendment — R5/R6 and the design's blocklist section (§5 password_policy.py
  content, gate question 2) cite a clause that no longer exists. Sent back to
  spec_author to revise in place.

- spec_author: revised `specs/password_policy/` in place. R1-R7 (down from
  R1-R9), blocklist requirements and design content removed, G-83 cited in
  all 3 files. Gate question 2 (blocklist content) dropped; only 2 gate
  questions remain (messages.py assignment, no-max-length).
- Leader: verified the revision. Found and fixed a renumbering slip — `R5`
  (username equality rule, no message) was left listed as an `FR-UX-03`
  citer in 3 spots (requirements.md scope note + coverage map, tasks.md T1)
  when it should have read `R7` (old `R9`, `UsernameReserved`). Fixed
  directly (mechanical, single-file, no logic change). Rest of the revision
  is consistent.

- Human approved `specs/password_policy/` (R1-R7, both gate questions
  confirmed) — 2026-08-26. `feature_list.json` set to `in_progress` before
  launching the implementer.
- implementer: launched against `specs/password_policy/`.

- implementer: **Feature in progress: 9 — password_policy**. Plan: tasks
  T1-T21 from `specs/password_policy/tasks.md`.
- implementer: T1-T21 done. Created `planner_core/messages.py` (first
  backend es-ES messages module), `domain/password_policy.py`,
  `domain/username_policy.py`, and their two test modules. No files
  modified, no blocklist logic built (`G-83`). `./init.sh` green: 193
  tests (182 -> 193, +11). `uv export` confirms no dependency added.
  Report: `progress/impl_password_policy.md`.

- reviewer: CHANGES_REQUESTED. 8 mutants planted (length boundary, ceiling,
  composition, signature, reservation-order, both normalize() calls,
  uniqueness guard) — all 8 killed, tree restored. 1 finding: the
  `UNKNOWN_USER_NAME` comment in `username_policy.py` is 6 lines (quotes
  `docs/data_model.md` §5.1 instead of pointing at it), double the 3-line
  ceiling in `docs/conventions.md`. Everything else (traceability, layering,
  dependency-zero, G-83 deferral verified independently, exception shape)
  passed clean.
- Leader: fixed the same over-long comment in `specs/password_policy/design.md`
  §5 (not code — leader may edit specs/) to a 2-line pointer. Sent the actual
  source fix (`backend/core/src/planner_core/domain/username_policy.py`) back
  to the implementer — single-file, single-comment, no logic change.

- implementer: comment in `username_policy.py` replaced with the 2-line
  pointer, exact match to `design.md` §5. `./init.sh` green, 193 tests
  unchanged (comment-only change, no logic touched — no mutation re-check
  needed beyond confirming the suite is still green).

- Human ran their own code review before sign-off, verified all doc citations
  independently (G-30/G-83, FR-AUTH-15/-17, data_model.md §5.1, design.md
  byte-for-byte match). One real finding: `password_policy.py`'s module
  docstring is two sentences (length rule + a G-83 blocklist-deferral note
  that duplicates design.md §0), violating `docs/conventions.md`'s
  one-sentence rule — every other `planner_core/` module stays to one.
  Leader verified the finding directly, sent the trim to the implementer.

- implementer: docstring trimmed to one sentence. `./init.sh` green, 193
  tests unchanged (comment-only change).

## Next step

Ready for human sign-off: review `specs/password_policy/`,
`backend/core/src/planner_core/{messages.py,domain/password_policy.py,domain/username_policy.py}`,
`backend/core/tests/domain/{test_password_policy.py,test_username_policy.py}`
and `progress/impl_password_policy.md`. Marking `done` and committing are
human-only.
