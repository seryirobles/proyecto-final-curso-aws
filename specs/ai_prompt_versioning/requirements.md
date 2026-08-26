# ai_prompt_versioning — Requirements

> Feature 24 · tier 1 · `sdd: true`
> Covers: `FR-AI-14`
> Depends on: feature 11 `ai_prompt_builder` (implemented, pending sign-off)
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen
> requirement id it implements and is verifiable by at least one concrete
> test that asserts a value.

## Purpose in one sentence

Give the AI prompt instruction content that feature 11 assembles
(`servings`, `output_language`, `healthy_balanced_instruction` — the wording
`FR-AI-06`, `FR-AI-07` and `FR-AI-13` require) a version identity, so the
version used for a given generation is an explicit, traceable choice rather
than "whatever the code currently contains," and so retired wording is never
lost.

> **Amended by feature 25 (`recipe_metadata_fields`), human-approved
> 2026-08-26 (`G-85`, corrected by `G-86`).** `servings` is no longer part
> of the versioned wording — see the R1, R5 amendments below.
> `recipe_metadata_instruction` (feature 25's R23) is versioned in its
> place, through the same `PromptInstructionsVersion` shape this feature
> defined.

## The single frozen requirement this feature translates

`docs/requirements.md` line 113, `FR-AI-14`:

> AI prompt instructions (`FR-AI-06`, `FR-AI-07`, `FR-AI-13`, and any future
> wording changes) shall be **versioned**. The prompt version used for a
> given generation shall be **deployment configuration**, explicitly selected
> rather than defaulting silently to whatever the code currently contains;
> retired versions shall be retained, not deleted, so a past AI-generated
> recipe can be traced back to the wording that produced it.

`docs/gaps_and_resolutions.md` `G-84` (Part T) is the gap analysis behind it:
`ai_prompt.py`'s `build_instructions()` (feature 11) compiles
`HEALTHY_BALANCED_INSTRUCTION`, `OUTPUT_LANGUAGE` and `CONFIGURED_SERVINGS`
as plain module constants with no version identity, so every generation uses
whatever the current source tree happens to contain, and nothing records
which wording produced a past AI-generated recipe.

## One `SHALL` per requirement

Every `R<n>` below carries exactly one `SHALL`, counted mechanically rather
than by eye, per the checklist in `AGENTS.md` / `docs/specs.md`.

## Scope note

**Not versioned by this feature: `ALLOWED_UNITS`.** `G-84`'s gap text names
only `HEALTHY_BALANCED_INSTRUCTION`, `OUTPUT_LANGUAGE` and
`CONFIGURED_SERVINGS` — the three constants that carry *wording* a human
could plausibly want to tweak over time. `ALLOWED_UNITS` is a structural
derivation of the closed `Unit` vocabulary (`FR-LIB-05`, owned by
`text_and_units`), not prompt wording, and versioning it would mean
versioning the unit vocabulary itself — out of this feature's `covers`
array and not asked for by `FR-AI-14`.

**How "deployment configuration" is implemented is `design.md`'s territory,
not this file's.** `docs/architecture.md` §1.2.2 and §3.1 rule 6 give this
project one precedent for a deployment-varying value with no natural home in
a zero-IO `domain/` — the `Clock` port, `Protocol` plus injected default
implementation, never read ambiently. The human resolved `design.md`'s gate
question by generalizing that same shape into a reusable `ConfigPort` (not
scoped to prompt versions alone), described in full in `design.md` §3 and
§9. The requirements below are written at the level that holds regardless of
that resolution: they state what must be true of the versioned instructions
and their selection, not which layer performs the selection.

**Not addressed by this feature: recording a generation's prompt version on
the resulting `Recipe`/`MealSnapshot`.** `FR-LIB-03` and `FR-CAND-07` — the
requirements that define those types' content shape — are not in this
feature's `covers` array, the same boundary feature 11's own design (§9 gate
question 1) drew for `numeroComensales`. This feature makes the active
version's identifier available to whichever caller builds a prompt (R7); it
does not persist that identifier anywhere. Recording it against a generated
recipe is deferred to whichever feature (12 `ai_output_validation` or 17
`ai_lambda`) first parses AI output into a `Recipe`, exactly as feature 11's
design.md §9 already deferred `numeroComensales` there.

---

## R1
Implements: FR-AI-14

The system SHALL represent each version of the AI prompt instruction content
— `servings`, `output_language` and `healthy_balanced_instruction` — as a
distinct, immutable value carrying its own version identifier.

> **Amended by feature 25 (`recipe_metadata_fields`,
> `specs/recipe_metadata_fields/requirements.md` R23), human-approved
> 2026-08-26 (`G-85`, corrected by `G-86`).** The versioned content is now
> `recipe_metadata_instruction`, `output_language` and
> `healthy_balanced_instruction` — `servings` is removed, replaced in kind
> by an instruction telling the model to state a value itself.

## R2
Implements: FR-AI-14

The system SHALL retain every version of the AI prompt instruction content
ever defined, including versions superseded by a newer one.

## R3
Implements: FR-AI-14

The system SHALL determine which single retained version is the active one
through one designated selection point, kept separate from where each
version's content is authored.

## R4
Implements: FR-AI-14

IF the active-version selection point does not resolve to a version
identifier present in the retained set — whether because no value is
configured or because the configured value names an unregistered version —
THEN the system SHALL raise a named domain exception rather than silently
falling back to a different version.

## R5
Implements: FR-AI-14

WHEN the shared instruction block used by every AI prompt is composed, the
system SHALL source its `servings`, `output_language` and
`healthy_balanced_instruction` values from the active prompt-instruction
version's content.

> **Amended by feature 25 (`recipe_metadata_fields`,
> `specs/recipe_metadata_fields/requirements.md` R25), human-approved
> 2026-08-26 (`G-85`, corrected by `G-86`).** The composed instruction block
> now sources `recipe_metadata_instruction`, `output_language` and
> `healthy_balanced_instruction` — `servings` is no longer one of its
> fields.

## R6
Implements: FR-AI-14

The system SHALL make every retained version, active or retired, retrievable
by its version identifier.

## R7
Implements: FR-AI-14

WHEN the active prompt-instruction version's content is resolved, the system
SHALL expose its version identifier alongside that content, so a caller
building a prompt can capture which version it used.

---

## Coverage map

| Frozen requirement | Covered by |
|---|---|
| `FR-AI-14` | R1, R2, R3, R4, R5, R6, R7 |

| `feature_list.json` acceptance criterion | Covered by |
|---|---|
| Prompt instructions carry a version identifier (`G-84`) | R1, R7 |
| The prompt version used for a given generation is deployment configuration, explicitly selected rather than implied by the current source tree (`FR-AI-14`) | R3, R4 (the concrete mechanism — `ConfigPort`, `design.md` §3/§9 — satisfies R3/R4 as written, and R3/R4 hold independently of that resolution) |
| Retired prompt versions are retained, not deleted, so a past AI-generated recipe can be traced back to the wording that produced it (`FR-AI-14`, `G-84`) | R2, R6, R7 (the *recording* half — attaching a version id to a persisted recipe — is out of scope here; see the Scope note above) |

Supporting requirement not demanded by a single acceptance bullet but
required by the invariant the others rest on: R5, which is what makes R1–R4
and R6–R7 actually reach a built prompt instead of describing an unused
registry sitting beside the constants feature 11 already built.
