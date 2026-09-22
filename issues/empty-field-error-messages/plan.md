# empty-field-error-messages — plan

## Expected behaviour

Every `E<n>` below is one instance of the same rule, kept separate because the
human may accept the rule for some fields and not others.

### E1
Implements: `FR-UX-03`, `FR-LIB-05`

WHEN a recipe write carries an ingredient whose `unit` is empty, the API SHALL
reject the request with `422` and the detail
`El campo Unidad no puede estar vacío.`

### E2
Implements: `FR-UX-03`, `FR-LIB-03`, `FR-LIB-04`

WHEN a recipe write carries an empty or whitespace-only `name`, the API SHALL
reject the request with `422` and the detail
`El campo Nombre no puede estar vacío.`

### E3
Implements: `FR-UX-03`, `FR-LIB-03`

WHEN a recipe write carries an empty `category`, the API SHALL reject the
request with `422` and the detail
`El campo Categoría no puede estar vacío.`

### E4
Implements: `FR-UX-03`, `FR-LIB-03`

WHEN a recipe write carries an ingredient whose `name` is empty, the API SHALL
reject the request with `422` and the detail
`El campo Nombre del ingrediente no puede estar vacío.`

### E5
Implements: `FR-UX-03`, `FR-LIB-03`, `NFR` invariant 12 (`docs/architecture.md` §4)

WHEN a recipe write carries an ingredient whose `quantity` is absent-valued or
blank, the API SHALL reject the request with `422` and the detail
`El campo Cantidad no puede estar vacío.`

### E6
Implements: `FR-UX-03`, `FR-LIB-03`

WHEN a recipe write carries a blank entry in `tools`, the API SHALL reject the
request with `422` and the detail
`El campo Utensilio no puede estar vacío.`

### E7
Implements: `FR-UX-03`, `FR-LIB-03`

WHEN a recipe write carries a blank entry in `procedure`, the API SHALL reject
the request with `422` and the detail
`El campo Paso de la elaboración no puede estar vacío.`

### E8
Implements: `FR-UX-03`, `FR-SHOP-01`, `FR-SHOP-02`

WHEN a shopping-item write carries an empty `name` or an empty `unit`, the API
SHALL reject the request with `422` and the matching `El campo … no puede estar
vacío.` detail.

### E9
Implements: `FR-LIB-05`, `FR-LIB-03`

WHEN a write carries a filled-in value, the API SHALL keep today's outcome —
accepted if valid, `UNKNOWN_UNIT` / `UNKNOWN_INGREDIENT_CATEGORY` if outside
the fixed list.

The seven field names above are the user-facing strings this fix introduces;
they are pinned by the staged tests, so the human should read them at the gate.

## Fix design

One layer: the wire boundary (`lambda_api`, `docs/architecture.md` §3). `core`
gains only the messages. No frontend change — the SPA already renders the API's
`detail` verbatim (`useLibrary.js:16`, `LibraryView.jsx:108-118`), so the
correct text arrives by itself.

| File | Layer | Change |
|---|---|---|
| `backend/core/src/planner_core/messages.py` | core | The es-ES template and the field names it takes, as constants/one helper — all Spanish text stays in this module (`docs/conventions.md` § *Language policy*). |
| `backend/core/src/planner_core/domain/errors.py` (or beside it) | core/domain | One named exception, e.g. `EmptyField(PlannerError)`, carrying the field name. Invariant 12: the failure is explicit, not a `ValueError` escaping to a 500. |
| `backend/lambda_api/src/planner_api/serialization.py` | lambda_api | A `require_non_empty(value, field)` used by `decode_recipe` (name, category, each tool, each step) and `decode_ingredient` (name, quantity, unit), and by `decode_shopping_item` (name, unit). The check runs **before** `parse_unit`/`parse_category`/`float`. |
| `backend/lambda_api/src/planner_api/errors.py` | lambda_api | One `_TABLE` row: `422`, code `EMPTY_FIELD`, detail from the exception. |
| `docs/rest_api_contract.md` §4 | doc | One row in the exception/status table, beside `UNKNOWN_UNIT`. |

