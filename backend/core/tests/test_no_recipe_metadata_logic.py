"""Source scan: no domain logic anywhere reads servings or estimated_time.

R21, R22 are negative claims about the whole planner_core package, so no
single call site can prove them; a scan of the sources is the only way to
make them verifiable — the same discipline test_no_ambient_time.py already
established for the Clock port's default implementation (docs/architecture.md
section 1.2.2). R18-R20 (no deployment-wide servings target survives, under
any name) are proven structurally via dataclasses.fields() rather than by
text alone.

specs/recipe_metadata_fields/design.md section 7 is the authority on this
scan's exact shape; it is deliberately not paraphrased further here.
"""

from __future__ import annotations

import ast
import dataclasses
import re
from pathlib import Path

from planner_core.domain.ai_prompt import PromptInstructions, PromptInstructionsVersion

TESTS_ROOT = Path(__file__).resolve().parent
CORE_SRC = TESTS_ROOT.parent / "src" / "planner_core"

RECIPE_SOURCE = CORE_SRC / "domain" / "recipe.py"
AI_OUTPUT_SOURCE = CORE_SRC / "domain" / "ai_output.py"
CANDIDATE_SOURCE = CORE_SRC / "domain" / "candidate.py"
AI_PROMPT_SOURCE = CORE_SRC / "domain" / "ai_prompt.py"

# recipe.py and ai_output.py exist only to declare or pass through the two
# fields, so a whole-module exemption is safe (design.md section 7).
FULLY_EXEMPT_MODULES = (RECIPE_SOURCE, AI_OUTPUT_SOURCE)

# candidate.py is general-purpose (Candidate, SlotContents, promote,
# summary...); only these two exact lines inside to_library_entry have a
# legitimate reason to name either field.
CANDIDATE_SANCTIONED_LINES = (
    re.compile(r"\s*servings=meal\.servings,"),
    re.compile(r"\s*estimated_time=meal\.estimated_time,"),
)

# ai_prompt.py's JSON_OUTPUT_INSTRUCTION names the model's output-schema keys as
# versioned prompt text, not domain logic (FR-AI-14 / G-84). A reword must land
# as a new prompt version; see progress/impl_ai_prompt_versioning.md for the v2 history.
AI_PROMPT_SANCTIONED_LINES = (
    re.compile(r'\s*"procedure \(lista de str\), category \(str\), servings \(int\|null\), "'),
    re.compile(r'\s*"estimated_time \(str\|null\)\. Sin texto adicional\."'),
    re.compile(r'\s*"procedure \(list of str\), category \(str\), servings \(int\|null\), "'),
    re.compile(r'\s*"estimated_time \(str\|null\)\. No additional text\."'),
    # v3 (issue tiempo-estimado-numeric-minutes, G-90): estimated_time becomes
    # an integer minute count; worded so neither line repeats v2's verbatim.
    re.compile(r'\s*"procedure \(list of str\), category \(str\), servings \(int\|null\); "'),
    re.compile(
        r'\s*"estimated_time \(int\|null, whole minutes from 0 to 6000 inclusive\)\. '
        r'No additional text\."'
    ),
)

INFORMATIONAL_METADATA = re.compile(r"\bservings\b|\bestimated_time\b")


def _annotation_names_int(annotation: ast.expr | None) -> bool:
    """True for `int` or `Final[int]` - a rename defeats a literal-text
    check, so R18 is enforced structurally instead (reviewer finding)."""
    if isinstance(annotation, ast.Name):
        return annotation.id == "int"
    if isinstance(annotation, ast.Subscript):
        return _annotation_names_int(annotation.slice)
    return False


def _module_level_int_constants(source: Path) -> list[str]:
    """Every top-level `NAME: int = ...` / `NAME: Final[int] = ...` /
    `NAME = <int literal>` in source, by name - ai_prompt.py's only
    legitimate top-level constants are all non-int (design.md section 6)."""
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    offenders: list[str] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if _annotation_names_int(node.annotation):
                offenders.append(node.target.id)
        elif isinstance(node, ast.Assign):
            value = node.value
            is_int_literal = (
                isinstance(value, ast.Constant)
                and isinstance(value.value, int)
                and not isinstance(value.value, bool)
            )
            if is_int_literal:
                offenders.extend(t.id for t in node.targets if isinstance(t, ast.Name))
    return offenders


def _offenders(sources: list[Path]) -> list[str]:
    offences: list[str] = []
    for source in sources:
        if source in FULLY_EXEMPT_MODULES:
            continue
        for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
            if source == CANDIDATE_SOURCE and any(
                p.fullmatch(line) for p in CANDIDATE_SANCTIONED_LINES
            ):
                continue
            if source == AI_PROMPT_SOURCE and any(
                p.fullmatch(line) for p in AI_PROMPT_SANCTIONED_LINES
            ):
                continue
            found = INFORMATIONAL_METADATA.search(line)
            if found:
                offences.append(f"{source}:{number}: {found.group(0)}")
    return offences


