"""Tests for candidates, slot contents, promotion and attribution (R1-R24)."""

from __future__ import annotations

import dataclasses
import inspect
from datetime import date

import pytest

from planner_core.domain.calendar import MealSlot, SlotRef
from planner_core.domain.candidate import (
    UNKNOWN_USER_ID,
    Candidate,
    CandidateNotFound,
    SlotContents,
    add_candidate,
    clear_definitive,
    definitive,
    edit_candidate,
    new_candidate,
    promote,
    remove_candidate,
    resolve_author,
    summary,
    to_library_entry,
)
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Ingredient, MealSnapshot
from planner_core.domain.units import parse_unit


def _meal(name: str = "Lentejas con chorizo") -> MealSnapshot:
    return MealSnapshot(
        name=name,
        ingredients=(Ingredient(name="lentejas", quantity=500, unit=parse_unit("g")),),
        tools=("olla",),
        procedure=("Cocer las lentejas.",),
        category=IngredientCategory.LEGUME,
    )


def _candidate(id: str = "c1", name: str = "Lentejas con chorizo", author: str = "u1") -> Candidate:
    return Candidate(id=id, meal=_meal(name), author=author)


def test_candidate_is_frozen() -> None:
    """R3: mutating means constructing a new instance (docs/conventions.md)."""
    candidate = _candidate("c1")

    with pytest.raises(dataclasses.FrozenInstanceError):
        candidate.__setattr__("author", "u2")


def test_slot_contents_is_frozen() -> None:
    """R1: mutating means constructing a new instance (docs/conventions.md)."""
    plan = SlotContents(candidates=(_candidate("c1"),))

    with pytest.raises(dataclasses.FrozenInstanceError):
        plan.__setattr__("definitive_id", "c1")


def test_slot_contents_holds_candidates_and_at_most_one_definitive() -> None:
    """R1: definitive_id is a single value, never a collection."""
    one = _candidate("c1")
    two = _candidate("c2", name="Otro plato")
    plan = SlotContents(candidates=(one, two), definitive_id="c1")

    assert plan.definitive_id == "c1"


def test_slot_contents_rejects_a_dangling_definitive_id() -> None:
    """R2: a definitive pointer must name a real candidate."""
    one = _candidate("c1")

    with pytest.raises(CandidateNotFound) as excinfo:
        SlotContents(candidates=(one,), definitive_id="does-not-exist")
    assert excinfo.value.candidate_id == "does-not-exist"


def test_candidate_fields_are_exactly_the_fixed_shape() -> None:
    """R3: id, meal and author, nothing else."""
    field_names = {f.name for f in dataclasses.fields(Candidate)}
    assert field_names == {"id", "meal", "author"}


def test_definitive_resolves_by_id_lookup_not_by_cache() -> None:
    """R4, R14: a second plan sharing the id but different content still resolves live."""
    original = _candidate("c1")
    plan = SlotContents(candidates=(original,), definitive_id="c1")
    assert definitive(plan) == original

    edited = Candidate(id="c1", meal=_meal("Nuevo nombre"), author=original.author)
    reconstructed = SlotContents(candidates=(edited,), definitive_id="c1")
    resolved = definitive(reconstructed)
    assert resolved == edited
    assert resolved is not None
    assert resolved.meal.name == "Nuevo nombre"


def test_new_candidate_is_the_only_construction_path() -> None:
    """R5: library pick, from-scratch and accepted AI preview all land as plain Candidates."""
    pisto, tortilla, gazpacho = _meal("Pisto"), _meal("Tortilla"), _meal("Gazpacho")
    library_pick = new_candidate("c1", pisto, "u1")
    from_scratch = new_candidate("c2", tortilla, "u2")
    ai_preview = new_candidate("c3", gazpacho, "u1")

    for result, expected_id, expected_meal, expected_author in (
        (library_pick, "c1", pisto, "u1"),
        (from_scratch, "c2", tortilla, "u2"),
        (ai_preview, "c3", gazpacho, "u1"),
    ):
        assert isinstance(result, Candidate)
        assert {f.name for f in dataclasses.fields(result)} == {"id", "meal", "author"}
        assert result.id == expected_id
        assert result.meal == expected_meal
        assert result.author == expected_author


