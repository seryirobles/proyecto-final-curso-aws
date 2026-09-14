# frontend_spa — Design

> Feature 20 · tier 4. Read `requirements.md` first. Sources:
> `docs/architecture.md` §1.1/§3/§3.1, `docs/conventions.md` "Frontend
> conventions", `docs/rest_api_contract.md` (endpoints/payloads/errors/auth/
> ETag), `docs/frontend_prototype.md` (mining + §4 contradictions),
> `specs/realtime_channel_transport/` (the `usePolling` hook this feature
> consumes), `docs/data_model.md` §9 (parked archive browse).

## 0. Governing decisions already made elsewhere — not re-opened

- Stack: idiomatic React (function components, hooks, JSX), Vite, Vitest,
  plain JS/ESM, no TypeScript (`architecture.md` §1.1, formerly P7). Not
  re-litigated.
- Styling: inline `style` objects off `frontend/src/tokens/` — no
  stylesheet, no CSS framework, no CSS-in-JS. Fluid-first layout;
  `matchMedia` for genuine breakpoints (`conventions.md`).
- Auth transport: `HttpOnly` cookie, `SameSite=Lax`, same-origin
  (`rest_api_contract.md` §5). No token ever touches JS; every `fetch` call
  needs `credentials: "include"` and nothing else.
- Marker transport: `ETag`/`If-None-Match`, `usePolling(url, config)` already
  built (feature 26, done) — returns `{ data, marker, connectionLost,
  applyMutationMarker }`, backed by `frontend/src/realtime/pollingEngine.js`.
  This feature is `usePolling`'s **first consumer** (feature 26 design §8:
  "every view, every call site of `usePolling`… is feature 20").
- Messages/tokens/locale modules already exist
  (`frontend/src/messages/`, `frontend/src/tokens/`, `frontend/src/locale.js`)
  and are **extended**, not replaced.
- Wire shape: English `camelCase` JSON, RFC 9457 `application/problem+json`
  errors with a `code` extension member (`rest_api_contract.md` §3–§4). The
  unit vocabulary is `Unit` (`"g" | "ml" | "unit"`,
  `backend/core/src/planner_core/domain/units.py`) and the ingredient
  category vocabulary is `IngredientCategory` (`"meat" | "fish" |
  "carbohydrate" | "legume" | "vegetable" | "eggs"`,
  `.../domain/ingredient_category.py`) — both **already decided** by features
  3 and 6 (`done`). This feature does not re-decide either list; §6 below
  proposes only their es-ES **display labels**, which is genuinely new
  (nothing upstream renders these codes as UI text).
- No `docs/architecture.md` §2 item is open.

## 1. Scope boundary

### 1.1 What this feature builds (its own `R<n>`)

The 16 `FR-*` ids in `requirements.md`'s `covers`-array coverage table
(`R1`–`R22`), plus the three auth screens' `R23`–`R37` (fold, 2026-09-13,
§5a) — each of the latter cites an `FR-AUTH-*` id owned by feature 15/16,
same `FR-CAND-04`-style citation as `ai_lambda`'s `R21`, never added to
`covers` (see the coverage-check footnote in `requirements.md`).

### 1.2 What this feature renders but does not own (consumed, not owned)

The description and acceptance criteria ask for a full, usable SPA —
candidates, definitive selection, library, rules, shopping list, summary.
Most of that behaviour is **already specified and tested** by earlier,
`done` features at the domain/API layer; this feature's job is to call the
already-built endpoint and display the already-proven result, not to
re-derive a requirement for it. Per the `ai_lambda` precedent
(`FR-CAND-04` "consumed-not-owned"), each is named here, not re-claimed:

| Screen area | `FR-*` consumed | Owned by (feature) |
|---|---|---|
| Promote/clear definitive meal | `FR-CAND-05`, `FR-CAND-08` | 5 `week_plan_model` |
| Weekly summary content | `FR-SUM-01`, `FR-SUM-03` | 5 `week_plan_model` |
| Rules list/add/edit/remove, satisfiability errors | `FR-RULE-01`–`-07` | 6 `rules_model`, 27 (satisfiability) |
| Shopping list content, checkbox, re-sync | `FR-SHOP-01`–`-10` | 7/8 `shopping_aggregation`/`shopping_list_state`, 27 (re-sync) |
| Connection-loss indicator | `FR-RT-03` | 26 `realtime_channel_transport` (explicitly named as feature 20's job in its design §8) |
| Author display on candidates/library recipes | `FR-CAND-04` | 5 `week_plan_model` |
| Recipe snapshot semantics | `FR-CAND-07` | 4 `recipe_model` |
| Fixed unit/category dropdown **values** | `FR-LIB-05`, `FR-RULE-04` | 3 `text_and_units`, 6 `rules_model` (this feature adds only the es-ES labels, §6) |

Tasks that build these areas carry **no `R<n>`** in `tasks.md` — they cite
the consumed `FR-*` and its owning feature instead, mirroring
`specs/realtime_channel_transport/tasks.md` T24a's "No `R<n>` (infrastructure
for T24b)" pattern.

