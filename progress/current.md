# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

- **Feature in progress:** 4 — `recipe_model`
- **Started:** 2026-08-23
- **Agent:** leader → spec_author → implementer → reviewer

## Plan

Feature 3's session summary was moved to `progress/history.md` and this file
reset before starting.

Feature 4 `recipe_model` (tier 1, `sdd: true`) is the next actionable feature:
`depends_on: [3]` is satisfied, `covers` = `FR-LIB-03`, `FR-LIB-05`,
`FR-CAND-07`, `FR-MENU-04`. It goes through `spec_author` first, then stops at
the human approval gate before any code.

## Log

- `./init.sh` exit 0 — every gate green, 55 backend tests,
  `done: 3, pending: 11, blocked: 9`. Reported next actionable feature: 4.
- Working tree clean at `fcb0ed0`.
- `spec_author` launched for feature 4. **Spec written**, feature 4
  `pending` -> `spec_ready`: `specs/recipe_model/{requirements,design,tasks}.md`
  (15 R-blocks, 25 tasks, 3 gate questions in `design.md` §9).
- Leader verification of the spec, not relayed:
  - **One `SHALL` per R-block holds** — 15 R-blocks, 15 `SHALL`/`SHALL NOT`;
    the other two matches are the header rule stating the constraint.
  - **Gate 1 is genuinely open.** `FR-RULE-04` names the categories only as
    `(meat, fish, carbohydrates, legumes, vegetarian, …)` with a trailing
    ellipsis, and `G-69` amends `FR-RULE-04` without enumerating the set. So
    the concrete vocabulary is not fixed by a frozen doc and is the human's
    call, exactly as feature 3's unit list was.
- **Finding for the human — `tiempo` is persisted but unrequired.**
  `docs/data_model.md` §1 carries `tiempo` on both `DatosPlatoSemana` and
  `DatosPlatoBiblioteca`, and AP14 returns it in the library list. It appears
  **nowhere** in `docs/requirements.md` — no `FR-*` mentions prep time, so no
  feature `covers` it and no spec can cite it. The spec omitting it is correct
  under "never invent requirements"; the divergence is between the two docs.
  Not a spec defect, and not the leader's to resolve.

- **Human approved all three gate questions of `specs/recipe_model/design.md`
  §9 on 2026-08-23, all as recommended** ("go ahead"):
  1. **Ingredient-category vocabulary:** the five terms `FR-RULE-04` names --
     `MEAT`, `FISH`, `CARBOHYDRATE`, `LEGUME`, `VEGETARIAN`. Nothing invented
     to close its trailing ellipsis.
  2. **`Ingredient.unit` takes an already-resolved `Unit`**, never a raw
     string; the `parse_unit` boundary stays at the call site, not inside
     `Ingredient.__post_init__`.
  3. **No servings, prep-time or attribution field** on `Recipe` or
     `MealSnapshot`. Those stay feature 11's (`numeroComensales`, `G-64`) and
     feature 5's (`anadidoPor`).
- The `tiempo` finding is **NOT** covered by that approval. It needs a
  frozen-doc lift and no permission is standing -- left open for the human.
- `feature_list.json`: feature 4 `spec_ready` -> `in_progress`.
- Implementer launched on `specs/recipe_model/tasks.md` (25 tasks).

- Implementer completed all 25 tasks in `specs/recipe_model/tasks.md`.
  `./init.sh` exit 0, **70 backend tests** (55 before, +15). Full report:
  `progress/impl_recipe_model.md`.
- One spec-text gap found and fixed in the T21 mechanical guard (the literal
  `Unit(` scan as specced would have flagged feature 3's own
  `class Unit(StrEnum):` and `raise UnknownUnit(value)`); resolved with a
  word-boundary regex plus a class-header exclusion, recorded in `tasks.md`
  T21 and `progress/impl_recipe_model.md` §4 rather than silently patched.
