# generation_request — Design

> Feature 10 · tier 1 · pure `planner_core.domain`
> Read `requirements.md` first. This document records the technical decisions
> taken before any code is written, per `docs/specs.md`.
> Depends on feature 6 `rules_model` (closed, `RuleSet`, `CategoryCountRule`,
> `PinRule`, `apply_override`), feature 5 `week_plan_model` (closed,
> `SlotContents`, `Candidate`, `definitive`) and feature 2 `week_calendar`
> (closed, `IsoWeek`, `SlotRef`, `slots_from`) — this feature **consumes**
> all three and re-derives none of them.

## 0. The invariant this feature exists to protect

`docs/gaps_and_resolutions.md`, `G-71`:

> Slots holding a definitive are skipped entirely, and an existing
> definitive outranks a pin rule — the skipped pin is reported through the
> existing per-slot messaging (FR-AI-12) rather than applied silently.
> Category counts describe the week's final state: existing meals count
> toward each total and generation supplies only the remainder.

Every function below is subordinate to this: a slot's *current occupancy*,
not merely the rules, decides whether it is a target (§5), and a
pre-existing definitive is reported when it silently overrides a pin, never
swallowed (§5).

---

## 1. Scope boundary — what this feature owns of each `FR-*`

See `requirements.md`'s scope-note table for the full per-requirement split.
Two lines deserve emphasis because they are easy to get wrong:

**This feature does not generate, add, or persist anything.** It is a pure
projection: given the shared rules, an optional per-run override, a week, a
"first eligible day" boundary and the week's current occupancy, it answers
three questions — what are the effective rules, which slots need what, and
what key identifies this request. `open_slots` and `pinned_slots` are
descriptions for feature 11/12/17 to act on; no function here calls
`candidate.add_candidate` or anything that mutates a `SlotContents`.

**"Which live week is current" and "what is today" are not resolved here.**
`first_day` is a plain, caller-supplied `date`, exactly like
`calendar.slots_from`'s own existing parameter. Deciding that the current
week's `first_day` is today and the next week's is its Monday (i.e. no
restriction) is an `application/`-layer concern for whichever feature wires
an actual submission handler — the same split `week_calendar` already
drew between `domain/calendar.py` (plain dates) and
`application/live_weeks.py` (reads the `Clock` once). This feature adds no
`application/` piece of its own because it has nothing that needs "now" —
every input is caller-supplied.

**The reusable artefact this feature adds.** `GenerationMode`,
`RuleOverride`, `GenerationRequest`, `PinnedTarget`, `SkippedPin`,
`GenerationTargets`, `GenerationPlan`, and the four functions that produce
and compose them. Feature 11 (`ai_prompt_builder`) consumes
`GenerationTargets.open_slots` and `.remaining_category_counts` to build
per-slot prompts; feature 12/17 consume `.pinned_slots` and
`.skipped_pins` to add deterministic candidates and surface FR-AI-12
messages, without recomputing any of this feature's arithmetic.

---

## 2. Layering

`docs/architecture.md` §3: `domain/` is *"Pure logic. No IO, no AWS SDK, no
framework, no clock."* Every function below is a pure transformation of
plain values — no port, no clock, no id generator, no IO.

| Piece | Layer | Why |
|---|---|---|
| `GenerationMode`, `RuleOverride`, `GenerationRequest`, `PinnedTarget`, `SkippedPin`, `GenerationTargets`, `GenerationPlan`, and every function in §6 | `planner_core/domain/generation.py` | Pure value objects and pure functions between them; no IO, no ambient state, no clock. `first_day` is caller-supplied, mirroring `calendar.slots_from`. |

No `application/` piece — see §1. This feature is architecture-independent
in the same sense `week_plan_model` and `rules_model` are: its tests need
no fake beyond plain values, not even a fixed clock.

---

## 3. Files

### Created

| Path | Contents |
|---|---|
| `backend/core/src/planner_core/domain/generation.py` | `GenerationMode`, `RuleOverride`, `GenerationRequest`, `PinnedTarget`, `SkippedPin`, `GenerationTargets`, `GenerationPlan`, `effective_rules`, `resolve_targets`, `idempotency_key`, `build_plan`. |
| `backend/core/tests/domain/test_generation.py` | R1–R25. |

### Modified

