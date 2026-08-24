# week_plan_model — Requirements

> Feature 5 · tier 1 · `sdd: true`
> Covers: `FR-MENU-03`, `FR-CAND-01`, `FR-CAND-02`, `FR-CAND-04`, `FR-CAND-05`,
> `FR-CAND-06`, `FR-CAND-08`, `FR-SUM-01`, `FR-SUM-03`, `FR-AUTH-13`
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen
> requirement ids it implements and is verifiable by at least one concrete test
> that asserts a value.

## Purpose in one sentence

Give a meal slot its contents — a list of candidates plus at most one
definitive, each candidate carrying an immutable author — and the pure
operations that add, edit, remove, promote, clear, summarize and
attribution-resolve them, all built around the `MealSnapshot` feature 4
already shipped (`specs/recipe_model/design.md` §5).

## One `SHALL` per requirement

Every `R<n>` below carries exactly one `SHALL` or one `SHALL NOT`, counted
mechanically rather than by eye, per the checklist in `AGENTS.md` /
`docs/specs.md` and the four combined requirements recorded as an accepted
deviation in `specs/week_calendar/requirements.md`.

## Scope note on the ten covered requirements

Several of the ten ids in `covers` are UI-facing or straddle a feature not yet
built. This spec claims only the half each one names below; the rest belongs
elsewhere and is not implemented here.

| Requirement | Owned **here** | Deferred to |
|---|---|---|
| `FR-MENU-03` | The slot-contents shape: a list of candidates, at most one definitive, and the invariant that the definitive always names a real candidate. | Which slot a `SlotContents` belongs to (day/week identity) — **feature 2 `week_calendar`**'s `SlotRef`, reused, not re-derived. |
| `FR-CAND-01` | Add/edit/remove as individual pure operations on `SlotContents`, and the duplicate-name warning on add. | The UI form and its buttons — **feature 20**. |
| `FR-CAND-02` | The single construction path (`new_candidate`) every authoring source lands on. | The choice **of** authoring method (library pick / from scratch / AI) and the AI preview lifecycle itself — **feature 20** (UI) and **feature 12** (`ai_output_validation`, AI preview accept/discard). |
| `FR-CAND-04` | The `author` field on `Candidate`, set once at construction and immutable through every other operation. | Displaying the author string, and rendering "other users' candidates" — **feature 20**. |
| `FR-CAND-05` | Promote/replace semantics, and the guarantee that editing the current definitive is the same operation as editing any candidate (`G-67`). | The promote UI control — **feature 20**. |
| `FR-CAND-06` | Constructing a new library `Recipe` from a candidate's snapshot, and the same-name collision warning, both as one pure function. | The "add to library" UI action and the actual write to the library repository — **feature 20** and **feature 14** (`persistence_ports`). Library-recipe *authorship* (`FR-LIB-01`, `FR-LIB-02`) is untouched here — see `design.md` §1 and rejected alternative E. |
| `FR-CAND-08` | Clearing the definitive, leaving candidates unchanged. | The clear-selection UI control — **feature 20**. |
| `FR-SUM-01` | Which entries belong in a week's summary — exactly the slots holding a definitive, paired with that definitive. | The read-only view itself and its edit-prevention — **feature 20**. |
| `FR-SUM-03` | The pure resolution rule: an author id absent from a caller-supplied known-user set resolves to the reserved placeholder. | Populating the known-user set from real account data (needs an account/removal model — **feature 15 `auth_flow`**, blocked on `P2`) and rendering the placeholder label in Castilian — **feature 20**. |
| `FR-AUTH-13` | The candidate-authorship half only: a candidate is never removed or excluded from a `SlotContents` because its author is unknown. | The admin removal action itself, session invalidation, and library-recipe reattribution — **feature 15**, out of scope here (see scope note above on `FR-CAND-06`). |

---

## R1
Implements: FR-MENU-03

The system SHALL declare `SlotContents` as `@dataclass(frozen=True)` in
`planner_core.domain.candidate` with fields exactly
`candidates: tuple[Candidate, ...]` and `definitive_id: str | None`.

## R2
Implements: FR-MENU-03

IF `SlotContents` is constructed with a `definitive_id` that does not equal
the `id` of any element of `candidates`, THEN the system SHALL raise
`CandidateNotFound`.

## R3
Implements: FR-MENU-03, FR-CAND-04

The system SHALL declare `Candidate` as `@dataclass(frozen=True)` in
`planner_core.domain.candidate` with fields exactly `id: str`,
`meal: MealSnapshot` and `author: str`.

## R4
Implements: FR-MENU-03

The system SHALL provide `definitive(plan: SlotContents) -> Candidate | None`
returning the element of `plan.candidates` whose `id` equals
`plan.definitive_id`, or `None` when `plan.definitive_id` is `None`.

## R5
Implements: FR-CAND-02

The system SHALL provide `new_candidate(id: str, meal: MealSnapshot, author:
str) -> Candidate` as the single construction path for a candidate, used
identically regardless of whether `meal` originated from a library pick, a
from-scratch recipe, or an accepted AI preview.

## R6
Implements: FR-CAND-01

The system SHALL provide `add_candidate(plan: SlotContents, candidate:
Candidate) -> AddCandidateResult` whose `plan` field is `plan` with
`candidate` appended to `candidates`.

## R7
Implements: FR-CAND-01

WHEN `add_candidate` is called with a `candidate` whose meal name normalizes
equal to an existing candidate's meal name in `plan`, the system SHALL set
`AddCandidateResult.duplicate_warning` to `True`.

## R8
Implements: FR-CAND-01

The system SHALL NOT omit `candidate` from `AddCandidateResult.plan.candidates`
when `AddCandidateResult.duplicate_warning` is `True`.

