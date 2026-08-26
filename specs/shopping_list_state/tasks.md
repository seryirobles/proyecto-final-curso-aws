# shopping_list_state — Tasks

> Execute in order. Tick `[x]` as each completes.
> Read `design.md` §5–§7 before touching `resync`; the id-supply contract and
> the two determinism notes are load-bearing, not incidental.

## Domain — sources (`backend/core/src/planner_core/domain/shopping.py`, extended)

- [x] T1 — Add `Sequence` to the `collections.abc` import line and add
  `from planner_core.domain.errors import PlannerError` (`design.md` §6).
  Existing feature-7 imports and functions (`in_scope_slots` through
  `required_shopping_items`) are untouched. Covers: R1–R19 (infrastructure).
- [x] T2 — Add `ShoppingItemNotFound(PlannerError)`, carrying `item_id`, same
  shape as `candidate.CandidateNotFound` (`design.md` §6). Covers: R6.
- [x] T3 — Add `InsufficientNewIds(PlannerError)` (`design.md` §5, §6).
  Covers: R12.
- [x] T4 — Add `ShoppingItem` frozen dataclass: `id: str`, `name: str`,
  `quantity: float`, `unit: Unit`, `checked: bool = False` (`design.md` §6).
  Covers: R1.
- [x] T5 — Add `add_item(items, item) -> tuple[ShoppingItem, ...]`: append
  unconditionally, no key check (`design.md` §6). Covers: R2, R19.
- [x] T6 — Add `edit_item(items, item_id, name, quantity) -> tuple[ShoppingItem, ...]`:
  raise `ShoppingItemNotFound` if `item_id` is absent; otherwise replace the
  matching item's `name` and `quantity`, preserving `id`, `unit` and
  `checked` (`design.md` §6). Covers: R3, R4, R6.
- [x] T7 — Add `remove_item(items, item_id) -> tuple[ShoppingItem, ...]`: raise
  if absent; otherwise filter the matching item out (`design.md` §6). Covers:
  R5, R6.
- [x] T8 — Add `check_item(items, item_id)` and `uncheck_item(items, item_id)`,
  each `-> tuple[ShoppingItem, ...]`: raise if absent; otherwise replace the
  matching item's `checked` flag, preserving everything else (`design.md`
  §6). Covers: R6, R7, R8.
- [x] T9 — Add `unchecked_items(items)` and `checked_items(items)`, each
  `-> tuple[ShoppingItem, ...]`: pure filters preserving list order
  (`design.md` §6). Covers: R9.
- [x] T10 — Add `outstanding_amounts(items, required) -> tuple[Ingredient, ...]`:
  accumulate `checked_totals` keyed on `(normalize(name), unit)` over checked
  items only; for each `required` entry compute `required.quantity -
  checked_totals.get(key, 0)`; include in the result only when strictly
  positive (`design.md` §6). Covers: R10, R13.
- [x] T11 — Add `resync(items, required, new_ids) -> tuple[ShoppingItem, ...]`:
  call `outstanding_amounts`; build `matched_index` as the first unchecked
  item's position per key (`setdefault`, single pass); for each outstanding
  entry, overwrite the matched unchecked item's `quantity` only (`design.md`
  §7) if a match exists, else draw the next id from `new_ids` and append a
  new unchecked item, raising `InsufficientNewIds` if `new_ids` is exhausted;
  every checked item and every item whose key never appears in `outstanding`
  passes through unchanged; nothing is ever removed (`design.md` §6). Covers:
  R11, R12, R14, R15, R16, R17, R18, R20, R21.

## Tests (`backend/core/tests/domain/test_shopping.py`, extended)

- [x] T12 — `test_shopping_item_has_exactly_the_fixed_fields` —
  `{f.name for f in dataclasses.fields(ShoppingItem)} == {"id", "name",
  "quantity", "unit", "checked"}` (`design.md` §6, mirrors
  `specs/shopping_aggregation/tasks.md` T17). Covers: R1.
- [x] T13 — `test_add_item_appends_unconditionally` — start from a
  non-empty tuple; assert the new item is the last element and nothing else
  changed. Covers: R2.
- [x] T14 — `test_add_item_does_not_reject_a_matching_normalized_name_and_unit`
  — add an item whose normalized name + unit matches an existing item's;
  assert both survive as separate elements. Covers: R19.
- [x] T15 — `test_edit_item_replaces_name_and_quantity` — edit an existing
  item; assert the returned item's `name` and `quantity` are the new values.
  Covers: R3.
- [x] T16 — `test_edit_item_preserves_unit_and_check_state` — edit a checked
  item's name/quantity; assert `unit` and `checked` are unchanged on the
  result. Covers: R4.
- [x] T17 — `test_edit_item_on_unknown_id_raises_shopping_item_not_found` —
  assert `ShoppingItemNotFound` is raised, carrying the missing id. Covers:
  R6.
- [x] T18 — `test_remove_item_deletes_the_matching_item` — assert the result
  tuple no longer contains that id and every other item is untouched.
  Covers: R5.
- [x] T19 — `test_remove_item_on_unknown_id_raises_shopping_item_not_found`.
  Covers: R6.
- [x] T20 — `test_check_item_sets_checked_true` /
  `test_uncheck_item_sets_checked_false` — assert only the `checked` field of
  the matching item changes. Covers: R7, R8.
- [x] T21 — `test_check_and_uncheck_on_unknown_id_raise` — both functions,
  same assertion as T17/T19. Covers: R6.
