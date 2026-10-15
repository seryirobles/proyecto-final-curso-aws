"""Issue ai-week-dishes-still-similar: the newest prompt widens the avoid line,
adds a positive variety steer after the list, and drops the empty-needs line;
v1-v5 render byte-identical (G-95, FR-AI-06, FR-AI-14). No live call."""

from __future__ import annotations

import hashlib
import re

import pytest
from planner_core.domain.ai_prompt import (
    PROMPT_INSTRUCTION_VERSIONS,
    build_category_prompt,
    build_reference_prompt,
    build_specification_prompt,
)
from planner_core.domain.ingredient_category import IngredientCategory
from planner_core.domain.recipe import Ingredient, Recipe
from planner_core.domain.rules import CategoryCountRule
from planner_core.domain.units import parse_unit
from planner_core.ports.ai_provider import AiPrompt

from planner_ai.adapters.bedrock import _render

LATEST = list(PROMPT_INSTRUCTION_VERSIONS)[-1]  # append-only registry (R2)
AVOID = (
    "Budín de Calabaza con Quinoa y Yogur de Chía",
    "Budín de Calabacín con Quinoa y Yogur de Chía",
    "Lasaña de Verduras con Tofu y Quinoa",
)
NEEDS = (CategoryCountRule(category=IngredientCategory.LEGUME, count=2),)
_REFERENCE = Recipe(
    name="Tortilla de patatas",
    ingredients=(Ingredient(name="patata", quantity=500, unit=parse_unit("g")),),
    tools=("sarten",),
    procedure=("Freir la patata.", "Cuajar con el huevo."),
    category=IngredientCategory.CARBOHYDRATE,
)


def _cases(version_id: str) -> dict[str, AiPrompt]:
    return {
        "needs": build_category_prompt(NEEDS, version_id),
        "empty_needs": build_category_prompt((), version_id),
        "avoid": build_category_prompt(NEEDS, version_id, AVOID),
        "avoid_empty_needs": build_category_prompt((), version_id, AVOID),
        "specification": build_specification_prompt(("arroz",), ("olla",), version_id),
        "reference": build_reference_prompt(_REFERENCE, ("sin gluten",), version_id),
    }


