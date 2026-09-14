# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

## 2026-09-14 — Reopen: features 16/27 GET /v1/rules recipeName bug, + feature 20 simplification — DONE

Owner-authorized reopen (`done -> in_progress` on 16/27 already done by the
leader before dispatch), no `spec_author` round — bug fully specified by
`docs/rest_api_contract.md`/`docs/data_model.md` §6 already. Fixed:
`rule_editing.read_rules` now takes `recipes: RecipeRepository` and resolves
each pin's `recipeName` (data_model.md §6 read-time-resolution pattern, one
`get()` per pin, ≤7); `serialization.py::encode_rule` carries it on the wire
for `PinRule`; `routing.py::_list_rules` wires `deps.recipes` through.
Frontend: `RulesView.jsx`'s `useLibraryPicker`-cross-reference workaround
removed — reads `rule.recipeName` straight off the API now (`useLibraryPicker`
itself untouched, `allRecipes` still exported per instruction, though no
other current call site consumes it).

Backend: `uv run pytest -q -m "not aws"` **798 passed** (795→798), ruff/mypy
clean. Frontend: `npx vitest run` **312/312**, `npx eslint .` clean. Both
mutation checks (dropped recipe-name resolution; dropped `recipeName` wire
field) confirmed killed by the new tests, reverted. Quality gates all green;
`./init.sh` §4 guardrails report the expected multi-`in_progress` state
(16/20/27 at once, per the leader's reopen scope), not a code issue. Full
detail: `progress/impl_rest_api_persistence_and_services.md` → "Reopen round
2026-09-14"; `progress/impl_frontend_spa.md` → "Reopen 2026-09-14".
`feature_list.json` untouched beyond the leader's existing 16/27 flips —
status changes are the owner's alone. Reviewer next.

## 2026-09-14 — Fix round 1: 3 reviewer findings on the recipeName reopen — DONE

Fixed a real surviving mutant plus 2 mechanical findings from the reviewer
on the round above. Detail:
`progress/impl_rest_api_persistence_and_services.md` → "Fix round 1
(2026-09-14)". Backend `uv run pytest -q -m "not aws"` **800 passed**
(798→800), ruff/mypy clean. Frontend `npx vitest run` **312/312**,
`npx eslint .` / `npx prettier --check .` clean. `feature_list.json`
untouched.

## 2026-09-14 — feature 20 `frontend_spa` — implementation-complete (T1–T63)

Final cleanup: `frontend/tests/test_all_strings_from_messages.test.js`'s
4-line `stripAttributeExpressions` header trimmed to 3 lines (points at
`progress/impl_frontend_spa.md` → "T62 — Fix round 3" instead of reproducing
the reasoning). `specs/frontend_spa/tasks.md` T13 ticked `[x]` — `es-ES.js`
has grown to 145 keys across every slice, and T62's guard (now verified
sound across 4 review passes) proves no component hardcodes copy outside it.

Every task T1–T63 in `specs/frontend_spa/tasks.md` is now ticked. `npx
vitest run` 312/312. `./init.sh` fully green (795 backend, ruff/mypy/
prettier/eslint/vitest). Feature 20 is genuinely, fully
implementation-complete. `feature_list.json` untouched — still
`in_progress`, status change is the owner's alone.

## 2026-09-14 — feature 20 `frontend_spa`, T62 — Fix round 3 (braced-attribute copy, real gap) — DONE

Reviewer found the round-2 `SAFE_ATTR_NAMES` allowlist only ever applied to
*quoted* (`attr="..."`) attribute values — `stripAttributeExpressions`
blanket-deleted every `attr={...}` braced value before anything scanned it,
so a braced prop (the ONLY possible shape for a conditional prop, and the
dominant `EmptyState`/`LoadingState` copy-passing pattern here — 9 call
sites) was completely invisible. Fixed: `stripAttributeExpressions` now
scans a braced value's inner text via `findRenderPositionLiterals` (same
ternary/fallback rendering-position logic already used for JSX children)
before stripping it, but only when the attribute is NOT allowlisted, NOT
`style`, and NOT an `/^on[A-Z]/` event handler, and the value itself isn't an
object literal (`^\{`) or a function/arrow body — catalogued from every
real braced-attribute shape in `frontend/src/components/**/*.jsx` (all
`style={{...}}` or `on*={...}` besides plain member-expression props), so no
new false positive was introduced.

Both exact reviewer mutants (`ShoppingListView.jsx`'s `EmptyState` →
`message={'Todavia no hay elementos en la lista de la compra.'}` and →
`message={items.length ? 'Sin elementos pendientes' :
MESSAGES.SHOPPING_LIST_VIEW_EMPTY}`) hand-planted, confirmed **killed**,
reverted, diffed byte-identical. All 5 previously-fixed mutants (EmptyState
`||` fallback, LoadingState bare text, the round-2 quoted-prop mutant, the
WeekLabel template-literal mutant, the WeekLabel plain-string mutant)
re-verified still **killed**. Full zero-false-positive sweep against the
real tree: clean (312/312 `npx vitest run` includes the R15 sweep). 4-line
comment (~scanRegion header) trimmed to 3. `npx eslint .` clean, `npx
prettier --check .` clean (one `--write`, line-wrap only on the new test
cases). `./init.sh` fully green (795 backend, ruff/mypy/prettier/eslint/
vitest). Full detail: `progress/impl_frontend_spa.md` → "T62 — Fix round 3
(braced-attribute copy, real gap)". `feature_list.json` untouched. Still
`in_progress` — reviewer verification next.

## 2026-09-14 — feature 20 `frontend_spa`, T62 — Fix round 2 (adversarial mutation probe) — DONE

Reviewer's adversarial mutation probe found 3 further real gaps in the fix
round 1 guard, plus 2 mechanical items. **F1 (blocking):** the blanket
`attr="..."` exclusion swallowed hardcoded prop text too (e.g.
`<EmptyState message="..." />`, the dominant way copy reaches leaf
components here) — replaced with a `SAFE_ATTR_NAMES` allowlist
(`type`/`className`/`id`/`key`/`htmlFor`/`name`/`href`/`src`/
`data-testid`/`role`/`designation`/`value`, catalogued from the real tree)
so anything else quoted and letter-bearing is flagged. **F2 (blocking):**
backtick template literals were invisible to the scan (prettier never
touches them) — now scanned in the same rendering positions, flagged only
when a hardcoded text segment exists outside `${...}` interpolations.
**F3 (real gap, fixed not documented):** a `const` computed above `return`
and referenced bare as `{name}` (the `WeekLabel.jsx` shape) is now resolved
and scanned too. **F5 (optional, fixed at low risk):** the bare-text paren
exclusion is narrowed to only exempt a gap that also carries a ternary/arrow
operator (real JS syntax like `) : (`), so `<p>Cantidad (unidades)</p>`-style
prose is no longer exempted. **F4 (mechanical):** 10-line file header
trimmed to 3 lines.

