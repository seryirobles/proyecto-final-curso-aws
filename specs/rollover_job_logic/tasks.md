# rollover_job_logic — Tasks

> Feature 13 · tier 1. Read `requirements.md` and `design.md` first. The
> `implementer` ticks `[x]` as each completes; the `reviewer` rejects if any
> `[ ]` remains without a documented justification.

- [x] T1 — Create `backend/core/src/planner_core/domain/rollover.py` with its
  module docstring and imports (`collections.abc.Mapping`,
  `dataclasses.dataclass`, `planner_core.domain.calendar.{IsoWeek, SlotRef}`,
  `planner_core.domain.candidate.SlotContents`,
  `planner_core.domain.shopping.{ShoppingItem, unchecked_items}`). Covers:
  R1–R13 (scaffolding).

- [x] T2 — Add `ArchivedWeek` (`@dataclass(frozen=True)`, fields `week`,
  `plans`, `shopping_snapshot`, exactly). Covers: R1.

- [x] T3 — Add `RolloverResult` (`@dataclass(frozen=True)`, fields
  `archived`, `new_current_plans`, `new_next_plans`, `shopping_items`,
  exactly). Covers: R3.

- [x] T4 — Add `archive_week(week, plans, shopping_items)`, constructing an
  `ArchivedWeek` directly from its arguments with no transformation. Covers:
  R4, R5, R6.

- [x] T5 — Add `promote_next_to_current(next_plans)`, returning `next_plans`
  unchanged. Covers: R7.

- [x] T6 — Add `init_empty_next_week()`, taking no parameters and returning
  an empty mapping. Covers: R8, R10.

- [x] T7 — Add `roll_over(former_current_week, former_current_plans,
  former_next_plans, shopping_items)`, composing `archive_week`,
  `promote_next_to_current`, `init_empty_next_week` and
  `shopping.unchecked_items` in that order into one `RolloverResult`. Covers:
  R9, R13 (and, by composition, R4, R5, R6, R7, R8).

- [x] T8 — Create `backend/core/tests/domain/test_rollover.py` covering every
  `R<n>`, including: `ArchivedWeek` field-shape and frozen-ness
  (`pytest.raises(dataclasses.FrozenInstanceError)` on an attempted
  attribute set, R2); `RolloverResult` field-shape (R3); `roll_over`'s
  `archived.week`/`archived.plans`/`archived.shopping_snapshot` equality
  against its inputs (R4, R5, R6), using a `shopping_items` fixture that
  contains at least one checked item so R6's pre-cleanup snapshot is
  distinguishable from R9's post-cleanup result; `roll_over`'s
  `new_current_plans` equality with `former_next_plans`, including a case
  where `former_next_plans` already holds candidates and a definitive (R7);
  `roll_over`'s `new_next_plans` equals `{}` regardless of what
  `former_current_plans`/`former_next_plans` contain (R8);
  `init_empty_next_week`'s signature has zero parameters, asserted via
  `inspect.signature` (R10); `roll_over`'s `shopping_items` result equals the
  checked-item-free subset of the input, in order, for a fixture mixing
  checked and unchecked items (R9); a parametrized case invoking each of
  `archive_week`, `promote_next_to_current` and `init_empty_next_week` twice
  with identical arguments and asserting the two results are equal (R11); a
  case applying `unchecked_items` to a list already containing zero checked
  items and asserting the result equals the input unchanged (R12); a case
  invoking `roll_over` twice with identical arguments and asserting the two
  `RolloverResult` values are equal (R13). Covers: R1–R13.

- [x] T9 — Run `./init.sh`; confirm `ruff format`, `ruff check`, `mypy
  --strict` and `pytest` (deselecting `-m 'not aws'`) all pass, and that
  `test_shared_kernel_guards.py` and `test_no_ambient_time.py` still pass
  unmodified. Covers: R1–R13.
