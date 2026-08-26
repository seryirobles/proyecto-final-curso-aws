# generation_request — Tasks

> Feature 10 · tier 1. Read `requirements.md` and `design.md` first. The
> `implementer` ticks `[x]` as each completes; the `reviewer` rejects if any
> `[ ]` remains without a documented justification.

- [x] T1 — Create `backend/core/src/planner_core/domain/generation.py` with
  its module docstring and imports (`calendar.IsoWeek`, `calendar.SlotRef`,
  `calendar.slots_from`, `candidate.SlotContents`, `candidate.definitive`,
  `rules.CategoryCountRule`, `rules.PinRule`, `rules.RuleSet`,
  `rules.apply_override`). Covers: R1–R25 (scaffolding).

- [x] T2 — Add `GenerationMode` (`StrEnum`: `LIBRARY_ONLY`, `AI_ONLY`,
  `MIX`). Covers: R1.

- [x] T3 — Add `RuleOverride` (`@dataclass(frozen=True)`). Covers: R2.

- [x] T4 — Add `effective_rules(shared, override)`: returns `shared`
  unchanged when `override is None`, else `apply_override(shared,
  override.category_counts, override.pins, override.disabled_days)`.
  Covers: R3, R4, R5.

- [x] T5 — Add `PinnedTarget`, `SkippedPin` and `GenerationTargets`
  (`@dataclass(frozen=True)` each). Covers: R6, R7, R8.

- [x] T6 — Add `resolve_targets(week, rules, first_day, occupancy)`: build
  the disabled-day- and today-onward-filtered candidate slot list (reusing
  `slots_from`), the `day_by_number` → `PinRule` → `SlotRef` resolution map,
  then the per-slot skip/pin/open classification pass. Covers: R9, R10,
  R11, R12, R13, R14.

- [x] T7 — Add `remaining_category_counts`'s computation inside
  `resolve_targets`: tally definitive-only occupancy per category across
  the whole `occupancy` mapping, subtract from each rule's `count`, floor
  at zero. Covers: R15.

- [x] T8 — Add `idempotency_key(week, targets, rules, mode)`: canonical
  payload (sorted slot list, sorted rule-set fields, `mode.value`),
  `json.dumps(..., sort_keys=True, separators=(",", ":"))`,
  `hashlib.sha256(...).hexdigest()`. `mode` is a fourth payload field, added
  per the human's explicit override of gate question 3 (2026-08-26) — see
  `design.md` §6, §9. Covers: R16, R17, R18, R19, R25.

- [x] T9 — Add `GenerationRequest` (`@dataclass(frozen=True)`) and
  `GenerationPlan` (`@dataclass(frozen=True)`). Covers: R20.

- [x] T10 — Add `build_plan(request, shared_rules, first_day, occupancy)`
  composing `effective_rules`, `resolve_targets` and `idempotency_key`,
  passing `request.mode` as `idempotency_key`'s fourth argument.
  Covers: R21, R22, R23, R24.

- [x] T11 — Create `backend/core/tests/domain/test_generation.py` covering
  every `R<n>`, including: an `effective_rules` identity/override pair; a
  `resolve_targets` case with a disabled day, a past day (current week), an
  occupied-plain slot, an occupied-plus-pinned slot (asserting the
  `SkippedPin`), an unoccupied-plus-pinned slot, an open slot that already
  holds non-definitive candidates (asserting it is still `open_slots`), and
  a category-count remainder case; an `idempotency_key` equality case (same
  week, targets, rules and mode) and four inequality cases (rules differ,
  targets differ, week differs, mode differs); a `build_plan` case asserting
  all four field equalities, including that `idempotency_key` reflects
  `request.mode`. Covers: R1–R25.

- [x] T12 — Run `./init.sh`; confirm `ruff format`, `ruff check`, `mypy
  --strict` and `pytest` (deselecting `-m 'not aws'`) all pass, and that
  `test_shared_kernel_guards.py` and `test_no_ambient_time.py` still pass
  unmodified. Covers: R1–R25.
