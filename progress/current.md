# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

- **Feature in progress:** 14 — `persistence_ports`
- **Started:** 2026-08-26
- **Agent:** implementer (working)

## Implementer plan (this run)

Plan: tasks T1..T30 from `specs/persistence_ports/tasks.md`. All 4 gate
questions resolved as designed (design.md §11); recipe_metadata_fields
(feature 25) done and committed, no change needed to this feature's design
per leader's brief — `LibraryRecipe` wraps `Recipe` by composition.

- implementer: T1–T30 complete, all ticked. Six ports
  (`accounts`/`recipes`/`weeks`/`rules`/`shopping_list`/`archive.py`) added
  verbatim per design.md §3; six fakes appended to
  `core/tests/support/fakes.py` (atomicity traps for
  `FakeAccountRepository.create/rename` and
  `FakeShoppingListRepository.acquire_lock` implemented as designed). Port
  conformance tests + 2 frozen-instance tests under `core/tests/ports/`;
  mechanical storage-agnosticism scan
  `core/tests/test_ports_are_storage_agnostic.py` (R7 import-allowlist scan,
  R10 AWS-SDK-name scan); application composition test
  `core/tests/application/test_persistence_fakes_compose.py`; contract suite
  (`backend/tests/contract/conftest.py` + 6 `*_contract.py` files).
  `./init.sh` green: 383 tests (up from 295).
  Two mechanical snags, not design deviations: (1) task's planned
  `test_rules.py` collided on basename with the existing
  `domain/test_rules.py` under pytest's import mode — ticked as
  `test_rule_repository.py` instead; (2) a second `conftest.py` tripped
  mypy's duplicate-module check against `core/tests/conftest.py` — fixed
  with two empty package markers (`backend/tests/__init__.py`,
  `backend/tests/contract/__init__.py`), no `pyproject.toml` change.
  Traceability map in `progress/impl_persistence_ports.md`. Awaiting
  reviewer.
- reviewer: CHANGES_REQUESTED, 2 findings, 2 mutants survived (lock-expiry
  `>=`/`>` boundary in `fakes.py:206` untested; storage-agnostic scan's
  allowlist admitted `sqlite3`/`dbm`/`shelve` as "stdlib" and the bare
  `planner_core` package as wider than intended).
- implementer (fix pass): added the `now == expires_at` boundary test to
  both `core/tests/ports/test_shopping_list.py` and
  `backend/tests/contract/test_shopping_list_repository_contract.py`; added
  a `DENYLIST_STORAGE_MODULES` check plus a narrowed
  `planner_core.domain`/`planner_core.ports`-only allowance to
  `test_ports_are_storage_agnostic.py` (full dotted import paths now
  tracked, not just top-level segments). All three named mutants
  (`>=`→`>`, `import sqlite3` in `ports/rules.py`, `import
  planner_core.application` in `ports/rules.py`) verified caught and
  reverted; regression mutant (`import pytest` in `ports/weeks.py`) still
  caught. `./init.sh` green: 385 tests. Report updated in
  `progress/impl_persistence_ports.md`. Awaiting reviewer.
- reviewer (cheap verification, same agent resumed): re-applied both named
  mutants (`>=`→`>` in `fakes.py`, `import sqlite3` in `ports/rules.py`) —
  both killed. Spot-checked the narrowed allowlist with a planted
  `planner_core.application` import — caught. Regression check on the
  original `import pytest` mutant — still caught. `./init.sh` green (385
  tests), tree restored (`git status --porcelain` unchanged at 29 entries).

```
APPROVED — 0 findings, 0 mutants survived
```

## Next step

Ready for human sign-off: `specs/persistence_ports/`,
`backend/core/src/planner_core/ports/{accounts,recipes,weeks,rules,shopping_list,archive}.py`,
`backend/core/tests/support/fakes.py`,
`backend/core/tests/ports/{test_accounts,test_recipes,test_weeks,test_rule_repository,test_shopping_list,test_archive}.py`,
`backend/core/tests/test_ports_are_storage_agnostic.py`,
`backend/core/tests/application/test_persistence_fakes_compose.py`,
`backend/tests/contract/` (six suites + `conftest.py` + `__init__.py`),
`backend/tests/__init__.py`, and `progress/impl_persistence_ports.md`.
Marking `done` and committing are human-only.

