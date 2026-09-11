# impl_ai_prompt_versioning

Feature 24 · tier 1 · `sdd: true`. Tasks T1-T9 complete (`specs/ai_prompt_versioning/tasks.md`).

## Files

Created:
- `backend/core/src/planner_core/ports/config.py` — `ConfigPort` (`Protocol`), `EnvConfig`.
- `backend/core/src/planner_core/application/prompt_version.py` — `resolve_active_prompt_version(config)`.
- `backend/core/tests/application/test_prompt_version.py`
- `backend/core/tests/ports/test_config.py` — added post-review (reviewer
  finding: `EnvConfig.get` was unverified). Mirrors `tests/ports/test_clock.py`:
  `isinstance(FakeConfig(...), ConfigPort)`, `isinstance(EnvConfig(), ConfigPort)`,
  and an `EnvConfig` test via `monkeypatch.setenv` asserting the value comes
  back for the exact key requested (catches a wrong-key/prefix bug) plus a
  `None`-for-unset-key case.

Modified:
- `backend/core/src/planner_core/domain/ai_prompt.py` — added `PromptInstructionsVersion`,
  `PROMPT_INSTRUCTION_VERSIONS` (`v1` entry), `PROMPT_VERSION_CONFIG_KEY`,
  `UnknownPromptVersion`, `resolve_prompt_version`; `build_instructions()` and
  the three builders gained `version_id: str`.
- `backend/core/tests/domain/test_ai_prompt.py` — updated existing feature-11
  tests for `version_id`, added R1/R2/R4/R6 registry tests.
- `backend/core/tests/support/fakes.py` — added `FakeConfig`.
- `specs/ai_prompt_builder/requirements.md` (feature 11, T5) — amended R6-R9,
  R13, R16, R19 for the new `version_id` parameter, with an explicit amendment
  note. Flagged per T5: this is a breaking change to feature 11's
  already-implemented `build_instructions()` signature, human-approved
  2026-08-26 (`progress/current.md`).

## Traceability

- R1 (FR-AI-14) → `test_resolve_prompt_version_registry_carries_every_expected_version`, `test_prompt_instructions_version_is_frozen`
- R2 (FR-AI-14) → `test_resolve_prompt_version_registry_carries_every_expected_version` (registry is append-only by construction; single retained `v1` asserted present)
- R3 (FR-AI-14) → `test_resolve_active_prompt_version_returns_the_version_named_by_the_config_key`
- R4 (FR-AI-14) → `test_build_instructions_raises_unknown_prompt_version_for_unregistered_id`, `test_resolve_prompt_version_raises_unknown_prompt_version_for_unregistered_id`, `test_resolve_active_prompt_version_raises_when_the_key_is_unset`, `test_resolve_active_prompt_version_raises_when_the_configured_id_is_unregistered`
- R5 (FR-AI-14) → `test_build_instructions_sources_content_from_the_named_version`, `test_build_instructions_matches_the_module_constants`
- R6 (FR-AI-14) → `test_resolve_prompt_version_registry_carries_every_expected_version`
- R7 (FR-AI-14) → `test_resolve_active_prompt_version_returns_the_version_named_by_the_config_key`, `test_resolve_active_prompt_version_reads_the_config_port_exactly_once`

`FR-AI-14` → R1-R7 (all above). No other `FR-*` in this feature's `covers` array.

## Test result

`./init.sh` green: 249 tests (237 → 246 → 249, +3 post-review for
`test_config.py`). ruff format/check, mypy strict, pytest, prettier/eslint/vitest
all pass.

## Post-review fix

Reviewer finding: `backend/core/tests/ports/test_config.py` did not exist —
`EnvConfig.get` (the production adapter for FR-AI-14's deployment
configuration) was unverified; a wrong-key/prefix mutant and a `return None`
mutant both survived. Added the module (mirrors `tests/ports/test_clock.py`'s
pattern). Confirmed both named mutants now die:
- `os.environ.get(f"PLANNER_{key}")` (prefix bug) → `test_env_config_satisfies_the_config_port_and_reads_the_exact_key` fails.
- `return None` unconditionally → same test fails.
Both reverted; `config.py` confirmed byte-identical to pre-mutation source.
`./init.sh` green afterward: 249 tests.

## Deviations / things the spec didn't anticipate

- `test_no_ambient_time.py`'s `SYSTEM_CLOCK` scan (`test_no_core_module_but_the_port_names_the_real_clock`)
  flagged `config.py`'s docstring for literally naming `SystemClock` in prose
  (design.md's own §3 docstring draft does this). Reworded to describe it
  without the literal name — no behavioural change, no test file touched.
- The same guard's `test_week_calendar_tests_never_call_an_ambient_clock`
  flagged `test_prompt_version.py` for containing the substring
  `resolve_live_weeks` in a comment (unrelated to Clock, just text matching).
  Reworded the comment to drop the literal name.
  Both are source-scan false positives from prose mentioning unrelated
  identifiers, not design or layering issues; no scan file was modified, per
  `docs/architecture.md` §1.2.2 ("Read the module" — the guard is the
  authority, not something to loosen).
- Added one extra domain test beyond `tasks.md` T7's enumerated list —
  `test_build_instructions_sources_content_from_the_named_version` — to prove
  `build_instructions` genuinely reads the named version's content rather
  than happening to match the module constants (temporarily registers and
  removes a second version; leaves `PROMPT_INSTRUCTION_VERSIONS` unchanged
  otherwise).

## v2 (English) prompt wording — 2026-09-11

Owner correction: AI generation prompts sent to Bedrock should be in
**English**, not Spanish — English tokenizes more efficiently. Scope: instruction
*wording* only. `FR-AI-07` (model output in Castilian Spanish) untouched —
`OUTPUT_LANGUAGE = "es-ES"` and every version's `output_language` field stay
`"es-ES"`, including `v2`'s. `Unit`/`IngredientCategory` enum values (`unit.value`
/ `category.value`, interpolated at render time) untouched — fixed Spanish domain
vocabulary, `FR-LIB-05`/`FR-LIB-03`, a different concern. Exercises this
feature's own already-approved R1/R2/R6 (append-only registry) — no new
requirement, no `spec_author` round.

