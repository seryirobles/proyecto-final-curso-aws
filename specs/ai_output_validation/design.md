# ai_output_validation — Design

> Feature 12 · tier 1 · pure `planner_core.domain`
> Read `requirements.md` first. This document records the technical decisions
> taken before any code is written, per `docs/specs.md`.
> Depends on feature 4 `recipe_model` (closed: `Recipe`, `Ingredient`,
> `IngredientCategory`), feature 3 `text_and_units` (closed: `Unit`,
> `parse_unit`), feature 6 `rules_model` (closed: `parse_category`), feature 2
> `week_calendar` (closed: `SlotRef`) and feature 11 `ai_prompt_builder`
> (closed: `PromptInstructions` and the three prompt builders). It does not
> import feature 10 `generation_request` (see §6, alternative C).

## 0. The invariant this feature exists to protect

`docs/gaps_and_resolutions.md`, `G-48`:

> The AI path needs validation, not just prompting, because model output is
> not guaranteed to follow instructions; a failed validation is surfaced
> through the existing per-slot failure flow (`FR-AI-12`).

and `G-66`:

> [Insufficient library recipes is s]urfaced through the existing per-slot
> failure mechanism with a clear message naming the cause..., never a silent
> partial result.

Both gaps point at the same shape: AI output (or the lack of a usable library
recipe) can fail, and that failure must become an explicit, named, Spanish
value the caller can show — never an exception that crashes a whole-week run,
never a silently-dropped slot, never a `Recipe` built from data that skipped
validation.

---

## 1. Scope boundary — what this feature owns

**This feature does not call an AI provider, search the library, or persist
anything.** It is a pure translator and a pure state machine:

- Given an already-parsed, provider-agnostic recipe shape (`RawRecipeOutput`
  — see §4 for why this shape, not a raw `Mapping`), it either returns a
  valid `Recipe` or raises a named exception (`validate_ai_recipe_output`),
  and a convenience wrapper (`validate_and_preview`) turns that raise into a
  `GenerationFailure` value instead of letting it propagate.
- Given a validated `Recipe`, it represents the not-yet-persisted preview a
  user can accept or discard (`RecipePreview`, `accept_preview`,
  `discard_preview`).
- It defines the per-slot outcome shape (`SlotGenerationResult`,
  `GenerationSuccess`, `GenerationFailure`, `GenerationFailureReason`) a
  whole-week run's caller assembles one entry per slot into.

**What stays outside this feature, and where it goes instead:**

| Concern | Lives in |
|---|---|
| Turning a raw AI provider response (HTTP body, SDK object) into `RawRecipeOutput` | Feature 17 (`ai_lambda`) — the only package allowed to import an AI SDK (`docs/architecture.md` §1.2, §3.1 rule 3). |
| Actually invoking the provider, once or on regeneration | Feature 17. This feature has no IO of any kind. |
| Building the (possibly adjusted) prompt a regeneration sends | Already built — `ai_prompt_builder`'s `build_specification_prompt` / `build_reference_prompt` (feature 11, closed), which already accept ingredients/tools/extra-specifications as parameters. Regeneration does not need a new function here; see §5. |
| Detecting that library-only/mix mode has no suitable recipe for a slot | Feature 17 — it has the library read access this feature deliberately does not. This feature only provides the vocabulary (`GenerationFailureReason.INSUFFICIENT_LIBRARY_RECIPES`) and message to report it with once detected. |
| Showing a loading/progress state while a call is in flight | Feature 20 (frontend) / feature 17's async handling. Not domain data — see §1.1. |
| Retrying a failed slot | Reuses `generation_request`'s existing per-slot idempotency machinery (feature 10, closed) — a retry is simply calling the same generation path again for that one slot. No new type needed. |
| Persisting an accepted preview as a `Candidate` or a library `Recipe` | `candidate.py`'s existing `new_candidate` / `to_library_entry`, and `recipe.py`'s existing `snapshot` (features 5 and 4, both closed). `accept_preview` hands back the `Recipe`; the caller feeds it into whichever of those two paths the UI targeted. |

### 1.1 Why "progress/loading state" has no domain type

