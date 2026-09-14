# realtime_channel_transport — Design

> Feature 26 · tier 3 · Read `requirements.md` first. Structural template:
> `specs/rest_api_lambda/` (shell layering) and `specs/rest_api_persistence_and_services/`
> (port/adapter shape). Sources: `docs/architecture.md` §1.1/§1.2.4/§3–§3.1,
> `docs/rest_api_contract.md` §6, `docs/data_model.md` §1.1/§4.4/§4.7/§5.3/§5.5,
> `docs/conventions.md` "Frontend conventions".

## 0. Governing decisions already made elsewhere — not re-opened

- Transport is **adaptive polling + conditional GET**, decided
  (`architecture.md` §1.2.4, `G-88`). This feature does not re-litigate
  WebSocket/AppSync/long-polling.
- Marker wire format is **`ETag`/`If-None-Match`**, a quoted `marcaCambio`
  integer, strong validator (`rest_api_contract.md` §6). Not a custom header,
  not a payload envelope, not a weak validator — already rejected there.
- `current_version()` reads and version-returning writes on `WeekRepository`,
  `RecipeRepository`, `RuleRepository`, `ShoppingListRepository` already exist
  (feature 18, done). This feature calls them; it does not add or change their
  signatures except the one addition in §4.
- `ETag` emission on `200`/mutations and `Cache-Control: no-store` already
  ship (feature 16, done, `rest_api_lambda` `R28`–`R30`). This feature adds
  only `If-None-Match` parsing and the `304` mapping — explicitly named as
  feature 26's job in `specs/rest_api_lambda/design.md` §0.
