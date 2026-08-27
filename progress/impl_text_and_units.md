# Implementation report — feature 3 `text_and_units`

> Implementer session, 2026-08-23. Spec: `specs/text_and_units/`, approved at
> the gate on 2026-08-23 with all three §10 questions answered as recommended.
> Status left as `in_progress` — the reviewer closes it, not this agent.

---

## 1. Result

`./init.sh` → **exit 0**, every gate green:

| Gate | Result |
|---|---|
| `ruff format --check` | OK (24 files) |
| `ruff check` | OK |
| `mypy` (strict) | OK — no issues in 24 source files |
| `pytest` (unit, no AWS) | **55 passed** (35 before this feature, **+20**) |
| `prettier --check` / `eslint` / `vitest` (frontend) | OK |

All 27 tasks of `tasks.md` are ticked. No task was skipped.

---

## 2. Files

### Created — sources

| Path | Contents |
|---|---|
| `backend/core/src/planner_core/domain/text.py` | `normalize`, `COMBINING_TILDE`, private `_is_removable_mark`. ASCII-only. |
| `backend/core/src/planner_core/domain/units.py` | `Unit(StrEnum)`, `UnknownUnit(PlannerError)`, `parse_unit`. ASCII-only. |

### Created — tests

| Path | Tests |
|---|---|
| `backend/core/tests/domain/test_text.py` | 11 (T4–T14) |
| `backend/core/tests/domain/test_units.py` | 6 (T15–T20) |
| `backend/core/tests/test_shared_kernel_guards.py` | 3 (T21–T23) |

### Modified

**None.** `git diff --stat -- backend` is empty: no tracked backend file was
touched. `planner_core/domain/errors.py` was reused unchanged (`UnknownUnit`
subclasses the `PlannerError` feature 2 declared), `backend/core/pyproject.toml`
still reads `dependencies = []`, and no frozen doc, no `feature_list.json`
entry and no IaC/CI file was written. No git write command was run at any point.

---

## 3. Traceability — every `R<n>` proved by a test that asserts a value

| `R<n>` | Task | Test | Module |
|---|---|---|---|
| R1 | T1, T21 | `test_planner_core_has_one_name_fold` (plus all 11 `test_text` tests, which reach the fold only through `normalize`) | guards / text |
| R2 | T21 | `test_planner_core_has_one_name_fold` | guards |
| R3 | T4 | `test_normalize_strips_surrounding_whitespace` | text |
| R4 | T5 | `test_normalize_keeps_whitespace_inside_the_name` | text |
| R5 | T6 | `test_normalize_folds_case` | text |
| R6 | T7 | `test_normalize_folds_the_written_accent_and_the_diaeresis` | text |
| R7 | T8 | `test_normalize_keeps_the_tilde_of_ene` | text |
| R8 | T9 | `test_normalize_returns_composed_form` (+ the `U+00F1` codepoint assertion in T8) | text |
| R9 | T10 | `test_normalize_of_a_blank_name_is_the_empty_string` | text |
| R10 | T11 | `test_normalize_does_not_fold_plurals` | text |
| R11 | T12 | `test_normalize_does_not_stem` | text |
| R12 | T13 | `test_normalize_does_not_match_synonyms` | text |
| R13 | T14 | `test_the_three_spellings_of_tomate_share_one_key` | text |
| R14 | T15 | `test_the_unit_vocabulary_is_closed` | units |
| R15 | T15 | `test_the_unit_vocabulary_is_closed` | units |
| R16 | T22 | `test_planner_core_has_one_unit_vocabulary` | guards |
| R17 | T16 | `test_parse_unit_resolves_every_code` | units |
| R18 | T17 | `test_parse_unit_rejects_a_value_outside_the_list` | units |
| R19 | T18 | `test_unknown_unit_is_a_planner_error` | units |
| R20 | T19 | `test_unknown_unit_carries_the_rejected_value` | units |
| R21 | T20 | `test_the_units_module_exposes_no_conversion` | units |
| R22 | T23 | `test_the_shared_kernel_modules_are_ascii_only` | guards |

### `FR-*` reachability (the `covers` array)

| Frozen requirement | Reached through | Proved by |
|---|---|---|
| `FR-SHOP-03` | R1–R19, R21, R22 | all 20 tests above |
| `FR-LIB-05` | R14–R18, R20, R22 | `test_the_unit_vocabulary_is_closed`, `test_parse_unit_resolves_every_code`, `test_parse_unit_rejects_a_value_outside_the_list`, `test_unknown_unit_is_a_planner_error`, `test_unknown_unit_carries_the_rejected_value`, `test_the_shared_kernel_modules_are_ascii_only` |

Both directions hold: every `R<n>` has at least one test asserting a value, and
neither `FR-*` in the `covers` array is left without a reachable `R<n>`.

