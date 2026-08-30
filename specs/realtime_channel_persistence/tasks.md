# realtime_channel_persistence — Tasks

> Ordered, discrete, each `[ ]` cites the `R<n>` id(s) it covers. Read
> `design.md` first. All four port amendments are backward-compatible for
> callers that ignore the return value; grep confirms no `application/`
> caller exists yet.

## Ports

- [x] T1 — `backend/core/src/planner_core/ports/weeks.py`: add
      `current_version(self, week: IsoWeek) -> int` with the marker-only /
      strongly-consistent / no-side-effect docstring (`design.md` §3);
      change `save_slot` and `save_week` return `None` → `int`, docstring
      noting the bump is same-operation (`docs/data_model.md` §1.1/§5.5).
      Covers: R1, R4, R5.
- [x] T2 — `backend/core/src/planner_core/ports/recipes.py`: add
      `current_version(self) -> int`; change `save` and `delete` returns
      `None` → `int`. `delete` still raises `RecipeNotFound`. Covers: R1,
      R4, R5.
- [x] T3 — `backend/core/src/planner_core/ports/rules.py`: add
      `current_version(self) -> int`; change `save` return `None` → `int`.
      Covers: R1, R4, R5.
- [x] T4 — `backend/core/src/planner_core/ports/shopping_list.py`: add
      `current_version(self) -> int`; change `save_item`, `delete_item`,
      `delete_checked_items` returns `None` → `int`. `delete_item` still
      raises `ShoppingItemNotFound`. `delete_checked_items` docstring:
      returns the marker, bumps only when it removed ≥ 1 item (R9).
      `acquire_lock` / `release_lock` unchanged (`-> None`, no bump).
      Covers: R1, R4, R5, R9.

## Fakes

- [x] T5 — `FakeWeekRepository` in `backend/core/tests/support/fakes.py`:
      add `versions: dict[IsoWeek, int]`; `current_version` returns
      `versions.get(week, 0)` (R3); `save_slot` / `save_week` bump this
      week's entry in the same method body as the data write and return
      it. Covers: R3, R5, R6, R10.
- [x] T6 — `FakeRecipeRepository`: add `version: int = 0`; `save` /
      `delete` bump and return it; reads do not. Covers: R3, R5, R6, R10.
- [x] T7 — `FakeRuleRepository`: add `version: int = 0`; `save` bumps and
      returns it. Covers: R3, R5, R6, R10.
- [x] T8 — `FakeShoppingListRepository`: add `version: int = 0`;
      `save_item` / `delete_item` bump unconditionally and return it;
      `delete_checked_items` bumps only if it removed ≥ 1 item, always
      returns the current marker; `acquire_lock` / `release_lock` do not
      touch `version`. Covers: R3, R5, R6, R9, R10.

## Conformance tests (`backend/core/tests/ports/`)

- [x] T9 — `test_weeks.py`: `current_version` is `0` before any write;
      `save_slot` and `save_week` each return an `int` greater than the
      prior value and equal to the next `current_version(week)`;
      `get_week` and repeated `current_version` calls do not advance it;
      two distinct `IsoWeek`s carry independent markers. Covers: R1, R2,
      R3, R4, R5.
- [x] T10 — `test_recipes.py`: same shape for `save` / `delete` vs
      `current_version()`; `get` / `list_all` do not advance it. Covers:
      R1, R2, R3, R4, R5.
- [x] T11 — `test_rule_repository.py`: same shape for `save` vs
      `current_version()`; `get` does not advance it. Covers: R1, R2, R3,
      R4, R5.
- [x] T12 — `test_shopping_list.py`: same shape for `save_item` /
      `delete_item`; `list_items` / `current_version` do not advance it;
      `delete_checked_items` with nothing checked returns the marker and
      does **not** advance it, and running it twice leaves the marker
      fixed (Level 4 idempotency); with a checked item present it removes
      that item and does advance; a checked item left in place is
      byte-for-byte untouched; `acquire_lock` / `release_lock` do not
      advance it. Covers: R2, R4, R5, R9.

## Scan test (`backend/core/tests/`)

- [x] T13 — create
      `test_change_marker_is_not_a_write_condition.py`:
      `test_no_mutating_port_method_accepts_an_expected_version` —
      `ast`-scan the four port modules, assert no `*Repository` method
      parameter is in the expected-version denylist except
      `current_version`'s own `week` (`design.md` §6); plus
      `test_the_expected_version_scan_catches_a_planted_parameter`
      parsing an inline mutant. Covers: R7.
- [x] T14 — same file:
      `test_the_change_marker_stays_inside_the_four_port_modules` — regex
      over every `planner_core/**/*.py` and `lambda_api` / `lambda_ai`
      `src/**/*.py`, assert the only hits are `weeks.py`, `recipes.py`,
      `rules.py`, `shopping_list.py`; plus a pattern self-test
      (known-good / known-bad lines). Covers: R12.

## Contract suites (`backend/tests/contract/`)

- [x] T15 — extend `test_week_repository_contract.py`,
      `test_recipe_repository_contract.py`,
      `test_rule_repository_contract.py`,
      `test_shopping_list_repository_contract.py`, each parametrized over
      its existing `IMPLEMENTATIONS`, with: every mutating method advances
      `current_version` and returns exactly the new value; every read
      leaves it unchanged; two successive writes to the same resource both
      succeed with no raise and the marker advances twice (R8, R11);
      `delete_checked_items` with nothing checked is a no-op that does not
      advance the marker (shopping suite only). Covers: R2, R4, R5, R8,
      R9, R11.

## Traceability report

- [x] T16 — write `progress/impl_realtime_channel_persistence.md` per
      `docs/verification.md` Level 3: the `R1..R12 → test` map both
      directions, plus each acceptance criterion matched to tasks, plus
      the Level 5 mutant→killing-test list from `design.md` §8.
