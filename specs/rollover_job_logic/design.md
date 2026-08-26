# rollover_job_logic — Design

> Feature 13 · tier 1 · pure `planner_core.domain`
> Read `requirements.md` first. This document records the technical decisions
> taken before any code is written, per `docs/specs.md`.
> Depends on feature 2 `week_calendar` (closed: `IsoWeek`, `SlotRef`), feature
> 5 `week_plan_model` (closed: `SlotContents`) and feature 8
> `shopping_list_state` (closed: `ShoppingItem`, `unchecked_items`,
> `checked_items`). Adds no field to any of the three.

## 0. The invariant this feature exists to protect

`docs/gaps_and_resolutions.md`, `G-61`:

> Rollover is an atomic, idempotent, re-runnable job: retrying after partial
> failure completes the remaining steps without data loss, double-archiving,
> or double-cleanup.

and `G-73` (supersedes `G-53`, the current rule for `FR-SHOP-09`):

> At rollover the list is cleared of every checked item, with no requirement
> test... The check state already carries the meaning the week attribution
> was reconstructing.

Every function below is subordinate to both: `roll_over` never partially
mutates anything (it is a single pure call that either returns one complete
`RolloverResult` or does not return at all), and its cleanup step never
consults which week a checked item was "for" — there is no such attribute to
consult (`G-73` deliberately removed it), so the unconditional-ness of
`FR-SHOP-09` is structural, not a branch that could be gotten wrong.

---

## 1. Scope boundary — what this feature owns

**This feature has no IO, no scheduling, and no persistence.** It is the pure
transition function a future scheduled job (persistence-layer, not yet built)
would call once per rollover, handed the two live weeks' plans and the
current shopping list, and would use to compute the complete post-rollover
state to write.

| Concern | Lives in |
|---|---|
| Deciding *when* a rollover is due (comparing `IsoWeek.containing(today)` against the persisted current week) | A future application-layer use case (feature 14+, `persistence_ports` and beyond) — this feature takes the two weeks' identities and plans as already-resolved arguments, the same "plain values, not an ambient clock" discipline `docs/specs.md`'s own worked example enforces for `Clock` (see section 6, rejected alternative B). |
| Persisting `RolloverResult` — writing the archive, overwriting the live current/next plans, overwriting the shopping list | An adapter (feature 14+). Nothing here imports a port or touches `boto3`. |
| Retrieving an archived week later, browsing past weeks (`FR-ARCH-03`, `FR-ARCH-04`) | Out of this feature's `covers`; a read-side concern for a later feature once persistence exists. |
| Concurrency / serialization of the rollover job itself (two schedule triggers firing close together) | Not named by any `FR-*` this feature covers, and — like `FR-SHOP-10`'s serialization clause, deferred the same way in `specs/shopping_list_state/design.md` section 1 — needs a real lock or conditional write, which needs a real persistence port. Deferred to feature 14+. |

---

## 2. Layering

`docs/architecture.md` section 3: `domain/` is *"Pure logic. No IO, no AWS
SDK, no framework, no clock."* Every piece below is a plain value or a pure
function between plain values.

| Piece | Layer | Why |
|---|---|---|
| `ArchivedWeek`, `RolloverResult`, `archive_week`, `promote_next_to_current`, `init_empty_next_week`, `roll_over` | `planner_core/domain/rollover.py` | Pure value objects and pure functions; no IO, no ambient state, no clock, no port import. |

No `application/` piece: exactly like `ai_prompt_builder` and
`shopping_list_state`, every input here is caller-supplied, and no use case
orchestrating a real clock or a real persistence port exists yet.

---

## 3. Files

### Created

| Path | Contents |
|---|---|
| `backend/core/src/planner_core/domain/rollover.py` | `ArchivedWeek`, `RolloverResult`, `archive_week`, `promote_next_to_current`, `init_empty_next_week`, `roll_over`. |
| `backend/core/tests/domain/test_rollover.py` | R1–R13. |

### Modified

None. No new user-facing string, no new exception, no change to
`shopping.py`, `candidate.py` or `calendar.py` — this feature composes their
existing exports.

No `pyproject.toml` change: no dependency added. `rollover.py` imports only
`dataclasses`, `collections.abc` (stdlib) and sibling `planner_core.domain`
modules — `planner-core` keeps `dependencies = []`.

---

## 4. Signatures

