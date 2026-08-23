# Review — feature 3 (text_and_units)

**Verdict:** APPROVED

Reviewed 2026-08-23 against `specs/text_and_units/`, `docs/architecture.md`,
`docs/conventions.md`, `docs/specs.md`, `docs/verification.md`, `CHECKPOINTS.md`.
One doc-grade finding, recorded in *Required changes* — it does not block the
code, which is correct as written.

## Requirement coverage (FR → R)

`feature_list.json` feature 3 `covers`: `FR-SHOP-03`, `FR-LIB-05`.

- FR-SHOP-03: [x] cited by R1–R13, R14–R19, R21, R22
- FR-LIB-05:  [x] cited by R14, R15, R16, R17, R18, R20, R22

Both ids appear in at least one `R<n>`. No `R<n>` cites an id outside the
`covers` array, so nothing was invented (`CHECKPOINTS.md` C7).

## Test traceability (R → test)

Every row verified by reading the test, not by trusting
`progress/impl_text_and_units.md` §3. Every listed test asserts a concrete
value; none is a bare "did not raise".

- R1:  [x] `test_planner_core_has_one_name_fold` — `test_shared_kernel_guards.py:52`
- R2:  [x] `test_planner_core_has_one_name_fold` — `test_shared_kernel_guards.py:73`
- R3:  [x] `test_normalize_strips_surrounding_whitespace` — `test_text.py:26`
- R4:  [x] `test_normalize_keeps_whitespace_inside_the_name` — `test_text.py:35`
- R5:  [x] `test_normalize_folds_case` — `test_text.py:40`
- R6:  [x] `test_normalize_folds_the_written_accent_and_the_diaeresis` — `test_text.py:45`
- R7:  [x] `test_normalize_keeps_the_tilde_of_ene` — `test_text.py:63` (asserts the
  surviving codepoint is `U+00F1` and the length is 4, not merely inequality)
- R8:  [x] `test_normalize_returns_composed_form` — `test_text.py:79`
- R9:  [x] `test_normalize_of_a_blank_name_is_the_empty_string` — `test_text.py:88`
- R10: [x] `test_normalize_does_not_fold_plurals` — `test_text.py:94`
- R11: [x] `test_normalize_does_not_stem` — `test_text.py:100`
- R12: [x] `test_normalize_does_not_match_synonyms` — `test_text.py:106`
- R13: [x] `test_the_three_spellings_of_tomate_share_one_key` — `test_text.py:113`
- R14: [x] `test_the_unit_vocabulary_is_closed` — `test_units.py:32`
- R15: [x] `test_the_unit_vocabulary_is_closed` — `test_units.py:34`
- R16: [x] `test_planner_core_has_one_unit_vocabulary` — `test_shared_kernel_guards.py:76`
- R17: [x] `test_parse_unit_resolves_every_code` — `test_units.py:38`
- R18: [x] `test_parse_unit_rejects_a_value_outside_the_list` — `test_units.py:45`
- R19: [x] `test_unknown_unit_is_a_planner_error` — `test_units.py:52` (asserts the
  lineage **and** that a real raise is caught by `except PlannerError`)
- R20: [x] `test_unknown_unit_carries_the_rejected_value` — `test_units.py:62`
- R21: [x] `test_the_units_module_exposes_no_conversion` — `test_units.py:71`
- R22: [x] `test_the_shared_kernel_modules_are_ascii_only` — `test_shared_kernel_guards.py:103`

The three mechanical guards each self-test before scanning, and each asserts the
scanned file list is non-empty and contains named modules — so none can pass by
matching nothing (`test_shared_kernel_guards.py:59-71`, `:78-98`, `:113-116`).
Mutation H below proves the R2 scan really reaches `ports/`, not only `domain/`.

## Tasks complete

All 27 tasks in `specs/text_and_units/tasks.md` are `[x]`.

