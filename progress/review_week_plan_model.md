# Review — feature 5 (`week_plan_model`)

**Verdict:** CHANGES_REQUESTED

Everything structural is right. The layering is clean, the tree is untouched
outside the two new files, `./init.sh` is green (96 backend tests), all 41
tasks are ticked, all ten `FR-*` are cited by an `R<n>`, and all 24 `R<n>`
name a test. The feature is rejected on **Level 5 only**: 34 mutations were
run and **8 survived**, all of them in the "returns a slightly wrong answer"
class this feature was warned about. Three of the eight defeat a numbered
`R<n>` verbatim (R20, R1, R3/R5); two defeat `docs/architecture.md` §4
invariant 2; one lets the `UNKNOWN_USER_ID` literal drift away from the value
the human pinned at the gate.

The mutation register is the substance of this review; the coverage tables
above it are all green and are recorded for completeness.

---

## Requirement coverage (FR → R)

| `covers` id | Status | Cited by |
|---|---|---|
| `FR-MENU-03` | [x] | R1, R2, R3, R4, R17 |
| `FR-CAND-01` | [x] | R6, R7, R8, R9, R10, R11 |
| `FR-CAND-02` | [x] | R5 |
| `FR-CAND-04` | [x] | R3, R15 |
| `FR-CAND-05` | [x] | R12, R13, R14 |
| `FR-CAND-06` | [x] | R18, R19, R20 |
| `FR-CAND-08` | [x] | R16 |
| `FR-SUM-01` | [x] | R21 |
| `FR-SUM-03` | [x] | R22, R23 |
| `FR-AUTH-13` | [x] | R24 |

Ten of ten. No `R<n>` cites an id outside the `covers` array — checked against
`requirements.md`'s per-`R<n>` `Implements:` lines, not against its own
summary table.

## Test traceability (R → test)

Every `R<n>` has a named, existing test. The **quality** column records what
mutation testing found; a `weak` entry still counts as coverage for step 4 but
is the reason for the verdict.

| `R<n>` | Test | Quality |
|---|---|---|
| R1 | `test_slot_contents_holds_candidates_and_at_most_one_definitive` | **weak** — asserts field shape only; `frozen=True`, which R1 states literally, is unverified (M47) |
| R2 | `test_slot_contents_rejects_a_dangling_definitive_id` | [x] strong (M22) |
| R3 | `test_candidate_fields_are_exactly_the_fixed_shape` | **weak** — field names only; `frozen=True` unverified (M46) |
| R4 | `test_definitive_resolves_by_id_lookup_not_by_cache` | [x] strong (M20) |
| R5 | `test_new_candidate_is_the_only_construction_path` | **weak** — asserts type and field names, never that the arguments arrive in the result (M48, M49) |
| R6 | `test_add_candidate_always_appends` | **weak** on the "otherwise unchanged" half (M50) |
| R7 | `test_add_candidate_warns_on_a_normalized_name_match` + `…does_not_warn_on_distinct_names` | [x] strong (M25, M26, M27) |
| R8 | `test_add_candidate_warns_on_a_normalized_name_match` | [x] strong — asserts the addition, not just the flag (M24) |
| R9 | `test_edit_candidate_replaces_meal_preserving_id_and_author` | [x] strong (M35, M37) |
| R10 | `test_remove_candidate_removes_the_matching_one` | [x] strong (M39) |
| R11 | `test_edit_and_remove_raise_on_an_unknown_id` | [x] strong (M38, M39) |
| R12 | `test_promote_sets_the_definitive_and_replaces_any_previous` | [x] strong (M34) |
| R13 | `test_promote_raises_on_an_unknown_id` | [x] passes, but see M40 — the guard it targets is unreachable |
| R14 | `test_editing_the_definitive_candidate_propagates`, `test_definitive_resolves_by_id_lookup_not_by_cache` | [x] **strong** — the headline `G-67` guarantee is genuinely tested (M20, M51) |
| R15 | `test_edit_candidate_replaces_meal_preserving_id_and_author`, `test_promote_takes_no_author_or_promoter_argument` | [x] strong (M36) |
| R16 | `test_clear_definitive_unsets_it_and_keeps_candidates` | [x] strong (M52) |
| R17 | `test_removing_the_definitive_candidate_clears_it` | **weak** — proves the clear happens, never that it happens *only* then (M23) |
| R18 | `test_to_library_entry_builds_a_new_recipe_from_the_snapshot` | [x] strong (M33) |
| R19 | `test_to_library_entry_warns_on_a_normalized_name_collision` + `…does_not_warn_without_a_collision` | [x] strong (M30, M31, M32) |
| R20 | `test_to_library_entry_warns_on_a_normalized_name_collision` | **weak** — its only R20 assertion is vacuous; see F2 (M29) |
| R21 | `test_summary_contains_exactly_the_definitive_holding_slots` | [x] strong (M44, M45) |
| R22 | `test_resolve_author_returns_the_id_unchanged_when_known` | [x] strong (M42) |
| R23 | `test_resolve_author_substitutes_the_placeholder_when_unknown`, `…is_idempotent_on_the_placeholder` | **weak** on the literal — see F4 (M43) |
| R24 | `test_a_candidate_with_an_unknown_author_is_never_excluded` | [x] strong (M20, M41) |