- [x] T22 — `test_unchecked_items_and_checked_items_partition_the_list` — a
  mixed list; assert `unchecked_items(items) + checked_items(items)` is a
  reordering of `items` where every element appears exactly once, split
  strictly by `checked`. Covers: R9.
- [x] T23 — `test_outstanding_amounts_computes_required_minus_checked` — one
  checked item `arroz 500 g` (`Unit.GRAM`), `required=(Ingredient("arroz",
  800, Unit.GRAM),)`; assert the result is exactly one `Ingredient("arroz",
  300, Unit.GRAM)` — the acceptance-criterion-7 scenario, computation half
  (`docs/gaps_and_resolutions.md` G-77). Covers: R10.
- [x] T24 — `test_outstanding_amounts_omits_zero_or_negative` — a checked
  item covering the full required quantity (equal or greater); assert that
  key is absent from the result, not present with a zero or negative value.
  Covers: R13.
- [x] T24a — `test_outstanding_amounts_omits_the_exact_zero_boundary` — a
  checked item whose quantity exactly equals the required quantity; assert
  that key is omitted (not present with a zero value) and that `resync`
  neither modifies that checked item nor adds a new row for it. Covers: R13.
- [x] T25 — `test_resync_writes_outstanding_to_the_matching_unchecked_item` —
  an unchecked item and a `required` entry sharing its key with a smaller
  quantity than required; assert that item's `quantity` becomes the
  outstanding amount, its `id` and `unit` unchanged. Covers: R11.
- [x] T26 — `test_resync_creates_a_new_unchecked_item_when_none_matches` — no
  existing item shares the required key; assert a new unchecked item appears
  carrying the outstanding amount and the next id from `new_ids`. Covers:
  R12.
- [x] T27 — `test_resync_new_item_carries_the_remainder_not_the_gross_amount`
  — the acceptance-criterion-7 scenario in full: checked `arroz 500 g`,
  `required` raised to `800 g`; call `resync`; assert the checked item is
  byte-for-byte unchanged and a **new** unchecked item carries `300 g`, not
  `800 g` (`docs/gaps_and_resolutions.md` G-77). Covers: R10, R11, R12, R15.
- [x] T28 — `test_resync_never_removes_a_stale_or_manual_item` — an unchecked
  item whose key never appears in `required`; assert it is still present,
  byte-for-byte unchanged, after `resync`. Covers: R14, R16.
- [x] T29 — `test_resync_never_modifies_a_checked_items_quantity_or_state` —
  a checked item whose key's required amount increases; assert that exact
  item (by `id`, `quantity`, `checked`) is present unchanged in the result —
  the direct `R15` assertion, `FR-SHOP-08`'s core guarantee. Covers: R15.
- [x] T30 — `test_resync_leaves_a_manual_item_absent_from_the_computed_set_untouched`
  — a manually-added item with no corresponding `required` entry at all;
  call `resync` with an unrelated `required` set; assert the manual item is
  still present afterwards — acceptance criterion 4's second half. Covers:
  R16.
- [x] T31 — `test_resync_is_idempotent_across_two_consecutive_presses` — call
  `resync` twice in a row with the same `items` (from the first call's
  result), the same `required`, and an empty `new_ids` the second time
  (nothing new should be needed); assert the two results are equal —
  acceptance criterion 4's first half. Covers: R17.
- [x] T32 — `test_resync_retains_checked_and_new_unchecked_item_sharing_a_key`
  — after T27's scenario, assert both the checked `arroz 500 g` and the new
  unchecked `arroz 300 g` are present simultaneously, as two distinct `id`s —
  the purchase-plus-remainder guarantee (`FR-SHOP-10`, `G-77`). Covers: R18.
- [x] T33 — `test_resync_raises_insufficient_new_ids_when_supply_is_exhausted`
  — a `required` set needing one new item, `new_ids=()`; assert
  `InsufficientNewIds` is raised and no partial item is silently created
  (`design.md` §8 alternative E). Covers: R12.
- [x] T33a — `test_resync_writes_to_the_first_of_two_matching_unchecked_items`
  — two pre-existing unchecked items sharing a normalized name + unit, in
  list order; run `resync`; assert the first receives the write and the
  second is byte-for-byte unchanged (`design.md` §7, §9 gate question 1).
  Covers: R20.
- [x] T33b — `test_resync_preserves_the_matched_items_own_name_and_unit` — an
  existing unchecked item whose raw spelling differs from `required`'s for
  the same normalized key; run `resync`; assert only `quantity` changes on
  the matched item, its own `name`/`unit` survive untouched (`design.md` §7,
  §9 gate question 3). Covers: R21.

## Close-out

- [x] T34 — Record the `R<n> → test` map in
  `progress/impl_shopping_list_state.md` (`docs/verification.md` Level 3).
  Covers: R1–R21.
- [x] T35 — Confirm `backend/core/pyproject.toml` still reads
  `dependencies = []`, and that `uv export --package planner-api --no-dev`
  and `uv export --package planner-ai --no-dev` both resolve with nothing
  added. Covers: R1–R21 (no dependency introduced).
- [x] T36 — Run `./init.sh` and confirm every gate is green: `ruff format`,
  `ruff check`, `mypy --strict`, `pytest` (including
  `test_shared_kernel_guards.py` and `test_no_ambient_time.py`, unmodified
  but re-run), plus the frontend gate. Covers: R1–R21.
