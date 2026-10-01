# Frontend UI/UX improvement plan (desktop + mobile)

Audit date: 2026-10-01 · Scope: `frontend/src/**` at commit `9d25fe6` (branch `dev`).
Rubric: Vercel *Web Interface Guidelines* (`.claude/skills/web-design-guidelines/SKILL.md` →
`vercel-labs/web-interface-guidelines/command.md`, fetched 2026-10-01), plus WCAG 2.2 AA
success criteria where the guideline is silent. Rule names below are quoted from that rubric
(section › rule) or cited as WCAG SC numbers.

**Method.** Static audit only. Every `.jsx` under `src/components/`, the tokens, the hooks that
shape UI state, `index.html`, `fonts.js`, `locale.js`, `domain/labels.js` and the messages module
were read line by line. No dev server was started: the SPA needs the local API on `:8080`, and
starting Vite writes a cache into `frontend/node_modules/.vite`, which the brief forbids. Layout
claims at 1440 / 768 / 375 px were worked out from the inline `grid`/`flex` rules and token
sizes. Contrast ratios were computed from `tokens/colors.js` with the WCAG relative-luminance
formula. **Phase 1, slice S0 is a real-browser check that has to confirm these before anything ships.**

---

## Read this first: three gates on what may change

The project has frozen decisions that block parts of a textbook WCAG 2.2 AA plan. Every
finding and slice carries one of these tags:

| Tag | Meaning | Source |
|---|---|---|
| **OK** | Can ship now. It uses native HTML semantics, inline styles and existing tokens, and adds no ARIA. | — |
| **CONV** | Needs a stylesheet or `@media`/pseudo-class rule, which the inline-CSS convention forbids. Ships only with an approved `design.md` deviation. | `docs/conventions.md` › *Styling: inline CSS* / *The responsive constraint* |
| **REQ** | Adds accessibility work beyond browser defaults: `aria-*`, `role`, `tabIndex`, a11y libraries or contrast targets. **Needs a requirement change** (a new lettered Part lifting FR-UX-07/G-62) and an update to `tests/test_no_extra_accessibility.test.js` (R22). | `docs/requirements.md` FR-UX-07; conventions › *Do not* |

Key point for the owner: **most of the high-value fixes are tagged OK.** FR-UX-07 says the app
"relies on browser-default accessibility". Today the code *removes* some of those defaults:
`outline: 'none'` strips the focus ring, `type="button"` replaces native `<form>` submission,
and hand-made overlays replace `<dialog>`. Restoring a browser default does not add a11y work
beyond the defaults, so it falls inside the frozen scope.

---

## (a) Summary

The SPA is functionally complete and consistently tokenised for colour. Its responsive story
is **fluid grids only**, and the `useBreakpoint` hook and `BREAKPOINT` tokens exist but are
**used nowhere** (no `useBreakpoint`/`tokens.breakpoint` references outside their own files).
On desktop the app works but looks unfinished. On a 375 px phone several screens overflow
sideways or become unusable. Primitives are duplicated: three different "submit" styles, two
copies of the auth card, and two copies each of the Edit/Delete/Close icons. Forms skip native
`<form>` behaviour. Overlays are plain `position: fixed` divs with no Escape key, no focus
handling and no scroll lock.

### Top 5 issues

1. **Authoring forms open off-screen (P0, both).** "Añadir plato", "Añadir receta" and
   "Añadir elemento" mount their form **below the whole page**
   (`WeekPlannerView.jsx:79-93`, `LibraryView.jsx:205-216`, `ShoppingListView.jsx:232-241`).
   On a phone the Monday button opens a form roughly 2,000 px further down, with no scroll and
   no title naming the day or slot. This is the same symptom as the past issue
   `add-dish-button-inert`.
2. **Mobile layouts overflow (P0, mobile).** The nav is 5 non-wrapping pills
   (`App.jsx:142`). The summary grid is fixed at `repeat(7, …)` (`SummaryView.jsx:47`), which
   leaves about 35 px per column at 375 px. These rows also never wrap: the authoring tabs, the
   ingredient row, the rule forms, the admin create row, `AccountRow` and the shopping re-sync
   row.
3. **Focus ring removed on every shared input (P0, both, OK).** `controlStyles.js:143` and
   `LibraryFilters.jsx:53` set `outline: 'none'` and put nothing in its place. Rubric: *Focus
   States › Never `outline: none` without focus replacement*; WCAG 2.4.7. This also breaks the
   FR-UX-07 "browser defaults" promise.
4. **Forms don't behave like forms (P1, both, OK).** No `<form>` anywhere. Enter does not
   submit login or set-password. There is no `autocomplete` (password managers fail, and so does
   iOS keychain), and no busy label while a request runs. Disabled submit buttons look identical
   to enabled ones (`LoginView.jsx:85-97`). Mutation buttons have no in-flight state, so a double
   tap duplicates a POST (`useWeekPlanner.js` `submitCandidate`).
5. **Error and validation text is barely legible, and errors are shown inconsistently (P1,
   both).** Errors render as `honey` on `honeySoft` at **2.28:1** in Week and Library, but as
   plain body-ink text with no visual treatment in Rules, Shopping, Summary, Admin and Login.
   Inline validation uses `honey` on `surface` at **2.72:1** in 12 px text. Errors always appear
   at the top of the page, even when the user acted at the bottom.

---

## (b) Findings

Severity: **P0** blocks a task or breaks layout on a supported device · **P1** major friction
or a clear standards failure · **P2** moderate · **P3** polish.
Device: D = desktop/laptop, M = mobile, B = both.

