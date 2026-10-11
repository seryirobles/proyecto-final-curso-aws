# ai_fallback_recipe - Design

Layer: `core/domain` only (`docs/architecture.md` section 3). The versioned wording
lives in `planner_core/domain/ai_prompt.py`; `lambda_ai`'s `_render` and the
`AiProvider` port are untouched, because `_render` already emits
`healthy_balanced_instruction` for every mode. No API, persistence or frontend change.

## Ordering constraint

Issues 15-17 are `in_progress` and touch the same `v4` code (`ai_prompt.py`,
`test_ai_prompt.py`, the staged dish-framing tests). Implementation of this feature
starts only after they are `done`, or when the owner says to start anyway.

## Owner decisions (2026-10-11)

1. **Edit `v4` in place, no `v5`.** `v4` is unreleased. Accepted consequence: feature 34
   and issue 17 share `v4`'s text, so a recipe generated under `v4` cannot be traced to
   which of the two wording changes produced it (FR-AI-14 traceability). Issue 17's
   guard stays valid: `v4` is still `v3` with only `healthy_balanced_instruction` replaced.
2. **Keep the 422** for empty `ingredients` / `tools` (R14, R15). Blank strings and
   generic text still reach the model; the fallback covers them.
3. **Scope: single-recipe only** (specification and reference). The week prompt receives
   the sentence inert through the shared line (R4); it carries no
   ingredients/tools/specifications. "Unusable week input" is not defined.
4. **A lettered Part is wanted**; the leader writes it (see below).
5. **English wording accepted.**

## Design

`HEALTHY_BALANCED_INSTRUCTION_V4` gets one more sentence appended. `PROMPT_INSTRUCTION_VERSIONS["v4"]`
is otherwise unchanged. The model decides whether the input is unusable; code does not
classify it (R13). Proposed wording:

> If the ingredients, tools or specifications below are empty, generic, unrelated to
> cooking or unintelligible (for example "test"), ignore the unusable part and still
> produce one valid dish that follows these guidelines; honour any part that is usable.

Constraints from issue 17's tests
(`issues/generated-recipe-title-is-the-instruction/tests/backend/lambda_ai/tests/test_prompt_dish_framing.py`,
read-only), all pinned by R17/R11/R8/R9 here:
- the regex `\bgenerate\b[^.\n]*\bmenu` must not match: the sentence uses "produce" and
  never pairs "generate" with "menu" in one sentence;
- the "one dish" and "name ... dish" wording tests keep passing because the existing v4
  sentences stay untouched and the new one only adds to them;
- the FR-AI-06/07 word guard (healthy, balanced, protein, medical, es-ES) still holds;
- `test_v4_differs_from_v3_only_in_the_healthy_balanced_instruction` compares against
  `HEALTHY_BALANCED_INSTRUCTION_V4`, so the constant is edited, not a new one added;
- `test_ai_prompt.py` asserts `set(PROMPT_INSTRUCTION_VERSIONS) == {"v1".."v4"}`: unchanged.

The reference recipe is always usable input, so reference mode with unusable extra
specifications still adapts the reference (R7). Selecting `v4` stays deployment
config (`AI_PROMPT_VERSION_ID`); the default is not changed here.

## What tests cannot prove

Deterministic tests (no network) pin: the wording is present in the rendered
specification, reference and category prompts (R2-R4); it names the four cases (R5),
the guidelines and the keep-usable-parts clause (R6, R7); other lines equal `v3`'s
(R12); `v1`-`v3` unchanged (R10); `v4` is `v3` plus one field (R11); validation unchanged
(R14, R15); issue 17's regex still passes (R17). They cannot show that Nova 2 Lite,
given "test"/"test", returns a real recipe instead of the placeholder.

**Probe (owner runs it; agents run nothing paid).** An uncommitted script in the
scratchpad, not in the repo: it imports `build_specification_prompt` /
`build_reference_prompt`, renders each through `planner_ai.adapters.bedrock._render`
with `v4` before the edit (baseline, from the issue-17 text) and after, calls Converse
with the worker's settings (`AI_MODEL_ID`, same forced tool), 3 calls per cell, and
prints the recipe name and procedure. Matrix: `test`/`test`; `""`/`""`; `asdfgh`/`qwerty`;
`coche`/`semaforo` (unrelated); `comida`/`cosas` (generic); reference + `asdf`; control
`pollo`/`sarten` (must still use chicken). Pass: each unusable cell gives a named dish
whose procedure is not the generic two-step placeholder, and the control is unchanged.
Fail: report the cell; the wording is revised.

## Files

| File | Change |
|---|---|
| `backend/core/src/planner_core/domain/ai_prompt.py` | append the sentence to `HEALTHY_BALANCED_INSTRUCTION_V4`; update its docstring |
| `backend/core/tests/domain/test_ai_prompt_fallback.py` | new: registry tests (R1, R10, R11, R12, R16) |
| `backend/lambda_ai/tests/test_prompt_fallback_wording.py` | new: rendered-text tests per mode (R2-R9, R17) |
| `backend/lambda_api/tests/` (existing single-recipe request tests) | add R14, R15 only if no test already pins them |

New signatures: none. New exceptions: none.

## What would need a Part (`docs/gaps_and_resolutions.md`; the leader writes it, not this spec)

- One new lettered Part (next after AC) with a `G-nn` recording the owner request as a
  refinement of FR-AI-01/-02: unusable single-recipe input yields one dish following
  the general guidelines. Owner decision 4. Include decision 1 (shares unreleased `v4`
  with issue 17) and decision 2 (empty lists stay 422, so no contract change).
- No amendment of FR-AI-04, the contract section 3.6 or G-89 is needed under decisions 2 and 3.
- Removed text is struck through, never deleted.

## Rejected alternatives

1. **Detect unusable input in code (stoplist, length or dictionary heuristic).** Deterministic
   and testable, but "generic / unrelated / unintelligible" in Spanish is open-ended; a
   heuristic misfires on real inputs ("ñoquis", "té") and still needs wording for the
   fallback case. The owner's phrasing leaves the judgement to the model.
2. **A second model call to classify the input first.** Gives an explicit signal, but doubles
   Bedrock calls against the NFR-AI-01 cap on every request to guard a rare case, and adds
   a failure path.
3. **A dedicated `fallback_instruction` field on `PromptInstructionsVersion`.** Allows
   per-mode wording and keeps the sentence out of week prompts, but changes the dataclass,
   the renderer and every retained version for one sentence, and breaks issue 17's
   `v4 == v3 + one field` guard.
