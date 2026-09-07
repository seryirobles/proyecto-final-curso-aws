"""Parsing the enriched api->ai SQS message body (R1; message enrichment
specs/rest_api_persistence_and_services/ R40)."""

from __future__ import annotations

import dataclasses

import pytest

from planner_ai.message import GenerationMessage, MalformedMessage, parse_message


def _body(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "idPeticionIA": "hash-1",
        "weekId": "2026-W34",
        "mode": "mix",
        "promptVersionId": "v1",
        "authorUserId": "u-7",
        "effectiveRules": {
            "categoryCounts": [{"category": "vegetable", "count": 2}],
            "pins": [{"day": 1, "slot": 1, "recipeId": "r-1"}],
            "disabledDays": [6],
        },
    }
    base.update(overrides)
    return base


def test_generation_message_is_frozen() -> None:
    message = parse_message(_body())
    with pytest.raises(dataclasses.FrozenInstanceError):
        message.__setattr__("author", "someone-else")


def test_a_full_body_parses_to_every_worker_input() -> None:
    message = parse_message(_body())

    assert isinstance(message, GenerationMessage)
    assert message.idempotency_key == "hash-1"
    assert message.request.week.week_id == "2026-W34"
    assert message.prompt_version_id == "v1"
    assert message.author == "u-7"
    assert message.effective_rules.disabled_days == (6,)
    assert message.effective_rules.pins[0].recipe_id == "r-1"
    assert message.effective_rules.category_counts[0].count == 2


def test_a_message_with_no_effective_rules_key_is_rejected() -> None:
    """finding 1 (R40): a message that lost its enrichment must not generate
    against empty rules — the worker never reaches the provider."""
    body = _body()
    del body["effectiveRules"]
    with pytest.raises(MalformedMessage):
        parse_message(body)


@pytest.mark.parametrize(
    "overrides",
    [
        {"weekId": "nonsense"},
        {"mode": "sideways"},
        {"idPeticionIA": None},
        {"promptVersionId": None},
        {"effectiveRules": None},
    ],
)
def test_a_malformed_field_raises(overrides: dict[str, object]) -> None:
    with pytest.raises(MalformedMessage):
        parse_message(_body(**overrides))