- T1–T3 (sources): [x]
- T4–T14 (`normalize` tests): [x]
- T15–T20 (unit tests): [x]
- T21–T23 (guards): [x]
- T24 (mutation battery): [x] — run and reported, with one survivor adjudicated below
- T25–T27 (close-out, dependency check, `./init.sh`): [x]

No `[ ]` remains. Nothing needed a justification.

## Invariants exercised

`docs/architecture.md` §4 invariant 10 (*normalised matching*) is the only
invariant this feature touches. `docs/verification.md` Level 4 row for `G-56`:

- Normalised matching (`G-56`, `FR-SHOP-03`): [x]
  `test_the_three_spellings_of_tomate_share_one_key` asserts `{"Tomate",
  "tomate ", "tomáte"}` collapse to a **set of size one** equal to `{"tomate"}`
  — the property, not a happy path. The Level 4 row is satisfied verbatim.
- The *negative* half of the same invariant ("no fuzzy matching beyond that") is
  exercised as three separate properties rather than a comment: R10 plurals,
  R11 stemming, R12 synonyms.
- `docs/architecture.md` §4 invariant 12 (*errors are explicit*): [x]
  `parse_unit` raises `UnknownUnit(PlannerError)`; it never returns `None`.
  Proved by `test_unknown_unit_is_a_planner_error`.

No other §4 invariant is in this feature's reach: no snapshot, no idempotent
compound operation, no shopping-list state, no clock.

## Mutation testing

Eight mutations of my own, one live at a time, each reverted before the next.
Baseline SHA-256 taken before the first and re-verified after the last.

- R3 — `strip()` → `lstrip()` in `domain/text.py:34`: [x] killed by
  `test_normalize_strips_surrounding_whitespace` and
  `test_the_three_spellings_of_tomate_share_one_key` (2 failed)
- R6 — weakened the mark predicate `startswith("M")` → `startswith("Mc")` in
  `domain/text.py:16`, so the acute and diaeresis survive: [x] killed by
  `test_normalize_folds_the_written_accent_and_the_diaeresis`,
  `test_normalize_strips_surrounding_whitespace`,
  `test_the_three_spellings_of_tomate_share_one_key` (3 failed)
- R9 — added a "helpful" fallback `... or name` at `domain/text.py:36`, so a
  blank name returns itself: [x] killed by
  `test_normalize_of_a_blank_name_is_the_empty_string`
- R7 — repointed `COMBINING_TILDE` from `U+0303` to `U+0304` at
  `domain/text.py:12`, folding `ñ` → `n`: [x] killed by
  `test_normalize_keeps_the_tilde_of_ene`. This is the human's gate decision 2,
  and the test fails on the codepoint assertion, not merely on inequality.
- R18 — weakened the comparison `value == unit.value` → `value in unit.value`
  at `domain/units.py:48`, so `""` resolves to `Unit.GRAM`: [x] killed by
  `test_parse_unit_rejects_a_value_outside_the_list`
- R20 — silently casefolded the carried value, `self.value = value.casefold()`
  at `domain/units.py:37`: [x] killed by
  `test_unknown_unit_carries_the_rejected_value` **and** by
  `test_planner_core_has_one_name_fold` (the second-fold guard caught it too)
- R15 — changed the `UNIT` code `"unit"` → `"units"` at `domain/units.py:22`:
  [x] killed by `test_the_unit_vocabulary_is_closed` and
  `test_parse_unit_resolves_every_code`
- R1/R2 — planted a second fold (`name.strip().lower()`) in
  `ports/clock.py`, a directory the implementer's battery never probed: [x]
  killed by `test_planner_core_has_one_name_fold`. The guard's `rglob` really
  covers the whole package, not just `domain/`.

### Adjudication of the implementer's surviving mutation 6

`progress/impl_text_and_units.md` §4.1 reports mutation 6 (*move `casefold()`
after the mark removal*) as surviving. **Verified independently, not accepted.**

I re-ran the mutation myself (`domain/text.py:34-36`, casefold moved between
mark removal and the NFC recomposition) → **55 passed**. The mutant does
survive.

I then verified the implementer's analysis in Python rather than trusting it:

