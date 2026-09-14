# frontend_spa — Tasks

> Ordered. Each `[ ]` names the `R<n>` it covers, or "No `R<n>`" with the
> consumed `FR-*`/owning feature (design.md §1.2/§1.3) when the task wires
> already-covered behaviour rather than implementing one of this feature's
> own requirements. Read `design.md` first.

## Shared infrastructure

- [x] T1 — Add `frontend/src/api/client.js`: `ApiError`, `apiFetch(path,
  options)` (design.md §4.1). No `R<n>` (transport plumbing every view
  needs).
- [x] T2 — `frontend/tests/api/client.test.js`: `200`/`204` pass-through;
  `problem+json` non-2xx throws `ApiError` with the right fields; a rejected
  `fetch` throws `code: "NETWORK_ERROR"`. No `R<n>`.
- [x] T3 — Add `frontend/src/domain/labels.js`: `UNIT_LABELS`,
  `CATEGORY_LABELS`, `SLOT_LABELS`, `DAY_LABELS` (design.md §6). Covers: R15
  (labels sourced from one module, not scattered literals).
- [x] T4 — `frontend/tests/domain/labels.test.js`: every `Unit` and
  `IngredientCategory` member (imported from `planner_core`'s mirrored JS
  list — see T4a) has a mapped label. Covers: R15.
- [x] T4a — Add a small frontend-side literal mirror of the `Unit`/
  `IngredientCategory` wire codes (`frontend/src/domain/wireCodes.js`) used
  only by T3/T4 and by form dropdowns — the source of truth stays
  `backend/core/.../units.py` / `ingredient_category.py`; this file lists
  the same string values for the frontend toolchain, which cannot import
  Python. No `R<n>` (mirrors an already-decided backend vocabulary, adds no
  new value).
- [x] T5 — Add `frontend/src/hooks/useBreakpoint.js` (design.md §4.3).
  Covers: R17.
- [x] T6 — `frontend/tests/hooks/useBreakpoint.test.js`: fake `matchMedia`,
  initial value and a `change` event flip. Covers: R17.
- [x] T7 — Add `frontend/src/hooks/useConfirm.js` (design.md §4.4). Covers:
  R18.
- [x] T8 — `frontend/tests/hooks/useConfirm.test.js`: `requestConfirm` sets
  `pending`; `confirm()` invokes the handler once and clears; `cancel()`
  clears without invoking. Covers: R18.
- [x] T9 — Add `frontend/src/components/ConfirmDialog.jsx`,
  `EmptyState.jsx`, `LoadingState.jsx` (pure, tokens-styled). Covers: R18,
  R19, R20.
- [x] T10 — `frontend/tests/components/ConfirmDialog.test.jsx`,
  `EmptyState.test.jsx`, `LoadingState.test.jsx`: render the passed
  message/guidance text and fire the right callback. Covers: R15, R18, R19,
  R20.
- [x] T11 — Add `frontend/src/components/WeekLabel.jsx`: `{ designation,
  monday, sunday }` → "Semana actual/próxima · <Mon–Sun via
  `locale.js:formatDate`>". Covers: R16, R21.
- [x] T12 — `frontend/tests/components/WeekLabel.test.jsx`: both
  designations, date range formatted through `Intl` (assert against
  `formatDate` output, not a hand-written string). Covers: R16, R21.
