# week_plan_model — Design

> Feature 5 · tier 1 · pure `planner_core.domain`
> Read `requirements.md` first. This document records the technical decisions
> taken before any code is written, per `docs/specs.md`.
> Depends on feature 2 `week_calendar` (closed, `SlotRef`) and feature 4
> `recipe_model` (closed, `MealSnapshot`, `snapshot()`, `Recipe`) — this
> feature **consumes** both and re-derives neither.

## 0. The invariants this feature exists to protect

`docs/architecture.md` §4:

> **11. Content freezes only at archival.** A definitive meal stays editable
> like any candidate until its week is archived. (`FR-CAND-05`, `G-67`)

> **9. Removed users leave their content behind**, reattributed to a reserved
> "unknown user" placeholder. Never cascade-delete authored content.
> (`FR-AUTH-13`, `FR-SUM-03`, `G-29`, `G-58`)

> **3. Warn, do not block, on duplicates.** Same-name candidate in a slot
> (`G-59`), same-name library recipe (`G-26`).

Every operation below is subordinate to these three sentences: promotion never
copies or freezes content (§5), a candidate's existence never depends on
whether its author still exists (§6), and a duplicate name is surfaced, never
rejected (§4, §7).

---

## 1. Scope boundary — what this feature owns of each `FR-*`

See `requirements.md`'s scope-note table for the full per-requirement split.
Two lines deserve emphasis because they are easy to get wrong:

**`FR-SUM-01`'s "read-only … cannot be edited from this view" clause is not
implemented here.** This feature owns only *which meals appear* in a summary
— exactly the definitives (R21). Enforcing that the summary view offers no
edit controls is a UI concern, feature 20's.

**`FR-AUTH-13`'s library-recipe clause is not implemented here.** The frozen
text names two content types: "candidate meals, library recipes." `Recipe`
(feature 4, closed) carries no author field — `FR-LIB-01`/`FR-LIB-02` are not
in this feature's `covers` array, and no feature has assigned `Recipe` an
author yet. This spec claims only the candidate-authorship half (R24).
Retrofitting `Recipe` is flagged as gate question 3, not done silently.

**The reusable artefact this feature adds.** `Candidate`, `SlotContents`, and
the operations that construct and transform them. No later tier-1 feature in
this backlog needs to redeclare `Candidate` or `SlotContents` — feature 7
(`shopping_aggregation`) consumes only `MealSnapshot`s already promoted to
definitive (via `definitive(plan)`), not the candidate machinery itself.

---

## 2. Layering

`docs/architecture.md` §3: `domain/` is *"Pure logic. No IO, no AWS SDK, no
framework, no clock."* Every function below is a pure transformation of plain
values — no port, no clock, no id generator, no IO.

| Piece | Layer | Why |
|---|---|---|
| `Candidate`, `SlotContents`, `AddCandidateResult`, `LibraryEntryResult`, `CandidateNotFound`, `UNKNOWN_USER_ID`, and every function in §6 | `planner_core/domain/candidate.py` | Pure value objects and pure functions between them; no IO, no ambient state. |

No `application/` piece. Unlike feature 2 (`week_calendar`), nothing here
needs "now" — a candidate's `id` and `author` are supplied by the caller, not
read from a port (§8, rejected alternative B). This feature is, if anything,
*more* architecture-independent than feature 2: its tests need no fake at
all, not even a fixed clock.

---

## 3. Files

### Created

| Path | Contents |
|---|---|
| `backend/core/src/planner_core/domain/candidate.py` | `Candidate`, `SlotContents`, `AddCandidateResult`, `LibraryEntryResult`, `CandidateNotFound`, `UNKNOWN_USER_ID`, `new_candidate`, `definitive`, `add_candidate`, `edit_candidate`, `remove_candidate`, `promote`, `clear_definitive`, `summary`, `to_library_entry`, `resolve_author`. |
| `backend/core/tests/domain/test_candidate.py` | R1–R24. |

### Modified

