# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

- **Feature in progress:** 11 — `ai_prompt_builder`
- **Started:** 2026-08-26
- **Agent:** spec_author (launching)

## Plan

Feature 10 — `generation_request` — is `done` and committed (`44501cd`), tree
clean. `./init.sh` reports feature 11 — `ai_prompt_builder` (tier 1,
`sdd: true`, depends_on [10] `generation_request`, done) as the next
actionable feature.

Covers FR-AI-01, FR-AI-02, FR-AI-04, FR-AI-06, FR-AI-07, FR-AI-13:
provider-agnostic prompt assembly (plain data structures, no provider SDK —
P4 still pending), Castilian Spanish output instruction, configured servings
stated explicitly, category counts as explicit prompt instructions
(verifiable post-generation against each recipe's `tipoAlimento`), the fixed
unit vocabulary as a prompt constraint, the healthy/varied-protein
instruction labelled non-medical, and both single-recipe modes (from
specifications; from a library reference plus specifications).

Per SDD flow: spec_author writes
`specs/ai_prompt_builder/{requirements,design,tasks}.md`, sets status to
`spec_ready`, then STOP for human approval gate.

## Log

- Leader: confirmed feature 10 done/committed, archived session to
  `history.md`, ran `./init.sh` (green, 221 tests) — next actionable
  feature confirmed as 11.
- spec_author: launched against FR-AI-01, FR-AI-02, FR-AI-04, FR-AI-06,
  FR-AI-07, FR-AI-13.

- spec_author: `spec_ready -> specs/ai_prompt_builder/`. R1-R20, one gate
  question in `design.md` §9.
- Leader: verified the spec against actual code (not guessed) —
  `GenerationTargets.remaining_category_counts`, `CategoryCountRule`,
  `Recipe`, `Unit` in `domain/{generation,rules,recipe,units}.py`; the
  `SHARED_KERNEL_MODULES` tuple in `test_shared_kernel_guards.py`;
  `docs/architecture.md` §2.1's pending servings-count item and §6's
  "single documented constants module" line; `docs/data_model.md`'s
  `numeroComensales` attribute; `specs/recipe_model/design.md`'s own
  cross-reference naming feature 11 as where it'd be addressed. All
  citations accurate. Status set to `spec_ready`.

## Gate question for the human (design.md §9)

`specs/ai_prompt_builder/design.md` does **not** add `numeroComensales` to
`Recipe`/`MealSnapshot` — `FR-LIB-03`/`FR-CAND-07` (the requirements that
define those types' shape) are in neither this feature's nor feature 12's
`covers` array, so adding the field here would be inventing an uncovered
requirement. `FR-AI-13`'s literal text ("stated explicitly in every prompt")
is satisfied via `CONFIGURED_SERVINGS` traveling through every prompt;
*persisting* the number on the resulting recipe is left open.

Recommendation: amend feature 12's or feature 17's `covers` array (whichever
first parses AI output into a `Recipe`) to add `FR-LIB-03` when that happens
— that is the natural point to set `numeroComensales`.

- Human: gate question resolved — deferred to feature 12/17 (recommendation
  approved as designed). `CONFIGURED_SERVINGS = 4` approved together with
  the spec. `design.md` §9 updated with the resolution note. Status set to
  `in_progress`.
- implementer: launching against `specs/ai_prompt_builder/`.

- implementer: T1-T10 complete. New module
  `backend/core/src/planner_core/domain/ai_prompt.py` and its test
  `backend/core/tests/domain/test_ai_prompt.py` (R1-R20). Fixed two
  design.md §6 docstrings exceeding the 100-char ruff limit when
  transcribed verbatim (wording shortened, no meaning change). `./init.sh`
  green: 234 tests (221 -> 234, +13). Report: `progress/impl_ai_prompt_builder.md`.

- reviewer: launched against `progress/impl_ai_prompt_builder.md`,
  `ai_prompt.py`, `test_ai_prompt.py`, mutation testing included.

- reviewer: CHANGES_REQUESTED. 19 mutants planted, 15 killed, 4 survived —
  all real test-coverage gaps, not design issues: (1) R3's test only checks
  `HEALTHY_BALANCED_INSTRUCTION` is non-empty, so replacing the whole
  approved string with `"x"` still passes; (2)-(4) `SpecificationPrompt`,
  `ReferencePrompt`, `CategoryPrompt` (R10-R12) have no frozen-instance test
  — only `PromptInstructions` (R5) does — so removing `frozen=True` from any
  of the three leaves the suite green. Tree restored, byte-identical to
  pre-review state.
- Leader: sent all 4 findings back to the implementer — straightforward
  "add the missing test assertion", no design change.

- implementer: all 4 findings fixed. All 4 mutants re-applied and confirmed
  caught by the strengthened/new tests, then reverted (`ai_prompt.py`
  byte-identical to pre-review, tree clean otherwise). `./init.sh` green:
  237 tests (234 -> 237).

## Next step

Ready for human sign-off: review `specs/ai_prompt_builder/`,
`backend/core/src/planner_core/domain/ai_prompt.py`,
`backend/core/tests/domain/test_ai_prompt.py` and
`progress/impl_ai_prompt_builder.md`. Marking `done` and committing are
human-only.
