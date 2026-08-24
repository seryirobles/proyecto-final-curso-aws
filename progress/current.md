# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

- **Feature in progress:** 5 - `week_plan_model`
- **Started:** 2026-08-24
- **Agent:** leader -> spec_author (gate pending)

## Plan

Feature 4's session summary was moved to `progress/history.md` and this file
reset before starting.

Feature 5 `week_plan_model` (tier 1, `sdd: true`) is the next actionable
feature: `depends_on: [2, 4]` are both `done`, `covers` = `FR-MENU-03`,
`FR-CAND-01`, `FR-CAND-02`, `FR-CAND-04`, `FR-CAND-05`, `FR-CAND-06`,
`FR-CAND-08`, `FR-SUM-01`, `FR-SUM-03`, `FR-AUTH-13` (10 ids, the widest
`covers` array in tier 1). It goes through `spec_author` first, then **stops at
the human approval gate** before any code.

## Log

- `./init.sh` exit 0 - every gate green, 71 backend tests,
  `done: 4, pending: 10, blocked: 9`. Reported next actionable feature: 5.
- Working tree clean at `623b378 feat: categories and recipe data structure`.

- `spec_author` returned: `specs/week_plan_model/{requirements,design,tasks}.md`,
  feature 5 `pending` -> `spec_ready`. 24 R-blocks, 41 tasks, 4 gate questions.
- **Leader verification of the spec, not relayed:**
  - 24 R-blocks, ids contiguous `R1..R24`, **exactly one `SHALL` each** (27
    total; the other three state the header rule).
  - All ten `covers` ids cited, none orphaned. `FR-LIB-01`/`FR-LIB-02` appear
    **only** in the scope note at `requirements.md:38`, never inside an
    R-block -- correctly fenced, not invented.
  - No `Clock`, `datetime`, `uuid` or `time()` anywhere in the design; the only
    hits are explicit statements of *not* using one. The date-not-`Clock`
    ruling is extended to ids by analogy (design §8, alternative B).
  - `backend/` untouched.

## Human approval gate -- 2026-08-24

**All four gate questions approved as recommended** ("OK"):