- Feature 4 left `in_progress` for the reviewer.

- **T21 fix verified independently by the leader, not relayed.** The guard now
  anchors the `Unit(` pattern on a word boundary and excludes the class header.
  `UnknownUnit(` has no word boundary before `Unit` -- it is one continuous
  identifier -- so it cannot match, and `parse_unit(` never could. No source
  outside the test module was changed to make the guard pass.
- New source: `domain/recipe.py`, `domain/ingredient_category.py`. New tests:
  `tests/domain/test_recipe.py`, `tests/domain/test_ingredient_category.py`,
  plus an added guard in `tests/test_shared_kernel_guards.py`.
- `feature_list.json` untouched by the implementer. No git write command used.
- **Reviewer launched** (automatic after every implementer run).

- **Reviewer: CHANGES_REQUESTED** -> `progress/review_recipe_model.md`.
  Mutation score **11 killed / 13 run**. Tree restored to the pre-review state;
  no `feature_list.json` edit, no git write command.
- **All three blocking findings verified by the leader, not relayed:**
  1. **F2 (R3, `FR-LIB-05`) -- surviving mutant.** Re-declaring
     `Ingredient.unit` as `unit: str` (`domain/recipe.py:22`) passes pytest,
     `mypy --strict` and `ruff`. Confirmed: T14
     (`tests/domain/test_recipe.py:47`) asserts
     `isinstance(ingredient.unit, Unit)` on a value it built with
     `parse_unit("g")` -- true for any annotation. The test checks the runtime
     value, never the declared type.
  2. **F1 (R9) -- surviving mutant.** `CLASS_HEADER_LINE`
     (`tests/test_shared_kernel_guards.py:60`) is `^\s*class\s+\w+\(`, which
     exempts *every* class header, while `design.md` §7 and the regex's own
     comment claim it exempts only `class Unit(StrEnum):`. A keyword argument
     in any other class header hides a real construction. The rest of the
     re-spec is sound -- a plain `Unit("g")` call was caught.
  3. **F3 -- two `# type: ignore[misc]`** at `tests/domain/test_recipe.py:32`
     and `:74`. Confirmed present, and `progress/impl_recipe_model.md` §5/§6
     states none was used. **This is a `CHECKPOINTS.md` C4 violation in its own
     right**, not only a report inaccuracy: C4 requires mypy clean *"with no
     new `# type: ignore`"*. Both are avoidable -- `setattr(recipe, "name",
     "Otro")` inside the `pytest.raises` block raises the same
     `FrozenInstanceError` without an ignore.
- **Non-blocking:** R12's own test does not notice an added
  `origin: Recipe | None` field; the suite catches it via R10's parity
  assertion instead.
- **Confirmed clean by the reviewer:** the `G-05` snapshot test proves the real
  invariant (a constant-category mutant fails it with `- legume / + meat`), the
  shared kernel is consumed rather than re-implemented, and no comment run
  exceeds two lines.

- **Fix round launched 2026-08-24** on the human's go-ahead. Implementer scoped
  to F1, F2, F3 and correcting the record only; R12's non-blocking note left
  out of scope. Reviewer follows automatically.

- **Fix round done** -> new dated section in `progress/impl_recipe_model.md`.
  `./init.sh` exit 0, **71 backend tests** (70 -> 71; +1 self-test for F1).
  Verified by the leader, not relayed:
  - **F3 clear:** zero `# type: ignore` anywhere in `backend/`.
  - **F2 fixed at the declaration:** `test_recipe.py:54` now asserts
    `typing.get_type_hints(Ingredient)["unit"] is Unit`, which no runtime value
    can satisfy vacuously.
  - **F1 narrowed:** `CLASS_HEADER_LINE` is now `^\s*class\s+Unit\(` --
    the enum's own declaration only -- with a self-test covering
    `class ShoppingUnit(StrEnum):` and `class UnitOfMeasure:`.
