"""Issue add-dish-button-inert, scope extension of 2026-09-22 (E6): editing a
candidate takes the same three-way authoring body as adding one (AP13, named
"Editar o anadir comida"; rest_api_contract.md section 3.1, FR-CAND-02). The
bare `{"recipe": ...}` body the SPA's from-scratch tab sends keeps working."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from _helpers import api_event, authorizer_context, make_deps, seed_user
from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import Candidate, SlotContents
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Ingredient, Recipe, snapshot
from planner_core.domain.units import Unit
from planner_core.ports.recipes import LibraryRecipe

from planner_api.handler import handle
from planner_api.wiring import Dependencies

WEEK = IsoWeek(2026, 34)
SLOT = SlotRef(date.fromisocalendar(2026, 34, 1), MealSlot.LUNCH)
PATH_PARAMS = {"weekId": "2026-W34", "day": "1", "slot": "1", "candidateId": "c-1"}
RESOURCE = "/v1/weeks/{weekId}/days/{day}/slots/{slot}/candidates/{candidateId}"


def _recipe(name: str) -> Recipe:
    return Recipe(
        name=name,
        ingredients=(Ingredient(name="lentejas", quantity=300.0, unit=Unit.GRAM),),
        tools=("olla",),
        procedure=("Cocer.",),
        category=IngredientCategory.LEGUME,
    )


def _recipe_body(name: str) -> dict[str, Any]:
    return {
        "name": name,
        "category": "legume",
        "ingredients": [{"name": "lentejas", "quantity": 300, "unit": "g"}],
        "tools": ["olla"],
        "procedure": ["Cocer."],
    }


def _seed(deps: Dependencies) -> None:
    deps.weeks.save_slot(
        WEEK,
        SLOT,
        SlotContents(
            candidates=(Candidate(id="c-1", meal=snapshot(_recipe("Lentejas")), author="u-1"),)
        ),
    )


def _edit(deps: Dependencies, body: dict[str, Any], token: str) -> dict[str, Any]:
    event = api_event(
        "PUT",
        RESOURCE,
        path_params=PATH_PARAMS,
        body=body,
        cookie=token,
        context=authorizer_context(user_id="u-1"),
    )
    return handle(event, deps)


def test_editing_a_candidate_from_a_library_recipe_copies_its_content() -> None:
    """E6: the `library` arm of the section 3.1 body, on PUT as on POST."""
    deps = make_deps()
    token = seed_user(deps, user_id="u-1")
    _seed(deps)
    deps.recipes.save(LibraryRecipe(id="r-1", recipe=_recipe("Lentejas al curry"), author="u-1"))

    response = _edit(deps, {"source": "library", "recipeId": "r-1"}, token)

    assert response["statusCode"] == 200
    assert json.loads(response["body"])["candidate"]["recipe"]["name"] == "Lentejas al curry"


def test_editing_a_candidate_from_scratch_uses_the_manual_body() -> None:
    """E6: the `manual` arm, which is what the SPA's from-scratch tab sends."""
    deps = make_deps()
    token = seed_user(deps, user_id="u-1")
    _seed(deps)

    response = _edit(
        deps, {"source": "manual", "recipe": _recipe_body("Lentejas estofadas")}, token
    )

    assert response["statusCode"] == 200
    assert json.loads(response["body"])["candidate"]["recipe"]["name"] == "Lentejas estofadas"


def test_editing_a_candidate_still_accepts_the_bare_recipe_body() -> None:
    """Regression: the shape shipped today keeps working (no client break)."""
    deps = make_deps()
    token = seed_user(deps, user_id="u-1")
    _seed(deps)

    response = _edit(deps, {"recipe": _recipe_body("Lentejas viudas")}, token)

    assert response["statusCode"] == 200
    assert json.loads(response["body"])["candidate"]["recipe"]["name"] == "Lentejas viudas"


def test_editing_a_candidate_with_an_unknown_library_recipe_is_not_found() -> None:
    """E6: the same RECIPE_NOT_FOUND the add path raises, not a 400."""
    deps = make_deps()
    token = seed_user(deps, user_id="u-1")
    _seed(deps)

    response = _edit(deps, {"source": "library", "recipeId": "missing"}, token)

    assert response["statusCode"] == 404
    assert json.loads(response["body"])["code"] == "RECIPE_NOT_FOUND"