`FR-AI-12`'s progress/loading clause describes a **transient UI state**
("a call is currently in flight"), not a fact about a completed generation.
`docs/architecture.md` §3 places business logic — not UI state — in
`planner_core`; a "pending" enum member here would have no behaviour, no
invariant and no test beyond "it exists," and this feature already draws that
line the same way `ai_prompt_builder`'s design (§1) drew it for "which slot
gets an AI call."

---

## 2. Layering

`docs/architecture.md` §3: `domain/` is *"Pure logic. No IO, no AWS SDK, no
framework, no clock."* Every piece below is a plain value or a pure function
between plain values.

| Piece | Layer | Why |
|---|---|---|
| `RawIngredient`, `RawRecipeOutput`, `validate_ai_recipe_output`, `RecipePreview`, `new_preview`, `accept_preview`, `discard_preview`, `GenerationFailureReason`, `GenerationFailure`, `GenerationSuccess`, `build_generation_failure`, `validate_and_preview`, `SlotGenerationResult` | `planner_core/domain/ai_output.py` | Pure value objects and pure functions; no IO, no ambient state, no clock, no provider SDK. |

No `application/` piece: exactly like `ai_prompt_builder` and
`generation_request`, every input here is caller-supplied.

---

## 3. Files

### Created

| Path | Contents |
|---|---|
| `backend/core/src/planner_core/domain/ai_output.py` | `RawIngredient`, `RawRecipeOutput`, `validate_ai_recipe_output`, `RecipePreview`, `new_preview`, `accept_preview`, `discard_preview`, `GenerationFailureReason`, `GenerationFailure`, `GenerationSuccess`, `GenerationOutcome` (type alias), `build_generation_failure`, `validate_and_preview`, `SlotGenerationResult`. |
| `backend/core/tests/domain/test_ai_output.py` | R1–R21. |

### Modified

| Path | Change |
|---|---|
| `backend/core/src/planner_core/messages.py` | Three new `UPPER_SNAKE` es-ES constants (content proposed in §4): `AI_GENERATION_INVALID_OUTPUT`, `AI_GENERATION_INSUFFICIENT_LIBRARY_RECIPES`, `AI_GENERATION_UNAVAILABLE`. No existing constant is touched. |

No `pyproject.toml` change: no dependency added. `ai_output.py` imports only
`dataclasses`, `enum` (stdlib) and sibling `planner_core.domain` /
`planner_core.messages` modules — `planner-core` keeps `dependencies = []`.