- **A second-order finding the implementer caught and did not paper over:** the
  reviewer's suggested `setattr(recipe, "name", "Otro")` type-checks clean but
  trips ruff's `B010`, which recommends the direct assignment `mypy` rejects --
  the two gates point opposite ways. Resolved with
  `recipe.__setattr__("name", "Otro")`, clean under all three gates and still
  failing correctly if `frozen=True` is removed. Handed to the reviewer to
  judge as idiomatic or not.
- **Re-review launched.**

- **Session resumed 2026-08-24.** The previous session ended before the
  re-review landed: `progress/review_recipe_model.md` was still the original
  2026-08-23 `CHANGES_REQUESTED` report, stamped *before* the fix round's own
  report. No verdict on the fixes existed.
- `./init.sh` re-run on resume, **exit 0** — 71 backend tests, all seven gates
  green, `done: 3, in_progress: 1, pending: 10, blocked: 9`.
- **Re-review relaunched** (automatic, no permission asked). Scoped to F1, F2,
  F3, the `__setattr__` idiom judgement call, Level 5 mutation testing and a
  full C1–C7 re-walk. Instructed to append a dated 2026-08-24 section to
  `progress/review_recipe_model.md` without overwriting the original review.

- **Re-review verdict: APPROVED** -> dated `2026-08-24` section appended to
  `progress/review_recipe_model.md`; the 2026-08-23 review kept intact as history.
  Mutation score **6 killed / 6 run (100%)**, including both round-1 survivors
  re-run verbatim (M14 `unit: str`, M15 the class-header keyword argument) --
  each now dies. `C4` and `C6` moved `[ ]` -> `[x]`; all seven checkpoints green.
- **Verified by the leader, not relayed:**
  - `CLASS_HEADER_LINE` is `^\s*class\s+Unit\(`
    (`tests/test_shared_kernel_guards.py:61`), with the self-test at `:207-214`
    pinning both halves via `tmp_path`.
  - `typing.get_type_hints(Ingredient)["unit"] is Unit` present at
    `tests/domain/test_recipe.py:54`, added alongside the runtime assertions
    rather than replacing them.
  - Zero `# type: ignore` anywhere under `backend/`.
  - Tree byte-identical to the pre-review state: same 4 modified, same 7
    untracked. Both mutation probes lived in the scratchpad, outside the repo.
- **The `__setattr__` idiom was ruled acceptable and told to stay.** The reviewer
  reproduced the gate conflict itself rather than taking it on trust: `setattr`
  trips `B010` whose autofix is the assignment `mypy --strict` rejects; the
  dunder call is clean under all three gates with no suppression. Proved live by
  M16/M17 (dropping `frozen=True` from `Recipe` and `MealSnapshot` fails both
  tests).
- **Two non-blocking observations left open:** O1 (R12's denylist still misses a
  differently-named `Recipe | None` field -- deliberately out of scope this
  round) and O2, new and cosmetic (a stale docstring at
  `test_shared_kernel_guards.py:76` describing the old wide regex).

## Post-approval vocabulary change (2026-08-24) -- `G-82`

The gate-1 answer recorded above (five terms, 2026-08-23) has been **superseded
by the human**. The entry above is left as written: it is an accurate record of
what was approved on that date, not a live statement of the vocabulary.

- **The human added `EGGS` by hand** to `domain/ingredient_category.py`.
  Legal without a requirement change: `FR-RULE-04` says "at minimum" and ends
  in an ellipsis, so an *addition* rides in on it.
- **The human then struck `VEGETARIAN` and replaced it with `VEGETABLE`.** That
  needed a lift -- `FR-RULE-04`'s frozen text names `vegetarian` explicitly --
  authorised in this session and recorded as **`G-82`, Part R** of
  `docs/gaps_and_resolutions.md`.
