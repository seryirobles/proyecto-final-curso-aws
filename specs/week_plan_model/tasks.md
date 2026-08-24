# week_plan_model — Tasks

> Execute in order. Tick `[x]` as each completes.
> Read `design.md` §5 before choosing between a flag and a pointer for
> "definitive," §6 before typing any signature, and §8 before reaching for a
> `Clock`-like port for ids — the caller supplies `id` and `author`.

## Domain — sources (`backend/core/src/planner_core/domain/candidate.py`)

- [x] T1 — Create the module with its docstring, and add `UNKNOWN_USER_ID:
  Final[str] = "unknown-user"` and `CandidateNotFound(PlannerError)` —
  importing `PlannerError` from `planner_core.domain.errors` — storing the
  offending id on `self.candidate_id`. Covers: R2, R11, R13, R22, R23.
- [x] T2 — Add `Candidate` (`@dataclass(frozen=True)`) with fields exactly
  `id: str`, `meal: MealSnapshot`, `author: str`, importing `MealSnapshot`
  from `planner_core.domain.recipe`. Covers: R3.
- [x] T3 — Add `SlotContents` (`@dataclass(frozen=True)`) with fields
  `candidates: tuple[Candidate, ...] = ()` and `definitive_id: str | None =
  None`, plus `__post_init__` raising `CandidateNotFound(definitive_id)` when
  `definitive_id` is not `None` and no element of `candidates` has that `id`
  (`design.md` §5). Covers: R1, R2.
- [x] T4 — Add `new_candidate(id, meal, author) -> Candidate`, a thin
  constructor call with no branching on where `meal` came from (`design.md`
  §1 — the point is that this is the *only* construction path). Covers: R5.
- [x] T5 — Add `definitive(plan: SlotContents) -> Candidate | None`,
  returning the element of `plan.candidates` whose `id` equals
  `plan.definitive_id`, or `None`. No caching, no stored copy — a fresh
  lookup every call (`design.md` §5). Covers: R4.
- [x] T6 — Add `AddCandidateResult` (`@dataclass(frozen=True)`, fields
  `plan: SlotContents`, `duplicate_warning: bool`) and `add_candidate(plan,
  candidate) -> AddCandidateResult`: append `candidate` to `plan.candidates`
  unconditionally; set `duplicate_warning` by comparing
  `normalize(candidate.meal.name)` (import `normalize` from
  `planner_core.domain.text`) against `normalize(c.meal.name)` for every
  existing `c` in `plan.candidates` — never re-deriving the normalization
  rule itself. Covers: R6, R7, R8.
- [x] T7 — Add `edit_candidate(plan, candidate_id, meal) -> SlotContents`:
  rebuild `candidates` replacing the element whose `id == candidate_id` with
  a candidate carrying the new `meal` but the same `id` and `author`,
  preserving tuple position; raise `CandidateNotFound(candidate_id)` if no
  element matches. Covers: R9, R11, R15.
- [x] T8 — Add `remove_candidate(plan, candidate_id) -> SlotContents`:
  filter `candidate_id` out of `candidates`; raise `CandidateNotFound` first
  if no element matches; if `plan.definitive_id == candidate_id`, the result's
  `definitive_id` is `None`, otherwise unchanged (`design.md` §5, §8
  rejected alternative D). Covers: R10, R11, R17.
- [x] T9 — Add `promote(plan, candidate_id) -> SlotContents`: raise
  `CandidateNotFound` if no element of `plan.candidates` has `id ==
  candidate_id`; otherwise return `plan` with `definitive_id` set to
  `candidate_id`. No parameter recording who performed the promotion
  (`design.md` §1, `G-79`). Covers: R12, R13, R15.
- [x] T10 — Add `clear_definitive(plan) -> SlotContents`: return `plan` with
  `definitive_id` set to `None`, `candidates` unchanged. Covers: R16.
- [x] T11 — Add `summary(plans: Mapping[SlotRef, SlotContents]) ->
  tuple[tuple[SlotRef, Candidate], ...]`, importing `SlotRef` from
  `planner_core.domain.calendar`: iterate `plans` in order, keep only entries
  where `definitive(plan)` is not `None`, pair each kept `SlotRef` with that
  candidate. Covers: R21.
