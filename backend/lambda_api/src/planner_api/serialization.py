"""Wire <-> domain boundary: JSON parsing, camelCase encoding and path-param
parsing (docs/rest_api_contract.md section 1, section 3.0). The one place the
English-identifier / Spanish-string split (docs/conventions.md) meets HTTP."""

from __future__ import annotations

import json
from typing import Any  # untyped JSON in/out is the wire boundary itself (conventions.md)

from planner_core import messages
from planner_core.domain.calendar import IsoWeek, MealSlot, SlotRef
from planner_core.domain.candidate import Candidate
from planner_core.domain.errors import (
    EmptyCategory,
    EmptyIngredientName,
    EmptyMeasure,
    EmptyName,
    EmptyProcedureStep,
    EmptyQuantity,
    EmptyTool,
    PlannerError,
)
from planner_core.domain.generation import (
    GenerationMode,
    GenerationTargets,
    ReferenceSource,
    RuleOverride,
    SingleRecipeRequest,
    SlotStatus,
    SpecificationSource,
)
from planner_core.domain.ingredient_category import IngredientCategory, parse_category
from planner_core.domain.recipe import (
    Ingredient,
    MealSnapshot,
    Recipe,
    parse_estimated_minutes,
    parse_quantity,
    parse_servings_count,
    require_recipe_sections,
)
from planner_core.domain.rules import (
    CategoryCountRule,
    DisabledDay,
    PinRule,
    Rule,
    RuleSet,
    available_days_for_pin,
    available_days_to_disable,
    max_selectable_count,
)
from planner_core.domain.shopping import ShoppingItem
from planner_core.domain.units import parse_unit
from planner_core.ports.accounts import AccountRecord
from planner_core.ports.generation_queue import StoredGeneration


class MalformedRequest(PlannerError):
    """R18 — unparseable JSON, a missing field, a client-supplied id/author, or
    an unparseable path parameter. One code covers all four (design.md's T2)."""

    def __init__(self) -> None:
        super().__init__(messages.MALFORMED_REQUEST)


class RouteNotFound(PlannerError):
    """No `(method, resource)` entry matches - a deployment/routing bug, since
    API Gateway only invokes the Lambda for a configured resource."""

    def __init__(self) -> None:
        super().__init__(messages.ROUTE_NOT_FOUND)


def parse_json_body(raw: str | None) -> dict[str, Any]:
    """An absent body decodes as {} — several routes (logout, resync) take
    none; a present-but-invalid one is R18's malformed-JSON case."""
    if raw is None or raw == "":
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        raise MalformedRequest from None
    if not isinstance(parsed, dict):
        raise MalformedRequest
    return parsed


def reject_keys(body: dict[str, Any], *forbidden: str) -> None:
    """R39 / contract section 3.0 rule 3 — id and author are server-assigned."""
    if any(key in body for key in forbidden):
        raise MalformedRequest


def require_field(body: dict[str, Any], key: str) -> Any:
    if key not in body:
        raise MalformedRequest
    return body[key]


_EMPTY_FIELD_EXCEPTIONS: dict[str, type[PlannerError]] = {
    "name": EmptyName,
    "category": EmptyCategory,
    "ingredient_name": EmptyIngredientName,
    "quantity": EmptyQuantity,
    "unit": EmptyMeasure,
    "tool": EmptyTool,
    "procedure_step": EmptyProcedureStep,
}


def require_non_empty(value: Any, field: str) -> Any:
    """R18-adjacent: a present-but-blank required field names itself (422),
    instead of falling through to the value parser's own rejection or an
    uncaught `float("")` (issue empty-field-error-messages)."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        raise _EMPTY_FIELD_EXCEPTIONS[field]()
    return value


def parse_week_id(value: str) -> IsoWeek:
    """`<isoYear>-W<ww>` (data_model.md section 2). Any failure to parse — not
    just an out-of-range week — is the same 400 in a path (design.md section 4)."""
    try:
        year_str, week_str = value.split("-W", 1)
        return IsoWeek(int(year_str), int(week_str))
    except (ValueError, PlannerError):
        raise MalformedRequest from None


def parse_day(value: str) -> int:
    try:
        day = int(value)
    except ValueError:
        raise MalformedRequest from None
    if day not in range(1, 8):
        raise MalformedRequest
    return day


def parse_slot(value: str) -> MealSlot:
    try:
        return MealSlot(int(value))
    except ValueError:
        raise MalformedRequest from None


def resolve_slot_ref(week: IsoWeek, day: int, slot: MealSlot) -> SlotRef:
    day_by_number = {week_day.day_number: week_day.day for week_day in week.days}
    civil_day = day_by_number.get(day)
    if civil_day is None:
        raise MalformedRequest
    return SlotRef(civil_day, slot)


def encode_ingredient(ingredient: Ingredient) -> dict[str, Any]:
    return {"name": ingredient.name, "quantity": ingredient.quantity, "unit": ingredient.unit.value}


def decode_ingredient(payload: dict[str, Any]) -> Ingredient:
    return Ingredient(
        name=str(require_non_empty(require_field(payload, "name"), "ingredient_name")),
        quantity=parse_quantity(
            float(require_non_empty(require_field(payload, "quantity"), "quantity"))
        ),
        unit=parse_unit(str(require_non_empty(require_field(payload, "unit"), "unit"))),
    )


def encode_recipe(recipe: Recipe | MealSnapshot) -> dict[str, Any]:
    return {
        "name": recipe.name,
        "category": recipe.category.value,
        "servings": recipe.servings,
        "estimatedTime": recipe.estimated_time,
        "ingredients": [encode_ingredient(i) for i in recipe.ingredients],
        "tools": list(recipe.tools),
        "procedure": list(recipe.procedure),
    }


def parse_servings(value: Any) -> int | None:
    """rest_api_contract.md section 3.1: an integer or null, never a string —
    a bad value must 400, not persist an unreadable numeroComensales
    (issue servings-and-time-inputs-not-numeric). A well-formed but
    non-positive integer is a domain rejection (422, InvalidServings),
    same split as parse_estimated_time (G-91, Part AA)."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise MalformedRequest
    return parse_servings_count(value)