- `unicodedata.normalize("NFD", chr(0x0130))` → `U+0049 U+0307`. The dot is
  already a separate combining mark **before** any casefold, so step 3 strips it
  under either ordering. Both orders return `"i"`, length 1.
- Exhaustive sweep of `U+0000`–`U+2FFFF` comparing the specified fold against
  the reordered fold: **64 divergent codepoints, all Greek iota-subscript /
  prosgegrammeni** (`U+0345`, `U+1F80`–`U+1FFC`). **Zero Latin codepoints
  diverge.** None of the 20 values of `design.md` §8.1 diverges.

**Ruling: dead justification — a DOC defect, not a code defect, and not a
missing test.**

The ordering is not load-bearing for any input in scope. No `R<n>` and no
`FR-*` says anything about the internal step order or about Greek script; R6
constrains the *output*, which is identical under both orders for every Latin
input. On the requirement's actual domain this is an **equivalent mutant** —
observationally indistinguishable — and an equivalent mutant cannot be killed by
any honest test. The only test that could kill it would assert a Greek
iota-subscript value, which `design.md` §8 explicitly forbids inventing
(*"Use these exact values. Do not invent new ones."*) and which no requirement
demands. The implementer was right to decline to invent one, and right to keep
the specified order and record the survivor rather than weaken the mutation.

What **is** wrong is the prose that justifies the order. `design.md` §5.1's
claim — *"`\"İ\".casefold()` is `i` + `U+0307` … Doing it after step 3 would
leave that mark in the output"* — is false: step 3 removes that mark either way.
The claim is true of the casefold, and false of the pipeline. Exact locations in
*Required changes* below. `design.md` is a spec file, not one of the five frozen
requirement docs, so correcting it is permitted — but it is not mine to make and
not the implementer's to make unasked. It is the leader's to route.

- Tree restored: [x] `git status --porcelain` is byte-identical to the
  pre-review snapshot (9 modified harness/progress files, 7 untracked additions;
  `git diff --stat -- backend` empty). SHA-256 re-verified as MATCH for
  `domain/text.py`, `domain/units.py`, `domain/calendar.py` and
  `ports/clock.py`. No git write command was run at any point.

## Boundaries

- No Terraform / CI files generated: [x] no `*.tf`, `*.tfvars` or
  `.github/workflows/**` in the change set; `init.sh` §4 tripwire green.
- No architecture decision from §2 made silently: [x] P2–P6 untouched. The one
  §2.1 *decide-in-a-spec* item (the literal unit list, `G-39`) was proposed in
  `design.md` §4 and **decided by the human at the gate on 2026-08-23**, not by
  an agent. The three-member vocabulary in `domain/units.py:20-22` matches that
  decision exactly.
- Frozen requirement docs unmodified: [x] `git status` shows no change to
  `docs/requirements.md`, `docs/app_user_stories.md`,
  `docs/coverage_analysis.md`, `docs/gaps_and_resolutions.md`,
  `docs/gaps_pending_stakeholders.md`. `docs/data_model.md` also untouched.
- `feature_list.json` not touched by the implementer; feature 3 left
  `in_progress`: [x]

## Layering (`docs/architecture.md` §3)

- `domain/text.py` imports `unicodedata` and `typing.Final` only; `domain/units.py`
  imports `enum.StrEnum` and `planner_core.domain.errors`. No `application/`, no
  `ports/`, no adapter, no handler, no AWS SDK: [x]
- `core` runtime dependencies still `[]` (`backend/core/pyproject.toml:5`): [x]
- No `application/` piece added, correctly — nothing here orchestrates a port: [x]
- Ambient time: `backend/core/tests/test_no_ambient_time.py` is green and
  **unmodified** — no exemption widened, no allowance loosened, no self-check
  deleted, and neither new module reads a clock: [x]

## Conventions (`docs/conventions.md`)

- Naming: `normalize`, `parse_unit`, `Unit`, `UnknownUnit`, `_is_removable_mark`,
  `COMBINING_TILDE` — all match the table: [x]
