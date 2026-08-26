# persistence_ports — Tasks

> Ordered, discrete, each `[ ]` cites the `R<n>` id(s) it covers. Per
> `docs/conventions.md`, every new `@dataclass(frozen=True)` gets its own
> frozen-instance test — named explicitly below, not left implicit.

## Ports

- [ ] T1 — Add `AccountRecord`, `AccountNotFound`, `AccountRepository` in
      `backend/core/src/planner_core/ports/accounts.py`. Covers: R1, R7.
- [ ] T2 — Add `LibraryRecipe`, `RecipeNotFound`, `RecipeRepository` in
      `backend/core/src/planner_core/ports/recipes.py`. Covers: R2, R7.
- [ ] T3 — Add `WeekRepository` in
      `backend/core/src/planner_core/ports/weeks.py`. Covers: R3, R7.
- [ ] T4 — Add `RuleRepository` in
      `backend/core/src/planner_core/ports/rules.py`. Covers: R4, R7.
- [ ] T5 — Add `ShoppingListLockHeld`, `ShoppingListRepository` in
      `backend/core/src/planner_core/ports/shopping_list.py`. Covers: R5, R7.
- [ ] T6 — Add `ArchiveRepository` in
      `backend/core/src/planner_core/ports/archive.py`. Covers: R6, R7.

## Fakes

- [ ] T7 — Add `FakeAccountRepository` to
      `backend/core/tests/support/fakes.py`, replicating create/rename's
      atomic uniqueness-reservation semantics (`design.md` §4, §5.2's trap:
      release the old reservation by looking up the stored record, never by
      re-folding a caller-supplied old name). Covers: R8.
- [ ] T8 — Add `FakeRecipeRepository`. Covers: R8.
- [ ] T9 — Add `FakeWeekRepository`. Covers: R8.
- [ ] T10 — Add `FakeRuleRepository`. Covers: R8.
- [ ] T11 — Add `FakeShoppingListRepository`, whose `acquire_lock` compares
      `expires_at` against the caller-supplied `now` as data, never as a
      guarantee an expired lock is gone (`design.md` §4, §5.3's trap).
      Covers: R8.
- [ ] T12 — Add `FakeArchiveRepository`. Covers: R8.

## Frozen-instance tests (docs/conventions.md)

- [ ] T13 — `test_account_record_is_frozen` in `backend/core/tests/ports/test_accounts.py`
      (attempt an attribute set on `AccountRecord`, expect
      `dataclasses.FrozenInstanceError`). Covers: R1.
- [ ] T14 — `test_library_recipe_is_frozen` in `backend/core/tests/ports/test_recipes.py`.
      Covers: R2.

## Port conformance tests

- [ ] T15 — `backend/core/tests/ports/test_accounts.py`: `isinstance(fake, AccountRepository)`
      plus one behavioural test per method (create, duplicate-name rejection,
      get_by_id/get_by_username round trip including the accent/case fold,
      rename releasing the old reservation, update_credentials, delete,
      `AccountNotFound` on each operation targeting a missing id). Covers: R1, R8.
- [ ] T16 — `backend/core/tests/ports/test_recipes.py`: conformance plus
      save/get/list/delete round trip and `RecipeNotFound`. Covers: R2, R8.
- [ ] T17 — `backend/core/tests/ports/test_weeks.py`: conformance plus
      `get_week` returning `{}` for an unwritten week, `save_slot` round trip,
      `save_week` overwriting every slot at once. Covers: R3, R8.
- [ ] T18 — `backend/core/tests/ports/test_rules.py`: conformance plus `get()`
      returning `RuleSet()` before any `save`, and a save/get round trip.
      Covers: R4, R8.
- [ ] T19 — `backend/core/tests/ports/test_shopping_list.py`: conformance plus
      save/list/delete round trip, `delete_checked_items` as a no-op when
      nothing is checked, `acquire_lock` raising `ShoppingListLockHeld` when
      held and unexpired, succeeding when expired, and `release_lock` as a
      no-op for a non-owner. Covers: R5, R8.
- [ ] T20 — `backend/core/tests/ports/test_archive.py`: conformance plus
      save/get round trip and `save` being a safe overwrite (idempotent
      re-save of an equal `ArchivedWeek`). Covers: R6, R8.

## Storage-agnosticism guard

- [ ] T21 — `backend/core/tests/test_ports_are_storage_agnostic.py`:
      `test_port_signatures_use_only_domain_and_stdlib_types` (R7, mechanical
      scan of the six new port modules' imports against an allowlist of
      stdlib + `planner_core.domain.*` + `planner_core.ports.*`) and
      `test_no_aws_sdk_import` (R10, asserts none of the six port modules,
      the fakes module, or the contract-test tree imports `boto3` or any
      other AWS SDK name). Covers: R7, R10.

## Application-layer usage

- [ ] T22 — `backend/core/tests/application/test_persistence_fakes_compose.py`:
      compose `FakeAccountRepository`, `FakeRecipeRepository`,
      `FakeWeekRepository` and `FakeShoppingListRepository` in one scenario —
      create an account, save a recipe, build a candidate from it
      (`planner_core.domain.candidate`) and write it to a week slot, derive
      the required shopping items (`planner_core.domain.shopping.required_shopping_items`)
      and write them — proving the fakes are usable together the way a real
      use case eventually will (`design.md` §8). Covers: R8.

## Contract suite

- [ ] T23 — `backend/tests/contract/conftest.py`: `sys.path` wiring so
      `from support.fakes import ...` resolves (`design.md` §6). Covers: R9.
- [ ] T24 — `backend/tests/contract/test_account_repository_contract.py`,
      parametrized over `IMPLEMENTATIONS = [FakeAccountRepository]`,
      exercising the same scenarios as T15 through the `Protocol` alone (no
      reference to `Fake*`-specific attributes). Covers: R9.
- [ ] T25 — `backend/tests/contract/test_recipe_repository_contract.py`,
      mirroring T16. Covers: R9.
- [ ] T26 — `backend/tests/contract/test_week_repository_contract.py`,
      mirroring T17. Covers: R9.
- [ ] T27 — `backend/tests/contract/test_rule_repository_contract.py`,
      mirroring T18. Covers: R9.
- [ ] T28 — `backend/tests/contract/test_shopping_list_repository_contract.py`,
      mirroring T19. Covers: R9.
- [ ] T29 — `backend/tests/contract/test_archive_repository_contract.py`,
      mirroring T20. Covers: R9.

## Traceability report

- [ ] T30 — Write `progress/impl_persistence_ports.md` per `docs/verification.md`
      Level 3: the `R<n> → test` map for R1–R10, plus the four acceptance
      criteria explicitly matched to the tasks above.