- The re-sync composition (`resync_shopping_list`, lock acquire/release,
  additive merge, `G-77`'s never-touch-a-checked-item guarantee) is feature
  27, done. This feature amends its write step only — not the lock protocol,
  not the merge logic, not `G-77`'s guarantees.
- No `docs/architecture.md` §2 item is open.
- Frontend: React function components/hooks, Vite, Vitest, plain JS/ESM, no
  new frontend runtime dependency without an approved `design.md` — this one
  adds none. It does add new **dev-only** test dependencies (`jsdom`,
  `@testing-library/react`) for `usePolling.js`'s own test, per the owner's
  gate ruling on frontend testability (§5, §7, §9) — approved 2026-09-11.

## 1. Layering (`docs/architecture.md` §3, §3.1)

| Piece | Layer | Notes |
|---|---|---|
| `planner_api/conditional_get.py` | `planner_api/` (thin, wire-boundary) | Pure `If-None-Match` parsing. No business logic. |
| `planner_api/handler.py` | `planner_api/` (AWS entry point) | Gains the pre-dispatch `304` short-circuit. Still thin. |
| `planner_api/routing.py` | `planner_api/` | `RouteSpec` gains one field naming, per pollable `GET` route, which port read supplies the cheap marker. |
| `planner_core/ports/shopping_list.py` | `planner_core/ports/` | `ShoppingListRepository` gains `save_items` (batch, one bump). |
| `planner_api/adapters/dynamo/shopping_list.py` | `planner_api/adapters/` | Implements `save_items` via one `_table.commit()` call. |
| `planner_core/application/shopping_editing.py` | `planner_core/application/` | `resync_shopping_list` calls `save_items` once instead of `save_item` in a loop. |
| `frontend/src/realtime/etag.js` | frontend, pure module | Marker quoting/parsing — no DOM, no fetch. |
| `frontend/src/realtime/pollingEngine.js` | frontend, pure module + plain factory | All polling decision logic: interval selection, backoff, jitter, connection-loss, the marker`+1` rule. Framework-free. |
| `frontend/src/realtime/conditionalGet.js` | frontend, default adapter | Wraps `fetch` with `If-None-Match`/`ETag`; the engine's default transport, injectable in tests. |
| `frontend/src/hooks/usePolling.js` | frontend, thin hook | `useSyncExternalStore` over one `pollingEngine` instance. No decision logic of its own. |

## 2. Files created / modified

**`backend/lambda_api/src/planner_api/`**
- `conditional_get.py` — new: `parse_if_none_match(header_value: str | None) -> int | None`.
- `routing.py` — `RouteSpec` gains `current_version_reader`; the five pollable
  `GET` entries (`_get_week`, `_get_week_summary`, `_list_library`,
  `_list_rules`, `_get_shopping_list`) set it. `_quoted_etag` renamed to the
  public `quoted_etag` (still lives here) so `handler.py` can reuse it for the
  `304` path instead of duplicating the quoting format.
- `handler.py` — resolves `deps` once per invocation (was inline at the
  `spec.handler(...)` call site); before dispatching a `GET` whose spec names
  a `current_version_reader`, parses `If-None-Match` and short-circuits to
  `304` on a match.

**`backend/lambda_api/tests/`** — `test_conditional_get.py` (pure parser),
extend `test_routing_table.py` / `test_handler.py`-equivalent for the `304`
path and R7's route scoping.

**`backend/core/src/planner_core/`**
- `ports/shopping_list.py` — add `save_items(items: Sequence[ShoppingItem]) -> int | None`.
- `application/shopping_editing.py` — `resync_shopping_list`'s write step
  changes from a per-item `save_item` loop to one `save_items(changed)` call.

**`backend/lambda_api/src/planner_api/adapters/dynamo/shopping_list.py`** —
add `save_items`.

**`backend/core/tests/support/fakes.py`** — `FakeShoppingListRepository.save_items`.

**`backend/tests/contract/test_shopping_list_repository_contract.py`** — new
cases for `save_items` (single bump for a batch; empty batch is a no-op).

**`backend/core/tests/application/test_shopping_editing.py`** — new case:
several differing items in one re-sync bump the marker once.

**`frontend/src/realtime/`** (new) — `etag.js`, `pollingEngine.js`, `conditionalGet.js`.
**`frontend/src/hooks/usePolling.js`** (new).
**`frontend/tests/realtime/`** (new) — `etag.test.js`, `pollingEngine.test.js`, `conditionalGet.test.js`.
**`frontend/tests/hooks/usePolling.test.js`** (new) — `jsdom` via a per-file
`// @vitest-environment jsdom` pragma; the project's only jsdom test (§7, §9).
**`frontend/package.json`** — new devDependencies: `jsdom`,
`@testing-library/react` (+ `@testing-library/dom` if the installed
`@testing-library/react` version needs it as a peer — confirm at
implementation time). Dev-only; no new runtime dependency (§0).

Nothing under `backend/lambda_ai/` is touched. Nothing in `frontend/` beyond
the files above (no view consumes the hook yet — that is feature 20).

## 3. Backend — conditional-GET short-circuit (`R1`–`R7`)

`conditional_get.parse_if_none_match`:

```python
def parse_if_none_match(header_value: str | None) -> int | None:
    """A single `"<digits>"` value -> the int. Anything else (absent, `*`, a
    comma-separated list, unquoted, non-numeric) -> None — R6's "never wrong,
    only slower" fallback (contract.md section 6's stale-marker table)."""
```

`RouteSpec` gains:

```python
current_version_reader: Callable[[dict[str, str], Dependencies], int] | None = None
```

set per pollable route, e.g. `("GET", "/v1/weeks/{weekId}")`:
`lambda path, deps: deps.weeks.current_version(ser.parse_week_id(path["weekId"]))`;
`/summary` shares the same reader (one `SEMANA#` marker); library/rules/shopping-list
readers call their respective `deps.<port>.current_version()` with no arguments.

`handler.py`'s `handle()`: resolve `resolved_deps` once, then, only for a `GET`
whose route names a reader — parse `If-None-Match` from
`(event.get("headers") or {}).get("If-None-Match")` (same fixed-key lookup
`authorizer.py` already uses for `Cookie`, not a new case-insensitive helper);
if it parses and equals `resolved_deps`'s cheap read, return
`_response(304, None, etag=quoted_etag(current))` **without calling
`spec.handler`** (R5 — the expensive `AP8`/`AP14`/`AP18`/`AP22` `Query` never
runs). Otherwise dispatch exactly as today; the handler's own marker-first
read (feature 27, done) still supplies the `200`'s `ETag`.

`/v1/generations/{generationId}` and every non-pollable route get no reader —
R7 is a routing-table fact, checked by asserting the dispatch table's
`current_version_reader` is `None` everywhere except the four resources' `GET`
entries.

## 4. Backend — re-sync marker-bump collapse (`R8`–`R11`)

`ShoppingListRepository.save_items`:

```python
def save_items(self, items: Sequence[ShoppingItem]) -> int | None:
    """Upsert every item in one transaction with a single marcaCambio bump
    (R8, R9). `items` empty -> no write, no bump, returns None (R10) — same
    'no differing items' case `ResyncOutcome.marker` already models."""
```

Dynamo adapter: `_table.commit(_pk(), [_table.put_action(_item_dict(i)) for i in items])`
when `items` is non-empty — `_table.commit` already bundles the data actions
plus **exactly one** `marker_bump_action` into one `TransactWriteItems`
(`_table.py`, unchanged), which is also what already keeps R11 true: the
bump action it appends carries no `ConditionExpression` (same code path every
other mutating adapter method already uses).

`resync_shopping_list`'s write step becomes:

```python
by_id = {item.id: item for item in before}
changed = tuple(item for item in merged if by_id.get(item.id) != item)
marker = shopping.save_items(changed)
```

replacing the per-item `for item in merged: ... shopping.save_item(item)`
loop. `ResyncOutcome.marker`'s type and "`None` means already in sync"
contract are unchanged — only how many underlying writes/bumps produce it.

A household list is far under `TransactWriteItems`'s 100-item limit
(`data_model.md` §4.4, already established for `AP21`'s equivalent batch).

## 5. Frontend — the polling engine (`R12`–`R26`)

**`realtime/etag.js`** (pure):

```js
export function quoteMarker(marker) { /* 41 -> '"41"' */ }
export function parseMarker(headerValue) { /* '"41"' -> 41; else null */ }
```

Same parsing leniency as the backend's `parse_if_none_match` (§3) — a
malformed `ETag` on a response is treated as "no marker", never thrown.

**`realtime/pollingEngine.js`** — a plain, framework-free factory, `useSyncExternalStore`
over a **class of engine object**, not a React hook. All decision logic lives
here so it is unit-testable directly with Vitest under this project's `node`
test environment, independently of how `usePolling.js` itself gets tested
(no DOM, no `jsdom` needed for *this* module's own tests — the split's
rationale stands regardless of the hook-testing approach; see §7):

```js
export function computeDelay({ isBackgrounded, consecutiveFailures, config }, random) { ... }
// R16, R17, R21, R22 — base = isBackgrounded ? config.backgroundIntervalMs
// : config.activeIntervalMs; doubled once per consecutiveFailures, capped at
// config.backoffCapMs, then jittered by ±config.jitterRatio using the
// injected `random` (defaults to Math.random — never read ambient inside the
// pure function itself, mirroring the "Clock is a port" convention translated
// to the frontend: `random`/`now` are parameters, not globals).

export function resolveMutationMarker(heldMarker, returnedMarker) { ... }
// R25, R26 — returnedMarker === heldMarker + 1 -> { marker: returnedMarker,
// refetch: false }; else -> { marker: heldMarker, refetch: true }.

export function createPollingEngine(config, deps) { ... }
// deps = { fetchResource, visibilitySource, setTimeoutFn, clearTimeoutFn, random }
// fetchResource: (heldMarker) => Promise<{ status, marker, body }>
//   (conditionalGet.js's export, by default — R12, R13, R14)
// visibilitySource: { isBackgrounded(): bool, subscribe(cb): unsubscribe }
//   (a DOM-backed default reading document.hidden / document.hasFocus() and
//   listening to visibilitychange + window blur/focus; a test passes a fake
//   exposing the same shape with no document at all)
// Returns { subscribe(listener), getSnapshot(), applyMutationMarker(marker),
//   start(), dispose() }. getSnapshot() -> { data, marker, connectionLost }.
// Each engine instance owns its own held marker / failure count / timer
// (R15) — two instances never share state.
// dispose() sets an internal `disposed` flag; scheduleNext() is then a
// no-op, so an in-flight request's `finally` block cannot re-arm a
// disposed engine (bug found + fixed in feature 20's fix round 2,
// 2026-09-13 — see progress/impl_frontend_spa.md).
```

Failure/success transitions (R19, R20, R23, R24) and the visibility-driven
resume (R18 — on `visibilitySource`'s foreground transition, call the fetch
immediately instead of only rescheduling) live inside `createPollingEngine`,
built on top of `computeDelay`/`resolveMutationMarker`.

**`realtime/conditionalGet.js`** — the default `fetchResource`: wraps the
native `fetch(url, { headers: { "If-None-Match": quoteMarker(heldMarker) } })`,
maps `304` to `{ status: 304, marker: heldMarker, body: null }` and `200` to
`{ status: 200, marker: parseMarker(response.headers.get("ETag")), body: await response.json() }`.
Testable by stubbing `globalThis.fetch` — no DOM needed.

**`hooks/usePolling.js`** — the only piece that is genuinely a React hook:

```js
export function usePolling(url, config) {
  const engine = useMemo(() => createPollingEngine(config, { fetchResource: conditionalGet(url) }), [url, ...]);
  useEffect(() => { engine.start(); return () => engine.dispose(); }, [engine]);
  const snapshot = useSyncExternalStore(engine.subscribe, engine.getSnapshot);
  return { ...snapshot, applyMutationMarker: engine.applyMutationMarker };
}
```

Its own decision logic is nil — every `R<n>` it implements is *proven* at the
`pollingEngine`/`etag`/`conditionalGet` layer, same as before. What changed
under the owner's gate ruling (2026-09-11, §7) is that the hook's **React
wiring itself** (does mounting actually call `engine.start()`; does a
`visibilitychange` DOM event actually reach the engine through the real
`document`-backed default `visibilitySource`; does a snapshot change actually
re-render the calling component; does unmount actually call `dispose()`) is no
longer taken on faith from the module-level tests — it gets its own
`jsdom`-backed test via `@testing-library/react`, `usePolling.test.js` (§9).
The module-level tests still carry every `R<n>`'s correctness proof; the hook
test proves the wiring connects them to a real DOM.

## 6. Values fixed at the spec gate

`docs/architecture.md` §2.1 lists unit list / ingredient categories / servings
count as the "propose in a spec" items; the polling engine's tuning constants
are the same kind of implementation detail — no `FR-*`/`G-*` pins a number,
and G-88 deliberately left "capped, jittered" unquantified.

| Constant | Value | Rationale |
|---|---|---|
| `ACTIVE_INTERVAL_MS` | `5000` | Responsive at this project's 2–10 user scale; `AP29`'s marker read is "muy alta" frequency by design — cheap even at 5 s. |
| `BACKGROUND_INTERVAL_MS` | `30000` | 6× fewer polls while the tab is hidden/blurred, still catches a change within half a minute of refocus in the worst case (R18 makes the actual worst case near-zero). |
| `BACKOFF_CAP_MS` | `60000` | Bounds worst-case inter-attempt gap during an outage to one minute. |
| `BACKOFF_JITTER_RATIO` | `0.2` | ±20% avoids every client in a 2–10 user household retrying in lockstep. |
| `CONNECTION_LOST_THRESHOLD` | `3` | Three consecutive failures (≥15 s of active-tab misses) balances quick user feedback against flagging one dropped request. |

These live as named exports of `pollingEngine.js` (or a `config.js` beside
it), referenced by name in tests — never a bare literal repeated across files
(`conventions.md` naming table, `UPPER_SNAKE` constants).

## 7. Rejected alternatives

**Coupling the single marker bump to the lock-release `DeleteItem` itself**
(one `TransactWriteItems` containing the item puts, the lock release
conditioned on `ownerId`, and the bump). Rejected: it would mean a lock lost
to TTL expiry between acquire and release aborts the item writes too — a new,
undocumented failure mode `data_model.md` §5.3 never specifies a domain
exception for. Batching the item writes with the bump in **their own**
transaction (§4), executed just before the existing separate `release_lock`
call, satisfies "single bump" and the atomicity rule without inventing new
failure semantics on the lock's existing best-effort release.

**(Accepted, reversed 2026-09-11 — owner's gate ruling.)** Testing
`usePolling.js` itself with `jsdom` + `@testing-library/react`, exercising the
hook's actual React wiring (rendering, `visibilitychange` firing through a
real DOM, re-render on engine-state change, unmount cleanup) rather than
treating it as untested plumbing. The spec-ready round proposed leaving it
untested — reasoning that 100% of the decision logic is already proven at the
`pollingEngine`/`etag`/`conditionalGet` layer with zero new dependencies — and
the owner rejected that: proof that the logic is *correct* is not proof that
the *hook* wires a real DOM's visibility events to it correctly, and that
wiring is exactly the part the module-level tests cannot see. `jsdom` and
`@testing-library/react` are added as **dev-only** dependencies for this one
test file (§9); `frontend/vite.config.js`'s project-wide `environment: "node"`
is left unchanged via a per-file `// @vitest-environment jsdom` pragma (§9) —
the many node-only test files pay no jsdom cost.

The `useSyncExternalStore` + plain-factory split (§5) that made this possible
in the first place is **not** rejected and does not change: keeping every
decision branch (interval math, backoff, jitter, marker resolution, failure
counting) in framework-free `pollingEngine.js` means the hook test above only
has to prove wiring, not re-derive R16–R26's correctness with a slower,
DOM-heavy test. Had the logic lived inside the hook itself, the jsdom suite
would have had to cover all of it instead of a thin wiring layer.

**Resetting the visibility-driven timer on refocus instead of polling
immediately (R18).** Cheaper (no guaranteed extra request) but leaves up to
`ACTIVE_INTERVAL_MS` of staleness exactly when the user returns to the tab —
in tension with `G-88`'s "resumes immediately on `visibilitychange`" wording
and `FR-RT-03`'s "re-synchronize state upon reconnection". An immediate poll
costs at most one redundant request and matches the stated behaviour exactly.

## 8. What is NOT here

- Feature 18: `MarcaCambio`, `current_version()`, version-returning writes.
- Feature 16: `ETag` emission on `200`/mutations, `Cache-Control: no-store`,
  routing/auth/error-mapping/serialization shells.
- Feature 27: the re-sync composition's lock protocol, additive merge, `G-77`
  guarantees — only the write step's transaction shape changes here.
- Feature 20: every view, every call site of `usePolling`, the visible
  connection-loss UI element `FR-RT-03`/`G-22` requires, and wiring
  `applyMutationMarker` to each mutation's own fetch call.
- Feature 21: API Gateway caching/throttling of poll traffic.

## 9. Test strategy (feeds `tasks.md`)

- **Conditional GET, backend**: `parse_if_none_match` — valid quoted digits,
  absent, `*`, list, unquoted, non-numeric (R6). Handler-level: a stale marker
  → `304`, no body, `ETag` echoed, and the port's list/query method is
  asserted **not called** (a spy) (R1–R5). A current marker → normal `200`
  path unchanged. Route-table scan: exactly the four pollable resources' `GET`
  entries carry a `current_version_reader` (R7).
- **Re-sync collapse**: contract suite — `save_items` over 3 items bumps the
  version by exactly 1, not 3; empty sequence returns `None` and does not
  bump (R8–R10); a scan/assertion that `save_items`' transaction never sets a
  `ConditionExpression` on the marker `Update` (R11, mirrors feature 18's
  existing scan technique). Application suite — a resync fixture needing 3
  additions bumps `shopping.current_version()` once (R8, R9).
- **Frontend, `etag.js`**: round-trip quote/parse; malformed → `null`.
- **Frontend, `pollingEngine.js`**: `computeDelay` — active vs. background
  base, doubling per failure, cap, jitter bounds (R16, R17, R21, R22, with an
  injected deterministic `random`); engine-level — a fake `fetchResource`
  returning `304` keeps `data`/`marker` (R13); returning `200` replaces them
  (R14); two engine instances never share failure/marker state (R15); a fake
  `visibilitySource` toggling background→foreground triggers an immediate
  fetch call (R18); N consecutive fake-fetch rejections flip `connectionLost`
  (R19, R23), one success clears it and resets the count (R20, R24);
  `applyMutationMarker` — `held+1` stores, else discards and triggers a
  refetch (R25, R26).
- **Frontend, `conditionalGet.js`**: a stubbed `global.fetch` — `304` →
  `{status:304, marker: held, body: null}`; `200` with an `ETag` → parsed
  marker + JSON body.
- **Frontend, `usePolling.js`** (owner's gate ruling, 2026-09-11): a real-DOM
  test, `frontend/tests/hooks/usePolling.test.js`, opting into `jsdom` for
  this file only via the `// @vitest-environment jsdom` docblock pragma at
  its top (confirmed supported by the installed `vitest@^4.1.10`; every other
  test file keeps the project-wide `environment: "node"` from
  `vite.config.js` unchanged). Rendered with `@testing-library/react`'s
  `renderHook`, a fake `createPollingEngine`/`fetchResource` injected the same
  way T20/T21 already fake it (no real network, no real timers):
  - mounting renders and calls the injected engine's `start()`;
  - dispatching a real `visibilitychange`/`blur`/`focus` DOM event on
    `document`/`window` reaches the engine's `visibilitySource` and is
    observed as a call into it (proving the *hook's* default
    `visibilitySource` wiring — not R16–R18's scheduling math, already proven
    in `pollingEngine.test.js`);
  - the engine calling its `subscribe` listener triggers a re-render, and the
    hook's returned snapshot reflects the new value (`useSyncExternalStore`
    wiring);
  - unmounting calls the injected engine's `dispose()` exactly once.
  This test does not re-prove any `R<n>`'s interval/backoff/marker logic —
  that proof stays at the `pollingEngine` layer (T19, T21). It proves the
  wiring T24 previously left unverified.
