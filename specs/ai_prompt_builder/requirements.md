# ai_prompt_builder — Requirements

> Feature 11 · tier 1 · `sdd: true`
> Covers: `FR-AI-01`, `FR-AI-02`, `FR-AI-04`, `FR-AI-06`, `FR-AI-07`, `FR-AI-13`
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen
> requirement ids it implements and is verifiable by at least one concrete
> test that asserts a value.

## Purpose in one sentence

Assemble the three shapes of AI recipe-generation request this project needs
— from user specifications (`FR-AI-01`), from a library reference recipe
(`FR-AI-02`), and per open slot in whole-week generation (`FR-AI-04`) — as
plain, provider-agnostic data carrying the instructions every one of them
must state (servings, output language, the healthy/varied-protein notice,
the fixed unit vocabulary), without generating, validating or invoking
anything itself.

> **Amended by feature 25 (`recipe_metadata_fields`), human-approved
> 2026-08-26 (`G-85`, corrected by `G-86`).** "Servings" is no longer a
> prompt instruction of its own — see the R1, R5, R6 amendments below.

## One `SHALL` per requirement

Every `R<n>` below carries exactly one `SHALL`, counted mechanically rather
than by eye, per the checklist in `AGENTS.md` / `docs/specs.md`.

## Scope note on the six covered requirements

Several of the six ids in `covers` are shared with a requirement this feature
only partly owns. `FR-LIB-05` is cited below on several requirements — it is
**not** in this feature's `covers` array (it belongs to `recipe_model`,
feature 4, and `ai_output_validation`, feature 12), but this feature directly
consumes the fixed `Unit` vocabulary it names to build the unit-constraint
instruction, the same way `generation_request` (feature 10) consumed
`FR-RULE-05` without owning it.

| Requirement | Owned **here** | Deferred to |
|---|---|---|
| `FR-AI-01` | The `SpecificationPrompt` shape and `build_specification_prompt`, carrying the user's raw ingredients and tools. | Actually calling the model and turning its response into a `Recipe`/preview — **feature 12** (`ai_output_validation`), **feature 17** (`ai_lambda`). The authoring form itself — **feature 20**. |
| `FR-AI-02` | The `ReferencePrompt` shape and `build_reference_prompt`, carrying the chosen library `Recipe` plus the user's extra specifications. | Same as above, plus the library-recipe **picker** UI (search, per `G-46`) — **feature 20**. |
| `FR-AI-04` | The `CategoryPrompt` shape and `build_category_prompt`, carrying the week's remaining category counts (`generation_request`'s `GenerationTargets.remaining_category_counts`) as an explicit instruction for one open slot's AI-generated meal. | Deciding *which* open slots get an AI call vs. a library pick (library-only/mix mode selection), calling the model once per slot (`FR-AI-09`), and the post-generation verification against each recipe's stored `tipoAlimento` this requirement's own text promises — **feature 12**, **feature 17**. |
| `FR-AI-06` | The `HEALTHY_BALANCED_INSTRUCTION` constant (healthy, balanced, protein-varied, labelled non-medical) attached to every prompt via `PromptInstructions`. | Displaying the non-medical label to the user in the UI — **feature 20**. |
| `FR-AI-07` | The `OUTPUT_LANGUAGE` constant (`"es-ES"`) attached to every prompt via `PromptInstructions`. | Validating that the AI actually complied — **feature 12**. |
| `FR-AI-13` | ~~The `CONFIGURED_SERVINGS` constant attached to every prompt via `PromptInstructions` (the concrete value is proposed in `design.md` §4, a `docs/architecture.md` §2.1 item).~~ **Superseded by feature 25 (`G-85`, corrected by `G-86`):** `CONFIGURED_SERVINGS` is removed; `RECIPE_METADATA_INSTRUCTION`/`recipe_metadata_instruction` (an instruction, not a target value) is owned by `recipe_metadata_fields`, feature 25. | Persisting a `numeroComensales`/`estimated_time` value on the resulting `Recipe`/`MealSnapshot` — resolved by feature 25 (`recipe_metadata_fields`), no longer open. |

---

## R1
Implements: FR-AI-13

The system SHALL declare `CONFIGURED_SERVINGS` as a module-level `int`
constant in `planner_core.domain.ai_prompt` (the concrete value is proposed
in `design.md` §4 and approved at this spec's human gate, per
`docs/architecture.md` §2.1).

