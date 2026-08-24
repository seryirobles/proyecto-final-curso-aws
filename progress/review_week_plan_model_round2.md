# Review — feature 5 (`week_plan_model`), round 2

**Verdict:** CHANGES_REQUESTED

All six findings and the observation from round 1 are genuinely closed. I
re-ran every one of the seven named mutants plus `M53` myself and **all eight
died**, each on the assertion the implementer claims kills it — the kill table
in `progress/impl_week_plan_model_review1.md` is accurate in every row. The
new assertions were audited for the "cannot fail" defect that produced F2 and
**none of them has it**: every one was proven live by a mutation. F1's test
asserts behaviour, not shape, exactly as required. F6's correction in
`design.md` §6 is accurate and complete. `./init.sh` green, 100 tests.

The feature is rejected on **one new survivor**, found by probing the code
path the fixes now touch, exactly as instructed: **M57** — `to_library_entry`
degrading its recipe on the *duplicate* path only. It is the residue of my own
round-1 under-specification (F2 asked for "name and one of the collection
fields", and that is precisely what was delivered), so it is not implementer
negligence. It is still a real, unnoticed defect against a numbered
requirement, and the fix is three assertions in a test that already exists.

---

## Re-run mutation register

Numbering continues the house register. Round 1 used M20–M54; the fresh
mutations here are M55–M57. All mutations applied to
`backend/core/src/planner_core/domain/candidate.py` only, one live at a time,
each reverted from a byte-verified backup and hash-checked back to
`sha256 d4048ab5…` before the next. `PYTHONDONTWRITEBYTECODE=1` and a
`__pycache__` purge before **and** after every run, per round 1's harness note.
The whole `core` suite (100 tests) was run for each.

### Part A — the seven named mutants plus O1's, re-run independently

| # | `R<n>` / doc | Mutation | Result |
|---|---|---|---|
| M23 | §4 inv. 2, R17's converse | `remove_candidate`: `definitive_id = None` unconditionally | **killed** — `test_removing_a_non_definitive_candidate_leaves_the_definitive_untouched`, on `assert result.definitive_id == "c1"` (`AssertionError: assert None == 'c1'`) |
| M29 | R20, §4 inv. 3 (`G-26`) | `to_library_entry`: hollow `Recipe(name="", ingredients=(), tools=(), procedure=())` on the duplicate path | **killed** — `test_to_library_entry_warns_on_a_normalized_name_collision`, on `assert result.recipe.name == meal.name` (`assert '' == 'Tomate '`) |
| M43 | R23, `docs/data_model.md` §5.1 | `UNKNOWN_USER_ID = "usuario-desconocido"` | **killed** — `test_unknown_user_id_matches_the_seeded_placeholder_account`, and **only** that test. The pin is the sole mechanism and it does fire on drift. |
| M46 | R3 | `Candidate`: `@dataclass(frozen=True)` → `@dataclass()` | **killed** — `test_candidate_is_frozen` (`DID NOT RAISE FrozenInstanceError`) |
| M47 | R1 | `SlotContents`: `@dataclass(frozen=True)` → `@dataclass()` | **killed** — `test_slot_contents_is_frozen` |
| M48 | R5 | `new_candidate` branches on `meal.name` (`len > 6`) and substitutes `UNKNOWN_USER_ID` for one authoring source | **killed** — `test_new_candidate_is_the_only_construction_path`, on `assert result.author == expected_author` (`assert 'unknown-user' == 'u2'`) |
| M49 | R5, R3 (`FR-CAND-04`) | `new_candidate` discards `author`, always writes `UNKNOWN_USER_ID` | **killed** — same test, `assert 'unknown-user' == 'u1'` |
| M53 | O1, `tasks.md` T1 | `CandidateNotFound.__init__` stores `""` for both the message and `.candidate_id` | **killed 3×** — `test_slot_contents_rejects_a_dangling_definitive_id`, `test_edit_and_remove_raise_on_an_unknown_id`, `test_promote_raises_on_an_unknown_id` |

Eight for eight. Not one of these needed the implementer's word for it; each
failure traceback was read.

### Part B — fresh mutations against the paths the new tests now touch

| # | `R<n>` / doc | Mutation | Result |
|---|---|---|---|
| M55 | R17 | `remove_candidate`: `definitive_id = plan.definitive_id` — **never** clear | **killed** — `test_removing_the_definitive_candidate_clears_it`, via `SlotContents.__post_init__` raising `CandidateNotFound: c1`. F1's new test correctly stays green here. |
| M56 | R18, `G-26` | `to_library_entry` on the duplicate path returns the **existing** colliding name instead of the snapshot's (`name=matches[0]`) — "reuse the entry" rather than "always create a new one" | **killed** — `test_to_library_entry_warns_on_a_normalized_name_collision` (`assert 'tomate' == 'Tomate '`) |
| M57 | **R18** | `to_library_entry` on the duplicate path keeps `name` and `ingredients` but returns `tools=()`, `procedure=()` | **SURVIVED — 100 passed.** See F7. |
| M40 | R13 | `promote`'s guard clause dropped (re-run to re-verify O2) | survived, **equivalent mutant — not a finding.** Confirmed below. |

**Both branches of `remove_candidate`'s conditional are now independently
covered**, which was the point of F1. M23 attacks the `plan.definitive_id !=
candidate_id` branch and dies on the new test; M55 attacks the `==` branch and
dies on R17's test. Neither test masks the other: under M55 the new test
passes, under M23 R17's test passes. That is a clean split, not two tests
happening to cover one branch twice.

**Round-2 totals: 12 mutations run, 10 killed, 1 equivalent, 1 genuine
survivor.**

---

## Audit of the assertions added this round

The instruction was to check every new assertion for the F2 defect — a subject
that is non-optional, a value compared to itself, or a type the annotation
already guarantees. Each one below was proven capable of failing by a live
mutation, not by inspection.

| New / changed assertion | `test_candidate.py` | Can it fail? |
|---|---|---|
| `pytest.raises(FrozenInstanceError)` on `candidate.__setattr__("author", "u2")` | `:51-52` | **Yes** — M46. Same idiom as `test_recipe.py:32-33`, so the house pattern is preserved. |
| `pytest.raises(FrozenInstanceError)` on `plan.__setattr__("definitive_id", "c1")` | `:59-60` | **Yes** — M47. Note the value chosen (`"c1"`) is a *valid* candidate id, so an unfrozen dataclass genuinely succeeds rather than raising something else. |
| `result.definitive_id == "c1"` and `definitive(result) == one` | `:183-184` | **Yes** — M23 kills on the first. This is the behavioural pair F1 demanded, not a tuple-length check. |
| `result.recipe.name == meal.name`, `result.recipe.ingredients == meal.ingredients` | `:280-281` | **Yes** — M29 and M56. Neither is self-comparison: the recipe is a rebuild, so the assertion checks the copy carried the content. |
| `result.id / .meal / .author == expected_*`, all three sources | `:116-118` | **Yes** — M48, M49. The distinct authors (`u1`,`u2`,`u1`) make a cross-source mix-up detectable, which is what R5 is actually about. |
| `UNKNOWN_USER_ID == "unknown-user"` | `:322` | **Yes** — M43, and it is the only test that fails, so the pin is load-bearing rather than incidental. |
| `excinfo.value.candidate_id == "…"` × 4 | `:79`, `:193`, `:196`, `:217` | **Yes** — M53, three separate failures. |

**No new assertion is decoration.** The two that come closest are pre-existing
companions, not additions: `assert isinstance(result, Candidate)`
(`test_candidate.py:114`) restates the return annotation, but it now sits
beside three value assertions rather than standing alone, which was the whole
of F3.

### F4 specifically

M43 confirms the pin fails on drift, and fails **alone** — nothing else in the
suite compensates for it. The comment is the docstring
`"""Pinned value, shared with feature 15's seed account (docs/data_model.md
section 5.1)."""` — **one line, a pointer, not a paraphrase.** It names the
document and section and states no part of the rule the document carries.
Verified against the target: `docs/data_model.md:302-309` does pin
`idUsuario` to exactly `unknown-user` and does say feature 15 does not get to
pick it. Compliant with `docs/conventions.md` § *Comments*.

### F6 specifically

`specs/week_plan_model/design.md` §6 now shows the two-line alias import,
**character-for-character identical** to `candidate.py:5-6`:

```python
from collections.abc import Iterable, Mapping
from collections.abc import Set as AbstractSet
```

The appended note is accurate on all three claims — that the original line
raises `ImportError` (not merely a mypy error), that `collections.abc` has no
`AbstractSet` and the name there is `Set`, and that `typing.AbstractSet` is the
deprecated PEP 585 alias. It also records *why* the alias form was chosen over
bare `Set`, which is the part a future reader would otherwise re-litigate.
Correction accurate and complete; F6 closed.

---

## Blocking finding

### F7 — `to_library_entry` can silently hollow out a library entry on the duplicate path (M57)

`backend/core/tests/domain/test_candidate.py:273-281`

Give `to_library_entry` a branch that fires only when `duplicate_warning` is
`True` and returns the recipe with `tools=()` and `procedure=()` — name and
ingredients intact — and **100 tests still pass**.

The consequence is concrete: a user saves a meal to the library, the name
collides with an existing entry, and the new entry is created (so `G-26` looks
honoured) but arrives with no tools and no procedure. It is a recipe that
cannot be cooked, produced only on the path that warned.

**The `R<n>` it defeats is R18**, not R20. R20 says the system SHALL NOT *omit*
`recipe` when the warning fires, and M57 does not omit it — that is why M29 and
M56 now die and this one does not. R18 says the result's `recipe` field is *"a
new `Recipe` constructed from `meal`'s content"*, unconditionally, with no
exemption for the duplicate case. The suite proves R18 on exactly one of the
two input classes:

- `test_to_library_entry_builds_a_new_recipe_from_the_snapshot`
  (`:259-270`) asserts all five fields — but passes `existing_names=()`, so it
  never reaches the duplicate path.
- `test_to_library_entry_warns_on_a_normalized_name_collision`
  (`:273-281`) reaches the duplicate path — but asserts only `name` and
  `ingredients`.

Between them, `tools`, `procedure` and `category` are unverified on any input
that warns.

**This is my own under-specification from round 1, and I am recording that
plainly.** F2 asked for *"at minimum `result.recipe.name == meal.name` and one
of the collection fields"*, and that minimum is exactly what was delivered. The
implementer followed the instruction. The instruction was too narrow, and the
mutant that walks through the gap is neither contrived nor equivalent.

**Required:** extend `test_to_library_entry_warns_on_a_normalized_name_collision`
with `result.recipe.tools == meal.tools`, `result.recipe.procedure ==
meal.procedure` and `result.recipe.category == meal.category`, so the duplicate
path asserts the same five fields the non-duplicate path already does.

---

## Requirement coverage (FR → R)

Unchanged from round 1 and re-checked against `requirements.md`'s per-`R<n>`
`Implements:` lines. Ten of ten `covers` ids cited.

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

## Test traceability (R → test) — deltas only

Every `R<n>` still has at least one concrete test; the four additions
strengthen four of them. Changes since round 1:

| `R<n>` | Change | Quality now |
|---|---|---|
| R1 | **+** `test_slot_contents_is_frozen` | [x] strong — `frozen=True`, which R1 states literally, is now verified (M47) |
| R3 | **+** `test_candidate_is_frozen` | [x] strong (M46) |
| R5 | value assertions added to the existing test | [x] strong (M48, M49) |
| R10 / R17 | **+** `test_removing_a_non_definitive_candidate_leaves_the_definitive_untouched` | [x] strong — both branches now independently covered (M23, M55) |
| R18 | unchanged | **weak on the duplicate path** — F7 (M57) |
| R20 | content assertions replace the tautology | [x] strong (M29, M56) |
| R23 | **+** `test_unknown_user_id_matches_the_seeded_placeholder_account` | [x] strong on the literal (M43) |

**Every new test maps upward.** Two carry an `R<n>` in their own docstring
(`test_candidate_is_frozen` → R3, `test_slot_contents_is_frozen` → R1). The
other two are explicitly recorded as what they are rather than left
unattributed: `test_removing_a_non_definitive_candidate_leaves_the_definitive_untouched`
cites `docs/architecture.md` §4 invariant 2 — a Level-4 invariant test, a
category `docs/verification.md` recognises — and
`test_unknown_user_id_matches_the_seeded_placeholder_account` cites
`docs/data_model.md` §5.1, defending R23's constant. Neither is an orphan.

## Tasks complete

T1–T41: all `[x]` in `specs/week_plan_model/tasks.md`; zero `[ ]` remain. No
new task was owed — the four additions are review-driven test work, not
unimplemented spec scope.

## Invariants exercised — deltas only

| Invariant | Round 1 | Now |
|---|---|---|
| §4.2 Never silently undo the user's reality | [ ] M23 survived | **[x]** `test_removing_a_non_definitive_candidate_leaves_the_definitive_untouched` — M23 dies on `result.definitive_id`, M55 confirms the opposite branch |
| §4.3 Warn, do not block — library recipe (`G-26`) | [ ] M29 survived | **[x]** M29 and M56 both die. (M57 is R18's problem, not `G-26`'s — the entry *is* created.) |
| §4.9 Removed users leave content behind | [~] placeholder identity unpinned | **[x]** M43 dies on the pinned literal |
| §4.11, §4.3 (candidate), §4.12, §4.1 | [x] | [x] unchanged |

## Boundaries

- No Terraform / `*.tfvars` / CI files: **[x]** — `init.sh` §4 tripwire green.
- No §2 architecture decision taken silently: **[x]** — nothing here touches
  P2–P6.
- Frozen requirement docs unmodified: **[x]** — all five clean in
  `git status`.
- `docs/data_model.md` modified (+9 lines at §5.1): legitimate, not a frozen
  doc, and it records the human's own gate ruling — the ruling F4 now enforces.
- `feature_list.json`: the only diff is feature 5 `"pending"` → `"in_progress"`.
  Nothing marked `done`. **[x]**

## Layering, conventions, gates

- Layering (`docs/architecture.md` §3.1): unchanged and clean — `candidate.py`
  imports stdlib plus four sibling `domain` modules; no `boto3`, no Lambda
  package, no `datetime`. `backend/core/pyproject.toml:6` still
  `dependencies = []`. **[x]**
- Ambient time: `test_no_ambient_time.py` + `test_shared_kernel_guards.py`
  run clean (14 passed) and unmodified. No exemption widened, no allowance
  loosened, no self-check deleted. **[x]**
- **Comment ceiling:** `candidate.py` and `test_candidate.py` contain **zero**
  `#` comments, and every docstring in both — including all four new ones — is
  a single line. Nothing reproduces a document; F4's docstring points at
  `docs/data_model.md` §5.1 and stops. **[x]**
- **ASCII:** verified by byte scan, not by eye — `candidate.py` (5 738 bytes)
  and `test_candidate.py` (12 529 bytes) contain no byte above `0x7F`. **[x]**
- Language rule: Spanish appears in `test_candidate.py` only as fixture data
  (`"Lentejas con chorizo"`, `"Cocer las lentejas."`, `"olla"`, `"Tomate "`),
  matching `test_recipe.py`'s precedent. Not user-facing application strings.
  **[x]**
- `./init.sh`: green end to end — `ruff format`, `ruff check`, `mypy`,
  **100 passed**, plus `prettier`, `eslint`, `vitest`. Run **once**. **[x]**

## No source file changed

**Algorithm: SHA-256 over the file bytes, cross-checked against Git's own
blob hash (SHA-1 of the `blob <len>\0` header plus content, via
`git hash-object`).** Both computed before the first mutation and again after
the last revert, and both agree:

| File | SHA-256 | `git hash-object` |
|---|---|---|
| `candidate.py` | `d4048ab5ae990d721e420266ea55d2599aca01a22129998ef3463e9d84f596d9` | `fa4fa32404c0aeedb71f49a89fdf00b09c705c82` |
| `test_candidate.py` | `2604b7b42a53ce029189b8ffb42d78954260d0a181164c9a93cb5c7ba27814da` | `81d8d83d731edabdf71b81d2a28471c53ab20701` |

`candidate.py`'s blob is `fa4fa324` — **identical to the round-1 baseline and
to the implementer's claim**, independently derived here. `test_candidate.py`
moved from round 1's `90591ee5` to `81d8d83d`, which is the expected and only
change: the test-only edits. No source file in the repository was modified by
the implementer or by me.

## Carried observations

- **O2 (M40) — still accurately described.** Re-run this round: `promote`'s
  guard can still be dropped with the suite green, and O1's new
  `excinfo.value.candidate_id` assertion does **not** kill it — correctly, since
  `SlotContents.__post_init__` raises the identical `CandidateNotFound` with the
  identical `.candidate_id` one line later. Same exception class, same
  constructor argument, same message: no test can distinguish them. Equivalent
  mutant, not a finding. R13's explicit guard remains dead code in the strict
  sense and remains worth keeping, where the reader looks for the precondition.
- **O3 — still accurate.** `candidate.py` is absent from
  `SHARED_KERNEL_MODULES`, whose self-check
  (`test_shared_kernel_guards.py:149-154`) pins the set to exactly `text.py`,
  `units.py`, `recipe.py`, `ingredient_category.py`. The module declares no
  vocabulary, and `test_planner_core_has_one_name_fold` scans **all** of
  `src/planner_core` except `text.py`, so a second fold planted in
  `candidate.py` would be caught today. ASCII-only in fact (byte-verified
  above), just not mechanically pinned — exactly what `design.md` §7 claims.
- **O4 — unchanged.** No user-facing Spanish literal outside fixture data.
- **O5 (new, non-blocking).** The traceability table in
  `progress/impl_week_plan_model.md` was not updated for the four additions:
  R1, R3, R10/R17 and R23 each gained a test that the map does not list.
  Traceability is *complete* in both directions regardless — every `R<n>` still
  names at least one test — so this is document drift, not a coverage gap.
  Worth one edit while F7 is being fixed.
- **O6 (new, non-blocking).** Two **pre-existing** assertions cannot fail, the
  same class F2 existed for. `test_candidate.py:70` —
  `assert not isinstance(plan.definitive_id, (list, tuple, set))` — is
  unreachable-false given line 69 already asserts `== "c1"`. `:229` —
  `assert result.meal.name != "Original"` — is unreachable-false given line 228
  asserts `== "Editado"`. Neither is blocking: R1 and R14 both now have
  assertions proven live by mutation (M47, M20, M51). Named because decoration
  accumulates, and because the round-1 finding was that nobody had noticed the
  last one. (`:335`, `assert orphaned in plan.candidates`, is **not** in this
  class — it is R24's literal statement and a `__post_init__` that filtered
  candidates would break it.)

## Checkpoints

- **C1** — harness files, four docs, five frozen docs unmodified, `./init.sh`
  exit 0: **[x]**
- **C2** — exactly one `in_progress` (feature 5); blocked features carry
  reasons; `progress/current.md` describes this session: **[x]**
- **C3** — layering, no AWS SDK, zero runtime deps, ambient-time guard green,
  two Lambda packages, no stray `print()` or context-free TODO: **[x]**
- **C4** — `ruff format --check`, `ruff check`, `mypy`, `pytest -q`
  (100 passed) all green; `core` tests need no clock, network or filesystem;
  one test module per source module: **[x]**, with the standing `Clock`
  contract-suite deferral to feature 14 unticked by the human's own recorded
  decision (`CHECKPOINTS.md` C4 note).
- **C5** — no stray artefacts; `progress/history.md` carries the feature 4
  entry; feature 5 correctly left `in_progress`: **[x]**
- **C6** — spec folder complete, strict EARS, every `R<n>` cites an `FR-*`,
  every `covers` id appears in an `R<n>`, every `R<n>` has a concrete test,
  all 41 tasks `[x]`, `init.sh` coverage check green (103/103 ids): **[x]**
- **C7** — no `*.tf`, no `.github/workflows/**`, no §2 decision taken
  silently, no requirement invented, frozen docs unedited: **[x]**

## Tree state

- **Tree restored: [x]** `git status --porcelain` is byte-identical to the
  state at the start of this review — same 4 modified (`docs/data_model.md`,
  `feature_list.json`, `progress/current.md`, `progress/history.md`), same 6
  untracked paths. Both feature files hash-verified above. **I edited nothing**
  this round — no test was touched, and every mutation was reverted from the
  scratchpad backup and hash-checked before the next was applied. No git write
  command was run at any point; `feature_list.json` untouched by this review.
  The harness and the `candidate.py` backup live in the session scratchpad,
  outside the repository. `__pycache__` directories were purged as part of the
  harness (gitignored build artefacts, no repository effect).
- After the final revert: `ruff format --check`, `ruff check`, `mypy` and
  `pytest` (100 passed) all green.

---

## Required changes

1. **F7** — in `test_to_library_entry_warns_on_a_normalized_name_collision`
   (`backend/core/tests/domain/test_candidate.py:273-281`), add
   `result.recipe.tools == meal.tools`, `result.recipe.procedure ==
   meal.procedure` and `result.recipe.category == meal.category`, so R18 is
   asserted on the duplicate path with the same five fields the non-duplicate
   test already uses (kills M57).
2. **O5** — add the four new tests to the traceability table in
   `progress/impl_week_plan_model.md` (R1, R3, R10/R17, R23).

Optionally, O6: delete the two pre-existing assertions at
`test_candidate.py:70` and `:229`, neither of which can fail.

**Neither required change touches `candidate.py`.** The source shipped is
correct as written; `fa4fa324` stands.
