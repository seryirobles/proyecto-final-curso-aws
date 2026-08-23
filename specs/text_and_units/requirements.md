# text_and_units — Requirements

> Feature 3 · tier 1 · `sdd: true`
> Covers: `FR-SHOP-03`, `FR-LIB-05`
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen
> requirement ids it implements and is verifiable by at least one concrete test
> that asserts a value.

## Purpose in one sentence

Make "are these two ingredient names the same thing, and is this a unit we
accept" a single, deterministic, shared answer — `docs/architecture.md` §4
invariant 10: **text matching is normalised; case-, accent- and
trim-insensitive for ingredient aggregation, and no fuzzy matching beyond
that.**

## One `SHALL` per requirement

Every `R<n>` below carries exactly one `SHALL` or one `SHALL NOT`, counted
mechanically rather than by eye. Where a rule and the prohibition guarding it
belong together they are **two** requirements — R1/R2, R6/R7, R14/R16, R17/R18.
`specs/week_calendar/requirements.md` records four combined requirements as an
accepted deviation; that is not a pattern to copy, and this file does not.

## Scope note on the two covered requirements

Both `FR-SHOP-03` and `FR-LIB-05` are claimed by later features as well. This
feature owns **only the shared kernel** of each — the vocabulary and the fold.
`design.md` §1 draws the exact line.

---

## R1
Implements: FR-SHOP-03

The system SHALL derive the matching form of an ingredient name exclusively
from `normalize(name)` in `planner_core.domain.text`.

## R2
Implements: FR-SHOP-03

The system SHALL NOT declare a second name-folding implementation anywhere in
the `planner_core` package.

## R3
Implements: FR-SHOP-03

The system SHALL remove leading and trailing whitespace from the name.

## R4
Implements: FR-SHOP-03

The system SHALL NOT alter whitespace that lies between two non-whitespace
characters of the name.

## R5
Implements: FR-SHOP-03

The system SHALL case-fold the name to lower case.

## R6
Implements: FR-SHOP-03

The system SHALL remove from the name every Unicode combining mark except the
combining tilde `U+0303`, so that the Castilian written accent (`á`, `é`, `í`,
`ó`, `ú`) and the diaeresis (`ü`) fold to their base letters.

## R7
Implements: FR-SHOP-03

The system SHALL NOT remove the tilde of `ñ` or `Ñ`.

## R8
Implements: FR-SHOP-03

The system SHALL return the normalized name in Unicode normal form NFC.

## R9
Implements: FR-SHOP-03

WHEN the name is empty or consists only of whitespace, the system SHALL return
the empty string.

## R10
Implements: FR-SHOP-03

The system SHALL NOT fold a plural form of a name onto its singular form.

## R11
Implements: FR-SHOP-03

The system SHALL NOT reduce a name to a stem.

## R12
Implements: FR-SHOP-03

The system SHALL NOT map a name onto a synonym of that name.

## R13
Implements: FR-SHOP-03

The system SHALL produce one single identical normalized value for the three
names `"Tomate"`, `"tomate "` and `"tomáte"`.

## R14
Implements: FR-SHOP-03, FR-LIB-05

The system SHALL define the admissible measurement units as a closed
enumeration `Unit` in `planner_core.domain.units` whose members are exactly
`GRAM`, `MILLILITRE` and `UNIT`.

## R15
Implements: FR-SHOP-03, FR-LIB-05

The system SHALL identify the members of `Unit` by exactly the codes `"g"`,
`"ml"` and `"unit"` respectively.

## R16
Implements: FR-SHOP-03, FR-LIB-05

The system SHALL NOT declare a second measurement-unit vocabulary anywhere in
the `planner_core` package.

## R17
Implements: FR-SHOP-03, FR-LIB-05

WHEN a value equals the code of a member of `Unit` exactly, the system SHALL
resolve it to that member through `parse_unit(value)`.

## R18
Implements: FR-SHOP-03, FR-LIB-05

IF a value is not exactly the code of a member of `Unit`, THEN the system SHALL
raise `UnknownUnit`.

## R19
Implements: FR-SHOP-03

The system SHALL derive `UnknownUnit` from `PlannerError`.

## R20
Implements: FR-LIB-05

The system SHALL expose, on the raised `UnknownUnit`, the exact value that was
rejected.

## R21
Implements: FR-SHOP-03

The system SHALL NOT expose any operation that converts a quantity from one
member of `Unit` to another.

## R22
Implements: FR-SHOP-03, FR-LIB-05

The system SHALL restrict the source modules added by this feature to ASCII
characters, so that neither a Castilian Spanish literal nor a hard-coded table
of accented characters can enter them.

---

## Coverage map

| Frozen requirement | Covered by |
|---|---|
| `FR-SHOP-03` | R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R21, R22 |
| `FR-LIB-05` | R14, R15, R16, R17, R18, R20, R22 |

| `feature_list.json` acceptance criterion | Covered by |
|---|---|
| A fixed unit list is defined as a closed vocabulary (concrete values in `design.md` per G-39) | R14, R15, R16 |
| `normalize(name)` is case-, accent- and leading/trailing-whitespace-insensitive | R3, R5, R6, R13 |
| No stemming, no singular/plural folding, no synonym matching (G-56) | R10, R11, R12 |
| Tests prove `"Tomate"`, `"tomate "` and `"tomáte"` normalize to one key | R13 |
| A value outside the fixed unit list is rejected with a named domain exception | R18, R19, R20 |

Supporting requirements not demanded by a criterion but required by the
documents the criteria rest on: R1/R2 (one shared helper —
`docs/data_model.md` §2), R4 (leading/trailing only, not internal —
`FR-SHOP-03`), R7 (`ñ` is a letter, not an accent — `design.md` §5), R8 (NFC),
R9 (blank input), R21 (no cross-unit conversion — `FR-SHOP-03`), R22 (no
user-facing text in backend domain code — `docs/conventions.md` § *Language
policy*).