## Tasks complete

T1–T41: all `[x]` in `specs/week_plan_model/tasks.md`. Spot-checked six against
the shipped code rather than taken on trust — T3 (`__post_init__`), T5 (no
cache in `definitive`), T7 (position-preserving rebuild), T8 (the R17 clear),
T12 (`Recipe` field-by-field), T13 (`resolve_author`). All match. T40's claim
verified independently: `backend/core/pyproject.toml:6` still reads
`dependencies = []`.

## Invariants exercised (`docs/verification.md` Level 4)

| Invariant | Status |
|---|---|
| §4.11 Content freezes only at archival (`FR-CAND-05`, `G-67`) | [x] `test_editing_the_definitive_candidate_propagates` — proved live by M20 and M51 |
| §4.3 Warn, do not block — candidate (`G-59`) | [x] `test_add_candidate_warns_on_a_normalized_name_match` asserts `new in result.plan.candidates`; M24 dies on it |
| §4.3 Warn, do not block — library recipe (`G-26`) | [ ] **the mirror assertion is missing** — M29 survives (F2) |
| §4.9 Removed users leave content behind (`FR-AUTH-13`, `FR-SUM-03`, `G-29`) | [~] the *rule* is tested (M41, M42 die); the *placeholder identity* is not (M43, F4) |
| §4.2 Never silently undo the user's reality | [ ] **not exercised** — M23 and M50 both silently discard a definitive selection and the suite stays green (F1) |
| §4.12 Errors are explicit (named exceptions, never `None`) | [x] M38, M39 die; `definitive()` returning `None` is a genuine answer, not a failure signal |
| §4.1 Snapshots (`FR-CAND-07`) | n/a here — feature 4's, already closed; `to_library_entry` copies field-by-field and M33 dies |

---

## Mutation testing — 26 killed / 34 run, 8 genuine survivors

Numbering continues the house register: feature 4 used **M1–M19** across its
two rounds, so this feature uses **M20–M54**.

All mutations were applied to `backend/core/src/planner_core/domain/candidate.py`
only, one at a time, each reverted from a byte-verified backup before the next.
The whole backend suite (`core/tests`, 96 tests) was run for every one.

> **Harness note, recorded because it nearly produced a false finding.**
> The first pass reported M51 as a survivor. It is not. CPython's
> source-to-bytecode cache validates on `(mtime_seconds, size)`, and M50 and
> M51 replace the *same* substring in two different functions — identical file
> size, written inside the same second — so M51 re-ran M50's cached bytecode.
> The register below was re-run end to end with `PYTHONDONTWRITEBYTECODE=1`
> and a `__pycache__` purge before every mutation. Any reviewer mutating two
> same-length edits in one session needs this; a stale cache can only ever
> manufacture a *false survivor*, never a false kill.