```python
"""The week-rollover transition: archive the ending week, promote next to
current, initialize an empty next week, and clean bought shopping items —
composed as one pure, deterministic function (FR-MENU-06, FR-MENU-08, G-61)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from planner_core.domain.calendar import IsoWeek, SlotRef
from planner_core.domain.candidate import SlotContents
from planner_core.domain.shopping import ShoppingItem, unchecked_items


@dataclass(frozen=True)
class ArchivedWeek:
    """A closed week's full record: its menu and the shopping list as it
    stood before rollover cleanup (FR-ARCH-01, FR-ARCH-02). Frozen — no
    function in this module mutates one once built (R2)."""

    week: IsoWeek
    plans: Mapping[SlotRef, SlotContents]
    shopping_snapshot: tuple[ShoppingItem, ...]


@dataclass(frozen=True)
class RolloverResult:
    """The complete post-rollover state, produced by one call (FR-MENU-08)."""

    archived: ArchivedWeek
    new_current_plans: Mapping[SlotRef, SlotContents]
    new_next_plans: Mapping[SlotRef, SlotContents]
    shopping_items: tuple[ShoppingItem, ...]


def archive_week(
    week: IsoWeek,
    plans: Mapping[SlotRef, SlotContents],
    shopping_items: tuple[ShoppingItem, ...],
) -> ArchivedWeek:
    """Steps 1+2: snapshot the ending week's menu and the list, before
    cleanup (R1, R4, R5, R6; see section 6, rejected alternative D, on why
    these two collapse)."""
    return ArchivedWeek(week=week, plans=plans, shopping_snapshot=shopping_items)


def promote_next_to_current(
    next_plans: Mapping[SlotRef, SlotContents],
) -> Mapping[SlotRef, SlotContents]:
    """Step 3: the former next week's plans become the new current week's,
    unchanged (R7, G-28)."""
    return next_plans


def init_empty_next_week() -> Mapping[SlotRef, SlotContents]:
    """Step 4: a fresh next week starts with no slots. Zero parameters, so no
    rule or generation input has anywhere to enter (R8, R10, G-15)."""
    return {}


def roll_over(
    former_current_week: IsoWeek,
    former_current_plans: Mapping[SlotRef, SlotContents],
    former_next_plans: Mapping[SlotRef, SlotContents],
    shopping_items: tuple[ShoppingItem, ...],
) -> RolloverResult:
    """The five-step transition, composed in order (FR-MENU-06, G-61).

    Total and deterministic: same arguments always return an equal result
    (R13); this is FR-MENU-08's retry-safety basis (section 5).
    """
    archived = archive_week(former_current_week, former_current_plans, shopping_items)
    new_current_plans = promote_next_to_current(former_next_plans)
    new_next_plans = init_empty_next_week()
    cleaned_items = unchecked_items(shopping_items)
    return RolloverResult(
        archived=archived,
        new_current_plans=new_current_plans,
        new_next_plans=new_next_plans,
        shopping_items=cleaned_items,
    )
```

---

## 5. What "idempotent, re-runnable after interruption" means for a pure function with no IO

`FR-MENU-08` (and `G-61`) describe rollover as a five-step *job* whose steps
can fail partway, and requires that retrying after a partial failure not
double-archive, double-clean, or lose data. Read literally, that presumes a
process that can crash **between** steps — which presumes something durable
was already written by an earlier step and something else was not yet
written by a later one. `domain/` has no IO (`docs/architecture.md` section
3): nothing in this module ever writes anything, so nothing in this module
can be interrupted mid-write. `roll_over` either runs to completion and
returns one complete `RolloverResult`, or an exception propagates and nothing
it would have returned ever exists anywhere — there is no partial value to
leak, by construction (`docs/architecture.md` section 4, invariant 12: no
function returns a partial result and calls it done).

**What this feature can and does prove instead:** every one of the four
pieces `roll_over` composes is a *pure, deterministic function of its own
arguments* — R11 (`archive_week`, `promote_next_to_current`,
`init_empty_next_week`) and R12 (cleanup, i.e. `unchecked_items`) prove this
individually; R13 proves it for the composed whole. This is the same
discipline `docs/architecture.md` section 4 invariant 5 already states for
this exact requirement — *"Compound operations are idempotent... Recompute-
from-source beats diff-and-patch"* — and the same technique
`shopping_list_state` used for `FR-SHOP-10`'s idempotence (`resync` recomputes
from `required`, R17 in that spec) and `shopping_aggregation` used for its own
determinism claims. The payoff for the **eventual** persistence-layer caller
(feature 14+, not built yet) is real: because `roll_over` is total and
deterministic, a caller that crashes after calling it but before finishing
its writes can simply call it again with the **same** pre-rollover arguments
and get the identical `RolloverResult` back — so its writes (an archive put,
a plans overwrite, a shopping-list overwrite) are naturally safe to retry as
**idempotent overwrites**, not appends. R12 sharpens this for cleanup
specifically: cleaning an already-cleaned list is a no-op, so even a
half-finished retry of just that one step cannot lose or duplicate anything
further.

**What this feature does *not* prove, and cannot prove without IO:** that a
specific sequence of *persisted* writes, interleaved with an actual crash at
an actual byte offset, converges — that is an adapter/use-case property,
tested against a real or fake persistence port, not a pure function's. See
the gate question in section 7.

---

## 6. Rejected alternatives

