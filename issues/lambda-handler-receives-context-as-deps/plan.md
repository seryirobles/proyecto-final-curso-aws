# Issue 22 — plan

Fix design: the four entry-point modules only (handler layer). In each, replace
`lambda_handler = handle` with `def lambda_handler(event, context)` calling
`handle(event)`, and `deps or build_…()` with `deps if deps is not None else
build_…()`. No new dependency, no Terraform change. Comments stay within 3 lines.

**Expected behaviour**
- **E1:** invoked as `planner_api.handler.lambda_handler(event, context)`, the api SHALL build its dependencies from wiring and SHALL NOT read them from the context. FR-AUTH-02, NFR-ARCH-01.
- **E2:** same for `planner_api.authorizer`. FR-AUTH-09.
- **E3:** same for `planner_api.scheduled`. FR-MENU-08, FR-SHOP-09.
- **E4:** same for `planner_ai.handler`. FR-AI-01, FR-AI-03.
- **E5:** WHEN a caller injects a bundle, `handle` SHALL use it whatever its truthiness. NFR-ARCH-01.
- **E6:** every `handler = "…"` string in `terraform/*.tf` SHALL resolve to a callable taking exactly two required positional parameters. NFR-ARCH-01.

**Tests (staged under `issues/<name>/tests/`, destination in parentheses)**
- `test_api_package_lambda_entry_points.py` (`backend/lambda_api/tests/`): E1, E2, E3, E5, plus two regression tests (wiring failure gives a 500 problem; authorizer denies a missing cookie without building).
- `test_ai_lambda_entry_point.py` (`backend/lambda_ai/tests/`): E4, E5.
- `test_terraform_lambda_handlers.py` (`backend/tests/`): E6 and a guard that the scan finds exactly four handlers.

**Red at triage:** pytest 12 failed / 3 passed (the 3 are the two regressions and the scan guard); `mypy .` 6 `arg-type` errors the fix removes; ruff clean.
