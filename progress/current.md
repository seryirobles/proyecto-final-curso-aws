# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

## 2026-09-11 — feature 17/27 committed; correction reopens feature 24

Owner committed the bundle as `1944822 feat: ai generation lambda`;
feature 16, 17, 27 all `done`. Tree clean.

**Owner correction:** AI generation prompts sent to Bedrock should be in
**English**, not Spanish — more token-efficient. Scope check: FR-AI-07
governs the model's OUTPUT language only (`OUTPUT_LANGUAGE = "es-ES"`
untouched); this is instruction wording only, not user-facing text
(`rest_api_contract.md` §3.0's wire-vs-UI-string boundary applies — an
internal Bedrock payload isn't user-facing, so English is not an
es-ES-policy violation). Category/unit *values* interpolated into the
prompt (`IngredientCategory`/`Unit`) stay Spanish — fixed domain
vocabulary, a different concern.

No new requirement needed: feature 24 `ai_prompt_versioning`'s own R1/R2/R6
(distinct immutable versions, all retained, all retrievable by id) already
specify exactly this operation. **No `spec_author` round** — reopened
feature 24 (`done -> in_progress`) directly to `implementer`: add
`PROMPT_INSTRUCTION_VERSIONS["v2"]` in English, `"v1"` (Spanish) retained
untouched per the append-only design. Also updates
`backend/lambda_ai/tests/test_bedrock.py` (v2 render case) and feature
25's `test_no_recipe_metadata_logic.py` sanctioned-line exemption (v2's
JSON-instruction mentions of servings/estimated_time need the same
allowlist entry v1's has). `bedrock.py` itself needs no code change — it's
already a pure version-agnostic assembler (this session's earlier F6).

**Implementer done.** `./init.sh` green — **773 passed** (+4). Only
feature 24's status changed in `feature_list.json` (mine, no drift).
`progress/impl_ai_prompt_versioning.md` got a full retroactive report
(this feature had none — pre-dates the report convention) plus the new
"v2 (English)" section. `v1` diff is purely additive (8 new `_V2`
constants + registry entry); `output_language` stays `"es-ES"` for both
versions. Own mutation probe caught a self-comparison test that didn't
actually verify content, fixed with a literal-content assertion.

**`reviewer` launched** for the delta (v1-untouched guarantee, v2
content real, `output_language` still es-ES, the feature-25 guard's new
exemption narrow, `conventions.md` language-policy read).

**Reviewer run — CHANGES_REQUESTED.** 1 finding, 1 mutant survived:
`RECIPE_METADATA_INSTRUCTION_V2` had no literal-content test (every v2
assertion on it was a self-comparison) — blank it to `""` and the whole
suite stayed green, meaning v2 could ship with no instruction telling
the model to state diners/prep-time and nothing would notice. 2
non-blocking notes: stale "Spanish" wording in a `bedrock.py` comment
(v2 is English now); v1/v2 template fields have no literal tests either
(pre-existing from feature 11, not required).

**Fix round — DONE.** Added the missing literal-content test (mirrors
the one for `HEALTHY_BALANCED_INSTRUCTION_V2`) + reworded the stale
comment. `./init.sh` green, 774 tests. No `feature_list.json` drift.

**Verification — APPROVED.** 0 findings, 0 mutants survived. Mutant
re-applied and killed (`AssertionError: '' == 'Also state t...'`), tree
restored (sha256-verified byte-identical), comment confirmed
language-neutral and accurate. `./init.sh` green — 774 passed.

**Feature 24's v2 (English prompt wording) reopen is complete and
reviewer-APPROVED.**

## Next step — OWNER

1. **Commit** — 8 changed files: `domain/ai_prompt.py`,
   `test_ai_prompt.py`, `test_no_recipe_metadata_logic.py`,
   `test_bedrock.py`, `bedrock.py` (comment only),
   `impl_ai_prompt_versioning.md`, `feature_list.json`. Small enough for
   one commit, e.g. `feat: version ai generation prompts in english`.
2. **Status:** feature 24 `in_progress -> done` (re-close). Yours alone.
3. **Deployment note for later:** activating v2 is a `ConfigPort`
   (`AI_PROMPT_VERSION_ID`) value — feature 21 IaC / deploy config, not
   code. Nothing in the tree defaults to a version id.

## 2026-09-11 — implementer DONE, awaiting reviewer

`domain/ai_prompt.py` gained 8 `_V2` constants (English translations of v1's
wording) + `PROMPT_INSTRUCTION_VERSIONS["v2"]` (`output_language=OUTPUT_LANGUAGE`,
same es-ES value as v1). No `OUTPUT_LANGUAGE_V2` — only the template's label
wording is English, the substituted value is unchanged. `v1` untouched (purely
additive diff). `bedrock.py::_render` needed no change — already version-agnostic.

Tests: `test_ai_prompt.py` (+3, registry set `{"v1","v2"}` + literal-content v2
test + `build_instructions("v2")` test), `test_bedrock.py` (+1, v2-parallel F5
render case, English wording), `test_no_recipe_metadata_logic.py` (feature 25
guard — 2 new sanctioned-line patterns for `JSON_OUTPUT_INSTRUCTION_V2`'s
English `servings`/`estimated_time` JSON-key mentions; `RECIPE_METADATA_INSTRUCTION_V2`
worded "diners" instead of "servings" so it needs no exemption, mirroring v1's
Spanish wording choice).

Mutation probe: blanked `HEALTHY_BALANCED_INSTRUCTION_V2`. First attempt (a
registry-value self-comparison) did NOT catch it — added a literal-content
assertion instead (mirrors v1's own pattern), which did. Reverted, byte-identical.

`./init.sh` green — **773 passed** (769 → 773). Report:
`progress/impl_ai_prompt_versioning.md` → "v2 (English) prompt wording —
2026-09-11". No `feature_list.json` change, no commit. Cheap `reviewer`
verification follows automatically.

### Log

- **Feature in progress:** 17 `ai_lambda` — SDD spec phase
- **Started:** 2026-09-06
- **Agent:** `spec_author` launching on a new `specs/ai_lambda/`

## 2026-09-06 — feature 16 closed by owner, feature 17 opened

Owner committed the reopen round (`a805aa5 feat: main lambda api`,
`9b428a5 chore: mark feature as done`) and flipped feature 16 -> `done`
plus feature 27 back to `done`. Tree clean. `./init.sh` green — 27
features, 20 done, 3 pending (17, 20, 26), 4 blocked, 694 tests.

`./init.sh` reports **feature 17 `ai_lambda`** as the next actionable
feature (`depends_on: [12, 14]`, both `done`). Status `pending` -> SDD
Case A: launch one `spec_author`, then stop at the human approval gate.

### Scope of feature 17

The `ai` Lambda worker shell: SQS consumer + AWS Bedrock provider adapter
+ cost-cap kill-switch (`NFR-AI-01`) + per-slot concurrency (`FR-AI-09`)
+ idempotent invocation + writing whole-week results through
`WeekRepository` (`G-88`). The generation *domain* logic already lives in
`planner_core` (features 10/11/12/24/25). Mirrors feature 16's
shell-vs-core split. `covers` = `{FR-AI-09, NFR-AI-01}` only.

### Log

- 2026-09-06 — Launched `spec_author` for feature 17 `ai_lambda`.
- 2026-09-06 — `spec_author` returned `spec_ready -> specs/ai_lambda/`
  (20 EARS reqs, `./init.sh` green, 694 tests) with 8 gate questions.

### Gate ruling — in progress (2026-09-06)

- **Q2 (attempt ordinal) — RULED.** Feature 17 does not implement
  `attempt`; it is a single-recipe-regenerate concern. Owner: don't leave
  it hanging, but not by reopening 3 `done` features + a frozen-contract
  edit. **New feature 28 `single_recipe_generation`** added (`pending`,
  tier 3, `depends_on: [11, 12, 16, 17]`, `covers: []`). Owns the
  single-recipe `POST /v1/generations` body, the server-authoritative
  `attempt` fold, and the `ai` worker's single-recipe branch. Its first
  acceptance item is an owner-owned `rest_api_contract.md` lift (§3.5/§7
  document only `type:"week"` today). `./init.sh` green, 28 features,
  next actionable unchanged (26).
- **Q5 (Bedrock SDK) — RULED.** `boto3` (+ `moto` dev dep),
  `lambda_ai/pyproject.toml` only.
- **Q6 (model id) — RULED.** `BEDROCK_MODEL_ID = "anthropic.claude-sonnet-5"`
  module constant, `AI_MODEL_ID` env override.
- **Q7 (partial-failure surface) — RULED.** Worker writes `resultado` as
  `[{day, slot, status, message}]`, passed through verbatim; per-slot
  retry is client-side (feature 28 / frontend).
- **Q1 (cost-cap gate) — RULED.** `GenerationGate` port
  (`is_generation_enabled() -> bool`) + **SSM Parameter Store** adapter
  (`/planner/<env>/ai-generation-enabled`, ~5s TTL). Budget / Budget
  action / reserved-concurrency-0 / ESM-disable / SNS->Lambda flip = all
  feature 21 IaC, second layer. No data-model change.
- **Q3 (per-slot 409) — RULED.** Downgrade the whole-week
  `POST /v1/generations` 409 to **exact-hash-resubmit dedupe only**
  (`attribute_not_exists(PK)` already delivers it). Concurrent different
  whole-week runs allowed (FR-AI-11 additive + at-write definitive
  re-check). Deliberate deviation from `rest_api_contract.md` §3.5 /
  line 171 — owner reconciles the contract doc. True per-slot 409 -> f28.
- **Q4 (write-back port) — RULED.** `GenerationQueue` gains
  `claim(key) -> bool` (conditional `pending->running`, idempotent-
  invocation guard) + `record_result(key, status, per_slot) -> None`.
  **Feature 27 delta** (same pattern as the R31 `discard` reopen).
  Fake + `SqsGenerationQueue` + a new `planner_ai` adapter. Owner flips
  27 `done -> in_progress` when the implementer round starts.
- **Q8a (adapter copy) — RULED.** `planner_ai/adapters/` gets its own
  copy of `weeks.py` + `_table.py` + `_meal.py`; `test_week_repository_
  contract.py` parametrized over BOTH adapters so drift fails a test.
  No `architecture.md` edit, no shared workspace member.
- **Q8b (message enrichment) — RULED.** `GenerationQueue.submit`'s SQS
  message gains the resolved effective rules + prompt version id (api
  already computes them for the 202 body). Worker reads inputs from the
  message — no `RuleRepository` copy, no mid-generation TOCTOU
  (FR-AI-05). **Feature 27 delta** (the `submit` message payload).

### spec_author fold pass — done + one more delta (2026-09-06)

Round 1: all 8 rulings folded into `specs/ai_lambda/`; feature-27 delta
R36–R40 (Q4 `claim`/`record_result` + Q8b message enrichment), design
§3b/§6/§8/§9, tasks T34–T40. `./init.sh` green, 694 tests.

**New ambiguity the fold surfaced — pinned-slot candidate writing
(FR-AI-11).** Nothing writes the pinned-library-meal candidates for
pinned slots today; the worker is `open_slots`-only. **Owner ruled:**
api-synchronous, **feature-27 delta.** `generation_submission` grows a
`recipes: RecipeRepository` param + a user-id param and writes pinned
candidates on the fresh-submit path (reusing `new_candidate` /
`add_slot_candidate`). `FR-AI-11` cited-not-owned (feature 10). Accepted
edge: resubmit-after-partial-failure can double-write pinned candidates
(additive, consistent with Q3). Round 2 dispatched to `spec_author`
(R41…, T41…).

### spec_author fold — COMPLETE, one overstep corrected (2026-09-06)

Round 2 done. Final spec state:

- **`specs/ai_lambda/`** — R1–R21 (R21 = `FR-CAND-04` consumed-not-owned,
  candidate authorship). design §0–§12: SSM `GenerationGate`, the feature-27
  reopen surface, adapter copy + mandatory dual-adapter `WeekRepository`
  contract suite, message enrichment (+`authorUserId`), §9.1 the 409
  downgrade deviation, §10 fixed values, §11 three rejected alternatives.
  New ports `ai_provider.py` + `generation_gate.py`, new use case
  `application/week_generation.py`, the whole `planner_ai` shell.
- **`specs/rest_api_persistence_and_services/`** — delta R36–R43,
  T34–T43 (unchecked), design §2/§3b/§3c/§6/§8/§9. R36–R39 `claim` +
  `record_result`; R40 message enrichment; R41–R43 synchronous
  pinned-slot candidate writes (R43: idempotent-hit writes nothing).
  `covers` unchanged; `FR-AI-11`/`FR-CAND-04` added consumed-not-owned.

**Overstep:** the `spec_author` flipped feature 27 `done -> in_progress`
in `feature_list.json` (misattributed to the leader in its result). No
implementer is running; the spec is not approved; the owner reserved
that flip. **Leader reverted 27 -> `done`.** `./init.sh` green again —
694 tests, 28 features, next actionable 26. Feature 17 stays
`spec_ready` (the `spec_author`'s legitimate flip). Feature 28
untouched.

## 2026-09-06 — spec APPROVED, bundled implementer launched

Owner approved ("go"). Owner flipped feature 27 `done -> in_progress`;
leader flipped feature 17 `spec_ready -> in_progress`. Both `in_progress`
for the bundle — `./init.sh` §4 will flag the dual `in_progress` + the
16->27 dep order, inherent to the bundle (same as the 16+27 reopen),
resolves on the owner's `done` marks.

**One `implementer` launched** for both, in order:
1. Feature 27 delta — `specs/rest_api_persistence_and_services/tasks.md`
   T34–T43 (port `claim`/`record_result`, SQS adapter, `submit` message
   enrichment, `generation_submission` pinned-slot writes + `recipes`/
   `author` params, `routing.py` caller).
2. Feature 17 — `specs/ai_lambda/tasks.md` T1–T24 (ports `ai_provider` +
   `generation_gate`, `application/week_generation.py`, the `planner_ai`
   shell: bedrock/ssm/dynamo adapters, wiring, handler; dual-adapter
   `WeekRepository` contract suite).

Reports: `progress/impl_rest_api_persistence_and_services.md` ->
"Reopen round 2 2026-09-06", `progress/impl_rest_api_lambda.md` ->
"Feature 17 2026-09-06". `reviewer` launches automatically after.

## 2026-09-06 — implementer running (bundle)

- **Feature in progress:** 27 delta (T34–T43) then 17 (T1–T24)
- **Plan (27):** tasks T34–T43 from
  `specs/rest_api_persistence_and_services/tasks.md`
- **Plan (17):** tasks T1–T24 from `specs/ai_lambda/tasks.md`
- Decision: `GenerationQueue.submit` gains keyword-only params
  `effective_rules` / `prompt_version_id` / `author` (defaulted so existing
  call sites stay green) — the design's "serialisation change" needs the
  values at the producer, and `submit_generation` is its only caller.
  `submit_generation` gains `prompt_version_id: str` too (T41 under-specified
  the routing caller; routing resolves it via `resolve_active_prompt_version`).

## 2026-09-06 — implementer DONE (bundle), awaiting reviewer

Both features implemented in one run.

- **Feature 27 delta** — T34–T43 ticked. `GenerationQueue` port grew
  `claim` / `record_result` (+ a `GenerationResultSink` base Protocol) and
  `submit` grew defaulted `effective_rules` / `prompt_version_id` / `author`
  kwargs; `SqsGenerationQueue` claim/record_result + enriched message body;
  `generation_submission` writes pinned-slot candidates on the fresh path +
  takes `recipes` / `author` / `prompt_version_id`; `routing._submit_generation`
  wires them (prompt id via `deps.config.get(PROMPT_VERSION_CONFIG_KEY)` —
  raw, worker validates). Report: `progress/impl_rest_api_persistence_and_services.md`
  → "Reopen round 2".
- **Feature 17 `ai_lambda`** — T1–T24 ticked. New ports `ai_provider` /
  `generation_gate`; use case `application/week_generation.py`; the whole
  `planner_ai` shell (dynamo copy + `generations.py`, `bedrock.py`, `ssm.py`,
  `message.py`, `wiring.py`, `handler.py`). Dual-adapter `WeekRepository`
  contract suite (T21). Report: **`progress/impl_ai_lambda.md`** (new file;
  the dispatch note said `impl_rest_api_lambda.md` but protocol is
  `impl_<spec-dir>.md`).

`./init.sh`: §5 fully green (762 passed, ruff/mypy/prettier/eslint/vitest).
§4 red only on the intentional dual `in_progress` (17 + 27) + the 16→27
dep-order check — clears on the owner's `done` marks.

## Implementer run — bundled (2026-09-06) — DONE

Both parts implemented in one run. `./init.sh` §5 green — **762 passed**
(+68). §4 fails only on the intentional dual `in_progress` (17 + 27) +
16->27 dep order. All T34–T43 + T1–T24 ticked. `feature_list.json` diff
is +21/-2 (the two status flips + feature 28 only — no implementer
meddling).

Implementer-flagged deviations (all in the reports):
1. `submit` gained defaulted enrichment kwargs (producer needs the values).
2. `prompt_version_id` reaches `submit_generation` from `routing` via raw
   config read (T41 under-specified it).
3. A `GenerationResultSink` base Protocol was split out so `planner_ai`
   need not implement `submit` — **note: design §11 rejected a write-only
   sink port**; reviewer to judge whether this crosses that line.
4. Bedrock `AiProvider` contract case uses a stubbed client, not moto.

Report filename: feature 17's is `progress/impl_ai_lambda.md` (not
`impl_rest_api_lambda.md` — that's feature 16's; dispatch note was wrong,
implementer corrected it).

## Reviewer run — bundled — DISPATCHED (2026-09-06)

Launched with tree-safety warning (uncommitted feature — file-copy backup
only, never git checkout/restore/stash). Briefed to scrutinise the 4
deviations (esp. #3 vs design §11), spec drift, G-88 scan teeth, the T21
dual-adapter contract suite, and the `claim`/`record_result` alias +
condition mutants.

## Reviewer run — bundled — CHANGES_REQUESTED (2026-09-06)

7 findings, **4 mutants survived**. FR->R coverage complete; tasks all
`[x]`; boundaries clean; `core` stdlib-only; the 4 implementer deviations
judged (deviation #3 `GenerationResultSink` split **ACCEPTED** — one
module, `GenerationQueue` still extends it, contract suite covers all
impls; #1 partially rejected -> finding 1; #3 prompt-version -> finding 2;
#4 stub accepted for the parse half). Tree restored byte-identical, all
by file copy.

**Required (fix round):**
1. **`message.py` + `submit` enrichment defaults — un-enriched message
   generates silently.** `_parse_rules(body.get("effectiveRules"))` turns
   missing/null into an empty `RuleSet`; combined with
   `effective_rules: RuleSet | None = None` on the port + adapter, a
   message that lost enrichment generates ignoring the user's confirmed
   category counts / pins / disabled days, then records `completed` —
   exactly what R40 exists to prevent. Make `effectiveRules` required
   like `promptVersionId`/`authorUserId`; add the test. (`ports/
   generation_queue.py:72`, `adapters/sqs.py:89`, `planner_ai/message.py:80`)
2. **`routing.py:737` bypasses feature 24.** `prompt_version_id =
   deps.config.get(PROMPT_VERSION_CONFIG_KEY)` duplicates
   `application/prompt_version.py::resolve_active_prompt_version` and
   drops its `UnknownPromptVersion` guard — unset/unknown key -> `202`,
   enqueues `promptVersionId: null`, worker fails *after* claiming (every
   slot lost). Also config resolution in the thin handler
   (`conventions.md` Packaging). Route through feature 24's use case.
3. **R8/R10 have no real test** (2 surviving mutants,
   `week_generation.py:106-107`). The only test seeds the definitive
   *before* the run so `resolve_targets` filters the slot and the
   at-write branch never runs. Add: a definitive promoted *between*
   `resolve_targets` and the write (`WeekRepository` whose 2nd
   `get_week` returns a now-definitive slot).
4. **T21 dual-adapter contract suite is vacuous** (owner-mandated).
   Parametrizes over the `planner_ai` copy but every case writes+reads
   the *same* adapter, so cross-copy key/attr drift is invisible
   (`SEMANA#...#drift` -> 18 passed). Add a cross-copy case: write with
   `planner_api`'s adapter, read with `planner_ai`'s, and back.
5. **`_render` uncovered (T15/R2 surviving mutant** — `_render` -> `""`,
   8 passed). Both `AiProvider` contract stubs discard `body`. Assert the
   rendered body carries `healthy_balanced_instruction`,
   `recipe_metadata_instruction`, `output_language`, the allowed-unit
   list and the category counts.
6. **Un-versioned prompt wording in `bedrock.py`** (`_JSON_INSTRUCTION`,
   "Genera una receta para un hueco abierto…", "Idioma de salida: …",
   "Unidades permitidas: …") — new Spanish prompt semantics outside
   `PROMPT_INSTRUCTION_VERSIONS` (feature 24's append-only registry,
   FR-AI-14/G-84). Editing them changes every prompt with no version
   bump. **OWNER CALL:** fold the render template into the versioned
   block, or rule adapter serialisation wording out of FR-AI-14 scope.
7. **Minor / leader-folds:** `specs/rest_api_persistence_and_services/
   design.md` §3c's `submit_generation` signature omits the
   `prompt_version_id` param the code added.

**Finding 6 — OWNER RULED: yes**, fold the render template into the
versioned block (`PromptInstructionsVersion` gains the JSON-output
instruction + per-mode framing; `v1` populated with the current strings;
`bedrock.py::_render` becomes a pure assembler, zero Spanish literals).
Cited `FR-AI-14` consumed-not-owned (feature 24).

## Fix round 1 — dispatched (2026-09-06)

One `implementer` for findings 1–6 + the finding-7 doc sync
(`submit_generation` signature after finding 2 moves prompt-version
resolution into the application layer via `config: ConfigPort` +
`resolve_active_prompt_version`). Reports append "Fix round 1" to both
impl files. Cheap `reviewer` verification follows.

## Fix round 1 — implementer DONE (2026-09-06)

All 6 findings + the finding-7 doc sync landed. `./init.sh` §5 green —
**769 passed** (762 → 769). §4 still red only on the intentional dual
`in_progress` (17 + 27) + the 16→27 dep order — unchanged, clears on the
owner's `done` marks. No `feature_list.json` status change, no commit.

- **F1** — `effectiveRules` now required on the SQS message parse
  (`message.py` `_require`); `submit`'s `effective_rules` lost its
  `| None = None` default (port + SQS adapter + fake). Un-enriched message
  → parse raises, worker never calls the provider.
- **F2** — `generation_submission` takes `config: ConfigPort` and resolves
  the prompt version through feature 24's `resolve_active_prompt_version`
  **before any write**; unset/unknown key → `UnknownPromptVersion` →
  `422 UNKNOWN_PROMPT_VERSION` (new `errors.py` mapping + `messages.py`
  constant). `routing.py` no longer reads config.
- **F3** — new `test_week_generation.py` test: a definitive promoted
  *between* `resolve_targets` and the write; kills both `:106-107` mutants.
- **F4** — new cross-copy case in `test_week_repository_contract.py`:
  write with `planner_api`'s adapter, read with `planner_ai`'s, and back.
  Proven vacuous-before: `SEMANA#…#drift` → 18 same-adapter cases pass, the
  cross-copy case fails.
- **F5** — new `test_bedrock.py` test asserts `_render`'s output carries
  the version wording + unit list + category counts; `_render` → `""` fails.
- **F6 (OWNER RULED yes)** — `_JSON_INSTRUCTION` + the framing/label prose
  moved into `domain/ai_prompt.py`'s `PromptInstructionsVersion` (`v1`
  populated **verbatim**, append-only intact). `bedrock.py::_render` is a
  pure `string.Template` assembler, zero Spanish literals. Cited **FR-AI-14
  consumed-not-owned** — NOT added to feature 17's or 27's `covers`.
  Feature 24 field-shape tests extended (green). `test_no_recipe_metadata_
  logic.py` gained a narrow sanctioned-line exemption for
  `JSON_OUTPUT_INSTRUCTION` (mirrors `CANDIDATE_SANCTIONED_LINES`) +
  verbatim guard — flagged for the owner re: the feature 25 spec doc.
- **F7** — `specs/rest_api_persistence_and_services/design.md` §2 + §3c
  synced to the `config: ConfigPort` signature.

Reports: `progress/impl_ai_lambda.md` + `progress/impl_rest_api_persistence_and_services.md`
→ "Fix round 1 — 2026-09-06". 5 mutation probes (F1, F3, F4, F5, F6) all
killed by the new tests, reverted by hand (file edits, no git).

## Fix round 1 — DONE (2026-09-06)

`./init.sh` §5 green — **769 passed** (762 -> 769). All 5 mutation probes
(F1/F3/F4/F5/F6) planted + killed by new tests, reverted by hand. No
`feature_list.json` change (statuses 17 + 27 still `in_progress`; 24 + 25
still `done`). F1–F7 all addressed:
- F2 added `422 UNKNOWN_PROMPT_VERSION` + moved prompt-version resolution
  into `submit_generation(config: ConfigPort)`.
- F6 moved the JSON + framing prose verbatim into
  `domain/ai_prompt.py` `PromptInstructionsVersion`/`PromptInstructions`
  `v1` (append-only intact); `bedrock.py::_render` is now a pure
  `string.Template` assembler. Cited `FR-AI-14` consumed-not-owned.
- **Owner note:** `test_no_recipe_metadata_logic.py` (feature 25 guard)
  gained a narrow sanctioned-line exemption + verbatim guard for the
  relocated metadata-instruction string — the feature 25 spec doc may
  now be slightly behind its guard. Non-blocking; flag at close.

## Verification run — APPROVED (2026-09-06)

0 findings, 0 mutants survived. All 5 fix-round mutants (F1/F3/F4/F5/F6)
re-applied and KILLED; a bonus feature-25 guard probe (`return
recipe.servings` in `ai_prompt.py`) also killed. F2 traced — prompt
version resolved in `submit_generation` after the idempotent-hit return,
before the pinned writes + enqueue; `422 UNKNOWN_PROMPT_VERSION` mapped.
F6 `domain/ai_prompt.py` diff is purely additive (6 new fields, `v1`'s
original 3 untouched). `bedrock.py` has zero Spanish literals. G-88
intact. Tree restored byte-identical. `./init.sh` §5 green — **769
passed**. §4 red only on the intentional dual `in_progress`.

**The bundle is implementation-complete and reviewer-APPROVED.**

## Next step — OWNER

1. **Commit** the bundle — 46 code/spec entries (feature 17 first commit
   + feature 27 reopen delta). `progress/current.md` stays uncommitted
   (wiped at session close). Suggested split (gga `TIMEOUT`=1200 on a
   changeset this size — see the gga-splits-large-commits memory):
   - `feat: generation queue claim/record-result and submit enrichment`
     — `ports/generation_queue.py`, `adapters/sqs.py`, fakes, the two
     contract suites, `messages.py`, `errors.py`, `_helpers.py`,
     `test_error_mapping.py`, `specs/rest_api_persistence_and_services/`.
   - `feat: synchronous pinned-slot candidates at generation submit`
     — `generation_submission.py` + its test, `routing.py`.
   - `feat: ai generation lambda worker` — all of `backend/lambda_ai/`,
     the new `planner_core` ports + `week_generation.py`, the new
     contract suites, `test_week_repository_contract.py`,
     `test_no_generation_quota.py`, `specs/ai_lambda/`.
   - `feat: version the full rendered ai prompt` — `domain/ai_prompt.py`,
     `test_ai_prompt.py`, `test_no_recipe_metadata_logic.py`,
     `bedrock.py` (the F6 slice; could also ride commit 3).
   - `chore: mark features done` — `feature_list.json` with 17 + 27
     both `done`.
2. **Status:** feature 17 `in_progress` -> `done` (its FIRST `done`);
   feature 27 `in_progress` -> `done` (re-close). Leader never sets these.

## Deferred — OWNER, later (none block anything)

- Contract lift (a): feature 28 single-recipe `POST /v1/generations`
  body + `attempt` derivation.
- Contract lift (b): reconcile the whole-week 409 downgrade (Q3) in
  `rest_api_contract.md` §3.5 / L171.
- **F5** (from feature 16): `EXPECTED_ROUTES` in `test_routing_table.py`
  is a hand-maintained literal — own feature or signed-off deferral.
- **Feature 25 guard/spec:** `test_no_recipe_metadata_logic.py` gained a
  sanctioned-line exemption for the relocated `JSON_OUTPUT_INSTRUCTION`
  lines; `specs/recipe_metadata_fields/` may want a one-line note that
  the metadata instruction now also lives in the versioned prompt block.

## Deferred — OWNER, later (neither blocks this round)

- Contract lift (a): feature 28's single-recipe `POST /v1/generations`
  body + `attempt` derivation.
- Contract lift (b): reconcile the whole-week 409 downgrade (Q3) in
  `rest_api_contract.md` §3.5 / L171.
- **F5** (carried from feature 16): `EXPECTED_ROUTES` in
  `test_routing_table.py` is a hand-maintained literal — own feature or
  signed-off deferral.

## Feature 28 — single_recipe_generation (added 2026-09-06)

`pending`, tier 3, `depends_on: [11, 12, 16, 17]`, `covers: []`. Owns the
single-recipe AI generation submit-then-poll path that feature 12
explicitly deferred: the contract body shape (owner lift), the
server-authoritative `attempt` fold, the domain single-recipe request
type + key, the `ai` worker's single-recipe branch, the per-slot 409.
Not actionable until 17 is `done`.

### Carried forward (feature 16, non-blocking)

- **F5** — `EXPECTED_ROUTES` in `backend/lambda_api/tests/test_routing_table.py`
  is a hand-maintained literal, not derived from `docs/rest_api_contract.md`.
  Owner to pick a home: its own small backlog feature or a signed-off
  deferral. Not urgent; feature 16 closed without it.