### Killed

| # | `R<n>` / invariant | Mutation | Killed by |
|---|---|---|---|
| M20 | R4, R14 (`G-67`) | `definitive()` memoises resolved candidates in a module-level dict — the exact "cache, not lookup" shape `design.md` §5 forbids | **3 tests**: `test_definitive_resolves_by_id_lookup_not_by_cache`, `test_editing_the_definitive_candidate_propagates`, `test_a_candidate_with_an_unknown_author_is_never_excluded` |
| M21 | R17 | `remove_candidate` leaves `definitive_id` pointing at the removed candidate | `test_removing_the_definitive_candidate_clears_it` |
| M22 | R2 | `SlotContents.__post_init__` guard deleted entirely (`return`) | `test_slot_contents_rejects_a_dangling_definitive_id` |
| M24 | R8, §4.3 (`G-59`) | `add_candidate` **rejects** on duplicate: returns `plan` unchanged with `duplicate_warning=True` | `test_add_candidate_warns_on_a_normalized_name_match` — on `assert new in result.plan.candidates`, not on the flag |
| M25 | R7 | `duplicate_warning = False` unconditionally | `test_add_candidate_warns_on_a_normalized_name_match` |
| M26 | R7 | `duplicate_warning = True` unconditionally | `test_add_candidate_does_not_warn_on_distinct_names` |
| M27 | R7 | duplicate check compares raw names, dropping `normalize()` | `test_add_candidate_warns_on_a_normalized_name_match` |
| M28 | R6 | `add_candidate` prepends instead of appending | `test_add_candidate_always_appends` |
| M30 | R19 | `to_library_entry` never warns | `test_to_library_entry_warns_on_a_normalized_name_collision` |
| M31 | R19 | `to_library_entry` always warns | `test_to_library_entry_does_not_warn_without_a_collision` |
| M32 | R19 | collision check compares raw names, dropping `normalize()` | `test_to_library_entry_warns_on_a_normalized_name_collision` |
| M33 | R18 | `to_library_entry` builds the `Recipe` with `procedure=()` | `test_to_library_entry_builds_a_new_recipe_from_the_snapshot` |
| M34 | R12 | `promote` keeps any previous definitive (`plan.definitive_id or candidate_id`) — accumulate instead of replace | `test_promote_sets_the_definitive_and_replaces_any_previous` |
| M35 | R9 (`design.md` §6) | `edit_candidate` rebuilt as remove-then-append, losing tuple position | `test_edit_candidate_replaces_meal_preserving_id_and_author` |
| M36 | R15 | `edit_candidate` resets `author` to `UNKNOWN_USER_ID` | `test_edit_candidate_replaces_meal_preserving_id_and_author` |
| M37 | R9 | `edit_candidate` reassigns the id (`c.id + "-v2"`) | 2 tests: `…preserving_id_and_author`, `test_editing_the_definitive_candidate_propagates` |
| M38 | R11 | `edit_candidate`'s guard clause dropped | `test_edit_and_remove_raise_on_an_unknown_id` |
| M39 | R11 | `remove_candidate`'s guard clause dropped | `test_edit_and_remove_raise_on_an_unknown_id` |
| M41 | R23 | `resolve_author` returns `author_id` unconditionally | 2 tests: `test_resolve_author_substitutes_the_placeholder_when_unknown`, `test_a_candidate_with_an_unknown_author_is_never_excluded` |
| M42 | R22 | `resolve_author` returns `UNKNOWN_USER_ID` unconditionally | `test_resolve_author_returns_the_id_unchanged_when_known` |
| M44 | R21 | `summary` keeps every slot, definitive or not | `test_summary_contains_exactly_the_definitive_holding_slots` |
| M45 | R21 | `summary` keeps exactly the slots *without* a definitive | `test_summary_contains_exactly_the_definitive_holding_slots` |
| M51 | R14 (`G-67`) | `edit_candidate` returns `definitive_id=None` — editing silently un-promotes | `test_editing_the_definitive_candidate_propagates` |
| M52 | R16 | `clear_definitive` discards `candidates` too | `test_clear_definitive_unsets_it_and_keeps_candidates` |
| M54 | deviation check | the import line restored to `design.md` §6's literal text (see the ruling below) | `mypy --strict`: `Module "collections.abc" has no attribute "AbstractSet"`; runtime `ImportError` |