def parse_estimated_time(value: Any) -> int | None:
    """G-90: the wrong JSON type is malformed (400, same shape as
    parse_servings); a well-formed integer outside [0, 6000] is a domain
    rejection (422, InvalidEstimatedTime) - issue tiempo-estimado-numeric-minutes."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise MalformedRequest
    return parse_estimated_minutes(value)


def decode_recipe(payload: dict[str, Any]) -> Recipe:
    reject_keys(payload, "id")
    ingredients = tuple(decode_ingredient(i) for i in payload.get("ingredients", []))
    tools = tuple(str(require_non_empty(t, "tool")) for t in payload.get("tools", ()))
    procedure = tuple(
        str(require_non_empty(s, "procedure_step")) for s in payload.get("procedure", ())
    )
    require_recipe_sections(ingredients, tools, procedure)  # G-89, Part Y
    return Recipe(
        name=str(require_non_empty(require_field(payload, "name"), "name")),
        ingredients=ingredients,
        tools=tools,
        procedure=procedure,
        category=parse_category(
            str(require_non_empty(require_field(payload, "category"), "category"))
        ),
        servings=parse_servings(payload.get("servings")),
        estimated_time=parse_estimated_time(payload.get("estimatedTime")),
    )


def encode_candidate(candidate: Candidate) -> dict[str, Any]:
    return {
        "id": candidate.id,
        "author": candidate.author,
        "recipe": encode_recipe(candidate.meal),
    }


def encode_slot_ref(slot: SlotRef) -> dict[str, Any]:
    return {"day": slot.day_number, "slot": int(slot.slot.value)}


def encode_generation(stored: StoredGeneration) -> dict[str, Any]:
    """The GET body (section 3.5): per-slot progress for a whole-week run, the
    decoded result for a single-recipe one. Whole-week runs carry no `result`."""
    if stored.slots is None:
        return {
            "generationId": stored.idempotency_key,
            "status": stored.status,
            "result": decode_generation_result(stored.result),
        }
    slots: list[dict[str, Any]] = []
    for progress in stored.slots:
        entry: dict[str, Any] = {
            "day": progress.day,
            "slot": progress.slot,
            "status": progress.status.value,
        }
        if progress.status is SlotStatus.ERROR and progress.error is not None:
            entry["error"] = {"code": progress.error.code, "message": progress.error.message}
        slots.append(entry)
    return {"generationId": stored.idempotency_key, "status": stored.status, "slots": slots}


def encode_account(account: AccountRecord) -> dict[str, Any]:
    return {
        "userId": account.user_id,
        "username": account.username,
        "role": account.role.value,
        "passwordResetRequired": account.password_reset_required,
    }


def encode_shopping_item(item: ShoppingItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "name": item.name,
        "quantity": item.quantity,
        "unit": item.unit.value,
        "checked": item.checked,
    }


def decode_shopping_item(payload: dict[str, Any], *, item_id: str) -> ShoppingItem:
    reject_keys(payload, "id")
    return ShoppingItem(
        id=item_id,
        name=str(require_non_empty(require_field(payload, "name"), "name")),
        quantity=float(require_field(payload, "quantity")),  # bound: issue 7, not this one
        unit=parse_unit(str(require_non_empty(require_field(payload, "unit"), "unit"))),
    )


def encode_rule(rule: Rule, *, recipe_name: str | None = None) -> dict[str, Any]:
    """`recipe_name` is the pin's read-time-resolved recipe name (AP22,
    docs/rest_api_contract.md section "Rules"); omitted for PUT/DELETE echoes,
    which have no repository read to resolve it from."""
    match rule:
        case CategoryCountRule():
            return {"type": "categoryCount", "category": rule.category.value, "count": rule.count}
        case PinRule():
            payload: dict[str, Any] = {
                "type": "pin",
                "day": rule.day,
                "slot": int(rule.slot.value),
                "recipeId": rule.recipe_id,
            }
            if recipe_name is not None:
                payload["recipeName"] = recipe_name
            return payload
        case DisabledDay():
            return {"type": "disabledDay", "day": rule.day}


def encode_available_options(rule_set: RuleSet) -> dict[str, Any]:
    """R1-R4: one call per already-built pure function (rules_model, feature 6),
    no arithmetic of its own (rest_api_contract.md section 3.7)."""
    return {
        "maxCountByCategory": {
            category.value: max_selectable_count(rule_set, category)
            for category in IngredientCategory
        },
        "daysAvailableForPin": list(available_days_for_pin(rule_set)),
        "daysAvailableToDisable": list(available_days_to_disable(rule_set)),
    }


def decode_rule(payload: dict[str, Any]) -> Rule:
    kind = require_field(payload, "type")
    if kind == "categoryCount":
        return CategoryCountRule(
            category=parse_category(str(require_field(payload, "category"))),
            count=int(require_field(payload, "count")),
        )
    if kind == "pin":
        return PinRule(
            day=int(require_field(payload, "day")),
            slot=parse_slot(str(require_field(payload, "slot"))),
            recipe_id=str(require_field(payload, "recipeId")),
        )
    if kind == "disabledDay":
        return DisabledDay(day=int(require_field(payload, "day")))
    raise MalformedRequest


def decode_rule_override(payload: dict[str, Any] | None) -> RuleOverride | None:
    if payload is None:
        return None
    category_counts = payload.get("categoryCounts")
    pins = payload.get("pins")
    disabled_days = payload.get("disabledDays")
    return RuleOverride(
        category_counts=None
        if category_counts is None
        else tuple(
            CategoryCountRule(category=parse_category(str(c["category"])), count=int(c["count"]))
            for c in category_counts
        ),
        pins=None
        if pins is None
        else tuple(
            PinRule(
                day=int(p["day"]), slot=parse_slot(str(p["slot"])), recipe_id=str(p["recipeId"])
            )
            for p in pins
        ),
        disabled_days=None if disabled_days is None else tuple(int(d) for d in disabled_days),
    )


def parse_generation_mode(value: str) -> GenerationMode:
    try:
        return GenerationMode(value)
    except ValueError:
        raise MalformedRequest from None


def encode_generation_targets(targets: GenerationTargets) -> dict[str, Any]:
    return {
        "openSlots": [encode_slot_ref(s) for s in targets.open_slots],
        "pinnedSlots": [
            {**encode_slot_ref(t.slot), "recipeId": t.recipe_id} for t in targets.pinned_slots
        ],
        "skippedPins": [
            {**encode_slot_ref(s.slot), "recipeId": s.pin.recipe_id} for s in targets.skipped_pins
        ],
    }


def _require_object(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise MalformedRequest
    return payload


def _string_list(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise MalformedRequest
    return tuple(value)


def _decode_slot_target(target: dict[str, Any]) -> SlotRef:
    week = parse_week_id(str(require_field(target, "weekId")))
    day = require_field(target, "day")
    slot = require_field(target, "slot")
    if isinstance(day, bool) or not isinstance(day, int) or day not in range(1, 8):
        raise MalformedRequest
    if isinstance(slot, bool) or not isinstance(slot, int):
        raise MalformedRequest
    return resolve_slot_ref(week, day, parse_slot(str(slot)))


def decode_single_recipe_request(body: dict[str, Any]) -> SingleRecipeRequest:
    """`POST /v1/generations` with `type: "recipe"` (rest_api_contract.md section 3.6).
    `attempt` is server-authoritative, so a client-supplied one is a 400 (section 7 Q3)."""
    reject_keys(body, "attempt")
    target = _require_object(require_field(body, "target"))
    target_kind = require_field(target, "kind")
    if target_kind == "library":
        slot_ref = None
    elif target_kind == "slot":
        slot_ref = _decode_slot_target(target)
    else:
        raise MalformedRequest

    source = _require_object(require_field(body, "source"))
    source_kind = require_field(source, "kind")
    if source_kind == "specification":
        # Absent lists read as empty -> 422, as decode_recipe does (section 4).
        return SingleRecipeRequest(
            slot_ref,
            SpecificationSource(
                ingredients=_string_list(source.get("ingredients", [])),
                tools=_string_list(source.get("tools", [])),
            ),
        )
    if source_kind == "reference":
        recipe_id = require_field(source, "recipeId")
        if not isinstance(recipe_id, str) or recipe_id == "":
            raise MalformedRequest
        extra = _string_list(require_field(source, "extraSpecifications"))
        return SingleRecipeRequest(slot_ref, ReferenceSource(recipe_id, extra))
    raise MalformedRequest


def decode_generation_result(result: str | None) -> Any:
    """A single-recipe result is a JSON object and goes out as one (section 3.6);
    the whole-week per-slot list stays the opaque string it always was."""
    if result is None:
        return None
    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        return result
    return parsed if isinstance(parsed, dict) else result