Every input and expected output comes verbatim from `design.md` §8.1 and §8.2.
All 20 rows of §8.1 and all 9 rows of §8.2 were executed against the real
implementation before being written down; every one matched the design — no
correction was needed.

---

## 4. Anti-hollow-green — the mutation battery (T24)

Method as established by `progress/impl_week_calendar.md` §4, tightened as
`tasks.md` T24 requires: SHA-256 taken **before** each mutation, the mutation
applied, `uv run pytest -q` run from `backend/`, the file restored from an
in-memory copy of the original bytes, and the restore **verified by SHA-256
against the pre-mutation hash**. The driver aborts on any hash mismatch. **No
git command that writes was used.**

| # | Mutation | Module | Result — failing tests |
|---|---|---|---|
| 1 | Drop the `strip()` step | `text.py` | **3 failed**: `test_normalize_strips_surrounding_whitespace`, `test_normalize_of_a_blank_name_is_the_empty_string`, `test_the_three_spellings_of_tomate_share_one_key` |
| 2 | Drop the `casefold()` step | `text.py` | **5 failed**, incl. `test_normalize_folds_case`, `test_the_three_spellings_of_tomate_share_one_key` |
| 3 | Drop the combining-mark removal | `text.py` | **3 failed**, incl. `test_normalize_folds_the_written_accent_and_the_diaeresis`, `test_the_three_spellings_of_tomate_share_one_key` |
| 4 | Drop the `U+0303` exemption | `text.py` | **1 failed**: `test_normalize_keeps_the_tilde_of_ene` |
| 5 | Drop the final NFC recomposition | `text.py` | **2 failed**: `test_normalize_returns_composed_form`, `test_normalize_keeps_the_tilde_of_ene` |
| 6 | Move `casefold()` after the mark removal | `text.py` | **SURVIVED — 55 passed.** See §4.1 |
| 7 | Add plural folding — `removesuffix("s")` | `text.py` | **2 failed**: `test_normalize_does_not_fold_plurals`, `test_normalize_does_not_stem` |
| 8 | Collapse internal whitespace | `text.py` | **1 failed**: `test_normalize_keeps_whitespace_inside_the_name` |
| 9 | Add `KILOGRAM = "kg"` to `Unit` | `units.py` | **3 failed**: `test_the_unit_vocabulary_is_closed`, `test_parse_unit_rejects_a_value_outside_the_list`, `test_the_units_module_exposes_no_conversion` |
| 10 | Make `parse_unit` case-insensitive | `units.py` | **3 failed**: `test_parse_unit_rejects_a_value_outside_the_list`, `test_unknown_unit_carries_the_rejected_value`, `test_planner_core_has_one_name_fold` |
| 11 | Make `parse_unit` tolerant — `value.strip()` | `units.py` | **1 failed**: `test_parse_unit_rejects_a_value_outside_the_list` |
| 12 | `UnknownUnit` inherits `Exception` directly | `units.py` | **1 failed**: `test_unknown_unit_is_a_planner_error` |
| 13 | Stop storing the rejected value | `units.py` | **1 failed**: `test_unknown_unit_carries_the_rejected_value` |
| 14 | Add a `convert(quantity, source, target)` helper | `units.py` | **1 failed**: `test_the_units_module_exposes_no_conversion` |
| 15 | Add a `.lower()`-based second fold in `units.py` | `units.py` | **2 failed**: `test_planner_core_has_one_name_fold`, `test_the_units_module_exposes_no_conversion` |
| 16 | Add `class ShoppingUnit(StrEnum)` to `calendar.py` | `calendar.py` | **1 failed**: `test_planner_core_has_one_unit_vocabulary` |
| 17 | Put an accented `str.maketrans` table in `text.py` | `text.py` | **1 failed**: `test_the_shared_kernel_modules_are_ascii_only` |

Every mutation landed on the test the T24 table predicted, except #6.

### Restore hashes (SHA-256, identical before and after every mutation)

| File | SHA-256 |
|---|---|
| `backend/core/src/planner_core/domain/text.py` | `adecf3c4136f5e56db2e7cdb9ba83fb4fdafd7404acb3ffe42022ee9f5bb8e1b` |
| `backend/core/src/planner_core/domain/units.py` | `3f024ba13b8b392e07056c33b267fcc90e06247f817d56b374e9cd38c6cdeb66` |
| `backend/core/src/planner_core/domain/calendar.py` | `e87c761ecec186a9aea5d3fa93becf11eec8774cc6054ed8b8e096e6939b813e` |

`git status` after the battery shows the three source files unmodified
(`calendar.py` is tracked; `git diff -- backend` is empty), and the two new
modules present as untracked additions only.

### 4.1 Mutation 6 survived — and it is not a hole in the suite

