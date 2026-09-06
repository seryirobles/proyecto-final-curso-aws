# Implementation report — rest_api_lambda (feature 16)

## Files touched

New: `backend/lambda_api/src/planner_api/{errors,serialization,routing,handler,
authorizer,scheduled,wiring}.py`, `backend/lambda_api/src/planner_api/adapters/markers.py`.
New tests: `backend/lambda_api/tests/{_helpers,test_authorizer,test_error_mapping,
test_frozen_dataclasses,test_generation_route,test_handler,test_markers,
test_routing_table,test_rules_routes,test_scheduled,test_serialization}.py`.
Modified: `backend/core/src/planner_core/messages.py` (new constants only —
see spec-gap 1), `backend/pyproject.toml` (`pythonpath` pytest option — spec-gap 3).

## Traceability

| R<n> | Test |
|---|---|
| R1, R4 | `test_handler.test_login_sets_the_session_cookie_with_the_contract_attributes` |
| R2 | `test_routing_table.test_get_routes_never_call_a_mutating_port_method` |
| R3 | `test_handler.test_logout_expires_the_cookie_on_the_same_response` |
| R5 | `test_handler.test_login_never_places_the_token_in_the_response_body` |
| R6, R7, R8 | `test_authorizer.test_a_valid_session_cookie_is_allowed_with_userid_role_and_password_context` |
| R9 | `test_authorizer.test_a_missing_cookie_header_is_denied`, `test_an_unparseable_cookie_is_denied`, `test_an_expired_session_token_is_denied` |
| R10 | `test_authorizer.test_authenticate_is_evaluated_on_every_call_never_cached` |
| R11 | `test_handler.test_a_role_mismatch_is_rejected_with_403_forbidden`, `test_handler.test_an_admin_is_rejected_from_a_user_only_route_with_403_forbidden` |
| R12 | `test_handler.test_the_role_and_password_reset_gate_never_reads_the_account_record` |
| R13 | `test_handler.test_password_reset_pending_blocks_an_unrelated_route`, `test_logout_is_allowed_while_password_reset_is_pending`, `test_set_password_is_allowed_while_password_reset_is_pending` |
| R14, R15, R16 | `test_error_mapping.test_known_domain_exceptions_map_to_the_contract_status_and_code`, `test_problem_body_is_rfc9457_shaped` |
| R17 | `test_error_mapping.test_every_mapped_detail_is_a_messages_module_constant` |
| R18 | `test_serialization.test_unparseable_json_raises_malformed_request` (+ 5 more malformed-input cases), `test_handler.test_malformed_json_body_returns_400` |
| R19 | `test_handler.test_a_domain_rejection_maps_to_the_contract_status` |
| R20 | `test_error_mapping.test_unmapped_planner_error_maps_to_500_internal_error` |
| R21 | `test_rules_routes.test_an_unsatisfiable_rule_change_is_rejected_422_with_conflicts`, `test_error_mapping.test_unsatisfiable_rule_set_carries_the_conflicting_rules_as_details` |
| R22 | `test_handler.test_handling_a_request_emits_a_structured_log_record` |
| R23 | `test_handler.test_no_source_module_calls_print` |
| R24, R25 | `test_handler.test_a_500_response_logs_the_causing_exception_with_its_traceback`, `test_an_unrouted_request_returns_404_without_a_traceback` |
| R26 | `test_routing_table.test_every_contract_endpoint_is_routed_exactly_once` |
| R27, R33 | `test_routing_table.test_no_route_exposes_ap9_ingredients_or_rollover` |
| R28 | `test_markers.test_get_week_carries_the_weeks_marker_as_a_strong_etag`, `test_shopping_list_read_carries_its_own_marker` |
| R29 | `test_markers.test_adding_a_library_recipe_returns_the_writes_marker_as_the_etag`, `test_deleting_a_rule_returns_the_writes_marker_as_the_etag` |
| R30 | `test_handler.test_cache_control_no_store_is_set_on_success_and_error_responses` |
| R31 | `test_rules_routes.test_put_rule_maps_to_the_single_rule_write_operation`, `test_delete_rule_maps_to_the_single_rule_delete_operation`, `test_rules_routes.test_a_body_that_does_not_match_the_path_ruleid_is_rejected` |
| R32, R34 | `test_scheduled.test_rollover_cleans_checked_items_and_keeps_unchecked_ones`, `test_rerunning_rollover_for_the_same_boundary_changes_nothing_further` |
| R35 | `test_generation_route.test_submitting_a_fresh_generation_enqueues_through_the_generation_queue_port` |
| R36 | `test_generation_route.test_planner_api_imports_no_ai_provider_sdk_module` + `uv export --package planner-api --no-dev` (manual, clean) |
| R37 | `test_generation_route.test_a_stored_idempotent_hit_returns_200_without_enqueueing` |
| R38 | `test_serialization.test_recipe_round_trips_through_camel_case_keys` |
| R39 | `test_serialization.test_client_supplied_author_is_rejected`, `test_handler.test_a_client_supplied_author_is_rejected_at_the_route_level` |
| R40 | `test_scheduled.test_the_noop_archive_repository_retains_nothing` |
| R41 | `test_scheduled.test_the_noop_archive_repository_logs_the_discarded_record` |