**M20 is the one that matters most and it dies three times over.** The
feature's headline guarantee — `G-67` propagation as a *consequence* of
`definitive()` being a fresh lookup, with no propagation code anywhere — is
genuinely tested, and `test_definitive_resolves_by_id_lookup_not_by_cache`
earns its name. M51 confirms the other half: `edit_candidate` cannot quietly
drop the pointer either.

**M24 is the second.** `test_add_candidate_warns_on_a_normalized_name_match`
asserts the flag **and** the addition, so turning "warn" into "reject" fails
it. That is exactly the assertion `to_library_entry`'s test is missing — see F2.

### Survived

| # | `R<n>` / invariant | Mutation | Classification |
|---|---|---|---|
| M23 | §4.2, R6/R12 | `remove_candidate` sets `definitive_id = None` **unconditionally** | **F1 — real hole** |
| M29 | R20, §4.3 (`G-26`) | `to_library_entry` returns a hollow `Recipe(name="", ingredients=(), tools=(), procedure=())` when `duplicate_warning` is `True` | **F2 — real hole** |
| M40 | R13 | `promote`'s guard clause dropped | **equivalent mutant — not a finding** |
| M43 | R23, `docs/data_model.md` §5.1 | `UNKNOWN_USER_ID` changed to `"usuario-desconocido"` | **F4 — real hole** |
| M46 | R3 | `@dataclass(frozen=True)` → `@dataclass()` on `Candidate` | **F5 — real hole** |
| M47 | R1 | `@dataclass(frozen=True)` → `@dataclass()` on `SlotContents` | **F5 — real hole** |
| M48 | R5 | `new_candidate` branches on `meal.name` and substitutes a different `author` for one source | **F3 — real hole** |
| M49 | R5, R3 (`FR-CAND-04`) | `new_candidate` discards the `author` argument entirely and always writes `UNKNOWN_USER_ID` | **F3 — real hole** |
| M53 | `tasks.md` T1 only | `CandidateNotFound.__init__` stores `""` instead of the offending id | **O1 — observation, not blocking** |

**M40 is interrogated, not counted.** Dropping `promote`'s guard is *behaviourally
identical*: the very next statement constructs `SlotContents(candidates=…,
definitive_id=candidate_id)`, whose `__post_init__` raises
`CandidateNotFound(self.definitive_id)` — same exception class, same
constructor argument, same `.candidate_id` attribute, same message. There is no
observable difference for a test to detect, so no test can be written that
would kill it. This is an equivalent mutant. (It does mean R13's explicit guard
is dead code in the strict sense; that is a design remark, recorded as O2, not
a defect.)

- **Tree restored: [x]** `git status --porcelain` is byte-identical to the
  pre-review state — same 4 modified, same 4 untracked paths. Both feature
  files verified against `git hash-object` baselines taken before the first
  mutation and again after the last:
  `candidate.py fa4fa324`, `test_candidate.py 90591ee5`. `test_candidate.py`
  was never written to at all. After the final revert: `ruff format --check`
  (30 files), `ruff check`, `mypy` (30 source files) and `pytest` (96 passed)
  all green. No git write command was run at any point; `feature_list.json`
  untouched by this review. The harness scripts and the `candidate.py` backup
  live in the session scratchpad, outside the repository.

---

## Blocking findings

### F1 — `remove_candidate` can discard a definitive it was never asked to touch (M23)

`backend/core/src/planner_core/domain/candidate.py:108`

```python
definitive_id = None if plan.definitive_id == candidate_id else plan.definitive_id
```