- Typing: `mypy` strict clean, no `# type: ignore`, no bare `Any`: [x]
- Error handling: raises a named domain exception derived from `PlannerError`,
  never returns `None` for failure: [x]
- Language rule: both source modules are **ASCII-only and mechanically enforced**
  (R22), so no Castilian literal can enter them, and none did. The Spanish
  strings in `test_text.py` are test *data* exercising the fold, not user-facing
  strings — correct, and the module docstring says so: [x]
- Comments: sparse and each records a non-obvious *why* with a citation, as the
  convention asks. One of them is factually wrong — see *Required changes* 1: [ ]

## Checkpoints

- C1: [x] harness complete; the five frozen docs unmodified; `./init.sh` exit 0.
- C2: [x] exactly one `in_progress` (feature 3); every `blocked` feature has a
  reason; `progress/current.md` describes this session.
- C3: [x] layering clean; `core` deps `[]`; exactly two Lambda packages; no
  ambient time beyond the sanctioned `SystemClock.now`; no stray `print()`, no
  context-free TODO.
- C4: [x] `ruff format`, `ruff check`, `mypy`, `pytest` (**55 passed**, +20 from
  this feature) all green; `core` tests need no AWS, network or real clock; one
  test module per new source module (`text.py`→`test_text.py`,
  `units.py`→`test_units.py`).
  The contract-suite box remains deliberately unticked under the C4 deferral
  note (feature 14) — unchanged by this feature, which implements no port.
- C5: [x] no suspicious untracked files; `progress/history.md` has the last
  session; feature 3 correctly left `in_progress` for the leader to close.
- C6: [x] all three spec files present; strict EARS with exactly one `SHALL` per
  requirement (`requirements.md` explicitly declines feature 2's combined-`SHALL`
  deviation); every `R<n>` cites an `FR-*`; both `covers` ids appear in an
  `R<n>`; every `R<n>` has a concrete test; all 27 tasks `[x]`; `init.sh`
  reports all 103 FR/NFR ids covered.
- C7: [x] no agent-generated IaC or CI; no §2 decision made silently; no
  requirement invented; frozen docs unedited.

## Required changes (if any)

None blocking. **Approved.** One documentation correction to route, and one
optional follow-up:

1. **Correct the dead justification in `specs/text_and_units/design.md` §5.1**
   (leader to route; not the reviewer's edit, and `design.md` is a spec file,
   not a frozen requirement doc). The paragraph at **`design.md:176-180`**
   asserts *"Doing it after step 3 would leave that mark in the output"*. That is
   false — `unicodedata.normalize("NFD", "İ")` already yields `I` + `U+0307`, so
   step 3 removes the dot under either ordering. The ordering diverges only on 64
   Greek iota-subscript codepoints, none of which is in scope. The honest
   statement is that the order is **not** observable on any in-scope value and is
   kept because it does not depend on the input having a canonical decomposition.
   Three dependent lines carry the same false claim and should move with it:
   - `design.md:348` — the `chr(0x0130)` row is labelled *"R6, ordering rule of
     §5.1"*; it proves R6 only.
   - `tasks.md:39` (T7) — *"the regression test for the step order of
     `design.md` §5.1"*; it is not one.
   - `tasks.md:120` (T24 row 6) — predicts T7 catches the reorder; it cannot.
2. **Optional, same defect one layer down:** the comment at
   `backend/core/src/planner_core/domain/text.py:31-33` restates the §5.1 claim
   in source (*"a fold applied afterwards would leave that mark in the output"*).
   `docs/conventions.md` § *Comments* admits comments only to explain a
   non-obvious *why*; a *why* that is factually wrong is worse than none, because
   the next reader will trust it. Whoever corrects §5.1 should correct this
   comment in the same pass. **No behaviour change** — the code is right, and the
   implemented order stays.

Neither item changes a line of executable code, neither affects any `R<n>`, and
neither is a reason to hold the feature. Feature 3 is complete and correct.
