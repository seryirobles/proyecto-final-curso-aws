# Implementation report — ai_output_validation (feature 12)

Status: tasks T1-T12 complete, `./init.sh` green. Not marked `done` — human/reviewer only.

## Files

- `backend/core/src/planner_core/domain/ai_output.py` (new)
- `backend/core/tests/domain/test_ai_output.py` (new)
- `backend/core/src/planner_core/messages.py` (modified — 3 constants appended, no existing constant touched)
- `specs/ai_output_validation/tasks.md` (T1-T12 ticked)

## Test result

277 passed (was 249 before this feature; +28 new tests, all in `test_ai_output.py`).
`ruff format`, `ruff check`, `mypy --strict`, `pytest` all green via `./init.sh`.

### Reviewer round 1 — CHANGES_REQUESTED, both fixed

1. Missing frozen-ness tests for `GenerationFailure` (R15), `GenerationSuccess`
   (R16), `SlotGenerationResult` (R20/R21) — added
   `test_generation_failure_is_frozen`, `test_generation_success_is_frozen`,
   `test_slot_generation_result_is_frozen`. Confirmed each of the three named
   mutants (dropping `frozen=True` on that one type) makes exactly its new
   test fail, one mutant at a time, then reverted `ai_output.py` to
   byte-identical (`grep -n "@dataclass" ai_output.py` shows all six
   declarations back to `frozen=True`).
2. Weak assertion in
   `test_slot_generation_results_preserve_each_entrys_own_outcome_independently`
   — entries 0 and 2 previously shared one `success_outcome` value (an
   `isinstance` check, or even an equality check against the shared value,
   cannot detect a swap between two identical values). Now built from two
   distinct raw recipes (`success_outcome_a`, `success_outcome_c`) so a swap
   between entries 0 and 2 fails an equality assertion.

`./init.sh` re-run green after the fix: 277 passed (was 274 after round 1's
25, +3 frozen-ness tests).

### Sign-off fix — broken Spanish in the 3 new `messages.py` constants

Human caught it directly (neither structural review nor mutation testing
could): the three constants had unaccented/typo'd Spanish, unlike the file's
pre-existing constants. Corrected content only, no design/behavior change:
`valida` → `válida`, `Anade` → `Añade`, `generacion` → `generación`,
`esta`/`mas` → `está`/`más`, and the ungrammatical `"Puedelo intentar mas
tarde"` → `"Puedes intentarlo más tarde."`. `./init.sh` re-run green, 277
passed (no count change — content-only, no test asserts specific characters
beyond structural equality against the constant itself).

## Traceability — R<n> to FR-* to test

| R<n> | FR-* | Test(s) |
|---|---|---|
| R1 | FR-LIB-05 | `test_raw_ingredient_fields_are_exactly_the_fixed_shape`, `test_raw_ingredient_is_frozen` |
| R2 | FR-LIB-05, FR-LIB-03 | `test_raw_recipe_output_fields_are_exactly_the_fixed_shape`, `test_raw_recipe_output_is_frozen` |
| R3 | FR-LIB-05 | `test_validate_ai_recipe_output_resolves_units_in_order` |
| R4 | FR-LIB-05 | `test_validate_ai_recipe_output_raises_unknown_unit_for_unresolvable_unit` |
| R5 | FR-LIB-03 | `test_validate_ai_recipe_output_resolves_category` |
| R6 | FR-LIB-03 | `test_validate_ai_recipe_output_raises_unknown_ingredient_category_for_bad_category` |
| R7-R9 | FR-LIB-03 | `test_validate_ai_recipe_output_carries_name_tools_procedure_unchanged` |
| R10 | FR-AI-10 | `test_recipe_preview_fields_are_exactly_recipe`, `test_recipe_preview_is_frozen` |
| R11 | FR-AI-10 | `test_new_preview_carries_the_recipe` |
| R12 | FR-AI-10 | `test_accept_preview_returns_the_recipe` |
| R13 | FR-AI-10 | `test_discard_preview_returns_none` |
| R14 | FR-AI-12 | `test_generation_failure_reason_has_exactly_the_three_members` |
| R15 | FR-AI-12 | `test_generation_failure_fields_are_exactly_the_fixed_shape` |
| R16 | FR-AI-12 | `test_generation_success_fields_are_exactly_the_fixed_shape` |
| R17 | FR-AI-12, FR-UX-03 | `test_build_generation_failure_maps_reason_to_its_message` (parametrized, all 3 reasons) |
| R18 | FR-AI-10 | `test_validate_and_preview_success_wraps_a_new_preview` |
| R19 | FR-AI-10, FR-AI-12 | `test_validate_and_preview_returns_invalid_output_failure_for_unknown_unit`, `..._for_unknown_category` |
| R20 | FR-AI-12 | `test_slot_generation_result_fields_are_exactly_the_fixed_shape`, `test_slot_generation_result_is_frozen` |
| R21 | FR-AI-12, FR-AI-09 | `test_slot_generation_results_preserve_each_entrys_own_outcome_independently` |

All three `covers` ids (`FR-AI-10`, `FR-AI-12`, `FR-LIB-05`) reachable via the R<n> map above; consumed-not-owned ids `FR-LIB-03`, `FR-UX-03`, `FR-AI-09` also covered per `requirements.md`'s scope-note table.

## Deviations / notes not anticipated by the spec

- mypy strict flags `func-returns-value` on any expression use (including plain
  assignment) of a `-> None` function's call result — `discard_preview(preview)`
  hit this. Resolved without weakening the type or `# type: ignore`: the test
  calls it for its side effect, then asserts `get_type_hints(discard_preview)
  ["return"] is type(None)` — mypy itself already guarantees no non-`None`
  value can leave a `-> None` function, so this is equivalent proof of R13
  without triggering the checker.
- `AI_GENERATION_UNAVAILABLE`'s two-line literal collapsed to one line under
  `ruff format` (both fit within the 100-char limit); content unchanged from
  `design.md` §4, reproduced verbatim (including its non-standard "Puedelo"
  wording and missing accents, consistent with `ai_prompt.py`'s existing
  precedent of unaccented Castilian content constants).
- `docstring` on `accept_preview` shortened by one word to fit the 100-char
  `ruff` line limit; meaning unchanged from `design.md`.