Replace that whole line with `definitive_id = None` and **96 tests still pass.**
Under that mutation, removing *any* candidate wipes the slot's chosen meal:
the user deletes an idea they rejected, and the meal they had promoted quietly
stops being definitive. That is `docs/architecture.md` §4 invariant 2 —
*"never silently undo the user's reality"* — and nothing notices.

The reason is narrow and fixable: `test_remove_candidate_removes_the_matching_one`
(`test_candidate.py:141`) builds its plan with **no definitive at all**
(`SlotContents(candidates=(one, two, three))`, line 144), so the conditional it
would have to exercise is never reached. R17's own test only ever removes *the*
definitive. Between them the two tests cover both branches of the `if` — but
only ever the branch that returns `None`.

**Required:** one test that removes a **non-definitive** candidate from a plan
that *has* a definitive, and asserts the definitive survives — both
`result.definitive_id` and `definitive(result)`.

### F2 — R20 is asserted with a statement that cannot fail (M29)

`backend/core/tests/domain/test_candidate.py:241`

```python
assert result.recipe is not None
```

`LibraryEntryResult.recipe` is declared `recipe: Recipe`
(`candidate.py:63`) — not `Recipe | None`. Under `mypy --strict` this
assertion is a tautology, and at runtime it is true for *any* `Recipe`
whatsoever. R20 says the system *"SHALL NOT omit `recipe` from the result when
`duplicate_warning` is `True`"*, and this is the only assertion carrying it.

M29 replaces the recipe with an empty husk — `name=""`, no ingredients, no
tools, no procedure — precisely on the duplicate path, and the suite stays
green. `docs/architecture.md` §4 invariant 3 and `G-26` require the entry to be
**created anyway**; right now nothing proves it is.

Contrast `add_candidate`, which gets this right: its sibling test asserts
`assert new in result.plan.candidates` (line 115), and M24 — the same
reject-on-duplicate defect — dies on it. The library path needs the mirror of
that assertion.

**Required:** in `test_to_library_entry_warns_on_a_normalized_name_collision`,
replace the `is not None` line with assertions on the returned recipe's actual
content — at minimum `result.recipe.name == meal.name` and one of the
collection fields — so that "warned" can never mean "hollowed out".

### F3 — `new_candidate` is never asserted to carry its arguments (M48, M49)

`backend/core/tests/domain/test_candidate.py:85-93`

`test_new_candidate_is_the_only_construction_path` calls `new_candidate` three
times and asserts only `isinstance(result, Candidate)` and that the dataclass
has the fields `{"id", "meal", "author"}`. Neither assertion looks at a
*value*. So:

- **M49** — `new_candidate` ignoring its `author` parameter and hard-writing
  `UNKNOWN_USER_ID` into every candidate: **survives.** Every meal in the app
  would be attributed to the removed-user placeholder (`FR-CAND-04`,
  `FR-SUM-01`), and no test fails.
- **M48** — `new_candidate` branching on `meal.name` and treating one authoring
  source differently: **survives.** R5's whole point is that the three
  authoring sources are handled *identically*; the test names all three but
  cannot tell them apart because it inspects no value.

This is `docs/verification.md`'s "a test that only asserts the function did not
raise" in a slightly better disguise: it asserts the function returned the
right *type*.

**Required:** assert the returned `Candidate`'s `id`, `meal` and `author` equal
the arguments passed in, for at least one of the three calls, and assert the
three results differ from one another only in the arguments that differed.

### F4 — the `UNKNOWN_USER_ID` literal is unpinned and can drift silently (M43)

`backend/core/src/planner_core/domain/candidate.py:15`

```python
UNKNOWN_USER_ID: Final[str] = "unknown-user"
```

Change it to anything at all and **96 tests still pass**, because both R23
tests compare `resolve_author(...)` against the symbol `UNKNOWN_USER_ID`, never
against its value.

That is normally a defensible style. It is not defensible here, because the
human ruled at the 2026-08-24 gate that this literal is shared state across two
features, and `docs/data_model.md:302-309` now records it:

> **The seeded account's `idUsuario` is exactly `unknown-user`.** … **Feature 15
> does not get to pick this value** — it is fixed here.

The failure mode is exactly the one that document describes: if the constant
and the seeded account disagree, a removed author resolves to an id no account
has, the placeholder is never found, and `FR-SUM-03` breaks with no crash and
no red test. The whole reason the human pinned it was to prevent a silent
divergence — and there is currently no mechanism enforcing the pin.

**Required:** one assertion on the literal value —
`assert UNKNOWN_USER_ID == "unknown-user"` — carrying a comment that points at
`docs/data_model.md` §5.1 (a pointer, per `docs/conventions.md`; not a
paraphrase of the rule).

### F5 — R1 and R3 name `frozen=True` and nothing checks it (M46, M47)

R1: *"SHALL declare `SlotContents` as `@dataclass(frozen=True)`"*.
R3: *"SHALL declare `Candidate` as `@dataclass(frozen=True)`"*.
`docs/conventions.md` § *Python style*: *"domain entities are
`@dataclass(frozen=True)`. Mutating means constructing a new instance."*

Remove `frozen=True` from either and the suite stays green (M46, M47).
`test_slot_contents_holds_candidates_and_at_most_one_definitive` and
`test_candidate_fields_are_exactly_the_fixed_shape` both inspect the field
*shape* and stop there.

This is not a hypothetical: an unfrozen `Candidate` makes every "returns a new
instance" guarantee in this module unenforceable, and the immutability of
`Candidate.author` (R15, `FR-CAND-04`) becomes a convention rather than a
property. Feature 4's second review round already settled the house idiom for
this — `test_recipe_is_frozen`, `test_meal_snapshot_is_a_distinct_frozen_type`,
proved live by mutations M16/M17 — so the pattern to copy already exists in
`backend/core/tests/domain/test_recipe.py`.

**Required:** `pytest.raises(dataclasses.FrozenInstanceError)` on an attribute
assignment, for `Candidate` and for `SlotContents`. Extending it to
`AddCandidateResult` and `LibraryEntryResult` is optional — no `R<n>` states
`frozen` for those two, though `design.md` §6 shows it.

---

## Ruling on the declared deviation — `AbstractSet`

**The implementer's claim is correct in all three parts, and I verified each
rather than taking it on trust.**

1. `collections.abc` has no `AbstractSet`. Confirmed on the pinned interpreter
   (CPython 3.13.13, provisioned by uv): `"AbstractSet" in dir(collections.abc)`
   → `False`. The name there is `Set`.
2. `AbstractSet` lives in `typing` and is the deprecated PEP 585 alias of
   `collections.abc.Set`.
3. `mypy --strict` does reject the spec's literal line. Registered as **M54**:
   restoring `design.md` §6's exact import produces
   `candidate.py:5: error: Module "collections.abc" has no attribute "AbstractSet"
   [attr-defined]`, and importing the module at runtime raises
   `ImportError: cannot import name 'AbstractSet' from 'collections.abc'`. The
   spec's line does not merely fail type-checking — **it does not run.**

**Ruling: the alias is the right fix, and it is the shipped code that is
correct.** `from collections.abc import Set as AbstractSet` is the established
stdlib-consumer idiom, used precisely because bare `Set` reads as the builtin
`set` at every call site. It adds no dependency (`core` stays at
`dependencies = []`), it satisfies `ruff` and `mypy --strict`, and — the
deciding point — it keeps the parameter annotation reading **exactly**
`known_user_ids: AbstractSet[str]`, which is the text R22 and R23 specify. The
two alternatives are both worse: importing `typing.AbstractSet` pulls in a
deprecated alias for no gain, and renaming the annotation to `Set[str]` would
make R22/R23's own wording stale on the day of the fix. Calling this "a stdlib
import typo fix, not a design decision" is the correct characterisation.

### F6 — but `design.md` §6 is wrong and should be corrected