None. This feature declares no second vocabulary (no enum, no closed set),
so `backend/core/tests/test_shared_kernel_guards.py` needs no new scan — see
§7 for why `candidate.py` is deliberately **not** added to that module's
`SHARED_KERNEL_MODULES` tuple. No `pyproject.toml` change: no dependency
added, `planner-core` keeps `dependencies = []`.

---

## 4. `docs/architecture.md` §2.1 items

None of the three named items (unit list, ingredient-category list, servings
count) are touched here — all three belong to features 3, 4/6 and 11
respectively. This feature proposes exactly one concrete value of its own,
`UNKNOWN_USER_ID` (§6), flagged as gate question 1 since it is not one of the
three items §2.1 names explicitly.

---

## 5. Definitive as a pointer, not a flag — why `edit_candidate` needs no special case

`FR-MENU-03` reads *"a list of candidate meals and at most one definitive
meal,"* and `G-67` requires that promoting never copies or freezes content.
Two shapes could satisfy the first sentence:

**A. A boolean on each `Candidate`** (`is_definitive: bool`), policed by hand
to stay at most one `True` across the tuple. Every promote rebuilds the whole
tuple, flipping one element's flag and clearing any other. Every edit that
happens to target the definitive one must *also* remember to preserve the
flag. Two independent pieces of code (`promote`, `edit_candidate`) both have
to get the invariant right.

