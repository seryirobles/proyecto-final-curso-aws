# empty-field-error-messages — tasks

- [x] T1 — Move `issues/empty-field-error-messages/tests/backend/lambda_api/tests/test_empty_field_errors.py`
  to `backend/lambda_api/tests/`, verbatim. Confirm red: **12 failed, 5 passed**,
  with the three failure modes recorded in `plan.md`. Covers: E1–E8.
- [x] T2 — Add the es-ES message template and the seven field names to
  `backend/core/src/planner_core/messages.py`. No Spanish literal outside that
  module. Covers: E1–E8.
- [x] T3 — Add the named domain exception carrying the field name (core/domain).
  Covers: E1–E8.
- [x] T4 — Add `require_non_empty` in
  `backend/lambda_api/src/planner_api/serialization.py` and apply it in
  `decode_recipe` (name, category, each tool entry, each procedure entry),
  `decode_ingredient` (name, quantity, unit) and `decode_shopping_item`
  (name, unit) — **before** `parse_unit` / `parse_category` / `float`.
  Covers: E1–E8.
- [x] T5 — Map the exception in `backend/lambda_api/src/planner_api/errors.py`:
  `422`, code `EMPTY_FIELD`, detail from the exception. Covers: E1–E8.
- [x] T6 — Add the row to the error table in `docs/rest_api_contract.md` §4.
- [x] T7 — Confirm E9 stayed green and no live suite regressed
  (`test_serialization.py`, `test_error_mapping.py`, the two `core` parser test
  modules). Run `./init.sh` green and record the `E<n>` -> `T<n>` -> test map in
  `progress/impl_empty-field-error-messages.md`.