## Prior session (feature 25) — closed

Feature 25 `recipe_metadata_fields` is `done` and committed (`4e89d02`).
Reviewer's second round returned `APPROVED — 0 findings, 0 mutants survived`.
Full log moved below for reference; will be archived to `history.md` at
session close.

## Plan

Feature 13 (`rollover_job_logic`) is `done` and committed (`f94f13c`), tree
clean. `./init.sh` reports feature 14 — `persistence_ports` (tier 2,
`sdd: true`, depends_on [5, 6, 8] `week_plan_model`/`rules_model`/
`shopping_list_state`, all done, pending) as the next actionable feature.

Covers NFR-BKP-01. Repository interfaces (`typing.Protocol`) for accounts,
recipes, weeks, rules, the shopping list and the archive, plus in-memory
fakes and a contract-test harness parametrized to run against any
implementation. Closes P1 (`docs/architecture.md` §1.2.1); does not decide
P6 (deployment topology, human-owned).

Per SDD flow: spec_author writes
`specs/persistence_ports/{requirements,design,tasks}.md`, sets status to
`spec_ready`, then STOP for human approval gate.

## Log

- Leader: confirmed feature 13 done/committed, archived session to
  `history.md`, ran `./init.sh` (green, 295 tests) — next actionable
  feature confirmed as 14.
- spec_author: `spec_ready -> specs/persistence_ports/`. Six `Protocol`
  ports (`AccountRepository`, `RecipeRepository`, `WeekRepository`,
  `RuleRepository`, `ShoppingListRepository`, `ArchiveRepository`), fakes in
  `core/tests/support/fakes.py`, one parametrized contract suite per port
  under `backend/tests/contract/`, mechanical storage-agnosticism scan
  mirroring `test_no_ambient_time.py`. `feature_list.json` status flipped
  to `spec_ready` (single-line `Edit`, `git diff` confirms). 4 rejected
  alternatives (§9), 2 flagged pre-existing gaps not fixed here (§7), 4 gate
  questions (§11). Leader read `design.md` in full and verified the
  `feature_list.json` diff before presenting gate questions.

## Gate questions for the human (specs/persistence_ports/design.md §11)

1. **`AccountRepository` presupposes application-managed credential storage**
   (`password_hash`, `password_reset_required`) — consistent with the closed
   `docs/data_model.md` §1 (P1), but ahead of architecture §2 P2 (Cognito vs.
   application-managed) being formally decided. spec_author recommends
   accepting — P1's closure text names this feature as what it unblocks —
   flagged as the port most likely to be reshaped if P2 lands on Cognito.
2. **`Recipe` carries no `tiempo`/`numeroComensales`**, though
   `docs/data_model.md` §1 lists both on `DatosPlatoBiblioteca`/
   `DatosPlatoSemana` — a pre-existing feature-4 gap, not introduced here.
   `LibraryRecipe` persists only what `Recipe` actually carries.
   spec_author recommends treating this as a gap for whichever feature next
   touches `Recipe` to close, or striking the two attributes from
   `data_model.md` if the human considers them already dead.
3. **Six ports, one per aggregate**, rather than one consolidated interface
   or a finer split (e.g. a separate lock port for the shopping list).
   spec_author recommends accepting as designed.
4. **`ArchiveRepository` is deliberately minimal** — `get`/`save` only, no
   listing/browsing (`FR-ARCH-03`/`-04` stay with feature 19, blocked on
   P6). spec_author recommends accepting — `NFR-BKP-01` only requires
   past weeks be persisted, not browsable.

- Human: 1 acknowledged, leaning app-managed (P2 signal, informational —
  not a formal P2 decision). 3, 4 accepted as recommended.
