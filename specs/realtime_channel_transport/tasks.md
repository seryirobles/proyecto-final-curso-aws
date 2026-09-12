# realtime_channel_transport — Tasks

> Ordered. Each `[ ]` names the `R<n>` it covers. Backend conditional-GET and
> the re-sync collapse are independent of the frontend engine and may proceed
> in parallel; both are independent of `frontend_spa` (feature 20), which only
> consumes `usePolling` later. Read `design.md` first.

## Backend — conditional-GET short-circuit

- [x] T1 — Add `planner_api/conditional_get.py` with
  `parse_if_none_match(header_value) -> int | None` (single quoted digits →
  int; absent/`*`/list/unquoted/non-numeric → `None`). Covers: R6.
- [x] T2 — Rename `routing._quoted_etag` to public `routing.quoted_etag`
  (same body); update its one existing call site. Covers: R3.
- [x] T3 — Add `current_version_reader` to `RouteSpec` in `routing.py`; set it
  on the five pollable `GET` entries (`_get_week`, `_get_week_summary`,
  `_list_library`, `_list_rules`, `_get_shopping_list`), each calling the
  matching port's `current_version()`. Leave every other route's field at its
  `None` default. Covers: R7.
- [x] T4 — In `handler.py`'s `handle()`, resolve `deps` once per invocation
  (replacing the inline `deps or build_dependencies()` at the dispatch call).
  Covers: R1 (prerequisite refactor, no behavioural change on its own).
- [x] T5 — Before dispatching a `GET` whose `RouteSpec.current_version_reader`
  is set, parse `If-None-Match`; on a parsed value, call the reader and
  compare. On a match, return `_response(304, None, etag=quoted_etag(current))`
  without calling `spec.handler`. On a mismatch or an unparseable header,
  proceed to `spec.handler` unchanged. Covers: R1, R2, R4, R5.
- [x] T6 — `test_conditional_get.py`: parser cases for R6 (absent, `*`, list,
  unquoted, non-numeric, valid). Covers: R6.
- [x] T7 — Handler-level tests: a stale held marker on each of the four
  pollable `GET` routes → `304`, empty body, `ETag` echoed, and the
  underlying read port's list/query method asserted not called (a spy fake).
  A current marker → unchanged `200` path. Covers: R1, R2, R3, R4, R5.
- [x] T8 — Route-table scan test: assert `current_version_reader` is `None`
  for every route except the four pollable `GET` entries (including
  `/v1/generations/{generationId}`, which must stay `None`). Covers: R7.

## Backend — shopping-list re-sync marker-bump collapse

- [x] T9 — Add `save_items(items: Sequence[ShoppingItem]) -> int | None` to
  `ShoppingListRepository` (`planner_core/ports/shopping_list.py`). Empty
  sequence → `None`, no write, no bump. Covers: R8, R9, R10.
- [x] T10 — Implement `save_items` in
  `planner_api/adapters/dynamo/shopping_list.py` via one
  `_table.commit(_pk(), [put_action(...) for ...])` call (empty → `None`
  short-circuit before touching DynamoDB). Covers: R8, R9, R10, R11.
- [x] T11 — Implement `FakeShoppingListRepository.save_items` (batch upsert,
  one `version += 1`, empty → `None`) in `backend/core/tests/support/fakes.py`.
  Covers: R8, R9, R10.
- [x] T12 — In `application/shopping_editing.py`'s `resync_shopping_list`,
  replace the per-item `save_item` loop with computing `changed` once and
  calling `shopping.save_items(changed)`. Covers: R8, R9, R10.