### 1.3 What this feature does not build at all

> **Fold, 2026-09-13:** Login, set-password, and the admin screen were
> **out of scope in the first pass** (bullet removed here) and are now
> **in scope** per the owner's ruling on the spec-gate questions — see the
> note atop `requirements.md` and §5a below. Still absent, unchanged:

- **Archive browsing (`FR-ARCH-04`).** No endpoint exists —
  `rest_api_contract.md` §1 lists it under "Not exposed, by decision":
  `idSemana` is a partition key, and `data_model.md` §9 parks it; feature 19
  `archive_and_cold_storage` is `blocked`. This feature builds no Archive
  view. `R5`'s "recipe detail reachable everywhere" is still true
  structurally — `GET /v1/weeks/{weekId}` serves any week id, including a
  past one, through the *same* week/detail components — but nothing here
  lets a user discover a past week id to request. When a future feature adds
  a browse endpoint, no component here needs to change.
- **Single-recipe AI generation submit-then-poll** (`POST /v1/generations`
  single-recipe body, preview accept/discard/regenerate). Its wire contract
  is explicitly not yet decided — `rest_api_contract.md` marks it an
  "OWNER-OWNED PRECURSOR" for feature 28, still `pending`
  (`progress/current.md`, 2026-09-06 entry). R6's "AI" authoring method is
  therefore a **stub**: selectable, shows the spec-input shape (ingredients +
  tools, or a reference recipe + notes), and its submit control is disabled
  with an es-ES "not available yet" message — building a working submission
  against an undecided body would either invent the contract or need
  rewriting the moment feature 28 lands it.
- **Whole-week AI generation** (`FR-AI-03`/`-05`/`-11`, confirmation prompt,
  per-slot progress). Not in this feature's `covers`, not in its
  description, and no feature currently owns its frontend half either — left
  for a future feature, same reasoning as archive.
- **The AI lambda worker, single-recipe generation's backend piece, any
  `backend/` code.** Features 17 and 28.

## 2. Layering (`docs/architecture.md` §3, §3.1)

Everything lives under `frontend/src/`, the SPA's own toolchain root — no
`backend/` file is touched. Per `conventions.md` "Frontend conventions": a
custom hook owns state/handlers/API calls/derived values; a component is a
pure function of props; no business logic (week boundaries, aggregation,
rule satisfiability, scoping) is ever recomputed client-side — every number
shown is a value the API already returned.