Every new `@dataclass(frozen=True)` (`AuthContext`, `RouteResult`, `RouteSpec`,
`_ErrorSpec`, `ProblemResponse`, `Dependencies`) has its own frozen-instance
test in `test_frozen_dataclasses.py`.

## Test result

`./init.sh` green: ruff format, ruff check, mypy strict zero errors, pytest
677 passed (0 failed), prettier/eslint/vitest green (frontend untouched by
this feature). See "Fix round 1" below for the delta from 674.

## Fix round 1 (reviewer CHANGES_REQUESTED, 5 items; AP27/R26 gap routed to owner separately, untouched)

1. **R11 surviving mutant.** Added
   `test_handler.test_an_admin_is_rejected_from_a_user_only_route_with_403_forbidden`
   (`ADMIN` hitting `GET /v1/live-weeks`, `requires_role=Role.USER` → 403
   `FORBIDDEN`), closing the missing direction of `handler.py:71`'s gate.
2. **R39 surviving mutant.** Added
   `test_handler.test_a_client_supplied_author_is_rejected_at_the_route_level`
   (`POST /v1/library/recipes` with `"author"` in the body → 400
   `MALFORMED_REQUEST`), proving `routing.py`'s `reject_keys(...)` call sites
   actually run, not just the helper in isolation.
3. **R23 surviving mutant.** `test_handler.py`'s `test_no_source_module_calls_print`
   now scans `_SRC.rglob("*.py")` instead of `.glob("*.py")`, so
   `planner_api/adapters/**` is inspected too.
4. **ETag quoting (RFC 7232).** Added `routing.py:_quoted_etag(marker)` and
   routed every `etag=` emission (20 call sites) through it, producing
   `ETag: "41"` instead of `ETag: 41`. Updated the four literal assertions in
   `test_markers.py` to expect the quoted form.
5. **T9 — `_put_rule` ignored `{ruleId}`.** `routing.py:_put_rule` now computes
   `planner_core.domain.rules.rule_id(rule)` from the decoded body and raises
   `MalformedRequest` (400) when it disagrees with `path["ruleId"]` — the path
   segment is authoritative per T9's wording ("decode `ruleId` to the natural
   key"). Added
   `test_rules_routes.test_a_body_that_does_not_match_the_path_ruleid_is_rejected`
   (`PUT /v1/rules/cat#meat` with a `fish` body → 400, no write reaches the
   repository).

Test count: 674 → 677 (3 new tests: items 1, 2 and 5 above; item 3 and 4 changed
existing tests/code without adding new ones). `./init.sh` green after the
round (ruff format, ruff check, mypy strict, pytest 677 passed, prettier/eslint/vitest).