**A. A persisted step-cursor (e.g. `RolloverCursor` enum plus a stored index
of which of the five steps last completed) so a retry could resume from where
it left off.** Rejected. Tracking "which step already ran" is inherently a
piece of durable state that must survive a crash to be useful — that is IO,
and `domain/` has none (`docs/architecture.md` section 3, section 3.1 rule
1). Building it here would smuggle a persistence concern into the one layer
this project keeps IO-free by design; it belongs, if it is ever needed at
all, to the application/persistence layer that has an actual store to put a
cursor in (feature 14+).

**B. Injecting a `Clock` (or a callable id/timestamp generator) into
`roll_over` so `ArchivedWeek` could carry when the archive was created.** No
`FR-*` this feature covers asks for a timestamp on `ArchivedWeek`, and a
callable domain could invoke ambiently is exactly the shape `docs/specs.md`'s
own worked example rejected for `Clock`: *"domain functions take a plain
date, never a Clock."* `roll_over` takes only already-resolved plain values.

**C. A new `clean_bought_items` function in `rollover.py`, reimplementing
"keep only unchecked items," instead of calling `shopping.unchecked_items`
directly.** Rejected. `unchecked_items` (feature 8, closed) already *is*
exactly this filter — "items not yet bought, in list order." `FR-SHOP-09`'s
cleanup step is definitionally identical to it: drop every checked item,
keep every unchecked one, unconditionally. A wrapper would duplicate logic
that already has its own tests and risk drifting from feature 8's behavior
if either were changed independently later.

**D. Splitting "archive the week" and "snapshot the shopping list" into two
separate functions, mirroring the acceptance bullet's five discrete-sounding
steps literally.** Rejected. The snapshot's entire content is "whatever
`shopping_items` was passed in" — the exact same value `archive_week` already
receives to build `ArchivedWeek.shopping_snapshot`. A second function would
be a pass-through with no independently testable behavior beyond what R6
already proves; the ordering guarantee that actually matters (snapshot
happens *before* cleanup) is proven by R6 and R9 reading two different fields
of one `RolloverResult`, not by how many functions compute them.

**E. `RolloverResult` carrying the new current/next weeks' `IsoWeek`
identities as fields, alongside their plans.** Rejected. `IsoWeek.containing`
and `following` (`calendar.py`, feature 2, closed) already let any caller
derive both identities from `today` without this feature repeating that
computation, and this feature's own inputs (`former_current_week`,
`former_next_plans`) never need the *new* current/next weeks' identities to
do their work — only their plans. Adding the fields would duplicate
`calendar.py`'s job for no behavioral gain.

---

## 7. Boundary checks and gate questions

### Boundary checks

- **`docs/architecture.md` section 2 (pending, human-owned):** nothing here
  needs P2, P3, P4, P5 or P6. This feature is pure `domain/`, no port, no
  adapter, no Lambda, no scheduling.
- **section 2.1 decide-in-a-spec items:** none touched. No unit, category or
  servings value enters this feature.
- **Frozen docs:** none modified.
- **`ShoppingItem`/`SlotContents`/`IsoWeek`/`SlotRef` (shared kernel):**
  unchanged. No field added to any of them.
- **User-facing strings:** none. No new exception carries a message; the one
  raised condition (`FrozenInstanceError`, R2) is a stdlib exception from
  attempting to mutate a frozen dataclass, not a domain-raised error.
- **Runtime dependencies:** none added.
- **Requirements invented:** none. Every `R<n>` cites `FR-MENU-06`,
  `FR-MENU-08`, `FR-ARCH-01`, `FR-ARCH-02` or `FR-SHOP-09` — all five in this
  feature's `covers` array. No id outside it is cited.

### Gate questions for the human

1. **Section 5's interpretation of `FR-MENU-08`'s "safely retryable after a
   partial failure" as "every step, and the whole function, is a pure
   deterministic recompute" — rather than literal crash-between-steps
   simulation — is this accepted for this tier?** Grounding:
   `docs/architecture.md` section 3 (`domain/` has no IO to be interrupted
   mid-write) and section 4 invariant 5 (recompute-from-source is this
   project's standing answer to "idempotent"), plus the identical treatment
   `shopping_list_state` gave `FR-SHOP-10`'s "serialized" clause (deferred to
   feature 14+, not built here). Recommendation: accept it at this tier, on
   the understanding that a **fuller** test — an actual persisted write
   interrupted and retried — belongs to whichever feature 14+ persistence
   feature first gives `roll_over` a real caller with real IO to interrupt.
   If the human disagrees, this feature is blocked on inventing
   crash-recovery machinery `docs/architecture.md` section 3 does not permit
   inside `core` — there is no smaller fix available at this tier.

2. **`RolloverResult` exposes `new_current_plans` / `new_next_plans` as plain
   `Mapping` values with no attached `IsoWeek`, per rejected alternative E.**
   Recommendation: keep it that way — the caller already has
   `IsoWeek.following`. Alternative: add the two `IsoWeek` fields anyway, for
   a caller-convenience reason no `FR-*` states. What turns on it: whether a
   future feature-14+ caller derives the new weeks' identities itself (one
   extra `IsoWeek.containing(today).following()` call) or reads them off this
   result directly.