# sha256 of _render output at triage (2026-10-12); retired wording never changes.
GOLDEN: dict[str, str] = {
    "v1/needs": "27634ac709f6b66bd92227ed107dd746f85f9bc0430d78c066760d729b4855db",
    "v1/empty_needs": "bc9f522a2b7a91918692df187e79cde3f076d144d97cd543c4f9605c132ca2d7",
    "v1/avoid": "27634ac709f6b66bd92227ed107dd746f85f9bc0430d78c066760d729b4855db",
    "v1/avoid_empty_needs": "bc9f522a2b7a91918692df187e79cde3f076d144d97cd543c4f9605c132ca2d7",
    "v1/specification": "306a900955dce6d04530da3f6a1b54a5d4c77a5bed61edd02114764ebd3000e1",
    "v1/reference": "5a019057d189c73f39f9b675448742f4308565fa92a475bf1ed0227e539e6409",
    "v2/needs": "2ac0a0d7686b8a3e71c205baf88d3472298235ca709b379661284c335a81f6f5",
    "v2/empty_needs": "ee5866d595fdf88817746dcc00e0b48958531e8709c2a7e108545880e488b143",
    "v2/avoid": "2ac0a0d7686b8a3e71c205baf88d3472298235ca709b379661284c335a81f6f5",
    "v2/avoid_empty_needs": "ee5866d595fdf88817746dcc00e0b48958531e8709c2a7e108545880e488b143",
    "v2/specification": "9599468341be5336e1f835d52324c080ddb04f346ff061edac5ad4df9b451ce1",
    "v2/reference": "d8bb8840e6c02397aaee9e6a0940ca05afdfe8ff1fc44d0a94b28421fccdef69",
    "v3/needs": "89fa0e4182bb81f80c9a5c79c8bdb517d2229c006f0662f5c5325fa96c120c82",
    "v3/empty_needs": "e4475aa432b433e38569bade703cb28aab44ef9531b28f646564ed77a9f2cca5",
    "v3/avoid": "89fa0e4182bb81f80c9a5c79c8bdb517d2229c006f0662f5c5325fa96c120c82",
    "v3/avoid_empty_needs": "e4475aa432b433e38569bade703cb28aab44ef9531b28f646564ed77a9f2cca5",
    "v3/specification": "faaa10a6fc3416f8f0f45f9f05e31fc27003442322002d0a1b8df89d9c1ed564",
    "v3/reference": "34922924eed22970c8fab0e6e4127c1c2526601ab48da73696772828a95b1831",
    "v4/needs": "3be104b3fab73f2e5e2080c88044984b8237e5847660519132b0e25515272a8b",
    "v4/empty_needs": "d3ee22a628e81fd2a63eb3737738cc914926a6a9d1c3c0516d25f47298ed5ced",
    "v4/avoid": "3be104b3fab73f2e5e2080c88044984b8237e5847660519132b0e25515272a8b",
    "v4/avoid_empty_needs": "d3ee22a628e81fd2a63eb3737738cc914926a6a9d1c3c0516d25f47298ed5ced",
    "v4/specification": "cfb7e1bbe7bcc28d9a12fc377693f213e511fa4bab5cc6003af4062d75c07d48",
    "v4/reference": "8c3fe30ad52b39f60a3bb508cd80ae3bc1f55f8cee3d218f494efd7b3b75f5d7",
    "v5/needs": "3be104b3fab73f2e5e2080c88044984b8237e5847660519132b0e25515272a8b",
    "v5/empty_needs": "d3ee22a628e81fd2a63eb3737738cc914926a6a9d1c3c0516d25f47298ed5ced",
    "v5/avoid": "675f3dbfbb49d97f7546731a5019d5743b143177bae3ec87d90cf4d19ad22544",
    "v5/avoid_empty_needs": "357dc7fe85826801793cd21ec3d3b9970d2e95c8d423933546500800a6339e7b",
    "v5/specification": "cfb7e1bbe7bcc28d9a12fc377693f213e511fa4bab5cc6003af4062d75c07d48",
    "v5/reference": "8c3fe30ad52b39f60a3bb508cd80ae3bc1f55f8cee3d218f494efd7b3b75f5d7",
}


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_v6_is_the_newest_prompt_version() -> None:
    """E5."""
    assert LATEST == "v6"


@pytest.mark.parametrize("version_id", ["v1", "v2", "v3", "v4", "v5"])
def test_retired_versions_render_byte_identical(version_id: str) -> None:
    """E5 — regression: v1-v5 untouched (FR-AI-14)."""
    rendered = {case: _digest(_render(p)) for case, p in _cases(version_id).items()}
    expected = {case: GOLDEN[f"{version_id}/{case}"] for case in rendered}
    assert rendered == expected


def test_every_avoided_name_still_reaches_the_model() -> None:
    """E1 — regression of G-95 decision (1)."""
    text = _render(build_category_prompt(NEEDS, LATEST, AVOID))
    assert [name for name in AVOID if name not in text] == []


def test_the_avoid_instruction_covers_main_ingredient_and_style() -> None:
    """E2 — reproduction: v5 avoids names only."""
    text = _render(build_category_prompt(NEEDS, LATEST, AVOID)).casefold()
    assert "main ingredient" in text
    assert "style" in text


def test_a_positive_variety_steer_follows_the_avoided_names() -> None:
    """E3 — the list is not the last dish content the model reads."""
    text = _render(build_category_prompt(NEEDS, LATEST, AVOID))
    list_end = max(text.rindex(name) + len(name) for name in AVOID)
    assert "cuisine" in text[list_end:].casefold()


@pytest.mark.parametrize("avoid", [(), AVOID], ids=["first_slot", "later_slot"])
def test_empty_needs_render_no_dangling_line(avoid: tuple[str, ...]) -> None:
    """E4 — reproduction: v5 renders "remaining needs: ." with no rules."""
    text = _render(build_category_prompt((), LATEST, avoid))
    assert [line for line in text.splitlines() if re.search(r":\s*\.\s*$", line)] == []


def test_needs_still_render_when_present() -> None:
    """E4 — regression: a category rule still reaches the model."""
    text = _render(build_category_prompt(NEEDS, LATEST))
    assert "2x legume" in text
