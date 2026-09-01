"""R2/R3: the DynamoDB adapters store the Spanish attribute names
docs/data_model.md section 1 assigns, and hand planner_core only English domain
objects — no Spanish persisted key leaks back."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import UTC, date, datetime
from typing import Any

from planner_api.adapters.dynamo import _table
from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import Candidate, SlotContents
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Ingredient, MealSnapshot, Recipe
from planner_core.domain.role import Role
from planner_core.domain.rules import CategoryCountRule
from planner_core.domain.units import Unit
from planner_core.ports.accounts import AccountRecord
from planner_core.ports.recipes import LibraryRecipe

from tests.contract.dynamo_contract import (
    dynamo_account_repository,
    dynamo_recipe_repository,
    dynamo_rule_repository,
    dynamo_week_repository,
)

_SPANISH = {
    "nombreUsuario",
    "tipo",
    "isPassReseteada",
    "passHash",
    "validoDesde",
    "idUsuario",
    "nombrePlato",
    "tipoAlimento",
    "tiempo",
    "numeroComensales",
    "añadidoPor",
    "ingredientes",
    "utensilios",
    "pasos",
    "idPlatoDefinitivo",
    "tipoRegla",
    "cantidad",
    "numeroDia",
    "numeroComida",
    "idPlato",
}


def _rows(pk: str, prefix: str) -> list[dict[str, Any]]:
    return _table.query_prefix(pk, prefix)


def test_account_item_uses_the_spanish_attribute_names() -> None:
    dynamo_account_repository().create(
        AccountRecord(
            user_id="u1",
            username="Ana",
            role=Role.USER,
            password_hash="h",
            password_reset_required=True,
            credentials_valid_since=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    attrs = set(_rows("USUARIOS", "ID#")[0]) - {"PK", "SK"}
    assert attrs == {"nombreUsuario", "tipo", "isPassReseteada", "passHash", "validoDesde"}


def test_recipe_item_stores_spanish_keys_and_round_trips_an_english_object() -> None:
    recipe = Recipe(
        name="Lentejas",
        ingredients=(Ingredient(name="Lentejas", quantity=200.0, unit=Unit.GRAM),),
        tools=("olla",),
        procedure=("Cocer",),
        category=IngredientCategory.LEGUME,
    )
    repo = dynamo_recipe_repository()
    repo.save(LibraryRecipe(id="r1", recipe=recipe, author="u1"))

    attrs = set(_rows(f"BIBLIOTECA#{_table.LIBRARY_ID}", "ID#")[0]) - {"PK", "SK"}
    assert attrs <= _SPANISH and {"nombrePlato", "añadidoPor"} <= attrs

    back = repo.get("r1")
    assert back is not None and back.recipe == recipe


def test_rule_item_uses_the_spanish_attribute_names() -> None:
    dynamo_rule_repository().save_rule(CategoryCountRule(category=IngredientCategory.MEAT, count=2))
    attrs = set(_rows(f"GRUPOREGLAS#{_table.RULES_ID}", "REGLA#")[0]) - {"PK", "SK"}
    assert attrs == {"tipoRegla", "tipoAlimento", "cantidad"}


def test_week_candidate_item_uses_the_spanish_attribute_names() -> None:
    meal = MealSnapshot(
        name="Arroz",
        ingredients=(Ingredient(name="Arroz", quantity=100.0, unit=Unit.GRAM),),
        tools=(),
        procedure=(),
        category=IngredientCategory.CARBOHYDRATE,
    )
    week = IsoWeek(2026, 30)
    slot = SlotRef(date.fromisocalendar(2026, 30, 1), MealSlot.LUNCH)
    repo = dynamo_week_repository()
    repo.save_slot(
        week, slot, SlotContents(candidates=(Candidate(id="c1", meal=meal, author="u1"),))
    )

    attrs = set(_rows(f"SEMANA#{week.week_id}", "DIA#")[0]) - {"PK", "SK"}
    assert attrs <= _SPANISH and {"nombrePlato", "añadidoPor"} <= attrs


def test_no_returned_domain_object_carries_a_spanish_attribute_name() -> None:
    for domain_type in (AccountRecord, LibraryRecipe, Candidate, SlotContents):
        assert is_dataclass(domain_type)
        assert not (_SPANISH & {f.name for f in fields(domain_type)})
