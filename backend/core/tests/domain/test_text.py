"""Tests for the shared name fold (R3-R13).

Every input and expected output is taken verbatim from
`specs/text_and_units/design.md` section 8.1. Accented characters appear here as
literal test data on purpose: the source module is ASCII-only (R22), so the
accents the fold exists to handle can only be exercised from this side.

The codepoints that do not render as themselves -- the non-breaking space, the
decomposed acute and tilde, and the Turkish dotted capital I -- are built with
`chr()` rather than pasted, so which codepoint is meant does not depend on the
reader's editor.
"""

from __future__ import annotations

from planner_core.domain.text import normalize

NON_BREAKING_SPACE = chr(0xA0)
COMBINING_ACUTE = chr(0x0301)
COMBINING_DOT_ABOVE = chr(0x0307)
COMBINING_TILDE = chr(0x0303)
DOTTED_CAPITAL_I = chr(0x0130)
LATIN_SMALL_N_WITH_TILDE = chr(0xF1)


def test_normalize_strips_surrounding_whitespace() -> None:
    """R3: leading and trailing whitespace never reaches the merge key."""
    assert normalize("tomate ") == "tomate"
    assert normalize("  Jamón  ") == "jamon"

    # Names get pasted from web recipes, and str.strip() removes U+00A0 too.
    assert normalize(NON_BREAKING_SPACE + "jamón" + NON_BREAKING_SPACE) == "jamon"


def test_normalize_keeps_whitespace_inside_the_name() -> None:
    """R4: FR-SHOP-03 says leading and trailing only; collapsing is a future refinement."""
    assert normalize("tomate  cherry") == "tomate  cherry"


def test_normalize_folds_case() -> None:
    """R5: the display name keeps the user's casing, the key does not."""
    assert normalize("Tomate") == "tomate"


def test_normalize_folds_the_written_accent_and_the_diaeresis() -> None:
    """R6: the acute on vowels and the diaeresis fold onto the base letter."""
    assert normalize("tomáte") == "tomate"
    assert normalize("Pingüino") == "pinguino"

    # Decomposed input, as it arrives from macOS and from some web sources.
    assert normalize("jamo" + COMBINING_ACUTE + "n") == "jamon"

    # Verifies R6: U+0130 folds to a bare "i", with no combining dot left over.
    # Not a step-order regression test -- the two orderings are equivalent on
    # this domain; see the sweep in specs/text_and_units/design.md section 5.1.
    folded = normalize(DOTTED_CAPITAL_I)

    assert folded == "i"
    assert len(folded) == 1
    assert COMBINING_DOT_ABOVE not in folded


def test_normalize_keeps_the_tilde_of_ene() -> None:
    """R7: the tilde is part of a distinct letter, so piña and pina stay two keys."""
    folded = normalize("Piña")

    assert folded == "piña"
    assert len(folded) == 4
    assert folded[2] == LATIN_SMALL_N_WITH_TILDE

    assert normalize("pina") == "pina"
    assert normalize("Piña") != normalize("pina")

    assert normalize("año") == "año"
    assert normalize("ano") == "ano"
    assert normalize("año") != normalize("ano")


def test_normalize_returns_composed_form() -> None:
    """R8: NFC, so a decomposed and a precomposed spelling produce one key, not two."""
    decomposed = normalize("Pin" + COMBINING_TILDE + "a")

    assert decomposed == normalize("Piña")
    assert len(decomposed) == 4
    assert COMBINING_TILDE not in decomposed


def test_normalize_of_a_blank_name_is_the_empty_string() -> None:
    """R9: total function. Whether a blank name is acceptable belongs to features 4 and 8."""
    assert normalize("") == ""
    assert normalize("   ") == ""


def test_normalize_does_not_fold_plurals() -> None:
    """R10: G-56 stops at what can be normalized losslessly."""
    assert normalize("tomates") == "tomates"
    assert normalize("tomates") != normalize("tomate")


def test_normalize_does_not_stem() -> None:
    """R11: G-56 names 'tomate cherry' vs 'tomatitos' as the case it refuses."""
    assert normalize("tomatitos") == "tomatitos"
    assert normalize("tomatitos") != normalize("tomate")


def test_normalize_does_not_match_synonyms() -> None:
    """R12: G-74 depends on this refusal; adding it reopens a removed requirement."""
    assert normalize("papa") == "papa"
    assert normalize("patata") == "patata"
    assert normalize("papa") != normalize("patata")


def test_the_three_spellings_of_tomate_share_one_key() -> None:
    """R13: the feature_list.json criterion, and the G-56 row of docs/verification.md."""
    keys = {normalize("Tomate"), normalize("tomate "), normalize("tomáte")}

    assert len(keys) == 1
    assert keys == {"tomate"}