- [x] T13 — Add `frontend/src/messages/es-ES.js` keys for every string this
  feature introduces (view titles, empty-state guidance, confirmation
  prompts, form labels, the AI-stub notice, generic/network error text).
  Covers: R15. Complete as of the T62 guard slice (2026-09-14): `es-ES.js`
  has grown to 145 keys across every section, and T62's now-verified-sound
  no-hardcoded-copy guard (progress/impl_frontend_spa.md — "T62 — Fix round
  3") proves no component in the tree sources copy outside this module.

## Week planner (R1–R6, consumes FR-CAND-04/-05/-07/-08)

- [x] T14 — Add `frontend/src/hooks/useWeekPlanner.js`: fetches
  `GET /v1/live-weeks` once on mount; `usePolling(GET /v1/weeks/{weekId})`
  for the selected week; exposes `switchWeek(designation)`,
  `openCandidateAuthoring(day, slot)`, `openDetail(recipe)`,
  `promoteDefinitive`/`clearDefinitive` (calling `PUT`/`DELETE
  …/slots/{slot}/definitive`, gated through `useConfirm` for clear/replace).
  Covers: R1, R2, R3, R18. No `R<n>` for the promote/clear domain outcome
  itself (`FR-CAND-05`/`-08`, feature 5) or author display (`FR-CAND-04`,
  feature 5) or snapshot semantics (`FR-CAND-07`, feature 4) — this task
  only wires the calls.
- [x] T15 — Add `frontend/src/components/WeekSwitcher.jsx`,
  `WeekPlannerView.jsx`, `DaySlot.jsx`, `MealCard.jsx` (pure, structural —
  7×2 grid, `EmptyState` for a slot with no candidates, `LoadingState`
  during the initial fetch). Covers: R1, R2, R3, R19, R20.
- [x] T16 — `frontend/tests/hooks/useWeekPlanner.test.js`: switching weeks
  requests the other `weekId` (R2); the returned view-model has identical
  field names/shape for both weeks (R3); `openCandidateAuthoring`/
  `openDetail` are called with the right arguments from a mocked day/slot
  (R4/R5 wiring, wired further in T20); `clearDefinitive` routes through
  `useConfirm` before calling `apiFetch` (R18); an empty slot flags
  `isEmpty` (R19).
- [x] T17 — `frontend/tests/components/WeekPlannerView.test.jsx`: renders
  seven days × two slots for a given week payload (R1); renders the same
  component tree shape for a "current" and a "next" fixture, differing only
  in data (R3).

## Recipe detail (R4, R5)

- [x] T18 — Add `frontend/src/hooks/useRecipeDetail.js`: opens with an
  already-held recipe object, or fetches `GET
  .../candidates/{candidateId}` / `GET /v1/library/recipes/{recipeId}` when
  only an id is passed. Covers: R4.
- [x] T19 — Add `frontend/src/components/RecipeDetailView.jsx`: renders
  ingredients (name/quantity/unit label via `domain/labels.js`), tools,
  procedure, estimated time, servings. Covers: R4.
- [x] T20 — Wire `openDetail` from `MealCard` (week view), the definitive
  slot's meal card, `SummaryView`'s meal rows, and `LibraryView`'s recipe
  rows to the same `useRecipeDetail` opener. Covers: R5. Complete as of the
  Summary view slice (2026-09-14): `SummaryView`'s meal buttons now call
  `useSummary.openDetail` (`useRecipeDetail` under the hood, T18) — the 4th
  and last of the 4 named call sites, alongside `MealCard` (regular +
  definitive, `useWeekPlanner.openDetail`) and `LibraryView`'s recipe rows
  (`useLibrary.openDetail`).
- [x] T21 — `frontend/tests/hooks/useRecipeDetail.test.js` +
  `RecipeDetailView.test.jsx`: full field rendering from a fixture recipe
  (R4); a shared-opener assertion — the same handler reference reaches all
  four call sites from T20 (R5). Complete as of the Summary view slice
  (2026-09-14): field rendering (R4) is fully covered; the shared-opener
  assertion is covered by `WeekPlannerView.test.jsx` (regular + definitive
  `MealCard`), `useLibrary.test.js`'s `openDetail` test (`LibraryView`'s
  rows), and `useSummary.test.js`/`SummaryView.test.jsx`'s `openDetail`
  tests (`SummaryView`'s meal rows) — all 4 of the 4 call sites.

## The shared authoring flow (R6, R7, R8)

- [x] T22 — Add `frontend/src/hooks/useRecipeAuthoring.js` (design.md §5.1):
  `mode: "candidate"` → methods `["library", "scratch", "ai"]`; `mode:
  "library"` → `["scratch", "ai"]`. Manual-form state for `scratch`
  (name/category/servings/estimatedTime/ingredients/tools/procedure); `ai`
  method exposes spec-input fields only, `canSubmit: false` (design.md §1.3
  stub). Covers: R6, R7, R8.
- [x] T23 — Add `frontend/src/components/RecipeAuthoringForm.jsx`: method
  tabs, the manual-form fields (category dropdown off `CATEGORY_LABELS`,
  ingredient rows with a unit dropdown off `UNIT_LABELS`), the `ai` tab
  rendering the disabled stub notice (`MESSAGES.AI_GENERATION_UNAVAILABLE`),
  and (for `mode: "candidate"` only) the `library` tab embedding
  `LibraryRecipePicker` (built in T25). Covers: R6, R7, R8, R20. Completed
  (library view slice, 2026-09-13): the `library` tab now embeds
  `LibraryRecipePicker`/`useLibraryPicker` (T25/T26 landed); the deferred
  placeholder is gone.
- [x] T24 — `frontend/tests/hooks/useRecipeAuthoring.test.js`: `mode:
  "candidate"` exposes exactly the three methods in order (R6); `mode:
  "library"` exposes exactly the two methods, `"library"` absent (R7, R8);
  submitting the `scratch` method posts the `manual` body shape from
  `rest_api_contract.md` §3.1; the `ai` method's submit stays disabled
  (design.md §1.3 — asserts no `POST /v1/generations` call is ever made by
  this feature).

## Library recipe picker (R11, R12, R13, R14) + Library view (R9, R10)

- [x] T25 — Add `frontend/src/hooks/useLibraryPicker.js`: `name`/`category`
  filter state; polls the fixed, unfiltered `GET /v1/library/recipes`
  (feature 26's hook) exactly once and stays subscribed, then filters the
  already-polled list client-side by `name`/`category` — presentation
  filtering of an already-fetched list, not a new request per keystroke
  (`rest_api_contract.md` §7 Q7). Covers: R11, R13, R14.
- [x] T26 — Add `frontend/src/components/LibraryRecipePicker.jsx`: search
  input + category `<select>` + result list, pure function of
  `useLibraryPicker`'s state. Covers: R11, R13.
- [x] T27 — Reuse `LibraryRecipePicker`/`useLibraryPicker` in three call
  sites: `RecipeAuthoringForm`'s `library` method (T23), the AI-stub tab's
  reference-recipe field (spec-input only, T22/T23), and `RulesView`'s
  pin-recipe field (T33). Covers: R12. Complete as of the Rules view slice
  (2026-09-14): all 3 of 3 sites wired — `useRecipeAuthoring` composes two
  `useLibraryPicker` instances for its `library`/`ai` tabs (library view
  slice, 2026-09-13), and `RulesView` embeds `LibraryRecipePicker` for its
  pin-recipe field, resolving pin display names from `useLibraryPicker`'s
  unfiltered `allRecipes` (T33/fix round 1, finding 6).
- [x] T28 — Add `frontend/src/hooks/useLibrary.js`: top-level library view
  state (`useLibraryPicker` plus add/edit/remove handlers routed through
  `useRecipeAuthoring`/`useConfirm`). Covers: R9, R10, R18.
- [x] T29 — Add `frontend/src/components/LibraryView.jsx`: recipe list
  (author shown per-recipe — `FR-CAND-04`/`FR-LIB-01` field, no attribution
  logic here), add/edit/remove actions, `EmptyState` for zero results.
  Covers: R9, R10, R19.
- [x] T30 — `frontend/tests/hooks/useLibraryPicker.test.js` +
  `useLibrary.test.js`: a `name` or `category` change filters the already-
  polled recipe list client-side, over the fixed unfiltered poll (R11, R13,
  F1 fix round 1); the filter state object has exactly the keys
  `name`/`category`, nothing else (R14); remove routes through
  `useConfirm` (R18); a fixture with recipes from two different authors
  both render (R9).
- [x] T31 — `frontend/tests/components/LibraryRecipePicker.test.jsx`: same
  component instance/props shape asserted from all three T27 call sites
  (R12). Complete as of T34 — `RecipeAuthoringForm`'s `library` method and
  `ai` reference-recipe field (T27), plus `RulesView`'s pin picker (T33).

## Rules view (consumes FR-RULE-01…07; reuses R12 for pin picker)

- [x] T32 — Add `frontend/src/hooks/useRules.js`:
  `usePolling(GET /v1/rules)`; add/edit via `PUT /v1/rules/{ruleId}`;
  remove via `DELETE /v1/rules/{ruleId}` gated by `useConfirm`; surfaces
  `UNSATISFIABLE_RULE_SET`'s `details.conflicts` from a caught `ApiError`
  (T1) as es-ES text. Covers: R18. No `R<n>` for rule semantics/
  satisfiability itself — `FR-RULE-01…07`, features 6 and 27.
- [x] T33 — Add `frontend/src/components/RulesView.jsx`: rule list, dropdown
  -only add/edit controls (category-count / pin-day-slot / disable-day, all
  fixed-value `<select>`s — never free text, mirroring `FR-RULE-03`'s own
  constraint), the pin rule's recipe field embedding `LibraryRecipePicker`
  (T27), `EmptyState` for zero rules. Covers: R12, R19.
- [x] T34 — `frontend/tests/hooks/useRules.test.js` +
  `RulesView.test.jsx`: remove routes through `useConfirm` (R18); an
  `UNSATISFIABLE_RULE_SET` `ApiError` renders `details.conflicts`'s es-ES
  text (no `R<n>` — the error text itself is R15's messages-module rule);
  the pin field's picker is the same shared component as T31 (R12).

## Shopping list view (consumes FR-SHOP-01…10)

- [x] T35 — Add `frontend/src/hooks/useShoppingList.js`:
  `usePolling(GET /v1/shopping-list)`; add/edit via `POST`/`PUT
  .../items`; check/uncheck via `PATCH .../items/{itemId}`; remove via
  `DELETE`, gated by `useConfirm`; resync via `POST
  .../shopping-list/resync`, surfacing `409 SHOPPING_LIST_LOCK_HELD` as
  es-ES text without auto-retry (`rest_api_contract.md` §3.3). Covers: R18,
  R20. No `R<n>` for aggregation/re-sync semantics (`FR-SHOP-*`, features 7,
  8, 27).
- [x] T36 — Add `frontend/src/components/ShoppingListView.jsx`: two
  sections (unchecked, then checked — greyed out via `tokens.color.ink3`),
  add/edit/remove controls, the resync button showing `LoadingState` while
  in flight, `EmptyState` for zero items, `WeekLabel`-scoped copy near the
  resync button (R21 — the button is week-scoped per `FR-SHOP-05`). Covers:
  R19, R20, R21.
- [x] T37 — `frontend/tests/hooks/useShoppingList.test.js` +
  `ShoppingListView.test.jsx`: remove routes through `useConfirm` (R18); an
  in-flight resync sets a loading flag (R20); zero items sets the
  empty-state flag (R19); the resync affordance renders `WeekLabel`'s
  designation/range text (R21); a `409` sets a retryable-error state with no
  automatic re-call.

## Summary view (consumes FR-SUM-01/-03; R5, R21)

- [x] T38 — Add `frontend/src/hooks/useSummary.js`:
  `usePolling(GET /v1/weeks/{weekId}/summary)`. Covers: none new — wires
  `FR-SUM-01`/`-03` (feature 5) plus reuses `openDetail` (R5) and
  `WeekLabel` (R21).
- [x] T39 — Add `frontend/src/components/SummaryView.jsx`: read-only
  definitive-meal grid, each meal opening `RecipeDetailView` via the shared
  opener (T20), `WeekLabel` header, `EmptyState` for a week with no
  definitives yet. Covers: R5, R19, R21.
- [x] T40 — `frontend/tests/hooks/useSummary.test.js` +
  `SummaryView.test.jsx`: clicking a meal calls the same `openDetail`
  handler asserted in T21 (R5); the header renders `WeekLabel` (R21); zero
  definitives sets the empty-state flag (R19).

## App shell (navigation, connection-loss indicator)

- [x] T41 — Add `frontend/src/hooks/useApp.js`: `activeView` state,
  `navigateTo(view)`. No `R<n>` (pure navigation plumbing — see design.md §7
  for why no router library is used).
- [x] T42 — Add `frontend/src/components/App.jsx`,
  `ConnectionLostBanner.jsx`: renders the nav strip + active view; the
  banner reads `connectionLost` off the active view's own poll(s) and
  renders `MESSAGES.CONNECTION_LOST` when true. No `R<n>` — wires `FR-RT-03`
  (feature 26, done, this feature's explicit job per its design §8).
- [x] T43 — `frontend/tests/hooks/useApp.test.js`: `navigateTo` switches
  `activeView` among all five nav targets.
- [x] T44 — `frontend/tests/components/App.test.jsx`,
  `ConnectionLostBanner.test.jsx`: the banner renders only when the active
  view's poll reports `connectionLost: true`; the correct view component
  mounts per `activeView`.
- [x] T45 — Update `frontend/src/main.jsx` to mount `App` instead of
  `PlaceholderView` (`PlaceholderView.jsx` itself is left in place, unused
  by the mounted app — it remains feature 1's scaffold record per its own
  doc comment; not deleted, since deleting it is not something this
  feature's `R<n>`s ask for).

## Auth screens — login, set-password, admin (fold, 2026-09-13; R23–R37, design.md §5a)

- [x] T46 — Add `frontend/src/hooks/useSession.js`: mount-time probe against
  `GET /v1/live-weeks` distinguishing `200`/`FORBIDDEN`/
  `PASSWORD_RESET_PENDING`/anything else into `authenticated(User)`/
  `authenticated(Admin)`/`passwordResetPending`/`anonymous`; `login(username,
  password)` posts `/v1/session`; `setPassword(newPassword)` puts
  `/v1/session/password` then re-probes; `logout()` deletes `/v1/session`
  (design.md §5a). Covers: R23, R25, R27, R32.
- [x] T47 — `frontend/tests/hooks/useSession.test.js`: each probe outcome
  (R23); `login`'s two branches by `passwordResetRequired` (R25, R26);
  `setPassword` re-probes after its `PUT` (R27); `logout` resets to
  `anonymous` (R32).
- [x] T48 — Extend `frontend/src/hooks/useApp.js` to compose `useSession()`;
  the five meal-planning `activeView` targets are reachable only when
  `session.status === "authenticated" && session.role === "User"`. Covers:
  R30, R31. Closed (2026-09-14): `App.jsx` now consumes `navTargets` and
  branches on `session.status`/`role` (T58/T59) — see
  `progress/impl_frontend_spa.md` "Auth screens, second half (T54-T60)".
- [x] T49 — `frontend/tests/hooks/useApp.test.js` (extend): role `Admin`
  exposes no meal-planning nav target (R30); role `User` exposes no `admin`
  nav target (R31).
- [x] T50 — Add `frontend/src/components/LoginView.jsx` +
  `frontend/src/hooks/useLoginForm.js`: username/password draft fields, a
  submit control calling `session.login`, an inline error for a caught
  `INVALID_CREDENTIALS` `ApiError`; no registration control (design.md
  §5a). Covers: R24, R25, R29.
- [x] T51 — `frontend/tests/hooks/useLoginForm.test.js` +
  `LoginView.test.jsx`: renders username+password+submit (R24); submit
  calls `POST /v1/session` with the entered values (R25); no
  registration link/button anywhere on the screen (R29).
- [x] T52 — Add `frontend/src/components/SetPasswordView.jsx` +
  `frontend/src/hooks/useSetPasswordForm.js`: new-password + confirm
  fields (client-side match check only), a submit control calling
  `session.setPassword`, a "Cancelar" control calling `session.logout`
  (design.md §5a). Covers: R26, R27.
- [x] T53 — `frontend/tests/hooks/useSetPasswordForm.test.js` +
  `SetPasswordView.test.jsx`: renders only while
  `session.status === "passwordResetPending"` (R26); submit calls `PUT
  /v1/session/password` with `{ newPassword }` (R27); a mismatched confirm
  field blocks submit; a `PASSWORD_TOO_SHORT` `ApiError` renders its
  `detail`.
- [x] T54 — Add `frontend/tests/test_no_self_password_change.js` (design.md
  §9, mechanical scan mirroring `test_no_extra_accessibility.js`'s
  technique): no `frontend/src/components/**/*.jsx` file other than
  `SetPasswordView.jsx` calls `apiFetch` against `/v1/session/password`.
  Covers: R28. Filename corrected to `test_no_self_password_change.test.js`
  — `vite.config.js`'s `include: ['tests/**/*.test.{js,jsx}']` would never
  pick up the literal `test_*.js` (pytest-style) name; see
  `progress/impl_frontend_spa.md`.
- [x] T55 — Add `frontend/src/hooks/useAdminAccounts.js`: `GET /v1/users` on
  mount (plain `apiFetch`, no `usePolling` — accounts is not one of
  `FR-RT-01`'s four pollable resources, design.md §5a); create (`POST
  {username, temporaryPassword}`, no role field — R35); rename (`PATCH
  {username}`); reset password (`PATCH {temporaryPassword}`, gated by
  `useConfirm`); remove (`DELETE`, gated by `useConfirm`, extends R18);
  every mutation refetches the list. Covers: R18, R35.
- [x] T56 — Add `frontend/src/components/AdminAccountsView.jsx` +
  `AccountRow.jsx`: create form (username + initial-password fields, no
  role selector); per-row username/`ROLE_LABELS`/pending-status (R33);
  rename/reset/remove controls per row (R34); the reset control hidden on
  the acting admin's own row (R37); the remove control hidden on an
  admin-role row (R36); `EmptyState`/`LoadingState` reused for the list.
  Covers: R33, R34, R36, R37, R19, R20.
- [x] T57 — `frontend/tests/hooks/useAdminAccounts.test.js` +
  `AdminAccountsView.test.jsx`/`AccountRow.test.jsx`: create posts exactly
  `{username, temporaryPassword}` (R35); rename/reset/remove call the right
  method+path; reset and remove both route through `useConfirm` first
  (R18); a fixture list renders username/role/pending badge per row (R33);
  all four controls render for an ordinary row (R34); an admin-role fixture
  row has no remove control (R36); a row matching the acting-admin's
  `userId` has no reset-password control (R37).
- [x] T58 — Add a logout control to `frontend/src/components/App.jsx`'s
  header, present in both the User and the Admin shell, wired to
  `session.logout` (design.md §5a). Covers: R32.
- [x] T59 — `frontend/tests/components/App.test.jsx` (extend): the logout
  control renders in both shells; clicking it calls `DELETE /v1/session`
  (R32). Also extend `App.jsx`'s own render-branch tests: `anonymous` →
  `LoginView`; `passwordResetPending` → `SetPasswordView`; `authenticated`
  + `Admin` → `AdminAccountsView` only (R30); `authenticated` + `User` →
  the existing five-view shell, no `admin` nav target (R31).
- [x] T60 — Extend `frontend/src/messages/es-ES.js` with every string T50,
  T52, T56 introduce (mined labels/captions per design.md §5a — "Usuario",
  "Contraseña", "Entrar", "Nueva contraseña", "Confirmar contraseña",
  "Guardar y entrar", "Cancelar", "Administración de usuarios", "Nuevo
  usuario", "Contraseña inicial", "Crear", "Renombrar", "Restablecer
  contraseña", "Eliminar", "contraseña pendiente", the `INVALID_CREDENTIALS`/
  `PASSWORD_TOO_SHORT`/`USERNAME_ALREADY_TAKEN` fallback captions). Extends
  T13. Covers: R15. No new keys added for those 3 error codes — `err.detail`
  already carries the backend's own es-ES text (design.md §4.1/§5a, "no new
  mechanism"); see `progress/impl_frontend_spa.md`.

## Cross-cutting mechanical guards (R15, R22)

- [x] T61 — Add `frontend/tests/test_no_extra_accessibility.js` (design.md
  §9): scans `frontend/src/**/*.jsx` source text for `aria-*`, a non-native
  `role="..."`, explicit `tabIndex`, or an accessibility-library import;
  fails if any is found. Covers: R22.
- [x] T62 — Add `frontend/tests/test_all_strings_from_messages.js`: scans
  each component's `return` JSX for (a) a single- or double-quoted string
  literal in a rendering position inside a `{...}` expression container
  (e.g. a ternary branch or `||`/`??`/`&&` fallback, never a comparison
  operand) and (b) bare JSX text between sibling tags, failing on either
  when the content is not whitespace/punctuation-only and is not a
  `MESSAGES.*` reference. Quote-agnostic (fix round 1 — `.prettierrc.json`'s
  `singleQuote: true` means a double-quoted-only scan is vacuous; every
  non-attribute literal in this codebase is single-quoted). Also flags (c)
  a non-allowlisted quoted prop value, (d) a backtick template literal with
  a hardcoded text segment, and (e) a `const` computed above `return` and
  referenced bare in the JSX (fix round 2 — design.md §9). Covers: R15.

## Gate

- [x] T63 — `./init.sh` green (ruff, mypy, pytest — untouched by this
  feature — plus frontend lint/format/test); update `progress/current.md`.