def test_add_candidate_always_appends() -> None:
    """R6: the new candidate lands last, existing ones untouched."""
    plan = SlotContents(candidates=(_candidate("c1"), _candidate("c2"), _candidate("c3")))
    fourth = _candidate("c4", name="Otro plato distinto")

    result = add_candidate(plan, fourth)

    assert [c.id for c in result.plan.candidates] == ["c1", "c2", "c3", "c4"]


def test_add_candidate_warns_on_a_normalized_name_match() -> None:
    """R7, R8: a normalized-name collision warns but the candidate is still added."""
    existing = _candidate("c1", name="tomate ")
    plan = SlotContents(candidates=(existing,))
    new = _candidate("c2", name="Tomate")

    result = add_candidate(plan, new)

    assert result.duplicate_warning is True
    assert new in result.plan.candidates


def test_add_candidate_does_not_warn_on_distinct_names() -> None:
    """R7 negative case: distinct names raise no warning."""
    plan = SlotContents(candidates=(_candidate("c1", name="Tomate"),))
    new = _candidate("c2", name="Pisto")

    result = add_candidate(plan, new)

    assert result.duplicate_warning is False


def test_edit_candidate_replaces_meal_preserving_id_and_author() -> None:
    """R9, R15: id and author survive an edit; position in the tuple is unchanged."""
    plan = SlotContents(candidates=(_candidate("c1", author="u1"), _candidate("c2", author="u2")))

    result = edit_candidate(plan, "c1", _meal("Nuevo nombre"))

    assert [c.id for c in result.candidates] == ["c1", "c2"]
    edited = result.candidates[0]
    assert edited.id == "c1"
    assert edited.author == "u1"
    assert edited.meal.name == "Nuevo nombre"


def test_remove_candidate_removes_the_matching_one() -> None:
    """R10: the other two candidates are untouched."""
    one, two, three = _candidate("c1"), _candidate("c2", name="Dos"), _candidate("c3", name="Tres")
    plan = SlotContents(candidates=(one, two, three))

    result = remove_candidate(plan, "c2")

    assert [c.id for c in result.candidates] == ["c1", "c3"]


def test_removing_a_non_definitive_candidate_leaves_the_definitive_untouched() -> None:
    """Architecture section 4 invariant 2: removal never touches an unrelated definitive."""
    one, two = _candidate("c1"), _candidate("c2", name="Dos")
    plan = SlotContents(candidates=(one, two), definitive_id="c1")

    result = remove_candidate(plan, "c2")

    assert result.definitive_id == "c1"
    assert definitive(result) == one


def test_edit_and_remove_raise_on_an_unknown_id() -> None:
    """R11: both operations raise CandidateNotFound for an absent id."""
    plan = SlotContents(candidates=(_candidate("c1"),))

    with pytest.raises(CandidateNotFound) as edit_excinfo:
        edit_candidate(plan, "missing", _meal())
    assert edit_excinfo.value.candidate_id == "missing"
    with pytest.raises(CandidateNotFound) as remove_excinfo:
        remove_candidate(plan, "missing")
    assert remove_excinfo.value.candidate_id == "missing"


def test_promote_sets_the_definitive_and_replaces_any_previous() -> None:
    """R12: promoting b in a plan definitive on a replaces the pointer."""
    a, b = _candidate("a"), _candidate("b", name="Otro")
    plan = SlotContents(candidates=(a, b), definitive_id="a")

    result = promote(plan, "b")

    resolved = definitive(result)
    assert resolved is not None
    assert resolved.id == "b"


def test_promote_raises_on_an_unknown_id() -> None:
    """R13: CandidateNotFound for an id absent from the plan."""
    plan = SlotContents(candidates=(_candidate("a"),))

    with pytest.raises(CandidateNotFound) as excinfo:
        promote(plan, "missing")
    assert excinfo.value.candidate_id == "missing"


def test_editing_the_definitive_candidate_propagates() -> None:
    """R14 (G-67): definitive(plan) shows the edited content with no extra call."""
    plan = SlotContents(candidates=(_candidate("c1", name="Original"),), definitive_id="c1")

    edited_plan = edit_candidate(plan, "c1", _meal("Editado"))

    result = definitive(edited_plan)
    assert result is not None
    assert result.meal.name == "Editado"


def test_promote_takes_no_author_or_promoter_argument() -> None:
    """R15 (G-79): promote's signature carries no promoter identity parameter."""
    assert set(inspect.signature(promote).parameters) == {"plan", "candidate_id"}