1. **`UNKNOWN_USER_ID = "unknown-user"`** as an internal domain sentinel --
   never persisted by this feature, never rendered (the Castilian label is
   feature 20's). **Extra ruling from the human:** feature 15's seeded
   placeholder account's `idUsuario` is meant to be **exactly** that literal.
   Pinned in `docs/data_model.md` §5.1, since feature 15 is not built yet and
   would otherwise pick its own. If the two disagree, a removed author
   resolves to nothing instead of the placeholder and `FR-SUM-03` breaks
   silently. Note they are different things: the reserved *name* is the es-ES
   `usuario desconocido`; the *id* is the ASCII `unknown-user`.
2. **`Candidate.id`/`author` stay caller-supplied**; no `Ids` port built. The
   architecture anticipates the port family, but no covered `FR-*` asks for a
   generation *mechanism* -- only that candidates be addressable.
3. **`Recipe` gains no author field.** `FR-AUTH-13` does name library recipes,
   but that half belongs to whoever implements `FR-LIB-01`/`FR-LIB-02`.
   Reaching into feature 4's closed dataclass from another feature's spec is
   the boundary that keeps closed features closed.
4. **`remove_candidate` silently clears `definitive_id`** rather than raising.
   The leader's argument, accepted: the UI does not need the exception -- it
   can check `definitive(plan)` before calling, so raising buys no information
   the caller cannot already see, at the cost of an exception for a
   foreseeable, legal user action. `FR-UX-04` confirmation flows stay
   feature 20's.

Feature 5 `spec_ready` -> `in_progress`.

## Implementer + three review rounds (2026-08-24)

- **Implementer:** `progress/impl_week_plan_model.md`. `domain/candidate.py`
  + `tests/domain/test_candidate.py`, no file modified. 96 tests, all gates.
  One declared deviation: `design.md` §6's
  `from collections.abc import AbstractSet` does not merely fail
  `mypy --strict` -- it raises `ImportError`. `collections.abc` has no
  `AbstractSet`; the name there is `Set`. Shipped the alias form.
- **Round 1** (`review_week_plan_model.md`): CHANGES_REQUESTED. 34 mutations,
  **8 survivors, every one a missing assertion** -- no defect in the source.
  `F1`-`F6`.
- **Round 2** (`_round2.md`): CHANGES_REQUESTED on one new survivor, `F7`.
  All of round 1 verified genuinely closed.
- **Round 3** (`_round3.md`): **APPROVED.** 10 mutations, 9 killed, 1
  equivalent (`M40`), 0 genuine survivors.

### What the three rounds were actually about

**Not one finding was a bug in `candidate.py`.** Its git blob hash is
`fa4fa32404c0aeedb71f49a89fdf00b09c705c82` -- unchanged from the first
implementer run through roughly forty mutations. The source was right the
first time; the tests were not proving it.

- **`F1` (M23)** -- the one that would have shipped. Replacing
  `remove_candidate`'s conditional with `definitive_id = None` left all 96
  tests green: deleting *any* candidate would silently wipe the slot's chosen
  meal (`docs/architecture.md` §4 invariant 2). Two tests between them covered
  both branches of the `if`, but only ever the branch returning `None`.
- **`F2` (M29)** -- `assert result.recipe is not None` on a field typed
  `Recipe`, not `Recipe | None`. **The assertion could not fail.** A hollow
  recipe on the duplicate path kept the suite green.
- **`F7` (M57)** -- the same defect one level deeper, and the reviewer
  recorded it as **its own round-1 under-specification**: `F2` asked for
  "name and one of the collection fields", which is exactly what was
  delivered, so `tools`/`procedure`/`category` stayed unasserted on the
  warning path. `G-26` would have looked honoured while producing a recipe
  nobody can cook.
- **`F4` (M43)** -- `UNKNOWN_USER_ID` compared only against its own symbol,
  so the literal could drift from the value pinned at this session's gate.
  The mutant used to kill it is `"usuario-desconocido"` -- the plausible
  mistake, confusing the reserved es-ES *name* with the ASCII *id*.
- **`F5`** -- `frozen=True` named in R1 and R3, tested by nothing.
- **`O6`** -- two pre-existing assertions removed as incapable of failing,
  each merely restating the line above it.

### The lesson, recorded

**An assertion that restates what the previous line already proved is not
coverage.** It reads as thoroughness on review and catches nothing, which is
worse than an obviously thin test because nobody goes back to check. Every one
of the seven findings was a missing or fake assertion; none was a defect in
the code. In a pure-domain feature with no IO, that is where the risk lives.

### Leader-closed after approval

- **`O8`** -- `impl_week_plan_model.md`'s test-output section was two rounds
  stale (`96 passed` / 25 tests; truly 100 / 29). Superseding note added; the
  original figures left as the dated record of that run.
- **`O9`** -- `tasks.md` T14's "never a collection" wording ran ahead of its
  test after the sanctioned `O6` removal. Note added; substantively satisfied.

### Open register carried to feature 6's reviewer

`O2` (`promote`'s guard is an equivalent mutant -- keep it, it is where a
reader looks for R13's precondition; do not "fix" it by weakening
`__post_init__`), `O3` (`candidate.py` correctly outside
`SHARED_KERNEL_MODULES`), `O4`, and `O7` (R18's "a `Recipe`, not a
`MealSnapshot`" rests on `mypy` alone on the duplicate path).

## Next step

**Feature 5 `week_plan_model` is APPROVED and ready to close.** `./init.sh`
exit 0, 100 backend tests, every gate green.

Two acts remain and **both are the human's alone**:

1. Mark feature 5 `done` in `feature_list.json` (`"id": 5`,
   `"status": "in_progress"` -> `"done"`).
2. Commit. The tree carries feature 5's two new files, `specs/week_plan_model/`,
   five `progress/` reports, the `docs/data_model.md` §5.1 pin, and this
   session's `G-82` documentation edits. Nothing is staged; no agent touched
   git.

## Implementer session -- 2026-08-24

- **Feature in progress:** 5 - `week_plan_model`
- **Plan:** tasks T1..T41 from `specs/week_plan_model/tasks.md`.
- Built `backend/core/src/planner_core/domain/candidate.py` and
  `backend/core/tests/domain/test_candidate.py` (25 tests, R1-R24). One fix
  to design.md's literal import (`collections.abc.AbstractSet` does not
  exist; used `Set as AbstractSet`), documented in
  `progress/impl_week_plan_model.md`.
- `./init.sh` green: 96 backend tests (71 pre-existing + 25 new), frontend
  gate unaffected. All 41 tasks ticked in `tasks.md`.
- Feature left `in_progress`, not marked `done` -- awaiting the mandatory
  `reviewer` run.