Both original mutants (EmptyState `||` fallback, LoadingState bare text)
re-verified still caught. 4 new mutants hand-planted on the real tree
(F1: `ShoppingListView.jsx`'s `EmptyState`; F2+F3 combined and F3 isolated:
`WeekLabel.jsx`'s `designationLabel`) — all caught, all reverted and
diffed byte-identical against backups. `npx vitest run` 309/309 (301→309:
8 new self-check cases). `npx eslint .` clean, `npx prettier --check .`
clean (one `--write`, line-wrap only). `./init.sh` fully green (795
backend, ruff/mypy/prettier/eslint/vitest). `specs/frontend_spa/design.md`
§9 and `tasks.md` T62 updated to describe the 3 new detection paths + the
F5 tightening. Full detail: `progress/impl_frontend_spa.md` → "T62 — Fix
round 2 (adversarial mutation probe, 5 findings)". `feature_list.json`
untouched. Still `in_progress` — reviewer verification next.

## 2026-09-14 — feature 20 `frontend_spa`, T62 — Fix round 1 (vacuous guard) — DONE

Reviewer found `test_all_strings_from_messages.test.js`'s scan was vacuous
(`.prettierrc.json`'s `singleQuote: true` means it only ever matched
double-quoted literals, a set that's empty by construction after prettier)
and also missed bare JSX text entirely. **Confirmed real, fixed:** the
guard is now quote-agnostic, JSX-aware (scoped to each component's `return`
JSX, distinguishing a ternary/fallback rendering position from a comparison
operand, and bare text between real sibling tags from a `.length > 0`-style
false match), mutation-verified against both of the reviewer's named
violation classes. **Reviewer's cited live violation — checked, not
present:** `EmptyState.jsx` was read along with its 9 call sites and its
test; the real file is `{message}`, no fallback, no such string, no
`EMPTY_STATE_DEFAULT` key anywhere — nothing to fix there. Docs corrected
(`design.md` §9, `tasks.md` T62, both said "double-quoted"). Full detail:
`progress/impl_frontend_spa.md` → "T62 — Fix round 1 (reviewer finding:
vacuous guard)".

`npx vitest run` 301/301 (299→301), `npx eslint .` clean, `npx prettier
--check .` clean, `./init.sh` fully green (795 backend,
ruff/mypy/prettier/eslint/vitest). `feature_list.json` untouched.

## 2026-09-14 — feature 20 `frontend_spa`, Cross-cutting mechanical guards + Gate (T61–T63) — DONE, FEATURE IMPLEMENTATION-COMPLETE

**This is the final task of feature 20.** All of T1–T63 are now ticked in
`specs/frontend_spa/tasks.md`; feature 20 `frontend_spa` is
implementation-complete, built entirely on the reviewer-approved T1–T60.

`frontend/tests/test_no_extra_accessibility.test.js` (R22, scans
`frontend/src/**/*.jsx` for `aria-*`, explicit `role="..."`, `tabIndex`, or
an accessibility-library import) and `frontend/tests/
test_all_strings_from_messages.test.js` (R15, scans
`frontend/src/components/**/*.jsx` for a hardcoded JSX-text double-quoted
literal outside `MESSAGES.*`, after stripping comments/imports/attribute
values) — both mirror `test_no_self_password_change.test.js`'s established
mechanical-scan pattern and `backend/core/tests/test_no_ambient_time.py`'s
technique per design.md §9. **Both guards passed clean on first run — no
violation found.** 60 tasks and 20+ review rounds across this feature held
the accessibility and es-ES-messages invariants with no drift. Filenames
use `*.test.js` (not tasks.md's literal `test_*.js`), the same
`vite.config.js` glob fix T54 already established.

`npx vitest run` 299/299 (295→299: 2 new files, 2 cases each — one
self-verifies each scan's pattern before trusting it, one runs it against
the real tree). `npx eslint .` clean. `./init.sh` fully green: ruff, mypy,
**795 backend pytest** (untouched by this feature), prettier, eslint,
vitest all pass. Full traceability: `progress/impl_frontend_spa.md` →
"Cross-cutting mechanical guards + Gate (T61–T63)". `feature_list.json`
untouched — status left `in_progress`; ready for a final comprehensive
review before the owner considers marking it `done`.

## 2026-09-14 — feature 20 `frontend_spa`, Auth screens second half — Fix round 1 (5 findings) — DONE

Finding 1 (BLOCKING, real bug, security-relevant, fail-open R37 violation
after reload): `AccountRow.jsx`'s `isOwnRow` now fails **closed** —
`actingUserId == null` hides reset on every row instead of showing it on
every row. New `AccountRow.test.jsx` case covers the unknown-identity state
explicitly. Known usability tradeoff, not fixed here (owner-flagged
separately): a reloaded Admin session still can't reset ANY row (including
ones it should) until a fresh `login()` populates `session.userId` — the
mount probe (`GET /v1/live-weeks`) carries no `userId` field
(`rest_api_contract.md` verified); needs a backend contract change or a
different identity source, out of scope for this fix. Finding 2 (BLOCKING,
surviving mutant): `App.test.jsx`'s `AdminAccountsView` mock now renders
`actingUserId` into its marker text, so deleting App.jsx's
`actingUserId={session.userId}` wiring now fails the Admin-shell test.
Finding 3 (BLOCKING, 2 surviving mutants): `useAdminAccounts.test.js`'s
rename/remove tests now assert the post-mutation refetch (call count +
`toHaveBeenLastCalledWith('/v1/users')`). Finding 4 (mechanical): 6
over-length comments trimmed to the 3-line ceiling (`App.jsx`,
`useAdminAccounts.js`, `useSession.js`, `App.test.jsx`,
`useAdminAccounts.test.js`, `test_no_self_password_change.test.js`).
Finding 5 (mechanical): T60/this file's "15 new `es-ES.js` keys" corrected
to 13 (`ROLE_LABELS`' 2 values live in `domain/labels.js`, a different file).

`npx vitest run` 295/295 (294→295: +1 new case, `AccountRow.test.jsx`'s
fail-closed test; findings 2/3 extended existing tests' assertions instead
of adding cases), `npx eslint .` clean. No `backend/` file touched,
`feature_list.json` untouched. Full detail:
`progress/impl_frontend_spa.md` → "Auth screens, second half (T54–T60)" →
"Fix round 1". Still `in_progress` — reviewer verification next.

## 2026-09-14 — feature 20 `frontend_spa`, Auth screens second half (T54–T60) — DONE

**Feature in progress: 20 — frontend_spa (T54–T60 only, per explicit dispatch
scope; built on the reviewer-approved T1–T53). Also closes T48 (fully
ticked, no longer "Partial") — `App.jsx` now consumes `navTargets` and
branches its render on `session.status`/`role`, the wiring the previous
review explicitly deferred here.**

`frontend/src/hooks/useAdminAccounts.js` (plain `GET /v1/users` on mount,
not `usePolling`; create/rename/reset/remove, reset+remove gated by
`useConfirm`, every mutation refetches), `frontend/src/components/
AdminAccountsView.jsx` + `AccountRow.jsx` (create form, no role selector;
reset hidden on the acting admin's own row R37; remove hidden on an
admin-role row R36), `frontend/src/domain/labels.js` (+`ROLE_LABELS`),
`frontend/tests/test_no_self_password_change.test.js` (mechanical scan,
R28). `App.jsx` extended: logout control in both shells (R32, T58); full
4-way render branch on `session.status`/`role` — `loading`→`LoadingState`,
`anonymous`→`LoginView`, `passwordResetPending`→`SetPasswordView`,
`Admin`→`AdminAccountsView` only (R30), `User`→ existing 5-view shell
restricted to `navTargets` (R31), trailing `return null` documents the
branch as exhaustive. 13 new `es-ES.js` keys (`APP_LOGOUT` + 12
`ADMIN_ACCOUNTS_*`); the 2 `ROLE_LABELS` values are `domain/labels.js`, a
different module (fix round 1 finding 5 corrected this from a mis-reported 15).

**Design decision (disclosed):** `useSession.js` gained `userId` on
`login()`'s authenticated branch (additive, no existing test changed) —
design.md's own `AdminAccountsView` row already assumed an "acting admin"
prop sourced from session, needed for R37, but T46 never captured it since
the mount-probe response carries no `userId`. Known, bounded limitation:
a page reload as an already-logged-in Admin leaves `userId` unknown, so the
reset control shows on that admin's own row too; the server still rejects
it with `Forbidden` (same generic error surfacing as every other mutation).
Also corrected: the real endpoint path param is `{userId}` (verified
against `routing.py`/`rest_api_contract.md`), not `{username}` as the
dispatch brief's shorthand said; and T54's literal filename
(`test_no_self_password_change.js`) never matches `vite.config.js`'s
`*.test.{js,jsx}` include glob, so it was named
`test_no_self_password_change.test.js` instead (tasks.md notes this).

4 mutation probes hand-applied and confirmed **killed**, then reverted:
`AccountRow.jsx`'s `isOwnRow`/`isAdminRow` conditions (R37/R36 — the
"swapped condition still renders something, just not verified which" bug
class this feature's reviews keep flagging), `App.jsx`'s `isAdmin`/`isUser`
collapse, and `App.jsx`'s `loading` branch deletion (the last one surfaced
a genuine pre-existing test gap — no case covered `loading` — fixed by
adding the test before probing, not after).

`npx vitest run` 294/294 (265→294), `npx eslint .` clean, `npx prettier
--check .` clean, `npx vite build` succeeds (64 modules, sanity-checks the
real import graph — no live backend available in this environment to
exercise the actual network round-trip), `./init.sh` fully green (795
backend, ruff/mypy/prettier/eslint/vitest). `tasks.md` T54–T60 ticked, T48
flipped from Partial to `[x]`. Full traceability, all deviations and the
mutation-probe detail: `progress/impl_frontend_spa.md` → "Auth screens,
second half (T54–T60)". `feature_list.json` untouched. Status left
`in_progress` — reviewer next.

## 2026-09-14 — feature 20 `frontend_spa`, Auth screens — Fix round 1 (4 findings) — DONE

F1 (blocking, security, 2 surviving mutants): added `type` assertions on all
3 password inputs (`LoginView.test.jsx`, `SetPasswordView.test.jsx`);
hand-flipped each `type="password"` to `type="text"`, confirmed failure,
reverted — all three mutants **killed**. F2 (docs-only, real mismatch):
`specs/frontend_spa/design.md` §5a corrected — backend checks role *before*
password-reset status (`handler.py`), not the reverse as previously
claimed. Flagged limitation for the owner: an Admin with a pending reset
probes as `authenticated(Admin)` (403 FORBIDDEN from the role check), not
`passwordResetPending` — reachable only via the mount probe, not login;
bounded, no security exposure. 3-line pointer comment added next to
`useSession.js`'s `classifyProbeFailure`. F3 (mechanical): `tasks.md` T48
un-ticked with a "Partial" note matching the feature's established
convention. F4 (mechanical): 3 over-length header comments trimmed to the
3-line ceiling (`useSession.js`, `useApp.js`, `useSetPasswordForm.js`).
`npx vitest run` 265/265 (263→265), `npx eslint .` clean. No `backend/` file
touched. Full detail: `progress/impl_frontend_spa.md` → "Auth screens — Fix
round 1". `feature_list.json` untouched. Still `in_progress` — reviewer
verification next.

## 2026-09-14 — feature 20 `frontend_spa`, Auth screens first half (T46–T53) — DONE

**Feature in progress: 20 — frontend_spa (T46–T53 only, per explicit dispatch
scope; T54 self-password-change scan, admin accounts, App.jsx's logout
control and the anonymous/passwordResetPending/Admin render-branch wiring are
a separate implementer run). Built on the reviewer-approved T1–T45.**

`frontend/src/hooks/useSession.js` (mount-time probe against `GET
/v1/live-weeks` classifying `200`/`FORBIDDEN`/`PASSWORD_RESET_PENDING`/other
into the 4-way `authenticated(User)`/`authenticated(Admin)`/
`passwordResetPending`/`anonymous` state; `login`/`setPassword`/`logout`),
`useApp.js` extended to compose `useSession()` and expose an additive
`navTargets` field (role-gated subset of `VIEWS` — `navigateTo` itself stays
ungated, since gating it would break `App.test.jsx`'s existing synchronous
`fireEvent.click` assertions; `App.jsx`'s real render-branch enforcement is
T59, not this run), `useLoginForm.js`/`LoginView.jsx`,
`useSetPasswordForm.js`/`SetPasswordView.jsx`, 10 new `es-ES.js` keys.
`App.test.jsx` gained one addition (`useSession.js` mock) to stay free of
real network calls now that `useApp` composes it.

`npx vitest run` 263/263 (232→263), `npx eslint .` clean, `npx prettier
--check .` clean, `./init.sh` fully green (795 backend,
ruff/mypy/prettier/eslint/vitest). Two hand-applied mutants on the
load-bearing probe classification and role gate both hand-verified
**killed**, reverted. `tasks.md` T46–T53 ticked. Full traceability, the
`navTargets` design deviation and the `useSession` error-handling design:
`progress/impl_frontend_spa.md` → "Auth screens, first half — session probe,
nav gating, login, set-password (T46–T53)". `feature_list.json` untouched.
Status left `in_progress` — reviewer next.

## 2026-09-14 — feature 20 `frontend_spa`, App shell — Fix round 1 (5 findings) — DONE

F1 (BLOCKING, measured: ~72 req/min, 83% off-screen): each of the 5 view
hooks now takes `{ active = true }`, threaded to every `usePolling`/
`useLibraryPicker` call inside (including `useRecipeAuthoring`'s two
pickers, ANDed with its own `method` gate); `App.jsx` passes `{ active:
activeView === '<view>' }` per hook. F2 (BLOCKING): `weekUrl`/`summaryUrl`
now gate `enabled` too, no more `fetch(null)`. F3/F4 (mechanical): removed
the false "Rules of Hooks forbid a per-view hook" rationale from `App.jsx`'s
banner (trimmed to 3 lines) and this file; F5a: `App.jsx` derives
`NAV_ITEMS` from `useApp.js`'s `VIEWS` instead of duplicating it; F5b:
corrected the impl report's `FR-RT-03` sentence (consumed, not owned).
Proof (`App.polling.test.jsx`, real hooks, fake timers, 60s): active
view's poll fires repeatedly, the other 4 views' polls **never** fire (0
requests each). `npx vitest run` 232/232 (221→232), `npx eslint .` clean,
`npx prettier --check .` clean, `./init.sh` fully green (795 backend,
ruff/mypy/prettier/eslint/vitest). Zero regressions across the 5 view-hook
suites + `App.test.jsx` + `useApp.test.js` + `useRecipeAuthoring.test.js` +
`useLibraryPicker.test.js` (86 tests). Full traceability: `progress/
impl_frontend_spa.md` → "App shell — Fix round 1". `feature_list.json`
untouched. Status left `in_progress` — reviewer next.

## 2026-09-14 — feature 20 `frontend_spa`, App shell (T41–T45) — DONE

**Feature in progress: 20 — frontend_spa (T41–T45 only, per explicit dispatch
scope; Auth screens section T46+ is a separate implementer run). Built on
the reviewer-approved T1–T40 (all 7 meal-planning views).**

`frontend/src/hooks/useApp.js` (`activeView` state, `navigateTo(view)`, no
auth/session awareness — T48/T49 extend it later), `frontend/src/components/
App.jsx` (nav strip reusing `WeekSwitcher.jsx`'s active/inactive `terraSoft`
button pattern, the active view's component, one `ConnectionLostBanner`),
`ConnectionLostBanner.jsx` (`honeySoft` warning accent), 6 new `es-ES.js`
keys (5 `NAV_*` + `CONNECTION_LOST`), `main.jsx` now mounts `App` instead of
`PlaceholderView` (`PlaceholderView.jsx` itself untouched, feature 1's
scaffold record). Design decision: verified all 5 view hooks expose a
top-level `connectionLost` boolean (convention holds); `App.jsx` calls all 5
unconditionally (Rules of Hooks forbid a different hook per branch across
renders) and picks the active one's `connectionLost` for the single banner
— noted, not fixed, tradeoff: all 5 polls run regardless of active view,
harmless data-wise, no `R<n>` governs it. 3 new test files, 8 new cases;
`App.test.jsx` mocks the 5 hooks + 5 view components so it tests only
`App.jsx`'s own wiring. 2 hand-applied mutants (active-view lookup pinned to
`week`; banner guard flipped) both hand-verified **killed**, reverted. `npx
vitest run` 221/221 (213→221), `npx eslint .` clean, `npx prettier --check .`
clean, `npx vite build` succeeds (first real mount of `App`, not
`PlaceholderView`), `./init.sh` fully green (795 backend,
ruff/mypy/prettier/eslint/vitest). `tasks.md` T41–T45 ticked. Full
traceability: `progress/impl_frontend_spa.md` → "App shell (T41–T45)".
`feature_list.json` untouched. Status left `in_progress` — reviewer next.

## 2026-09-14 — feature 20 `frontend_spa`, Summary view fix round 1 (3 findings) — DONE

Finding 1 (2 surviving mutants, slot-label swap + day off-by-one in
`SummaryView.jsx`): one new `within()`-scoped test proves a meal renders in
its own day column with its own slot label and not in another day's column
— both mutants hand-verified **killed**, reverted. Finding 2: `useSummary.js`
banner trimmed to 3 lines, pointing at `progress/impl_frontend_spa.md` ->
"Summary view (T38–T40)". `npx vitest run` 213/213 (212→213), `npx eslint .`
clean, `./init.sh` fully green. Detail: `progress/impl_frontend_spa.md` ->
"Fix round 1 (reviewer findings, 2026-09-14)". `feature_list.json`
untouched. Still `in_progress` — reviewer verification next.

## 2026-09-14 — feature 20 `frontend_spa`, Summary view (T38–T40) — DONE

**Feature in progress: 20 — frontend_spa (T38–T40 only, per explicit dispatch
scope; App shell/Auth sections are separate implementer runs). Built on the
reviewer-approved T1–T37 — closes T20/T21's deferred 4th and final
`openDetail` call site (`SummaryView`'s meal rows), the last of the 4 named
sites.**

`frontend/src/hooks/useSummary.js` (fetches `GET /v1/live-weeks` once, polls
`GET /v1/weeks/{weekId}/summary` for the current live week only — the
Screens table cites just R5/R21 for this view, not R2/R3, so no designation
switcher was added; `buildSummaryViewModel` regroups the backend's
definitive-only `meals` array back into the full 7×2 grid shape so empty
slots have a cell to skip), `frontend/src/components/SummaryView.jsx`
(read-only grid, `WeekLabel` header, `EmptyState` for a week with zero
definitives, each meal button opening `RecipeDetailView` via the shared
`useRecipeDetail` opener), 2 new `es-ES.js` keys
(`SUMMARY_VIEW_TITLE`/`_EMPTY`). `tasks.md` T38/T39/T40 ticked; **T20 and T21
flipped from "3 of 4"/Partial to fully `[x]`** — all four `openDetail` call
sites now exist. 2 new test files, 12 new cases (5 hook + 7 component),
including a day/slot-membership assertion (not just presence) per the
Shopping list slice's M2 lesson — mutation-hand-verified **killed** by
corrupting the grouping key to always resolve to day 1. `npx vitest run`
212/212 (200→212), `npx eslint .` clean, `npx prettier --check .` clean,
`./init.sh` fully green (795 backend, ruff/mypy/prettier/eslint/vitest).
Full traceability: `progress/impl_frontend_spa.md` → "Summary view
(T38–T40)". `feature_list.json` untouched. Status left `in_progress` —
reviewer next.

## 2026-09-14 — feature 20 `frontend_spa`, Shopping list view fix round 1 (6 findings) — DONE

M1/M2/M3 surviving mutants fixed in their tests (edit-body deep-equal,
per-section `within()` scoping, fake-timer no-retry check) and hand-verified
**killed**. M4 ("resync button stays disabled forever after a 409") — the
`finally { setIsResyncing(false) }` was already present in the committed
`useShoppingList.js`; added the missing regression test only, mutant
(moving the reset to the success branch) hand-verified **killed**. Decision
2 (real UX bug): `SHOPPING_LIST_RESYNC_SCOPE_LABEL` reworded to state the
true `FR-SHOP-05` scope ("desde hoy hasta el final de la semana próxima"),
new `SHOPPING_LIST_RESYNC_SCOPE_CONNECTOR` ("y") renders between the two
`WeekLabel`s — `WeekLabel.jsx` itself untouched. Decision 3: new test proves
a failed live-weeks fetch leaves `liveWeeks: null` and `error: null`. `npx
vitest run` 200/200 (198→200), `npx eslint .` clean, `npx prettier --check .`
clean, `./init.sh` fully green (795 backend, ruff/mypy/prettier/eslint/vitest).
Full detail: `progress/impl_frontend_spa.md` → "Shopping list view — Fix
round 1". `feature_list.json` untouched. Still `in_progress` — reviewer next.

## 2026-09-14 — feature 20 `frontend_spa`, Shopping list view (T35–T37) — DONE

`frontend/src/hooks/useShoppingList.js` (usePolling(GET /v1/shopping-list),
add/edit/check/remove/resync, a 409 `SHOPPING_LIST_LOCK_HELD` sets `error`
with no auto-retry), `frontend/src/components/ShoppingListView.jsx`
(unchecked/checked sections, checked rows greyed via `tokens.color.ink3`,
resync button showing two `WeekLabel`s — current + next, per `FR-SHOP-05`'s
two-week scope), 18 new `es-ES.js` keys. Edit pre-fills from the real item
(F4 lesson, no data loss). 2 new test files, 24 new cases. `npx vitest run`
198/198 (174→198), `npx eslint .` clean, `npx prettier --check .` clean,
`./init.sh` fully green (795 backend, ruff/mypy/prettier/eslint/vitest).
`tasks.md` T35/T36/T37 ticked. Full traceability + design decisions:
`progress/impl_frontend_spa.md` → "Shopping list view (T35–T37)".
`feature_list.json` untouched. Status left `in_progress` — reviewer next.

## 2026-09-14 — feature 20 `frontend_spa`, Rules view (T32–T34)

**Feature in progress: 20 — frontend_spa (T32–T34 only, per explicit dispatch
scope; Shopping list/Summary/App shell/Auth sections are separate
implementer runs). Built on the reviewer-approved T1–T31 — closes T31's
deferred 3rd `LibraryRecipePicker` call site (`RulesView`'s pin-recipe
field).**

`frontend/src/hooks/useRules.js`, `frontend/src/components/RulesView.jsx`,
17 new `es-ES.js` keys (16 `RULES_*` + `CONFIRM_REMOVE_RULE`). `GET /v1/rules`
polled unfiltered (no query params — the library slice's filtered-URL bug
does not apply here). Two design gaps
filled, both recorded in `progress/impl_frontend_spa.md` → "Rules view
(T32–T34)": (1) the real, `done` backend never returns a pin rule's
`recipeName` despite the docs describing one — `RulesView` resolves it by
cross-referencing the already-polled library list instead; (2) no row-level
"Editar" control exists at all — `PUT /v1/rules/{ruleId}` is a blind
upsert-by-natural-key, so a prefillable identity field would risk silently
orphaning the original rule (the library slice's F4 bug class, inverted).
3 new test files/additions (`useRules.test.js`, `RulesView.test.jsx`, +1 case
in `LibraryRecipePicker.test.jsx` completing T31). `npx vitest run` 172/172
(155→172), `npx eslint .` clean (fixed one `exhaustive-deps` warning),
`npx prettier --check .` clean, `./init.sh` fully green (795 backend,
ruff/mypy/prettier/eslint/vitest). `tasks.md` T32/T33/T34 ticked; T31
completed (un-ticked "Partial" → done). Full traceability and the design
decisions: `progress/impl_frontend_spa.md` → "Rules view (T32–T34)".
`feature_list.json` untouched. Status left `in_progress` — reviewer next.

**Fix round 1 (6 findings, 2026-09-14):** F1/F2 surviving-mutant tests fixed
(composed row-label assertion; dropdown-only-controls test) and confirmed
killing by hand; F3 comment trims; F4 `tasks.md` T27 ticked (3/3 sites); F5
key-count corrected to 17; F6 real bug fixed — `useLibraryPicker` now exposes
unfiltered `allRecipes`, `RulesView` resolves pin names from it so the pin
picker's own search box no longer churns pin rows to raw ids. `npx vitest run`
174/174, `npx eslint .` clean, `./init.sh` fully green. Details:
`progress/impl_frontend_spa.md` → "Rules view — Fix round 1".

## 2026-09-13 — feature 20 `frontend_spa`, library slice fix round 3 (regression) — DONE

Owner-reported regression, not a reviewer finding: fix round 2's `disposed`
flag on `pollingEngine.js` is permanent, but `usePolling.js` still memoized
its engine on `[url, config, createEngine]` — no `enabled` dependency — so
an `enabled: true -> false -> true` cycle (switching the authoring form's
`library`/`ai` tabs) disposed then reused the SAME engine, killing polling
after exactly one more fetch. Fixed: the memo now also keys on a
`generation` counter that bumps only on the `false -> true` transition
(via `useState`, not `useRef` — this project's `react-hooks/refs` eslint
rule forbids ref access during render), forcing a fresh, non-disposed
engine on every re-enable. Also closed the related gap the reviewer had
flagged as non-blocking: `pollNow()` (used by `applyMutationMarker` and the
visibility-regain path) had no `disposed` guard, added the same one-liner
`scheduleNext()` already had. 2 new regression tests (real
`createPollingEngine`, not the file's usual fake) — both hand-verified
**killed** by reverting each fix and observing the exact failure signature.
`npx vitest run` 155/155 (153→155), `npx eslint .` clean, `./init.sh` fully
green (795 backend, ruff/mypy/prettier/eslint/vitest). Re-ran
`useWeekPlanner.test.js`/`useLibraryPicker.test.js`/`useLibrary.test.js`/
`useRecipeAuthoring.test.js` alongside the two changed files — 69/69, no
regressions. Full detail: `progress/impl_frontend_spa.md` → "Library slice
— Fix round 3". `feature_list.json` untouched. Still `in_progress`.

## 2026-09-13 — feature 20 `frontend_spa`, library slice fix round 2 (8 findings) — DONE

All 8 reviewer findings fixed: F1 (surviving mutant — ordered, not sorted,
picker-`enabled` assertion), F2 (real pre-existing bug in
`frontend/src/realtime/pollingEngine.js`, feature 26 — `dispose()` gained a
`disposed` flag, `scheduleNext()` now a no-op once set, so an in-flight
request can no longer re-arm a disposed engine; feature 20's `enabled`
toggle just made it reachable), F3 (3 new `usePolling` tests for `enabled`
gating), F4/F5/F7 (spec wording: T30, design.md §5.1, T31 un-ticked to
"Partial"), F6 (3 over-length comments trimmed to the 3-line ceiling), F8
(dead `URLSearchParams` eslint global removed, grep-verified unused).
`npx vitest run` 153/153 (149→153), `npx eslint .` clean, `./init.sh` fully
green (795 backend, ruff/mypy/prettier/eslint/vitest — prettier needed one
`--write` on the new `usePolling.test.js` cases). F1's mutant hand-verified
**killed** (swapped the two `enabled:` expressions, reverted); F2's fix
hand-verified by reverting the `disposed` guard and confirming the new
regression test fails, then restoring. Also noted the `disposed` guard in
`specs/realtime_channel_transport/design.md` next to `createPollingEngine`'s
pseudocode — feature 26's `feature_list.json` status untouched (owner's
call). Full detail: `progress/impl_frontend_spa.md` → "Library slice — Fix
round 2". `feature_list.json` untouched. Still `in_progress` — reviewer
verification next.

## 2026-09-13 — feature 20 `frontend_spa`, library slice fix round 1 (7 findings) — DONE

All 7 reviewer findings fixed: F1 (real bug — filtered-URL poll tore down
`usePolling`'s engine on every keystroke, unmounting the search input;
`useLibraryPicker` now polls the fixed unfiltered URI and filters
client-side), F2 (3 concurrent library polls — `usePolling` gained an
`enabled` gate, `useRecipeAuthoring` enables only the active tab's
picker), F3 (surviving mutant — `ai`'s `canSubmit` test now selects a
reference recipe + notes first), F4 (real bug, data loss — `openEdit`
opened a blank form; `useRecipeAuthoring` now takes `initialRecipe` and
seeds/re-seeds `form` from it), F5 (`library` tab had no submit control),
F6 (`LibraryView` now reuses a new `LibraryFilters.jsx` instead of
duplicating the filter markup), F7 (this file's "17 new `es-ES.js` keys"
corrected to 14). `npx vitest run` 149/149 (135→149), `npx eslint .`
clean, `./init.sh` fully green (795 backend, ruff/mypy/prettier/eslint/
vitest). F3's mutant hand-verified **killed**; F1's fix hand-verified by
reverting to the old poll and confirming the new regression test fails,
then restoring. `specs/frontend_spa/tasks.md` T25 wording corrected;
`design.md` line 293 synced; T23/T27/T28/T29 re-checked, all still
honest. Full detail: `progress/impl_frontend_spa.md` → "Library slice —
Fix round 1". `feature_list.json` untouched. Still `in_progress` —
reviewer verification next.

## 2026-09-13 — feature 20 `frontend_spa`, Library recipe picker + Library view (T25–T31)

**Feature in progress: 20 — frontend_spa (T25–T31 only, per explicit dispatch
scope; Rules/Shopping list/Summary/App shell/Auth sections are separate
implementer runs). Built on the reviewer-approved T1–T24.**

`frontend/src/hooks/useLibraryPicker.js`, `useLibrary.js`;
`frontend/src/components/LibraryRecipePicker.jsx`, `LibraryView.jsx`; 14 new
`es-ES.js` keys (removed the now-dead `RECIPE_AUTHORING_LIBRARY_PENDING`;
corrected from a mis-reported 17 in fix round 1, F7).
`useRecipeAuthoring.js`/`RecipeAuthoringForm.jsx` extended: T27 wires 2 of 3
named `LibraryRecipePicker` call sites (the `library` method tab, replacing
T23's placeholder; the `ai` tab's new reference-recipe field + `notes`) —
`RulesView`'s pin-recipe field waits on T33. 3 new test files + 2 extended
(`useLibraryPicker.test.js`, `useLibrary.test.js`, `LibraryRecipePicker.test.jsx`,
`useRecipeAuthoring.test.js`, `RecipeAuthoringForm.test.jsx`). `npx vitest
run` 135/135 (108→135), `npx eslint .` clean (added `URLSearchParams` to
`frontend/eslint.config.js`'s globals), `./init.sh` fully green (795
backend, ruff/mypy/prettier/eslint/vitest). `tasks.md` T25/T26/T28/T29/T30/T31
ticked, T23 completed (placeholder gone); T27 left "Partial" (2 of 3 sites,
T13/T20/T21/T23 convention); T20/T21 partial notes extended to 3 of 4
`openDetail` call sites (`LibraryView` now wired, `SummaryView` remains).
Full traceability, design decisions and the T27/T20/T21 notes:
`progress/impl_frontend_spa.md` → "Library recipe picker + Library view
(T25–T31)". `feature_list.json` untouched. Status left `in_progress` —
reviewer next.

## 2026-09-13 — feature 20 `frontend_spa`, shared authoring flow (T22–T24)

**Feature in progress: 20 — frontend_spa (T22–T24 only, per explicit dispatch
scope; Library recipe picker/Rules/Shopping list/Summary/App shell/Auth
sections are separate implementer runs). Built on the reviewer-approved
T1–T21.**

`frontend/src/hooks/useRecipeAuthoring.js`, `frontend/src/components/
RecipeAuthoringForm.jsx`, 23 new `es-ES.js` keys. 2 new test files
(`useRecipeAuthoring.test.js`, `RecipeAuthoringForm.test.jsx`). `npx vitest
run` 107/107 (90→107), `npx eslint .` clean, `./init.sh` fully green (795
backend, ruff/mypy/prettier/eslint/vitest — also reformatted a pre-existing,
whitespace-only drift in `WeekPlannerView.jsx` unrelated to this slice's
logic, since `prettier --check` runs project-wide). `tasks.md` T22/T24
ticked; T23 left "Partial" (same convention as T13/T20/T21) — the `library`
tab renders a deferred placeholder, `LibraryRecipePicker` lands with T25/T26.
Full traceability, deviations and the T23 limitation:
`progress/impl_frontend_spa.md` → "The shared authoring flow (T22–T24)".
`feature_list.json` untouched. Status left `in_progress` — reviewer next.

## 2026-09-13 — feature 20 fix round 1, remaining half of finding 3 — DONE

`error`/`detailError` now render, not just get caught. `WeekPlannerView.jsx`
shows `error` as a plain `<p>`; mounts `RecipeDetailView` on
`detail || detailError` (was `detail` alone). `RecipeDetailView.jsx` gains
an `error` prop: recipe-less + error renders the close button + error text
instead of `null`. No new color token (reuses `tokens.color.ink`). 3 new
tests (1 `RecipeDetailView.test.jsx`, 2 `WeekPlannerView.test.jsx`) — 93/93
vitest, eslint clean. Detail: `progress/impl_frontend_spa.md` → "Fix round
1", item 3. `feature_list.json` untouched. Still `in_progress` — reviewer
next.

## 2026-09-13 — feature 20 fix round 1 (Week planner + Recipe detail, 4 findings) — DONE

All 4 reviewer findings fixed: `applyMutationMarker` mutant tests (both
`promoteDefinitive`/`clearDefinitive`), `useRecipeDetail` dep-array
regression test, `ApiError`-catch + `error` field at all 4 call sites
(new `error: string | null` shape — the baseline for later sections),
2 over-length comments cut to 3 lines. `npx vitest run` 90/90 (84→90),
`./init.sh` fully green (795 backend, ruff/mypy/prettier/eslint/vitest).
Both named mutants (marker-call deletion, dep-array revert to `[source]`)
re-applied by hand and confirmed **KILL**. Full detail:
`progress/impl_frontend_spa.md` → "Fix round 1". `feature_list.json`
untouched. Status still `in_progress` — reviewer verification next.

## 2026-09-14 — feature 20 `frontend_spa`, Library slice (T25–T31) closed after 4 fix rounds

Reviewer found real bugs, not just gaps: filtered-URL polling broke the
search box's focus every keystroke (contract said unfiltered poll + client
filter — fixed); editing a library recipe opened an empty form, so saving
silently wiped ingredients/tools/procedure (fixed, now pre-fills + tested
round-trip); the `library` authoring method had no submit control (added);
a genuine pre-existing bug in feature 26's `pollingEngine.js` (disposed
engines could re-arm) surfaced through this feature's new `enabled` toggle
— fixed inline (reviewer confirmed this was the right call), but the fix
itself briefly regressed polling dead after a tab-switch cycle (round 3
fixed with a `generation`-based cache-busting key, mutation-verified).
Final state: 155/155 vitest, `./init.sh` green, reviewer APPROVED after
round 4's comment trims. Full detail: `progress/impl_frontend_spa.md` →
"Library recipe picker + Library view" + its 4 fix-round subsections.

**Flagged for the owner, not resolved:** the library-recipe delete's
`409 PIN_RULES_AFFECTED` → `?confirmCascade=true` retry
(`rest_api_contract.md` §3.4) isn't planned in any task, present or
future — either it becomes a Rules-section task or is ruled explicitly
out of feature 20's scope.

## 2026-09-13 — feature 20 `frontend_spa`, Week planner + Recipe detail (T14–T21)

**Feature in progress: 20 — frontend_spa (T14–T21 only, per explicit dispatch
scope; authoring flow/Library/Rules/Shopping list/Summary/App shell/Auth
sections are separate implementer runs). Built on the reviewer-approved
T1–T13 shared infrastructure.**

`frontend/src/hooks/useWeekPlanner.js`, `useRecipeDetail.js`;
`frontend/src/components/WeekSwitcher.jsx`, `WeekPlannerView.jsx`,
`DaySlot.jsx`, `MealCard.jsx`, `RecipeDetailView.jsx`; 13 new `es-ES.js`
keys; `frontend/src/api/client.js` gained an additive `onHeaders` option
(needed to read a mutation's `ETag` for `usePolling`'s
`applyMutationMarker`, design.md §4.2 — backward compatible, no existing
caller/test broken). 4 new test files + 1 extended. `./init.sh` green — 795
backend tests (unchanged), vitest 84/84 (19 files), ruff/mypy/prettier/
eslint all pass. `tasks.md` T14–T19 ticked; T20/T21 left "Partial" (2 of
4 `openDetail` call sites — `SummaryView`/`LibraryView` don't exist yet,
per explicit dispatch scope). Full traceability, deviations and the T20/T21
limitation: `progress/impl_frontend_spa.md` → "Week planner + Recipe detail
(T14–T21)". Status left `in_progress` — reviewer next.

**Bug found and fixed while implementing (own code, this session):**
`useRecipeDetail`'s effect depended on the `source` object's own *identity*,
not its fields; a caller passing a fresh object literal each render (every
call site here does) re-ran the effect every render, called `setState`, and
looped — reproduced as a real `JS heap out of memory` crash under `vitest`.
Fixed by depending on `source`'s primitive fields instead. Also hit and
fixed `eslint-plugin-react-hooks`'s `set-state-in-effect` rule (already
enabled project-wide, not new) by deriving `isLoading` from a
request-keyed comparison instead of a second `setState` call in the effect
body.