def test_clear_definitive_unsets_it_and_keeps_candidates() -> None:
    """R16: candidates are unchanged after clearing."""
    plan = SlotContents(candidates=(_candidate("c1"),), definitive_id="c1")

    result = clear_definitive(plan)

    assert result.definitive_id is None
    assert result.candidates == plan.candidates


def test_removing_the_definitive_candidate_clears_it() -> None:
    """R17: no exception, the pointer is simply cleared."""
    plan = SlotContents(
        candidates=(_candidate("c1"), _candidate("c2", name="Otro")), definitive_id="c1"
    )

    result = remove_candidate(plan, "c1")

    assert result.definitive_id is None
    assert [c.id for c in result.candidates] == ["c2"]


def test_to_library_entry_builds_a_new_recipe_from_the_snapshot() -> None:
    """R18: every field carries over, and the result is a Recipe, not a MealSnapshot."""
    meal = _meal("Lentejas con chorizo")

    result = to_library_entry(meal, existing_names=())

    assert result.recipe.name == meal.name
    assert result.recipe.ingredients == meal.ingredients
    assert result.recipe.tools == meal.tools
    assert result.recipe.procedure == meal.procedure
    assert result.recipe.category == meal.category
    assert not isinstance(result.recipe, MealSnapshot)


def test_to_library_entry_warns_on_a_normalized_name_collision() -> None:
    """R19, R20: the recipe is still returned even when the warning fires."""
    meal = _meal("Tomate ")

    result = to_library_entry(meal, existing_names=["tomate"])

    assert result.duplicate_warning is True
    assert result.recipe.name == meal.name
    assert result.recipe.ingredients == meal.ingredients
    assert result.recipe.tools == meal.tools
    assert result.recipe.procedure == meal.procedure
    assert result.recipe.category == meal.category


def test_to_library_entry_does_not_warn_without_a_collision() -> None:
    """R19 negative case."""
    meal = _meal("Pisto")

    result = to_library_entry(meal, existing_names=["tomate"])

    assert result.duplicate_warning is False


def test_summary_contains_exactly_the_definitive_holding_slots() -> None:
    """R21: only the slot with a definitive appears, paired with it."""
    with_definitive = SlotContents(candidates=(_candidate("c1"),), definitive_id="c1")
    candidates_only = SlotContents(candidates=(_candidate("c2", name="Otro"),))
    empty = SlotContents()

    ref_with = SlotRef(day=date(2026, 8, 24), slot=MealSlot.LUNCH)
    ref_candidates = SlotRef(day=date(2026, 8, 24), slot=MealSlot.DINNER)
    ref_empty = SlotRef(day=date(2026, 8, 25), slot=MealSlot.LUNCH)

    plans = {ref_with: with_definitive, ref_candidates: candidates_only, ref_empty: empty}

    result = summary(plans)

    assert result == ((ref_with, definitive(with_definitive)),)


def test_resolve_author_returns_the_id_unchanged_when_known() -> None:
    """R22."""
    assert resolve_author("u1", {"u1", "u2"}) == "u1"


def test_resolve_author_substitutes_the_placeholder_when_unknown() -> None:
    """R23."""
    assert resolve_author("removed-user", {"u1", "u2"}) == UNKNOWN_USER_ID


def test_unknown_user_id_matches_the_seeded_placeholder_account() -> None:
    """Pinned value, shared with feature 15's seed account (docs/data_model.md section 5.1)."""
    assert UNKNOWN_USER_ID == "unknown-user"


def test_resolve_author_is_idempotent_on_the_placeholder() -> None:
    """R23 (design.md section 6): re-resolving an already-resolved id is a no-op."""
    assert resolve_author(UNKNOWN_USER_ID, {"u1"}) == UNKNOWN_USER_ID


def test_a_candidate_with_an_unknown_author_is_never_excluded() -> None:
    """R24 (FR-AUTH-13): a candidate stays fully usable regardless of its author's fate."""
    orphaned = _candidate("c1", author="removed-user")
    plan = SlotContents(candidates=(orphaned,))

    assert orphaned in plan.candidates

    promoted = promote(plan, "c1")
    assert definitive(promoted) == orphaned
    assert resolve_author(orphaned.author, {"u1", "u2"}) == UNKNOWN_USER_ID
    assert orphaned in promoted.candidates
