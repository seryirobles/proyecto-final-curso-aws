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