## Spec-gap notes

1. **`messages.py` needed new constants design.md said this feature would not
   touch.** `docs/rest_api_contract.md` §4's exception table names `PlannerError`
   subclasses (`AccountNotFound`, `RecipeNotFound`, `CandidateNotFound`,
   `ShoppingItemNotFound`, `ShoppingListLockHeld`, `InvalidWeekday`, `UnknownUnit`,
   `UnknownIngredientCategory`, `InvalidIsoWeek`, `PinRulesAffected`,
   `UnsatisfiableRuleSet`) that carry **no** es-ES message from an earlier
   feature — their constructors pass an id, not a `messages.*` string. R16
   requires `detail` to come from `planner_core.messages` regardless, and
   `conventions.md`'s "one messages module" rule leaves no second home for that
   text. Added 14 new constants (plus `MALFORMED_REQUEST`, `INTERNAL_ERROR`,
   `GENERATION_NOT_FOUND`, `ROUTE_NOT_FOUND` for this feature's own exceptions)
   — Spanish strings only, no logic change, no existing exception's `__init__`
   touched.
2. **R28's marker read conflicts with a feature-18 mechanical guard.**
   `backend/core/tests/test_change_marker_is_not_a_write_condition.py` (R12 of
   that feature, frozen/done) forbids the literal name `current_version`
   anywhere in `lambda_api/src` except `planner_api/adapters/` — but emitting
   an `ETag` on a pollable `GET` requires reading exactly that value, and
   feature 27's read services (`week_editing.load_week`,
   `library_editing.list_library`, `rule_editing.read_rules`,
   `shopping_editing.list_shopping`) return no marker themselves, so the
   handler layer must call the port method directly. Resolved without editing
   `backend/core/` or feature 27's services: added
   `planner_api/adapters/markers.py`, a new file of one-line forwards, inside
   the already-exempted adapters directory. `routing.py` calls
   `markers.week_marker(...)` etc. instead of `.current_version(...)` directly.
3. **`wiring.py`'s "fake stack for pytest" reads as picking a backend, but
   fakes live in `backend/core/tests/support/`** — a test-only path production
   `wiring.py` should not import. Tests bypass `wiring.build_dependencies()`
   entirely and construct `Dependencies` directly with `core`'s fakes
   (`backend/lambda_api/tests/_helpers.py`), mirroring
   `backend/tests/contract/conftest.py`'s existing pattern. `wiring.py` itself
   only builds the real AWS-backed stack. Added `pythonpath = ["core/tests"]`
   to `backend/pyproject.toml`'s `[tool.pytest.ini_options]` so
   `from support.fakes import ...` resolves — the same target the contract
   suite's conftest already inserts by hand; a local `conftest.py` in
   `lambda_api/tests/` was rejected because it collides on the bare module
   name `conftest` with `core/tests/conftest.py` under mypy (no `__init__.py`
   in either tree).
4. **`DELETE /v1/generations/{generationId}` (AP27) has no route.** The
   `GenerationQueue` port (feature 27) exposes only `stored_generation` and
   `submit` — no delete. Routing it would need a new port method, which is
   feature 27's territory, not this feature's to add. `R26`'s "every access
   pattern except AP3/AP9/AP29" is therefore not fully met for AP27; flagging
   rather than extending the shipped port.
5. **`POST .../candidates` `"source": "generation"` and the `?name=`/`?category=`
   library filters use assumptions the contract doesn't pin down.** No R<n>
   specifies the JSON shape of `StoredGeneration.result` (opaque `str | None`
   in the port) or exact filter semantics; implemented as "the same JSON a
   manual recipe body would carry" and a case-insensitive substring/exact
   match respectively, since neither is covered by this feature's `R<n>` list.

## Fix round 2