- On 2, human overrode the recommendation: **`data_model.md` is the source
  of truth** — both `tiempo` and `numeroComensales` should exist, per
  recipe, settable manually or by AI. Leader searched every doc (`tiempo`
  had zero `FR-*`/gap backing anywhere; `numeroComensales` had `FR-AI-13`/
  `G-64`, but as deployment config). Raised the shopping-aggregation
  consistency risk `G-64` was written to prevent (mismatched per-recipe
  serving baselines corrupting summed ingredient quantities) — human
  confirmed: **purely informational, no logic attached**, resolving the
  risk (nothing left to corrupt).
- Leader: lifted the freeze — new **Part U / G-85** in
  `docs/gaps_and_resolutions.md` (supersedes `G-64`), amended `FR-LIB-03`,
  `FR-MENU-04`, `FR-AI-13` in `docs/requirements.md`. Also backfilled
  `docs/coverage_analysis.md`'s gap-index table, which had already drifted
  three gaps behind (`G-82`–`G-84`/Parts R–T missing) before this session —
  fixed while in there, plus the US9/US17 rows and the closing counter.
  Flagged a stale cross-reference in `G-84` (its "same class of config as
  FR-AI-13's servings" parenthetical) with an inline note rather than
  rewriting the historical record.
- **Ripple:** `Recipe`/`MealSnapshot` (feature 4, done), the AI prompt
  builder's `CONFIGURED_SERVINGS` (feature 11, done), and AI output
  validation (feature 12, done) now lag the amended requirements.
  `persistence_ports` (feature 14) needs **no** change itself —
  `LibraryRecipe` wraps `Recipe` by composition — but the human chose to
  run the rework **next, ahead of** feature 14 rather than in parallel or
  deferred.
- Leader: added feature 25 `recipe_metadata_fields` to `feature_list.json`
  (tier 1, `sdd: true`, `depends_on: [4, 11, 12]`, `covers:
  ["FR-LIB-03", "FR-MENU-04", "FR-AI-13"]`, pending) — 7 acceptance
  criteria drawn from `G-85`'s decision text. `./init.sh` green (295
  tests, 25 features valid, all 104 FR/NFR ids still covered) and confirms
  25 as next actionable, 14 correctly parked at `spec_ready`.
- spec_author: launching against feature 25.
- spec_author (1st attempt): failed mid-investigation — session-limit API
  error, before writing any file. No cleanup needed; retried clean.
- spec_author (2nd attempt): `spec_ready -> specs/recipe_metadata_fields/`.
  `Recipe`/`MealSnapshot` gain `servings: int | None = None`,
  `estimated_time: str | None = None` (append-only position, every
  existing construction site uses kwargs so nothing breaks). `ai_output.py`
  mirrors both fields, passthrough, no new failure mode.
  `candidate.py`'s `to_library_entry` copy-through patched (mechanically
  required, else library-save silently drops both fields). `ai_prompt.py`:
  `CONFIGURED_SERVINGS` and `PromptInstructions`/`PromptInstructionsVersion
  .servings` removed outright (not left dead). Mechanical scan
  (`test_no_recipe_metadata_logic.py`, mirrors `test_no_ambient_time.py`)
  proves no domain logic reads either field — full-module exemption for
  `recipe.py`/`ai_output.py`, line-level sanctioned exemption for
  `candidate.py`'s two copy lines only. Cross-feature spec maintenance
  (amending `specs/ai_prompt_builder/` and `specs/ai_prompt_versioning/`
  requirements) assigned to the implementer as T5 — precedent: feature 24
  already amended feature 11's requirements.md the same way. 12 tasks, 22
  `R<n>`s, 6 rejected alternatives (§8), 4 gate questions (§9). Verified
  `feature_list.json` diff: only feature 25's own status flipped — the
  pending→spec_ready on feature 14 predates this run.

## Gate questions for the human (specs/recipe_metadata_fields/design.md §9)

1. **Field types**: `servings: int | None = None`, `estimated_time: str |
   None = None` — free string for time (no unit imposed), unbounded int
   for servings (no floor/ceiling, matching `Ingredient.quantity`'s own
   precedent).
2. **`servings` removed outright** from `PromptInstructions`/
   `PromptInstructionsVersion`, not kept-but-unused — the stronger but more
   disruptive option, touching feature 11's and 24's already-`done` code
   and specs.