## 2026-09-13 — feature 20 `frontend_spa`, shared infrastructure slice (T1–T13)

**Feature in progress: 20 — frontend_spa (T1–T13 only, per explicit dispatch
scope; Week planner/Recipe detail/etc. sections are separate implementer
runs).**

`frontend/src/api/client.js` (`ApiError`, `apiFetch`), `frontend/src/domain/
labels.js` + `wireCodes.js` (mirrors `backend/core/.../units.py` /
`ingredient_category.py` verbatim), `frontend/src/hooks/useBreakpoint.js` +
`useConfirm.js`, `frontend/src/components/ConfirmDialog.jsx` /
`EmptyState.jsx` / `LoadingState.jsx` / `WeekLabel.jsx`, plus 6 new
`es-ES.js` keys. One test file per source file, all passing (60/60 vitest).

**Bug found and fixed in `frontend/eslint.config.js`:** my first attempt to
disable `react/prop-types` (no TS, no `prop-types` dep — architecture.md
§1.1) added a second `rules:` key in the same object literal alongside
`...react.configs.flat.recommended`'s spread — that **replaced**, not
merged, the spread's 22 rules (JS object-literal semantics: last key wins).
Silently dropped `react/jsx-uses-vars`, which broke `no-unused-vars` for
every file using a component only inside JSX — including pre-existing
`src/main.jsx` and `tests/PlaceholderView.test.jsx`, unrelated to this
feature. Fixed by spreading `react.configs.flat.recommended.rules` into the
`rules:` object instead of replacing it. `./init.sh` green after the fix —
795 backend tests, vitest 60/60 (15 files), ruff/mypy/prettier/eslint all
pass. `tasks.md` T1–T13 ticked. Full traceability:
`progress/impl_frontend_spa.md`. Status left `in_progress` — reviewer next.

