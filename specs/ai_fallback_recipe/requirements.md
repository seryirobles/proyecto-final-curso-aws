# ai_fallback_recipe - Requirements

Depends on: feature 17 (`ai_lambda`), done. Shares prompt `v4` with issues 15-17 (see ordering note in `design.md`).

## Source

`feature_list.json` feature 34 has `covers: []`: no frozen `FR-*` is claimed. The
source is the owner request of 2026-10-11, verbatim:

> Como fallback, si no hay entrada o es genérica, no relacionada o ininteligible,
> que cree una receta cualquiera que siga las indicaciones generales

Trigger: ingredient "test" plus tool "test" in a specification request produced a
placeholder recipe ("Paso 1: Preparar los ingredientes / Paso 2: Cocinar según receta").
`Implements:` cites the existing ids the behaviour serves: FR-AI-01 and FR-AI-02
(single-recipe inputs), FR-AI-04 (week prompt), FR-AI-06 and FR-AI-07 (the "general
guidelines"), FR-AI-14 (wording is versioned). No new product requirement is
invented; the Part the owner wants is listed in `design.md`.

## Owner decisions (2026-10-11)

1. Edit `v4` in place: append the fallback sentence to the existing `v4`
   `healthy_balanced_instruction`. No `v5`.
2. Keep the 422 for empty `ingredients` / `tools` lists (R14, R15).
3. Scope is single-recipe (specification and reference). Week prompts receive the
   sentence inert through the shared line (R4).
4. A lettered Part (next after AC) recording the request is wanted; the leader writes it.
5. The English wording is accepted.

## Findings that bound the scope (verified in code, 2026-10-11)

- Specification source: an EMPTY `ingredients` or `tools` list is rejected before the
  prompt, `422 MISSING_INGREDIENTS` / `MISSING_TOOLS` (`single_recipe_submission.py`,
  `rest_api_contract.md` section 3.6). Empty or blank STRINGS inside a non-empty list
  are accepted (`_string_list` only checks types), and so is "test".
- Reference source: `extraSpecifications` must be present but may be `[]`; it reaches
  the prompt (`Specifications: .`). The reference recipe itself is always usable input.
- Week mode: the prompt carries category counts and rules, no free text.
- The wording is a model decision. Tests can pin that the wording is present; only a
  live probe shows the model obeys it (`design.md`, "What tests cannot prove").

## R1
Implements: FR-AI-14

The `v4` healthy-balanced instruction SHALL end with the fallback sentence.

## R2
Implements: FR-AI-01, FR-AI-14

WHEN a specification prompt is rendered with `v4`, the rendered text SHALL contain the fallback instruction.

## R3
Implements: FR-AI-02, FR-AI-14

WHEN a reference prompt is rendered with `v4`, the rendered text SHALL contain the fallback instruction.

## R4
Implements: FR-AI-04, FR-AI-14

WHEN a category prompt is rendered with `v4`, the rendered text SHALL contain the fallback instruction (the line is shared by all modes; owner decision 3).

## R5
Implements: FR-AI-01, FR-AI-02

The fallback instruction SHALL name each of the four cases: empty, generic, unrelated to cooking, and unintelligible.

## R6
Implements: FR-AI-01, FR-AI-02, FR-AI-06

The fallback instruction SHALL direct the model to produce one dish that follows the general guidelines when the user-supplied input is unusable.

## R7
Implements: FR-AI-01, FR-AI-02

The fallback instruction SHALL direct the model to keep honouring any part of the input that is usable.

## R8
Implements: FR-AI-06

WHEN a prompt is rendered with `v4`, the rendered text SHALL contain the healthy, balanced, protein-varied and non-medical guidance.

## R9
Implements: FR-AI-07

WHEN a prompt is rendered with `v4`, the rendered text SHALL contain the es-ES output-language directive.

## R10
Implements: FR-AI-14

The registry SHALL render versions `v1`, `v2` and `v3` byte-identically to their rendering before this feature.

## R11
Implements: FR-AI-14

The registry SHALL keep `v4` equal to `v3` with only the healthy-balanced instruction replaced (issue 17's guard `test_v4_differs_from_v3_only_in_the_healthy_balanced_instruction`).

## R12
Implements: FR-AI-01, FR-AI-02

WHEN a prompt is rendered with `v4`, every line except the healthy-balanced instruction SHALL equal the same line rendered with `v3`.

## R13
Implements: FR-AI-01

The specification prompt builder SHALL pass the user-supplied ingredient and tool strings to the prompt unchanged.

## R14
Implements: FR-AI-01

WHEN a specification request has an empty `ingredients` list, the system SHALL reject it with `MISSING_INGREDIENTS` before any prompt is built (today's behaviour, kept by owner decision 2).

## R15
Implements: FR-AI-01

WHEN a specification request has an empty `tools` list, the system SHALL reject it with `MISSING_TOOLS` before any prompt is built (same decision).

## R16
Implements: FR-AI-14

WHERE `AI_PROMPT_VERSION_ID` names `v4`, the prompt resolver SHALL return the `v4` wording including the fallback sentence.

## R17
Implements: FR-AI-01, FR-AI-02

WHEN a prompt is rendered with `v4`, the rendered text SHALL NOT match `\bgenerate\b[^.\n]*\bmenu` (case-insensitive), so issue 17's regex test keeps passing.

## Acceptance coverage

| Criterion (`feature_list.json`) | Requirements | Proof |
|---|---|---|
| Unusable input yields one valid recipe following the guidelines | R2-R9 (wording present) | Deterministic tests pin the wording; the behaviour itself is the owner-run live probe (T7, T8) |
| Usable input behaves as today; the wording change is versioned and retained versions unchanged | R1, R10-R13, R16, R17 | Deterministic tests. Deviation from the criterion's "new prompt version": owner decision 1 edits unreleased `v4` instead |
| `./init.sh` passes | all | T10 |
