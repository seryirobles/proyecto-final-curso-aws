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

## Reopened scope (2026-09-16) — visual design system completion

> No new `R<n>` (design.md §10.0 — this reopen elaborates feature 20's own
> acceptance criterion 3, not a new requirement). Each task cites the
> `R<n>`/`FR-*` the *component itself* already implements — the work is a
> styling-completeness fix, not new behaviour, so "Covers" names what the
> component already is, never a requirement newly gained.

### Tier A — foundation tokens

- [x] T64 — Add `frontend/src/tokens/fontFamily.js`: `FONT_FAMILY.heading/
  body/label`, each with a real fallback stack (design.md §10.1). No `R<n>`.
- [x] T65 — Add the three self-hosted `.woff2` files under
  `frontend/src/assets/fonts/` (Baloo 2 600/700, Nunito 400/600, DM Mono
  400 — OFL-licensed Google Fonts static files, not their CDN) and
  `frontend/src/fonts.js`'s `loadSelfHostedFonts()` (design.md §10.1, CSS
  Font Loading API — no `@font-face`, no stylesheet). No `R<n>`. The 5 real
  `.woff2` binaries were fetched directly from `fonts.gstatic.com`'s
  "latin" static subset (build-time asset fetch, not the runtime CDN
  `<link>` design.md rejects) — see progress/impl_frontend_spa.md for the
  exact URLs. `fonts.js` resolves each asset via `new URL(path,
  import.meta.url)` rather than design.md's literal `/src/assets/fonts/...`
  string, since a literal path only resolves in Vite dev and breaks after
  `vite build` hashes/moves the asset — a Vite-correctness fix, not a
  design change.
- [x] T66 — Call `loadSelfHostedFonts()` once from `frontend/src/main.jsx`,
  before `createRoot(...).render(...)`. No `R<n>`.
- [x] T67 — Add `frontend/src/tokens/borderRadius.js`: `RADIUS.none/sm/md/
  lg/pill` (design.md §10.2). No `R<n>`.
- [x] T68 — Add `frontend/src/tokens/shadow.js`: `SHADOW.none/sm/md/lg`,
  colour derived from `tokens.color.ink` (design.md §10.3). No `R<n>`.
- [x] T69 — Extend `frontend/src/tokens/index.js` to export `fontFamily`,
  `radius`, `shadow` alongside the existing four token groups (design.md
  §10.4). No `R<n>`.