**Reviewer — CHANGES_REQUESTED (2 findings, 1 mutant survived).** FR/R
coverage and mutation testing otherwise clean (6/7 mutants killed); both
implementer-documented deviations (`ApiError.detail`, `apiFetch`'s
`NETWORK_ERROR` catch) and the eslint fix judged correct. Required:
1. `labels.test.js`'s `UNIT_LABELS`/`CATEGORY_LABELS` loop tests only
   asserted `typeof`/`length`, so a renamed label value survived
   mutation (`meat: 'Carne'` → `'Pescado'`, 5/5 still green). 2. T13 was
   ticked done but only 6 of the feature's eventual message keys exist —
   every later section adds its own; reads as complete to the next
   implementer otherwise.

**Fix round — DONE.** Added `toEqual` exact-value assertions for both
label maps (pinned against design.md §6), mutant re-applied and
**killed**, `labels.js` reverted, suite green. T13 un-ticked in
`tasks.md` with a note that it stays open across the whole feature.
Cheap verification only (no second full review) per protocol.

**Shared-infrastructure slice (T1–T13) closed out.** Next: Week planner
(T14–T17) + Recipe detail (T18–T21) dispatched to a new implementer —
T20's `SummaryView`/`LibraryView` wiring explicitly deferred to those
sections' own runs (they don't exist yet).

