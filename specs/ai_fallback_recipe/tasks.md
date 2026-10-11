# ai_fallback_recipe - Tasks

Ordering: do not start until issues 15-17 are `done`, or the owner says to start anyway (they edit the same `v4` code).

- [x] T1 - Append the fallback sentence to `HEALTHY_BALANCED_INSTRUCTION_V4` (no new version, no new field); update the constant's docstring. Read the file first; edit, do not rewrite. Covers: R1, R5, R6, R7, R8.
- [x] T2 - Registry tests: `v4` equals `v3` with only the healthy-balanced field replaced; `v1`-`v3` rendered text equals a captured snapshot; `resolve_prompt_version("v4")` carries the sentence. Covers: R1, R10, R11, R16.
- [x] T3 - Render tests per mode (specification, reference, category) under `v4`: sentence present, names empty / generic / unrelated to cooking / unintelligible, keep-usable-parts clause, healthy-balanced and non-medical text, es-ES directive. Covers: R2, R3, R4, R5, R6, R7, R8, R9.
- [x] T4 - Render test: for each mode, every line except the healthy-balanced one equals the `v3` line; and the text does not match `\bgenerate\b[^.\n]*\bmenu`. Covers: R12, R17.
- [x] T5 - Builder test: `build_specification_prompt(("test",), ("test",), "v4")` carries both strings unchanged. Covers: R13.
- [x] T6 - Validation tests (only if not already pinned): empty ingredients gives `MISSING_INGREDIENTS`, empty tools gives `MISSING_TOOLS`, before any prompt is built. Covers: R14, R15.
- [x] T7 - Write the live probe script in the scratchpad (not the repo), per `design.md`; hand the path and run command to the leader. Covers: acceptance criterion 1 (not a deterministic test).
- [ ] T8 - Owner runs the probe and reports the matrix; record the result in `progress/current.md`. Covers: acceptance criterion 1.
- [x] T9 - Confirm issue 17's staged and in-repo `v4` tests still pass unmodified. Covers: R11, R17.
- [x] T10 - Run `./init.sh`; record the R to test table in `progress/impl_ai_fallback_recipe.md`. Covers: R1-R17.