Deliberately **not** in scope: any change to `parse_unit`/`parse_category`
(they stay membership tests, E9), the `quantity > 0` rule (issue 7), the
empty-list rule (issue 8), and `servings`/`estimatedTime` (issue 4, `G-85`).

### Rejected alternatives

**Validate in the frontend hook and never send the request.** It gives faster
feedback and is where the user's attention is. Rejected as *the* fix because
the API is the contract boundary — a blank `quantity` currently produces a
`500` there for any client — though nothing stops a later issue from adding the
client-side guard on top; issue 7 already adds one for `quantity`.

**Widen `parse_unit`/`parse_category` to raise a different exception for `""`.**
Two lines, no new helper. Rejected because it puts wire-shape concerns inside
domain parsers that `core` owns, and it still leaves `name`, `tools`,
`procedure` and `quantity` — four of the seven fields — unchecked.

## Test plan

| Staged | Destination |
|---|---|
| `issues/empty-field-error-messages/tests/backend/lambda_api/tests/test_empty_field_errors.py` | `backend/lambda_api/tests/test_empty_field_errors.py` |

The tests assert the wire outcome (`status`, `code`, `detail`) through
`build_problem_response`, never an exception class, so they constrain the
behaviour and not the shape of the fix.

| `E<n>` | Test | At triage |
|---|---|---|
| E1 | `test_an_unselected_unit_reports_the_empty_unit_message` (reproduction) | **RED** — `assert 'UNKNOWN_UNIT' == 'EMPTY_FIELD'` |
| E2 | `test_an_empty_recipe_name_…`, `test_a_whitespace_only_recipe_name_…` | **RED** — `DID NOT RAISE PlannerError` (the empty name is accepted) |
| E3 | `test_an_unselected_category_…` | **RED** — `assert 'UNKNOWN_INGREDIENT_CATEGORY' == 'EMPTY_FIELD'` |
| E4 | `test_an_empty_ingredient_name_…` | **RED** — `DID NOT RAISE PlannerError` |
| E5 | `test_a_blank_ingredient_quantity_…[None, "", "  "]` | **RED** — the raw `TypeError: float() argument must be…` / `ValueError: could not convert string to float: ''` escapes, which is the `500` |
| E6 | `test_a_blank_tool_entry_…` | **RED** — `DID NOT RAISE PlannerError` |
| E7 | `test_a_blank_procedure_step_…` | **RED** — `DID NOT RAISE PlannerError` |
| E8 | `test_an_unselected_unit_on_a_shopping_item_…`, `test_an_empty_shopping_item_name_…` | **RED** — wrong code, and no raise |
| E9 | `test_a_fully_filled_recipe_still_decodes`, `test_a_filled_in_unit_outside_the_list_still_reports_unknown_unit`, `test_a_filled_in_category_outside_the_list_…`, `test_a_filled_in_shopping_item_still_decodes`, `test_an_absent_estimated_time_is_still_accepted` | GREEN, must stay green |

### Red result at triage (2026-09-22)

Copied to its destination, run, deleted; the live tree was left as found.

```
cd backend && uv run pytest lambda_api/tests/test_empty_field_errors.py -q
12 failed, 5 passed in 0.15s
```

The twelve failures are the three distinct modes of `analysis.md` — wrong code
(2), silently accepted (7), uncaught `ValueError`/`TypeError` (3) — and the
five passes are E9's regressions.

Suites the fix must leave green: `backend/lambda_api/tests/test_serialization.py`,
`backend/lambda_api/tests/test_error_mapping.py`,
`backend/core/tests/domain/test_units.py`,
`backend/core/tests/domain/test_ingredient_category.py`.