## 2026-09-12 — feature 26 fix round 1 (reviewer CHANGES_REQUESTED, 2 findings)

Both required findings fixed. **M-A** — the 4 pollable-route 304 tests in
`test_handler.py` (weeks/library/rules/shopping) never bumped their marker
off `0`, so a reader wired to a constant was indistinguishable from a
correct one; rewrote each to write first, then assert `304` on the new
marker and `200` (full payload) on the stale `"0"`. This surfaced a real
bug — `library_editing.py::poll_marker` returned literal `0`, never
`recipes.current_version()` — now fixed. Both named mutants (`week_editing.
poll_marker` / `library_editing.poll_marker` → `return 0`) re-verified
**killed**. **M-B** — `usePolling.test.js` never exercised the hook's
`blur`/`focus` DOM wiring (only `visibilitychange`); added a case for both.
The named mutant (deleting the `blur`/`focus` listener pair) re-verified
**killed**. Bookkeeping: `impl_realtime_channel_transport.md`'s vitest count
corrected to the real 35→36 (was mis-reported as 29/4 files). `./init.sh`
green — 795 backend tests, vitest 36/7 files. No `feature_list.json`
change, no commit. Full detail: `progress/impl_realtime_channel_transport.md`
→ "Fix round 1 — 2026-09-12".

## 2026-09-12 — feature 26 gate closed; data-loss incident on this file

**Incident (disclosed):** an implementer session accidentally overwrote this
file's uncommitted content with a placeholder before reading it. That content
had shown as `M` in git status (uncommitted, never staged), so git holds no
blob of it and it is **not recoverable**. This file has been restored to the
last committed (`HEAD`) state below; whatever session notes existed between
that commit and this incident are lost. No spec, task, or source file was
affected.

**Feature 26 `realtime_channel_transport` gate (T25) closed.** Code and
backend tests already existed and were green from an earlier, unfinished
session; only the SDD bookkeeping and the frontend lint/format gate were
open. Fixed: `frontend/eslint.config.js` was missing `fetch`/`Event` in its
`globals` (feature's browser code legitimately uses both); removed a stale
`eslint-disable-next-line react-hooks/exhaustive-deps` in
`src/hooks/usePolling.js` whose dep array is already exhaustive; ran
`prettier --write` on the 6 flagged files. Verified all of T1–T25
(incl. T24a/T24b) against real code/tests and checked them off in
`specs/realtime_channel_transport/tasks.md`. `./init.sh` green — **795
backend tests**, vitest 29/29, ruff/mypy/prettier/eslint all pass. Full
traceability in `progress/impl_realtime_channel_transport.md`. Status left at
`in_progress` — `done` and commit are the owner's alone; ready for reviewer.

## 2026-09-12 — reconstructed: feature 26 spec'd + gate ruled (lost entry)

> Recovered from this conversation's own transcript (I read the original
> entry verbatim before the incident above destroyed it) — not from git,
> which held no blob of the uncommitted text. Reproduced as closely as
> memory allows; treat as best-effort, not a byte-exact restore.

`./init.sh` green (774 tests) at session start; feature 24's English-prompt
fix cycle already committed by owner (`fcbb6a4`). Next actionable: **26
`realtime_channel_transport`** (deps 16+18 both `done`).

`spec_author` produced `specs/realtime_channel_transport/` (R1–R26,
design.md, tasks.md T1–T25), `feature_list.json` 26 `pending -> spec_ready`.
3 gate questions:

1. Re-sync single-bump timing (same `TransactWriteItems` as the batched
   writes, just before `release_lock`, not folded into the lock's own
   delete) — **owner: OK**.
2. Polling constants (5s active / 30s background / 60s backoff cap / ±20%
   jitter / 3-failure threshold) — **owner: OK**.
3. Frontend test strategy — spec_author proposed a framework-free
   `pollingEngine.js` + inert `usePolling.js` hook (no new deps, since
   `vite.config.js` runs Vitest `environment: "node"`). **Owner reversed:**
   add `jsdom` + `@testing-library/react` and test `usePolling.js`'s real
   React wiring too.