`backend/core/tests/test_shared_kernel_guards.py`'s comment on
`UNIT_VOCABULARY` already names *"features 4, 7, 8 and 12 must import `Unit`
freely"* — this feature imports `Unit` (via `parse_unit`) and declares no
second unit or category vocabulary, so `SHARED_KERNEL_MODULES` (§7, mirroring
`ai_prompt_builder`'s own §7) needs no change.
`test_planner_core_never_constructs_unit_directly` (feature 3, R9) already
bans `Unit(...)` anywhere in `planner_core` — `validate_ai_recipe_output`
resolves every unit through `parse_unit`, never `Unit(raw_ingredient.unit)`
directly, and the same discipline applies to `parse_category` (the guard's
`INGREDIENT_CATEGORY_VOCABULARY` pattern only bans redeclaring the enum, but
matching `parse_unit`'s precedent is followed regardless).

---

## 4. Content proposed (not a `docs/architecture.md` §2.1 item)

Three es-ES failure messages, proposed here exactly as `ai_prompt_builder`
proposed `HEALTHY_BALANCED_INSTRUCTION` — an ordinary content decision, not a
§2.1 item, approved together with this spec at the human gate:

```python
AI_GENERATION_INVALID_OUTPUT = (
    "La receta generada no es valida. Puedes intentarlo de nuevo."
)
AI_GENERATION_INSUFFICIENT_LIBRARY_RECIPES = (
    "No hay suficientes recetas en la biblioteca para completar la semana "
    "con este modo. Anade recetas, cambia de modo o ajusta las reglas."
)
AI_GENERATION_UNAVAILABLE = (
    "La generacion con IA no esta disponible en este momento. "
    "Puedelo intentar mas tarde."
)
```

`AI_GENERATION_INSUFFICIENT_LIBRARY_RECIPES`'s wording names the three
remedies `G-66`'s own reasoning gives ("add recipes, switch to mix/AI-only
mode, relax rules") so the message is actionable, not just apologetic.

`AI_GENERATION_UNAVAILABLE` exists for `GenerationFailureReason
.GENERATION_UNAVAILABLE`, whose grounding is `G-70`'s text amending
`FR-AI-10` (in this feature's `covers`): *"It surfaces a friendly es-ES
message when generation is unavailable because the cap is reached."* No
`feature_list.json` acceptance bullet names this reason directly (unlike
`INVALID_OUTPUT` and `INSUFFICIENT_LIBRARY_RECIPES`, both bulleted); it is
included because `FR-AI-10` itself, not merely its gap note, is one of this
feature's three covered ids, and this is translation of that id's own
amended text, not invention. Flagged explicitly at §7 gate question 1 in case
the human disagrees with including it now.

Following `docs/conventions.md`'s Language policy, these are plain identifier
names (English) holding Castilian Spanish string content — the same split
`ai_prompt_builder`'s `HEALTHY_BALANCED_INSTRUCTION` already established, and
unlike that constant, these strings **are** user-facing (`FR-UX-03`), so they
belong in `messages.py`, not inline.

---

## 5. Why "regenerate" gets no dedicated function

`FR-AI-10`: *"the user can accept, discard, or regenerate (optionally
adjusting the specifications)... Each regeneration is a fresh AI invocation."*

A `regenerate_preview(preview, ...)` function was considered and rejected —
see §6, alternative A. The lifecycle this feature actually needs to represent
is: discard the current `RecipePreview` (or simply stop holding a reference
to it — `discard_preview` returns `None` precisely because nothing was ever
persisted, R13) and call `validate_and_preview` again on a **new** AI
response. "Adjusting the specifications" is already fully expressible through
`ai_prompt_builder`'s existing `build_specification_prompt` /
`build_reference_prompt` parameters (`ingredients`, `tools`,
`extra_specifications`) — the caller (feature 17) passes different arguments
to the same builder it used the first time. Nothing about "fresh invocation"
needs new domain machinery: `RecipePreview` is `frozen=True` (R10) and
`new_preview` takes no previous preview as input, so there is no code path
that could mutate or extend an existing preview into a "regenerated" one —
every call produces an independent value.

"No per-user quota" (`G-70`) is satisfied the same structural way: R10 fixes
`RecipePreview`'s fields at exactly `{recipe}`, and no other type this
feature declares carries a counter, a user id, or a timestamp either. There
is nothing to increment because nothing here counts.

---

## 6. Rejected alternatives

**A. A dedicated `regenerate_preview(preview, adjusted_ingredients=None, ...)`
function instead of relying on `ai_prompt_builder`'s existing builders (§5).**
Rejected. It would have to accept a `SpecificationPrompt | ReferencePrompt`
union to know which builder to call, re-deriving `ai_prompt_builder`'s own
mode distinction one layer up for no behavioural gain — the caller already
holds whichever prompt type it used to produce the current preview and can
call the matching builder directly. Adding it here would also blur the
boundary §1 draws: this feature validates and represents outcomes, it does
not build prompts.

**B. `GenerationOutcome` as a pair of optional fields
(`preview: RecipePreview | None`, `failure: GenerationFailure | None`)
instead of an explicit `GenerationSuccess | GenerationFailure` union (R18,
R19, R20).**
Rejected. A `None`/`None` or a both-set pair are representable-but-invalid
states — exactly what `docs/architecture.md` §4 invariant 12 ("functions...
do not return `None` to signal failure") warns against generalizing from
single-value returns to a struct. The explicit two-type union makes "which
one happened" a property of which type the value *is*, mirroring
`ai_prompt_builder`'s own choice of three distinct prompt dataclasses over
one dataclass with empty/`None` mode-specific fields (that spec's design §5).

**C. `SlotGenerationResult` importing `generation_request.GenerationTargets`
or `SlotRef`'s producing module directly, instead of only `SlotRef` from
`calendar.py`.**
Rejected — considered because feature 10 already pairs `SlotRef` with other
data (`PinnedTarget`, `SkippedPin`). This feature needs only the `SlotRef`
type, not feature 10's request/target shapes, so importing
`planner_core.domain.generation` would add a dependency this feature has no
other reason to take, the same reasoning `ai_prompt_builder`'s design (§8,
alternative B) gave for not accepting `GenerationTargets` directly.
`SlotGenerationResult`'s `slot: SlotRef` + `outcome: ...` shape does mirror
`PinnedTarget`'s and `SkippedPin`'s own "slot-plus-data" idiom deliberately —
consistency of shape, not of import.

**D. A new `MalformedAiRecipeOutput` exception for structural failures beyond
unit/category resolution (e.g. an empty `name`, a negative `quantity`).**
Rejected. `RawIngredient`/`RawRecipeOutput` are typed dataclasses (R1, R2);
the only failure this feature can observe from a value that already
satisfies those types is a `unit` or `category` code outside its fixed
vocabulary (R4, R6) — both already have a named, reused exception. Field-level
minutiae (name length, non-empty checks, quantity bounds) is explicitly listed
as out of requirement scope in `docs/gaps_and_resolutions.md`'s negative
space ("implementation details below requirement granularity; es-ES
validation messaging is already required"). Inventing a broader exception
here would validate a rule no `FR-*` states.

---

## 7. Boundary checks and gate questions

### Boundary checks

- **`docs/architecture.md` §2 (pending, human-owned):** nothing here needs
  P2, P3, P5 or P6. `P4` (the AI provider itself) is exactly what this
  feature stays agnostic to — `RawRecipeOutput` is deliberately a plain,
  already-parsed shape (§1), never a provider SDK type.
- **§2.1 decide-in-a-spec items:** none touched. The unit list, category
  list and servings count are all reused unchanged from their owning
  features (3, 6, 11).
- **Frozen docs:** none modified.
- **`Recipe`/`MealSnapshot` (shared kernel, feature 4, closed):** unchanged.
  No field added — see the next paragraph on the `numeroComensales` gate
  question `ai_prompt_builder` left open.
- **User-facing strings:** the three new constants in §4 go through
  `messages.py`, per `docs/conventions.md`.
- **Runtime dependencies:** none added.
- **Requirements invented:** none. Every `R<n>` cites `FR-AI-10`, `FR-AI-12`
  or `FR-LIB-05` (all three in `covers`), or `FR-LIB-03`/`FR-UX-03` (existing
  frozen ids this feature consumes but does not own — see `requirements.md`'s
  scope note, same treatment `ai_prompt_builder` gave `FR-LIB-05` itself).

### Gate questions for the human

1. **Does `GenerationFailureReason.GENERATION_UNAVAILABLE` (and its message,
   `AI_GENERATION_UNAVAILABLE`) belong in this feature, given no
   `feature_list.json` acceptance bullet names it directly?** Grounding:
   `G-70`'s text amending `FR-AI-10` (§4). Recommendation: keep it — it costs
   one enum member and one message constant, is grounded in a covered id's
   own amended text, and gives feature 17 somewhere to put a cap-reached
   failure without a follow-up spec amendment. If the human disagrees, drop
   the `GENERATION_UNAVAILABLE` member, its row in R14/R17, and the
   `AI_GENERATION_UNAVAILABLE` constant — nothing else in this design depends
   on it.

2. **`ai_prompt_builder`'s design §9 gate question 1 (human-resolved
   2026-08-26) named this feature or feature 17 as "whichever first parses AI
   output into a `Recipe`," to receive `FR-LIB-03` (and `FR-CAND-07` if
   `MealSnapshot` needs it) in its `covers` array at that time, for
   recording `numeroComensales`/servings on the result.** This feature *does*
   parse AI output into a `Recipe` (`validate_ai_recipe_output`). It
   deliberately does **not** claim that resolution: `numeroComensales` is not
   added to `Recipe` here, and `FR-LIB-03` is cited only as *consumed* (the
   scope-note table in `requirements.md`), not added to this feature's
   `covers` array, because the servings question is orthogonal to what this
   feature validates (units, category, schema) and `Recipe`/`MealSnapshot`
   are shared-kernel types this feature has no mandate to extend.
   Recommendation: leave the `numeroComensales` question for feature 17
   (`ai_lambda`), which is where the AI response first exists at all as a
   concrete value to attach a servings figure to — this feature only proves
   that value, once handed a `RawRecipeOutput`, resolves to a valid `Recipe`.