3. **`candidate.py`'s `to_library_entry`** (feature 5, done) gets a
   copy-through patch — mechanically required so library-saves don't
   silently drop the new fields; not scope creep.
4. **Cross-feature spec maintenance** (amending features 11/24's
   `requirements.md`) assigned to the implementer, not this document —
   matching feature 24's own precedent. Checked: feature 17 `ai_lambda`
   (blocked) doesn't cover `FR-AI-13`/`FR-LIB-03`, so nothing else needs
   touching.

- Human: 1, 3, 4 accepted as recommended. On 2, overrode design.md §8
  alternative E's rejection: the AI must be **instructed** to state
  servings and estimated time per recipe (not just passively "may" carry
  them) — flagged as an oversight in `G-85`'s own `FR-AI-13` rewrite, which
  struck the prompt-instruction clause without replacing it.
- Leader: lifted the freeze again — new **Part V / G-86** in
  `docs/gaps_and_resolutions.md` (corrects `G-85`, does not reverse it),
  re-amended `FR-AI-13` in `docs/requirements.md` to "shall instruct the
  model to state" instead of "may set." Synced `coverage_analysis.md`
  (gap index row, closing counter, US17 note). `git status` confirms only
  `docs/*` touched.
- Sending the correction back to spec_author (same agent, resumed with
  full context) to revise `specs/recipe_metadata_fields/design.md` §6/§8:
  un-reject alternative E, design the new instruction constant, decide
  whether it needs a new `PromptInstructions` field.
