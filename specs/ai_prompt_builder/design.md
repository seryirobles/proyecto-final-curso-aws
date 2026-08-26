# ai_prompt_builder — Design

> Feature 11 · tier 1 · pure `planner_core.domain`
> Read `requirements.md` first. This document records the technical decisions
> taken before any code is written, per `docs/specs.md`.
> Depends on feature 4 `recipe_model` (closed, `Recipe`, `Ingredient`,
> `IngredientCategory`), feature 6 `rules_model` (closed, `CategoryCountRule`)
> and feature 3 `text_and_units` (closed, `Unit`) — this feature **consumes**
> all three and re-derives none of them. It does not import feature 10
> `generation_request` (see §8, alternative B).

## 0. The invariant this feature exists to protect

`docs/gaps_and_resolutions.md`, `G-64`:

> Every AI generation prompt (single-recipe and per-slot whole-week) states a
> configured number of servings (deployment configuration, e.g. 4 diners)...
> Leaving it unspecified was not an option — an unstated assumption in a
> prompt isn't a default, it's nondeterminism.

and `G-48`/`G-69`, the same principle applied to units and categories: an AI
call given no explicit vocabulary constraint is free to invent one, silently
breaking shopping-list aggregation (`G-48`) or leaving category counts
unverifiable (`G-69`). Every function below exists to make these constraints
**structural** — part of the value every caller receives — rather than a
convention a caller could forget to apply at one of the three call sites.

---

## 1. Scope boundary — what this feature owns of each `FR-*`

See `requirements.md`'s scope-note table for the full per-requirement split.
Two lines deserve emphasis:

**This feature does not call an AI provider, validate its output, or decide
which slot gets an AI call versus a library pick.** It is a pure
constructor: given the caller's inputs (raw ingredients/tools, a reference
`Recipe`, or a week's remaining category counts), it returns an immutable
value describing what any downstream caller must ask an eventually-chosen
provider (`docs/architecture.md` §2 `P4`, still pending) to do. No function
here performs IO, imports a provider SDK, or reads a clock.

**"Which open slots need an AI call" is feature 10's and feature 17's
question, not this one's.** `generation_request`'s `GenerationTargets`
already separates `open_slots` (need something) from `pinned_slots` (already
resolved to a library recipe, no AI needed) and `remaining_category_counts`
(the week's residual need). This feature's `build_category_prompt` takes
that last field's *value* — a plain `tuple[CategoryCountRule, ...]` — not the
whole `GenerationTargets` object, so it stays decoupled from feature 10's
request/response shape (see §8, alternative B, for why that coupling was
rejected).

**The reusable artefact this feature adds.** `PromptInstructions`,
`SpecificationPrompt`, `ReferencePrompt`, `CategoryPrompt`, and the four
functions that build them. Feature 12 (`ai_output_validation`) and feature 17
(`ai_lambda`) consume these values to actually invoke a provider and validate
its response; neither redeclares the instruction constants.

---

## 2. Layering

`docs/architecture.md` §3: `domain/` is *"Pure logic. No IO, no AWS SDK, no
framework, no clock."* Every piece below is a plain value or a pure function
between plain values — no port, no clock, no id generator, no IO, and
critically, **no provider SDK import of any kind**, since `P4` (AI provider
and model) is still `docs/architecture.md` §2, pending and human-owned.

| Piece | Layer | Why |
|---|---|---|
| `PromptInstructions`, `SpecificationPrompt`, `ReferencePrompt`, `CategoryPrompt`, `build_instructions`, `build_specification_prompt`, `build_reference_prompt`, `build_category_prompt` | `planner_core/domain/ai_prompt.py` | Pure value objects and pure functions between them; no IO, no ambient state, no clock, no dependency on which provider (if any) is eventually selected. |

No `application/` piece: every input is caller-supplied, exactly like
`generation_request`'s own §2 (no piece of that feature needed one either,
for the same reason — nothing here needs "now").

---

## 3. Files

### Created