def test_the_informational_metadata_pattern_detects_what_it_claims_to() -> None:
    """A scan that matches nothing proves nothing: check the pattern first."""
    for banned in ("servings", "estimated_time", "raw.servings", "servings=meal.servings,"):
        assert INFORMATIONAL_METADATA.search(banned), banned

    assert not INFORMATIONAL_METADATA.search("# nothing relevant here")


def test_the_candidate_sanctioned_lines_exist_verbatim() -> None:
    """The exemption cannot quietly become a hole covering nothing (R21, R22)."""
    lines = CANDIDATE_SOURCE.read_text(encoding="utf-8").splitlines()

    for pattern in CANDIDATE_SANCTIONED_LINES:
        matching = [line for line in lines if pattern.fullmatch(line)]
        assert len(matching) == 1, (pattern.pattern, matching)


def test_the_ai_prompt_sanctioned_lines_exist_verbatim() -> None:
    """finding 6: the exemption tracks the JSON_OUTPUT_INSTRUCTION wording exactly,
    so a reword fails here and forces a prompt-version bump (FR-AI-14 / G-84)."""
    lines = AI_PROMPT_SOURCE.read_text(encoding="utf-8").splitlines()

    for pattern in AI_PROMPT_SANCTIONED_LINES:
        matching = [line for line in lines if pattern.fullmatch(line)]
        assert len(matching) == 1, (pattern.pattern, matching)


def test_no_planner_core_module_reads_servings_or_estimated_time_outside_the_sanctioned_sites() -> (
    None
):
    """R21, R22: only recipe.py, ai_output.py and candidate.py's two copy
    lines may name either field."""
    sources = sorted(CORE_SRC.rglob("*.py"))

    assert sources, f"no planner_core sources found under {CORE_SRC}"
    assert CORE_SRC / "domain" / "shopping.py" in sources
    assert CORE_SRC / "domain" / "rules.py" in sources
    assert CORE_SRC / "domain" / "generation.py" in sources
    assert CANDIDATE_SOURCE in sources

    assert _offenders(sources) == []


def test_prompt_instructions_declares_no_servings_field() -> None:
    """R19: PromptInstructions no longer carries a deployment-config servings target."""
    assert "servings" not in {f.name for f in dataclasses.fields(PromptInstructions)}


def test_prompt_instructions_version_declares_no_servings_field() -> None:
    """R20: PromptInstructionsVersion no longer carries a deployment-config servings target."""
    assert "servings" not in {f.name for f in dataclasses.fields(PromptInstructionsVersion)}


def test_configured_servings_no_longer_appears_anywhere_in_ai_prompt() -> None:
    """R18 (narrow): the old name specifically is gone, not merely unused.

    Does not catch a rename - test_ai_prompt_declares_no_top_level_int_constant
    below is the structural check that does."""
    assert not INFORMATIONAL_METADATA.search("CONFIGURED_SERVINGS"), "self-test: pattern too broad"
    source_text = AI_PROMPT_SOURCE.read_text(encoding="utf-8")
    assert "CONFIGURED_SERVINGS" not in source_text


def test_ai_prompt_declares_no_top_level_int_constant() -> None:
    """R18: no module-level int constant survives under any name - a rename
    of CONFIGURED_SERVINGS would still be a deployment-wide servings target."""
    assert _module_level_int_constants(AI_PROMPT_SOURCE) == []


def test_the_int_constant_scan_catches_a_renamed_deployment_config_constant(
    tmp_path: Path,
) -> None:
    """The reviewer's mutant: renaming CONFIGURED_SERVINGS must not defeat the guard."""
    annotated = tmp_path / "mutant_annotated.py"
    annotated.write_text(
        "from typing import Final\n\nDEFAULT_SERVINGS: Final[int] = 4\n", encoding="utf-8"
    )
    assert _module_level_int_constants(annotated) == ["DEFAULT_SERVINGS"]

    bare = tmp_path / "mutant_bare.py"
    bare.write_text("DEFAULT_SERVINGS = 4\n", encoding="utf-8")
    assert _module_level_int_constants(bare) == ["DEFAULT_SERVINGS"]

    non_int = tmp_path / "not_a_mutant.py"
    non_int.write_text(
        'from typing import Final\n\nFLAG: Final[bool] = True\nNAME: Final[str] = "x"\n',
        encoding="utf-8",
    )
    assert _module_level_int_constants(non_int) == []