- [x] T70 — Add a minimal inline `style` attribute to `frontend/index.html`'s
  `<body>` (background colour + generic `sans-serif` fallback only,
  design.md §10.5) — the one literal, non-token colour value this reopen
  permits, since static HTML cannot import a JS token; matched to
  `tokens.color.paper`'s literal value with a `// keep in sync with
  tokens/colors.js` comment. No `R<n>`.
- [x] T71 — Apply the foundation to `App.jsx`'s root wrapper element:
  `fontFamily: tokens.fontFamily.body`, `background: tokens.color.paper`,
  `color: tokens.color.ink`, full-height (design.md §10.5). No `R<n>`
  (extends the existing App-shell tasks T42/T58 — no new behaviour).
  Factored as a shared `rootShellStyle()` helper reused by both the Admin
  and User shell branches (the two existing root `<div>`s) — the
  `loading`/`anonymous`/`passwordResetPending` early returns are untouched,
  since restructuring those into the same wrapper is Tier C's `LoginView`/
  `SetPasswordView` card styling (T79/T80), not this task.

### Tier B — shared primitives

- [x] T72 — Style `EmptyState.jsx`/`LoadingState.jsx`: dashed-border card
  idiom for the empty state (`tokens.radius.md`, `tokens.color.line`),
  `tokens.fontFamily.body`; a loading-shimmer treatment reusing
  `tokens.color.surface2`/`surface` for the sweep, driven by a state tick
  in the existing hook (no CSS `@keyframes` — unavailable under the
  no-stylesheet rule). Covers: R19, R20 (styling completion — behaviour
  unchanged).
- [x] T73 — Style `ConfirmDialog.jsx`: backdrop (`tokens.color.ink` at low
  alpha) plus card shape (`tokens.radius.lg`, `tokens.shadow.lg`),
  `tokens.fontFamily.heading` for the prompt title. Covers: R18 (styling
  completion).
- [x] T74 — Style `ConnectionLostBanner.jsx`: correct palette —
  `tokens.color.honey`/`honeySoft` (warning accent) instead of the current
  mismatched colours; `tokens.radius.sm`. Covers: no new `R<n>` (consumes
  `FR-RT-03`, feature 26 — styling completion only).
- [x] T75 — Style `WeekLabel.jsx`: two-tier hierarchy — designation
  (current/next) in `tokens.fontFamily.heading`, the Monday–Sunday range in
  `tokens.fontFamily.label` beneath it (mined from the prototype's
  two-line week header). Covers: R16, R21 (styling completion).
- [x] T76 — Style `WeekSwitcher.jsx`: circular arrow buttons
  (`tokens.radius.pill`, fixed square dimensions) replacing the current
  plain rectangles. Covers: R2, R3 (styling completion).
- [x] T77 — Style `App.jsx`'s nav shell: header background/border/shadow
  (`tokens.color.surface`, `tokens.shadow.sm`), pill-shaped nav buttons
  (`tokens.radius.pill`) for the five-view nav strip and the logout
  control. Covers: no new `R<n>` (R30/R31/R32 already covered — styling
  completion).
- [x] T78 — `frontend/tests/components/*` (extend, Tier B): the shimmer
  tick in `LoadingState` is asserted through its exposed state, not a
  snapshot (`conventions.md` "Testing"); every other Tier B component test
  keeps the same props-in/markup-out assertions already proven in
  T10/T12/T44/T59, updated only where a structural change (e.g.
  `WeekSwitcher`'s button becoming a fixed-size circular element) makes an
  existing selector stale — no new behavioural assertions.

### Tier C — auth

- [x] T79 — Style `LoginView.jsx`: card container (`tokens.radius.md`,
  `tokens.shadow.md`), real input/button styling off tokens (currently
  unstyled native controls). Covers: R24, R25, R29 (styling completion).
- [x] T80 — Style `SetPasswordView.jsx`: same card treatment as T79.
  Covers: R26, R27, R28 (styling completion).
- [x] T80a — `frontend/tests/components/LoginView.test.jsx`,
  `SetPasswordView.test.jsx` (extend): selector-only updates for the new
  card markup — no new behavioural assertions.

### Tier D — planning

- [x] T81 — Style `WeekPlannerView.jsx`/`DaySlot.jsx`: day-card shape
  (`tokens.radius.md`, `tokens.shadow.sm`) per day cell, a status-badge
  treatment (`tokens.radius.pill`) for empty/has-candidates/has-definitive
  states. Covers: R1, R19, R20 (styling completion).
- [x] T82 (Partial) — Style `MealCard.jsx`: card shape (`tokens.radius.md`,
  `tokens.shadow.sm`) and icon-button treatment for its action controls
  done. The "IA" badge is **not implemented**: neither `docs/data_model.md`
  nor `docs/rest_api_contract.md` persists a candidate-origin field once an
  AI-generated recipe is accepted — `Candidate.author` is always the
  accepting human (`backend/core/src/planner_core/domain/candidate.py`),
  never a distinguishable "IA" marker, unlike the prototype's own
  `meal.author='IA'` idiom. See `progress/impl_frontend_spa.md`, Tier D.
  Covers: R4, R5 (styling completion, partial).
- [x] T83 — Style `RecipeDetailView.jsx`: slide-up-sheet shape
  (`tokens.radius.lg`, `tokens.shadow.lg`), pill badges for metadata, a
  numbered-step treatment for the procedure list (mined from the
  prototype's detail sheet). Covers: R4, R5 (styling completion).
- [x] T84 — `frontend/tests/components/*` (extend, Tier D): both existing
  files (`WeekPlannerView.test.jsx`, `RecipeDetailView.test.jsx`) passed
  **unmodified** against the new *markup* (same T80a outcome). That masked a
  real gap: T81's `dayStatus()` (three branches plus a definitive-over-
  candidates precedence rule) and its 3 new `WEEK_PLANNER_DAY_STATUS_*`
  message keys were new derived behaviour with zero test coverage, not mere
  restyling. Closed in the Tier D fix round: new `DaySlot.test.jsx` (all
  three branches + the precedence case), a promote-button and a
  day-indexing assertion added to `WeekPlannerView.test.jsx`, and an
  error-branch close-button assertion added to `RecipeDetailView.test.jsx`.
  `test_all_strings_from_messages.test.js`'s `SAFE_ATTR_NAMES` extended with
  SVG geometry attributes (a real false positive on the first inline `<svg>`
  icons this codebase has used, not a behavioural assertion).

### Tier E — library

- [x] T85 (Partial) — Style `LibraryView.jsx`/`LibraryRecipePicker.jsx`:
  card-grid layout (`tokens.radius.md`, `tokens.shadow.sm` per recipe card),
  a `tokens.radius.pill` category-color dot (new `CATEGORY_COLORS` in
  `domain/labels.js`), icon-button edit/remove row, instead of a plain list.
  The "IA" badge is **not implemented** — same wall as T82: no `Recipe`
  field distinguishes an AI-authored entry
  (`backend/core/src/planner_core/domain/recipe.py`). Covers: R9, R10, R11,
  R12 (styling completion, partial).
- [x] T86 — Style `LibraryFilters.jsx`: apply the token module at all
  (currently zero token references) — search input and category `<select>`
  styled off `tokens.color`/`tokens.space`/`tokens.radius.sm`. Covers: R11,
  R13, R14 (styling completion).
- [x] T87 — Style `RecipeAuthoringForm.jsx`'s non-AI parts only (`scratch`
  and `library` methods; the `ai` tab's stub content/behaviour stays
  untouched — feature 28's scope, design.md §10.6): form-field styling off
  tokens, an `--aub`-accented selector chip on the `ai` method tab so the
  disabled stub still reads as the AI path. Covers: R6, R7, R8 (styling
  completion).
- [x] T88 — `frontend/tests/components/*` (extend, Tier E): selector-only
  updates as T78/T84, plus one guard assertion that
  `RecipeAuthoringForm`'s `ai` tab still renders `canSubmit: false`
  (protects T22's stub logic from an accidental styling-pass regression).

### Tier F — summary / shopping / rules / admin

- [x] T89 — Style `SummaryView.jsx`: card shape (`tokens.radius.md`,
  `tokens.shadow.sm`) per definitive-meal row, pill-badge treatment
  consistent with T82. Covers: R5, R21 (styling completion).
- [x] T90 — Style `ShoppingListView.jsx`: checked items get a strikethrough
  (`textDecoration: 'line-through'`) alongside the existing `tokens.
  color.ink3` dimming (`FR-SHOP-08`'s "greyed out" wording is already met;
  the strikethrough is additional visual clarity mined from the prototype,
  not a new requirement), plus a card container per section
  (`tokens.radius.md`). Covers: R19, R20, R21 (styling completion; consumes
  `FR-SHOP-08`, feature 8).
- [x] T91 — Style `RulesView.jsx`: group rules by type (count/pin/disable)
  under `tokens.fontFamily.heading` section headers with a card container
  (`tokens.radius.md`) per group. Covers: R12, R19 (styling completion).
- [x] T92 — Style `AdminAccountsView.jsx`/`AccountRow.jsx`: an avatar-circle
  treatment (`tokens.radius.pill`, initials-based, no image dependency) per
  row, role/status badges (`tokens.radius.pill`, `tokens.color.terraSoft`/
  `honeySoft`) replacing the current plain text. Covers: R33, R34, R36,
  R37 (styling completion).
- [x] T93 — `frontend/tests/components/*` (extend, Tier F): selector-only
  updates as T78/T84/T88, plus one same-row-not-first-row targeting test per
  restyled list (Summary/Shopping/Rules/Admin) — every prior Tier F-adjacent
  round caught a handler misbound to the wrong row, so this tier adds that
  guard rather than relying on selector-only coverage alone.

### Gate

- [x] T94 — `./init.sh` green (frontend lint/format/test; `ruff`/`mypy`/
  `pytest` untouched by this reopen); update `progress/current.md`. This
  is the closing gate for the reopened scope — T63 remains the record of
  the original cycle's gate.