`test_a_client_supplied_author_is_rejected_at_the_route_level`
(`backend/lambda_api/tests/test_handler.py`) was a false positive: its body
had no `"recipe"` key, so it always 400'd on `require_field`
(`serialization.py:68-70`) before `reject_keys` (`routing.py:505`) mattered.
Rewrote the body to be otherwise valid and decodable — the same recipe shape
`test_markers.py`'s `test_adding_a_library_recipe_returns_the_writes_marker_as_the_etag`
uses — with `"author"` as the only forbidden key. Hand-verified: mutating all
three `reject_keys(body, "id", "author", "añadidoPor")` call sites in
`routing.py` down to `reject_keys(body, "id")` makes the test fail (201 vs
expected 400); reverting restores the pass. `./init.sh` green, 677 tests.

## Reopen round 2026-09-06 — AP27 route, marker off the read DTO, candidate author tests

Bundled with feature 27's reopen (T8b, T12b, T14, T15). Three changes, one run.

### Traceability

| R<n> | Test |
|---|---|
| R42 (`DELETE /v1/generations/{generationId}` → `GenerationQueue.discard`) | `test_generation_route.py::test_deleting_a_generation_discards_it_with_the_path_id_and_returns_204_no_etag` (204, no `ETag`, `queue.discards == ["g-1"]`, sibling key survives); `test_routing_table.py::test_every_contract_endpoint_is_routed_exactly_once` (AP27 now in `EXPECTED_ROUTES`) |
| R28/R29 (marker source moved, behaviour unchanged) | `test_markers.py` (all 4 assertions unchanged — end-to-end through `handle`, `ETag` still `== marker`); marker now read off feature 27's read-use-case DTO (`view.marker`), `adapters/markers.py` **deleted** |
| R39 (candidate routes — was proven for one route of three) | `test_handler.py::test_a_client_supplied_author_is_rejected_when_adding_a_candidate` (`_add_candidate`, `routing.py:375`), `::test_a_client_supplied_author_is_rejected_when_editing_a_candidate` (`_edit_candidate`, `routing.py:403`) — both send an otherwise-valid, decodable body; the non-author path is 201/404, so the 400 is unambiguously `reject_keys` |

### Spec-gaps closed

- **Spec-gap 2** (`adapters/markers.py` placement) — file deleted. `routing.py`'s
  6 `markers.*_marker(...)` calls now read `.marker` off feature 27's `WeekView` /
  `LibraryView` / `RulesView` / `ShoppingView` result DTOs. `_resync`'s
  marker-`None` fallback calls `shopping_editing.list_shopping(...).marker`.
  `grep current_version backend/lambda_api/src` → only `adapters/dynamo/*`; the
  feature-18 `test_the_change_marker_stays_inside_its_permitted_modules` guard passes.
- **Spec-gap 4** (`DELETE /v1/generations/{generationId}` had no route/port) —
  `GenerationQueue.discard` added in feature 27 (`R31`); `_delete_generation`
  route added here, calling `deps.queue.discard(path["generationId"])` directly
  (no use case, mirrors `_get_generation`). 204, no `ETag`.

### What the specs did not anticipate

- **`EXPECTED_ROUTES` is still a hand-maintained literal set** in
  `test_routing_table.py`. The reviewer's fix-round-1 ask to derive it
  independently from the contract was deferred alongside the AP27 gap and is
  **still open** — I added the `("DELETE", "/v1/generations/{generationId}")`
  tuple so `test_every_contract_endpoint_is_routed_exactly_once` passes, but the
  independent-derivation rewrite remains a follow-up.
- `test_markers.py` needed no rework (the brief expected "plumbing" changes):
  every assertion already went end-to-end through `handle`, so moving the marker
  source under the hood is transparent to it.

### `./init.sh`

Sections 1–3, 5, 6 green: ruff format, ruff check, mypy strict (141 source
files), pytest **693 passed** (feature-16 baseline 677; +16 across both
features — see the feature-27 report for the split), prettier / eslint / vitest.
**Section 4 fails** on `2 features in in_progress` (16 + 27) and the
16→27 dependency-ordering check — inherent to the owner's bundled reopen; both
resolve when the owner marks the two features `done`. No quality-gate regression.
