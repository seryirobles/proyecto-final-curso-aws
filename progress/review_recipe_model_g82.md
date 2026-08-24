# Review — feature 4 (recipe_model), `G-82` amendment

**Verdict:** CHANGES_REQUESTED

Reviewer session 2026-08-24, third pass on feature 4, scoped to the `G-82`
vocabulary amendment. `./init.sh` exit 0, **71 backend tests**, every gate green
(`ruff format`, `ruff check`, `mypy --strict`, `pytest`, `prettier`, `eslint`,
`vitest`).

**Nine mutations run, seven killed, two survived.** Both survivors are the same
defect family — a weakened comparison in `parse_category` — and both are killed
by the single assertion the implementer deliberately left out. I landed that
assertion under the leader's explicit grant (§ *Ruling*), so the hole is closed
in the tree; the finding still stands against the round as submitted.

**One outstanding required change is not mine to make:** `design.md` §8
rejected alternative A still asserts the set has exactly five terms.

---

## Scope of this pass

Re-review of an already-APPROVED feature. Round 1 (2026-08-23) and round 2
(2026-08-24, F1/F2/F3 fix round) are in `progress/review_recipe_model.md` and
are **not** re-litigated here. This pass covers only what `G-82` changed plus
the two items the leader asked me to report on (O1, O2).

The M4/M19 rows in `progress/review_recipe_model.md` were not touched, per the
constraint. `prototypes/`, `frontend/` and `docs/frontend_prototype.md` were not
read or edited.

---

## Requirement coverage (FR → R)

The `covers` array is unchanged by `G-82`: `FR-LIB-03`, `FR-LIB-05`,
`FR-CAND-07`, `FR-MENU-04`.

- FR-LIB-03:  [x] R1, R2, R3, R4, R5, R6, R7, R8, R15
- FR-LIB-05:  [x] R3, R9, R15
- FR-CAND-07: [x] R10, R11, R12, R13
- FR-MENU-04: [x] R14

