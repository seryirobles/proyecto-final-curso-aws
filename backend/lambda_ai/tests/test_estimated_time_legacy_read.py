"""Issue 11 (E8): the AI Lambda's own copy of the recipe-content mapper reads
`tiempo` the same way as the API Lambda's — a minute count, and a value stored
as free text before `G-90` reads back as absent instead of raising."""

from __future__ import annotations

from decimal import Decimal

from planner_ai.adapters.dynamo import _meal


def test_reading_a_numeric_tiempo_gives_the_minute_count() -> None:
    assert _meal.read_estimated_time({"tiempo": Decimal(30)}) == 30
    assert _meal.read_estimated_time({"tiempo": 30}) == 30


def test_reading_a_legacy_free_text_tiempo_reads_as_absent_and_never_raises() -> None:
    assert _meal.read_estimated_time({"tiempo": "30 min"}) is None


def test_reading_an_absent_tiempo_is_still_none() -> None:
    assert _meal.read_estimated_time({}) is None
    assert _meal.read_estimated_time({"tiempo": None}) is None