Fold pass done: design.md §0/§2/§5/§7/§9 updated, tasks.md gained T24a (add
`jsdom`/`@testing-library/react`/`@testing-library/dom` devDeps) + T24b
(`usePolling.test.js`, per-file `// @vitest-environment jsdom` pragma —
confirmed supported by installed `vitest@^4.1.10`, project-wide config
untouched). `requirements.md` needed no change. `feature_list.json` still
`spec_ready` (fold pass doesn't flip status).

Owner then said "go" (off-session from this reconstruction's view) —
leader flipped feature 26 `spec_ready -> in_progress` and dispatched the
`implementer`, which produced all the code/tests now closed out above.

## 2026-09-11 — feature 17/27 committed; correction reopens feature 24

Owner committed the bundle as `1944822 feat: ai generation lambda`;
feature 16, 17, 27 all `done`. Tree clean.

**Owner correction:** AI generation prompts sent to Bedrock should be in
**English**, not Spanish — more token-efficient. Scope check: FR-AI-07
governs the model's OUTPUT language only (`OUTPUT_LANGUAGE = "es-ES"`
untouched); this is instruction wording only, not user-facing text
(`rest_api_contract.md` §3.0's wire-vs-UI-string boundary applies — an
internal Bedrock payload isn't user-facing, so English is not an
es-ES-policy violation). Category/unit *values* interpolated into the
prompt (`IngredientCategory`/`Unit`) stay Spanish — fixed domain
vocabulary, a different concern.

No new requirement needed: feature 24 `ai_prompt_versioning`'s own R1/R2/R6
(distinct immutable versions, all retained, all retrievable by id) already
specify exactly this operation. **No `spec_author` round** — reopened
feature 24 (`done -> in_progress`) directly to `implementer`: add
`PROMPT_INSTRUCTION_VERSIONS["v2"]` in English, `"v1"` (Spanish) retained
untouched per the append-only design. Also updates
`backend/lambda_ai/tests/test_bedrock.py` (v2 render case) and feature
25's `test_no_recipe_metadata_logic.py` sanctioned-line exemption (v2's
JSON-instruction mentions of servings/estimated_time need the same
allowlist entry v1's has). `bedrock.py` itself needs no code change — it's
already a pure version-agnostic assembler (this session's earlier F6).

**Implementer done.** `./init.sh` green — **773 passed** (+4). Only
feature 24's status changed in `feature_list.json` (mine, no drift).
`progress/impl_ai_prompt_versioning.md` got a full retroactive report
(this feature had none — pre-dates the report convention) plus the new
"v2 (English)" section. `v1` diff is purely additive (8 new `_V2`
constants + registry entry); `output_language` stays `"es-ES"` for both
versions. Own mutation probe caught a self-comparison test that didn't
actually verify content, fixed with a literal-content assertion.

**`reviewer` launched** for the delta (v1-untouched guarantee, v2
content real, `output_language` still es-ES, the feature-25 guard's new
exemption narrow, `conventions.md` language-policy read).

**Reviewer run — CHANGES_REQUESTED.** 1 finding, 1 mutant survived:
`RECIPE_METADATA_INSTRUCTION_V2` had no literal-content test (every v2
assertion on it was a self-comparison) — blank it to `""` and the whole
suite stayed green, meaning v2 could ship with no instruction telling
the model to state diners/prep-time and nothing would notice. 2
non-blocking notes: stale "Spanish" wording in a `bedrock.py` comment
(v2 is English now); v1/v2 template fields have no literal tests either
(pre-existing from feature 11, not required).

**Fix round — DONE.** Added the missing literal-content test (mirrors
the one for `HEALTHY_BALANCED_INSTRUCTION_V2`) + reworded the stale
comment. `./init.sh` green, 774 tests. No `feature_list.json` drift.

**Verification — APPROVED.** 0 findings, 0 mutants survived. Mutant
re-applied and killed (`AssertionError: '' == 'Also state t...'`), tree
restored (sha256-verified byte-identical), comment confirmed
language-neutral and accurate. `./init.sh` green — 774 passed.

**Feature 24's v2 (English prompt wording) reopen is complete and
reviewer-APPROVED.**

## Next step — OWNER

1. **Commit** — 8 changed files: `domain/ai_prompt.py`,
   `test_ai_prompt.py`, `test_no_recipe_metadata_logic.py`,
   `test_bedrock.py`, `bedrock.py` (comment only),
   `impl_ai_prompt_versioning.md`, `feature_list.json`. Small enough for
   one commit, e.g. `feat: version ai generation prompts in english`.
2. **Status:** feature 24 `in_progress -> done` (re-close). Yours alone.
3. **Deployment note for later:** activating v2 is a `ConfigPort`
   (`AI_PROMPT_VERSION_ID`) value — feature 21 IaC / deploy config, not
   code. Nothing in the tree defaults to a version id.

## 2026-09-11 — implementer DONE, awaiting reviewer

`domain/ai_prompt.py` gained 8 `_V2` constants (English translations of v1's
wording) + `PROMPT_INSTRUCTION_VERSIONS["v2"]` (`output_language=OUTPUT_LANGUAGE`,
same es-ES value as v1). No `OUTPUT_LANGUAGE_V2` — only the template's label
wording is English, the substituted value is unchanged. `v1` untouched (purely
additive diff). `bedrock.py::_render` needed no change — already version-agnostic.

Tests: `test_ai_prompt.py` (+3, registry set `{"v1","v2"}` + literal-content v2
test + `build_instructions("v2")` test), `test_bedrock.py` (+1, v2-parallel F5
render case, English wording), `test_no_recipe_metadata_logic.py` (feature 25
guard — 2 new sanctioned-line patterns for `JSON_OUTPUT_INSTRUCTION_V2`'s
English `servings`/`estimated_time` JSON-key mentions; `RECIPE_METADATA_INSTRUCTION_V2`
worded "diners" instead of "servings" so it needs no exemption, mirroring v1's
Spanish wording choice).

Mutation probe: blanked `HEALTHY_BALANCED_INSTRUCTION_V2`. First attempt (a
registry-value self-comparison) did NOT catch it — added a literal-content
assertion instead (mirrors v1's own pattern), which did. Reverted, byte-identical.

`./init.sh` green — **773 passed** (769 → 773). Report:
`progress/impl_ai_prompt_versioning.md` → "v2 (English) prompt wording —
2026-09-11". No `feature_list.json` change, no commit. Cheap `reviewer`
verification follows automatically.

### Log

- **Feature in progress:** 17 `ai_lambda` — SDD spec phase
- **Started:** 2026-09-06
- **Agent:** `spec_author` launching on a new `specs/ai_lambda/`

## 2026-09-06 — feature 16 closed by owner, feature 17 opened

Owner committed the reopen round (`a805aa5 feat: main lambda api`,
`9b428a5 chore: mark feature as done`) and flipped feature 16 -> `done`
plus feature 27 back to `done`. Tree clean. `./init.sh` green — 27
features, 20 done, 3 pending (17, 20, 26), 4 blocked, 694 tests.

`./init.sh` reports **feature 17 `ai_lambda`** as the next actionable
feature (`depends_on: [12, 14]`, both `done`). Status `pending` -> SDD
Case A: launch one `spec_author`, then stop at the human approval gate.

### Scope of feature 17

The `ai` Lambda worker shell: SQS consumer + AWS Bedrock provider adapter
+ cost-cap kill-switch (`NFR-AI-01`) + per-slot concurrency (`FR-AI-09`)
+ idempotent invocation + writing whole-week results through
`WeekRepository` (`G-88`). The generation *domain* logic already lives in
`planner_core` (features 10/11/12/24/25). Mirrors feature 16's
shell-vs-core split. `covers` = `{FR-AI-09, NFR-AI-01}` only.

### Log

- 2026-09-06 — Launched `spec_author` for feature 17 `ai_lambda`.
- 2026-09-06 — `spec_author` returned `spec_ready -> specs/ai_lambda/`
  (20 EARS reqs, `./init.sh` green, 694 tests) with 8 gate questions.

### Gate ruling — in progress (2026-09-06)

- **Q2 (attempt ordinal) — RULED.** Feature 17 does not implement
  `attempt`; it is a single-recipe-regenerate concern. Owner: don't leave
  it hanging, but not by reopening 3 `done` features + a frozen-contract
  edit. **New feature 28 `single_recipe_generation`** added (`pending`,
  tier 3, `depends_on: [11, 12, 16, 17]`, `covers: []`). Owns the
  single-recipe `POST /v1/generations` body, the server-authoritative
  `attempt` fold, and the `ai` worker's single-recipe branch. Its first
  acceptance item is an owner-owned `rest_api_contract.md` lift (§3.5/§7
  document only `type:"week"` today). `./init.sh` green, 28 features,
  next actionable unchanged (26).
- **Q5 (Bedrock SDK) — RULED.** `boto3` (+ `moto` dev dep),
  `lambda_ai/pyproject.toml` only.
- **Q6 (model id) — RULED.** `BEDROCK_MODEL_ID = "anthropic.claude-sonnet-5"`
  module constant, `AI_MODEL_ID` env override.
- **Q7 (partial-failure surface) — RULED.** Worker writes `resultado` as
  `[{day, slot, status, message}]`, passed through verbatim; per-slot
  retry is client-side (feature 28 / frontend).
- **Q1 (cost-cap gate) — RULED.** `GenerationGate` port
  (`is_generation_enabled() -> bool`) + **SSM Parameter Store** adapter
  (`/planner/<env>/ai-generation-enabled`, ~5s TTL). Budget / Budget
  action / reserved-concurrency-0 / ESM-disable / SNS->Lambda flip = all
  feature 21 IaC, second layer. No data-model change.
- **Q3 (per-slot 409) — RULED.** Downgrade the whole-week
  `POST /v1/generations` 409 to **exact-hash-resubmit dedupe only**
  (`attribute_not_exists(PK)` already delivers it). Concurrent different
  whole-week runs allowed (FR-AI-11 additive + at-write definitive
  re-check). Deliberate deviation from `rest_api_contract.md` §3.5 /
  line 171 — owner reconciles the contract doc. True per-slot 409 -> f28.
- **Q4 (write-back port) — RULED.** `GenerationQueue` gains
  `claim(key) -> bool` (conditional `pending->running`, idempotent-
  invocation guard) + `record_result(key, status, per_slot) -> None`.
  **Feature 27 delta** (same pattern as the R31 `discard` reopen).
  Fake + `SqsGenerationQueue` + a new `planner_ai` adapter. Owner flips
  27 `done -> in_progress` when the implementer round starts.
- **Q8a (adapter copy) — RULED.** `planner_ai/adapters/` gets its own
  copy of `weeks.py` + `_table.py` + `_meal.py`; `test_week_repository_
  contract.py` parametrized over BOTH adapters so drift fails a test.
  No `architecture.md` edit, no shared workspace member.
- **Q8b (message enrichment) — RULED.** `GenerationQueue.submit`'s SQS
  message gains the resolved effective rules + prompt version id (api
  already computes them for the 202 body). Worker reads inputs from the
  message — no `RuleRepository` copy, no mid-generation TOCTOU
  (FR-AI-05). **Feature 27 delta** (the `submit` message payload).

### spec_author fold pass — done + one more delta (2026-09-06)

Round 1: all 8 rulings folded into `specs/ai_lambda/`; feature-27 delta
R36–R40 (Q4 `claim`/`record_result` + Q8b message enrichment), design
§3b/§6/§8/§9, tasks T34–T40. `./init.sh` green, 694 tests.

**New ambiguity the fold surfaced — pinned-slot candidate writing
(FR-AI-11).** Nothing writes the pinned-library-meal candidates for
pinned slots today; the worker is `open_slots`-only. **Owner ruled:**
api-synchronous, **feature-27 delta.** `generation_submission` grows a
`recipes: RecipeRepository` param + a user-id param and writes pinned
candidates on the fresh-submit path (reusing `new_candidate` /
`add_slot_candidate`). `FR-AI-11` cited-not-owned (feature 10). Accepted
edge: resubmit-after-partial-failure can double-write pinned candidates
(additive, consistent with Q3). Round 2 dispatched to `spec_author`
(R41…, T41…).

### spec_author fold — COMPLETE, one overstep corrected (2026-09-06)

Round 2 done. Final spec state:

- **`specs/ai_lambda/`** — R1–R21 (R21 = `FR-CAND-04` consumed-not-owned,
  candidate authorship). design §0–§12: SSM `GenerationGate`, the feature-27
  reopen surface, adapter copy + mandatory dual-adapter `WeekRepository`
  contract suite, message enrichment (+`authorUserId`), §9.1 the 409
  downgrade deviation, §10 fixed values, §11 three rejected alternatives.
  New ports `ai_provider.py` + `generation_gate.py`, new use case
  `application/week_generation.py`, the whole `planner_ai` shell.
- **`specs/rest_api_persistence_and_services/`** — delta R36–R43,
  T34–T43 (unchecked), design §2/§3b/§3c/§6/§8/§9. R36–R39 `claim` +
  `record_result`; R40 message enrichment; R41–R43 synchronous
  pinned-slot candidate writes (R43: idempotent-hit writes nothing).
  `covers` unchanged; `FR-AI-11`/`FR-CAND-04` added consumed-not-owned.

**Overstep:** the `spec_author` flipped feature 27 `done -> in_progress`
in `feature_list.json` (misattributed to the leader in its result). No
implementer is running; the spec is not approved; the owner reserved
that flip. **Leader reverted 27 -> `done`.** `./init.sh` green again —
694 tests, 28 features, next actionable 26. Feature 17 stays
`spec_ready` (the `spec_author`'s legitimate flip). Feature 28
untouched.

## 2026-09-06 — spec APPROVED, bundled implementer launched

Owner approved ("go"). Owner flipped feature 27 `done -> in_progress`;
leader flipped feature 17 `spec_ready -> in_progress`. Both `in_progress`
for the bundle — `./init.sh` §4 will flag the dual `in_progress` + the
16->27 dep order, inherent to the bundle (same as the 16+27 reopen),
resolves on the owner's `done` marks.

**One `implementer` launched** for both, in order:
1. Feature 27 delta — `specs/rest_api_persistence_and_services/tasks.md`
   T34–T43 (port `claim`/`record_result`, SQS adapter, `submit` message
   enrichment, `generation_submission` pinned-slot writes + `recipes`/
   `author` params, `routing.py` caller).
2. Feature 17 — `specs/ai_lambda/tasks.md` T1–T24 (ports `ai_provider` +
   `generation_gate`, `application/week_generation.py`, the `planner_ai`
   shell: bedrock/ssm/dynamo adapters, wiring, handler; dual-adapter
   `WeekRepository` contract suite).

Reports: `progress/impl_rest_api_persistence_and_services.md` ->
"Reopen round 2 2026-09-06", `progress/impl_rest_api_lambda.md` ->
"Feature 17 2026-09-06". `reviewer` launches automatically after.

## 2026-09-06 — implementer running (bundle)

- **Feature in progress:** 27 delta (T34–T43) then 17 (T1–T24)
- **Plan (27):** tasks T34–T43 from
  `specs/rest_api_persistence_and_services/tasks.md`
- **Plan (17):** tasks T1–T24 from `specs/ai_lambda/tasks.md`
- Decision: `GenerationQueue.submit` gains keyword-only params
  `effective_rules` / `prompt_version_id` / `author` (defaulted so existing
  call sites stay green) — the design's "serialisation change" needs the
  values at the producer, and `submit_generation` is its only caller.
  `submit_generation` gains `prompt_version_id: str` too (T41 under-specified
  the routing caller; routing resolves it via `resolve_active_prompt_version`).

## 2026-09-06 — implementer DONE (bundle), awaiting reviewer

Both features implemented in one run.

- **Feature 27 delta** — T34–T43 ticked. `GenerationQueue` port grew
  `claim` / `record_result` (+ a `GenerationResultSink` base Protocol) and
  `submit` grew defaulted `effective_rules` / `prompt_version_id` / `author`
  kwargs; `SqsGenerationQueue` claim/record_result + enriched message body;
  `generation_submission` writes pinned-slot candidates on the fresh path +
  takes `recipes` / `author` / `prompt_version_id`; `routing._submit_generation`
  wires them (prompt id via `deps.config.get(PROMPT_VERSION_CONFIG_KEY)` —
  raw, worker validates). Report: `progress/impl_rest_api_persistence_and_services.md`
  → "Reopen round 2".
- **Feature 17 `ai_lambda`** — T1–T24 ticked. New ports `ai_provider` /
  `generation_gate`; use case `application/week_generation.py`; the whole
  `planner_ai` shell (dynamo copy + `generations.py`, `bedrock.py`, `ssm.py`,
  `message.py`, `wiring.py`, `handler.py`). Dual-adapter `WeekRepository`
  contract suite (T21). Report: **`progress/impl_ai_lambda.md`** (new file;
  the dispatch note said `impl_rest_api_lambda.md` but protocol is
  `impl_<spec-dir>.md`).

`./init.sh`: §5 fully green (762 passed, ruff/mypy/prettier/eslint/vitest).
§4 red only on the intentional dual `in_progress` (17 + 27) + the 16→27
dep-order check — clears on the owner's `done` marks.

## Implementer run — bundled (2026-09-06) — DONE

Both parts implemented in one run. `./init.sh` §5 green — **762 passed**
(+68). §4 fails only on the intentional dual `in_progress` (17 + 27) +
16->27 dep order. All T34–T43 + T1–T24 ticked. `feature_list.json` diff
is +21/-2 (the two status flips + feature 28 only — no implementer
meddling).

Implementer-flagged deviations (all in the reports):
1. `submit` gained defaulted enrichment kwargs (producer needs the values).
2. `prompt_version_id` reaches `submit_generation` from `routing` via raw
   config read (T41 under-specified it).
3. A `GenerationResultSink` base Protocol was split out so `planner_ai`
   need not implement `submit` — **note: design §11 rejected a write-only
   sink port**; reviewer to judge whether this crosses that line.
4. Bedrock `AiProvider` contract case uses a stubbed client, not moto.

Report filename: feature 17's is `progress/impl_ai_lambda.md` (not
`impl_rest_api_lambda.md` — that's feature 16's; dispatch note was wrong,
implementer corrected it).

## Reviewer run — bundled — DISPATCHED (2026-09-06)

Launched with tree-safety warning (uncommitted feature — file-copy backup
only, never git checkout/restore/stash). Briefed to scrutinise the 4
deviations (esp. #3 vs design §11), spec drift, G-88 scan teeth, the T21
dual-adapter contract suite, and the `claim`/`record_result` alias +
condition mutants.

## Reviewer run — bundled — CHANGES_REQUESTED (2026-09-06)

7 findings, **4 mutants survived**. FR->R coverage complete; tasks all
`[x]`; boundaries clean; `core` stdlib-only; the 4 implementer deviations
judged (deviation #3 `GenerationResultSink` split **ACCEPTED** — one
module, `GenerationQueue` still extends it, contract suite covers all
impls; #1 partially rejected -> finding 1; #3 prompt-version -> finding 2;
#4 stub accepted for the parse half). Tree restored byte-identical, all
by file copy.

**Required (fix round):**
1. **`message.py` + `submit` enrichment defaults — un-enriched message
   generates silently.** `_parse_rules(body.get("effectiveRules"))` turns
   missing/null into an empty `RuleSet`; combined with
   `effective_rules: RuleSet | None = None` on the port + adapter, a
   message that lost enrichment generates ignoring the user's confirmed
   category counts / pins / disabled days, then records `completed` —
   exactly what R40 exists to prevent. Make `effectiveRules` required
   like `promptVersionId`/`authorUserId`; add the test. (`ports/
   generation_queue.py:72`, `adapters/sqs.py:89`, `planner_ai/message.py:80`)
2. **`routing.py:737` bypasses feature 24.** `prompt_version_id =
   deps.config.get(PROMPT_VERSION_CONFIG_KEY)` duplicates
   `application/prompt_version.py::resolve_active_prompt_version` and
   drops its `UnknownPromptVersion` guard — unset/unknown key -> `202`,
   enqueues `promptVersionId: null`, worker fails *after* claiming (every
   slot lost). Also config resolution in the thin handler
   (`conventions.md` Packaging). Route through feature 24's use case.
3. **R8/R10 have no real test** (2 surviving mutants,
   `week_generation.py:106-107`). The only test seeds the definitive
   *before* the run so `resolve_targets` filters the slot and the
   at-write branch never runs. Add: a definitive promoted *between*
   `resolve_targets` and the write (`WeekRepository` whose 2nd
   `get_week` returns a now-definitive slot).
4. **T21 dual-adapter contract suite is vacuous** (owner-mandated).
   Parametrizes over the `planner_ai` copy but every case writes+reads
   the *same* adapter, so cross-copy key/attr drift is invisible
   (`SEMANA#...#drift` -> 18 passed). Add a cross-copy case: write with
   `planner_api`'s adapter, read with `planner_ai`'s, and back.
5. **`_render` uncovered (T15/R2 surviving mutant** — `_render` -> `""`,
   8 passed). Both `AiProvider` contract stubs discard `body`. Assert the
   rendered body carries `healthy_balanced_instruction`,
   `recipe_metadata_instruction`, `output_language`, the allowed-unit
   list and the category counts.
6. **Un-versioned prompt wording in `bedrock.py`** (`_JSON_INSTRUCTION`,
   "Genera una receta para un hueco abierto…", "Idioma de salida: …",
   "Unidades permitidas: …") — new Spanish prompt semantics outside
   `PROMPT_INSTRUCTION_VERSIONS` (feature 24's append-only registry,
   FR-AI-14/G-84). Editing them changes every prompt with no version
   bump. **OWNER CALL:** fold the render template into the versioned
   block, or rule adapter serialisation wording out of FR-AI-14 scope.
7. **Minor / leader-folds:** `specs/rest_api_persistence_and_services/
   design.md` §3c's `submit_generation` signature omits the
   `prompt_version_id` param the code added.

**Finding 6 — OWNER RULED: yes**, fold the render template into the
versioned block (`PromptInstructionsVersion` gains the JSON-output
instruction + per-mode framing; `v1` populated with the current strings;
`bedrock.py::_render` becomes a pure assembler, zero Spanish literals).
Cited `FR-AI-14` consumed-not-owned (feature 24).

## Fix round 1 — dispatched (2026-09-06)

One `implementer` for findings 1–6 + the finding-7 doc sync
(`submit_generation` signature after finding 2 moves prompt-version
resolution into the application layer via `config: ConfigPort` +
`resolve_active_prompt_version`). Reports append "Fix round 1" to both
impl files. Cheap `reviewer` verification follows.

## Fix round 1 — implementer DONE (2026-09-06)

All 6 findings + the finding-7 doc sync landed. `./init.sh` §5 green —
**769 passed** (762 → 769). §4 still red only on the intentional dual
`in_progress` (17 + 27) + the 16→27 dep order — unchanged, clears on the
owner's `done` marks. No `feature_list.json` status change, no commit.

- **F1** — `effectiveRules` now required on the SQS message parse
  (`message.py` `_require`); `submit`'s `effective_rules` lost its
  `| None = None` default (port + SQS adapter + fake). Un-enriched message
  → parse raises, worker never calls the provider.
- **F2** — `generation_submission` takes `config: ConfigPort` and resolves
  the prompt version through feature 24's `resolve_active_prompt_version`
  **before any write**; unset/unknown key → `UnknownPromptVersion` →
  `422 UNKNOWN_PROMPT_VERSION` (new `errors.py` mapping + `messages.py`
  constant). `routing.py` no longer reads config.
- **F3** — new `test_week_generation.py` test: a definitive promoted
  *between* `resolve_targets` and the write; kills both `:106-107` mutants.
- **F4** — new cross-copy case in `test_week_repository_contract.py`:
  write with `planner_api`'s adapter, read with `planner_ai`'s, and back.
  Proven vacuous-before: `SEMANA#…#drift` → 18 same-adapter cases pass, the
  cross-copy case fails.
- **F5** — new `test_bedrock.py` test asserts `_render`'s output carries
  the version wording + unit list + category counts; `_render` → `""` fails.
- **F6 (OWNER RULED yes)** — `_JSON_INSTRUCTION` + the framing/label prose
  moved into `domain/ai_prompt.py`'s `PromptInstructionsVersion` (`v1`
  populated **verbatim**, append-only intact). `bedrock.py::_render` is a
  pure `string.Template` assembler, zero Spanish literals. Cited **FR-AI-14
  consumed-not-owned** — NOT added to feature 17's or 27's `covers`.
  Feature 24 field-shape tests extended (green). `test_no_recipe_metadata_
  logic.py` gained a narrow sanctioned-line exemption for
  `JSON_OUTPUT_INSTRUCTION` (mirrors `CANDIDATE_SANCTIONED_LINES`) +
  verbatim guard — flagged for the owner re: the feature 25 spec doc.
- **F7** — `specs/rest_api_persistence_and_services/design.md` §2 + §3c
  synced to the `config: ConfigPort` signature.

Reports: `progress/impl_ai_lambda.md` + `progress/impl_rest_api_persistence_and_services.md`
→ "Fix round 1 — 2026-09-06". 5 mutation probes (F1, F3, F4, F5, F6) all
killed by the new tests, reverted by hand (file edits, no git).

## Fix round 1 — DONE (2026-09-06)

`./init.sh` §5 green — **769 passed** (762 -> 769). All 5 mutation probes
(F1/F3/F4/F5/F6) planted + killed by new tests, reverted by hand. No
`feature_list.json` change (statuses 17 + 27 still `in_progress`; 24 + 25
still `done`). F1–F7 all addressed:
- F2 added `422 UNKNOWN_PROMPT_VERSION` + moved prompt-version resolution
  into `submit_generation(config: ConfigPort)`.
- F6 moved the JSON + framing prose verbatim into
  `domain/ai_prompt.py` `PromptInstructionsVersion`/`PromptInstructions`
  `v1` (append-only intact); `bedrock.py::_render` is now a pure
  `string.Template` assembler. Cited `FR-AI-14` consumed-not-owned.
- **Owner note:** `test_no_recipe_metadata_logic.py` (feature 25 guard)
  gained a narrow sanctioned-line exemption + verbatim guard for the
  relocated metadata-instruction string — the feature 25 spec doc may
  now be slightly behind its guard. Non-blocking; flag at close.

## Verification run — APPROVED (2026-09-06)

0 findings, 0 mutants survived. All 5 fix-round mutants (F1/F3/F4/F5/F6)
re-applied and KILLED; a bonus feature-25 guard probe (`return
recipe.servings` in `ai_prompt.py`) also killed. F2 traced — prompt
version resolved in `submit_generation` after the idempotent-hit return,
before the pinned writes + enqueue; `422 UNKNOWN_PROMPT_VERSION` mapped.
F6 `domain/ai_prompt.py` diff is purely additive (6 new fields, `v1`'s
original 3 untouched). `bedrock.py` has zero Spanish literals. G-88
intact. Tree restored byte-identical. `./init.sh` §5 green — **769
passed**. §4 red only on the intentional dual `in_progress`.

**The bundle is implementation-complete and reviewer-APPROVED.**

## Next step — OWNER

1. **Commit** the bundle — 46 code/spec entries (feature 17 first commit
   + feature 27 reopen delta). `progress/current.md` stays uncommitted
   (wiped at session close). Suggested split (gga `TIMEOUT`=1200 on a
   changeset this size — see the gga-splits-large-commits memory):
   - `feat: generation queue claim/record-result and submit enrichment`
     — `ports/generation_queue.py`, `adapters/sqs.py`, fakes, the two
     contract suites, `messages.py`, `errors.py`, `_helpers.py`,
     `test_error_mapping.py`, `specs/rest_api_persistence_and_services/`.
   - `feat: synchronous pinned-slot candidates at generation submit`
     — `generation_submission.py` + its test, `routing.py`.
   - `feat: ai generation lambda worker` — all of `backend/lambda_ai/`,
     the new `planner_core` ports + `week_generation.py`, the new
     contract suites, `test_week_repository_contract.py`,
     `test_no_generation_quota.py`, `specs/ai_lambda/`.
   - `feat: version the full rendered ai prompt` — `domain/ai_prompt.py`,
     `test_ai_prompt.py`, `test_no_recipe_metadata_logic.py`,
     `bedrock.py` (the F6 slice; could also ride commit 3).
   - `chore: mark features done` — `feature_list.json` with 17 + 27
     both `done`.
2. **Status:** feature 17 `in_progress` -> `done` (its FIRST `done`);
   feature 27 `in_progress` -> `done` (re-close). Leader never sets these.

## Deferred — OWNER, later (none block anything)

- Contract lift (a): feature 28 single-recipe `POST /v1/generations`
  body + `attempt` derivation.
- Contract lift (b): reconcile the whole-week 409 downgrade (Q3) in
  `rest_api_contract.md` §3.5 / L171.
- **F5** (from feature 16): `EXPECTED_ROUTES` in `test_routing_table.py`
  is a hand-maintained literal — own feature or signed-off deferral.
- **Feature 25 guard/spec:** `test_no_recipe_metadata_logic.py` gained a
  sanctioned-line exemption for the relocated `JSON_OUTPUT_INSTRUCTION`
  lines; `specs/recipe_metadata_fields/` may want a one-line note that
  the metadata instruction now also lives in the versioned prompt block.

## Deferred — OWNER, later (neither blocks this round)

- Contract lift (a): feature 28's single-recipe `POST /v1/generations`
  body + `attempt` derivation.
- Contract lift (b): reconcile the whole-week 409 downgrade (Q3) in
  `rest_api_contract.md` §3.5 / L171.
- **F5** (carried from feature 16): `EXPECTED_ROUTES` in
  `test_routing_table.py` is a hand-maintained literal — own feature or
  signed-off deferral.

## Feature 28 — single_recipe_generation (added 2026-09-06)

`pending`, tier 3, `depends_on: [11, 12, 16, 17]`, `covers: []`. Owns the
single-recipe AI generation submit-then-poll path that feature 12
explicitly deferred: the contract body shape (owner lift), the
server-authoritative `attempt` fold, the domain single-recipe request
type + key, the `ai` worker's single-recipe branch, the per-slot 409.
Not actionable until 17 is `done`.

### Carried forward (feature 16, non-blocking)

- **F5** — `EXPECTED_ROUTES` in `backend/lambda_api/tests/test_routing_table.py`
  is a hand-maintained literal, not derived from `docs/rest_api_contract.md`.
  Owner to pick a home: its own small backlog feature or a signed-off
  deferral. Not urgent; feature 16 closed without it.