**The defect is in the rationale, not in the code: `design.md` §5.1 says
case-folding must precede mark removal because `"İ".casefold()` introduces a
combining mark, but `unicodedata.normalize("NFD", "İ")` is already
`"I" + U+0307`, so step 3 removes that dot whichever side of it the `casefold()`
sits.** The two orderings are therefore observationally identical on the `"İ"`
value the design nominates, and `test_normalize_folds_the_written_accent_and_the_diaeresis`
cannot distinguish them.

Evidence gathered rather than assumed:

- `unicodedata.normalize("NFD", chr(0x0130))` → `"I" + chr(0x0307)` (a *canonical*
  decomposition), while `chr(0x0130).casefold()` → `"i" + chr(0x0307)`. Both routes
  reach `"i"`, length 1, no `U+0307`.
- Both plausible readings of the mutation were run through the full suite:
  casefold after the NFC recomposition, and casefold between mark removal and
  recomposition. **55 passed** in both cases.
- An exhaustive sweep of `U+0000`–`U+2FFFF` comparing the specified fold against
  the casefold-last fold found **64 divergent codepoints, all of them Greek
  iota-subscript / prosgegrammeni forms** (`U+0345`, `U+1F80`–`U+1FFC`). Not one
  Latin codepoint differs, and none of the 20 values of `design.md` §8.1 does.

**Why no test was added.** T24 says to fix the test rather than weaken the
mutation, but the only inputs that separate the two orderings are Greek, and
`design.md` §8 states *"Use these exact values. Do not invent new ones."* Adding
a Greek codepoint would assert behaviour no `R<n>` and no `FR-*` demands, on
data the spec forbids inventing — which is the kind of scope creep
`docs/specs.md` exists to prevent. The mutation was **not** weakened either: it
is recorded as survived, with the reason.

**Why the implemented order was kept anyway.** It is what the approved
`design.md` §5.1 prescribes, and it is the safer of the two: it does not depend
on the input codepoint having a canonical decomposition. The source comment was
written to record the ordering and cite §5.1; a reviewer may wish to route the
§5.1 wording back through a spec correction, since the `"İ"` justification does
not hold for this implementation. **That is a spec-text defect for the leader to
route, not an implementation deviation** — no code change is implied.

---

## 5. Boundary checks

| Check | Result |
|---|---|
| Runtime dependencies (T26) | `backend/core/pyproject.toml` still `dependencies = []`. `uv export --package planner-api --no-dev` and `--package planner-ai --no-dev` both resolve 27 packages with nothing added — only the three workspace members. |
| Layering (`architecture.md` §3) | Both modules are pure functions of plain values in `domain/`. No port, no clock, no IO, no AWS SDK, no `application/` piece. |
| Ambient time | Neither module reads a clock; the existing `test_no_ambient_time.py` scans now cover both new modules and stay green. |
| Architecture §2 decisions | None taken. The one §2.1 *decide-in-a-spec* item (the literal unit list) was decided by the human at the gate, not here. |
| User-facing strings | None. `UnknownUnit` carries only the rejected value; no backend messages module was created (gate answer 3). |
| Frozen docs | Untouched. `docs/data_model.md` untouched — a unit code is an attribute value, not one of the §2 key formats. |
| `feature_list.json` | Untouched; feature 3 left `in_progress` for the reviewer. |
| Terraform / CI | None written. |
| `# type: ignore` | None used; `mypy --strict` is clean without one. |

---

## 6. Decisions the design did not settle

Three, all small, all recorded here so the reviewer sees them rather than
discovers them:

1. **What counts as "a Unicode combining mark" (R6).** The design says *"drop
   every combining mark"* without naming the predicate. Implemented as
   `unicodedata.category(character).startswith("M")` — the Unicode general
   category **Mark** — rather than `unicodedata.combining(character) != 0`,
   which is the combining *class* and misses marks whose class is 0. The
   category test is the literal reading of R6. Both predicates give identical
   results on every value of `design.md` §8.1.
2. **`COMBINING_TILDE` is a module-level public constant in `text.py`.** The
   design gives only the signature of `normalize`. The constant is named rather
   than inlined so the one judgement call of §5.3 is visible at the top of the
   module with its `why` beside it. It is written as the escape `"̃"`, so
   R22's ASCII restriction holds. R21's "exactly three public names" assertion
   applies to `units.py` only, so nothing constrains this.
3. **How the guards define "public name" (T20).** `test_the_units_module_exposes_no_conversion`
   filters `vars(units)` by `__module__ == units.__name__`, which excludes the
   imported `StrEnum`, `PlannerError` and `__future__.annotations` while
   catching anything the module declares itself. Mutations 14 and 15 confirm it
   catches a real addition rather than passing by construction.