> **Superseded by feature 25 (`recipe_metadata_fields`,
> `specs/recipe_metadata_fields/requirements.md` R18), human-approved
> 2026-08-26 (`G-85`, corrected by `G-86`).** `CONFIGURED_SERVINGS` is
> removed outright: servings became a per-recipe field on `Recipe`, not
> deployment configuration. `RECIPE_METADATA_INSTRUCTION` (feature 25's R23,
> R24) replaces it in kind — an instruction asking the model to state a
> value, never a target the app supplies.

## R2
Implements: FR-AI-07

The system SHALL declare `OUTPUT_LANGUAGE` as a module-level `str` constant
in `planner_core.domain.ai_prompt` equal to `"es-ES"`.

## R3
Implements: FR-AI-06

The system SHALL declare `HEALTHY_BALANCED_INSTRUCTION` as a module-level,
non-empty `str` constant in `planner_core.domain.ai_prompt` instructing the
model to produce healthy, balanced menus that vary protein sources and
labelling the output non-medical (exact wording proposed in `design.md`).

## R4
Implements: FR-LIB-05

The system SHALL declare `ALLOWED_UNITS` as a module-level `tuple[Unit, ...]`
constant in `planner_core.domain.ai_prompt` equal to a tuple containing
every member of `Unit`.

## R5
Implements: FR-AI-06, FR-AI-07, FR-AI-13, FR-LIB-05

The system SHALL declare `PromptInstructions` as `@dataclass(frozen=True)`
in `planner_core.domain.ai_prompt` with fields exactly `servings: int`,
`output_language: str`, `healthy_balanced_instruction: str` and
`allowed_units: tuple[Unit, ...]`.

> **Amended by feature 24 (`ai_prompt_versioning`, `specs/ai_prompt_versioning/design.md`
> section 5), human-approved 2026-08-26.** `build_instructions()` gained a
> `version_id: str` parameter: `servings`, `output_language` and
> `healthy_balanced_instruction` are no longer read from the module constants
> directly but from `resolve_prompt_version(version_id)`'s result — feature
> 24's `v1` entry carries these same constants' values unchanged, so R6-R9's
> claims still hold for `version_id="v1"`. `build_specification_prompt`,
> `build_reference_prompt` and `build_category_prompt` each gained the same
> `version_id: str` parameter, forwarded to `build_instructions()` unchanged
> otherwise (R13, R16, R19, amended below).

> **Further amended by feature 25 (`recipe_metadata_fields`,
> `specs/recipe_metadata_fields/requirements.md` R19, R24), human-approved
> 2026-08-26 (`G-85`, corrected by `G-86`).** `PromptInstructions` no longer
> declares `servings: int`. It declares `recipe_metadata_instruction: str`
> in its place — an instruction telling the model to state a servings count
> and an estimated prep/cook time itself, never a value the app supplies.
> The fixed field set as of feature 25 is `output_language: str`,
> `healthy_balanced_instruction: str`, `recipe_metadata_instruction: str`
> and `allowed_units: tuple[Unit, ...]`.

## R6
Implements: FR-AI-13

`build_instructions(version_id)`'s result's `servings` field SHALL equal
`resolve_prompt_version(version_id).servings`.

> **Superseded by feature 25 (`recipe_metadata_fields`,
> `specs/recipe_metadata_fields/requirements.md` R25), human-approved
> 2026-08-26 (`G-85`, corrected by `G-86`).** `PromptInstructions` and
> `PromptInstructionsVersion` no longer carry a `servings` field, so this
> claim no longer applies; feature 25's R25 makes the equivalent claim for
> `recipe_metadata_instruction`.

## R7
Implements: FR-AI-07

`build_instructions(version_id)`'s result's `output_language` field SHALL
equal `resolve_prompt_version(version_id).output_language`.

## R8
Implements: FR-AI-06

`build_instructions(version_id)`'s result's `healthy_balanced_instruction`
field SHALL equal `resolve_prompt_version(version_id).healthy_balanced_instruction`.

## R9
Implements: FR-LIB-05

`build_instructions(version_id)`'s result's `allowed_units` field SHALL equal
`ALLOWED_UNITS`.

## R10
Implements: FR-AI-01

The system SHALL declare `SpecificationPrompt` as `@dataclass(frozen=True)`
in `planner_core.domain.ai_prompt` with fields exactly `instructions:
PromptInstructions`, `ingredients: tuple[str, ...]` and `tools: tuple[str,
...]`.

## R11
Implements: FR-AI-02