`FR-RULE-04` is the requirement `G-82` amended, and it is **not** in this
feature's `covers` array — correctly. `specs/recipe_model/requirements.md` R4
reaches it the way `G-82`'s *"deliberately not changed"* note says the whole
family does: by reference through `FR-LIB-03` (*"the same set stored per
recipe"*). `init.sh` §4 confirms all 103 ids are covered by some feature and no
`covers` cites an unknown id.

R4's amended text names all six members and cites `G-82` explicitly
(`requirements.md:59-64`). No `R<n>` was invented and none was dropped.

## Test traceability (R → test)

Only R4, R5, R6, R8 and R15 are in this amendment's blast radius; the rest are
carried forward from round 2 and were re-run green, not re-derived.

- R1:  [x] `test_recipe_is_frozen`
- R2:  [x] `test_recipe_fields_are_exactly_the_fixed_shape`
- R3:  [x] `test_ingredient_unit_is_the_shared_unit_enum` (+ field-shape test)
- R4:  [x] `test_the_ingredient_category_vocabulary_is_closed` — **asserts all
  six codes *and* all six names, in declaration order.** Proved live by M20,
  M21, M22, M23, M24.
- R5:  [x] `test_parse_category_resolves_every_code` — all six codes. Proved
  live by M20, M21, M23, M24.
- R6:  [x] `test_parse_category_rejects_a_value_outside_the_list` — **was
  insufficient** (M27, M28); closed this pass, see § *Ruling*.
- R7:  [x] `test_unknown_ingredient_category_is_a_planner_error`
- R8:  [x] `test_planner_core_has_one_ingredient_category_vocabulary` — regex
  updated to `VEGETABLE|EGGS`. Proved live for **both new members** by M25 and
  M26 against real planted source, not against the test's own fixture.
- R9:  [x] `test_planner_core_never_constructs_unit_directly` +
  `test_the_class_header_exclusion_only_hides_units_own_declaration`
- R10: [x] `test_meal_snapshot_is_a_distinct_frozen_type`
- R11: [x] `test_snapshot_copies_the_recipes_content`
- R12: [x] `test_meal_snapshot_holds_no_reference_to_the_recipe` (see O1)
- R13: [x] `test_editing_or_deleting_the_library_recipe_leaves_an_existing_snapshot_unchanged`
- R14: [x] `test_snapshot_copies_the_recipes_content`
- R15: [x] `test_the_shared_kernel_modules_are_ascii_only`

### `EGGS` is genuinely covered now

Asked for specifically. `EGGS` was in the source before this round with no test
and no guard. It is now covered, and **proved by mutation, not by inspection**:

| Attack on `EGGS` | Killed by |
|---|---|
| M21 — member deleted from the enum | R4 + R5 tests (2 failures) |
| M24 — code string changed to `"egg"` | R4 + R5 tests (2 failures) |
| M26 — second vocabulary declaring `EGGS` planted in `recipe.py` | R8 guard, reported with file:line |
| M22 — reordered relative to `VEGETABLE` | R4's ordered-list assertion |

## Tasks complete

T1–T25: all `[x]` in `specs/recipe_model/tasks.md`, checked mechanically. Zero
`[ ]`. T1, T7, T8 and T20 were amended to the six-member set and their text
matches what the code and tests now do.

## Invariants exercised (`docs/verification.md` Level 4)

- **Snapshots (`FR-CAND-07`, `G-05`)**: [x] untouched by `G-82`;
  `test_editing_or_deleting_the_library_recipe_leaves_an_existing_snapshot_unchanged`
  is byte-identical to the version round 2 proved live (M2, M18). Not re-mutated
  — re-proving a green invariant a third time is the wandering the protocol
  forbids.
- **Normalised matching (`G-56`)**: [x] not re-implemented here; the feature-3
  fold guard scans the amended module and stays green.
- No other §4 invariant is touched by this feature.

---

## Mutation testing — 7 killed / 9 run

Numbering continues from `progress/review_recipe_model.md` (M1–M19). All
mutations are in **source**; no test file was mutated.

| # | `R<n>` | Mutation | Result |
|---|---|---|---|
| M20 | R4, R5 | `VEGETABLE = "vegetable"` deleted from the enum | [x] killed — `test_the_ingredient_category_vocabulary_is_closed` **and** `test_parse_category_resolves_every_code` (`UnknownIngredientCategory: vegetable`) |
| M21 | R4, R5 | `EGGS = "eggs"` deleted from the enum | [x] killed — same two tests (`UnknownIngredientCategory: eggs`) |
| M22 | R4 | `VEGETABLE` and `EGGS` swapped in declaration order | [x] killed — `test_the_ingredient_category_vocabulary_is_closed`, `At index 4 diff: 'eggs' != 'vegetable'` |
| M23 | R4, R5 | `VEGETABLE = "veg"` (code string changed) | [x] killed — same two tests |
| M24 | R4, R5 | `EGGS = "egg"` (code string changed) | [x] killed — same two tests |
| M25 | R8 | `class FoodKind:` with `VEGETABLE = "vegetable"` appended to `domain/recipe.py` — a second vocabulary whose class name does **not** contain `IngredientCategory`, so only the member-name alternation can catch it | [x] killed — `test_planner_core_has_one_ingredient_category_vocabulary` reports `recipe.py:66` |
| M26 | R8 | same, declaring `EGGS = "eggs"` | [x] killed — same guard, same shape |
| M27 | R6 | `if value == category.value:` → `if value.startswith(category.value):` | [ ] **MUTANT SURVIVED** — 71 passed. See F1. |
| M28 | R6 | `if value == category.value:` → `if value[:3] == category.value[:3]:` | [ ] **MUTANT SURVIVED** — 71 passed. See F1. |

**M25/M26 are deliberately built to isolate the member-name alternation.** The
R8 regex has two arms (`class \w*IngredientCategory\w*` and the
`MEAT|FISH|…|VEGETABLE|EGGS` list). Planting a class named `FoodKind` disarms
the first arm, so the kill proves the second arm really carries `VEGETABLE` and
`EGGS` — the exact question the brief asked. A weakened regex missing either
member would have let both mutants live.

**The requested "break the self-test fixture" mutation was not run**, and
deliberately: that fixture lives in a test file, and mutating tests is
explicitly out of bounds. M25/M26 answer the same question from the source side
and answer it more strongly — they prove the guard fires against real planted
code, not against a string literal the test hands itself. What the fixture route
would have shown is recorded as O3 below instead.

### Re-verification after the landed fix

| # | Mutation re-run against the amended tuple | Result |
|---|---|---|
| M27 | `startswith` | [x] **now killed** — `test_parse_category_rejects_a_value_outside_the_list`, `test_ingredient_category.py:52` |
| M28 | 3-char prefix | [x] **now killed** — same test, same line |

- **Tree restored: [x] with one deliberate exception.** `git status --porcelain`
  is identical to the pre-review snapshot (6 modified, 8 untracked, same paths —
  `diff` against the pre-review capture is empty). Four of the five feature files
  hash byte-identical to their pre-review values:
  `ingredient_category.py 0db0e867`, `recipe.py 0c2b97f2`,
  `test_shared_kernel_guards.py 1b3fdf96`, `test_recipe.py 5e6bfadc`.
  `test_ingredient_category.py` changed `2f994e8e → ef3eaf7e` — **that is my
  landed fix, not a leftover mutation.** No mutation remains anywhere. No git
  write command was run; `feature_list.json` untouched.

---

## Ruling on the `"vegetarian"` rejection case, and on the zero-hits rule

The leader asked me to judge two consequences of the
`rg -i vegetarian backend/` verification step on their merits, and to overrule
the check if it is wrong. **It is wrong as a general rule, but it damaged only
one of the two places it reached.**

### 1. The test tuple — the check was wrong and it cost real coverage. FIXED.

`progress/impl_recipe_model_g82.md` §2 records `"vegetarian"` being kept out of
`test_parse_category_rejects_a_value_outside_the_list`'s tuple *"since the
literal word would violate the zero-hits check"*, on the reasoning that R4/R5's
exhaustive six-member assertions make the omission provable.

**That reasoning is wrong, and mutation proves it.** R4 and R5 prove the enum's
*membership*. They say nothing about how `parse_category` **compares**. M28
leaves the enum untouched and weakens only the comparison:

```python
if value[:3] == category.value[:3]:      # was: if value == category.value:
```

Under it, `parse_category("vegetarian")` returns `IngredientCategory.VEGETABLE`
— the struck code silently resolving to the member that replaced it, which is
precisely the `G-82` failure mode a stale record or prompt would produce. The
full suite stayed **green, 71 passed**. M27 (`startswith`) is the more realistic
mutation of the same family and also survived, resolving `"meatball"` → `meat`,
`"legumes"` → `legume`, `"vegetables"` → `vegetable`.

The four existing rejected values could not catch either: `"MEAT"` and `" meat"`
test case and trim forgiveness, `"dairy"` and `""` share no prefix with any
member. Round 1's M3 (`.strip().lower()`) died on exactly those, which is why
the gap was invisible until now.

**Landed** at `backend/core/tests/domain/test_ingredient_category.py:45-54`:

```python
for rejected in ("MEAT", " meat", "dairy", "", "vegetarian", "vegetables"):
```

`"vegetarian"` is the case the leader named — the one code that used to be valid
— and it kills M28. `"vegetables"` closes the same family from the suffix side
and kills M27; without it a `startswith` weakening still lives. The docstring
now says *"no prefix match"* and states why `"vegetarian"` is there, in two
lines, pointing at `G-82` rather than restating it (`docs/conventions.md`
§ *Comments*).

This edit is the one exception to *never fix the implementer's code*, made under
the leader's explicit grant (*"the tuple is a test, which is squarely yours to
edit"*). It is a test-only change; no source file was modified.

### 2. The docstring — the check was wrong to reach it, but no change is required.

`ingredient_category.py:11-16` reads *"the earlier diet-label member was
struck"* rather than naming `vegetarian`.

**Overruling the check without requiring an edit.** The zero-hits rule had no
business governing prose, and the implementer should not have let it. But judged
on its own merits the docstring is *correct as written*: it makes one claim and
cites `G-69` and `G-82` for the reasoning, which is exactly the
`docs/conventions.md` § *Keep them short* form (*"one claim, one pointer"*). A
reader who needs the struck term follows the citation and finds it, along with
the reasoning a source file must not reproduce. Naming `vegetarian` inline would
also have been fine and marginally clearer; it is not better enough to justify a
round trip, and mandating it would just replace one blunt rule with another.

**The general ruling:** a mechanical zero-hits grep is a fine way to prove a
*member* did not survive, and a bad way to constrain what tests and prose may
say. It should be scoped to the enum body and its consumers — e.g.
`rg -i vegetarian backend/core/src/` — never to `backend/` whole. Applied
whole, it fired on the two places where the word is most useful: the assertion
that the old code is now refused, and the sentence explaining why.

---

## Status of the two open observations

**O1 — R12's denylist still misses a differently-named `Recipe | None` field.
STILL OPEN, unchanged.**
`backend/core/tests/domain/test_recipe.py:95-103` is byte-identical to the file
round 2 cleared (`5e6bfadc`, matching the round-2 baseline). It still checks a
three-name denylist (`id`, `recipe`, `source`) plus `field.type != "Recipe"`, so
a field named `origin` annotated `Recipe | None` slips past; R12's real coverage
remains incidental, via R10's field-parity assertion. Untouched by `G-82` and
correctly out of this round's scope. Not counted against this verdict. A
substring test (`"Recipe" in field.type`) still closes it.

**O2 — stale docstring at `test_shared_kernel_guards.py:76`. STILL OPEN, not
overtaken.**
`_matches_excluding_class_headers` still reads *"skips a class statement's
base-class line entirely"*, which described the pre-F1 wide regex; the exclusion
is now `^\s*class\s+Unit\(` only. This round did edit that file, but only the
`INGREDIENT_CATEGORY_VOCABULARY` constant (`:49-52`) and the R8 self-test
fixture (`:168`) — line 76 was not in the diff, so the amendment did not
overtake it. Still cosmetic: the constant's own comment (`:58-60`) is accurate
and `test_the_class_header_exclusion_only_hides_units_own_declaration` pins the
real behaviour, so nothing here can hide a defect.

**O3 (new, non-blocking) — the R8 self-test exercises 2 of its 6 alternatives.**
`test_shared_kernel_guards.py:164-169`'s `banned` tuple asserts the regex fires
on `MEAT` and `VEGETABLE` only; `FISH`, `CARBOHYDRATE`, `LEGUME` and `EGGS` are
never fed to it. Today that hides nothing — M26 proved `EGGS` live against real
source, and the alternation is correct. But it means a future edit that drops a
member from the alternation passes the self-test in silence, which is exactly
the failure the leader anticipated. Cheap fix: put all six in the `banned`
tuple. Not blocking, and not a surviving mutant.

---

## Documentation consistency with the code

Asked for specifically. Checked every spec and doc that names the vocabulary.

| Location | Status |
|---|---|
| `docs/requirements.md` `FR-RULE-04` | [x] amended with strikethrough, `~~vegetarian~~ **vegetable**`, cites `G-82`. Matches the enum. |
| `docs/gaps_and_resolutions.md` Part R / `G-82` | [x] states the six-member set, the reasoning and the accepted cost. Matches. |
| `docs/data_model.md` `tipoAlimento` (:47-48, and the item-type rows) | [x] reaches the set **by reference** to `FR-RULE-04`, never enumerating it — exactly as `G-82`'s *"deliberately not changed"* note predicts. No edit needed, none made. |
| `specs/recipe_model/requirements.md` R4 | [x] six members named, `G-82` cited. |
| `specs/recipe_model/design.md` §4 vocabulary table | [x] strikethrough row for `VEGETARIAN`, added rows for `VEGETABLE` and `EGGS`, with the gate-amendment note fencing the preserved original recommendation. |
| `specs/recipe_model/design.md` §6 snippet | [x] six members, matching source order. |
| `specs/recipe_model/design.md` §7 R8 guard row | [x] lists `VEGETABLE`/`EGGS` in the scanned member set. Matches the regex. |
| `specs/recipe_model/design.md` §9 gate question 1 | [x] struck and marked answered, cites Part R. |
| `specs/recipe_model/tasks.md` T1, T7, T8, T20 | [x] all six members, consistent with code and tests. |
| **`specs/recipe_model/design.md` §8 alternative A (:302-305)** | **[ ] STALE — see F2.** |
| `backend/` | [x] `rg -i vegetarian backend/` → zero hits **before** my fix; my landed fix adds the literal to one test tuple, deliberately (see § *Ruling*). |

---

## Blocking findings

### F1 — R6 does not notice a forgiving comparison (M27, M28). Closed by the reviewer under grant.

`backend/core/src/planner_core/domain/ingredient_category.py:46`, test at
`backend/core/tests/domain/test_ingredient_category.py:45`.

Two single-line weakenings of `parse_category`'s comparison — `startswith`, and
a 3-character prefix — both left the full suite green at **71 passed**, and the
second accepted `"vegetarian"` as `IngredientCategory.VEGETABLE`. R6 says *"IF a
value is not exactly the code of a member, THEN raise"*; nothing in the suite
tested the word *exactly* against anything but case and whitespace.

Recorded as a finding against the round as submitted. **The missing assertion is
already landed** (§ *Ruling*, part 1) and both mutants now die, so no further
work is required on it.

### F2 — `design.md` §8 rejected alternative A still says the set has five terms

`specs/recipe_model/design.md:302-305`:

> **A. Give `Recipe` a sixth category, or leave the set open-ended.**
> Rejected — see §4. `FR-RULE-04` names exactly five terms; adding more invents
> scope […]

The approved set has **six** members and the code implements six. §4, §6, §7 and
§9 were all amended for `G-82`; §8 A was not, and unlike §4's preserved
recommendation it carries **no supersession marker**, so it reads as a live
prohibition on exactly what `G-82` decided. §4's own surviving line 89 (*"the
five named terms are not"*) is fine — it sits inside the block explicitly fenced
as the `spec_author`'s original recommendation. §8 A has no such fence.

The concrete cost: features 6 (`rules_model`), 11 and 12 all reuse this
vocabulary, and their `spec_author` reads `design.md` §8 for the alternatives
already rejected. As written it tells them a sixth member is out of scope.

**This is not mine to fix** — I hold a grant for the test tuple only, and
`specs/` belongs to the leader and `spec_author`. It needs the same one-line
treatment §4 and §9 received: a dated `G-82` note saying the alternative was
overtaken by the gate decision.

---

## Boundaries

- No Terraform / `*.tfvars` / CI files generated: [x] `init.sh` §4 guardrail
  green; `git status --porcelain` shows none.
- No architecture decision from `docs/architecture.md` §2 made silently: [x] the
  one §2.1 *decide-in-a-spec* item (the ingredient-category list) was decided by
  the **human** in `G-82` and merely executed here. Nothing from §2 proper (P2–P6)
  is touched.
- Frozen requirement docs: `docs/requirements.md` and
  `docs/gaps_and_resolutions.md` **are** modified — **legitimately.** Part R
  opens with *"Directed by the requirements owner, overriding the freeze in
  `CLAUDE.md` in the same manner as Parts I through Q. Granted for
  `requirements.md` only, and for the single enumeration named below."* The diff
  is exactly that: one table cell in `FR-RULE-04` and one appended Part. No agent
  edited them — `impl_recipe_model_g82.md` §5 records them as read-only inputs,
  and the diff's authorship is consistent with that.
- `feature_list.json`: [x] untouched by this round; feature 4 remains
  `in_progress`. Nothing marked `done` by me.
- `core` runtime dependencies: [x] `backend/core/pyproject.toml` still
  `dependencies = []`.

## Layering (`docs/architecture.md` §3.1)

- `domain/` importing `application/`, `ports/`, an adapter, a handler or an AWS
  SDK: [x] none. `recipe.py` imports `dataclasses` + two `domain` modules;
  `ingredient_category.py` imports `enum` + `domain.errors`.
- `core` importing an AWS SDK or a Lambda package: [x] none
  (`rg "boto3|planner_api|planner_ai" backend/core/src/` → no matches).
- `core` runtime dependency declared: [x] none.
- Ambient time: [x] `backend/core/tests/test_no_ambient_time.py` is **unmodified**
  (`git status --porcelain` on it is empty) and green, 8 passed. No exemption
  widened, no allowance loosened, no self-check deleted, no new ambient call.
- `application/` importing an adapter or handler: [x] n/a — no `application/`
  piece exists in this feature.
- Adapter imported outside a `wiring.py`: [x] n/a — no adapter.

## Conventions (`docs/conventions.md`)

- Naming, typing, error handling: [x] unchanged and correct.
  `UnknownIngredientCategory(PlannerError)` carries only the rejected value;
  `parse_category` raises rather than returning `None`.
- Language rule: [x] no user-facing Spanish literal outside a messages module.
  The Spanish recipe names in `test_recipe.py` are fixture *data*, per the
  precedent set in feature 3 and confirmed in round 1.
- **Comment ceiling — three lines, tests included:** [x] measured mechanically
  across all five feature files. Longest run of `#` lines is **3**
  (`test_shared_kernel_guards.py:58-60`, the `CLASS_HEADER_LINE` comment,
  exactly at the ceiling); the amended file's own new comment (`:47-48`) is two.
  My landed docstring is two lines of body and points at `G-82`. No comment
  reproduces a document.
- `# type: ignore`: [x] none anywhere in `backend/`.

## Checkpoints

- C1: [x] harness complete; `./init.sh` exit 0. The two modified frozen docs are
  the owner's own authorised `G-82` lift (Part R), not an agent edit.
- C2: [x] exactly one `in_progress` (feature 4); every `blocked` carries a
  reason; `progress/current.md` describes this session.
- C3: [x] layering clean, two Lambda packages, zero `core` deps, no stray
  `print()`, no context-free TODO.
- C4: [x] `ruff format`, `ruff check`, `mypy --strict` and `pytest` (71) all
  green; no `# type: ignore` anywhere. The `Clock` contract-suite deferral is
  feature 14's and unaffected.
- C5: [x] no stray files; no probe module was created this pass; all mutations
  reverted and hash-verified; `progress/history.md` carries the previous
  session's entry; feature 4 correctly left `in_progress`.
- C6: [ ] ← spec folder complete, strict EARS, every `R<n>` cites an `FR-*`,
  every `FR-*` in `covers` appears in an `R<n>`, every `R<n>` has a concrete
  test, all tasks `[x]`. Unticked on F2 alone: `design.md` §8 A contradicts the
  vocabulary the rest of the spec and the code implement.
- C7: [x] no agent-generated IaC/CI; no `docs/architecture.md` §2 decision taken
  by an agent; no requirement invented; the frozen-doc edits are the owner's own
  documented lift.

---

## Required changes

1. **`specs/recipe_model/design.md:302-305` (§8 alternative A)** — add the same
   dated `G-82` supersession note §4 and §9 already carry. As written it states
   that `FR-RULE-04` names exactly five terms and that a sixth invents scope,
   which contradicts the approved six-member set and would mislead the
   `spec_author` of features 6, 11 and 12. **Leader/`spec_author` edit — outside
   the reviewer's grant.** (F2)

2. *(Already landed by the reviewer — listed for the record, no action needed.)*
   `backend/core/tests/domain/test_ingredient_category.py:45-54` — `"vegetarian"`
   and `"vegetables"` added to the rejected-values tuple, closing M27 and M28.
   The tree is therefore **not** byte-identical to its pre-review state: that one
   file changed `2f994e8e → ef3eaf7e`. Every other file, including both source
   modules, is byte-identical. (F1)

3. *(Optional, non-blocking.)* Put all six member names in the R8 self-test's
   `banned` tuple (`test_shared_kernel_guards.py:164-169`), so a future edit that
   drops one from the alternation cannot pass in silence. (O3)

4. *(Optional, non-blocking, carried over.)* O1 — strengthen R12's test to a
   substring check on `field.type`. O2 — five-word docstring fix at
   `test_shared_kernel_guards.py:76`. Both unchanged by this round and neither
   can hide a defect today.

---

## Note for the next reviewer of this feature

The zero-hits `rg -i vegetarian backend/` rule is now **obsolete** and must not
be re-applied as written: `backend/core/tests/domain/test_ingredient_category.py`
contains the literal `"vegetarian"` **on purpose**, as the assertion that the
struck code is refused. If the intent survives as a check at all, scope it to
`backend/core/src/`.
