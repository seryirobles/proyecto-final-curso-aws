# text_and_units — Tasks

> Execute in order. Tick `[x]` as each completes.
> The concrete inputs and expected outputs are in `design.md` §8 — use **those
> exact values**, do not invent new ones.
> Read `design.md` §5.1 before writing `normalize` (the step order is *not*
> load-bearing — corrected 2026-08-23), and §5.3 before touching the `ñ` rule,
> which **is**.

## Domain — sources

- [x] T1 — Add `normalize(name: str) -> str` in
  `backend/core/src/planner_core/domain/text.py`. Four steps in this order:
  `strip()`, `casefold()`, NFD-decompose and drop every combining mark except
  `U+0303`, NFC-recompose. Standard library only (`unicodedata`), no non-ASCII
  literal anywhere in the module, and one comment recording *why* `casefold()`
  precedes mark removal (`design.md` §5.1 — `"İ".casefold()` introduces a
  combining mark). Covers: R1, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13.
- [x] T2 — Add `Unit(StrEnum)` with exactly `GRAM = "g"`,
  `MILLILITRE = "ml"`, `UNIT = "unit"` in
  `backend/core/src/planner_core/domain/units.py`. No other member, no factor or
  ratio attribute, no conversion helper. Covers: R14, R15, R21.
- [x] T3 — In the same module, add `UnknownUnit(PlannerError)` — importing
  `PlannerError` from `planner_core.domain.errors` — storing the rejected value
  on `self.value`, and `parse_unit(value: str) -> Unit` matching a member's code
  **exactly**: no case folding, no `strip()`, no call to `normalize`
  (`design.md` §9 D and E). Covers: R17, R18, R19, R20.

## Tests — `normalize` (`backend/core/tests/domain/test_text.py`)

- [x] T4 — `test_normalize_strips_surrounding_whitespace` — `"tomate "` and
  `"  Jamón  "`, plus the non-breaking-space pair of `design.md` §8.1. Covers:
  R3.
- [x] T5 — `test_normalize_keeps_whitespace_inside_the_name` — `"tomate  cherry"`
  keeps **both** spaces. Covers: R4.
- [x] T6 — `test_normalize_folds_case` — `"Tomate"` → `"tomate"`. Covers: R5.
- [x] T7 — `test_normalize_folds_the_written_accent_and_the_diaeresis` —
  `"tomáte"` → `"tomate"`, `"Pingüino"` → `"pinguino"`, and the decomposed
  `"jamón"` → `"jamon"`. Include the `"İ"` → `"i"` case. Covers: R6.
  *(Corrected 2026-08-23: this task originally called the `"İ"` value "the
  regression test for the step order of `design.md` §5.1". It is not — the two
  orderings are equivalent on this feature's domain, verified exhaustively over
  `U+0000`–`U+2FFFF`. The value still tests R6; it just does not pin an
  ordering. See `design.md` §5.1 as corrected.)*
- [x] T8 — `test_normalize_keeps_the_tilde_of_ene` — `"Piña"` → `"piña"`;
  `normalize("Piña") != normalize("pina")`; `normalize("año") !=
  normalize("ano")`. Assert the surviving codepoint is `U+00F1` and the result
  has length 4, not merely that the two differ. Covers: R7.
- [x] T9 — `test_normalize_returns_composed_form` — build the input as
  `"Pin" + chr(0x0303) + "a"` and assert it normalizes to the **same** value as
  the precomposed `"Piña"`, of length 4. Covers: R8.
- [x] T10 — `test_normalize_of_a_blank_name_is_the_empty_string` — `""` and
  `"   "`. Covers: R9.
- [x] T11 — `test_normalize_does_not_fold_plurals` — `normalize("tomates")`
  equals `"tomates"` and differs from `normalize("tomate")`. Covers: R10.
- [x] T12 — `test_normalize_does_not_stem` — `normalize("tomatitos")` equals
  `"tomatitos"`, unchanged and distinct from `normalize("tomate")`. Covers: R11.
- [x] T13 — `test_normalize_does_not_match_synonyms` — `"papa"` and `"patata"`
  each normalize to themselves and differ from each other. Covers: R12.
- [x] T14 — `test_the_three_spellings_of_tomate_share_one_key` — `"Tomate"`,
  `"tomate "` and `"tomáte"` all give `"tomate"`, asserted as a
  three-element set of size one. This is the `feature_list.json` acceptance
  criterion and the `docs/verification.md` Level 4 row for `G-56`. Covers: R13.

## Tests — units (`backend/core/tests/domain/test_units.py`)

- [x] T15 — `test_the_unit_vocabulary_is_closed` — `[u.value for u in Unit]`
  equals `["g", "ml", "unit"]` exactly, and the member names are exactly
  `GRAM`, `MILLILITRE`, `UNIT`. Covers: R14, R15.
- [x] T16 — `test_parse_unit_resolves_every_code` — `"g"`, `"ml"` and `"unit"`
  give `Unit.GRAM`, `Unit.MILLILITRE`, `Unit.UNIT`. Covers: R17.