Nothing else required a judgement: the three gate answers of 2026-08-23 closed
the unit vocabulary, the `ñ` rule and the absence of a Castilian message, and
every test value came from `design.md` §8.

---

## 7. Handover notes for the features that consume this kernel

Recorded here so they are not re-derived later, per `design.md` §1:

- **Features 4, 7, 8 and 12** must import `normalize` and `parse_unit`; the two
  guards in `test_shared_kernel_guards.py` will fail the build if they
  re-implement either. A bare `.lower()` anywhere under `src/planner_core` is
  caught as a second fold — that friction is deliberate.
- **Feature 9 `password_policy`** must generate the `FR-AUTH-17` username
  reservation key with this same `normalize` (`docs/data_model.md` §2), and must
  delete a stale reservation **by lookup, never by re-folding**
  (`docs/data_model.md` §5.2).
- **The es-ES rejection text for an unknown unit** belongs to features 9 and 12.
  `UnknownUnit.value` is the exact rejected string, ready to interpolate.

---

## 8. Source-comment correction, 2026-08-23 (post-review)

The `casefold()`-before-mark-removal comment in `text.py` lines 31–33 asserted
the same false "`İ.casefold()` leaves a stray combining dot" justification that
`design.md` §5.1 already corrected (§4.1 above). It was the last site still
carrying that claim. Replaced with a comment stating the honest reason: the
order is specified but not load-bearing on this domain — NFD already
decomposes `U+0130` before either fold order runs, the two orders diverge only
on 64 Greek iota-subscript codepoints (none in scope), and the reader is
pointed at the corrected sweep in `specs/text_and_units/design.md` §5.1.

No test, spec, `feature_list.json` entry or frozen doc was touched; only the
comment text changed, the code line below it is byte-identical. `./init.sh`
re-run afterwards: exit 0, 55 tests still passing. No git write command was
run.

New comment text:

```
    # casefold() runs before mark removal, per the specified order, but the
    # order is not load-bearing here: NFD already decomposes U+0130 into its
    # base letter plus a combining dot, so mark removal strips that dot under
    # either order. The two orders diverge only on Greek iota-subscript
    # codepoints, none of them in this feature's domain (Castilian ingredient
    # names, docs/data_model.md section 5.2 username key). See the exhaustive
    # sweep in specs/text_and_units/design.md section 5.1.
```

### 8.1 Sixth site, 2026-08-23

One more site carrying the same false justification survived the sweep in
§8: the comment above the `DOTTED_CAPITAL_I` assertions in
`backend/core/tests/domain/test_text.py`,
`test_normalize_folds_the_written_accent_and_the_diaeresis` (lines 53–55). It
called the assertions below it a "regression test for the step order of
design.md section 5.1" — the same claim already corrected in `design.md` §5.1,
`design.md` §8, `tasks.md` T7, the `tasks.md` T24 mutation row and `text.py`
itself.

Replaced with a comment stating what the assertions actually verify (R6:
`U+0130` folds to a bare `"i"` with no combining dot left over), that this is
not a step-order regression test because the two orderings are equivalent on
this domain, and a pointer to `specs/text_and_units/design.md` §5.1 for the
sweep. No assertion, the `folded = normalize(...)` line, the test name or the
docstring were touched.

New comment text:

```
    # Verifies R6: U+0130 folds to a bare "i", with no combining dot left over.
    # Not a step-order regression test -- the two orderings are equivalent on
    # this domain; see the sweep in specs/text_and_units/design.md section 5.1.
```

`./init.sh` re-run afterwards: exit 0, 55 tests still passing. No git write
command was run.

## 9. Comment-length cleanup, 2026-08-23

Applied the new convention (`docs/conventions.md` § *Comments* → *"Keep them
short — long text belongs in docs"*, effective 2026-08-23): three lines is the
ceiling, a comment states the *why* and points at the document that carries
the reasoning instead of reproducing it. Three blocks in this feature were
over the ceiling; all three shortened to a pointer at `design.md`, with the
`G-56`/`G-48` citations kept.

Comment text only. No code line, assertion, test name, docstring or import was
touched. `calendar.py`, `ports/clock.py` and `test_no_ambient_time.py` were
left alone (feature 2, closed).

New comment texts:

`text.py`, above `COMBINING_TILDE`:

```
# The tilde of Spanish n is a letter, not an accent
# (G-56, specs/text_and_units/design.md section 5.3).
```

`text.py`, inside `normalize`:

```
    # Step order is not load-bearing on our domain
    # (specs/text_and_units/design.md section 5.1).
```

`units.py`, inside `parse_unit`:

```
    # Exact match only, never through normalize() (G-48): fuzzy parsing
    # would let "kg" pass as "g", a cross-unit conversion in disguise.
```

`./init.sh` re-run afterwards: exit 0, 55 tests still passing. No git write
command was run.
