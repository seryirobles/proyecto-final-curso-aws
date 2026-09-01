"""DynamoDB `WeekRepository` — SEMANA#<idSemana> partition (docs/data_model.md
section 1, section 4.2). Operates at SlotContents granularity over the per-item
candidate / DEFINITIVO split. AP8/AP9 scope with begins_with(SK, 'DIA#') to
exclude MARCA; a dangling idPlatoDefinitivo reads as no definitive (section 5.4)."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import Any

from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import Candidate, SlotContents
from planner_core.domain.recipe import MealSnapshot

from planner_api.adapters.dynamo import _meal, _table

_DIA_PREFIX = "DIA#"


def _pk(week: IsoWeek) -> str:
    return f"SEMANA#{week.week_id}"


def _slot_prefix(day_number: int, meal: int) -> str:
    return f"{_DIA_PREFIX}{day_number}#COMIDA#{meal}#"


def _candidate_sk(day_number: int, meal: int, candidate_id: str) -> str:
    return f"{_slot_prefix(day_number, meal)}ID#{candidate_id}"


def _definitive_sk(day_number: int, meal: int) -> str:
    return f"{_slot_prefix(day_number, meal)}DEFINITIVO"


def _candidate_item(week: IsoWeek, ref: SlotRef, candidate: Candidate) -> dict[str, Any]:
    meal = candidate.meal
    return {
        "PK": _pk(week),
        "SK": _candidate_sk(ref.day_number, ref.slot.value, candidate.id),
        "añadidoPor": candidate.author,
        **_meal.content_attrs(
            name=meal.name,
            ingredients=meal.ingredients,
            tools=meal.tools,
            procedure=meal.procedure,
            category=meal.category,
            servings=meal.servings,
            estimated_time=meal.estimated_time,
        ),
    }


def _definitive_item(week: IsoWeek, ref: SlotRef, candidate_id: str) -> dict[str, Any]:
    return {
        "PK": _pk(week),
        "SK": _definitive_sk(ref.day_number, ref.slot.value),
        "idPlatoDefinitivo": candidate_id,
    }


def _to_candidate(item: dict[str, Any], candidate_id: str) -> Candidate:
    meal = MealSnapshot(
        name=str(item["nombrePlato"]),
        ingredients=_meal.read_ingredients(item),
        tools=_meal.read_tools(item),
        procedure=_meal.read_procedure(item),
        category=_meal.read_category(item),
        servings=_meal.read_servings(item),
        estimated_time=_meal.read_estimated_time(item),
    )
    return Candidate(id=candidate_id, meal=meal, author=str(item["añadidoPor"]))


def _parse_sk(sk: str) -> tuple[int, int, str]:
    # DIA#<d>#COMIDA#<c>#(ID#<idPlato> | DEFINITIVO)
    _, day, _, meal, tail = sk.split("#", 4)
    return int(day), int(meal), tail


def _slot_put_actions(
    week: IsoWeek, ref: SlotRef, contents: SlotContents
) -> tuple[list[dict[str, Any]], set[str]]:
    """Put actions for a slot's candidates + definitive, and the SK set they keep."""
    day, meal = ref.day_number, ref.slot.value
    keep = {_candidate_sk(day, meal, c.id) for c in contents.candidates}
    actions = [_table.put_action(_candidate_item(week, ref, c)) for c in contents.candidates]
    if contents.definitive_id is not None:
        keep.add(_definitive_sk(day, meal))
        actions.append(_table.put_action(_definitive_item(week, ref, contents.definitive_id)))
    return actions, keep


class DynamoWeekRepository:
    def current_version(self, week: IsoWeek) -> int:
        return _table.read_marker(_pk(week))

    def get_week(self, week: IsoWeek) -> Mapping[SlotRef, SlotContents]:
        candidates: dict[tuple[int, int], list[Candidate]] = {}
        definitives: dict[tuple[int, int], str] = {}
        for row in _table.query_prefix(_pk(week), _DIA_PREFIX):
            day, meal, tail = _parse_sk(str(row["SK"]))
            if tail == "DEFINITIVO":
                definitives[day, meal] = str(row["idPlatoDefinitivo"])
            else:
                cid = tail.removeprefix("ID#")
                candidates.setdefault((day, meal), []).append(_to_candidate(row, cid))

        result: dict[SlotRef, SlotContents] = {}
        for key in candidates.keys() | definitives.keys():
            day, meal = key
            ref = SlotRef(date.fromisocalendar(week.iso_year, week.iso_week, day), MealSlot(meal))
            slot_candidates = tuple(candidates.get(key, ()))
            definitive_id = definitives.get(key)
            if definitive_id is not None and not any(
                c.id == definitive_id for c in slot_candidates
            ):
                definitive_id = None  # dangling pointer reads as no definitive (section 5.4)
            result[ref] = SlotContents(candidates=slot_candidates, definitive_id=definitive_id)
        return result

    def save_slot(self, week: IsoWeek, slot: SlotRef, contents: SlotContents) -> int:
        prefix = _slot_prefix(slot.day_number, slot.slot.value)
        existing = {str(row["SK"]) for row in _table.query_prefix(_pk(week), prefix)}
        actions, keep = _slot_put_actions(week, slot, contents)
        actions.extend(_table.delete_action(_pk(week), sk) for sk in existing if sk not in keep)
        return _table.commit(_pk(week), actions)

    def save_week(self, week: IsoWeek, plans: Mapping[SlotRef, SlotContents]) -> int:
        existing = {str(row["SK"]) for row in _table.query_prefix(_pk(week), _DIA_PREFIX)}
        actions: list[dict[str, Any]] = []
        keep: set[str] = set()
        for ref, contents in plans.items():
            slot_actions, slot_keep = _slot_put_actions(week, ref, contents)
            actions.extend(slot_actions)
            keep |= slot_keep
        actions.extend(_table.delete_action(_pk(week), sk) for sk in existing if sk not in keep)
        return _table.commit(_pk(week), actions)
