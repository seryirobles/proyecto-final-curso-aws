# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

- **Feature in progress:** 12 — `ai_output_validation`
- **Started:** 2026-08-26
- **Agent:** spec_author (launching)

## Plan

Features 11 (`ai_prompt_builder`) and 24 (`ai_prompt_versioning`) are `done`
and committed (`5fbd2d3`, `37bc211`), tree clean. `./init.sh` reports feature
12 — `ai_output_validation` (tier 1, `sdd: true`, depends_on [11], pending) as
the next actionable feature.

Covers FR-AI-10, FR-AI-12, FR-LIB-05: validates model output against the
recipe schema and the fixed unit list, and models the accept/discard/
regenerate preview plus per-slot failure results.

Per SDD flow: spec_author writes
`specs/ai_output_validation/{requirements,design,tasks}.md`, sets status to
`spec_ready`, then STOP for human approval gate.

## Log

- Leader: confirmed features 11 and 24 done/committed, archived session to
  `history.md`, ran `./init.sh` (green, 249 tests) — next actionable feature
  confirmed as 12.
- spec_author: launched against `FR-AI-10`, `FR-AI-12`, `FR-LIB-05`.

- spec_author: `spec_ready -> specs/ai_output_validation/`. R1-R21 in
  `domain/ai_output.py`: `RawIngredient`/`RawRecipeOutput` (already-parsed,
  provider-agnostic shape), `validate_ai_recipe_output` (reuses `parse_unit`/
  `parse_category`, never redeclares either vocabulary), the
  `RecipePreview`/`new_preview`/`accept_preview`/`discard_preview` lifecycle,
  and `GenerationFailureReason`/`GenerationFailure`/`GenerationSuccess`/
  `SlotGenerationResult`. Four rejected alternatives (§6), two gate questions
  (§7). Leader spot-checked the `G-70` citation against
  `docs/gaps_and_resolutions.md` directly — accurate. Status set to
  `spec_ready`.

## Gate questions for the human (specs/ai_output_validation/design.md §7)

1. **Keep `GenerationFailureReason.GENERATION_UNAVAILABLE`?** No
   `feature_list.json` acceptance bullet names it, but it's grounded in
   `G-70`'s own text amending `FR-AI-10` (a covered id): *"surfaces a
   friendly es-ES message when generation is unavailable because the cap is
   reached."* spec_author recommends keeping it — cheap (one enum member,
   one message), gives feature 17 somewhere to put a cap-reached failure
   without a follow-up spec amendment. Dropping it removes one enum row, one
   message constant, nothing else depends on it.

2. **`numeroComensales`, again.** Feature 11's gate resolution said whichever
   feature "first parses AI output into a `Recipe`" should receive
   `FR-LIB-03` in its `covers` array to record servings. Feature 12 is that
   feature — but spec_author deliberately declined to claim it here (servings
   is orthogonal to what this feature validates: units, category, schema).
   Recommends leaving it for feature 17 (`ai_lambda`), where the AI response
   first exists as a concrete value to attach a figure to. Confirm or
   override.

- Human: approved both as recommended — `GENERATION_UNAVAILABLE` kept;
  `numeroComensales` deferred again, to feature 17. Status set to
  `in_progress`.
- implementer: launching against `specs/ai_output_validation/`.
- implementer: T1-T12 complete. Created `domain/ai_output.py` (RawIngredient,
  RawRecipeOutput, validate_ai_recipe_output, RecipePreview, new_preview,
  accept_preview, discard_preview, GenerationFailureReason, GenerationFailure,
  GenerationSuccess, GenerationOutcome, build_generation_failure,
  validate_and_preview, SlotGenerationResult) and
  `tests/domain/test_ai_output.py` (25 tests, R1-R21). Added 3 es-ES
  constants to `messages.py`. `./init.sh` green: 274 passed (was 249).
  Report: `progress/impl_ai_output_validation.md`. Awaiting reviewer.
