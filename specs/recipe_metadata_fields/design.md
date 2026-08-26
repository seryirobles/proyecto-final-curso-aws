# recipe_metadata_fields — Design

> Feature 25 · tier 1 · pure `planner_core.domain`
> Read `requirements.md` first. This document records the technical decisions
> taken before any code is written, per `docs/specs.md`.
> Depends on feature 4 `recipe_model` (closed: `Recipe`, `MealSnapshot`,
> `snapshot()`), feature 11 `ai_prompt_builder` (closed: `CONFIGURED_SERVINGS`,
> `PromptInstructions`, `build_instructions()`), feature 12
> `ai_output_validation` (closed: `RawRecipeOutput`,
> `validate_ai_recipe_output`) — all three `done` and now amended by this
> feature — plus feature 5 `week_plan_model` (closed: `candidate.py`'s
> `to_library_entry`, a call site this feature must keep correct even though
> `candidate.py` is not otherwise this feature's file).
>
> This feature is a **breaking change to three already-shipped, "done"
> features' code and specs** — feature 11, feature 12's own `RawRecipeOutput`
> shape, and feature 24 `ai_prompt_versioning`'s `PromptInstructionsVersion`.
> That is not unprecedented: feature 24 itself amended feature 11's
> `requirements.md` R6–R9 the same way (`specs/ai_prompt_versioning/design.md`
> §5, its own `tasks.md` T5). This design does the same to feature 11's and
> feature 24's `requirements.md`, and to features 11's, 12's and 4's code.

## 0. The invariant this feature exists to protect

`docs/gaps_and_resolutions.md`, `G-85` (Part U):

> Both `numeroComensales` (servings) and `tiempo` (estimated prep/cook time)
> become **per-recipe attributes**, stored on `Recipe`/`MealSnapshot` like any
> other content field, set either **manually** by the author or **by AI**...
> Both are **purely informational**: displayed alongside a recipe's other
> content, with **no validation, no dropdown constraint, and no
> shopping-aggregation logic** attached. `FR-AI-13`'s deployment-config
> framing for servings is dropped; ingredient-quantity consistency across
> recipes with different serving counts is explicitly **not** guaranteed or
> enforced.

**Corrected at the design gate, `G-86` (Part V):** `G-85`'s own replacement
text for `FR-AI-13` was passive — "AI-generated recipes **may** set a
servings count" — and this document's first draft read that literally,
rejecting any new prompt instruction as invention (§8, original alternative
E). The human caught this: dropping the *fixed target number*
(`CONFIGURED_SERVINGS = 4`) was the intended change; dropping the
*instruction to the model* was not. `FR-AI-13` now reads: AI recipe
generation **shall instruct the model** to state a servings count and an
estimated prep/cook time for each recipe it generates. Nothing else about
`G-85`'s decision changed — still purely informational, still no fixed
target, still no cross-recipe consistency requirement, still no validation,
still no downstream logic. §6 and §8 below reflect this correction; §7 (the
mechanical no-downstream-logic scan) is unaffected, because an instruction
that asks the model to state a value is not itself downstream logic reading
a `Recipe`'s field — see §1.

Everything below serves that paragraph's two halves: give the fields a home
on the shared-kernel types (§§4–6), and make the *absence* of any downstream
logic a mechanically checked fact rather than a hope (§7) — the same
discipline `docs/architecture.md` §1.2.2 required of `SystemClock` and
`backend/core/tests/test_no_ambient_time.py` enforces for it.

---

## 1. Scope boundary — what this feature owns of each `FR-*`

See `requirements.md`'s scope-note table for the full per-requirement split.
Three lines deserve emphasis here:

**This feature adds no validation and no new failure mode.** Every function
that carries `servings`/`estimated_time` through (`snapshot()`,
`validate_ai_recipe_output`, `to_library_entry`) already existed; none of
them gain a branch that inspects either field's *value* — only its
*presence*, to decide whether to copy it (never to reject its absence, per
R12/R13). The one genuinely new piece of behaviour is `recipe_metadata_
instruction` (R23–R25, `G-86`): a new constant string threaded into every
prompt, exactly the same shape `HEALTHY_BALANCED_INSTRUCTION` already has.
It asks the model to *state* a value; it does not supply one, validate one,
or read one back off a `Recipe` — so it adds no read of `servings`/
`estimated_time` anywhere in `planner_core`, and §7's scan is unaffected.

**`ConfigPort` (feature 24) is untouched.** This feature removes a *field*
(`servings`) from a type `ai_prompt_versioning` declared
(`PromptInstructionsVersion`); it does not touch the port, `EnvConfig`,
`resolve_active_prompt_version`, or `PROMPT_VERSION_CONFIG_KEY`. The
per-recipe `servings` this feature adds to `Recipe` has nothing to do with
*which prompt-wording version* is active — that remains exactly
`ai_prompt_versioning`'s concern, unrelated to this feature's.

---

## 2. Layering

`docs/architecture.md` §3: `domain/` is *"Pure logic. No IO, no AWS SDK, no
framework, no clock."* Every piece touched here is a plain dataclass field or
a pure function's existing body, unchanged in kind.

| Piece | Layer | Why |
|---|---|---|
| `Recipe.servings`, `Recipe.estimated_time`, `MealSnapshot.servings`, `MealSnapshot.estimated_time`, `snapshot()` (updated) | `planner_core/domain/recipe.py` | Existing pure value objects and pure function; two new fields, one new pair of copy assignments. |
| `RawRecipeOutput.servings`, `RawRecipeOutput.estimated_time`, `validate_ai_recipe_output()` (updated) | `planner_core/domain/ai_output.py` | Existing pure translator; two new fields, two new copy assignments — no new branch, no new exception. |
| `to_library_entry()` (updated) | `planner_core/domain/candidate.py` | Existing pure function; two new copy assignments in the `Recipe(...)` construction it already performs. |
| `ai_prompt.py`: removal of `CONFIGURED_SERVINGS`, removal of `servings` from `PromptInstructions` and `PromptInstructionsVersion`, addition of `RECIPE_METADATA_INSTRUCTION` and a `recipe_metadata_instruction` field on both, updated `build_instructions()` | `planner_core/domain/ai_prompt.py` | Existing pure value objects and pure function; a field/constant pair removed, a differently-shaped field/constant pair added — same kind of change `HEALTHY_BALANCED_INSTRUCTION` already established. |

No `application/` or `ports/` piece is created or modified. `ConfigPort`
(feature 24, `planner_core/ports/config.py`) is untouched — see §1.

---

## 3. Files

### Created

| Path | Contents |
|---|---|
| `backend/core/tests/test_no_recipe_metadata_logic.py` | The mechanical scan proving R18, R19, R20, R21, R22, built to `test_no_ambient_time.py`'s discipline (§7). `RECIPE_METADATA_INSTRUCTION`/`recipe_metadata_instruction` (R23–R25) are deliberately outside this scan's scope — see §7's note. |

### Modified

| Path | Change |
|---|---|
| `backend/core/src/planner_core/domain/recipe.py` | Add `servings: int \| None = None` and `estimated_time: str \| None = None` to `Recipe` and to `MealSnapshot` (after `category`, the only position `dataclasses` permits once every existing field is defaultless — §5). Update `snapshot()` to copy both (R5, R6). |
| `backend/core/src/planner_core/domain/ai_output.py` | Add the same two optional fields, same defaults, to `RawRecipeOutput`. Update `validate_ai_recipe_output()` to pass both straight through into the `Recipe(...)` it builds (R14, R15) — no `parse_*` call, no exception path, matching R12/R13. |
| `backend/core/src/planner_core/domain/candidate.py` | In `to_library_entry()`, add `servings=meal.servings` and `estimated_time=meal.estimated_time` to the existing `Recipe(...)` construction (R16, R17) — the two "sanctioned lines" R21/R22 name. |
| `backend/core/src/planner_core/domain/ai_prompt.py` | Remove `CONFIGURED_SERVINGS` entirely (R18). Remove `servings: int` from `PromptInstructions` (R19) and from `PromptInstructionsVersion` (R20). Add `RECIPE_METADATA_INSTRUCTION` (a module constant, `HEALTHY_BALANCED_INSTRUCTION`'s shape) and a `recipe_metadata_instruction: str` field on both `PromptInstructions` and `PromptInstructionsVersion` (R23, R24, `G-86`). Update `PROMPT_INSTRUCTION_VERSIONS["v1"]`'s construction to drop `servings=...` and add `recipe_metadata_instruction=RECIPE_METADATA_INSTRUCTION`. Update `build_instructions()` to stop reading `version.servings`/setting `PromptInstructions(servings=...)` and instead thread `version.recipe_metadata_instruction` through (R25). |
| `backend/core/tests/domain/test_recipe.py` | New tests for R1–R9 (field shape and defaults, `snapshot()` copy-through, arbitrary-value acceptance). Existing frozen-instance tests for `Recipe`/`MealSnapshot` (feature 4) already cover `frozen=True`'s survival — adding fields does not create a *new* dataclass, so `docs/conventions.md`'s "every new `@dataclass(frozen=True)` gets its own frozen-instance test" rule is not re-triggered; the existing tests simply keep passing. |
| `backend/core/tests/domain/test_ai_output.py` | New tests for R10–R15 (field shape, absent-value no-raise, copy-through). |
| `backend/core/tests/domain/test_candidate.py` | New tests for R16, R17 (`to_library_entry` copy-through). |
| `backend/core/tests/domain/test_ai_prompt.py` | Remove the two `CONFIGURED_SERVINGS` assertions and every `.servings ==` assertion; update every `build_instructions`/`build_*_prompt` call and its `PromptInstructions`/`PromptInstructionsVersion` field-shape assertion to the reduced field set; add assertions for R23–R25 (`recipe_metadata_instruction` present and equal to the resolved version's value in every one of the three prompt-builder outputs). |

### Modified — cross-feature spec maintenance (implementer task, not this document rewriting a frozen file)

| Path | Change |
|---|---|
| `specs/ai_prompt_builder/requirements.md` (feature 11) | Amend R6–R9 (the ones pinning `CONFIGURED_SERVINGS` and `PromptInstructions.servings`) to the shape this feature ships: `servings` gone, `recipe_metadata_instruction` added. |
| `specs/ai_prompt_versioning/requirements.md` and `design.md` (feature 24) | Amend every `PromptInstructionsVersion.servings` reference (its field-shape `R<n>`, its `v1` construction example) the same way. |

Neither of these is `docs/requirements.md` or another file on the frozen list
in `AGENTS.md` §2 — they are specs, and `docs/specs.md`'s own worked example
(`ai_prompt_versioning` amending `ai_prompt_builder`) is the precedent for
exactly this kind of cross-feature spec upkeep. `tasks.md` T5 assigns it to
the **implementer**, at the same point feature 24's own T5 did — not to this
document, which only records that the amendment is needed and why.

Nothing else changes. `backend/core/tests/test_shared_kernel_guards.py`
needs no edit: `SHARED_KERNEL_MODULES` and
`test_the_shared_kernel_modules_are_ascii_only`'s asserted set already name
`domain/recipe.py`; neither `UNIT_VOCABULARY` nor
`INGREDIENT_CATEGORY_VOCABULARY`'s patterns match `servings` or
`estimated_time` text, so those guards are unaffected by this feature's
field additions. No `pyproject.toml` change — no dependency added or
removed; `planner-core` keeps `dependencies = []`.

---

## 4. `docs/architecture.md` §2.1 — this feature retires one item, adds none

§2.1 lists *"The configured servings count for AI prompts (`G-64`,
`FR-AI-13`)"* as a decide-in-a-spec item. `G-85` supersedes `G-64` outright —
servings is no longer configuration of any kind, so there is nothing left
for this item to mean. This feature's approval at the human gate **retires**
that §2.1 line; it does not replace it with a new one, because neither
`servings`' type (`int | None`) nor `estimated_time`'s (`str | None`, §5) is
a closed vocabulary or a configured constant the way the unit list, the
category list, or the old `CONFIGURED_SERVINGS` value were. They are ordinary
field-type decisions, proposed here exactly as `ai_prompt_builder`'s design
proposed `HEALTHY_BALANCED_INSTRUCTION`'s wording (§4 of that document) —
approved together with this spec, not a separate §2.1 sign-off.

`RECIPE_METADATA_INSTRUCTION`'s exact wording (§6, `G-86`) is the same kind
of ordinary content decision, not a §2.1 item either: it is prompt-content
text, not a closed vocabulary or a deployment-selected value — `ConfigPort`
still selects only *which prompt-wording version* is active (feature 24,
unchanged), never the wording itself.

---

## 5. Field types — the first of two concrete proposals this design makes

(The second is `RECIPE_METADATA_INSTRUCTION`'s wording, §6, added by `G-86`.)

**`servings: int | None = None`.** `FR-LIB-03`'s own word is "number of
servings" — a count. `int` is the narrowest type that says "a whole number,
nothing else assumed" without imposing a *range* (R7 explicitly permits zero
or negative — no floor, no ceiling, matching `Recipe.Ingredient.quantity`'s
own precedent of an unbounded `float`, `specs/recipe_model/design.md` §6).

**`estimated_time: str | None = None`.** Rejected: `int` minutes (§8,
alternative A) — see below. A free string is the only shape that carries "45
min", "1 h 15 min", "30-40 minutos" or any other author's phrasing without
this feature silently choosing a unit `G-85` never named and explicitly
disclaimed enforcing ("no format enforcement").

**Field order.** Both types append `servings` then `estimated_time` as the
last two fields, after `category`. `dataclasses` requires every
default-carrying field to follow every defaultless one; `Recipe.name`
through `Recipe.category` (and `RawRecipeOutput`'s equivalents) carry no
default today, so this is the only legal position, not a style choice. It
has the useful side effect that **every existing construction call site
across the codebase — all nine files the earlier `grep` for `Recipe(`/
`MealSnapshot(` found — already uses keyword arguments** (confirmed by
inspection of `ai_output.py`, `candidate.py`, and every `tests/domain/test_*`
file that constructs either type), so none of them break; they simply get
`servings=None, estimated_time=None` implicitly, which is the correct
"nothing was said" state for content authored before this feature existed.

---

## 6. Signatures

### `planner_core/domain/recipe.py`

```python
@dataclass(frozen=True)
class Recipe:
    """A library recipe's immutable content (FR-LIB-03).

    No cuisine, difficulty or kcal field (G-68, G-36). servings and
    estimated_time are purely informational: no validation, no dropdown
    constraint, no downstream logic reads either (G-85) - see
    test_no_recipe_metadata_logic.py.
    """

    name: str
    ingredients: tuple[Ingredient, ...]
    tools: tuple[str, ...]
    procedure: tuple[str, ...]
    category: IngredientCategory
    servings: int | None = None
    estimated_time: str | None = None


@dataclass(frozen=True)
class MealSnapshot:
    """The copy of a recipe's content taken when it enters a week (FR-CAND-07).

    Mirrors Recipe's shape field-for-field, including servings and
    estimated_time (G-85) - see snapshot() below.
    """

    name: str
    ingredients: tuple[Ingredient, ...]
    tools: tuple[str, ...]
    procedure: tuple[str, ...]
    category: IngredientCategory
    servings: int | None = None
    estimated_time: str | None = None


def snapshot(recipe: Recipe) -> MealSnapshot:
    """Return a MealSnapshot decoupled from recipe (FR-CAND-07, G-05)."""
    return MealSnapshot(
        name=recipe.name,
        ingredients=recipe.ingredients,
        tools=recipe.tools,
        procedure=recipe.procedure,
        category=recipe.category,
        servings=recipe.servings,
        estimated_time=recipe.estimated_time,
    )
```

### `planner_core/domain/ai_output.py`

```python
@dataclass(frozen=True)
class RawRecipeOutput:
    """A single AI-generated recipe, already-parsed but not yet validated (design.md section 1)."""

    name: str
    ingredients: tuple[RawIngredient, ...]
    tools: tuple[str, ...]
    procedure: tuple[str, ...]
    category: str
    servings: int | None = None
    estimated_time: str | None = None


def validate_ai_recipe_output(raw: RawRecipeOutput) -> Recipe:
    """Resolve raw's unit and category strings against the fixed vocabularies (G-48).

    servings and estimated_time carry through unchanged and unvalidated
    (G-85) - their absence is not a failure (R12, R13).
    """
    ingredients = tuple(
        Ingredient(name=item.name, quantity=item.quantity, unit=parse_unit(item.unit))
        for item in raw.ingredients
    )
    return Recipe(
        name=raw.name,
        ingredients=ingredients,
        tools=raw.tools,
        procedure=raw.procedure,
        category=parse_category(raw.category),
        servings=raw.servings,
        estimated_time=raw.estimated_time,
    )
```

### `planner_core/domain/candidate.py`

```python
def to_library_entry(meal: MealSnapshot, existing_names: Iterable[str]) -> LibraryEntryResult:
    """Build a new Recipe from meal; warn, never block, on a same-name collision (G-26)."""
    recipe = Recipe(
        name=meal.name,
        ingredients=meal.ingredients,
        tools=meal.tools,
        procedure=meal.procedure,
        category=meal.category,
        servings=meal.servings,
        estimated_time=meal.estimated_time,
    )
    ...
```

The two new keyword lines above (`servings=meal.servings,` and
`estimated_time=meal.estimated_time,`) are exactly the "one sanctioned line"
R21 and R22 name — see §7.

### `planner_core/domain/ai_prompt.py`

```python
OUTPUT_LANGUAGE: Final[str] = "es-ES"
"""FR-AI-07: AI output is produced in Castilian Spanish."""

HEALTHY_BALANCED_INSTRUCTION: Final[str] = (
    "Genera un menu saludable y equilibrado, variando las fuentes de proteina "
    "entre los platos. Esta indicacion tiene fines de planificacion domestica "
    "y no constituye un consejo medico."
)
"""FR-AI-06: healthy/balanced/protein-varied, labelled non-medical."""

RECIPE_METADATA_INSTRUCTION: Final[str] = (
    "Indica tambien el numero de comensales y una estimacion del tiempo de "
    "preparacion y coccion para cada receta generada. Son datos meramente "
    "informativos: no ajustes las cantidades de los ingredientes en funcion "
    "de ellos."
)
"""FR-AI-13 (G-86): instructs the model to state both fields itself. No
target value is supplied - this asks the model to state one, not the app.
The second sentence heads off the exact risk G-64/G-85 raised (mismatched
serving-size baselines corrupting ingredient quantities): it tells the model
not to let a stated servings count change how it sizes ingredients, keeping
the field purely informational rather than a scaling hint. Same treatment
as HEALTHY_BALANCED_INSTRUCTION: Castilian Spanish content sent to a future
AI provider, never shown to a user, so it does not go through messages.py."""

ALLOWED_UNITS: Final[tuple[Unit, ...]] = tuple(Unit)
"""FR-LIB-05 (consumed): the fixed unit vocabulary, reused from units.py, never redeclared."""


@dataclass(frozen=True)
class PromptInstructionsVersion:
    """One version of the wording FR-AI-06, FR-AI-07 and FR-AI-13 require (FR-AI-14, R1).

    Carries no servings field (R20): FR-AI-13's deployment-config framing for
    servings was dropped by G-85 - a prompt no longer states a target
    serving count of any kind, versioned or not. recipe_metadata_instruction
    (R23) replaces it: an instruction asking the model to state a value,
    not a value the app supplies (G-86).
    """

    version_id: str
    output_language: str
    healthy_balanced_instruction: str
    recipe_metadata_instruction: str


PROMPT_INSTRUCTION_VERSIONS: Final[dict[str, PromptInstructionsVersion]] = {
    "v1": PromptInstructionsVersion(
        version_id="v1",
        output_language=OUTPUT_LANGUAGE,
        healthy_balanced_instruction=HEALTHY_BALANCED_INSTRUCTION,
        recipe_metadata_instruction=RECIPE_METADATA_INSTRUCTION,
    ),
}
"""Append-only (R2, G-84): a version is added here when wording changes; an
existing key is never removed or overwritten."""


@dataclass(frozen=True)
class PromptInstructions:
    """The instructions every AI recipe-generation prompt carries, regardless of mode.

    Carries no servings field (R19) - see PromptInstructionsVersion above.
    recipe_metadata_instruction (R24) carries the G-86 instruction instead.
    """

    output_language: str
    healthy_balanced_instruction: str
    recipe_metadata_instruction: str
    allowed_units: tuple[Unit, ...]


def build_instructions(version_id: str) -> PromptInstructions:
    """The shared instruction block every prompt carries.

    output_language, healthy_balanced_instruction and
    recipe_metadata_instruction come from the prompt-instruction version
    named by version_id (FR-AI-14, R25); raises UnknownPromptVersion if it
    does not resolve.
    """
    version = resolve_prompt_version(version_id)
    return PromptInstructions(
        output_language=version.output_language,
        healthy_balanced_instruction=version.healthy_balanced_instruction,
        recipe_metadata_instruction=version.recipe_metadata_instruction,
        allowed_units=ALLOWED_UNITS,
    )
```

`resolve_prompt_version`, `UnknownPromptVersion` and
`PROMPT_VERSION_CONFIG_KEY` are untouched — none of them ever read
`servings` or `recipe_metadata_instruction` specifically; they operate on
`version_id`/the registry generically. `build_specification_prompt`,
`build_reference_prompt` and `build_category_prompt` are untouched too: they
only forward `version_id` to `build_instructions` and otherwise handle their
own mode-specific fields — `recipe_metadata_instruction` reaches all three
automatically, the same way `healthy_balanced_instruction` already does,
because all three embed the same `instructions: PromptInstructions` field
(`ai_prompt_builder`'s design §5, unchanged by this feature).

### Exceptions

None added, none removed. Every function this feature touches was already
total over its typed inputs before this change (`ai_prompt_builder`'s
design §6, `ai_output_validation`'s design §2); adding two optional,
unvalidated fields introduces no new way for any of them to fail.

---

## 7. The mechanical scan — R18 through R22

Mirrors `test_no_ambient_time.py`'s exact technique (`docs/architecture.md`
§1.2.2's own precedent for "a directory boundary only holds until someone
types the import; the control has to be mechanical"), applied to two field
names instead of a clock call:

```python
CORE_SRC = ...  # backend/core/src/planner_core, same as every existing guard

RECIPE_SOURCE = CORE_SRC / "domain" / "recipe.py"
AI_OUTPUT_SOURCE = CORE_SRC / "domain" / "ai_output.py"
CANDIDATE_SOURCE = CORE_SRC / "domain" / "candidate.py"

# Full-module exemption, same treatment test_shared_kernel_guards.py gives
# RECIPE_SOURCE and INGREDIENT_CATEGORY_SOURCE: these two modules' entire job
# is declaring or passing through the two fields; nothing in either module
# is domain logic that could plausibly compute with servings/estimated_time.
FULLY_EXEMPT_MODULES = (RECIPE_SOURCE, AI_OUTPUT_SOURCE)

# candidate.py is a general-purpose module (Candidate, SlotContents, promote,
# summary...) with exactly one legitimate reason to name either field - the
# two-line copy inside to_library_entry. A whole-file exemption there would
# be too coarse: it would let a *different*, illegitimate reference inside
# candidate.py hide behind the same pass. So candidate.py gets a
# SANCTIONED_CALL-style line-level allowance instead (test_no_ambient_time.py
# section, DEFAULT_CLOCK_SOURCE's own treatment).
CANDIDATE_SANCTIONED_LINES = (
    re.compile(r"\s*servings=meal\.servings,"),
    re.compile(r"\s*estimated_time=meal\.estimated_time,"),
)

INFORMATIONAL_METADATA = re.compile(r"\bservings\b|\bestimated_time\b")
```

`_offenders(sources)` walks every `*.py` under `CORE_SRC`, skipping
`FULLY_EXEMPT_MODULES` entirely and, for `CANDIDATE_SOURCE` only, skipping a
line that fullmatches one of `CANDIDATE_SANCTIONED_LINES`; every other match
of `INFORMATIONAL_METADATA` is an offence (R21, R22).

Two further assertions in the same module, structural rather than textual,
prove R18–R20 directly rather than by absence-of-text alone (a name could in
principle survive under a different spelling; a `dataclasses.fields()`
introspection cannot):

```python
assert "servings" not in {f.name for f in dataclasses.fields(PromptInstructions)}
assert "servings" not in {f.name for f in dataclasses.fields(PromptInstructionsVersion)}
assert not INFORMATIONAL_METADATA.search("CONFIGURED_SERVINGS")  # self-test only
assert "CONFIGURED_SERVINGS" not in ai_prompt_source_text  # R18
```

**`RECIPE_METADATA_INSTRUCTION`/`recipe_metadata_instruction` (R23–R25,
`G-86`) are deliberately outside this scan's scope.** `INFORMATIONAL_METADATA`
bans the identifiers `servings` and `estimated_time` specifically, because
those name a *recipe's own* field — the thing R21/R22 forbid domain logic
from reading. `recipe_metadata_instruction` is a differently-named field on
`PromptInstructions`/`PromptInstructionsVersion` (prompt content, never a
`Recipe`'s attribute value); it is not "servings under a new spelling," so
extending the ban to it would not prove anything the ban's own rationale
asks for. Confirmed empty overlap: `RECIPE_METADATA_INSTRUCTION`'s proposed
Castilian Spanish wording (§6) contains neither English identifier as a
substring, so it cannot false-negative past the scan by accident either.

**Self-testing discipline**, matching `test_no_ambient_time.py`'s own three
guard rules: (1) a test asserts `INFORMATIONAL_METADATA` actually matches
`"servings"`, `"estimated_time"`, `"raw.servings"` and
`"servings=meal.servings,"` — a pattern that matches nothing proves nothing;
(2) a test asserts the sanctioned lines exist verbatim inside
`candidate.py`, so the exemption cannot quietly become a hole covering
nothing; (3) the scanned-file list is asserted non-empty and to contain
named modules (`domain/shopping.py`, `domain/rules.py`,
`domain/generation.py`), so the guard cannot pass by scanning zero files.

---

## 8. Rejected alternatives

**A. `estimated_time: int | None` (minutes) instead of `str | None`.**
Rejected — see §5. `G-85` says "no format enforcement"; choosing minutes as
an integer *is* a format decision (it silently forbids "1 h 15 min" or a
range, and forces every future reader/writer to agree that the unit is
minutes, which nothing in `requirements.md` or `G-85` states). A free string
carries whatever an author or an AI response actually says, unmodified —
exactly "purely informational."

**B. Leave `CONFIGURED_SERVINGS` and `PromptInstructions.servings` in place
but simply stop using them anywhere.** Rejected. The acceptance criterion is
explicit: *"no code path still treats servings as global config."* A dead
constant nobody reads is still a code path a future contributor could wire
back up by mistake, and it would fail R18's mechanical scan (which checks
for the constant's *existence*, not its use) — the same reasoning
`test_no_ambient_time.py` applies to `SystemClock`: reach is checked by
naming, not by calling.

**C. Exempt the whole of `candidate.py` from the mechanical scan, the same
blanket treatment `recipe.py` and `ai_output.py` get.** Rejected — see §7.
`candidate.py` is not a dedicated "carries these two fields" module the way
the other two are; it owns `Candidate`, `SlotContents`, `promote`,
`remove_candidate`, `summary` and more, none of which has any legitimate
reason to reference `servings`/`estimated_time`. A blanket exemption would
let a genuine violation hide inside `promote()` or `summary()` undetected —
defeating the guard's purpose. The narrower, line-level allowance costs one
extra regex and buys back that coverage.

**D. Add `FR-CAND-07` to this feature's own `covers` array (which would
require editing `feature_list.json` beyond the status flip) instead of
treating `MealSnapshot`'s extension as `FR-LIB-03`-mandated and
`FR-CAND-07`-consumed.** Rejected. `spec_author` edits `feature_list.json`
only to set `status: spec_ready` (project convention, `AGENTS.md` §3);
widening `covers` is a scope decision for whoever wrote the feature list,
not this document. `G-85`'s own text already grounds the extension directly
("`Both` ... become per-recipe attributes, stored on `Recipe`/
`MealSnapshot`"), so `FR-LIB-03` alone carries enough mandate without
needing a second id in `covers`.

**E. Add a new AI-prompt instruction telling the model to state a servings
count and an estimated prep/cook time for each recipe it generates.**
**Accepted — corrected at the design gate, `G-86` (Part V).** This
document's first draft rejected this, reading `G-85`'s passive replacement
text for `FR-AI-13` ("AI-generated recipes **may** set a servings count...")
literally, and concluded that inventing an instruction here would be scope
no `FR-*` granted. The human caught this at the gate: `G-85`'s amendment
struck the prompt-instruction clause *without meaning to* — only the fixed
deployment-config target (`CONFIGURED_SERVINGS = 4`) was meant to go, not
the instruction itself. `G-86` re-amends `FR-AI-13` to say so explicitly:
"AI recipe generation **shall instruct the model** to state a servings
count and an estimated prep/cook time for each recipe it generates." This
is no longer invention — it is `FR-AI-13`'s own frozen (as re-amended) text,
translated the same way every other `R<n>` in this spec translates a frozen
requirement. `RECIPE_METADATA_INSTRUCTION` (§6) is the result: an
instruction to *state* a value, never a target value the app supplies,
keeping every other half of `G-85`'s decision — no validation, no fixed
target, no cross-recipe consistency, no downstream logic — intact.

**E'. Fold the new instruction into the existing
`HEALTHY_BALANCED_INSTRUCTION` string instead of a separate
`RECIPE_METADATA_INSTRUCTION` constant and a separate `PromptInstructions`
field.** Rejected. `HEALTHY_BALANCED_INSTRUCTION` (`FR-AI-06`) and the new
instruction (`FR-AI-13`) trace to two different frozen requirements with two
different reasons to exist; merging them into one string would make a
future wording change to one risk silently rewording the other, and would
force `requirements.md`'s R6–R9-equivalent equality assertions (here, R25)
to test a substring of a larger string instead of a whole field — the same
"one instruction, one field" discipline `ai_prompt_builder`'s design §5
already chose over a single overloaded dataclass for the three prompt
*types*, applied here to instruction *strings* instead. A separate constant
and field cost one more line each and buy back that independence.

**E''. Two separate instruction constants/fields — one for `servings`, one
for `estimated_time` — instead of one instruction naming both.** Rejected.
`G-86` is explicit that the correction "applies to both fields (servings
and estimated_time), not just servings," but nothing requires them to be
two *sentences*: `FR-AI-13`'s own re-amended text states both in one clause
("state a servings count **and** an estimated prep/cook time"). One
instruction mirrors the requirement's own grouping and avoids two near-
duplicate constants a future wording change would have to keep in sync by
hand.

**F. Constrain `servings` to a small fixed range (e.g. 1–99) as basic
sanity-checking, short of a full dropdown.** Rejected. `G-85`'s own words are
"no validation" without qualification, and R7 tests exactly that a negative
or zero value is accepted — a range check is validation by another name.

---

## 9. Boundary checks and gate questions

### Boundary checks

- **`docs/architecture.md` §2 (pending, human-owned):** nothing here needs
  P2–P6. No AI provider is invoked or referenced (`P4` stays untouched, same
  as `ai_prompt_builder`'s own boundary check).
- **§2.1 decide-in-a-spec items:** one retired (§4), none added. The unit
  list, category list and prompt-version registry are all reused unchanged.
  `RECIPE_METADATA_INSTRUCTION`'s wording (§6) is content proposed at this
  gate, the same class of decision `HEALTHY_BALANCED_INSTRUCTION`'s wording
  was at feature 11's — not a new §2.1 item (§4).
- **Frozen docs:** none modified. `docs/data_model.md` needs no change —
  `numeroComensales`/`tiempo` were already listed there; this feature is the
  code catching up to that document, exactly as `G-85`'s own reasoning states
  (*"`docs/data_model.md` is the source of truth for shape here"*).
- **User-facing strings:** none added. Neither field goes through
  `messages.py` — there is no validation failure to have a message for.
  `RECIPE_METADATA_INSTRUCTION` is prompt content sent to a future AI
  provider, never shown to a user, so it does not go through `messages.py`
  either — same reasoning `ai_prompt_builder`'s design §4 gave for
  `HEALTHY_BALANCED_INSTRUCTION`.
- **Runtime dependencies:** none added; `planner-core` keeps
  `dependencies = []`.
- **Requirements invented:** none. Every `R<n>` cites `FR-LIB-03`,
  `FR-MENU-04` or `FR-AI-13` — all three in this feature's `covers` array.
  R23's `FR-AI-14` citation is a consumed, not owned, id (`requirements.md`'s
  scope note) — the same "cite without claiming" pattern this document uses
  for `FR-CAND-07`.

### Gate questions for the human

**Resolved at the design gate, 2026-08-26 (`G-86`, Part V):** questions 1, 3
and 4 below were accepted as originally recommended. Question 2 was also
accepted, but its premise needs a correction recorded here rather than a
silent edit: the question originally framed removing `servings` as leaving
`PromptInstructions`/`PromptInstructionsVersion` **permanently smaller** —
one field gone, nothing replacing it. That premise was itself downstream of
the same oversight `G-86` corrects (§0, §8 alternative E). The as-built
answer is different in kind: `servings` (an app-supplied target value) is
still removed, exactly as recommended, but `recipe_metadata_instruction` (an
instruction asking the model to state its own value) is added in its place
— so the two types end up the **same field count**, not one field lighter,
though the meaning of what occupies that slot changes completely. The
"stronger guarantee R18 proves" the question asked about is unaffected: R18
still bans any deployment-wide servings *target* constant; it says nothing
about, and is not weakened by, an instruction constant that supplies no
target at all.

1. **Field types (§5): `servings: int | None`, `estimated_time: str |
   None`.** Confirming these are the concrete values this feature's approval
   settles, the same way `CONFIGURED_SERVINGS = 4` and
   `HEALTHY_BALANCED_INSTRUCTION`'s wording were settled at feature 11's own
   gate. **Accepted**, and unaffected by `G-86` — the correction is about the
   presence of an instruction, not either field's shape.

2. **Removing `servings` from `PromptInstructions`/`PromptInstructionsVersion`
   entirely (§6), rather than keeping the field but always setting it to
   `None`/leaving it unused.** This is the more disruptive of two ways to
   satisfy "no code path treats servings as global config" — the other
   (keep-but-unused) was rejected in §8, alternative B, but costs a wider
   diff across feature 11's and 24's already-`done` code and specs. **Accepted
   — see the resolution note above** for how `G-86` changed what replaces the
   removed field.

3. **`candidate.py`'s `to_library_entry` copy-through (§6, §7) is included in
   this feature's diff even though `candidate.py` belongs to feature 5,
   already `done`.** Confirming this is treated as a mechanically necessary
   consequence of adding fields to `MealSnapshot` (the alternative — leaving
   it unpatched — would silently drop both fields on every library save, the
   exact kind of data loss `docs/architecture.md` §4 invariant 2 warns
   against generalizing from shopping items to any user-entered content) and
   not scope creep into feature 5's territory. **Accepted**, unaffected by
   `G-86`.

4. **Cross-feature spec maintenance (§3) is assigned to `tasks.md` T5 as an
   implementer task, not performed by this document.** Confirming that
   matches the precedent `ai_prompt_versioning` set for amending
   `ai_prompt_builder`'s `requirements.md`, and that no additional feature
   (e.g. `ai_lambda`, feature 17, still `blocked`) needs its own `covers`
   array touched by this change — checked directly: feature 17's `covers` is
   `["FR-AI-09", "NFR-AI-01"]`, neither `FR-AI-13` nor `FR-LIB-03`, so nothing
   there depends on today's prompt-instruction shape. **Accepted** — T5 now
   additionally amends the same two specs' `R<n>`s for
   `recipe_metadata_instruction` (§3), not only for `servings`'s removal.

5. **New at this revision: `RECIPE_METADATA_INSTRUCTION`'s exact wording
   (§6).** Proposed here the same way `HEALTHY_BALANCED_INSTRUCTION`'s
   wording was proposed at feature 11's gate — an ordinary content decision,
   approved together with this revision unless the human amends it. The
   second sentence ("no ajustes las cantidades... en funcion de ellos") is a
   deliberate addition beyond `FR-AI-13`'s literal text, included to head off
   the one failure mode `G-64`/`G-85` both worried about (a stated servings
   count silently driving ingredient-quantity scaling) at the prompt level,
   symmetric with how `HEALTHY_BALANCED_INSTRUCTION`'s own second sentence
   ("no constituye un consejo medico") heads off a different
   over-interpretation risk. If the human considers this an invented
   constraint rather than a reasonable instruction-wording choice, it is a
   one-line edit to drop.
