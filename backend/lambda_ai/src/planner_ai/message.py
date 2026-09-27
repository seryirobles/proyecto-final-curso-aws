"""Parse an `api`→`ai` SQS message body into the values `run_week_generation`
takes. The body is what `planner_api.adapters.sqs.SqsGenerationQueue.submit`
enriches (specs/rest_api_persistence_and_services/ R40): request identity plus
the resolved effective rules, the prompt-version id and the submitter's id."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from planner_core.application.single_recipe_generation import ReferenceInputs
from planner_core.domain.calendar import IsoWeek, MealSlot
from planner_core.domain.generation import GenerationMode, GenerationRequest, SpecificationSource
from planner_core.domain.ingredient_category import parse_category
from planner_core.domain.rules import CategoryCountRule, PinRule, RuleSet

from planner_ai.serialization import decode_recipe


class MalformedMessage(Exception):
    """Raised when an SQS body is missing a field or carries an unparseable value."""


@dataclass(frozen=True)
class GenerationMessage:
    """The parsed hand-off: everything the worker use case needs, nothing more."""

    idempotency_key: str
    request: GenerationRequest
    effective_rules: RuleSet
    prompt_version_id: str
    author: str


@dataclass(frozen=True)
class RecipeMessage:
    """The parsed single-recipe hand-off (specs/single_recipe_generation R14, R19, R20)."""

    idempotency_key: str
    source: SpecificationSource | ReferenceInputs
    prompt_version_id: str
    author: str


def _require(body: dict[str, Any], key: str) -> Any:
    if key not in body or body[key] is None:
        raise MalformedMessage(key)
    return body[key]


def _parse_week_id(value: str) -> IsoWeek:
    try:
        year_text, week_text = value.split("-W")
        return IsoWeek(int(year_text), int(week_text))
    except (ValueError, TypeError) as exc:
        raise MalformedMessage(f"weekId: {value!r}") from exc


def _parse_rules(payload: dict[str, Any]) -> RuleSet:
    # effectiveRules is required (R40): an un-enriched message must be rejected,
    # not generated against empty rules (specs/ai_lambda/design.md finding 1).
    try:
        return RuleSet(
            category_counts=tuple(
                CategoryCountRule(
                    category=parse_category(str(r["category"])), count=int(r["count"])
                )
                for r in payload.get("categoryCounts", [])
            ),
            pins=tuple(
                PinRule(
                    day=int(p["day"]),
                    slot=MealSlot(int(p["slot"])),
                    recipe_id=str(p["recipeId"]),
                )
                for p in payload.get("pins", [])
            ),
            disabled_days=tuple(int(d) for d in payload.get("disabledDays", [])),
        )
    except (AttributeError, KeyError, ValueError, TypeError) as exc:
        raise MalformedMessage(f"effectiveRules: {exc}") from exc


def parse_message(body: dict[str, Any]) -> GenerationMessage:
    """R1 — one request identified by the `idPeticionIA` the message carries."""
    try:
        mode = GenerationMode(str(_require(body, "mode")))
    except ValueError as exc:
        raise MalformedMessage(f"mode: {body.get('mode')!r}") from exc
    week = _parse_week_id(str(_require(body, "weekId")))
    return GenerationMessage(
        idempotency_key=str(_require(body, "idPeticionIA")),
        request=GenerationRequest(week=week, mode=mode, rule_override=None),
        effective_rules=_parse_rules(_require(body, "effectiveRules")),
        prompt_version_id=str(_require(body, "promptVersionId")),
        author=str(_require(body, "authorUserId")),
    )


def message_type(body: dict[str, Any]) -> str:
    """Whole-week messages predate the `type` field, so absent means `week`."""
    return str(body.get("type", "week"))


def _string_tuple(payload: dict[str, Any], key: str) -> tuple[str, ...]:
    value = _require(payload, key)
    if not isinstance(value, list):
        raise MalformedMessage(key)
    return tuple(str(item) for item in value)


def parse_recipe_message(body: dict[str, Any]) -> RecipeMessage:
    """A `type: "recipe"` body; the reference recipe snapshot travels on it (R20)."""
    source = _require(body, "source")
    if not isinstance(source, dict):
        raise MalformedMessage("source")
    parsed: SpecificationSource | ReferenceInputs
    if source.get("kind") == "specification":
        parsed = SpecificationSource(
            ingredients=_string_tuple(source, "ingredients"), tools=_string_tuple(source, "tools")
        )
    elif source.get("kind") == "reference":
        try:
            recipe = decode_recipe(_require(body, "referenceRecipe"))
        except (AttributeError, KeyError, ValueError, TypeError) as exc:
            raise MalformedMessage(f"referenceRecipe: {exc}") from exc
        parsed = ReferenceInputs(recipe, _string_tuple(source, "extraSpecifications"))
    else:
        raise MalformedMessage(f"source.kind: {source.get('kind')!r}")
    return RecipeMessage(
        idempotency_key=str(_require(body, "idPeticionIA")),
        source=parsed,
        prompt_version_id=str(_require(body, "promptVersionId")),
        author=str(_require(body, "authorUserId")),
    )