None. `generation.py` declares one new closed vocabulary, `GenerationMode`
— see §7 for why it is not added to
`backend/core/tests/test_shared_kernel_guards.py`'s `SHARED_KERNEL_MODULES`
tuple. No `pyproject.toml` change: no dependency added, `planner-core` keeps
`dependencies = []` (`hashlib` and `json`, used by `idempotency_key`, are
both standard library).

---

## 4. `docs/architecture.md` §2.1 items

None of the three named items (unit list, ingredient-category list,
servings count) are touched here. This feature proposes one concrete value
of its own that is not one of the three: the idempotency key's hash and
encoding scheme (§6, gate question 1). It is flagged there rather than
assumed pre-authorized, following `FR-AI-08`'s own wording — *"a hash of
the request"* — which names the mechanism's shape but not its concrete
algorithm.

---

## 5. Occupancy, not rules alone, decides the target set

`FR-AI-11`'s own text already says pins and disabled days are enforced
"deterministically... by the system" — that half needs only the rules.
`G-71` added the harder half: a slot's *current content* also decides
whether it is a target, and rules alone cannot answer that. Two shapes
could combine the two:

**A. Compute the rule-only target set first (disabled days, pins), then
have the caller (feature 11/12/17) separately check each slot's occupancy
before acting on it.** Rejected. This splits one invariant — "an existing
definitive always outranks a pin" — across two call sites that both have to
get it right, and it is exactly the shape `G-71`'s own gap statement
describes as the thing that went wrong: *"nothing consulted the current
contents of the week."* A caller that forgets the check re-introduces the
bug this feature exists to close.

