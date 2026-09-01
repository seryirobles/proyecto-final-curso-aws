"""Library recipe CRUD (AP15-AP17) plus the pin cascade on delete
(docs/rest_api_contract.md section 3.4, FR-RULE-07)."""

from __future__ import annotations

from dataclasses import dataclass

from planner_core.domain.rules import PinRule, PinRulesAffected, remove_pins_referencing, rule_id
from planner_core.domain.text import normalize
from planner_core.ports.recipes import LibraryRecipe, RecipeRepository
from planner_core.ports.rules import RuleRepository


@dataclass(frozen=True)
class SaveRecipeOutcome:
    """The library marker plus the same-name warning save never blocks on (G-26)."""

    marker: int
    duplicate_warning: bool


@dataclass(frozen=True)
class DeleteRecipeOutcome:
    """The library marker after the recipe delete, plus the pin rules the
    confirmed cascade removed (empty when none referenced it)."""

    marker: int
    removed_pins: tuple[PinRule, ...]


def list_library(*, recipes: RecipeRepository) -> tuple[LibraryRecipe, ...]:
    """AP14."""
    return recipes.list_all()


def save_recipe(entry: LibraryRecipe, *, recipes: RecipeRepository) -> SaveRecipeOutcome:
    """AP16 — create or edit by id; report a same-name collision, never reject it."""
    folded = normalize(entry.recipe.name)
    duplicate = any(
        other.id != entry.id and normalize(other.recipe.name) == folded
        for other in recipes.list_all()
    )
    return SaveRecipeOutcome(marker=recipes.save(entry), duplicate_warning=duplicate)


def delete_recipe(
    recipe_id: str, *, confirm_cascade: bool, recipes: RecipeRepository, rules: RuleRepository
) -> DeleteRecipeOutcome:
    """AP17. An unconfirmed delete of a pinned recipe reports the affected pins
    and writes nothing (R18); a confirmed one removes the recipe and every pin
    referencing it (R19). Matching is on the id, never the name (FR-CAND-06)."""
    affected = remove_pins_referencing(rules.get(), recipe_id).removed_pins
    if affected and not confirm_cascade:
        raise PinRulesAffected(affected)
    marker = recipes.delete(recipe_id)
    for pin in affected:
        rules.delete_rule(rule_id(pin))
    return DeleteRecipeOutcome(marker=marker, removed_pins=affected)
