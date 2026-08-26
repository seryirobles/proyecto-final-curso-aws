# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

- **Feature in progress:** 24 — `ai_prompt_versioning`
- **Started:** 2026-08-26
- **Agent:** implementer

## Plan (feature 24)

Tasks T1-T9 from `specs/ai_prompt_versioning/tasks.md`: `ConfigPort`/`EnvConfig`
in `ports/config.py`; versioned registry (`PromptInstructionsVersion`,
`PROMPT_INSTRUCTION_VERSIONS`, `PROMPT_VERSION_CONFIG_KEY`,
`UnknownPromptVersion`, `resolve_prompt_version`) in `domain/ai_prompt.py`;
`build_instructions()` and the three builders gain `version_id: str`;
`application/prompt_version.py::resolve_active_prompt_version(config)`;
amend `specs/ai_prompt_builder/requirements.md` (feature 11) for the
signature change; `FakeConfig` in `tests/support/fakes.py`; extend
`test_ai_prompt.py` and add `test_prompt_version.py`; `./init.sh` green.

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

- Human: requested prompt versioning (a config to select which prompt
  version is used). No FR covered this; scoped as a new feature rather than
  reopening feature 11 before sign-off. Human lifted the freeze: new
  `docs/gaps_and_resolutions.md` Part T (`G-84`) and new `FR-AI-14` in
  `docs/requirements.md` (plus `US12`/`US17` crosswalk rows), both pasted in
  by the human. Leader added feature 24 `ai_prompt_versioning` (tier 1,
  `sdd: true`, depends_on [11], covers `FR-AI-14`) to `feature_list.json`.
- Leader: launching `spec_author` against feature 24, in parallel with
  feature 11's pending sign-off.

- spec_author: `spec_ready -> specs/ai_prompt_versioning/`. R1-R7, all citing
  `FR-AI-14`. `design.md` deliberately leaves the selection mechanism open
  (one gate question, §9) and rejects index-position-as-identity as an
  alternative. `tasks.md` has a shared T0/T1/T6/T8 plus branching T2-T7 for
  each option. Feature 24 status set to `spec_ready`.

## Gate question for the human (specs/ai_prompt_versioning/design.md §9)

Option A — constant-in-domain, like `CONFIGURED_SERVINGS`/`G-64`:
`ACTIVE_PROMPT_VERSION_ID` constant in `domain/ai_prompt.py`; no signature
change to feature 11's `build_instructions()`; activating a new version is
still a code change.

Option B — port pattern, like `Clock`: `PromptVersionSelector` Protocol in
`ports/`, no shipped default (selection genuinely differs by environment);
forces `build_instructions()` to take a `version_id: str` parameter and
pushes selection into a new `application/` function — a breaking change to
feature 11's not-yet-signed-off signature, needing an explicit spec
amendment.

- Human: gate question resolved — neither Option A nor B as spec'd. Chose a
  general, reusable **`ConfigPort`** (env-var-backed), following the exact
  `Clock` port shape (`docs/architecture.md` §1.2.2/§3.1 rule 6): a `Protocol`
  in `ports/`, default implementation reading `os.environ` as the sanctioned
  IO boundary, injected everywhere it's needed (never an ambient singleton),
  `wiring.py` the only place constructing the real one. Prompt version
  selection becomes its first consumer, not a one-off `PromptVersionSelector`.
  Scaffolding is intentionally general for future config needs beyond this
  feature.
- Leader: resuming `spec_author` to revise `specs/ai_prompt_versioning/`
  against the resolved gate.