| Path | Contents |
|---|---|
| `backend/core/src/planner_core/domain/ai_prompt.py` | `CONFIGURED_SERVINGS`, `OUTPUT_LANGUAGE`, `HEALTHY_BALANCED_INSTRUCTION`, `ALLOWED_UNITS`, `PromptInstructions`, `SpecificationPrompt`, `ReferencePrompt`, `CategoryPrompt`, `build_instructions`, `build_specification_prompt`, `build_reference_prompt`, `build_category_prompt`. |
| `backend/core/tests/domain/test_ai_prompt.py` | R1–R20. |

### Modified

None. No `pyproject.toml` change: no dependency added, `planner-core` keeps
`dependencies = []` (`dataclasses` and `typing`, the only imports besides
sibling `planner_core.domain` modules, are both standard library).
`backend/core/tests/test_shared_kernel_guards.py`'s `SHARED_KERNEL_MODULES`
tuple is untouched — see §7 for why.

---

## 4. `docs/architecture.md` §2.1 items

This feature proposes one concrete value: **`CONFIGURED_SERVINGS = 4`**, the
named `docs/architecture.md` §2.1 item ("The configured servings count for AI
prompts, `G-64`, `FR-AI-13`"). Rationale: `G-64` itself gives "4 diners" as
its own example, and it is consistent with the fixed 2–10-person household
this deployment serves (`G-35`); no story asks for a different number, and
`G-64` explicitly rejected promoting this to a user-editable rule for the
MVP ("a config constant suffices; UI promotion is a later trivial upgrade").
Approving this value is part of approving this spec at the human gate — no
separate sign-off is needed.

`HEALTHY_BALANCED_INSTRUCTION`'s exact wording is **not** a §2.1 item (it is
not listed there); it is an ordinary content decision proposed here like any
other constant:

```
"Genera un menu saludable y equilibrado, variando las fuentes de proteina "
"entre los platos. Esta indicacion tiene fines de planificacion domestica "
"y no constituye un consejo medico."
```