- [x] T17 — `test_parse_unit_rejects_a_value_outside_the_list` — `"G"`, `" g"`,
  `"gramos"`, `"kg"` and `""` each raise `UnknownUnit`. `"kg"` is the deliberate
  exclusion of `design.md` §4; `"G"` and `" g"` are the deliberate strictness of
  §9 D. Covers: R18.
- [x] T18 — `test_unknown_unit_is_a_planner_error` — assert the lineage
  (`issubclass(UnknownUnit, PlannerError)`) **and** that a real
  `parse_unit("gramos")` raise is caught by `except PlannerError`, so the
  handler layer can catch the family by its base. Covers: R19.
- [x] T19 — `test_unknown_unit_carries_the_rejected_value` — `exc.value` equals
  `"gramos"` and `"G"` respectively, byte for byte. Covers: R20.
- [x] T20 — `test_the_units_module_exposes_no_conversion` — the module's public
  names are exactly `{"Unit", "UnknownUnit", "parse_unit"}`, and no `Unit`
  member carries a factor, ratio or base-unit attribute. Covers: R21.

## Tests — mechanical guards (`backend/core/tests/test_shared_kernel_guards.py`)

> Build these to the discipline of `backend/core/tests/test_no_ambient_time.py`
> tasks T44 and T46: each scan asserts its own pattern matches the exempt
> module, and asserts the scanned file list is non-empty and contains named
> modules — so no guard can pass by matching nothing. `design.md` §7 gives the
> patterns and the exemptions.

- [x] T21 — `test_planner_core_has_one_name_fold` — no `.py` under
  `src/planner_core` other than `domain/text.py` contains `unicodedata`,
  `casefold` or `.lower()`. Self-test: the pattern matches inside
  `domain/text.py`; the scanned list is non-empty and includes
  `domain/units.py` and `domain/calendar.py`. Covers: R1, R2.
- [x] T22 — `test_planner_core_has_one_unit_vocabulary` — no `.py` under
  `src/planner_core` other than `domain/units.py` declares a class whose name
  contains `Unit` or assigns `GRAM`, `MILLILITRE`, `LITRE` or `KILOGRAM`.
  Self-test as in T21. Covers: R16.
- [x] T23 — `test_the_shared_kernel_modules_are_ascii_only` — `domain/text.py`
  and `domain/units.py` contain no non-ASCII codepoint. Assert the scanned list
  is exactly those two files, so the guard cannot rot into covering nothing.
  Covers: R22.

## Anti-hollow-green — the mutation battery

- [x] T24 — Run the mutations below. For each: apply it, run
  `uv run pytest -q` from `backend/`, record the failing test, then restore the
  file and **verify the restore by SHA-256 against the hash taken before the
  mutation** (the method `progress/impl_week_calendar.md` §4 established). A
  mutation that does not turn a test red is a hole in the suite, not a passing
  grade — fix the test, do not weaken the mutation. Record the table in
  `progress/impl_text_and_units.md`. Covers: R1–R22.

| # | Mutation | Must be caught by |
|---|---|---|
| 1 | Drop the `strip()` step | T4 |
| 2 | Drop the `casefold()` step | T6, T14 |
| 3 | Drop the combining-mark removal | T7, T14 |
| 4 | Drop the `U+0303` exemption, folding `ñ` → `n` | T8 |
| 5 | Drop the final NFC recomposition | T9 |
| 6 | Move `casefold()` after the mark removal | **KNOWN EQUIVALENT MUTANT — expected to survive.** Verified 2026-08-23 over `U+0000`–`U+2FFFF`: the two orderings diverge on 64 codepoints, all Greek with iota subscript, none Latin. No honest test kills it; do not write one. See `design.md` §5.1 as corrected. |
| 7 | Add plural folding — `removesuffix("s")` | T11 |
| 8 | Collapse internal whitespace — `" ".join(name.split())` | T5 |
| 9 | Add `KILOGRAM = "kg"` to `Unit` | T15, T17 |
| 10 | Make `parse_unit` case-insensitive — `value.casefold()` | T17 |
| 11 | Make `parse_unit` tolerant — `value.strip()` | T17 |
| 12 | Make `UnknownUnit` inherit `Exception` directly | T18 |
| 13 | Stop storing the rejected value on `UnknownUnit` | T19 |
| 14 | Add a `convert(quantity, source, target)` helper to `units.py` | T20 |
| 15 | Add a `.lower()`-based second fold in `domain/units.py` | T21 |
| 16 | Add `class ShoppingUnit(StrEnum)` to `domain/calendar.py` | T22 |
| 17 | Put an accented `str.maketrans` table in `domain/text.py` | T23 |

## Close-out

- [x] T25 — Record the `R<n> → test` map in
  `progress/impl_text_and_units.md` (`docs/verification.md` Level 3), together
  with the T24 mutation table and the restore hashes. Covers: R1–R22.
- [x] T26 — Confirm `backend/core/pyproject.toml` still reads
  `dependencies = []`, and that `uv export --package planner-api --no-dev` and
  `uv export --package planner-ai --no-dev` both resolve with nothing added.
  Covers: R14, R21.
- [x] T27 — Run `./init.sh` and confirm every gate is green: `ruff format`,
  `ruff check`, `mypy --strict`, `pytest`, plus the frontend gate. Covers:
  R1–R22.