- [x] T13 — Contract suite additions in
  `test_shopping_list_repository_contract.py`: 3-item batch bumps the version
  by exactly 1; empty batch returns `None` and does not bump; the marker
  `Update` action inside `save_items`' transaction carries no
  `ConditionExpression` (mirrors feature 18's existing scan technique).
  Covers: R8, R9, R10, R11.
- [x] T14 — `test_shopping_editing.py`: a re-sync fixture needing 3 differing
  items advances `shopping.current_version()` by exactly 1, not 3. Covers: R8, R9.

## Frontend — pure modules

- [x] T15 — Add `frontend/src/realtime/etag.js`: `quoteMarker(marker)`,
  `parseMarker(headerValue)` (malformed → `null`). Covers: R12, R14.
- [x] T16 — `frontend/tests/realtime/etag.test.js`: round-trip and malformed
  cases. Covers: R12, R14.
- [x] T17 — Add `frontend/src/realtime/pollingEngine.js`'s constants
  (`ACTIVE_INTERVAL_MS`, `BACKGROUND_INTERVAL_MS`, `BACKOFF_CAP_MS`,
  `BACKOFF_JITTER_RATIO`, `CONNECTION_LOST_THRESHOLD`, `design.md` §6) and
  `computeDelay({ isBackgrounded, consecutiveFailures, config }, random)`.
  Covers: R16, R17, R21, R22.
- [x] T18 — Add `resolveMutationMarker(heldMarker, returnedMarker)` to the
  same module. Covers: R25, R26.
- [x] T19 — `frontend/tests/realtime/pollingEngine.test.js` (part 1):
  `computeDelay` — active vs. background base, doubling per failure, cap,
  jitter bounds with an injected deterministic `random`; `resolveMutationMarker`
  — `held+1` vs. mismatch. Covers: R16, R17, R21, R22, R25, R26.
- [x] T20 — Add `createPollingEngine(config, deps)` to `pollingEngine.js`:
  `subscribe`, `getSnapshot`, `applyMutationMarker`, `start`, `dispose`; wires
  `computeDelay`/`resolveMutationMarker` to a fake-timer-driven loop, the
  injected `fetchResource`, and the injected `visibilitySource`. Covers: R12,
  R13, R14, R15, R18, R19, R20, R23, R24.
- [x] T21 — `frontend/tests/realtime/pollingEngine.test.js` (part 2), using
  `vi.useFakeTimers()` and fake `fetchResource`/`visibilitySource` (no DOM):
  `304` keeps data/marker (R13); `200` replaces them (R14); two engine
  instances never share state (R15); background→foreground on the fake
  `visibilitySource` triggers an immediate fetch (R18); N consecutive
  rejected fetches set `connectionLost` (R19, R23); one success afterwards
  clears it and resets the failure count (R20, R24); `applyMutationMarker`
  drives a refetch only on mismatch (R25, R26).
- [x] T22 — Add `frontend/src/realtime/conditionalGet.js`: the default
  `fetchResource` wrapping `fetch` with `If-None-Match`/`ETag`. Covers: R12, R14.
- [x] T23 — `frontend/tests/realtime/conditionalGet.test.js`, stubbing
  `global.fetch`: `304` and `200` mapping. Covers: R12, R14.

## Frontend — the hook

- [x] T24 — Add `frontend/src/hooks/usePolling.js`: `useSyncExternalStore`
  over one `createPollingEngine` instance per call, plus a DOM-backed default
  `visibilitySource` (real `document`/`window`). No decision logic of its
  own — every `R<n>` branch is proven at the engine/module level (T19/T21/T23);
  this task's own test (T24b) proves the hook's React/DOM wiring, per the
  owner's gate ruling (design.md §7, §9). Covers: R12–R26 (wiring).
- [x] T24a — Add `jsdom` and `@testing-library/react` (plus
  `@testing-library/dom` if required as a peer) to `frontend/package.json`
  devDependencies; confirm the exact peer set at install time. Dev-only —
  no new runtime dependency. No `R<n>` (infrastructure for T24b).
- [x] T24b — `frontend/tests/hooks/usePolling.test.js`: opt into `jsdom` for
  this file only via the `// @vitest-environment jsdom` docblock pragma
  (leave `vite.config.js`'s project-wide `environment: "node"` untouched);
  render with `@testing-library/react`'s `renderHook` and a fake injected
  engine/`fetchResource`. Assert: mounting calls the injected engine's
  `start()`; a real `visibilitychange`/`blur`/`focus` DOM event reaches the
  hook's default `visibilitySource` wiring; the engine's `subscribe`
  notification triggers a re-render with the new snapshot; unmounting calls
  `dispose()` exactly once. Does not re-prove R16–R26's decision logic — that
  stays at T19/T21. Covers: R12–R26 (wiring, DOM-backed proof).

## Gate

- [x] T25 — `./init.sh` green (ruff, mypy, pytest unit + contract, frontend
  lint/format/test); update `progress/current.md`.