**B. `resolve_targets` takes `occupancy` directly and folds the check into
the same pass that resolves pins and disabled days** (chosen here). One
function, one pass over the week's candidate slots, and "skipped means
skipped" is a property of `GenerationTargets` itself — a slot with a
definitive simply never appears in `open_slots` or `pinned_slots`, so a
caller cannot re-target it by accident. The reported half (`skipped_pins`)
exists only for the slots where silence would have hidden something
(`G-71`'s "reported... never applied silently"); a plain skip with no pin
involved needs no report, since no rule was overridden.

**Category-count occupancy is definitive-only, not candidate-inclusive.**
`R15` counts a slot toward a category total only when it has a definitive.
`docs/architecture.md` §4 invariant 6 — *"Definitive meals derive the
shopping list. Candidates never do"* — and `G-71`'s own framing (*"a
definitive meal is the strongest signal of intent in the product"*) both
point the same way: a slot holding only candidates has not yet decided what
the week's meal there will be, so it cannot yet count toward what the
week's *final state* contains. Counting candidates would let an unresolved
slot with three different-category candidate proposals count toward three
totals it may never actually reach. Flagged as gate question 2 rather than
assumed, since the frozen text says "meals already present" without
naming which kind.

---

## 6. Signatures

```python
"""Whole-week generation requests: effective rules, target slots, idempotency key."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from planner_core.domain.calendar import IsoWeek, SlotRef, slots_from
from planner_core.domain.candidate import SlotContents, definitive
from planner_core.domain.rules import CategoryCountRule, PinRule, RuleSet, apply_override


class GenerationMode(StrEnum):
    """The three whole-week generation modes (FR-AI-03). Behavior is not this feature's."""

    LIBRARY_ONLY = "library_only"
    AI_ONLY = "ai_only"
    MIX = "mix"


@dataclass(frozen=True)
class RuleOverride:
    category_counts: tuple[CategoryCountRule, ...] | None = None
    pins: tuple[PinRule, ...] | None = None
    disabled_days: tuple[int, ...] | None = None


@dataclass(frozen=True)
class GenerationRequest:
    week: IsoWeek
    mode: GenerationMode
    rule_override: RuleOverride | None = None


@dataclass(frozen=True)
class PinnedTarget:
    """An unoccupied slot resolving deterministically to its pinned library meal."""

    slot: SlotRef
    recipe_id: str


@dataclass(frozen=True)
class SkippedPin:
    """A pin an existing definitive outranked; reported rather than applied silently (G-71)."""

    slot: SlotRef
    pin: PinRule


@dataclass(frozen=True)
class GenerationTargets:
    open_slots: tuple[SlotRef, ...]
    pinned_slots: tuple[PinnedTarget, ...]
    skipped_pins: tuple[SkippedPin, ...]
    remaining_category_counts: tuple[CategoryCountRule, ...]


@dataclass(frozen=True)
class GenerationPlan:
    effective_rules: RuleSet
    targets: GenerationTargets
    mode: GenerationMode
    idempotency_key: str


def effective_rules(shared: RuleSet, override: RuleOverride | None) -> RuleSet:
    """The run's effective rules; shared is never written to (FR-AI-05, FR-RULE-05)."""
    if override is None:
        return shared
    return apply_override(shared, override.category_counts, override.pins, override.disabled_days)


def resolve_targets(
    week: IsoWeek,
    rules: RuleSet,
    first_day: date,
    occupancy: Mapping[SlotRef, SlotContents],
) -> GenerationTargets: ...
    # disabled-day and today-onward exclusion, then per-slot resolution (R9-R15)


def idempotency_key(
    week: IsoWeek, targets: GenerationTargets, rules: RuleSet, mode: GenerationMode
) -> str: ...
    # sha256 over a canonical JSON payload (R16-R19, R25); see gate question 1.
    # mode is included per the human's explicit override of gate question 3
    # (2026-08-26) — see requirements.md's revision note and section 9 below.


def build_plan(
    request: GenerationRequest,
    shared_rules: RuleSet,
    first_day: date,
    occupancy: Mapping[SlotRef, SlotContents],
) -> GenerationPlan: ...
    # composes the three functions above, passing request.mode through to
    # idempotency_key as its fourth argument (R21-R25)
```

**`resolve_targets`'s candidate-slot pass, in order:**

1. `candidate_slots = tuple(s for s in slots_from(week, first_day) if s.day_number not in
   rules.disabled_days)` — today-onward scoping (R10) composes with disabled-day exclusion
   (R9) by filtering the same tuple twice; `slots_from` is reused unchanged, per the brief's
   instruction to reuse feature 2's primitive rather than reinvent it.
2. A `day_by_number` map (`{wd.day_number: wd.day for wd in week.days}`) resolves each
   `PinRule.day` (a weekday `1..7`) to its actual calendar `date` within `week`, then to a
   `SlotRef`. `RuleSet.__post_init__` already guarantees no pin names a disabled day
   (`rules_model` R7), so every resolved pin lands on some slot in `week.slots`; it may still
   land before `first_day` for the current week, in which case it is simply out of scope
   (neither targeted nor reported — the same treatment every other past-day slot gets).
3. For each candidate slot: `occupancy.get(slot, SlotContents())`, then
   `candidate.definitive(plan)`. A definitive present skips the slot from both `open_slots`
   and `pinned_slots` (R11); if a pin also resolves to that slot, it becomes a `SkippedPin`
   (R12). No definitive and a resolved pin becomes a `PinnedTarget` (R13). No definitive and
   no pin becomes an `open_slots` entry regardless of existing candidates (R14) — the read
   that makes "generation adds, never removes" true by construction (`FR-AI-11`, `G-18`):
   there is no code path here that excludes a slot for having candidates, so a future
   candidate-adding step (feature 11/12/17) always still has this slot to add to.
4. `remaining_category_counts` is a second, independent pass over the *whole* `occupancy`
   mapping (not `candidate_slots` — a definitive on a disabled or past day still counts
   toward the week's final state), tallying `definitive.meal.category` per rule, per R15.

**`idempotency_key`'s canonical payload** sorts every collection it serializes
(`slots`, `category_counts`, `pins`, `disabled_days`) before encoding, so two
equal `RuleSet`/`GenerationTargets` values that merely differ in tuple
*order* still hash equal — order is never semantically meaningful in either
type (`rules_model` and `week_plan_model` established this: "set" operations
replace, tuples are sets in spirit). `week.week_id` (already the ISO
week-numbering string `docs/data_model.md` §2 defines) stands in for the
week identity; `targets.open_slots` and `.pinned_slots`' underlying `SlotRef`
values stand in for "slot(s)"; `rules`' three fields stand in for "effective
rules" — `FR-AI-08`'s three named components. `mode.value` (a plain string,
since `GenerationMode` is a `StrEnum`) is hashed as a fourth payload field,
serializing trivially alongside the other three. It is not one of
`FR-AI-08`'s named components — its inclusion is not a re-reading of that
frozen text but an explicit human instruction (`requirements.md`'s revision
note, 2026-08-26; §9 gate question 3 below) that a mode change over an
otherwise-identical week/slots/rules is a deliberate different request, not
a resubmission to dedupe. `skipped_pins` and `remaining_category_counts` are
still **not** hashed: they are consequences of the targets and rules already
in the payload, not independent facts about "the request."

### Exceptions

None. Every function in this module is total over its typed inputs — no
new failure mode is introduced. `RuleSet` and `SlotContents` already raise
their own construction-time exceptions (`rules_model`, `week_plan_model`)
before any value of either type could reach this module.

No function in this feature returns `None` to signal failure
(`docs/architecture.md` §4 invariant 12).

---

## 7. Why `generation.py` is not added to the ASCII shared-kernel guard

`backend/core/tests/test_shared_kernel_guards.py`'s `SHARED_KERNEL_MODULES`
tuple guards modules that declare a closed vocabulary **another feature
would otherwise be tempted to redeclare** — `text.py`'s fold,
`units.py`'s `Unit`, `ingredient_category.py`'s `IngredientCategory`, plus
`recipe.py`. `GenerationMode` is a genuinely new three-member vocabulary
with no existing declaration anywhere in `planner_core` for a second one to
collide with, unlike `IngredientCategory` (which `rules_model` was already
anticipated importing, not redeclaring, before it existed). No feature
downstream of this one (11, 12, 17) has a plausible reason to declare its
own three-mode enum instead of importing this one — there is exactly one
place "library-only / AI-only / mix" is meaningful. The source is written
ASCII-only regardless, just not mechanically enforced, matching
`candidate.py`'s and `rules.py`'s precedent.

---

## 8. Rejected alternatives

**A. Fold occupancy directly into rule-only target resolution instead of
taking `occupancy` as `resolve_targets`'s own parameter (§5, alternative
A).**
Rejected — see §5. Splitting the check across two call sites is exactly
the shape `G-71` describes as the original bug.