- spec_author: revised, `spec_ready -> specs/ai_prompt_versioning/`, no gate
  question remaining. `design.md`: general `ConfigPort` (`Protocol` +
  `EnvConfig` default reading `os.environ`) in `ports/config.py`, shaped like
  `Clock`/`SystemClock`, injected, never a singleton; versioned-instruction
  registry + `UnknownPromptVersion` in `domain/ai_prompt.py`;
  `build_instructions()` and its three builders take a new `version_id: str`
  parameter; `application/prompt_version.py::resolve_active_prompt_version(config)`
  is where the port meets the domain value. Rejected alternatives: singleton
  (cites §3.1 rule 6, same reasoning as `Clock`'s ambient-time ban) and the
  narrow `PromptVersionSelector` (superseded by the generalization). `tasks.md`
  now one linear sequence, T1-T9.

**Flag for the human:** this changes feature 11's `build_instructions()`
signature (adds `version_id: str`) — a breaking change to a spec that's
implemented but not yet signed off. `tasks.md` T-item includes a feature-11
spec amendment for this. Worth deciding whether to sign off feature 11 as-is
first (then amend) or hold sign-off until feature 24 lands the signature
change.

- Human: approved. Confirmed feature 11's already-approved status stands, and
  is fine amending its `build_instructions()` signature as feature 24
  requires. Status set to `in_progress`.
- implementer: launching against `specs/ai_prompt_versioning/`, including its
  T-item amending `specs/ai_prompt_builder/` (feature 11) for the
  `version_id: str` signature change.

- implementer: T1-T9 complete. New `ports/config.py` (`ConfigPort`,
  `EnvConfig`), new `application/prompt_version.py`
  (`resolve_active_prompt_version`), `domain/ai_prompt.py` extended
  (`PromptInstructionsVersion`, `PROMPT_INSTRUCTION_VERSIONS`,
  `PROMPT_VERSION_CONFIG_KEY`, `UnknownPromptVersion`,
  `resolve_prompt_version`; `build_instructions()` + 3 builders gained
  `version_id: str`). `specs/ai_prompt_builder/requirements.md` amended
  (R6-R9, R13, R16, R19) per T5. `FakeConfig` added to `tests/support/fakes.py`.
  Two source-scan false positives hit and fixed by rewording prose (no scan
  file touched): `config.py`'s docstring named `SystemClock` literally, and
  `test_prompt_version.py` contained the substring `resolve_live_weeks` in an
  unrelated comment — both tripped `test_no_ambient_time.py`'s text scans.
  `./init.sh` green: 246 tests (237 -> 246, +9). Report:
  `progress/impl_ai_prompt_versioning.md`.

- reviewer: CHANGES_REQUESTED — one finding, everything else clean (coverage,
  traceability, architecture conformance, both source-scan false-positive
  claims, the feature-11 amendment). `EnvConfig.get` (`ports/config.py`) had
  no test at all; a wrong-key/prefix mutant and a `return None` mutant both
  survived.
- implementer: added `backend/core/tests/ports/test_config.py`, mirroring
  `tests/ports/test_clock.py`'s pattern (`isinstance(..., ConfigPort)` for
  both `FakeConfig` and `EnvConfig`; `monkeypatch.setenv` asserting the exact
  key comes back; `None` for an unset key). Confirmed both named mutants
  (`f"PLANNER_{key}"` prefix, unconditional `return None`) now fail the new
  test, then reverted `config.py` to byte-identical. `./init.sh` green: 249
  tests (246 -> 249, +3).

- reviewer: launched against `progress/impl_ai_prompt_versioning.md`,
  `config.py`, `prompt_version.py`, `ai_prompt.py`, the amended
  `specs/ai_prompt_builder/requirements.md`, mutation testing included.

- reviewer: CHANGES_REQUESTED. Everything else clean (coverage, traceability,
  architecture conformance — `ConfigPort` genuinely injected, no ambient
  `os.environ` read outside `EnvConfig`, both "false positive" scan claims
  verified genuine, feature-11 amendment checked line-by-line against the
  code). One finding: `EnvConfig.get` (`ports/config.py:31-32`) has no test —
  no `tests/ports/test_config.py` exists (C4 gap). One mutant survived
  (wrong-key / hardcoded-`None` variant of `EnvConfig.get`), all others
  killed. Tree restored, all gates reverified green.
- Leader: sending the finding back to the implementer — add the missing test
  module, mirroring `tests/ports/test_clock.py`'s pattern (fake +
  `@runtime_checkable` isinstance check + real adapter via `monkeypatch`). No
  design change.

- implementer: added `backend/core/tests/ports/test_config.py`. Confirmed
  both named mutants (`f"PLANNER_{key}"` prefix bug, unconditional `return
  None`) now die, then reverted `config.py` to byte-identical. `./init.sh`
  green: 249 tests (246 -> 249, +3). Report updated:
  `progress/impl_ai_prompt_versioning.md`.
- Leader: sending a narrow verification request back to the same reviewer
  (re-apply the two named mutants, confirm kill, don't re-run the full
  review) per the cheap-verification convention.

- reviewer: APPROVED. Both named mutants re-applied and killed by the new
  `test_config.py`; tree confirmed byte-identical to pre-mutation
  (`config.py` md5 unchanged). `./init.sh` green: 249 tests.

## Next step

Ready for human sign-off: review `specs/ai_prompt_versioning/`,
`backend/core/src/planner_core/ports/config.py`,
`backend/core/src/planner_core/application/prompt_version.py`,
the `version_id` changes in `backend/core/src/planner_core/domain/ai_prompt.py`,
the amended `specs/ai_prompt_builder/requirements.md` (feature 11), and
`progress/impl_ai_prompt_versioning.md`. Marking `done` and committing are
human-only. Feature 11 itself remains separately awaiting sign-off too.
