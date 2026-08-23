# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

- **Feature in progress:** 3 — `text_and_units`
- **Started:** 2026-08-23
- **Agent:** leader → implementer → reviewer

## Plan

Human approved the three gate questions of `specs/text_and_units/design.md` §10
on 2026-08-23, all as recommended:

1. **Unit vocabulary:** three units — `g`, `ml`, `unit`. One per dimension,
   because `FR-SHOP-03` forbids cross-unit conversion.
2. **`ñ` survives the fold:** `piña` != `pina`. Only vowel accents and `ü` fold.
3. **`UnknownUnit` carries no Castilian message**, only the rejected value.
   Features 9 and 12 own their rejection text; no backend messages module
   before P5.

Status `spec_ready` → `in_progress`. Next: implementer executes
`specs/text_and_units/tasks.md`, then the reviewer validates traceability.

## Log

- `./init.sh` exit 0 before any change — seven gates green, 35 backend tests.
- `feature_list.json`: feature 3 `spec_ready` → `in_progress`.
- Implementer: **Plan — tasks T1..T27 from `specs/text_and_units/tasks.md`.**
- T1–T3: `domain/text.py` (`normalize`) and `domain/units.py` (`Unit`,
  `UnknownUnit`, `parse_unit`) written. Both ASCII-only, standard library only,
  `dependencies = []` untouched.
- T4–T23: 20 tests added across `tests/domain/test_text.py`,
  `tests/domain/test_units.py` and `tests/test_shared_kernel_guards.py`. Every
  input taken verbatim from `design.md` §8; all 29 design rows matched the
  implementation on first run.
- T24: 17-mutation battery run, each restore verified by SHA-256. **16 caught by
  the predicted test; mutation 6 survived** — `design.md` §5.1's `"İ"`
  justification does not hold, because NFD already decomposes `U+0130` to
  `I` + `U+0307`. Recorded with evidence in `progress/impl_text_and_units.md`
  §4.1 rather than papered over; no test invented on data `design.md` §8
  forbids. **Spec-text defect for the leader to route — no code change implied.**
- T26: `uv export` for `planner-api` and `planner-ai` resolve with nothing added.
- T27: `./init.sh` exit 0 — all gates green, **55 backend tests** (35 → 55).
- No git write command was used. `feature_list.json` untouched by the
  implementer; feature 3 left `in_progress` for the reviewer.

- **Reviewer APPROVED** -> `progress/review_text_and_units.md`. Its own
  8-mutation pass killed everything, including the R7 `n`-tilde rule (it
  repointed `COMBINING_TILDE` to `U+0304`) and a second fold planted in
  `ports/clock.py`, which proves the R2 guard's scan reaches beyond `domain/`.
  `./init.sh` green, 55 passed. Tree restored to the pre-review state.
- **The surviving mutant is adjudicated: dead justification, not a missing
  test.** Verified independently by the leader, not relayed:
  `unicodedata.normalize("NFD", "İ")` is `U+0049 U+0307`, so mark removal
  strips the dot under either ordering; an exhaustive `U+0000`-`U+2FFFF` sweep
  found 64 divergent codepoints, all Greek with iota subscript, zero Latin. On
  this feature's domain the two orderings are **equivalent**, so mutation 6 is
  an equivalent mutant that no honest test can kill.
- **Doc drift fixed by the leader** (AGENTS.md 3.1: doc drift is agent work),
  five sites in all. Four in the spec, done: `design.md` 5.1 (the false
  rationale, replaced with the sweep result and an explicit "the order is not
  load-bearing"), `design.md` 8 (the `U+0130` row no longer cites an "ordering
  rule"), `tasks.md` T7 (no longer calls the value a step-order regression
  test), `tasks.md` T24 row 6 (now labelled KNOWN EQUIVALENT MUTANT - expected
  to survive, do not write a test for it), plus the `tasks.md` header note.
  The fifth site is in `backend/`, so it went to an implementer.

- **All six false-claim sites corrected.** The first sweep found five; a
  **sixth** was hiding in a test comment
  (`backend/core/tests/domain/test_text.py:53-55`) and survived one extra round
  because the sweep searched only `src/` and the implementer task said "do not
  touch any test". Two comment-only implementer runs closed both source sites;
  no assertion, test name, docstring or logic was touched.
- **Final repo-wide sweep is clean.** The only surviving matches quote the false
  claim in order to record that it *was* false: the two agent reports and the
  inline correction note in `tasks.md`. Those are correct as they stand.
- `./init.sh` exit 0, 55 tests passing.

- **New convention from the human 2026-08-23: comments stay short.** Long text
  belongs in docs. Encoded as a three-line ceiling (tests included) in
  `docs/conventions.md` section Comments, as a positive rule in
  `.claude/agents/implementer.md`, and as a reject condition in the reviewer's
  conventions step. The worked counter-example in the conventions section is
  this session's own 7-line comment.
- **Three over-length blocks in feature 3 shortened** (`text.py` x2,
  `units.py`), `G-56`/`G-48` citations preserved, files still ASCII-only,
  `./init.sh` exit 0 with 55 tests. Detected mechanically by scanning for runs
  of `#` lines longer than three - re-run that scan to verify.
- **Three over-length blocks remain in feature 2** (`domain/calendar.py:40`,
  `ports/clock.py:36`, `tests/test_no_ambient_time.py:37`). **Deliberately not
  touched**: the ruling was "from now on" and feature 2 is closed. Flagged for
  the human, his call.

## Next step

**Feature 3 is complete and ready to close, but the leader never marks `done`
and never commits.** Both are the human's call:

1. Set `feature_list.json` feature 3 -> `done`.
2. Move this session's summary into `progress/history.md` and reset this file
   to its template.

Nothing is staged or committed; no agent ran a git write command all session.