### Files touched

- `backend/core/src/planner_core/domain/ai_prompt.py` — added 8 new `_V2` module
  constants (`HEALTHY_BALANCED_INSTRUCTION_V2`, `RECIPE_METADATA_INSTRUCTION_V2`,
  `JSON_OUTPUT_INSTRUCTION_V2`, `OUTPUT_LANGUAGE_TEMPLATE_V2`,
  `ALLOWED_UNITS_TEMPLATE_V2`, `CATEGORY_FRAMING_TEMPLATE_V2`,
  `SPECIFICATION_FRAMING_TEMPLATE_V2`, `REFERENCE_FRAMING_TEMPLATE_V2`), English
  translations of v1's Spanish wording. No `OUTPUT_LANGUAGE_V2` constant — the
  *value* substituted for `${language}` stays `OUTPUT_LANGUAGE` ("es-ES") for
  both versions; only the template *label* wording changes. Added
  `PROMPT_INSTRUCTION_VERSIONS["v2"]` sourcing the new constants
  (`output_language=OUTPUT_LANGUAGE`, same as v1). `v1`'s entry and every v1
  constant are untouched (diff is purely additive).
- `backend/core/tests/domain/test_ai_prompt.py` — registry-set assertion now
  `{"v1", "v2"}`; added `test_healthy_balanced_instruction_v2_is_the_approved_english_wording`
  (literal-content assertion — catches a blanked constant, unlike comparing the
  constant to itself), `test_resolve_prompt_version_v2_carries_the_english_wording`,
  `test_build_instructions_v2_sources_from_the_v2_constants`. All pre-existing
  v1 tests pass unchanged (proves v1 untouched).
- `backend/lambda_ai/tests/test_bedrock.py` — added
  `test_render_is_version_agnostic_and_renders_v2_english_wording`, a v2-parallel
  case of the F5 render test (same structural assertions, `_render`/`bedrock.py`
  needed no code change — it was already a pure version-agnostic assembler).
- `backend/core/tests/test_no_recipe_metadata_logic.py` (feature 25 guard) —
  `AI_PROMPT_SANCTIONED_LINES` gained two v2 patterns for
  `JSON_OUTPUT_INSTRUCTION_V2`'s English `servings`/`estimated_time` JSON-key
  mentions (mirrors v1's exemption exactly).
  `RECIPE_METADATA_INSTRUCTION_V2` was worded to say "diners" rather than the
  literal word "servings" — same choice v1's Spanish wording ("numero de
  comensales") already makes — so it needs no separate exemption.

### R1/R2/R6 traceability (unchanged requirements, new data)

- **R1** (distinct, immutable value carrying its own version identifier) —
  `test_prompt_instructions_version_is_frozen` (existing, covers the dataclass
  shape both versions share) + `test_resolve_prompt_version_v2_carries_the_english_wording`
  (v2's `version_id == "v2"` alongside its own content).
- **R2** (retain every version, including superseded ones) —
  `test_resolve_prompt_version_registry_carries_every_expected_version`
  (`{"v1", "v2"}` — v1 still present, not superseded/removed) +
  `test_healthy_balanced_instruction_is_non_empty` / the other unchanged v1
  literal tests, proving v1's content is byte-identical to before.
- **R6** (every retained version retrievable by its version identifier) —
  `test_resolve_prompt_version_v2_carries_the_english_wording` (`resolve_prompt_version("v2")`)
  alongside the existing `resolve_prompt_version("v1")` coverage.

### Mutation probe

Blanked `HEALTHY_BALANCED_INSTRUCTION_V2` to `""`. First attempt — comparing
`version.healthy_balanced_instruction == HEALTHY_BALANCED_INSTRUCTION_V2` — did
**not** catch it (both sides import the same blanked constant, a
self-comparison). Added the literal-content test
(`test_healthy_balanced_instruction_v2_is_the_approved_english_wording`,
mirroring v1's `test_healthy_balanced_instruction_is_non_empty`), which failed
correctly against the blank. Reverted by hand; diffed byte-identical to the
pre-mutation source.

### Test result

`./init.sh` green — **773 passed** (769 → 773, +4: 3 new `test_ai_prompt.py`
cases + 1 new `test_bedrock.py` case). ruff format/check, mypy strict,
prettier/eslint/vitest all pass. No `feature_list.json` status change (stays
`in_progress`, owner's to close), no frozen-doc edit, no commit.

### Fix round — 2026-09-11 (reopen)

`RECIPE_METADATA_INSTRUCTION_V2` had the same self-comparison gap as
`HEALTHY_BALANCED_INSTRUCTION_V2` above. Added
`test_recipe_metadata_instruction_v2_is_the_approved_english_wording`
(literal English wording, mirrors the v1 and healthy-balanced-v2 tests);
blanking the constant now fails it, confirmed and reverted by hand. Also
reworded the stale "Spanish string" comment in `bedrock.py`'s `_render`.
`./init.sh` green — **774 passed** (773 → 774, +1). No `feature_list.json`
change, no commit.