Spec defects are reportable even when the code is right. `design.md` §6's
signature block still shows

```python
from collections.abc import AbstractSet, Iterable, Mapping
```

which, as M54 demonstrates, is an `ImportError`. Left as is, the design
document contradicts the shipped module, and the next reader — human or agent —
who treats §6 as the authority will reproduce the same failure. `design.md` is
not a frozen document; correcting the import line to the alias form (and noting
why in a sentence) costs nothing.

**Required:** update `specs/week_plan_model/design.md` §6 to the two-line alias
import that shipped. Non-blocking on the code; blocking on the spec staying
truthful.

---

## Observations (not blocking)

- **O1 (M53).** `CandidateNotFound` can stop carrying the offending id —
  `super().__init__("")` and `self.candidate_id = ""` — and the suite stays
  green. `tasks.md` T1 asks for the id to be stored, and `design.md` §6 declares
  `candidate_id: str`, but no `R<n>` states it, so this is not counted as a
  coverage gap. It is still a real degradation: every `CandidateNotFound` would
  surface an empty message. One assertion on `excinfo.value.candidate_id` inside
  the existing `pytest.raises` blocks would close it, and would cost nothing.
- **O2 (M40).** R13's guard in `promote` is unreachable in the observable sense:
  `SlotContents.__post_init__` raises the identical `CandidateNotFound` a line
  later. The same is *not* true of `edit_candidate` and `remove_candidate`,
  whose guards M38 and M39 prove load-bearing. No change requested — an explicit
  guard that states the precondition where the reader looks for it is worth
  keeping — but the register should record that R13's test passes for a reason
  other than the code R13 names.
- **O3.** `design.md` §7's decision to leave `candidate.py` out of
  `SHARED_KERNEL_MODULES` holds up. The module declares no vocabulary, and
  `test_planner_core_has_one_name_fold` already scans **all** of
  `src/planner_core` except `text.py`, so a second fold planted in
  `candidate.py` would be caught today. The source is ASCII-only in fact
  (verified), just not mechanically pinned — which is what §7 says.
- **O4.** Spanish appears in `test_candidate.py` only as fixture data
  (`"Lentejas con chorizo"`, `"Cocer las lentejas."`, `"olla"`). That is test
  content, not a user-facing application string, and matches the precedent set
  by `test_recipe.py`. No finding.

---

## Boundaries

- No Terraform / `*.tfvars` / CI files generated: **[x]** — `init.sh` §4's
  tripwire green, and the only new files are the two named in `design.md` §3.
- No architecture decision from §2 made silently: **[x]** — nothing here touches
  P2–P6. `resolve_author` takes the known-user set as a parameter precisely so
  P2 stays untouched; `Candidate.id`/`author` stay caller-supplied opaque
  strings rather than inventing the `ids` port (`design.md` §8, alternative B,
  gate question 2 approved).
- Frozen requirement docs unmodified: **[x]** — `git status` clean on all five.
- `docs/data_model.md` **is** modified (+9 lines at §5.1), but it is not one of
  the five frozen docs, and the change records the human's own gate ruling on
  `UNKNOWN_USER_ID`. Legitimate. (It is also the document F4 exists to protect.)
- `feature_list.json`: only `"pending"` → `"in_progress"` on feature 5. Nothing
  marked `done`. **[x]**

## Layering (`docs/architecture.md` §3.1)

- `domain/` importing `application/`, `ports/`, an adapter, a handler or an AWS
  SDK: **none.** `candidate.py` imports stdlib (`collections.abc`,
  `dataclasses`, `typing`) plus four sibling `domain` modules — `calendar`,
  `errors`, `recipe`, `text`. **[x]**
- `core` importing `boto3` / an AWS SDK / a Lambda package: **none.** **[x]**
- `core` runtime dependencies: `backend/core/pyproject.toml:6` →
  `dependencies = []`. **[x]**
- Ambient time: `backend/core/tests/test_no_ambient_time.py` passes unmodified
  (14 guard tests green across both guard modules); no exemption widened, no
  allowance loosened, no self-check deleted. `candidate.py` contains no
  `datetime` import at all. **[x]**