- [x] T12 — Add `LibraryEntryResult` (`@dataclass(frozen=True)`, fields
  `recipe: Recipe`, `duplicate_warning: bool`) and `to_library_entry(meal,
  existing_names) -> LibraryEntryResult`, importing `Recipe` from
  `planner_core.domain.recipe`: build `recipe = Recipe(name=meal.name,
  ingredients=meal.ingredients, tools=meal.tools, procedure=meal.procedure,
  category=meal.category)` unconditionally; set `duplicate_warning` by
  comparing `normalize(recipe.name)` against `normalize(existing)` for each
  `existing` in `existing_names`. Covers: R18, R19, R20.
- [x] T13 — Add `resolve_author(author_id: str, known_user_ids:
  AbstractSet[str]) -> str`: return `author_id` if it is a member of
  `known_user_ids`, else `UNKNOWN_USER_ID`. No mutation of any `Candidate`
  (`design.md` §6 — this is a pure render-time computation). Covers: R22,
  R23.

## Tests (`backend/core/tests/domain/test_candidate.py`)

- [x] T14 — `test_slot_contents_holds_candidates_and_at_most_one_definitive`
  — construct a `SlotContents` with two candidates and `definitive_id`
  matching one of them; assert `definitive_id` is a single value, never a
  collection. Covers: R1.
  > **Note, 2026-08-24 (`O9`).** The "never a collection" half is carried by
  > `assert plan.definitive_id == "c1"`, which `M63` proves catches exactly
  > that defect. A separate `isinstance` line was removed as incapable of
  > failing (`O6`, round 2). Substantively satisfied, not dropped.
- [x] T15 — `test_slot_contents_rejects_a_dangling_definitive_id` —
  `with pytest.raises(CandidateNotFound): SlotContents(candidates=(one,),
  definitive_id="does-not-exist")`. Covers: R2.
- [x] T16 — `test_candidate_fields_are_exactly_the_fixed_shape` — introspect
  `{f.name for f in dataclasses.fields(Candidate)}` equals exactly `{"id",
  "meal", "author"}`. Covers: R3.
- [x] T17 — `test_definitive_resolves_by_id_lookup_not_by_cache` — build a
  plan, call `definitive(plan)`, then build a *second* `SlotContents` sharing
  the same `definitive_id` but a `candidates` tuple with that id's element
  edited; assert the second call returns the edited content, proving the
  lookup is live. Covers: R4, R14.
- [x] T18 — `test_new_candidate_is_the_only_construction_path` — call
  `new_candidate` three times with meals built to represent a library pick,
  a from-scratch recipe and an accepted AI preview (all just `MealSnapshot`
  values — this feature does not model the AI pipeline); assert all three
  results are plain `Candidate` instances with no distinguishing "source"
  field. Covers: R5.
- [x] T19 — `test_add_candidate_always_appends` — add a candidate to a
  three-candidate plan; assert the result has four, in order, the new one
  last. Covers: R6.
