"""The single name fold behind ingredient matching: case, accent and trim insensitive."""

from __future__ import annotations

import unicodedata
from typing import Final

# The tilde of Spanish n is a letter, not an accent
# (G-56, specs/text_and_units/design.md section 5.3).
COMBINING_TILDE: Final = "\u0303"


def _is_removable_mark(character: str) -> bool:
    return character != COMBINING_TILDE and unicodedata.category(character).startswith("M")


def normalize(name: str) -> str:
    """Return the matching form of an ingredient name (FR-SHOP-03).

    Total: every string maps to a string, a blank name maps to the empty string,
    and nothing is raised. The result is the merge key for shopping aggregation
    and the fold behind the username reservation key (docs/data_model.md section
    2), so it is declared once here and never re-derived at a call site.

    Deliberately not: no stemming, no singular/plural folding, no synonym
    matching (G-56), no internal whitespace collapsing, and no rewriting of the
    display name the user actually typed.
    """
    # Step order is not load-bearing on our domain
    # (specs/text_and_units/design.md section 5.1).
    decomposed = unicodedata.normalize("NFD", name.strip().casefold())
    kept = "".join(character for character in decomposed if not _is_removable_mark(character))
    return unicodedata.normalize("NFC", kept)
