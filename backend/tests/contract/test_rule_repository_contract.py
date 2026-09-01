"""Contract suite for RuleRepository: one suite, run against every registered
implementation. GQ3: per-rule writes keyed by natural id, no whole-RuleSet
blob write. Feature 18's marker assertions carry over unchanged."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from planner_core.domain.calendar import MealSlot
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.rules import CategoryCountRule, DisabledDay, PinRule, RuleSet, rule_id
from planner_core.ports.rules import RuleRepository
from support.fakes import FakeRuleRepository

from tests.contract.dynamo_contract import dynamo_rule_repository

IMPLEMENTATIONS: list[Callable[[], RuleRepository]] = [FakeRuleRepository, dynamo_rule_repository]

CAT = CategoryCountRule(category=IngredientCategory.MEAT, count=2)
PIN = PinRule(day=1, slot=MealSlot.LUNCH, recipe_id="r1")


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_get_returns_an_empty_rule_set_before_any_write(
    repository_factory: Callable[[], RuleRepository],
) -> None:
    assert repository_factory().get() == RuleSet()


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_save_rule_then_get_reconstructs_the_set(
    repository_factory: Callable[[], RuleRepository],
) -> None:
    repo = repository_factory()
    repo.save_rule(CAT)
    repo.save_rule(PIN)
    repo.save_rule(DisabledDay(day=7))

    assert repo.get() == RuleSet(category_counts=(CAT,), pins=(PIN,), disabled_days=(7,))


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_save_rule_replaces_by_natural_key(
    repository_factory: Callable[[], RuleRepository],
) -> None:
    repo = repository_factory()
    repo.save_rule(CategoryCountRule(category=IngredientCategory.MEAT, count=2))
    repo.save_rule(CategoryCountRule(category=IngredientCategory.MEAT, count=3))

    assert repo.get().category_counts == (
        CategoryCountRule(category=IngredientCategory.MEAT, count=3),
    )


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_delete_rule_drops_the_item_by_id(
    repository_factory: Callable[[], RuleRepository],
) -> None:
    repo = repository_factory()
    repo.save_rule(PIN)

    repo.delete_rule(rule_id(PIN))

    assert repo.get() == RuleSet()


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_the_port_retains_no_whole_rule_set_write(
    repository_factory: Callable[[], RuleRepository],
) -> None:
    """R12 — save(RuleSet) is gone; only per-rule writes remain."""
    assert not hasattr(repository_factory(), "save")


# --- change marker (FR-RT-01): feature 18's assertions, retargeted ---


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_each_mutation_advances_the_marker_and_returns_the_new_value(
    repository_factory: Callable[[], RuleRepository],
) -> None:
    repo = repository_factory()

    assert repo.save_rule(CAT) == 1
    assert repo.current_version() == 1
    assert repo.delete_rule("cat#meat") == 2
    assert repo.current_version() == 2


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_reads_leave_the_marker_unchanged(
    repository_factory: Callable[[], RuleRepository],
) -> None:
    repo = repository_factory()
    repo.save_rule(CAT)

    repo.get()
    repo.current_version()

    assert repo.current_version() == 1


@pytest.mark.parametrize("repository_factory", IMPLEMENTATIONS)
def test_two_successive_writes_both_apply_and_advance_the_marker_twice(
    repository_factory: Callable[[], RuleRepository],
) -> None:
    repo = repository_factory()

    first = repo.save_rule(CAT)
    second = repo.save_rule(PIN)  # no raise: last-write-wins per rule

    assert (first, second) == (1, 2)