- `application/` importing an adapter or handler: n/a — this feature adds no
  `application/` piece, correctly (`design.md` §2). **[x]**
- Adapter imported outside its Lambda's `wiring.py`: n/a — no adapters exist.
  **[x]**

## Conventions (`docs/conventions.md`)

- Naming, `snake_case` / `PascalCase` / `UPPER_SNAKE`: **[x]**
- `mypy --strict`, fully annotated, no new `# type: ignore`: **[x]**
- Double quotes, `from __future__ import annotations`, module docstring first,
  distribution-package imports (no `src.` prefix): **[x]**
- **Comments — three-line ceiling:** `candidate.py` and `test_candidate.py`
  contain **zero** `#` comments. Every docstring is one line, except two
  three-line ones in `test_shared_kernel_guards.py` that this feature did not
  touch. Nothing reproduces a document; `design.md` and gap ids are *pointed*
  at (`candidate.py:39`, `:73`, `:104`). **[x]**
- Language rule — no user-facing Spanish literals outside the messages module:
  **[x]** (see O4).

## Checkpoints

- **C1** — harness files, four docs, five frozen docs unmodified, `./init.sh`
  exit 0: **[x]**
- **C2** — exactly one `in_progress` (feature 5); blocked features carry
  reasons (`init.sh` §4 validates); `progress/current.md` describes this
  session: **[x]**
- **C3** — layering, no AWS SDK, zero runtime deps, ambient-time guard green,
  two Lambda packages, no stray `print()` or context-free TODO in the new code:
  **[x]**
- **C4** — `ruff format --check`, `ruff check`, `mypy`, `pytest -q` (96 passed)
  all green; `core` tests need no clock, network or filesystem; one test module
  per source module (`candidate.py` → `test_candidate.py`): **[x]**, with the
  standing `Clock` contract-suite deferral to feature 14 still unticked by the
  human's own recorded decision (`CHECKPOINTS.md` C4 note).
- **C5** — no stray artefacts; `progress/history.md` carries the feature 4
  entry; feature 5 correctly left `in_progress`: **[x]**
- **C6** — spec folder complete, strict EARS, every `R<n>` cites an `FR-*`,
  every `covers` id appears in an `R<n>`, every `R<n>` has a concrete test,
  all tasks `[x]`, `init.sh` coverage check green (103/103 ids): **[x]**
- **C7** — no `*.tf`, no `.github/workflows/**`, no §2 decision taken silently,
  no requirement invented, frozen docs unedited: **[x]**

---

## Required changes

1. **F1** — add a test that removes a **non-definitive** candidate from a plan
   that has a definitive, asserting the definitive survives (kills M23).
2. **F2** — in `test_to_library_entry_warns_on_a_normalized_name_collision`
   (`test_candidate.py:241`), replace `assert result.recipe is not None` — which
   cannot fail, `recipe` being typed `Recipe` — with assertions on the returned
   recipe's actual content (kills M29).
3. **F3** — in `test_new_candidate_is_the_only_construction_path`, assert the
   returned `Candidate` carries the `id`, `meal` and `author` it was given
   (kills M48, M49).
4. **F4** — pin the literal: `assert UNKNOWN_USER_ID == "unknown-user"`, with a
   one-line comment pointing at `docs/data_model.md` §5.1 (kills M43).
5. **F5** — add `FrozenInstanceError` assertions for `Candidate` and
   `SlotContents`, following `test_recipe.py`'s existing idiom (kills M46, M47).
6. **F6** — correct `specs/week_plan_model/design.md` §6's import line to the
   alias form that shipped; the line as written raises `ImportError`.

Optionally, O1: assert `excinfo.value.candidate_id` inside the existing
`pytest.raises` blocks.

**None of these is a change to `candidate.py`.** Every finding is a missing
assertion, and every mutation was reverted; the source shipped is correct as
written. The one non-test change is F6, to the design document.
