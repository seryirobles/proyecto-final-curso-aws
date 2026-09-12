"""`If-None-Match` parsing for the conditional-GET short-circuit (feature 26,
R1-R7). Pure — no port access, no business logic."""

from __future__ import annotations

import re

_SINGLE_QUOTED_DIGITS = re.compile(r'^"(\d+)"$')


def parse_if_none_match(header_value: str | None) -> int | None:
    """A single `"<digits>"` value -> the int. Anything else (absent, `*`, a
    comma-separated list, unquoted, non-numeric) -> `None` — R6's "never
    wrong, only slower" fallback (rest_api_contract.md section 6)."""
    if header_value is None:
        return None
    match = _SINGLE_QUOTED_DIGITS.match(header_value.strip())
    return int(match.group(1)) if match else None