Written in Castilian Spanish deliberately, unlike the rest of this module's
identifiers and comments: it is the one string in this feature that could
plausibly leak into what the model treats as content to imitate or quote
back, and `FR-AI-07` already requires the *output* to be Castilian Spanish —
keeping the instruction in the same language as the output it requests
avoids an English instruction producing a Spanish echo of itself in the
response. This is the one deliberate exception to "identifiers, comments,
docstrings are English" (`docs/conventions.md` Language policy), because
this string is neither an identifier nor a comment — it is prompt *content*,
the same category the table already lists Castilian Spanish for
("AI-generated recipe content"). It is not written through the messages
module (`docs/conventions.md`'s "every user-facing string lives in one
messages module") because it is never shown to a user — it is sent only to
whichever provider `P4` eventually selects.

---

## 5. Why three prompt types instead of one

`FR-AI-01`, `FR-AI-02` and `FR-AI-04` describe three different sets of
mode-specific inputs (raw ingredients/tools; a reference recipe plus extra
specifications; a week's remaining category counts) sharing one set of
universal instructions (servings, language, the health notice, the unit
list). Two shapes could carry that:

**A. One `RecipePrompt` dataclass with every mode-specific field present and
empty/`None` when unused** (e.g. `ingredients: tuple[str, ...] = ()`,
`reference_recipe: Recipe | None = None`, `category_counts:
tuple[CategoryCountRule, ...] = ()`). Rejected. A consumer (feature 12/17)
would have to infer which of the three modes produced a given prompt by
checking which fields are non-empty — exactly the "guess it from what's
absent" ambiguity `generation_request`'s design (§8, alternative D) rejected
for `PinnedTarget` vs. reusing `PinRule` directly. A malformed caller could
also set two mode-specific fields at once, a state this feature's own types
should make unrepresentable, not merely undocumented.

**B. Three distinct dataclasses — `SpecificationPrompt`, `ReferencePrompt`,
`CategoryPrompt` — each carrying only its own mode-specific field(s), plus a
shared `instructions: PromptInstructions` field** (chosen here). Which type a
value has *is* which mode produced it; no field is ever absent-but-present.
The shared `instructions` field is composed once by `build_instructions()`
and reused by all three builders (R13, R16, R19), so `FR-AI-06`/`-07`/`-13`
and the consumed half of `FR-LIB-05` are asserted once, not three times
independently. This mirrors `recipe_model`'s own precedent of `Recipe` and
`MealSnapshot` as deliberately distinct, structurally similar types rather
than one type with an optional discriminator.

---

## 6. Signatures

```python
"""Provider-agnostic AI prompt assembly: single-recipe and whole-week category-targeted requests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from planner_core.domain.recipe import Recipe
from planner_core.domain.rules import CategoryCountRule
from planner_core.domain.units import Unit

CONFIGURED_SERVINGS: Final[int] = 4
"""Deployment configuration (G-64); proposed value, approved at this spec's human gate (design.md section 4)."""

OUTPUT_LANGUAGE: Final[str] = "es-ES"
"""FR-AI-07: AI output is produced in Castilian Spanish."""

HEALTHY_BALANCED_INSTRUCTION: Final[str] = (
    "Genera un menu saludable y equilibrado, variando las fuentes de proteina "
    "entre los platos. Esta indicacion tiene fines de planificacion domestica "
    "y no constituye un consejo medico."
)
"""FR-AI-06: healthy/balanced/protein-varied, labelled non-medical (design.md section 4)."""

ALLOWED_UNITS: Final[tuple[Unit, ...]] = tuple(Unit)
"""FR-LIB-05 (consumed): the fixed unit vocabulary, reused from units.py, never redeclared."""


@dataclass(frozen=True)
class PromptInstructions:
    """The instructions every AI recipe-generation prompt carries, regardless of mode."""

    servings: int
    output_language: str
    healthy_balanced_instruction: str
    allowed_units: tuple[Unit, ...]


@dataclass(frozen=True)
class SpecificationPrompt:
    """FR-AI-01: a single recipe generated from user-supplied ingredients and tools."""

    instructions: PromptInstructions
    ingredients: tuple[str, ...]
    tools: tuple[str, ...]


@dataclass(frozen=True)
class ReferencePrompt:
    """FR-AI-02: a single recipe generated from a chosen library recipe plus extra specifications."""

    instructions: PromptInstructions
    reference_recipe: Recipe
    extra_specifications: tuple[str, ...]


@dataclass(frozen=True)
class CategoryPrompt:
    """FR-AI-04: one open slot's AI-generated meal, carrying the week's remaining category needs."""

    instructions: PromptInstructions
    category_counts: tuple[CategoryCountRule, ...]


def build_instructions() -> PromptInstructions:
    """The shared instruction block every prompt carries (R6-R9)."""
    return PromptInstructions(
        servings=CONFIGURED_SERVINGS,
        output_language=OUTPUT_LANGUAGE,
        healthy_balanced_instruction=HEALTHY_BALANCED_INSTRUCTION,
        allowed_units=ALLOWED_UNITS,
    )


def build_specification_prompt(
    ingredients: tuple[str, ...], tools: tuple[str, ...]
) -> SpecificationPrompt:
    """FR-AI-01 (R13-R15)."""
    return SpecificationPrompt(
        instructions=build_instructions(), ingredients=ingredients, tools=tools
    )


def build_reference_prompt(
    reference_recipe: Recipe, extra_specifications: tuple[str, ...]
) -> ReferencePrompt:
    """FR-AI-02 (R16-R18)."""
    return ReferencePrompt(
        instructions=build_instructions(),
        reference_recipe=reference_recipe,
        extra_specifications=extra_specifications,
    )


def build_category_prompt(category_counts: tuple[CategoryCountRule, ...]) -> CategoryPrompt:
    """FR-AI-04 (R19-R20). category_counts is the caller's snapshot (design.md section 1) —
    typically generation_request's GenerationTargets.remaining_category_counts, passed
    unchanged for one open slot; this function neither reads nor recomputes it."""
    return CategoryPrompt(instructions=build_instructions(), category_counts=category_counts)
```

### Exceptions

None. Every function in this module is total over its typed inputs — no new
failure mode is introduced. `Recipe` and `CategoryCountRule` already raise
their own construction-time exceptions (`recipe_model`, `rules_model`)
before any value of either type could reach this module.

No function in this feature returns `None` to signal failure
(`docs/architecture.md` §4 invariant 12).

---

## 7. Why `ai_prompt.py` is not added to the shared-kernel guard

`backend/core/tests/test_shared_kernel_guards.py`'s `SHARED_KERNEL_MODULES`
tuple guards modules that declare a closed vocabulary another feature would
otherwise be tempted to redeclare — `text.py`'s fold, `units.py`'s `Unit`,
`ingredient_category.py`'s `IngredientCategory`, plus `recipe.py`. This
feature declares no new enum and no new closed vocabulary of its own: every
constant here (`CONFIGURED_SERVINGS`, `OUTPUT_LANGUAGE`,
`HEALTHY_BALANCED_INSTRUCTION`, `ALLOWED_UNITS`) is a single scalar or a
reuse of `Unit`, not a second enumeration a later feature could plausibly
redeclare instead of importing. `generation_request`'s design (§7) reached
the same conclusion for its own single new enum, `GenerationMode`, on
different grounds (no plausible reason to redeclare it); here there is no
new enum at all to consider.

---

## 8. Rejected alternatives

**A. One `RecipePrompt` dataclass with optional/empty mode-specific fields
instead of three distinct types (§5, alternative A).**
Rejected — see §5. Guessing a value's mode from which fields are populated
is the same ambiguity `generation_request` rejected for `PinnedTarget`.

**B. `build_category_prompt` accepting `generation_request.GenerationTargets`
directly, instead of the already-extracted `tuple[CategoryCountRule, ...]`
(§1).**
Rejected. This feature needs exactly one field of that object
(`remaining_category_counts`); accepting the whole type would import
`planner_core.domain.generation` merely to reach one attribute, coupling
prompt assembly to the whole generation-request/target-resolution shape it
has no other reason to know about. The caller (feature 17's per-slot
orchestration) already holds a `GenerationTargets` and can extract the one
field itself — exactly the same "accept the plain value, not the whole
request" split `generation_request`'s own `resolve_targets` and
`idempotency_key` already model as independently callable functions (that
spec's design §8, alternative C).

**C. A single natural-language string, pre-rendered for one specific
provider's request format (e.g. a chat-completion message array), instead of
the structured `PromptInstructions` + mode-specific dataclasses (§2, §6).**
Rejected. `docs/architecture.md` §2's `P4` (AI provider and model) is still
pending, and the feature's own acceptance criteria require "plain data
structures with no provider SDK imported." A pre-rendered, provider-shaped
string would force a guess at a format that might not survive whichever
provider `P4` eventually selects; a structured value lets feature 17
(`ai_lambda`), the feature that will actually own an AI SDK dependency,
render it however that provider's API needs, once, in one place.

**D. Passing `servings` (and the other three instruction fields) as
parameters to each builder function instead of reading them from module
constants via `build_instructions()` (§6).**
Rejected. `docs/architecture.md` §6 ("do not build a configuration
framework... a single documented constants module") and `G-64`'s own
reasoning ("a deployment config is the MVP-minimal fix... one constant")
both apply directly. Parameterizing would let two call sites pass different
servings counts for the same deployment, reopening exactly the
inconsistency `G-64` closed — "an unstated assumption in a prompt isn't a
default, it's nondeterminism" applies just as much to a *restatable*
assumption a caller could vary by accident.

---

## 9. Boundary checks and gate questions

### Boundary checks

- **`docs/architecture.md` §2 (pending, human-owned):** nothing here needs
  P2, P3, P5 or P6. `P4` (the AI provider itself) is exactly what this
  feature is designed to stay agnostic to — no import, no reference, no
  provider-shaped rendering (§8, alternative C).
- **§2.1 decide-in-a-spec items:** `CONFIGURED_SERVINGS = 4` is proposed in
  §4, the one named item this feature touches. The unit list and the
  ingredient-category list are untouched — both are reused unchanged from
  `units.py` and (via `rules.py`'s `CategoryCountRule`) `ingredient_category.py`.
- **Frozen docs:** none modified.
- **User-facing strings:** none, per `docs/conventions.md`'s Language
  policy — `HEALTHY_BALANCED_INSTRUCTION` is Castilian Spanish *content* sent
  to a future AI provider, never shown to a user, so it does not go through
  `messages.py` (see §4's reasoning).
- **Runtime dependencies:** none added; `planner-core` keeps
  `dependencies = []`.
- **Requirements invented:** none. Every `R<n>` cites one or more of
  `FR-AI-01`, `FR-AI-02`, `FR-AI-04`, `FR-AI-06`, `FR-AI-07`, `FR-AI-13` — all
  six in this feature's `covers` array — plus `FR-LIB-05`, an existing frozen
  id this feature consumes but does not own (see `requirements.md`'s scope
  note).

### Gate questions for the human

1. **Does this feature own persisting `numeroComensales` on `Recipe` /
   `MealSnapshot`, or is that deferred?** `docs/data_model.md` §1 lists
   `numeroComensales` as a stored attribute of both `DatosPlatoSemana` and
   `DatosPlatoBiblioteca`. `specs/recipe_model/design.md` §1 (feature 4,
   already closed) deliberately left it off `Recipe`/`MealSnapshot`, noting
   *"`numeroComensales` is `FR-AI-13`'s territory (feature 11, `G-64`)"* —
   naming this feature as where the field would eventually be addressed.

   **This spec does not add it**, for three reasons: (1) `FR-LIB-03` and
   `FR-CAND-07` — the requirements that define `Recipe`'s and
   `MealSnapshot`'s content shape — are **not** in this feature's `covers`
   array, and adding a field to either type without an `FR-*` in `covers` to
   cite would be exactly the "invent a requirement" this project forbids.
   (2) Neither is `FR-LIB-03` in feature 12's (`ai_output_validation`)
   `covers` array (`FR-AI-10`, `FR-AI-12`, `FR-LIB-05` only) — checked
   directly against `feature_list.json`, so this is a genuine gap in the
   current backlog decomposition, not a question this feature can resolve by
   picking a side. (3) `recipe.py` is one of the four shared-kernel modules
   `test_shared_kernel_guards.py` protects; its owning feature (4) is
   already closed, and extending its dataclasses from an unrelated feature
   without an explicit mandate risks a shape change nobody reviewed against
   `FR-LIB-03`'s and `FR-CAND-07`'s own text.

   **What this spec does instead:** `FR-AI-13`'s literal text — "stated
   explicitly in every prompt" — is fully satisfied by `CONFIGURED_SERVINGS`
   traveling through `PromptInstructions` into every prompt this feature
   builds (R1, R5, R6). The unaddressed half is *recording* the number on the
   resulting recipe once generated.

   **Recommendation:** amend either feature 12's or feature 17's `covers`
   array to add `FR-LIB-03` (and, if `MealSnapshot` needs it too,
   `FR-CAND-07`) when whichever of those features first parses AI output
   into a `Recipe` — that is the natural point to also set
   `numeroComensales`/`servings` to `CONFIGURED_SERVINGS`, and to decide
   whether manually-authored recipes (outside this feature's scope
   entirely) get a free-form value or the same constant. Alternative: amend
   *this* feature's `covers` array now to add `FR-LIB-03`/`FR-CAND-07` and
   extend `Recipe`/`MealSnapshot` here instead — rejected as the primary
   recommendation only because this feature builds prompts, not recipes, and
   has no AI response to attach the field to yet.

   **Resolved 2026-08-26 (human):** recommendation approved as designed.
   Deferred to feature 12 or feature 17, whichever first parses AI output
   into a `Recipe` — that feature's `covers` array gets `FR-LIB-03` (and
   `FR-CAND-07` if `MealSnapshot` needs it) at that time. This feature ships
   without touching `Recipe`/`MealSnapshot`. `CONFIGURED_SERVINGS = 4` (§4)
   approved together with this spec.