The system SHALL declare `ReferencePrompt` as `@dataclass(frozen=True)` in
`planner_core.domain.ai_prompt` with fields exactly `instructions:
PromptInstructions`, `reference_recipe: Recipe` and `extra_specifications:
tuple[str, ...]`.

## R12
Implements: FR-AI-04

The system SHALL declare `CategoryPrompt` as `@dataclass(frozen=True)` in
`planner_core.domain.ai_prompt` with fields exactly `instructions:
PromptInstructions` and `category_counts: tuple[CategoryCountRule, ...]`.

## R13
Implements: FR-AI-01

`build_specification_prompt(ingredients, tools, version_id)`'s result's
`instructions` field SHALL equal `build_instructions(version_id)`.

## R14
Implements: FR-AI-01

`build_specification_prompt(ingredients, tools)`'s result's `ingredients`
field SHALL equal `ingredients`.

## R15
Implements: FR-AI-01

`build_specification_prompt(ingredients, tools)`'s result's `tools` field
SHALL equal `tools`.

## R16
Implements: FR-AI-02

`build_reference_prompt(reference_recipe, extra_specifications, version_id)`'s
result's `instructions` field SHALL equal `build_instructions(version_id)`.

## R17
Implements: FR-AI-02

`build_reference_prompt(reference_recipe, extra_specifications)`'s result's
`reference_recipe` field SHALL equal `reference_recipe`.

## R18
Implements: FR-AI-02

`build_reference_prompt(reference_recipe, extra_specifications)`'s result's
`extra_specifications` field SHALL equal `extra_specifications`.

## R19
Implements: FR-AI-04

`build_category_prompt(category_counts, version_id)`'s result's
`instructions` field SHALL equal `build_instructions(version_id)`.

## R20
Implements: FR-AI-04

`build_category_prompt(category_counts)`'s result's `category_counts` field
SHALL equal `category_counts`.

---

## Coverage map

| Frozen requirement | Covered by |
|---|---|
| `FR-AI-01` | R10, R13, R14, R15 |
| `FR-AI-02` | R11, R16, R17, R18 |
| `FR-AI-04` | R12, R19, R20 |
| `FR-AI-06` | R3, R5, R8 |
| `FR-AI-07` | R2, R5, R7 |
| `FR-AI-13` | ~~R1, R5, R6~~ **superseded by feature 25 (`recipe_metadata_fields`) R18, R19, R20, R23, R24, R25 — `G-85`, corrected by `G-86`** |
| `FR-LIB-05` (consumed, not in `covers`) | R4, R5, R9 |

| `feature_list.json` acceptance criterion | Covered by |
|---|---|
| Prompts assembled as plain data structures with no provider SDK imported | Satisfied structurally, not by a single `R<n>`: `planner_core.domain.ai_prompt` imports only `dataclasses`, `typing` and sibling `planner_core.domain` modules (see `design.md` §3, §9); `core` keeps `dependencies = []`, so no provider SDK could be imported without a `pyproject.toml` change this spec does not make. |
| ~~Every prompt states the configured number of servings (`FR-AI-13`, `G-64`)~~ **superseded by feature 25: no target servings value is stated by the app; the model is instructed to state its own (`G-85`, corrected by `G-86`)** | R1, R5, R6 (historical) |
| Every prompt instructs Castilian Spanish output (`FR-AI-07`) | R2, R5, R7 |
| Every prompt instructs healthy, balanced menus that vary protein sources, labelled non-medical (`FR-AI-06`) | R3, R5, R8 |
| Ingredient-category counts are passed as explicit prompt instructions, verifiable after generation against each recipe's stored `tipoAlimento` (`FR-AI-04`, `G-69`, supersedes `G-63`) | R12, R19, R20 (the verifiability half is `ai_output_validation`'s, feature 12 — see the scope table) |
| Prompts constrain ingredient units to the fixed unit list (`FR-LIB-05`, `G-48`) | R4, R5, R9 |
| Both single-recipe modes are supported: from specifications, and from a library reference plus specifications (`FR-AI-01`, `FR-AI-02`) | R10, R11, R13–R18 |

Supporting requirements not demanded by a single acceptance bullet but
required by the invariants those bullets rest on: R5 (the shape every
builder composes into, so "every prompt" is a property of one dataclass
rather than three independent claims), R6–R9 (`build_instructions()`'s own
correctness, which R13, R16 and R19 each reuse rather than re-deriving).