- [x] T20 — `test_add_candidate_warns_on_a_normalized_name_match` — add a
  candidate named `"Tomate"` to a slot already holding one named `"tomate "`
  (trailing space, feature 3's normalization); assert
  `duplicate_warning is True` **and** the new candidate is present in
  `result.plan.candidates`. Covers: R7, R8.
- [x] T21 — `test_add_candidate_does_not_warn_on_distinct_names` — add a
  candidate with a distinct name; assert `duplicate_warning is False`.
  Covers: R7 (negative case).
- [x] T22 — `test_edit_candidate_replaces_meal_preserving_id_and_author` —
  edit one candidate's `meal`; assert its `id` and `author` are unchanged
  and its position in `candidates` is unchanged. Covers: R9, R15.
- [x] T23 — `test_remove_candidate_removes_the_matching_one` — remove one of
  three; assert the result has two, the other two unchanged. Covers: R10.
- [x] T24 — `test_edit_and_remove_raise_on_an_unknown_id` — both
  `edit_candidate` and `remove_candidate` raise `CandidateNotFound` for an id
  absent from `plan.candidates`. Covers: R11.
- [x] T25 — `test_promote_sets_the_definitive_and_replaces_any_previous` —
  promote candidate B in a plan already definitive on candidate A; assert
  `definitive(result).id == "b"`. Covers: R12.
- [x] T26 — `test_promote_raises_on_an_unknown_id` — `CandidateNotFound` for
  an id absent from `plan.candidates`. Covers: R13.
- [x] T27 — `test_editing_the_definitive_candidate_propagates` — promote a
  candidate, then `edit_candidate` that same id's `meal`; assert
  `definitive(result).meal` equals the new content, not the original
  (`G-67`, `docs/verification.md` Level 4). Covers: R14.
- [x] T28 — `test_promote_takes_no_author_or_promoter_argument` — call
  `inspect.signature(promote).parameters`; assert it is exactly `{"plan",
  "candidate_id"}` — no third parameter through which a promoter identity
  could be threaded (`G-79`). Covers: R15.
- [x] T29 — `test_clear_definitive_unsets_it_and_keeps_candidates` — clear a
  plan with a definitive; assert `definitive_id is None` and `candidates`
  unchanged (`G-16`). Covers: R16.
- [x] T30 — `test_removing_the_definitive_candidate_clears_it` — remove the
  candidate currently definitive; assert the result's `definitive_id is
  None` and no exception is raised. Covers: R17.
- [x] T31 — `test_to_library_entry_builds_a_new_recipe_from_the_snapshot` —
  build a `MealSnapshot` with non-trivial ingredients/tools/procedure; assert
  `result.recipe.name/ingredients/tools/procedure/category` all equal the
  snapshot's values, and `result.recipe` is a `Recipe`, not a `MealSnapshot`.
  Covers: R18.
- [x] T32 — `test_to_library_entry_warns_on_a_normalized_name_collision` —
  `existing_names=["tomate"]`, `meal.name="Tomate "`; assert
  `duplicate_warning is True` and `result.recipe` is still present (not
  `None`). Covers: R19, R20.
- [x] T33 — `test_to_library_entry_does_not_warn_without_a_collision` —
  distinct names; assert `duplicate_warning is False`. Covers: R19 (negative
  case).
- [x] T34 — `test_summary_contains_exactly_the_definitive_holding_slots` —
  build a `Mapping[SlotRef, SlotContents]` with three slots: one with a
  definitive, one with only candidates, one empty; assert `summary()` returns
  exactly one pair, matching the first slot's `SlotRef` and its definitive
  `Candidate`. Covers: R21.
- [x] T35 — `test_resolve_author_returns_the_id_unchanged_when_known` —
  `resolve_author("u1", {"u1", "u2"}) == "u1"`. Covers: R22.
- [x] T36 — `test_resolve_author_substitutes_the_placeholder_when_unknown` —
  `resolve_author("removed-user", {"u1", "u2"}) == UNKNOWN_USER_ID`. Covers:
  R23.
- [x] T37 — `test_resolve_author_is_idempotent_on_the_placeholder` —
  `resolve_author(UNKNOWN_USER_ID, {"u1"}) == UNKNOWN_USER_ID` (`design.md`
  §6). Covers: R23.
- [x] T38 — `test_a_candidate_with_an_unknown_author_is_never_excluded` —
  build a plan whose sole candidate's `author` is not in a `known_user_ids`
  set; assert the candidate is still present in `plan.candidates`, is still
  promotable, and `resolve_author` on its `author` returns the placeholder
  without the candidate itself disappearing from any operation in this
  module (`FR-AUTH-13`). Covers: R24.

## Close-out

- [x] T39 — Record the `R<n> → test` map in
  `progress/impl_week_plan_model.md` (`docs/verification.md` Level 3).
  Covers: R1–R24.
- [x] T40 — Confirm `backend/core/pyproject.toml` still reads
  `dependencies = []`, and that `uv export --package planner-api --no-dev`
  and `uv export --package planner-ai --no-dev` both resolve with nothing
  added. Covers: R1–R24 (no dependency introduced).
- [x] T41 — Run `./init.sh` and confirm every gate is green: `ruff format`,
  `ruff check`, `mypy --strict`, `pytest`, plus the frontend gate. Covers:
  R1–R24.
