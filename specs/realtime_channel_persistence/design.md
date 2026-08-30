# realtime_channel_persistence — Design

> Feature 18 · tier 2 · `planner_core.ports` + `backend/core/tests/support` +
> `backend/core/tests/ports` + `backend/core/tests` + `backend/tests/contract`
> Read `requirements.md` first. Amends the four repository ports feature 14
> `persistence_ports` created (all `done`); reuses features 4, 5, 6, 8's
> domain value types unchanged.

## 0. What this feature is, and is not

**Is:** four small amendments to existing `typing.Protocol` definitions in
`planner_core/ports/` — a `current_version` read added to each, and a
`-> int` return added to each mutating method — plus the matching in-memory
counters in `backend/core/tests/support/fakes.py`, extended conformance
tests, one new mechanical scan test, and extended contract suites.

**Is not:** a real adapter, an HTTP handler, `wiring.py`, conditional-GET
mechanics, or polling logic. The `MarcaCambio` DynamoDB item, `AP29`'s
`GetItem` shape, the `304` short-circuit and the transport question all
belong to a real adapter (P6) and feature 26 (P5). Nothing here imports
`boto3` or names DynamoDB.

**Deliberately unchanged:** `ShoppingListRepository.acquire_lock` /
`release_lock` keep their `-> None` return and do **not** bump the marker —
they are the `FR-SHOP-10` serialization lock, not a write to shopping-list
content (`docs/data_model.md` §4.4 notes the lock release is where a
*future* single-bump collapse would live; that collapse is out of scope,
`requirements.md` *Scope note*). `AccountRepository` and `ArchiveRepository`
are untouched — `docs/data_model.md` §1 defines no `MarcaCambio` instance
for `USUARIOS` or the archive.

## 1. Layering

`docs/architecture.md` §3, §3.1:

| Piece | Layer | Why |
|---|---|---|
| `current_version` + `-> int` returns on `WeekRepository`, `RecipeRepository`, `RuleRepository`, `ShoppingListRepository` | `planner_core/ports/` | Interface amendments. `int` is a builtin — no new import, so `test_ports_are_storage_agnostic.py`'s allowlist (feature 14, R7) still passes untouched. |
| `Fake*Repository` counter state | `backend/core/tests/support/fakes.py` | `docs/conventions.md` § *Tests*: fakes for our own ports live here so contract tests reuse them. |
| Conformance tests (`tests/ports/test_*.py`) | `backend/core/tests/ports/` | One module per port already exists; extend, do not add. |
| `test_change_marker_is_not_a_write_condition.py` (R7, R12) | `backend/core/tests/` | Same technique and directory level as `test_no_ambient_time.py` / `test_ports_are_storage_agnostic.py` / `test_no_recipe_metadata_logic.py` — a mechanical, not eyeballed, guard. |
| Contract suites (`backend/tests/contract/test_*_contract.py`) | `backend/tests/contract/` | `docs/architecture.md` §3.2: one suite per port, run against every registered implementation. Extend the four existing files. |