- spec_author: revised. `RECIPE_METADATA_INSTRUCTION` (new module constant,
  `HEALTHY_BALANCED_INSTRUCTION`'s shape) plus a `recipe_metadata_instruction:
  str` field on both `PromptInstructions`/`PromptInstructionsVersion`,
  replacing the removed `servings: int` field one-for-one (same field
  count, different meaning — an instruction to state a value, not a target
  the app supplies). R23-R25 added (25 total, still one SHALL/SHALL NOT
  each). Mechanical scan's field ban explicitly does NOT extend to
  `recipe_metadata_instruction` — different field, prompt content not a
  `Recipe` attribute, confirmed no substring collision with the banned
  identifiers. Gate questions 1/3/4 re-confirmed unaffected by the
  correction; question 2's resolution note rewritten (removal of `servings`
  stands, but it's replaced in kind, not left permanently smaller). One new
  gate question 5: exact wording of the instruction, which deliberately
  adds a second sentence telling the model not to scale ingredients off a
  stated servings count (mirrors `HEALTHY_BALANCED_INSTRUCTION`'s own
  second-sentence pattern) — flagged as a one-line edit to drop if judged
  an invented constraint.
- Human: gate question 5 accepted — keep the second sentence, matching
  what he'd already asked for in the original gate-question round.
- Leader: all 5 gate questions resolved. Flipped feature 25's status to
  `in_progress` (single-line `Edit`). Launching implementer against
  `specs/recipe_metadata_fields/`.

**Feature in progress: 25 — recipe_metadata_fields**
**Plan:** tasks from `specs/recipe_metadata_fields/tasks.md`.

- implementer: T1–T12 complete, all ticked. `Recipe`/`MealSnapshot` gain
  `servings`/`estimated_time`; `ai_output.py`/`candidate.py` copy-through
  patched; `ai_prompt.py`'s `CONFIGURED_SERVINGS` and `.servings` removed,
  `RECIPE_METADATA_INSTRUCTION`/`recipe_metadata_instruction` added. New
  mechanical scan `test_no_recipe_metadata_logic.py` (R18-R22). Cross-feature
  spec maintenance (T5) done via amendment blockquotes on
  `specs/ai_prompt_builder/requirements.md` and
  `specs/ai_prompt_versioning/{requirements,design}.md` — original text kept,
  not deleted. Trimmed a few docstrings to the 3-line ceiling and reworded
  two comments in `ai_prompt.py` to avoid the bare words "servings"/
  "estimated_time" outside the sanctioned sites, so they wouldn't trip the
  mechanical scan design.md §6 otherwise would have shipped tripping on its
  own signatures — comment wording only, no design deviation. `./init.sh`
  green: 316 tests (up from 295), `test_shared_kernel_guards.py` and
  `test_no_ambient_time.py` pass unmodified (`git diff --stat` empty).
  Traceability map in `progress/impl_recipe_metadata_fields.md`. Awaiting
  reviewer.
- reviewer: CHANGES_REQUESTED, 1 finding, 1 mutant survived (everything else
  clean). R18's guard matched only the literal string `"CONFIGURED_SERVINGS"`
  — renaming the constant (e.g. `DEFAULT_SERVINGS: Final[int] = 4`) defeated
  it; `INFORMATIONAL_METADATA` doesn't backstop it either (case-sensitive,
  designed for the per-recipe field names, not a deployment-config
  constant's name). Also flagged a false claim in
  `specs/recipe_metadata_fields/requirements.md`'s coverage map (R21
  doesn't rule out a renamed constant).
- implementer: fixed. Added an AST-based structural scan,
  `test_ai_prompt_declares_no_top_level_int_constant`, banning any
  top-level `int`/`Final[int]` constant in `ai_prompt.py` by any name —
  scoped to that module rather than all of `planner_core` because
  `password_policy.py`/`rules.py` declare legitimate, unrelated `Final[int]`
  constants elsewhere (a package-wide ban would false-positive). Added a
  self-test planting the mutant shape via `tmp_path`, plus verified directly
  against the real mutant (temporarily renamed `CONFIGURED_SERVINGS` in
  `ai_prompt.py` itself, confirmed the new test fails, reverted — `git diff
  --stat` clean after). Corrected the false R21 claim in `requirements.md`'s
  coverage map. `./init.sh` green: 318 tests (was 316), guard files still
  unmodified. Traceability report updated. Awaiting re-review.
- reviewer (cheap verification, same agent resumed — not a second full
  review): re-applied the exact named mutant (`DEFAULT_SERVINGS: Final[int]
  = 4`) — killed by the new scan (1 failed, 317 passed). Reverted, tree
  byte-identical to pre-check. Confirmed no false-positive: all six real
  top-level constants in `ai_prompt.py` pass. R21 coverage-map claim now
  accurate. One non-blocking note recorded, not a finding: an unparametrized
  bare `Final = 4` (no `[int]`) would slip past the annotation check — not
  the named mutant, and this project's mypy-strict/`Final[T]`-everywhere
  convention makes that shape unlikely.

```
APPROVED — 0 findings, 0 mutants survived
```

## Next step

Ready for human sign-off: `specs/recipe_metadata_fields/`,
`backend/core/src/planner_core/domain/{recipe,ai_output,candidate,ai_prompt}.py`,
`backend/core/tests/test_no_recipe_metadata_logic.py`,
`specs/ai_prompt_builder/requirements.md`,
`specs/ai_prompt_versioning/{requirements,design}.md`, and
`progress/impl_recipe_metadata_fields.md`. Marking `done` and committing
are human-only. Once signed off, `persistence_ports` (feature 14) is
unblocked to move to `in_progress` next.
- reviewer: CHANGES_REQUESTED — 1 finding, 1 mutant survived. Everything
  else clean: traceability, coverage, layering, language check, comment
  ceiling, frozen-dataclass rule not re-triggered (verified), T5's
  cross-feature amendments match the shipped shape, mechanical scan
  confirmed real (planted violations in `shopping.py` and hidden inside
  `candidate.py`, both caught). Survived mutant: renaming
  `CONFIGURED_SERVINGS` to e.g. `DEFAULT_SERVINGS` (same deployment-wide
  target, new uppercase name) passes R18's guard untouched —
  `test_configured_servings_no_longer_appears_anywhere_in_ai_prompt`
  checks only the literal old name, and `INFORMATIONAL_METADATA` is
  case-sensitive lowercase-only, so it doesn't catch a renamed constant
  either. `specs/recipe_metadata_fields/requirements.md`'s coverage map
  also overclaims — it credits R21 with ruling this out, which is false
  under the current, narrower guard. Tree restored, byte-identical.