- **The reasoning:** the set is one axis, a *predominant ingredient*. A diet
  label overlaps every plant-based member by construction, so the same week
  yields different counts depending on which correct answer each author picked,
  and `FR-AI-04`'s post-generation verification cannot be trusted.
  **Accepted cost, stated at the gate:** a *"vegetarian meals per week"* rule is
  no longer expressible.
- **Closed set, six members:** `MEAT`, `FISH`, `CARBOHYDRATE`, `LEGUME`,
  `VEGETABLE`, `EGGS`.
- **Requirements touched:** `FR-RULE-04` only (the literal enumeration).
  `FR-LIB-03`, `FR-LIB-04` and `FR-AI-04` reach the set by reference and
  inherit the edit with no text change. `G-69` is amended, not superseded.
- **Docs updated by the leader:** `docs/requirements.md` (strikethrough),
  `docs/gaps_and_resolutions.md` (Part R), and all three
  `specs/recipe_model/*.md`. `design.md` §9 gate question 1 is marked answered.
- **Deliberately not touched:** `prototypes/wireframe/Sobremesa.dc.html` (still
  shows a "Comidas vegetarianas" rule -- throwaway prototype, feature 20
  replaces it), `docs/frontend_prototype.md` §83 (an accurate description *of
  that prototype*), and the dated mutant rows in `review_recipe_model.md`.

## `G-82` implementer + reviewer round (2026-08-24)

- **Implementer:** `progress/impl_recipe_model_g82.md`. `VEGETARIAN` ->
  `VEGETABLE` in the enum, the R8 guard regex and its self-test fixture; `EGGS`
  (which the human had added by hand, untested) brought under R4/R5/R8.
  `./init.sh` exit 0, 71 tests, all six gates green.
- **Reviewer:** `progress/review_recipe_model_g82.md`. Verdict
  **CHANGES_REQUESTED**, 9 mutants run, 7 killed. Both survivors were the same
  defect and the reviewer landed the fix under an explicit grant.
- **`F1` — R6 never tested the comparison, only the membership.** `startswith`
  and a 3-char-prefix weakening of `parse_category` both left the suite green;
  under the second, `parse_category("vegetarian")` returned `VEGETABLE` — the
  struck code silently resolving to its replacement, exactly the stale-record
  failure `G-82` creates. Closed: `"vegetarian"` and `"vegetables"` added to the
  rejected-values tuple (`test_ingredient_category.py:45-54`), both mutants now
  die.
- **`F2` — `design.md` §8 alternative A still forbade a sixth category.**
  Unlike §4's, it carried no supersession marker, so it read as a live
  prohibition on what `G-82` decided, aimed straight at the `spec_author`s of
  features 6, 11 and 12. **Fixed by the leader:** the *sixth category* half is
  struck as overtaken; the *open-ended set* half stands unchanged.
- **The leader's `rg -i vegetarian backend/` check was wrong and is
  obsolete.** It was meant to prove the *member* did not survive; applied to
  `backend/` whole it also banned the *word*, and so suppressed the one
  assertion that catches a forgiving comparison. Never re-apply it as written.
  If it survives as a check at all, scope it to `backend/core/src/`.
- **Left open, all non-blocking:** `O3` (R8 self-test `banned` tuple names only
  one member, so dropping one from the alternation could pass in silence), `O1`
  and `O2` carried over from the first review. None can hide a defect today;
  none authorised by the human.

## Next step

**Feature 4 `recipe_model`'s one blocking finding (`F2`) is fixed.** The verdict
on record is still CHANGES_REQUESTED, since it was written before that edit
landed; the reviewer named `F2` as the sole outstanding item and as the
leader's, not its own.

It is still `in_progress` in `feature_list.json` and entirely uncommitted --
both the `done` mark and the commit are the human's call, never the leader's.

Nothing else is in flight. Once feature 4 closes, `./init.sh` reports the next
actionable feature as **9 - `password_policy`**.
