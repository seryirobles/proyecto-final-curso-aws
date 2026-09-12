"""`conditional_get.parse_if_none_match`: R6's leniency table."""

from __future__ import annotations

import pytest

from planner_api.conditional_get import parse_if_none_match


@pytest.mark.parametrize(
    ("header_value", "expected"),
    [
        ('"41"', 41),
        ('"0"', 0),
        (None, None),
        ("*", None),
        ('"41", "42"', None),
        ("41", None),
        ('"not-a-number"', None),
        ("", None),
    ],
)
def test_parse_if_none_match_only_accepts_a_single_quoted_integer(
    header_value: str | None, expected: int | None
) -> None:
    assert parse_if_none_match(header_value) == expected