**B. Count candidates as well as definitives toward
`remaining_category_counts` (§5, "category-count occupancy").**
Considered, not chosen — see gate question 2. Definitive-only occupancy is
the reading consistent with `docs/architecture.md` §4 invariant 6 and with
`G-71`'s own repeated emphasis on the definitive as "the strongest signal
of intent," but the frozen text itself does not disambiguate the two.

**C. One monolithic `resolve_generation(request, shared_rules, first_day,
occupancy) -> GenerationPlan` instead of four separately callable
functions (`effective_rules`, `resolve_targets`, `idempotency_key`,
`build_plan`).**
Rejected. `rules_model` and `week_plan_model` both favor small, independently
testable pure functions over one entry point — `effective_rules` alone is
what feature 20's confirmation prompt needs to preview the run's rules
before submission ever happens (`FR-AI-05`'s "displaying... the current
general rules"), and collapsing it into a single all-or-nothing function
would force that caller to also supply `first_day` and `occupancy` it does
not yet have, just to see the effective rules.

**D. Represent `pinned_slots` as `tuple[PinRule, ...]` directly, reusing
`rules_model`'s existing type, instead of introducing `PinnedTarget`.**
Rejected. `PinRule.day` is a weekday `1..7`, generic across every week the
shared rules apply to (`rules_model` R2's own "no week identity" guarantee)
— it is not the resolved calendar date within *this* `week`. Reusing
`PinRule` verbatim would force every consumer (feature 11/12/17) to
re-derive that date itself, duplicating step 2 of §6's resolution pass and
risking a second, possibly inconsistent, `day`-to-`date` mapping.
`PinnedTarget` carries the already-resolved `SlotRef` instead.

**E. Resolve "which live week is current" and default `first_day`
internally, via a `Clock` port, instead of taking `first_day` as a plain
`date` (§1).**
Rejected. `docs/architecture.md` §3.1 rule 6 and the human's ruling that
`domain/` functions take a date, never a `Clock`
(`specs/week_calendar/design.md` §9, alternative A) both apply verbatim.
`calendar.slots_from` already establishes the exact pattern this feature
reuses rather than reinvents: a plain `first_day` parameter, with whichever
`application/`-layer feature eventually wires a real submission handler
responsible for reading the clock once and picking `today` (current week)
or `week.monday` (next week, i.e. no restriction) before calling in.

---

## 9. Boundary checks and gate questions

### Boundary checks

- **`docs/architecture.md` §2 (pending, human-owned):** nothing here needs
  P2, P3, P4, P5 or P6. The AI provider (P4) that would actually fill
  `open_slots` is not touched — this feature only names the mode a caller
  should honor.
- **§2.1 decide-in-a-spec items:** none of the three named items (unit
  list, ingredient-category list, servings count) are touched. This
  feature's one concrete proposal — the idempotency key's hash/encoding
  scheme — is not one of the three named items; flagged separately as gate
  question 1.
- **Frozen docs:** none modified. `docs/data_model.md` needs no change
  here: the idempotency key is a domain-level computed string, and its
  eventual persisted form (`idPeticionIA`, per `docs/data_model.md` §2) is
  an adapter-boundary concern for feature 14/17, not decided here.
- **User-facing strings:** none. This feature produces no Castilian text;
  `GenerationMode`'s member names are internal codes, never rendered
  directly (the Castilian labels for the three modes are feature 20's).
- **Runtime dependencies:** none added; `planner-core` keeps
  `dependencies = []`. `hashlib` and `json` are standard library.
- **Requirements invented:** none. Every `R<n>` cites one or more of
  `FR-AI-03`, `FR-AI-05`, `FR-AI-08`, `FR-AI-11` — all four in this
  feature's `covers` array — plus `FR-RULE-05`, an existing frozen id this
  feature consumes but does not own (see `requirements.md`'s scope note).

### Gate questions for the human

1. **The idempotency key's hash and encoding scheme (§6): SHA-256 over a
   canonical JSON payload of `(week.week_id, sorted target slots,
   sorted effective-rules fields)`, hex-digest as the key.** Recommended:
   as designed, since `FR-AI-08` names the mechanism ("a hash of the
   request") but not the algorithm, and SHA-256-over-canonical-JSON is a
   standard, dependency-free (stdlib `hashlib`/`json`) way to make
   "same request twice" and "different request" both provably hold.
   Alternative: a simpler concatenated-string hash, or a non-cryptographic
   hash (e.g. `hash()`, which is not stable across process restarts in
   Python and therefore unsuitable for a key meant to survive a retry from
   a fresh Lambda invocation — ruled out for that reason, not proposed as a
   real alternative). What turns on it: feature 14/17's persisted key
   format and whether it needs to be a fixed-length string (SHA-256 hex is
   always 64 characters).

2. **`remaining_category_counts` counts only slots with a definitive, not
   slots holding only candidates (§5, §8 alternative B).** Recommended:
   definitive-only, per `docs/architecture.md` §4 invariant 6 and `G-71`'s
   own emphasis on the definitive as the signal of intent. Alternative:
   count any slot holding at least one candidate too, on the reading that
   "already planned" (`G-71`'s own phrase) includes an unconfirmed
   proposal. What turns on it: how conservative whole-week generation is
   about a category the household has *proposed* meals for but not yet
   chosen — the definitive-only reading treats that category as still
   fully needed; the candidate-inclusive reading would reduce it early,
   possibly leaving the household short if none of those candidates is
   ever promoted.

3. **Whether the idempotency key should also incorporate `mode` (§6,
   "not hashed" note).** Original recommendation, as first drafted: no —
   `FR-AI-08`'s text names exactly three components ("same week, slot(s),
   and effective rules"), and `mode` is not one of them, so the literal
   reading excludes it. Alternative considered at the time: include it, on
   the reasoning that an `AI_ONLY` submission and a `LIBRARY_ONLY`
   submission over the identical week/slots/rules are not "the same
   request" a user would consider a duplicate, and treating them as such
   under the literal reading could dedupe a resubmission that was actually
   a deliberate mode change.

   **Decided (human override, 2026-08-26): `mode` IS included.** The human
   overturned the "no" recommendation above for exactly the reasoning given
   in the alternative: switching modes over an otherwise-identical
   week/slots/rules is a deliberate, different request, not a duplicate
   resubmission, and must not be silently deduped. `idempotency_key` now
   takes `mode` as a fourth parameter (§6); `requirements.md` `R16` was
   reworded to hold all four inputs constant for its equality guarantee,
   `R24` now passes `request.mode` as the fourth argument, and `R25` is a
   new requirement proving a `mode` change alone changes the key. See
   `requirements.md`'s revision note for the full record. What turns on it:
   two different-mode submissions over otherwise-identical inputs are now
   both allowed to run — neither is suppressed as a duplicate of the other.