| Piece | Layer | Notes |
|---|---|---|
| `src/api/client.js` | frontend, pure module | `apiFetch`, `ApiError` — the one place that calls `fetch` with `credentials: "include"` and maps a non-2xx `problem+json` body to a thrown `ApiError`. No decision logic. |
| `src/domain/labels.js` | frontend, pure module | es-ES display labels for the `Unit`/`IngredientCategory` wire codes (§6) and the fixed day/slot codes. |
| `src/hooks/useBreakpoint.js` | frontend, thin hook | Wraps `window.matchMedia` (R17). |
| `src/hooks/useConfirm.js` | frontend, thin hook | Confirmation-gate state machine for R18 (no `window.confirm` — see §7). |
| `src/hooks/use<View>.js` (×7) | frontend, one hook per view | State, handlers, API calls per `conventions.md`'s naming rule. |
| `src/hooks/useRecipeAuthoring.js` | frontend, shared hook | The three/two-way authoring flow, reused by candidate and library authoring (R6–R8). |
| `src/hooks/useLibraryPicker.js` | frontend, shared hook | Search/filter state reused in three flows (R12). |
| `src/hooks/useSession.js` | frontend, shared hook | Session-status state machine (§5a): the bootstrap probe, `login`, `setPassword`, `logout`. Not a view hook — shared by three screens the way `useConfirm` is shared by five. |
| `src/hooks/useLoginForm.js`, `useSetPasswordForm.js`, `useAdminAccounts.js` | frontend, one hook per view | Same naming rule as the other view hooks (§5a). |
| `src/components/*.jsx` | frontend, presentational | Pure functions of props; own `style` objects off `tokens`. |
| `src/App.jsx` / `src/hooks/useApp.js` | frontend, shell | Composes `useSession`; session-status gate (login/set-password/admin/user shell) plus, once authenticated as User, active-view state, top nav, the one `ConnectionLostBanner` mount point. |
| `src/main.jsx` | frontend, entry point | Replaces `PlaceholderView` with `App` (feature 1's placeholder retired here). |

## 3. Files created / modified

**New, `frontend/src/api/`**
- `client.js` — `apiFetch(path, { method, body, headers, signal })`, always
  `credentials: "include"`, `Content-Type: application/json` when `body` is
  set; throws `ApiError extends Error` (`status`, `code`, `detail`,
  `details`) built from a `problem+json` body, or a generic `ApiError` with
  `code: "NETWORK_ERROR"` on a thrown `fetch` rejection.

**New, `frontend/src/domain/`**
- `labels.js` — `UNIT_LABELS`, `CATEGORY_LABELS`, `DAY_LABELS` (1–7 →
  `Intl`-derived weekday names, `locale.js`), `SLOT_LABELS` (`1` → "Comida",
  `2` → "Cena", the one pair of literal labels the fixed wire codes need,
  since `Intl` has no concept of "lunch/dinner"), `ROLE_LABELS` (`Admin` →
  "Administrador", `User` → "Usuario" — §5a, `AdminAccountsView`'s row
  label).

**New, `frontend/src/hooks/`** — `useBreakpoint.js`, `useConfirm.js`,
`useApp.js`, `useWeekPlanner.js`, `useRecipeDetail.js`,
`useRecipeAuthoring.js`, `useLibraryPicker.js`, `useLibrary.js`,
`useRules.js`, `useShoppingList.js`, `useSummary.js`, `useSession.js`,
`useLoginForm.js`, `useSetPasswordForm.js`, `useAdminAccounts.js`.

**New, `frontend/src/components/`** — `App.jsx`, `ConnectionLostBanner.jsx`,
`WeekSwitcher.jsx`, `WeekLabel.jsx`, `WeekPlannerView.jsx`, `DaySlot.jsx`,
`MealCard.jsx`, `RecipeDetailView.jsx`, `RecipeAuthoringForm.jsx`,
`LibraryRecipePicker.jsx`, `LibraryView.jsx`, `RulesView.jsx`,
`ShoppingListView.jsx`, `SummaryView.jsx`, `ConfirmDialog.jsx`,
`EmptyState.jsx`, `LoadingState.jsx`, `LoginView.jsx`,
`SetPasswordView.jsx`, `AdminAccountsView.jsx`, `AccountRow.jsx`.

**Modified**
- `frontend/src/main.jsx` — mounts `App` instead of `PlaceholderView`.
- `frontend/src/messages/es-ES.js` — every new UI string this feature needs
  (view titles, empty-state guidance, confirmation prompts, form labels,
  the AI-stub notice, the login/set-password/admin-screen strings — §5a),
  added as new `UPPER_SNAKE` keys. `PlaceholderView.jsx`
  and its two existing keys are untouched (feature 1 scaffold record).
- `frontend/src/tokens/*.js` — extended only if a screen genuinely needs a
  token the 18-colour lift / existing spacing-type scale does not cover
  (expected: none: the existing palette already has `terra`/`aub`/`honey`
  semantic accents for confirm/AI/warning treatments).

**New, `frontend/tests/`** — one test file per hook (`tests/hooks/`) and
targeted component tests (`tests/components/`) per §9, plus
`tests/test_no_extra_accessibility.js` (R22's mechanical scan).

Nothing under `backend/` is touched.

## 4. Shared infrastructure

### 4.1 `api/client.js` — the one fetch boundary

```js
export class ApiError extends Error {
  constructor({ status, code, detail, details }) { super(detail); this.status = status; this.code = code; this.details = details; }
}

export async function apiFetch(path, { method = "GET", body, signal } = {}) {
  const response = await fetch(path, {
    method, credentials: "include", signal,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (response.status === 204) return null;
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError({ status: response.status, code: payload?.code ?? "UNKNOWN_ERROR",
      detail: payload?.detail ?? MESSAGES.GENERIC_ERROR, details: payload?.details });
  }
  return payload;
}
```

Every view hook's mutation handler catches `ApiError` and surfaces
`error.detail` (already es-ES, `rest_api_contract.md` §4 — "copied verbatim
from `planner_core.messages`") — never composes its own message, which is
what R15 requires for error text specifically.

### 4.2 Optimistic self-updates (`usePolling`'s `applyMutationMarker`)

Every mutation call site follows the same shape, per feature 26 design §8's
explicit hand-off ("wiring `applyMutationMarker` to each mutation's own
fetch call" is feature 20's job):

```js
async function handleAddCandidate(input) {
  const result = await apiFetch(candidatesUrl, { method: "POST", body: input });
  weekPoll.applyMutationMarker(parseMarker(/* response ETag, via realtime/etag.js */));
  return result;
}
```

`parseMarker` and the response's `ETag` header round-trip through
`realtime/etag.js` (feature 26, already built) — this feature does not add a
second marker parser.

### 4.3 `useBreakpoint.js` (R17)

```js
export function useBreakpoint(query) {
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches);
  useEffect(() => {
    const mql = window.matchMedia(query);
    const onChange = () => setMatches(mql.matches);
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, [query]);
  return matches;
}
```

`tokens/breakpoints.js` (already exists) supplies the query strings by name
— no literal media-query string in a component.

### 4.4 `useConfirm.js` (R18)

```js
export function useConfirm() {
  const [pending, setPending] = useState(null); // { message, onConfirm } | null
  return {
    pending,
    requestConfirm: (message, onConfirm) => setPending({ message, onConfirm }),
    confirm: () => { pending?.onConfirm(); setPending(null); },
    cancel: () => setPending(null),
  };
}
```

`ConfirmDialog.jsx` is a pure component rendering `pending?.message` with
confirm/cancel buttons, styled off `tokens` — no `window.confirm` (rejected,
§7). Every destructive handler (`handleRemoveRecipe`, `handleRemoveCandidate`,
`handleRemoveShoppingItem`, `handleRemoveRule`, `handleClearDefinitive`)
calls `requestConfirm(message, actualHandler)` instead of calling the API
directly.

### 4.5 `domain/labels.js` (§6 values)

Maps the already-decided wire codes to es-ES display text; never the
reverse (the wire never receives a label, only the code — `rest_api_contract.md`
§3.0 rule 1: English `camelCase`/codes on the wire, es-ES reserved for
strings).

## 5. Screens

Seven meal-planning views, no router library (§7). Once `useSession` (§5a)
reports `{ status: "authenticated", role: "User" }`, `useApp.js` owns one
`activeView` state value (`"week" | "library" | "rules" | "shoppingList" |
"summary"`) and a `navigateTo(view)` handler; `App.jsx` renders a nav strip
(`WeekSwitcher` lives inside the week view, not the nav — R2/R3) plus the
active view's component, plus one `ConnectionLostBanner` fed by whichever
poll(s) the active view holds. Before that — anonymous, password-reset
pending, or role Admin — `App.jsx` renders none of this; see §5a.

| View | Hook | Polls | Renders (R<n> / consumed FR) |
|---|---|---|---|
| `WeekPlannerView` | `useWeekPlanner` | `GET /v1/live-weeks` (once), `usePolling(GET /v1/weeks/{weekId})` | R1, R2, R3, R6, R18 (clear/replace definitive), R19/R20; consumes `FR-CAND-05/-08`, `FR-CAND-04`, `FR-CAND-07` |
| `RecipeDetailView` | `useRecipeDetail` | none (opened with an already-fetched or `GET .../candidates/{id}` recipe) | R4, R5 |
| `RecipeAuthoringForm` | `useRecipeAuthoring` | none (submits `POST`/`PUT` per §3.1 of the contract) | R6, R7, R8, R20 |
| `LibraryView` (+ `LibraryRecipePicker`) | `useLibrary` / `useLibraryPicker` | `usePolling(GET /v1/library/recipes)`, unfiltered — `name`/`category` filter the polled list client-side (§7 Q7, fix round 1) | R9, R10, R11, R12, R13, R14, R18, R19 |
| `RulesView` | `useRules` | `usePolling(GET /v1/rules)` | R18, R19; consumes `FR-RULE-01…07`; reuses `LibraryRecipePicker` for the pin-recipe search (R12) |
| `ShoppingListView` | `useShoppingList` | `usePolling(GET /v1/shopping-list)` | R18, R19, R20; consumes `FR-SHOP-01…10` |
| `SummaryView` | `useSummary` | `usePolling(GET /v1/weeks/{weekId}/summary)` | R5, R21; consumes `FR-SUM-01`, `-03` |

`R21` (week labelling) is a single `WeekLabel.jsx` component
(`{ designation, monday, sunday }` → "Semana actual · 11–17 ago." via
`locale.js`'s `formatDate`), used by `WeekPlannerView`, `SummaryView`, and
any week-scoped action button (e.g. the shopping re-sync trigger, which is
week-scoped per `FR-SHOP-05`'s "current week from today plus next week"
even though the button itself lives in `ShoppingListView`).

### 5.1 `useRecipeAuthoring.js` — the shared flow (R6–R8)

```js
export function useRecipeAuthoring({
  mode /* "candidate" | "library" */,
  onSubmit,
  initialRecipe = null, // edit seed (F4 fix round 1); null for a fresh "add"
}) {
  const methods = mode === "candidate"
    ? ["library", "scratch", "ai"]
    : ["scratch", "ai"];              // R8 — no "library" method here
  const [method, setMethod] = useState(methods[0]);
  const [form, setForm] = useState(() =>
    initialRecipe ? recipeToForm(initialRecipe) : emptyForm(),
  );
  // Re-seeds `form` when initialRecipe's identity changes (edit -> edit of
  // a different recipe, or edit -> add) - a render-time comparison against
  // a `seededFrom` state slot, not an effect, mirrors useRecipeDetail's
  // request-keyed isLoading (avoids set-state-in-effect).
  // library method -> useLibraryPicker (own instance per tab, `enabled`
  // gated to the active one, F2 fix round 1); scratch -> manual field
  // state; ai -> reference-recipe picker + notes, submit always disabled
  // (design.md section 1.3)
  ...
}
```

The "from scratch" fields mirror `rest_api_contract.md` §3.1's `manual`
body: `name`, `category` (dropdown, `domain/labels.js` `CATEGORY_LABELS`),
`servings`/`estimatedTime` (freeform text inputs, no validation —
`FR-LIB-03`, `G-85`), `ingredients[]` (name, quantity, unit dropdown off
`UNIT_LABELS`), `tools[]`, `procedure[]`.

## 5a. Auth screens — Login, set-password, admin (fold, 2026-09-13, `R23`–`R37`)

Three screens, all rendered by `App.jsx` **before** (or instead of) the
seven-view shell of §5. Wire shapes below are read verbatim off the `done`
implementation — `backend/lambda_api/src/planner_api/routing.py`
(`_login`, `_set_password`, `_create_user`, `_update_user`, `_delete_user`)
and `serialization.py`'s `encode_account` — not re-derived, since
`rest_api_contract.md` itself states resource paths and semantics but not
every field name.

### `useSession.js` — the session-status state machine

```js
export function useSession() {
  const [session, setSession] = useState({ status: "loading" });
  // status: "loading" | "anonymous" | "passwordResetPending" | "authenticated"
  // "authenticated" carries { role: "Admin" | "User" }

  const probe = useCallback(() => apiFetch("/v1/live-weeks").then(
    () => setSession({ status: "authenticated", role: "User" }),
    (err) => setSession(
      err.code === "PASSWORD_RESET_PENDING" ? { status: "passwordResetPending" } :
      err.code === "FORBIDDEN" ? { status: "authenticated", role: "Admin" } :
      { status: "anonymous" }               // SESSION_EXPIRED, or no cookie
    )), []);
  useEffect(() => { probe(); }, [probe]);    // R23 — the mount-time check

  async function login(username, password) {
    const result = await apiFetch("/v1/session", { method: "POST", body: { username, password } }); // R25
    setSession(result.passwordResetRequired
      ? { status: "passwordResetPending" }
      : { status: "authenticated", role: result.role });
  }
  async function setPassword(newPassword) {
    await apiFetch("/v1/session/password", { method: "PUT", body: { newPassword } }); // R27
    await probe();                            // role wasn't known at login time (a page reload
  }                                            // into a pending session); re-run the same check.
  async function logout() {
    await apiFetch("/v1/session", { method: "DELETE" });
    setSession({ status: "anonymous" });
  }
  return { session, login, setPassword, logout };
}
```

**R23's mechanism, spelled out.** There is no `GET /v1/session` /
"whoami" route — `rest_api_contract.md` §1's resource table lists only
`POST`/`DELETE /v1/session`. An `HttpOnly` cookie is invisible to JS by
design (§4 of this file), so the SPA cannot read it directly either. It
reuses `GET /v1/live-weeks` (a `Role.USER`-only route, R7/R8/R11/R13 of
`specs/rest_api_lambda/requirements.md`) as a probe: `200` only a User can
get. The backend (`handler.py`) checks role *before* password-reset status,
so `403 PASSWORD_RESET_PENDING` only fires for a User with a pending reset;
an Admin with a pending reset gets plain `403 FORBIDDEN` from the role
check instead, and the probe misclassifies them as `authenticated(Admin)`
rather than `passwordResetPending` — a known, accepted limitation (see
`progress/impl_frontend_spa.md` "Auth screens, first half"), bounded because
the backend still rejects every admin action for that account regardless.
No new route is proposed; adding one would be an uninvited change to a
`done`, frozen contract (`rest_api_contract.md` line 3: "Status: DECIDED").

### `LoginView` (`useLoginForm.js`) — R24, R25, R29

Username + password draft fields, a submit button (mined from the
prototype's `Login` screen, `Sobremesa.dc.html` lines 66–87 — labels
"Usuario"/"Contraseña", button "Entrar"). Submit calls `session.login`;
a caught `ApiError` with `code: "INVALID_CREDENTIALS"` renders its
`detail` inline (same generic pattern as every other view's error
handling, §4.1 — no new mechanism). **Not mined:** the prototype's
`loginFails`/`lockedUntil` lockout countdown (`loginBtnLabel`'s "Espera
30s") — `NFR-SEC-04` brute-force protection is explicitly infrastructure
(`feature_list.json` feature 21, `G-87`), not this feature's job; the
login button is never disabled by a client-side attempt counter.

### `SetPasswordView` (`useSetPasswordForm.js`) — R26, R27, R28

Rendered whenever `session.status === "passwordResetPending"`. New-password
field plus a confirm field checked client-side for an exact match before
submit fires (mined from the prototype's "Confirmar contraseña" field,
lines 100–103) — the password *policy* itself (length, common/leaked
rejection) is `FR-AUTH-15`, feature 9, enforced server-side and surfaced
generically as a caught `PASSWORD_TOO_SHORT` `ApiError`; this screen does
not re-implement it. Submit calls `session.setPassword`. A "Cancelar"
control (prototype line 110) calls `session.logout` — abandoning the
attempt, never a bypass, since it does not grant access (R28 stays true:
no route back into the app without either finishing this screen or
logging in again). No dedicated `R<n>` for "Cancelar" — it is a UX nicety,
not an `FR-AUTH-*` obligation.

### `AdminAccountsView` (+ `AccountRow.jsx`, `useAdminAccounts.js`) — R33–R37

`GET /v1/users` on mount — **not** `usePolling`: accounts is not one of
`FR-RT-01`'s four pollable resources (`rest_api_contract.md` §2's "Poll"
column is blank for `/v1/users`), so this is the one view in this feature
that does not consume feature 26's hook. Every mutation refetches the list
instead of relying on a marker.

| Action | Call | Gate |
|---|---|---|
| Create | `POST /v1/users` `{ username, temporaryPassword }` | R35 — no `role` field exists to fill in; `_create_user` never accepts one, so an admin-role account cannot be created here even by mistake |
| Rename | `PATCH /v1/users/{userId}` `{ username }` | none — `account_admin.rename_user` places no role/self restriction (verified against `backend/core/src/planner_core/application/account_admin.py`) |
| Reset password | `PATCH /v1/users/{userId}` `{ temporaryPassword }` | `useConfirm` (extends R18); hidden on the acting admin's own row (R37) — `admin_set_password` raises `Forbidden` for a self-target, so the control is hidden rather than left to fail |
| Remove | `DELETE /v1/users/{userId}` | `useConfirm` (extends R18); hidden on an admin-role row (R36) — `remove_user` raises `Forbidden` for an Admin-role target |

Row rendering (`R33`): username, `roleLabel` (`domain/labels.js`'s
`ROLE_LABELS`, new: `{ Admin: "Administrador", User: "Usuario" }`), and a
"contraseña pendiente" badge when `passwordResetRequired` is true (mined
from the prototype's line 386 badge). `R34`'s four controls sit on
`AccountRow.jsx`; the create form sits above the list on
`AdminAccountsView.jsx` itself (mined layout, prototype lines 375–381,
label "Nuevo usuario" → username, "Contraseña inicial" → the
`temporaryPassword` field).

**Not mined:** the prototype's `canEdit:!isMe && role!=='admin'` gate on
its "Editar" button. `rename_user` carries no such restriction (checked
against the actual code, not assumed from the prototype, which `docs/
frontend_prototype.md` §4 already flags as encoding an earlier, sometimes
wrong, state of the rules) — renaming is offered on every row, including
the acting admin's own and other admins'.

### App-shell logout (R32)

One logout control (`title="Salir"` icon button, prototype line 126),
present in both the User nav strip and the thin Admin header, wired to
`session.logout`. No separate component — it lives directly in `App.jsx`'s
existing header markup for whichever shell is active.

## 6. Values fixed at the spec gate

Not architecture (§2.1 already closed the unit/category *lists* via features
3 and 6) — these are the es-ES **labels** for those already-fixed codes,
proposed here because nothing upstream needed to render them as text before:

| Code | es-ES label |
|---|---|
| `Unit.GRAM` (`"g"`) | "g" |
| `Unit.MILLILITRE` (`"ml"`) | "ml" |
| `Unit.UNIT` (`"unit"`) | "ud" |
| `IngredientCategory.MEAT` | "Carne" |
| `IngredientCategory.FISH` | "Pescado" |
| `IngredientCategory.CARBOHYDRATE` | "Carbohidratos" |
| `IngredientCategory.LEGUME` | "Legumbres" |
| `IngredientCategory.VEGETABLE` | "Vegetal" |
| `IngredientCategory.EGGS` | "Huevos" |
| slot `1` / `2` | "Comida" / "Cena" |
| `Role.ADMIN` | "Administrador" |
| `Role.USER` | "Usuario" |

The category labels follow the prototype's Spanish category vocabulary
(`docs/frontend_prototype.md` §2.2) except `vegetable`/`eggs`, which the
prototype never had (`G-82` renamed `vegetarian`→`vegetable`; `eggs` is new)
— translated directly, not mined.

## 7. Rejected alternatives

**A routing library (React Router or similar) for the seven-view nav.**
Rejected: no `FR-*` requires a URL per view or deep-linking, and
`docs/architecture.md` §6 requires a new dependency to be justified in an
approved `design.md` — a router buys nothing here that one `activeView`
state value in `useApp.js` does not already give, and it would introduce a
second state-ownership model alongside the hook/component split
`conventions.md` already mandates.

**A working single-recipe AI generation submission on the "AI" authoring
tab**, instead of the stub described in §1.3. Rejected: `POST
/v1/generations`'s single-recipe request body is explicitly undecided —
`rest_api_contract.md` marks it feature 28's "OWNER-OWNED PRECURSOR" — so
building against a guessed shape would either invent part of a frozen
contract or be rewritten the moment feature 28's spec lands.

**`window.confirm`/`window.alert` for R18's destructive-action gate**,
instead of `useConfirm.js` + `ConfirmDialog.jsx`. Rejected:
`conventions.md`'s testing rule asks for behaviour asserted "through state,"
and a native blocking dialog is a global side effect a hook cannot expose as
state — every test would need to stub `window.confirm`, and the dialog could
not be styled off `tokens` (`docs/frontend_prototype.md`'s "askConfirm" gate
is confirmed as a real, valuable idiom, just not through the browser API).

## 8. What is NOT here

- Archive browsing (§1.3) — no endpoint (`FR-ARCH-04` parked).
- Single-recipe AI generation submit-then-poll and the AI worker's
  single-recipe branch — feature 28.
- Whole-week AI generation UI (confirmation prompt, per-slot progress) —
  owned by no feature yet.
- Any `backend/` change.
- The `usePolling` hook itself, the polling engine, `etag.js`,
  `conditionalGet.js` — feature 26, done; this feature only calls them.
- The domain behaviour behind every "consumed, not owned" row in §1.2, and
  behind every `FR-AUTH-*` id §5a cites — those features' own `R<n>`
  already prove it (password policy, revocation marker, session expiry,
  "unknown user" reattribution); this feature proves only that the SPA
  calls the right endpoint and renders the response.
- A `GET /v1/session` "whoami" route — none exists; §5a's `useSession`
  probe works around its absence without proposing one (frozen contract).

## 9. Test strategy (feeds `tasks.md`)

Per `conventions.md` "Testing": assert behaviour through hook state; render
only when the assertion is genuinely about markup shape. No snapshot tests
of whole views.

- **`api/client.js`**: a stubbed `global.fetch` — `200`/`204` pass through;
  a `problem+json` body on a non-2xx throws `ApiError` with `status`/`code`/
  `detail`/`details`; a rejected `fetch` throws `ApiError` with
  `code: "NETWORK_ERROR"`.
- **`useBreakpoint.js`**: a fake `matchMedia` (object with `matches`,
  `addEventListener`/`removeEventListener`) — initial value, and a dispatched
  `change` event flips the returned boolean (R17).
- **`useConfirm.js`**: `requestConfirm` sets `pending`; `confirm()` calls the
  stored handler once and clears `pending`; `cancel()` clears without
  calling it (R18).
- **`useWeekPlanner.js`**: given a fake `apiFetch`/`usePolling`, switching
  weeks (R2) requests the other `weekId`; the returned view-model shape is
  identical in field names for both weeks (R3); clicking a meal calls
  `onOpenDetail` with its full recipe (R4/R5 wiring); an empty day/slot
  yields the empty-state flag (R19, consumed `FR-CAND-05/-08` unaffected).
- **`useRecipeAuthoring.js`**: `mode: "candidate"` exposes exactly
  `["library", "scratch", "ai"]` (R6); `mode: "library"` exposes exactly
  `["scratch", "ai"]`, never `"library"` (R7, R8).
- **`useLibrary.js` / `useLibraryPicker.js`**: a `name`/`category` filter
  updates the polled URL's query string (R11, R13); asserting the filter
  state object has exactly two keys (R14); the same `useLibraryPicker` hook
  instance shape is asserted reused from `RecipeAuthoringForm`'s
  library-pick method and from `RulesView`'s pin picker (R12).
- **`useRules.js` / `useShoppingList.js` / `useSummary.js`**: each view's
  destructive action calls `requestConfirm` before the API call fires (R18);
  an empty payload sets the empty-state flag (R19); a slow (`awaiting`)
  fetch sets the loading-state flag (R20); `SummaryView`'s label matches
  R21's designation + date-range shape.
- **`domain/labels.js`**: every `Unit`/`IngredientCategory` member has a
  mapped label (a loop over the enum's real values, not a hand-copied list —
  catches drift if the domain module ever adds a member).
- **`useSession.js`**: a stubbed `apiFetch` resolving `/v1/live-weeks`
  yields `{ status: "authenticated", role: "User" }` (R23); rejecting it
  with `code: "PASSWORD_RESET_PENDING"` yields `passwordResetPending`, with
  `code: "FORBIDDEN"` yields `{ authenticated, role: "Admin" }`, with any
  other code yields `anonymous` (R23); `login()` with
  `passwordResetRequired: true` in the response sets `passwordResetPending`
  without a role, `false` sets `authenticated` with the response's `role`
  (R25, R26); `setPassword()` calls the probe again after its `PUT`
  succeeds (R27); `logout()` sets `anonymous` after its `DELETE` (R32).
- **`LoginView`/`useLoginForm.js`**: renders a username field, a password
  field and a submit control (R24); submitting calls `apiFetch` with
  `POST /v1/session` and the entered `{ username, password }` (R25); an
  `INVALID_CREDENTIALS` `ApiError` sets an inline error message; no
  registration link/button exists anywhere on the screen (R29).
- **`SetPasswordView`/`useSetPasswordForm.js`**: renders only when
  `session.status === "passwordResetPending"` (R26); submitting calls
  `PUT /v1/session/password` with `{ newPassword }` (R27); a mismatched
  confirm field blocks submit before any call fires; a `PASSWORD_TOO_SHORT`
  `ApiError` renders its `detail`.
- **`useAdminAccounts.js`**: create posts `{ username, temporaryPassword }`
  with no third field (R35); rename `PATCH`es `{ username }`; reset
  `PATCH`es `{ temporaryPassword }` through `useConfirm` first; remove
  `DELETE`s through `useConfirm` first (extends R18); every mutation
  refetches the list rather than touching a marker.
- **`AdminAccountsView`/`AccountRow.test.jsx`**: a fixture list renders
  username, `ROLE_LABELS` text and a pending badge per row (R33); all four
  action controls render for an ordinary row (R34); a fixture row with
  `role: "Admin"` renders no remove control (R36); a fixture row whose
  `userId` matches the "acting admin" prop renders no reset-password
  control (R37); the create form's fields are exactly two, neither a role
  `<select>` (R35).
- **App shell logout** (`App.test.jsx`): the logout control renders in both
  the User and the Admin shell fixtures; clicking it calls `DELETE
  /v1/session` (R32).
- **Component tests** (rendering, `@testing-library/react`, `jsdom` per-file
  pragma like `usePolling.test.js`): `WeekLabel` renders "Semana actual" /
  "Semana próxima" plus a Monday–Sunday range formatted via `formatDate`
  (R21); `EmptyState`/`LoadingState` render the guidance text from
  `MESSAGES` (R19/R20, R15); `ConfirmDialog` renders the passed message and
  fires the right callback on each button (R18).
- **`tests/test_no_extra_accessibility.js`** (R22, mechanical, mirrors
  `backend/core/tests/test_no_ambient_time.py`'s technique): scans every
  `frontend/src/**/*.jsx` file's source text and fails on any `aria-*`
  attribute, non-native `role="..."`, explicit `tabIndex`, or an
  accessibility-oriented import (`@axe-core/*`, `react-aria`, etc.).
- **`tests/test_all_strings_from_messages.js`** (R15, spot-check, mirrors
  the same mechanical-scan idea; fix round 1 corrected a vacuous
  double-quoted-only scan — `.prettierrc.json`'s `singleQuote: true` makes
  every non-attribute literal single-quoted, so nothing was ever inspected):
  scans each component's `return` JSX for a single- or double-quoted string
  literal in a rendering position inside a `{...}` expression container
  (a ternary branch, or an `||`/`??`/`&&` fallback — never a comparison
  operand like `activeView === 'week'`) and for bare JSX text between
  sibling tags, failing on either when the content is not
  punctuation/whitespace-only and is not sourced from `MESSAGES` — catches
  a stray hardcoded Spanish (or English) string without needing to
  enumerate every screen's copy by hand. Fix round 2 (mutation-probe
  findings) closed three further gaps: (a) a quoted, letter-bearing prop
  value passed to a child (e.g. `<EmptyState message="..." />`) is flagged
  unless the attribute name is on a small structural allowlist (`type`,
  `className`, `id`, `key`, `htmlFor`, `name`, `href`, `src`,
  `data-testid`, `role`, `designation`, `value`); (b) a backtick template
  literal in the same rendering positions is scanned the same way a quoted
  literal is, flagged only when it carries a hardcoded text segment outside
  its `${...}` interpolations; (c) a `const` computed above `return` and
  referenced bare as `{name}` in the JSX (WeekLabel.jsx's own shape) has its
  initializer resolved and scanned for the same rendering-position
  violations. Also tightened (optional finding, fixed at low risk): the
  bare-text-between-tags paren exclusion now only skips a gap that carries
  a ternary/arrow operator (`?`, `:`, `=>`) alongside a paren — real JS
  syntax like `) : (` or `.map((x) => (` — so `<p>Cantidad (unidades)</p>`
  is no longer exempted by its own parenthetical aside.
- **`tests/test_no_self_password_change.js`** (R28, mechanical, same
  technique): scans every `frontend/src/components/**/*.jsx` file other than
  `SetPasswordView.jsx` for a call to `apiFetch` targeting
  `/v1/session/password` — fails if any other component calls it, proving
  the only path to changing a password is the forced set-password screen.