## R9
Implements: FR-CAND-01

The system SHALL provide `edit_candidate(plan: SlotContents, candidate_id:
str, meal: MealSnapshot) -> SlotContents` that replaces the matching
candidate's `meal` while preserving its `id` and `author`.

## R10
Implements: FR-CAND-01

The system SHALL provide `remove_candidate(plan: SlotContents, candidate_id:
str) -> SlotContents` that removes the matching candidate from
`plan.candidates`.

## R11
Implements: FR-CAND-01

IF `edit_candidate` or `remove_candidate` is called with a `candidate_id`
absent from `plan.candidates`, THEN the system SHALL raise
`CandidateNotFound`.

## R12
Implements: FR-CAND-05

The system SHALL provide `promote(plan: SlotContents, candidate_id: str) ->
SlotContents` that sets the result's `definitive_id` to `candidate_id`,
replacing any previous definitive.

## R13
Implements: FR-CAND-05

IF `promote` is called with a `candidate_id` absent from `plan.candidates`,
THEN the system SHALL raise `CandidateNotFound`.

## R14
Implements: FR-CAND-05

WHEN `edit_candidate` is applied to the candidate currently referenced by
`plan.definitive_id`, the system SHALL reflect the edited content as that
slot's definitive (`G-67`).

## R15
Implements: FR-CAND-04

The system SHALL NOT change a candidate's `author` field through
`edit_candidate` or `promote`.

## R16
Implements: FR-CAND-08

The system SHALL provide `clear_definitive(plan: SlotContents) ->
SlotContents` that sets the result's `definitive_id` to `None`, leaving
`candidates` unchanged.

## R17
Implements: FR-MENU-03

WHEN `remove_candidate` removes the candidate currently referenced by
`plan.definitive_id`, the system SHALL set the result's `definitive_id` to
`None`.

## R18
Implements: FR-CAND-06

The system SHALL provide `to_library_entry(meal: MealSnapshot,
existing_names: Iterable[str]) -> LibraryEntryResult` whose `recipe` field is
a new `Recipe` constructed from `meal`'s content.

## R19
Implements: FR-CAND-06

WHEN `to_library_entry`'s resulting `recipe.name` normalizes equal to a name
in `existing_names`, the system SHALL set
`LibraryEntryResult.duplicate_warning` to `True`.

## R20
Implements: FR-CAND-06

The system SHALL NOT omit `recipe` from the result of `to_library_entry` when
`duplicate_warning` is `True`.

## R21
Implements: FR-SUM-01

The system SHALL provide `summary(plans: Mapping[SlotRef, SlotContents]) ->
tuple[tuple[SlotRef, Candidate], ...]` containing exactly the entries of
`plans` whose `SlotContents` has a definitive, each paired with
`definitive(plan)`.

## R22
Implements: FR-SUM-03

The system SHALL provide `resolve_author(author_id: str, known_user_ids:
AbstractSet[str]) -> str` that returns `author_id` unchanged when it is a
member of `known_user_ids`.

## R23
Implements: FR-SUM-03

WHEN `author_id` is not a member of `known_user_ids`, `resolve_author` SHALL
return `UNKNOWN_USER_ID`.

## R24
Implements: FR-AUTH-13

The system SHALL NOT remove or exclude a candidate from a `SlotContents`
because its `author` is absent from a caller-supplied set of known user ids.

---

## Coverage map

| Frozen requirement | Covered by |
|---|---|
| `FR-MENU-03` | R1, R2, R3, R4, R17 |
| `FR-CAND-01` | R6, R7, R8, R9, R10, R11 |
| `FR-CAND-02` | R5 |
| `FR-CAND-04` | R3, R15 |
| `FR-CAND-05` | R12, R13, R14 |
| `FR-CAND-06` | R18, R19, R20 |
| `FR-CAND-08` | R16 |
| `FR-SUM-01` | R21 |
| `FR-SUM-03` | R22, R23 |
| `FR-AUTH-13` | R24 |

| `feature_list.json` acceptance criterion | Covered by |
|---|---|
| A slot holds a list of candidates and at most one definitive (`FR-MENU-03`) | R1, R2, R4 |
| A candidate is constructible from any of the three authoring sources, all landing as the same snapshot-backed candidate (`FR-CAND-02`) | R5 |
| Promoting a candidate replaces any previous definitive; clearing returns all meals to candidate status (`FR-CAND-05`, `FR-CAND-08`) | R12, R13, R16 |
| A promoted meal remains editable; edits propagate wherever it is shown (`G-67`) | R9, R14 |
| Adding a candidate whose normalized name matches one already in the slot returns a warning but still adds it (`FR-CAND-01`, `G-59`) | R6, R7, R8 |
| Saving a meal to the library always creates a new entry and warns on same-name collision (`FR-CAND-06`, `G-26`) | R18, R19, R20 |
| Every candidate carries its author; promotion records no separate attribution (`FR-CAND-04`, `G-79`) | R3, R15 |
| Attribution resolves to the reserved unknown-user placeholder when the author was removed (`FR-SUM-03`, `G-29`) | R22, R23 |

Supporting requirements not demanded by a single criterion but required by the
invariants those criteria rest on: R10, R11 (remove and its error case,
mirroring edit — `FR-CAND-01`'s "add, edit, or remove ... individually"), R17
(a dangling definitive pointer would silently break "at most one definitive
names a real candidate," `FR-MENU-03`), R21 (`FR-SUM-01`'s data-derivation
half, not claimed by any single acceptance bullet but required by `covers`),
R24 (`FR-AUTH-13`'s "retained ... rather than deleted or blocked from
removal" clause, restricted to candidate authorship — see `design.md` §1).