- reviewer: CHANGES_REQUESTED — 2 findings (missing frozen-ness tests for
  `GenerationFailure`/`GenerationSuccess`/`SlotGenerationResult`; weak
  isinstance-only assertion in the R21 independence test). Everything else
  verified clean (coverage, traceability, layering, `GENERATION_UNAVAILABLE`
  wiring); `discard_preview`/mypy workaround explicitly judged sound.
- implementer: fixed both — added 3 frozen-ness tests, strengthened the R21
  test with two distinct success outcomes so a swap is detectable. Confirmed
  all 3 named mutants die individually, reverted `ai_output.py` to
  byte-identical. `./init.sh` green: 277 passed (was 274, +3). Awaiting
  reviewer re-check.
- Human sign-off review: caught broken Spanish in the 3 new `messages.py`
  constants (`valida`, `Anade`, `generacion`, `esta`/`mas`, and the
  ungrammatical "Puedelo intentar mas tarde") — missed by structural review
  and mutation testing since no test asserted actual content beyond equality
  against the constant. implementer: corrected all three to proper es-ES
  (`válida`, `Añade`, `generación`, `está`/`más`, "Puedes intentarlo más
  tarde."). Content-only fix, no design/behaviour change. `./init.sh` green:
  277 passed, unchanged count as expected.
- Leader: sending a narrow verification request back to the same reviewer
  (re-apply the three named mutants, confirm kill) per the
  cheap-verification convention.

- reviewer: APPROVED. All 3 named mutants re-applied individually and
  killed by their corresponding new test, no cross-kill. Tree confirmed
  byte-identical to pre-review (`ai_output.py` hash unchanged). `./init.sh`
  green: 277 tests.

## Next step

Ready for human sign-off: review `specs/ai_output_validation/`,
`backend/core/src/planner_core/domain/ai_output.py`,
`backend/core/tests/domain/test_ai_output.py`, the three new constants in
`backend/core/src/planner_core/messages.py`, and
`progress/impl_ai_output_validation.md`. Marking `done` and committing are
human-only.

- Human: marked feature 12 `done`, then caught a real defect on sign-off
  review that the automated reviewer's checks don't cover (grammar/spelling
  is not something mutation testing or structural tests catch): the three
  new `messages.py` constants have broken Spanish — missing accents
  throughout (`valida`, `generacion`, `esta`, `mas`), a missing `ñ`
  (`Anade`), and `"Puedelo intentar mas tarde"` isn't a real Spanish
  construction. Leader verified byte-for-byte against the file directly —
  accurate. Status reverted to `in_progress`.
- Leader: sending the fix back to the implementer — content-only, no design
  change: `AI_GENERATION_INVALID_OUTPUT` -> "...no es válida...",
  `AI_GENERATION_INSUFFICIENT_LIBRARY_RECIPES` -> "Añade recetas...",
  `AI_GENERATION_UNAVAILABLE` -> "La generación con IA no está disponible en
  este momento. Puedes intentarlo más tarde."

- reviewer: launched against `progress/impl_ai_output_validation.md`,
  `ai_output.py`, `test_ai_output.py`, `messages.py`, mutation testing
  included; specifically judged the `discard_preview`/mypy `return-value`
  workaround.

- reviewer: CHANGES_REQUESTED. 2 findings, 3 mutants survived — real
  test-coverage gaps, not design issues: `GenerationFailure`,
  `GenerationSuccess` and `SlotGenerationResult` (R15/R16/R20) are all
  `frozen=True` but only their field sets are tested, not frozenness itself
  (mirrors feature 11's earlier finding shape); one existing test
  (`..._preserve_each_entrys_own_outcome_independently`) only asserts
  `isinstance`, not equality, so a swapped-outcome defect would pass.
  Everything else clean — coverage, traceability, architecture conformance,
  layering, `GENERATION_UNAVAILABLE` wiring. The flagged `discard_preview`
  deviation judged **sound, not under-testing**: both defect halves die (one
  via pytest, one via mypy's `return-value` check, a Level-1 `./init.sh`
  gate), no `# type: ignore`, no weakened type. Tree restored, gates
  reverified green.
- Leader: sending both findings back to the implementer — add 3 missing
  frozen-ness tests, strengthen one assertion to equality. No design change.