**B. A single `definitive_id: str | None` on `SlotContents`** (chosen here).
"At most one definitive" is now a fact of the type itself — one field, not a
per-element convention. `promote` writes one field. `edit_candidate` never
touches `definitive_id` at all: it replaces the matching tuple element by
`id`, and `definitive(plan)` re-resolves the pointer against the *current*
`candidates` tuple on every call. R14 (`G-67`'s propagation guarantee) is
therefore not a code path to write — it is a consequence of `definitive`
being a lookup, not a cache. This is the same reasoning `week_calendar` used
for `LiveWeeks` deriving the current/next split from `today` on every call
rather than storing a "which week is current" flag (`docs/architecture.md`
§4 invariant 7's data-model note).

R2's `__post_init__` check exists because option B trades "can't express two
definitives" for "can express a definitive that points at nothing" — a
dangling pointer is now the one way this shape can go wrong, so it is the one
thing validated at construction, mirroring `IsoWeek.__post_init__`
(`specs/week_calendar/design.md` §4) validating the one way *its* shape can
be wrong.

**R17's silent clear on removal is the same principle applied to a state
transition instead of a constructor.** `remove_candidate` cannot leave
`definitive_id` dangling either, so it clears it rather than raising — see
§8, rejected alternative D, for why raising was considered and rejected.

---

## 6. Signatures

```python
"""Slot contents: candidates, at most one definitive, and author attribution."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from typing import Final

from planner_core.domain.calendar import SlotRef
from planner_core.domain.errors import PlannerError
from planner_core.domain.recipe import MealSnapshot, Recipe
from planner_core.domain.text import normalize


UNKNOWN_USER_ID: Final[str] = "unknown-user"


class CandidateNotFound(PlannerError):
    """Raised when an operation targets a candidate id absent from the slot."""

    candidate_id: str

    def __init__(self, candidate_id: str) -> None:
        super().__init__(candidate_id)
        self.candidate_id = candidate_id


@dataclass(frozen=True)
class Candidate:
    id: str
    meal: MealSnapshot
    author: str


@dataclass(frozen=True)
class SlotContents:
    candidates: tuple[Candidate, ...] = ()
    definitive_id: str | None = None

    def __post_init__(self) -> None: ...   # raises CandidateNotFound, R2


@dataclass(frozen=True)
class AddCandidateResult:
    plan: SlotContents
    duplicate_warning: bool


@dataclass(frozen=True)
class LibraryEntryResult:
    recipe: Recipe
    duplicate_warning: bool


def new_candidate(id: str, meal: MealSnapshot, author: str) -> Candidate: ...

def definitive(plan: SlotContents) -> Candidate | None: ...

def add_candidate(plan: SlotContents, candidate: Candidate) -> AddCandidateResult: ...

def edit_candidate(plan: SlotContents, candidate_id: str, meal: MealSnapshot) -> SlotContents: ...
    # raises CandidateNotFound

def remove_candidate(plan: SlotContents, candidate_id: str) -> SlotContents: ...
    # raises CandidateNotFound; clears definitive_id if it pointed at candidate_id (R17)

def promote(plan: SlotContents, candidate_id: str) -> SlotContents: ...
    # raises CandidateNotFound

def clear_definitive(plan: SlotContents) -> SlotContents: ...

def summary(plans: Mapping[SlotRef, SlotContents]) -> tuple[tuple[SlotRef, Candidate], ...]: ...

def to_library_entry(meal: MealSnapshot, existing_names: Iterable[str]) -> LibraryEntryResult: ...

def resolve_author(author_id: str, known_user_ids: AbstractSet[str]) -> str: ...
```

**Corrected 2026-08-24 (`F6` of `progress/review_week_plan_model.md`).** This
block first read `from collections.abc import AbstractSet, ...`, which does not
merely fail `mypy --strict` — it raises `ImportError`. `collections.abc` has no
`AbstractSet`; the name there is `Set`, and `typing.AbstractSet` is its
deprecated PEP 585 alias. The alias import above is the stdlib-consumer idiom,
chosen so bare `Set` is never mistaken for the builtin `set` at a call site and
so the annotation still reads exactly `known_user_ids: AbstractSet[str]`, which
is the text `R22` and `R23` specify.

**`candidates` and `definitive_id` both default** (`()`, `None`) so a new,
empty slot is `SlotContents()`. Immutable defaults on a frozen dataclass need
no `default_factory` — `()` is not a mutable default the way `[]` would be.

**`edit_candidate` rebuilds `candidates` preserving position**: the matching
element is replaced in place (`tuple(new if c.id == candidate_id else c for c
in plan.candidates)`), not removed-then-appended, so a slot's display order
survives an edit.

**`resolve_author`'s idempotence is a consequence, not a special case.**
`UNKNOWN_USER_ID` is deliberately never a member of any realistic
`known_user_ids` set, so `resolve_author(UNKNOWN_USER_ID, known_user_ids)`
returns `UNKNOWN_USER_ID` unchanged — resolving an already-resolved
attribution is a no-op by construction, matching `docs/architecture.md` §4
invariant 5's "compound operations converge" spirit, though this function is
not itself one of the compound operations that invariant names.

**`resolve_author` never mutates `Candidate.author`.** `docs/data_model.md`
line 376 states the persisted `añadidoPor` is "resolved against the user
list" at render time, never rewritten — `resolve_author` is exactly that
render-time computation, kept pure so no caller is tempted to write its
result back onto the candidate.

### Exceptions

| Exception | Base | Raised when |
|---|---|---|
| `CandidateNotFound` | `PlannerError` | `SlotContents.__post_init__` is given a dangling `definitive_id` (R2); `edit_candidate`/`remove_candidate`/`promote` are given a `candidate_id` absent from `plan.candidates` (R11, R13). |

No function in this feature returns `None` to signal failure
(`docs/architecture.md` §4 invariant 12); `definitive(plan)` returning `None`
is a genuine answer ("no definitive yet"), not an error signal.

---

## 7. Why `candidate.py` is not added to the ASCII shared-kernel guard

`backend/core/tests/test_shared_kernel_guards.py`'s `SHARED_KERNEL_MODULES`
tuple exists to guard modules that declare a **closed vocabulary** other
features must reuse rather than redeclare (`text.py`'s fold, `units.py`'s
enum, `ingredient_category.py`'s enum) plus `recipe.py`, extended alongside
them in feature 4. `candidate.py` declares no enum and no vocabulary — it
*consumes* `normalize()` from `text.py` but restates none of its rules
(`docs/gaps_and_resolutions.md` instruction in this feature's brief). Nothing
about `candidate.py` risks a second, drifting vocabulary the way a second
`IngredientCategory` would, so extending the guard's asserted set would test
nothing beyond "this file has no accented characters" — true by writing it in
English, and not worth a mechanical guard on its own. The source is written
ASCII-only regardless (no em dash, no accented character), just not
mechanically enforced.

---

## 8. Rejected alternatives

**A. A boolean `is_definitive` flag on `Candidate` instead of a pointer on
`SlotContents`.**
Rejected — see §5. It splits "at most one definitive" across every element
of a tuple instead of stating it once, and makes `G-67`'s propagation
guarantee something `edit_candidate` must remember rather than something
`definitive()` derives for free.

**B. Generate `Candidate.id` inside `new_candidate` (e.g. `uuid4()`).**
Rejected. The human's ruling that domain functions take a date, never a
`Clock` (`docs/architecture.md` §3.1 rule 6, `specs/week_calendar/design.md`
§9 alternative A) is about the same underlying problem by analogy: a domain
function reaching for ambient, non-deterministic state instead of taking a
value. `docs/architecture.md` §3's repository layout anticipates an `ids`
port family (*"Interfaces (typing.Protocol): persistence, ai, clock,
ids"*), but no feature in this backlog has built it yet, and none of the ten
`FR-*` ids this feature covers mandates a generation *mechanism* — only that
each candidate be individually addressable. Building the port's shape now
would be inventing an interface no covered requirement asks for. `id` stays
caller-supplied, flagged as gate question 2.

**C. Track "author was removed" with a `removed: bool` flag on `Candidate`,
set by whatever process removes a user.**
Rejected. This is the same shape `docs/architecture.md` §4 invariant 2 warns
against generalizing: a flag that "needs an attribute recording state at a
past moment," which now has to be kept in sync by a second piece of code
(the removal action, feature 15, not yet built) or it silently goes stale. A
pure `resolve_author(author_id, known_user_ids)` computed against the
*current* known-user set at call time needs no stored state and cannot go
stale, mirroring `LiveWeeks` recomputing "which week is current" from `today`
every time rather than caching it.

**D. Have `remove_candidate` raise instead of silently clearing
`definitive_id` when removing the current definitive.**
Considered, not chosen — see gate question 4. The chosen behavior applies the
same "a dangling reference resolves to absent rather than corrupting the
invariant" principle `docs/data_model.md` §5's read-time resolution already
applies at the persistence layer (`docs/architecture.md` §1.2.1), generalized
to this value-object layer. Raising instead would need a two-step
UI confirmation flow no `FR-*` in this feature's `covers` array requires —
`FR-UX-04`'s destructive-action confirmation is feature 20's, not invented
here.

**E. Retrofit an `author` field onto `Recipe` (feature 4) so
`to_library_entry` can carry authorship, closing `FR-AUTH-13`'s
library-recipe clause too.**
Rejected as invention. `FR-LIB-03`, `FR-LIB-05`, `FR-CAND-07` and
`FR-MENU-04` — feature 4's entire `covers` array — say nothing about
authorship, and `FR-LIB-01`/`FR-LIB-02` (which do) are not in *this*
feature's `covers` array either. Modifying an already-closed feature's frozen
dataclass shape from inside a different feature's spec is exactly the
boundary `docs/specs.md` exists to prevent blurring. Flagged as gate
question 3 instead of silently done.

**F. Give `SlotContents` its own `SlotRef` field instead of keying it
externally in `summary()`'s `Mapping[SlotRef, SlotContents]`.**
Rejected. `SlotRef` (feature 2) already carries day+slot identity in full;
duplicating it onto `SlotContents` would let the two disagree (a
`SlotContents` claiming to belong to Tuesday lunch while stored under
Wednesday dinner's key) with nothing to catch the mismatch. Keeping
`SlotContents` a plain value describing only its own contents — no key,
no id of its own — mirrors `recipe_model`'s rejected alternative D
(`MealSnapshot` carries no persistence identity either).

---

## 9. Boundary checks and gate questions

### Boundary checks

- **`docs/architecture.md` §2 (pending, human-owned):** nothing here needs
  P2, P3, P4, P5 or P6. `FR-SUM-03`'s "known user ids" and `FR-AUTH-13`'s
  removal action both stay outside this feature precisely because they touch
  P2 (auth mechanism) through feature 15 — this feature only defines the pure
  function that *would* consume that data once it exists.
- **§2.1 decide-in-a-spec items:** none of the three named items are touched
  (§4). `UNKNOWN_USER_ID` is a fourth, feature-local proposal, not one of the
  three — flagged as gate question 1 rather than assumed authorized by §2.1.
- **Frozen docs:** none modified. `docs/data_model.md` needs no change here —
  `Candidate.id`/`author` are domain-level opaque strings, not a persistence
  key format; `idPlato`/`añadidoPor`'s actual formats stay `docs/data_model.md`
  §2's, assigned at the adapter boundary (`specs/recipe_model/design.md` §8,
  rejected alternative D, same reasoning extended here).
- **User-facing strings:** none. This feature produces no Castilian text;
  `UNKNOWN_USER_ID` is an internal sentinel, never rendered directly.
- **Runtime dependencies:** none added; `planner-core` keeps
  `dependencies = []`.
- **Requirements invented:** none. Every `R<n>` cites one or more of
  `FR-MENU-03`, `FR-CAND-01`, `FR-CAND-02`, `FR-CAND-04`, `FR-CAND-05`,
  `FR-CAND-06`, `FR-CAND-08`, `FR-SUM-01`, `FR-SUM-03`, `FR-AUTH-13` — all ten
  in this feature's `covers` array, no others (in particular, never
  `FR-CAND-07`, which is feature 4's, already closed).

### Gate questions for the human

> **All four approved as recommended by the human on 2026-08-24.** Question 1
> carries an extra ruling: the feature 15 placeholder account's `idUsuario` is
> meant to be **exactly** this literal, `unknown-user`. That is now pinned in
> `docs/data_model.md` §5.1 so feature 15 cannot choose independently.

1. **The `UNKNOWN_USER_ID` sentinel value (§6).** Recommended: an internal
   domain-level constant, `"unknown-user"`, used only for the `resolve_author`
   comparison — never persisted, never rendered directly (the Castilian label
   is feature 20's). Alternative: if the eventual real placeholder account
   (feature 15, seeded per `docs/data_model.md` line 299) is meant to carry
   this exact literal as its `idUsuario`, say so now so feature 15 does not
   pick an incompatible one independently. Otherwise this value is purely
   internal to this feature and callers pass whatever `known_user_ids` they
   have — the sentinel is only ever compared, never looked up.

2. **`Candidate.id` and `Candidate.author` are caller-supplied opaque
   strings; this feature builds no id-generation mechanism (§8, rejected
   alternative B).** Recommended: keep it this way, extending the
   date-not-`Clock` ruling to ids by analogy. Alternative: scaffold an `Ids`
   port now (`planner_core/ports/ids.py`) so id generation has one owner from
   the start rather than being reinvented independently by whichever feature
   first needs it. What turns on it: whether the human wants that port's
   shape decided now, ahead of any feature that actually needs it, or left
   for whichever feature turns out to need it first.

3. **Library-recipe authorship (`FR-LIB-01`/`FR-LIB-02`) is out of this
   feature's scope; `Recipe` still carries no author field (§1, §8 rejected
   alternative E).** Recommended: leave it to whichever feature implements
   `FR-LIB-01`/`FR-LIB-02` (currently feature 20, blocked) to decide whether
   `Recipe` gains an author field or whether library authorship is tracked
   only at the persistence layer's `añadidoPor` attribute with no domain
   counterpart. Alternative: retrofit `Recipe` now, in this feature, since
   `FR-AUTH-13`'s text also names "library recipes" among reattributed
   content. What turns on it: doing so would modify feature 4's closed
   dataclass shape from outside its own `covers` array.

4. **`remove_candidate` on the current definitive silently clears
   `definitive_id` rather than raising (§5, §8 rejected alternative D).**
   Recommended: silent clear, matching the read-time dangling-reference
   resolution `docs/architecture.md` §1.2.1 already applies at the
   persistence layer. Alternative: raise, forcing the caller to
   `clear_definitive` first — giving feature 20 a hook to ask "this is the
   chosen meal, remove it anyway?" (`FR-UX-04`'s confirmation pattern) before
   the removal happens rather than after. What turns on it: this is a
   domain-level default that feature 20's UI will have to code against
   either way, so it needs picking now rather than being discovered mid-UI.