| ID | Area / file:line | Rule violated | Sev | Dev | Gate | Evidence |
|---|---|---|---|---|---|---|
| F01 | `WeekPlannerView.jsx:79-93`, `LibraryView.jsx:205-216`, `ShoppingListView.jsx:232-241` | Focus States › overlays must not hide the focused element; WCAG 3.2 (predictable) | P0 | B | OK | Authoring/item form is appended after the full grid or list. Nothing scrolls it into view, and it has no title naming the target day/slot (the prototype's `addTitle`, "Añadir a lunes · Comida", was not carried over). |
| F02 | `App.jsx:142-153` | Safe Areas › avoid unwanted scrollbars; WCAG 1.4.10 reflow | P0 | M | OK | 5 nav pills in a `display:flex` row with no wrap and no overflow handling. "Lista de la compra" alone is about 150 px, so the page scrolls sideways at 375 px. |
| F03 | `SummaryView.jsx:47` | Content Handling › handle long content; WCAG 1.4.10 | P0 | M | OK | `repeat(7, minmax(0,1fr))` gives about 35 px per day at 375 px and about 90 px at 768 px, so recipe names break mid-word. |
| F04 | `tokens/controlStyles.js:143`, `LibraryFilters.jsx:53` | Focus States › never `outline:none` without replacement; WCAG 2.4.7 | P0 | B | OK | `selectStyle`/`inputStyle` (used by Rules, Shopping, Admin, AccountRow) and the library search input strip the native ring. |
| F05 | `RecipeAuthoringForm.jsx:398`, `:175-215` | Avoid unwanted scrollbars; WCAG 1.4.10 | P1 | M | OK | The 3 method tabs (about 480 px) and the ingredient row (name + 80 px qty + warning + unit select + "Quitar ingrediente") are non-wrapping flex rows. |
| F06 | `RulesView.jsx:117,174,232`; `AdminAccountsView.jsx:61-94`; `AccountRow.jsx:56-63`; `ShoppingListView.jsx:56`; `AiRecipePreview.jsx:53` | Avoid unwanted scrollbars; *Flex children need `min-w-0`* | P1 | M | OK | Every form or action row is a flex row without `flexWrap`. `AccountRow` puts avatar, name, 1-2 badges and 3 buttons on one line, plus an input while renaming. `ResyncScope` puts a long sentence, two WeekLabels and a button on one line. |
| F07 | `LoginView.jsx:73-83`, `SetPasswordView.jsx:71-81` | Layout correctness | P1 | B | OK | `width:'100%'` + padding + border with no `boxSizing:'border-box'` makes the inputs overflow the card by about 18 px. |
| F08 | `LoginView.jsx:127-152`, `SetPasswordView.jsx:146-172`, `ShoppingListView.jsx:98-143`, `AdminAccountsView.jsx:68-93`, `RulesView.jsx` forms, `RecipeAuthoringForm.jsx` | Forms › submit stays enabled + spinner; native `<form>` | P1 | B | OK | No `<form>` in the codebase, so Enter does nothing. Submit is `type="button"`. The prototype itself used `<form onSubmit>` (`Sobremesa.dc.html` login). |
| F09 | `LoginView.jsx:129-143`, `SetPasswordView.jsx:148-162`, `AdminAccountsView.jsx:70-84`, `AccountRow.jsx:106,133` | Forms › inputs need `autocomplete` and meaningful `name`; *disable spellcheck on usernames* | P1 | B | OK | No `autoComplete`, `name`, `spellCheck` or `autoCapitalize`. iOS capitalises the first letter of the username. Password managers can't tell login (`current-password`) from set or reset (`new-password`). |
| F10 | `LoginView.jsx:85-97,145-152`, `SetPasswordView.jsx:165-172` | Forms › spinner during request; Typography › loading ends with `…` | P1 | B | OK | `disabled` is set, but the inline `backgroundColor: terra` overrides the native disabled look, so the button never changes. No "Entrando…" text. |
| F11 | `useWeekPlanner.js` mutations, `useLibrary.js`, `useShoppingList.js`, `useRules.js`, `RecipeAuthoringForm.jsx:281,377` | Forms › spinner during request | P1 | B | OK | Only the auth hooks track `isSubmitting`. "Guardar receta", "Marcar como definitivo", "Guardar regla" and "Añadir" can fire twice, and nothing shows that a request is pending. |
| F12 | `WeekPlannerView.jsx:44-55`, `LibraryView.jsx:109-121` | WCAG 1.4.3 (contrast) | P1 | B | OK* | Error text is `honey` on `honeySoft` = **2.28:1**. *Using `ink` on `honeySoft`, as `ConnectionLostBanner` already does, is a consistency fix, not a new contrast target. |
| F13 | `RulesView.jsx:98`, `ShoppingListView.jsx:184`, `SummaryView.jsx:30`, `AdminAccountsView.jsx:59`, `LoginView.jsx:126`, `SetPasswordView.jsx:145` | Forms › errors inline next to fields; Content & Copy › error messages include fix | P1 | B | OK | Errors render as a plain `<p>` in body ink, so they can't be told apart from content. They always sit at the top of the view and never move focus or scroll. |
| F14 | `RecipeAuthoringForm.jsx:155,196,220,246,272,346` | WCAG 1.4.3 | P2 | B | OK* | Inline validation is 12 px `honey` on `surface`/`surface2`, about **2.6–2.7:1**. |
| F15 | `ShoppingListView.jsx:38` | Locale › numbers via `Intl.NumberFormat` (**FR-UX-03**) | P1 | B | OK | `{item.quantity}` is rendered raw, so 0.5 shows as "0.5" instead of "0,5". Every other quantity site uses `formatNumber`. |
| F16 | `RecipeDetailView.jsx:149-154` | Content Handling › don't render broken UI for empty values | P2 | B | OK | A null `servings` renders the pill "Comensales: " with nothing after it. `estimatedTime` is not formatted and also renders blank when null. |
| F17 | `MealCard.jsx:11-21`, `DaySlot.jsx:130-145`, `RecipeDetailView.jsx:80-101`, `LibraryView.jsx:54-65`, `controlStyles.js:168-174` (ghost) | WCAG 2.5.8 target size (24 px min); Touch › hit targets | P1 | M | OK | Padding of 4/8 px with 12 px text gives targets about 20–22 px tall. MealCard puts 3 of these side by side, so mis-taps on "Eliminar" are likely. |
| F18 | `ShoppingListView.jsx:32-36` | Forms › checkbox and label share one hit target | P1 | M | OK | A bare native checkbox (about 13 px) is not wrapped in a `<label>`, so tapping the item text does nothing. This is the most frequent action in a supermarket. |
| F19 | `RecipeAuthoringForm.jsx:62`, `LibraryFilters.jsx:56,65`, `controlStyles.js:136-144` | Touch › avoid iOS focus zoom (inputs < 16 px) | P1 | M | OK | Input font sizes are 14 px and 12 px, so iOS Safari zooms the page on every focus. |
| F20 | `RecipeAuthoringForm.jsx:179-192, 234-238, 260-264` | Accessibility › form controls need `<label>`; Forms › placeholders end with `…` and show an example | P1 | B | OK | The ingredient name and qty inputs use the placeholder as their only label. Tool and step inputs have **no label at all**. |
| F21 | `ConfirmDialog.jsx:10-57`, `RecipeDetailView.jsx:48-78` | Touch › `overscroll-behavior: contain` in modals; Animation › interruptible; WCAG 2.1.2/2.4.3 | P1 | B | OK | No Escape, no backdrop-click close, no initial focus, no focus containment, and the body still scrolls behind. Native `<dialog>.showModal()` gives all of this as a **browser default**, with no ARIA. |
| F22 | `ConfirmDialog.jsx:11-21` | Safe Areas | P2 | M | OK | The backdrop has no padding and the panel has no `maxWidth`, so long messages (the pin-cascade list) touch the screen edges on mobile and stretch wide on desktop. |
| F23 | `ConfirmDialog.jsx:42-52`, `messages/es-ES.js:14` | Content & Copy › specific button labels | P2 | B | OK | The button always says "Confirmar". "Eliminar receta", "Reemplazar" or "Quitar" would be clearer. The cancel button has no token styling and renders as a browser-grey button. |
| F24 | `RecipeDetailView.jsx:65` | Safe Areas › `env(safe-area-inset-*)`; mobile viewport units | P2 | M | OK | `maxHeight: '90vh'` is cut off under the iOS URL bar, and there is no bottom safe-area padding. The close button scrolls away inside long recipes. |
| F25 | `RecipeDetailView.jsx:48-78` | Layout | P2 | D | OK | The bottom sheet is also used at 1440 px: a 560 px panel glued to the bottom edge. On desktop it should be a centred modal. |
| F26 | `App.jsx:47-54` | Hover & Interactive States › states increase contrast | P2 | B | OK | Active nav is shown only by `terraSoft` vs `surface` background (about 1.2:1). There is no weight or border change. |
| F27 | `hooks/useApp.js` (`useState('week')`) | Navigation & State › URL reflects state; deep-link | P2 | B | OK? | Refresh always resets to "Semana". Browser/Android Back leaves the app. `document.title` never changes. A plain History API or hash sync is possible without a router library (design.md §5 bans only a *library*). |
| F28 | `index.html:5` | Safe Areas | P2 | M | OK | The viewport meta has no `viewport-fit=cover`, which the safe-area insets need. |
| F29 | `index.html:3-8` | Dark Mode › `color-scheme`; `<meta name="theme-color">` | P2 | M | OK | No `color-scheme: light` (Android "force dark" and Windows dark-mode `<select>` can half-invert the controls). No `theme-color` (the browser bar stays default). No favicon (404). |
| F30 | `index.html:8`, `App.jsx:43`, `LoginView.jsx:12` | Layout | P3 | B | OK | Body keeps the default 8 px margin, so the white header is not full-bleed. `100vh` on mobile should be `100dvh`. |
| F31 | `App.jsx:106-114, 133-141` | Accessibility › semantic HTML; headings hierarchical | P2 | B | OK | Header is a `<div>`, not `<header>`. The h1 is an untokenised 2em default. The week view has no h2 while every other view has one. Login/set-password have an h2 with no h1. Day names (`DaySlot.jsx:70`, `SummaryView.jsx:54`) are `<p>`, not headings. |
| F32 | `WeekSwitcher.jsx:37-61` | Accessibility › icon-only buttons need a name; touch target | P2 | B | OK (title) / REQ (aria-label) | The `‹`/`›` glyph buttons are named only by `title`, which is invisible on touch. They are 32 px. The active-week arrow is a clickable no-op. A two-segment "Actual / Próxima" control with visible ranges would be clearer. |
| F33 | `DaySlot.jsx:114-115` | Content Handling › empty states; visual noise | P2 | B | OK | An empty week renders **14** dashed "Todavía no hay platos para este hueco." boxes plus 7 "Sin platos" pills. |
| F34 | `EmptyState.jsx`, `messages/es-ES.js:97,124,146,173,105` | Content & Copy › include next step (**FR-UX-05** "with guidance") | P2 | B | OK | Messages only say something is empty ("Todavía no hay recetas…"). No call to action is placed in the empty state. The add button sits elsewhere, e.g. `LibraryView.jsx:126` directly above the empty box with no spacing. |
| F35 | `LoadingState.jsx:14-22`, `hooks/useLoadingShimmer.js:10-14` | Animation › honor `prefers-reduced-motion`; perceived performance | P2 | B | OK | The "shimmer" toggles `surface`↔`surface2` (about 1.05:1, effectively invisible) every 600 ms forever, whatever the reduced-motion setting. A text-only loader replaces the whole view, so the layout shifts when data arrives. |
| F36 | `SetPasswordView.jsx` + `useSetPasswordForm.js:20` | Forms › inline errors; Content › say what's required | P2 | B | OK | "No coinciden" fires on the first character typed in Confirm. The password policy (FR-AUTH-15: 10–64 chars; the prototype showed it verbatim) is not shown until the server rejects the password. |
| F37 | `RecipeAuthoringForm.jsx:281` | Forms › errors next to fields; submit enabled until request | P2 | B | OK | Submit is disabled with no explanation when name or category are blank (only the list sections warn). |
| F38 | `CandidateAuthoring.jsx:26-32`, `LibraryView.jsx:208-214` | Forms › warn before navigation with unsaved changes | P2 | B | OK | "Cerrar" (and switching nav or logging out) silently discards a half-written recipe or AI spec. |
| F39 | `MealCard.jsx:110-123`, `LibraryView.jsx:165-179`, `SummaryView.jsx:87-100`, `AccountRow.jsx:82` | Content Handling › long content, `min-w-0`, `break-words` | P2 | B | OK | User text (recipe names, usernames, ingredients) has no `overflowWrap`/`minWidth:0`, so a long unbroken word overflows its card. Button text centres by default when it wraps (MealCard/Summary). |
| F40 | `domain/labels.js:49-57`, `WeekLabel.jsx:12`, `WeekSwitcher.jsx:17` | Locale › Intl dates (timezone correctness) | P2 | B | OK | `new Date('YYYY-MM-DD')` is UTC midnight but is formatted in local time, so west of UTC every date and weekday label is one day early. Fine in Spain; wrong for a traveller. The range `28/9/2026–4/10/2026` is also hard to scan, and `Intl.DateTimeFormat#formatRange` gives "28 sept – 4 oct 2026". |
| F41 | `ShoppingListView.jsx:110-113`, `RecipeAuthoringForm.jsx:144-192` | Forms › correct `type`/`inputmode` | P2 | M | OK | `type="number"` with no `inputMode` (`decimal` for quantity, `numeric` for servings/time). Quantity can't take "0,5" with a comma in some engines. |
| F42 | `ShoppingListView.jsx:215-228` | Content Handling › empty states | P3 | B | OK | The "Comprado" card renders with only its heading when nothing is checked. |
| F43 | `RulesView.jsx:206-210` | IA / layout | P2 | M | OK | A full `LibraryRecipePicker` card grid sits inside the "Platos fijados" card, so on mobile the save button ends up several screens below the day/slot selects. |
| F44 | `RulesView.jsx:28`, `ShoppingListView.jsx:41-46`, `AccountRow.jsx:159` + `controlStyles.js:171` | WCAG 1.4.3; destructive styling | P2 | B | REQ (contrast target) / OK (token swap) | Destructive "Eliminar" is a ghost button in `ink3` = **2.95:1**, styled like a secondary action. The 18-colour palette has no danger colour (open question Q6). |
| F45 | `LoginView.jsx:62-71`, `RecipeAuthoringForm.jsx`, `LibraryRecipePicker.jsx:79-87`, `DaySlot.jsx:24-28` | WCAG 1.4.3 | P2 | B | REQ | `ink3` text (field labels, authors, "Sin platos" pill) is 2.6–2.95:1. The "Definitivo" badge, `olive` on `oliveSoft`, is 3.23:1 at 12 px. Input borders (`line2` on `surface2`) are 1.41:1 (WCAG 1.4.11). |
| F46 | all components | Hover & Interactive States › buttons need `hover:` state | P2 | D | CONV | Inline styles can't express `:hover`/`:active`/`:focus-visible`. No control has hover feedback, and link-styled buttons keep the default arrow cursor (`cursor:'pointer'` *is* possible inline → OK). |
| F47 | `ConnectionLostBanner.jsx`, error `<p>`s, AI progress | Accessibility › async updates need `aria-live` | P2 | B | REQ | Banners, errors and "Generando la receta…" aren't announced. (The native `<output>` element is an implicit status region and could be a borderline OK alternative.) |
| F48 | `App.jsx` shell | Accessibility › skip link; Focus › sticky header must not cover focus | P3 | D | OK | No skip link. Changing view leaves focus on the nav button, which is fine; but the new view's h2 isn't focused or scrolled to, and on mobile the user stays scrolled deep down. |
| F49 | `fonts.js:44-46`, `index.html` | Performance › critical fonts preload, `font-display: swap` | P3 | B | OK | `FontFace` has no `display` descriptor, and nothing is preloaded, so text reflows late when Baloo/Nunito arrive. |
| F50 | `WeekPlannerView.jsx:60` | Layout | P2 | D | OK | `minmax(260px,1fr)` gives 5 + 2 columns at 1440 px, so Saturday and Sunday wrap under Monday. 4 + 3 at 1280 px. `<main>` has no max-width, so at 2560 px cards stretch thin. |
| F51 | tokens (`RecipeDetailView.jsx:198-199`, `controlStyles.js:194-195`, `LoginView.jsx:23,37-38`, `AccountRow.jsx:69-70`, grid mins 200/240/260 px, `AiRecipePreview.jsx:14` `0`, `RecipeDetailView.jsx:166` `0`) | Convention: no literals in `style` | P3 | B | OK | Size literals have crept in. There are no control-height, icon-size, content-width, z-index or line-height tokens. |
| F52 | duplicated primitives | Consistency | P2 | B | OK | Three submit-button styles (`LoginView`, `RecipeAuthoringForm`, `controlStyles.primaryButtonStyle`). The auth card style is copied in two files. Edit/Delete/Close icons are each defined twice. Five different error renderings. |
| F53 | `useLoadingShimmer` + `AiFields` | Perceived performance / progress | P3 | B | OK | AI generation shows a generic loader with no elapsed or "this can take up to N s" hint, and the failed state has no inline "Reintentar" button (Generate must be found again). |
| F54 | `DAY_LABELS` usage | Copy | P3 | B | OK | Day headings render lowercase ("lunes"). As standalone card titles, Spanish convention allows initial capital (`textTransform:'capitalize'` inline, or capitalise in `labels.js`). |

Not violations (checked): `…` is used correctly in loading copy. Dates and numbers mostly use
`Intl`. No `user-scalable=no`, no `transition: all`, no `onPaste` blocking, no `autoFocus`, no
`<div onClick>`. Destructive actions are gated (FR-UX-04). Every clickable is a real `<button>`.

---

## (c) Cross-cutting foundations

### C1. Tokens (`src/tokens/`)
- **Semantic colour aliases** live in `colors.js` and point at the 18 lifted values, so no new
  colours are needed: `text`=ink, `textMuted`=ink2 (the minimum for any readable text; reserve
  `ink3` for disabled/decorative), `border`=line, `borderStrong`=line2, `accent`=terra,
  `ai`=aub, `warningBg`/`warningEdge`=honeySoft/honey, `warningText`=**ink**, and
  `focusRing`=terra.
  A `danger` colour would be a palette extension → **Q6**.
- **New scales:** `size.control` `{ sm: '32px', md: '44px' }` (44 on mobile, 36–40 on desktop);
  `size.icon` `{ sm: '14px', md: '20px' }`; `layout.contentMax: '1200px'`,
  `layout.sheetMax: '560px'`, `layout.dialogMax: '440px'`, `layout.authCardMax: '420px'`;
  `zIndex` `{ banner, sheet, dialog }`; `lineHeight` `{ tight: 1.2, body: 1.5 }`.
- **Input font-size floor:** `fontSize.input = fontSize.md` (16 px) on mobile (fixes F19).

### C2. Breakpoints and viewport
- Keep `BREAKPOINT.tablet = 600` / `desktop = 1024`, and finally *use* them. Add one
  `useViewport()` hook (built on the existing `useBreakpoint`) called **once in `App.jsx`**.
  It returns `'mobile' | 'tablet' | 'desktop'` and is passed down as a prop, so components stay
  pure (conventions › Separation of concerns).
- Styles are written mobile-first: the base object targets 375 px, and a `viewport` branch adds
  desktop overrides. Fluid grids stay the default, and breakpoints are used only for the 4
  real layout switches: nav position, sheet vs modal, week grid shape, summary layout.
- Add `prefers-reduced-motion` the same way: `useBreakpoint('(prefers-reduced-motion: reduce)')`.

### C3. Component primitives (new `src/components/ui/`, styles in `tokens/controlStyles.js`)
| Primitive | Replaces | Contract |
|---|---|---|
| `Button` (`variant`: primary / secondary / ghost / danger*; `size`; `busy`) | 3 submit styles, ghost, icon buttons | min-height `size.control`, `cursor:'pointer'`, visibly distinct `disabled` style, `busy` shows `…` label and blocks re-click, `touchAction:'manipulation'` |
| `Field` (label above, hint, error, child control) | ad-hoc `<label>`s | always a wrapping `<label>`; error text in `textMuted`/ink with honey edge; passes `name`/`autoComplete`/`inputMode` through |
| `TextInput` / `Select` / `TextArea` | `inputStyle`, `fieldInputStyle`, `searchInputStyle` | `boxSizing:'border-box'`, `width:'100%'`, 16 px on mobile, **no `outline:'none'`**, explicit `backgroundColor`/`color` on `<select>` |
| `FormRow` | every non-wrapping row | `display:flex; flexWrap:'wrap'; gap`; children `minWidth:0` |
| `Overlay` (`kind`: dialog / sheet) on native `<dialog>` | `ConfirmDialog` shell, `RecipeDetailView.Sheet`, inline authoring | `showModal()`/`close()` in a tiny `useDialog(ref, open)` hook; Escape → `onClose`; backdrop click → `onClose`; `overscrollBehavior:'contain'`; sticky header with title and close; `maxHeight:'90dvh'`; `paddingBottom: env(safe-area-inset-bottom)`; bottom sheet on mobile, centred on desktop |
| `Banner` (`tone`: warning / info) | 5 error renderings + `ConnectionLostBanner` | ink on honeySoft, 4 px honey edge, optional dismiss/"Reintentar" |
| `EmptyState` (+ optional `action`) | current text-only | message + one primary CTA (FR-UX-05 "guidance") |
| `Skeleton` | `LoadingState` text bar | layout-shaped blocks; static under reduced motion |
| `Card`, `Badge`, `PageHeader` (h2 + actions slot), `Icon` set | duplicated card/badge/icon code | single source |

\* `danger` depends on Q6. Until then use `secondary` with `ink` text.

### C4. Accessibility baseline that fits FR-UX-07 (all **OK**)
Use native semantics only: `<header>`, `<nav>`, `<main>`; one `<h1>` per screen, an `<h2>` per
view and `<h3>` per section/day; a `<form>` per form; `<label>` wrapping every control;
`<dialog>` for overlays; visible text on every button (no glyph-only buttons; keep the glyph
and add text, or a visible `title` fallback); don't remove the native focus ring; give
`<html lang="es-ES">` (already present) and the `translate="no"` attribute to brand-like tokens
(units "ud", "g", "ml"). Everything beyond this (ARIA names, live regions, `aria-current`,
contrast targets, axe in CI) belongs in **Phase 5 (REQ)**.

---

## (d) Per-screen improvements

### Shell (`App.jsx`, `index.html`)
- **Desktop:** `<header>` with the app title at left and Salir at right. Below it, a
  `<nav>` of pills with clear active state (weight 700 + terra border + terraSoft). Content is
  centred in `layout.contentMax`. `document.title` = "Vista · Planificador semanal".
- **Mobile:** sticky compact header (title at `fontSize.lg`, Salir as a smaller ghost). Put the
  **nav in a bottom tab bar**, as the prototype does (`Sobremesa.dc.html:422-427`): 5 icon +
  short-label buttons, ≥ 48 px tall, `paddingBottom: env(safe-area-inset-bottom)`,
  `position:'sticky'`/`fixed`, and the main content padded so nothing hides under it (Q3).
  Changing view scrolls to the top.
- Both: `viewport-fit=cover`, `color-scheme: light` + `theme-color` = paper, body `margin:0`,
  `minHeight:'100dvh'`, favicon from the monogram.

### Login / Set password
- **Both:** wrap in `<form onSubmit>`. Use `autoComplete="username"` / `"current-password"` /
  `"new-password"`, `name`, `spellCheck={false}`, `autoCapitalize="none"`. Submit stays enabled
  and validates on submit (Q: keep R-gated disabling? see Risks). While submitting it shows
  "Entrando…"/"Guardando…". The error shows in a `Banner` above the button. Make the h2 an h1.
  Fix `boxSizing`.
- **Set password:** show the FR-AUTH-15 policy hint under "Nueva contraseña". Show mismatch only
  on blur of Confirm or on submit, not on the first keystroke.
- **Mobile:** card is full-width with `space.md` gutters and inputs at 16 px. The top padding
  respects the safe area. The desktop layout is unchanged apart from the fixes.

### Week planner (`WeekPlannerView`, `DaySlot`, `MealCard`, `WeekSwitcher`)
- **Desktop (≥1024):** a 7-column grid (`repeat(7, minmax(0,1fr))` inside `contentMax`, with
  compact cards) or a deliberate 4 + 3 grid (Q7). Add a page h2 ("Menú semanal") and turn
  WeekSwitcher into a two-segment control that shows **both** weeks' designation + range, with
  the active one highlighted (FR-UX-06 stays satisfied). Show MealCard actions as a compact row
  with text labels.
- **Mobile (<600):** a horizontal **day strip** (L M X J V S D, today highlighted). Tapping a
  day scrolls to that day's card. On first load, open scrolled to today for the current week.
  Each day card has slots as `<h3>`-level rows. MealCard gets a 44 px primary action ("Marcar
  como definitivo"). Edit and Eliminar stay visible as 44 px secondary buttons in a wrapping
  row. "Añadir plato" becomes a full-width 44 px button.
- **Both:** an empty slot shows one compact line "Sin platos" + "Añadir plato" instead of a
  dashed box (F33). Authoring opens in the `Overlay` titled "Añadir a lunes · Comida" (F01).
  Edit uses "Editar · lunes · Comida". Recipe detail uses the `Overlay` (sheet on mobile, modal
  on desktop). The week error `Banner` sits in the overlay when the failure came from it.

### Recipe authoring (`RecipeAuthoringForm`, `AiRecipePreview`, `LibraryRecipePicker`)
- **Both:** method tabs wrap (`FormRow`). On mobile they become a full-width 3-segment control
  with shorter labels: "Biblioteca", "Desde cero", "Con IA" (keep the `aub` AI colour). Every
  input gets a real label. Ingredient rows become a mini card: name (full width), then qty
  (`inputMode="decimal"`), unit and remove in a wrapping row. Validation moves next to its
  field, in readable colour. Submit is a `busy` Button. If anything has been typed, closing
  asks for confirmation via `useConfirm` ("¿Descartar los cambios?").
- **AI tab:** `rows={3}` textareas. After 10 s the loader adds "Puede tardar unos segundos…".
  On `failed`, show a `Banner` with a "Reintentar" button. The preview's
  Accept/Regenerate/Discard row wraps, and on mobile Accept is full-width and first.
- **Picker:** cards are selectable by a whole-card `<button>` (or a `<label>` + radio, which is
  the native single-select). Name text gets `overflowWrap:'anywhere'`. If the library grows
  past about 50 items, add `contentVisibility:'auto'` (inline-capable).
- **Desktop:** the overlay is a centred `dialogMax`/`sheetMax` modal, with the ingredient row
  on one line when it fits.

### Library (`LibraryView`, `LibraryFilters`)
- **Desktop:** `PageHeader` with h2 + "Añadir receta" on the right. Filters on one line. Cards
  in an `auto-fill minmax(240px)` grid inside `contentMax`.
- **Mobile:** sticky filter bar (search at 16 px, full width, then the category select). Show
  "Añadir receta" as a floating or bottom full-width primary button above the tab bar. Card
  actions are 44 px.
- **Both:** the empty state carries the "Añadir receta" CTA. A filtered empty state offers
  "Quitar filtros". The pin-cascade confirm shows its rule list as a real `<ul>` in the dialog
  (widths fixed by F22). The confirm button reads "Eliminar receta y regla".

### Rules (`RulesView`)
- **Both:** each section's add form is a `<form>` with `FormRow` wrapping. Labels sit above
  selects. Each rule row has text left and a 44 px "Eliminar" right, with names wrapping.
- **Pin section:** move the recipe picker into an `Overlay` opened by "Elegir receta…", and
  show the selected recipe name inline (F43).
- **Mobile:** sections are stacked full-width cards. **Desktop:** sections can sit in 2 columns
  (count + disabled days | pins).

### Shopping list (`ShoppingListView`)
- **Mobile is the primary device here.** Rows are ≥ 48 px. The checkbox is wrapped with the
  name in one `<label>`, so the whole row toggles. Quantity uses `formatNumber` (F15) and is
  right-aligned with `fontVariantNumeric:'tabular-nums'`. Edit and Eliminar move into a compact
  trailing pair of 44 px buttons. Hide "Comprado" when empty, or show its count.
- Re-sync block: the scope sentence goes on its own line, then the two week ranges, then the
  button. Everything wraps. While re-syncing, the button itself shows "Resincronizando…"
  instead of a second loader inside the row.
- The add/edit item form becomes an `Overlay` (bottom sheet) with quantity
  `inputMode="decimal"` and unit select. On desktop, an inline card at the **top** of the list
  is acceptable.

### Summary (`SummaryView`)
- **Mobile:** a vertical list of days (h3 day, then Comida / Cena rows). Empty slots show "—"
  so the week's gaps are visible.
- **Tablet:** `auto-fill minmax(160px)`. **Desktop:** 7 columns are fine at ≥1024 within
  `contentMax`.
- Both: the error `Banner` goes after the h2, and the "Definitivo" badge is dropped (every
  entry is definitive, so it is noise) or kept tiny.

### Admin (`AdminAccountsView`, `AccountRow`)
- **Both:** the create form is a `<form>` with `autoComplete="off"` on username and
  `"new-password"` on the temporary password, and a policy hint. `AccountRow` becomes a card
  with avatar + name + badges on line 1 and actions on line 2 (wrapping). Rename and reset
  inputs open inline beneath, full-width.
- **Desktop:** a table-like row is OK if it wraps gracefully at < 900 px.

---

## (e) Phased work plan (small shippable slices)

Each slice is one implementer run plus the reviewer run, per project flow. Tests follow
`docs/conventions.md` › Testing: hook-first, RTL for markup shape, **no snapshots**. "Manual"
means the viewport matrix: 1440×900, 1280×800, 768×1024, 390×844, 375×667, 360×800, real iOS
Safari + Chrome Android, keyboard-only, and 200 % zoom / 320 px reflow.

### Phase 0: decide and verify (no code)
- **S0 Real-browser baseline.** Run the app locally against the local API and capture each view
  at the 3 widths. Confirm or reject F02/F03/F05/F06/F07/F19/F50, and record the result in
  `progress/current.md`. *Accept:* each P0/P1 layout finding is marked confirmed or rejected.
- Owner answers Q1–Q7.

### Phase 1: foundations and quick wins (all OK, low risk)
| Slice | Files | Acceptance | Test |
|---|---|---|---|
| S1 Restore focus ring | `tokens/controlStyles.js`, `LibraryFilters.jsx` | no `outline` override anywhere in `src/` | Vitest source-scan test (same technique as `test_no_extra_accessibility`) banning `outline: 'none'`/`outline:'none'`; manual Tab pass |
| S2 Document baseline | `index.html` (+ `vite-plugins/htmlMessages.js` if needed) | `viewport-fit=cover`; `<meta name="color-scheme" content="light">`; `theme-color` = paper; body margin 0; favicon | `tests/htmlMessages.test.js`-style assertion on built HTML |
| S3 Token additions | `tokens/*.js` | C1 aliases + size/layout/zIndex/lineHeight; literal sizes from F51 replaced | existing token tests + grep test for px literals in `style` (allow-list) |
| S4 FR-UX-03 / empty-value fixes | `ShoppingListView.jsx`, `RecipeDetailView.jsx` | quantity via `formatNumber`; null servings/time render nothing or "—" | RTL: `0.5` renders `0,5`; null servings has no dangling colon |
| S5 `Banner` + error unification | new `ui/Banner.jsx`; 7 views; `ConnectionLostBanner.jsx` | every `error` renders through `Banner`; text in ink; inline validation in ink2 + honey marker | RTL per view: error text present inside the banner element; source-scan: no `color: tokens.color.honey` on text |
| S6 Wrap and overflow | all files in F05/F06/F39 | every multi-control row has `flexWrap:'wrap'`; user text has `overflowWrap:'anywhere'`, flex children `minWidth:0`; `boxSizing` on inputs (F07) | Manual at 320/375 px: no horizontal page scroll on any view |

### Phase 2: forms done right (OK)
| Slice | Files | Acceptance | Test |
|---|---|---|---|
| S7 `Button` + `Field` primitives | `ui/Button.jsx`, `ui/Field.jsx`, `controlStyles.js` | distinct disabled look; `busy` label; min-height token; mobile 16 px inputs | RTL: `busy` → label ends with `…` and click is ignored |
| S8 Native forms on auth screens | `LoginView.jsx`, `SetPasswordView.jsx`, `useSetPasswordForm.js` | `<form onSubmit>`; Enter submits; autocomplete/name/spellCheck attrs; policy hint; mismatch on blur | RTL: `fireEvent.submit(form)` calls `submit`; attribute assertions; hook test for mismatch timing |
| S9 Native forms elsewhere | `ShoppingListView`, `AdminAccountsView`, `AccountRow`, `RulesView`, `RecipeAuthoringForm` | Enter submits; `inputMode` on numbers; every control labelled (F20) | RTL: `getByLabelText` finds every input (ingredient, tool, step included) |
| S10 In-flight state for mutations | `useWeekPlanner.js`, `useLibrary.js`, `useShoppingList.js`, `useRules.js`, `useAdminAccounts.js`, `useRecipeAuthoring.js` | each hook exposes `pending` per action; a 2nd call while pending is a no-op | hook tests: two rapid `submit()` → one `apiFetch` call |

### Phase 3: overlays and flows (OK)
| Slice | Files | Acceptance | Test |
|---|---|---|---|
| S11 `Overlay` on `<dialog>` + `useDialog` | `ui/Overlay.jsx`, `hooks/useDialog.js` | Escape and backdrop close; focus lands in dialog and returns to opener; background inert; sheet on mobile / modal on desktop; sticky title bar; `90dvh`; safe-area padding | RTL with a `showModal`/`close` stub (jsdom lacks them); `keyDown Escape` → `onClose`; manual iOS/Android |
| S12 Migrate ConfirmDialog + RecipeDetail | `ConfirmDialog.jsx`, `RecipeDetailView.jsx`, `useConfirm.js`, `messages/es-ES.js` | `requestConfirm(message, onConfirm, { confirmLabel })`; specific labels ("Eliminar", "Reemplazar", "Quitar") | update `ConfirmDialog.test.jsx` (the backdrop `data-testid` changes); hook test for label |
| S13 Authoring in an overlay with context | `WeekPlannerView.jsx`, `CandidateAuthoring.jsx`, `LibraryView.jsx`, `ShoppingListView.jsx`, messages | form opens in view with title naming the day/slot (or "Nueva receta" / "Editar receta"); dirty-close confirm | RTL: clicking "Añadir plato" renders an overlay whose heading contains the day + slot label; dirty close triggers confirm |
| S14 Rules pin picker in overlay | `RulesView.jsx` | picker opens on "Elegir receta…", selection shown inline | RTL |

### Phase 4: mobile and desktop layout (OK)
| Slice | Files | Acceptance | Test |
|---|---|---|---|
| S15 `useViewport` + shell | `hooks/useViewport.js`, `App.jsx` | bottom tab bar < 600 px; top pills ≥ 600; sticky header; `contentMax`; scroll-to-top on view change; `document.title` per view | hook test with mocked `matchMedia`; RTL: nav renders in the expected place per viewport |
| S16 Summary responsive | `SummaryView.jsx` | list on mobile, `auto-fill` on tablet, 7 columns on desktop; empty slots visible | RTL per viewport prop |
| S17 Week view | `WeekPlannerView.jsx`, `DaySlot.jsx`, `MealCard.jsx`, `WeekSwitcher.jsx` | desktop grid per Q7; mobile day strip + scroll-to-today; compact empty slot; 44 px targets; two-segment week switcher with both ranges | RTL: switcher shows both labels; empty slot renders a single line; manual target-size check |
| S18 Touch targets + list rows | `MealCard`, `DaySlot`, `ShoppingListView`, `RulesView`, `LibraryView`, `AccountRow` | all interactive ≥ 44 px on mobile, ≥ 24 px on desktop; whole-row checkbox label | RTL: clicking item text toggles checkbox; manual measure in DevTools |
| S19 View URL sync (if Q5 = yes) | `hooks/useApp.js` | `#/semana` etc.; Back/Forward work; refresh keeps view | hook test with `history` mocks |

### Phase 5: perceived performance and polish (OK)
| Slice | Files | Acceptance | Test |
|---|---|---|---|
| S20 Skeletons + reduced motion | `LoadingState.jsx`, `useLoadingShimmer.js`, views | layout-shaped skeleton per view; animation off under `prefers-reduced-motion` | hook test: interval not started when the reduce query matches |
| S21 Empty states with CTA | `EmptyState.jsx`, views, messages | each FR-UX-05 empty state has guidance + one action | RTL: action button present and wired |
| S22 Dates and copy | `labels.js`, `WeekLabel.jsx`, `locale.js`, messages | `timeZone:'UTC'` on day/date formatters; `formatRange` "28 sept – 4 oct 2026"; capitalised day titles; specific copy | unit tests run under `TZ=America/New_York` |
| S23 Fonts | `fonts.js` | `display:'swap'` descriptor; preload the 2 body/heading faces | `fonts.test.js` extension |
| S24 Primitive consolidation | auth views, icons, cards | one card, one icon set, one submit style | grep test: no local `submitButtonStyle`/duplicate icon fns |

### Phase 6: gated work (needs owner decision)
- **S25 [CONV] Minimal base stylesheet**, about 30 lines (`index.html <style>` or
  `src/base.css`): `*{box-sizing:border-box}`, `:focus-visible` ring with `focusRing`,
  `:hover`/`:active` for the `Button` variants (by `data-variant`), and
  `@media (prefers-reduced-motion)`. Needs an approved `design.md` deviation.
- **S26 [REQ] WCAG 2.2 AA layer**: `aria-label` on glyph buttons, `aria-current="page"` on nav,
  `aria-live="polite"` on Banner/AI progress, contrast fixes for `ink3`/`olive`/`line2` (F44,
  F45), a danger token, and `vitest-axe` in tests. Needs a new Part lifting FR-UX-07/G-62 and an
  edit to `tests/test_no_extra_accessibility.test.js`.

---

## (f) Risks, out of scope, open questions

### Risks
- **Inline-only styling.** Without S25, hover/focus-visible/media must go through JS
  (`matchMedia` re-renders). That's acceptable for 4 layout switches but not for per-element
  hover. Keep the JS breakpoint surface tiny (one `useViewport` in `App`).
- **`<dialog>` in jsdom.** `showModal()`/`close()` aren't implemented, so tests need a small
  prototype stub in a setup file. Several existing tests rely on `data-testid` backdrops
  (`ConfirmDialog.test.jsx`, `RecipeDetailView.test.jsx`, `*.closeButton.test.jsx`) and will
  need updating in the same slice.
- **R-gated disabled submits.** Some disabled-until-valid behaviour is spec'd (e.g. R27
  set-password mismatch, `canSave*` in rules). The rubric prefers enabled + validate-on-submit.
  Keep the spec'd gating, but make the disabled state *visible and explained*, unless the owner
  lifts it.
- **Polling + overlays.** Authoring overlays must not unmount when a poll refreshes the week.
  `authoringTarget` already lives in the hook, so verify in S13.
- **Mutation testing** (reviewer, Level 5) will hit the new primitives. Keep their logic in
  hooks so it can be killed by hook tests.
- **Uncommitted-work safety.** Slices touch many shared files (`controlStyles.js`, messages).
  Run them sequentially, not in parallel.

### Out of scope
- Dark theme: no requirement asks for one. Pin `color-scheme: light` instead (S2).
- Offline support, print/export, presence indicators (rejected in `gaps_and_resolutions.md`
  Part H). An i18n framework (single constant locale).
- Screens not in `useApp.VIEWS` (archive/history FR-ARCH, whole-week AI generation progress
  FR-AI-12): not audited, because they aren't reachable from the current nav.
- Removing `PlaceholderView.jsx` (scaffold artefact with its own test). Leave it.

### Open questions for the owner
1. **Q1 [CONV]:** Approve a ~30-line base stylesheet (S25) for `:focus-visible`, hover and
   reduced-motion, or stay strictly inline and accept no hover feedback?
2. **Q2 [REQ]:** Lift FR-UX-07 partially to a WCAG 2.2 AA subset (2.4.7 focus visible, 2.5.8
   target size, 1.4.3/1.4.11 contrast, 4.1.2 names for glyph buttons, 4.1.3 status messages),
   or keep browser defaults only?
3. **Q3:** Mobile nav as a bottom tab bar (prototype idiom) or as horizontally scrollable top
   pills?
4. **Q4:** Mobile week view as a day strip with scroll-to-day (proposed) or a true
   one-day-at-a-time pager?
5. **Q5:** Sync the active view to the URL hash with the History API (no router library), so
   Back and refresh work?
6. **Q6:** Add a `danger` colour token outside the 18-colour prototype lift, for destructive
   buttons?
7. **Q7:** Desktop week grid: a strict 7-column week, or the current fluid wrap tuned to 4 + 3?

---

## Owner decisions (2026-10-01)

- Start with the OK-tagged slices only (P0/P1 first); CONV/REQ slices wait for their paperwork.
- **Q1 (CONV):** approved — a ~30-line base stylesheet for `:focus-visible`, hover, reduced-motion. Still needs the `design.md` exception written before the CONV slices.
- **Q2 (REQ):** owner approves lifting FR-UX-07 to the WCAG 2.2 AA subset listed in Q2. Written as Part AC (G-93); was: needs a new lettered Part in `docs/gaps_and_resolutions.md` (struck-through text, never deleted).
- **Q3:** mobile nav = bottom tab bar. **Q4:** mobile week = day strip with scroll-to-day. **Q5:** yes, view synced to URL hash (History API, no router lib). **Q6:** yes, add a `danger` colour token.
- **Q7:** accepted — strict 7-column week at ≥1280 px, fluid 4 + 3 at 768–1279 px, day strip below 768 px.
- **Q2 written 2026-10-01:** `docs/gaps_and_resolutions.md` Part AC / G-93; `FR-UX-07` amended (struck through). Implementer must narrow `frontend/tests/test_no_extra_accessibility.test.js` and refresh `specs/frontend_spa/`.