**No `application/` piece.** No `planner_core/application/` use case calls
any of these four ports yet (grep confirms: `live_weeks`, `prompt_version`,
`authentication`, `account_admin` — none touch them). The orchestration
features that will (rollover, generation, feature 26's handler) are blocked
on P4/P5/P6. This feature changes signatures and fakes only, exactly the
shape feature 14 established.

## 2. Files

### Modified

| Path | Change |
|---|---|
| `backend/core/src/planner_core/ports/weeks.py` | Add `current_version(week: IsoWeek) -> int`; change `save_slot`, `save_week` returns `None` → `int`. |
| `backend/core/src/planner_core/ports/recipes.py` | Add `current_version() -> int`; change `save`, `delete` returns `None` → `int`. |
| `backend/core/src/planner_core/ports/rules.py` | Add `current_version() -> int`; change `save` return `None` → `int`. |
| `backend/core/src/planner_core/ports/shopping_list.py` | Add `current_version() -> int`; change `save_item`, `delete_item`, `delete_checked_items` returns `None` → `int`. `acquire_lock`, `release_lock` unchanged. |
| `backend/core/tests/support/fakes.py` | Add a counter to `FakeWeekRepository` (per-`IsoWeek`), `FakeRecipeRepository`, `FakeRuleRepository`, `FakeShoppingListRepository` (single). Bump inside each mutating method; `delete_checked_items` bumps only when it removed ≥ 1 item. |
| `backend/core/tests/ports/test_weeks.py`, `test_recipes.py`, `test_rule_repository.py`, `test_shopping_list.py` | Add marker behaviour tests (R1–R5, R9). |
| `backend/tests/contract/test_week_repository_contract.py`, `test_recipe_repository_contract.py`, `test_rule_repository_contract.py`, `test_shopping_list_repository_contract.py` | Add parametrized marker tests (R2, R4, R5, R8, R9, R11). |

### Created

| Path | Contents |
|---|---|
| `backend/core/tests/test_change_marker_is_not_a_write_condition.py` | R7: AST scan of the four port modules — no mutating method declares an expected-version parameter, plus a planted-mutant self-test. R12: no `planner_core` module outside the four port files and no `lambda_api` / `lambda_ai` module references the marker. |
| `progress/impl_realtime_channel_persistence.md` | The implementer's `R<n> → test` traceability map (`docs/verification.md` Level 3). |

No `pyproject.toml` change. `planner-core` stays `dependencies = []`.

## 3. Signatures

The change marker is a plain **`int`** — `docs/data_model.md` §1.1 fixes
`marcaCambio` as *"a counter, incremented atomically (`ADD marcaCambio 1`),
never a timestamp"*. Baseline `0` for a never-written resource; the first
write returns `1`. Rejected wrappers: §9 A.

```python
# planner_core/ports/weeks.py
@runtime_checkable
class WeekRepository(Protocol):

    def current_version(self, week: IsoWeek) -> int:
        """This week's change marker (docs/data_model.md section 4.7, AP29).
        A real adapter reads it strongly-consistently, marker attribute only;
        0 for a week never written. No side effects (R2)."""
        ...

    def get_week(self, week: IsoWeek) -> Mapping[SlotRef, SlotContents]: ...

    def save_slot(self, week: IsoWeek, slot: SlotRef, contents: SlotContents) -> int:
        """Overwrite one slot; return this week's marker as advanced by this
        write, bumped in the same operation (docs/data_model.md section 1.1/5.5)."""
        ...

    def save_week(self, week: IsoWeek, plans: Mapping[SlotRef, SlotContents]) -> int: ...
```

```python
# planner_core/ports/recipes.py
class RecipeRepository(Protocol):
    def current_version(self) -> int: ...          # library is one single-value partition
    def get(self, recipe_id: str) -> LibraryRecipe | None: ...
    def list_all(self) -> tuple[LibraryRecipe, ...]: ...
    def save(self, entry: LibraryRecipe) -> int: ...
    def delete(self, recipe_id: str) -> int: ...    # still raises RecipeNotFound

# planner_core/ports/rules.py
class RuleRepository(Protocol):
    def current_version(self) -> int: ...
    def get(self) -> RuleSet: ...
    def save(self, rule_set: RuleSet) -> int: ...

# planner_core/ports/shopping_list.py
class ShoppingListRepository(Protocol):
    def current_version(self) -> int: ...
    def list_items(self) -> tuple[ShoppingItem, ...]: ...
    def save_item(self, item: ShoppingItem) -> int: ...
    def delete_item(self, item_id: str) -> int: ...        # still raises ShoppingItemNotFound
    def delete_checked_items(self) -> int:
        """Return the shopping list's marker. Bump it only if this call removed
        at least one item — nothing checked is a no-op that does not bump
        (R9, feature 8's idempotency guarantee)."""
        ...
    def acquire_lock(self, owner_id: str, now: datetime, expires_at: datetime) -> None: ...
    def release_lock(self, owner_id: str) -> None: ...
```

`current_version` takes `week: IsoWeek` on `WeekRepository` and nothing on
the other three — the same asymmetry `get_week(week)` vs `get()` already
has, because the library, the shopping list and the rules are each a
single-value partition (`docs/data_model.md` §7).

### Data-model mapping (acceptance 1)

| Port | `MarcaCambio` instance (`docs/data_model.md` §1) |
|---|---|
| `WeekRepository`, keyed by `IsoWeek` | `SEMANA#<idSemana>` / `MARCA` |
| `RecipeRepository` | `BIBLIOTECA#<idBiblioteca>` / `MARCA` |
| `ShoppingListRepository` | `COMPRA#<idLista>` / `MARCA` |
| `RuleRepository` | `GRUPOREGLAS#<idGrupoReglas>` / `MARCA` |

One item type, four instances — not a new item family per resource
(`docs/data_model.md` §1). The amended whole-partition reads
(`AP8`/`AP9`, `AP14`, `AP22` gaining `begins_with` scopes; `AP21` becoming
`TransactWriteItems`) are a **real adapter's** concern (P6), recorded in
`docs/data_model.md` §3/§4 and out of this feature.

## 4. Fakes

Each fake gains counter state and bumps it inside every mutating method:

- `FakeWeekRepository`: `versions: dict[IsoWeek, int]`. `current_version`
  returns `versions.get(week, 0)`. `save_slot` / `save_week` do
  `versions[week] = versions.get(week, 0) + 1` in the same method body as
  the data write.
- `FakeRecipeRepository`, `FakeRuleRepository`: a single `version: int = 0`.
- `FakeShoppingListRepository`: a single `version: int = 0`. `save_item` /
  `delete_item` bump unconditionally. `delete_checked_items` computes the
  survivors, and bumps **only if** it removed at least one item.
  `acquire_lock` / `release_lock` do not touch `version`.

No fake reads its own counter to decide whether a write succeeds (R7) —
there is nothing to decide; writes are unconditional last-write-wins
(`FR-RT-02`, `G-07`).

## 5. Conformance tests (per port, `tests/ports/`)

Added to each of the four existing modules:

- `current_version` is `0` before any write (R3).
- each mutating method returns an `int` strictly greater than the value
  before the call (R4, R5).
- the value a mutating method returns equals the next `current_version()`
  (R4).
- `get_week` / `list_items` / `get` / `list_all` / `current_version`
  itself leave `current_version()` unchanged across repeated calls (R2).
- `FakeShoppingListRepository` only: `delete_checked_items` with nothing
  checked returns the current marker and does not advance it (R9); with a
  checked item present it removes it and does advance (R5); `acquire_lock`
  / `release_lock` do not advance it.
- `FakeWeekRepository` only: two different `IsoWeek`s carry independent
  markers.

## 6. The scan test (acceptance 4 — R7, R12)

`backend/core/tests/test_change_marker_is_not_a_write_condition.py`, built
to the discipline of `test_ports_are_storage_agnostic.py`: exhaustive over
the modules it claims to cover, with its own patterns checked against
known-good and known-bad lines first.

- **R7** — `ast.parse` each of the four port modules; for every method of
  every `*Repository` class, assert no parameter name is in
  `{"version", "expected_version", "current_version", "if_version",
  "expected_marca", "marca_cambio", "expected"}` **except** the
  zero-or-one-argument `current_version` method itself (whose only allowed
  parameter is `week`). A self-test parses an inline mutant source with
  `def save(self, entry, expected_version: int) -> int` and asserts the
  scan flags it.
- **R12** — regex `\bmarca|\bchange_marker|\bcurrent_version\b` over every
  `*.py` under `planner_core/` and under `lambda_api/` / `lambda_ai/`
  `src/`; the only permitted hits are the four port modules. A companion
  self-test checks the pattern matches a planted `current_version(` line
  and does not match an unrelated line.

There is no `ConditionExpression` string to scan for — this feature adds
no adapter. The prohibition is enforced structurally (no expected-version
parameter can be passed) and behaviourally (R8's contract test: two saves,
second wins, no raise).

## 7. Boundary checks

- **`docs/architecture.md` §2 (pending, human-owned):** P3 is **decided**
  (§1.2.4, `G-88`) and `G-88` states this half needs no other pending
  decision. P5 (how the marker travels over HTTP) and P6 (the real
  adapter, `AP29`'s `ConsistentRead`, the amended partition reads) are not
  touched — they are feature 26 and a future adapter.
- **§2.1 decide-in-a-spec items:** none. No unit, category, servings or
  difficulty value enters this feature.
- **Frozen docs:** none modified. Every `R<n>` cites `FR-RT-01` (frozen).
  R7 and R8 additionally record a preservation-of-`FR-RT-02` constraint in
  their R-blocks; `FR-RT-02` is not in `covers` (gate ruling 2026-08-30,
  §10).
- **Domain value types:** `SlotContents`, `RuleSet`, `ShoppingItem`,
  `LibraryRecipe`, `IsoWeek`, `SlotRef` unchanged — no field added.
- **`docs/conventions.md` "no ambient time":** `current_version` takes no
  clock and no instant; the marker is a counter, not a timestamp
  (`docs/data_model.md` §1.1). `acquire_lock`'s caller-supplied `now`
  is unchanged.
- **User-facing strings:** none. The marker is not user-visible; no es-ES
  text.
- **Runtime dependencies:** none added. `core` stays `dependencies = []`.
- **`test_ports_are_storage_agnostic.py` (feature 14, R7/R10):** still
  green — the amendments add only `int` returns, no import.

## 8. Verification obligations landed (`docs/verification.md`)

- Level 2: every amended port method and every fake gets a happy-path test;
  `delete_item` / `delete` keep their failure-path (`*NotFound`) tests.
- Level 3: `progress/impl_realtime_channel_persistence.md` carries the
  `R1..R12 → test` map, both directions.
- Level 4, idempotency (`docs/architecture.md` §4 invariant 5): R9's test
  runs `delete_checked_items` twice with nothing checked and asserts the
  marker never moves — `delete_checked_items` stays byte-for-byte
  idempotent, marker included.
- Level 4, "never undo the user's reality": R9 also asserts a checked item
  is untouched by `delete_checked_items` when other items are checked, and
  the marker bump does not rewrite it.
- Level 5 (mutation testing, `reviewer`-owned): the obvious mutants —
  drop the bump in one mutating method, bump on a `delete_checked_items`
  no-op, make `current_version` bump, return a stale value from a write,
  widen the R7 parameter allowlist — must each be killed by a named test.
  Tasks below name the test per mutant.

## 9. Rejected alternatives

**A. Wrap the marker in a `NewType("ChangeMarker", int)` or a frozen
`ChangeMarker` value object instead of returning a bare `int`.** Rejected.
`docs/data_model.md` §1.1 fixes it as a bare atomically-incremented
counter with no invariant to protect, and — decisively — acceptance 4 /
R7 mean **no port method ever accepts a marker as an argument**, so there
is no wrong-type-argument failure mode for a `NewType` to catch. The
wrapper would be pure ceremony that `test_ports_are_storage_agnostic.py`
would then have to allow-list.

**B. A separate `ChangeMarkerRepository` port with
`current_version(resource_key)`, used alongside the four repositories.**
Rejected. It re-creates the "one concept, two ports" split
`docs/data_model.md` §7 explicitly reverted for `LockLista`, and it lets a
caller read a marker through a different object than the one that writes
it — the exact seam `G-88`'s same-transaction rule closes. `AP29` being
"one call shape, four resources" is an HTTP-handler convenience
(feature 26), not a reason to merge the ports.

**C. Keep the mutating methods returning `None`; expose the post-write
marker only through a follow-up `current_version()` call.** Rejected —
and this was the naive shape. Acceptance 3 requires the write to return
its own new marker, because the follow-up-read shape reintroduces the
read-after-write race `docs/data_model.md` §4.7/§5.5 calls out: feature
26's handler must be able to hand the client a marker that provably
includes the write it just made, without a second round trip that a
concurrent writer can slip inside.

## 10. Gate — resolved 2026-08-30

1. **`covers`.** Add `FR-RT-01` only, not `FR-RT-02` — keeping feature 18
   requirement-free "would not be honest." `feature_list.json` feature 18
   `covers` is now `["FR-RT-01"]`.
2. **Baseline `0`** for a never-written resource — confirmed. The first
   write returns `1`.
3. **Return type is a plain `int`** (§9 A), no `ChangeMarker` wrapper —
   confirmed.
4. **`delete_checked_items` returns `int` always** — the marker whether or
   not it advanced, never `int | None` — confirmed.
5. **Strong consistency of the real `current_version` read** (`AP29`
   `ConsistentRead=True`, `docs/data_model.md` §4.7) is deferred to a real
   adapter in the `@pytest.mark.aws` tier (P6 / feature 26+); verified now
   only as read-your-writes against the fake (R4 + contract suite) —
   confirmed acceptable.
6. **`acquire_lock` / `release_lock` stay `-> None` and do not bump** —
   confirmed. The single-bump-on-lock-release alternative is the
   out-of-scope collapse `G-88` / `docs/data_model.md` §4.4 defer.

**Consequence of ruling 1.** R7 and R8 previously cited `FR-RT-02`. They
are last-write-wins *preservation* constraints — they keep the door shut on
optimistic locking — not implementations of the shared-collaboration model,
and per `G-88` the marker is read-only metadata / never a write
precondition, which is intrinsic to `FR-RT-01`'s polling design. Both
re-cited to `FR-RT-01`, each R-block now carries a
preservation-of-`FR-RT-02` note (`requirements.md` R7, R8, coverage map,
and the § *Why every `R<n>` cites …* note).
