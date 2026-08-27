# Implementation report — feature 1 `project_scaffold`, Part B (frontend toolchain root)

Scope: `frontend/` only. Backend (`backend/`) and shared root files (`.pre-commit-config.yaml`,
`init.sh`) are owned by parallel passes and were not touched.

## 1. File tree created

```
frontend/
  .prettierignore
  .prettierrc.json
  eslint.config.js
  index.html
  package.json
  package-lock.json
  vite.config.js
  src/
    main.jsx
    PlaceholderView.jsx
    locale.js
    messages/
      es-ES.js
      index.js
    tokens/
      colors.js
      spacing.js
      typography.js
      breakpoints.js
      index.js
  tests/
    .gitkeep          (pre-existing, left in place)
    PlaceholderView.test.jsx
    locale.test.js
  node_modules/        (installed, not part of source)
```

## 2. Acceptance criteria -> files

| Acceptance criterion (feature 1, frontend half) | Satisfied by |
|---|---|
| `frontend/` own toolchain root, private ESM `package.json`, untouched by Python gates | `frontend/package.json` (`"private": true`, `"type": "module"`); nothing under `backend/` references it |
| React + react-dom only runtime deps; Vite/Vitest/ESLint/Prettier as devDependencies | `frontend/package.json` `dependencies` vs `devDependencies` (see section 5) |
| `frontend/src/` and `frontend/tests/` exist; `src/messages/` and `src/tokens/` are real modules | `src/messages/es-ES.js` (2 UPPER_SNAKE keys), `src/tokens/{colors,spacing,typography,breakpoints,index}.js` |
| Every user-facing string is UPPER_SNAKE in the messages module | `src/messages/es-ES.js` — `SCAFFOLD_PLACEHOLDER_TITLE`, `SCAFFOLD_PLACEHOLDER_BODY`, both consumed by `PlaceholderView.jsx`, none inlined |
| Every colour, spacing, font size and breakpoint is a named token | `src/tokens/index.js` aggregates `tokens.color`, `tokens.space`, `tokens.fontSize`, `tokens.breakpoint`; `PlaceholderView.jsx` references only `tokens.*`, no literals |
| Locale exported as a constant `'es-ES'` used by `Intl.DateTimeFormat`/`Intl.NumberFormat`; not a runtime setting; no i18n framework | `src/locale.js` — `export const LOCALE = 'es-ES'`, `formatDate`/`formatNumber` wrap `Intl`; covered by `tests/locale.test.js` |
| `package.json` declares no CSS framework/component library/CSS-in-JS/templating engine/stylesheet | `frontend/package.json` — only the deps listed in section 5; no `.css` file anywhere under `frontend/` |
| Prettier + ESLint lint/format `frontend/` only, both green, both devDependencies; ESLint flat config, `eslint-config-prettier` last; plain JS/ESM, JSX enabled, no TypeScript parser | `eslint.config.js` (flat config, array order ends with `prettierConfig`), `.prettierrc.json`/`.prettierignore`; verification output in section 4 |
| Two toolchains mutually isolated; JS gate never reads `backend/`; neither reaches `prototypes/` | `eslint.config.js` `ignores: ['dist/**', 'node_modules/**']`; empirically verified in section 4.3 — every file ESLint/Prettier visited resolves under `frontend/`. **Corrected 2026-08-18:** this row originally also listed `'../backend/**'` and `'../prototypes/**'`. Those entries were **inert** — flat-config `ignores` resolve relative to the config's base path and never match above it — and were removed in the `gga` fix round (`progress/impl_gga_findings_fix.md`, finding 3). The isolation guarantee comes from **cwd-scoping**, which is what `eslint.config.js:1-9` now says. |
| React idiomatic (function components + hooks, JSX); Vite build tool/dev server; minimal `index.html`; `src/main.jsx` mounts a single placeholder component; NO product screens, no routing, no API layer | `index.html`, `src/main.jsx` (mounts `<PlaceholderView />` only), `src/PlaceholderView.jsx` (one function component, no router, no `fetch`) |
| Vitest test runner over `frontend/` only; at least one smoke test passing; behaviour through state, never whole-view snapshots | `vite.config.js` `test.include: ['tests/**/*.test.{js,jsx}']`; `tests/PlaceholderView.test.jsx` and `tests/locale.test.js` — both assert specific string/format content, no snapshot API used |
| Plain JS/ESM throughout; no TypeScript, no tsconfig, no type-checking gate | No `.ts`/`.tsx`/`tsconfig.json` anywhere under `frontend/`; ESLint uses `espree` (default parser) with `ecmaFeatures.jsx: true`, not `@typescript-eslint/parser` |

`./init.sh` itself was **not** modified (owned by the shared-root pass); it does not
yet run a frontend gate, so this report's section 4 stands in for that gate per the
"Verification before you report" instructions.

## 3. Dependency list, one line each

Runtime (`dependencies`):

| Package | Version | Why |
|---|---|---|
| `react` | ^19.2.8 | The framework, decided in `docs/architecture.md` §1.1 (P7, closed 2026-08-17) |
| `react-dom` | ^19.2.8 | React's DOM renderer; `createRoot` bootstrap in `main.jsx` |

Dev (`devDependencies`):

| Package | Version | Why |
|---|---|---|
| `vite` | ^8.2.1 | Build tool and dev server, decided in §1.1 |
| `@vitejs/plugin-react` | ^6.0.5 | Vite's JSX/Fast-Refresh transform for React — required to build `.jsx` at all |
| `vitest` | ^4.1.10 | Test runner, decided in `docs/conventions.md` § Testing |
| `eslint` | ^9.39.5 | Linter, "industry-standard pair" chosen by the human 2026-08-17 |
| `@eslint/js` | ^9.39.5 | ESLint's own recommended flat-config ruleset (`js.configs.recommended`) |
| `eslint-plugin-react` | ^7.37.5 | React/JSX-specific lint rules (flat config), including the `jsx-runtime` config so `React` need not be in scope |
| `eslint-plugin-react-hooks` | ^7.1.1 | Enforces the Rules of Hooks — load-bearing given the hook/component split in `docs/conventions.md` |
| `eslint-config-prettier` | ^10.1.8 | Disables ESLint's formatting-related rules so Prettier is the single source of truth; applied last in `eslint.config.js` |
| `prettier` | ^3.9.6 | Formatter, paired with ESLint |

No CSS framework, component library, CSS-in-JS library, templating engine, stylesheet,
router, HTTP client, i18n framework, TypeScript, or `@testing-library/*` /`jsdom` was
added. `docs/conventions.md` § Testing does not call for a DOM testing library by name —
it says "test the hook directly wherever the logic lives there... reach for rendering
only when the assertion is genuinely about what the component produces." The placeholder
has no hook, so the smoke test renders it with `react-dom/server`'s `renderToStaticMarkup`
(already inside `react-dom`, zero extra dependency) and asserts specific text content —
never `jsdom`, never a snapshot.

npm resolved `eslint@10` / `@eslint/js@10` by default; both were pinned to `^9` because
`eslint-plugin-react@7.37.5`'s peer range is `eslint@^3 || ... || ^9.7` and does not yet
accept ESLint 10 (verified: `npm install` failed with an `ERESOLVE` peer conflict before
the pin, succeeded cleanly after — see the transcript this report is based on).

## 4. Verification — verbatim output

### 4.1 `npm install`

```
up to date, audited 291 packages in 1s

129 packages are looking for funding
  run `npm fund` for details

found 0 vulnerabilities
```

### 4.2 `npx prettier --check .`

```
Checking formatting...
All matched files use Prettier code style!
```

### 4.3 `npx eslint .`

```
(no output — exit code 0)
```

Every file ESLint actually visited (`npx eslint . --format json`), confirmed to resolve
entirely under `frontend/`:

```
frontend\eslint.config.js
frontend\src\PlaceholderView.jsx
frontend\src\locale.js
frontend\src\main.jsx
frontend\src\messages\es-ES.js
frontend\src\messages\index.js
frontend\src\tokens\breakpoints.js
frontend\src\tokens\colors.js
frontend\src\tokens\index.js
frontend\src\tokens\spacing.js
frontend\src\tokens\typography.js
frontend\tests\PlaceholderView.test.jsx
frontend\tests\locale.test.js
frontend\vite.config.js
```

Prettier's `--log-level debug` run shows the same: every "resolve config from" line
points at a path under `frontend/`, none under `backend/` or `prototypes/`.

### 4.4 `npx vitest run`

```
 RUN  v4.1.10 C:/Users/Sergio/projects/proyecto-final-curso-aws/frontend

 Test Files  2 passed (2)
      Tests  4 passed (4)
   Start at  12:22:29
   Duration  210ms (transform 78ms, setup 0ms, import 126ms, tests 20ms, environment 0ms)
```

### 4.5 `npx vite build`

```
vite v8.2.1 building client environment for production...
transforming...✓ 22 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                  0.33 kB │ gzip:  0.24 kB
dist/assets/index-BTyO_1bt.js  191.35 kB │ gzip: 60.48 kB

✓ built in 74ms
```

The `dist/` output was removed after this check — it is a build artifact, not source.

## 5. The 13/18 colour tokens and where they came from

`docs/frontend_prototype.md` §2.4 and §6.1 describe "the 13 colour custom properties" on
`prototypes/wireframe/Sobremesa.dc.html:33` as the thing to lift verbatim. I extracted
that line directly and counted the actual custom properties present:

```
--paper --paper-2 --surface --surface-2 --ink --ink-2 --ink-3 --line --line-2
--terra --terra-deep --terra-soft --olive --olive-soft --aub --aub-soft --honey --honey-soft
```

That is **18** distinct `--name:#hex` pairs, not 13 — the documentation's count appears to
be off (possibly counting only the 13 "primary" names before the `-2`/`-3`/`-deep`/`-soft`
variants, but the line itself carries 18). Per the "verify before stating" convention, I
did not silently correct the doc; I lifted every property that is actually on that line,
unmodified, into `src/tokens/colors.js` (camelCase key, same hex value):

`paper`, `paper2`, `surface`, `surface2`, `ink`, `ink2`, `ink3`, `line`, `line2`, `terra`,
`terraDeep`, `terraSoft`, `olive`, `oliveSoft`, `aub`, `aubSoft`, `honey`, `honeySoft`.

This discrepancy is worth a human look at `docs/frontend_prototype.md` §2.4/§6.1, but it
does not block this feature — the source of truth (the actual prototype line) was used,
and all 18 values are cited with their provenance in a comment in `colors.js`.

## 6. Spacing, font-size and breakpoint scales — authored, not lifted

`docs/frontend_prototype.md` §2.4 is explicit that the prototype's 24 font sizes and 91
paddings are drift, not a system, and must not be copied. I authored three small scales
instead, each documented in its own module:

- **Spacing** (`src/tokens/spacing.js`): 6 steps on a 4px/8px grid — `4, 8, 16, 24, 32,
  48`. Doubling steps keep the scale legible and match the flex/grid gap sizes the
  fluid-first layout in `docs/conventions.md` needs (inline gaps through section spacing).
- **Font size** (`src/tokens/typography.js`): 6 steps on an approximate 1.25 (major third)
  ratio from a 16px body — `12, 14, 16, 20, 25, 31`. Enough range for a metadata label
  through a page title without inventing a size per component.
- **Breakpoints** (`src/tokens/breakpoints.js`): 2 thresholds — `tablet: 600`,
  `desktop: 1024`, for use with `window.matchMedia` per the responsive-constraint section
  of `docs/conventions.md`. Two is deliberate: the only genuine breakpoint the requirements
  name is the week grid collapsing to a day-by-day view on narrow phones; a third value
  would not correspond to any known layout change yet, and can be added when
  `frontend_spa` (feature 20) actually needs it.

## 7. What I could not do / deferred

- `./init.sh` was not modified — detecting the frontend toolchain root and wiring its gate
  in (with the WARN-while-absent fallback) is explicitly the shared-root pass's job per
  the task instructions, and `init.sh` is also off-limits per the implementer's hard rules
  without the leader's explicit go-ahead.
- `.pre-commit-config.yaml` was not touched, same reason.
- The colour-token count discrepancy in `docs/frontend_prototype.md` (says 13, the actual
  line has 18) is flagged above for the human/leader; I did not edit that frozen-adjacent
  doc.
- No product screens, router, or API layer were added — out of scope by the task
  instructions and by `docs/architecture.md` §1.1 (feature 20 `frontend_spa` remains
  blocked on feature 16).

## 8. Post-review fix — `index.html` title leaked outside the messages module

**Defect (review, low severity):** `frontend/index.html:6` hardcoded
`<title>Planificador semanal</title>` — a Castilian Spanish user-facing string living
outside `src/messages/`, violating the unconditional acceptance criterion that every
user-facing string is UPPER_SNAKE in the messages module (`FR-UX-01`, `FR-UX-03`).

**Fix:**

1. Added `APP_TITLE: 'Planificador semanal'` to `src/messages/es-ES.js` (same wording as
   before, no new product name invented).
2. Replaced the literal in `frontend/index.html` with the placeholder `%APP_TITLE%`.
3. Added `frontend/vite-plugins/htmlMessages.js` — a small `transformIndexHtml` plugin
   (`html-messages`) that does `html.replace('%APP_TITLE%', MESSAGES.APP_TITLE)`. Wired
   into `frontend/vite.config.js`'s `plugins` array alongside `react()`. No new
   dependency — plain JS/ESM, and `transformIndexHtml` runs for both `vite build` and
   the dev server, so both paths resolve the same way.
4. Added `frontend/tests/htmlMessages.test.js`: calls the plugin's
   `transformIndexHtml` directly on a fixture HTML string, asserts the output contains
   `<title>Planificador semanal</title>` and no longer contains the `%APP_TITLE%`
   placeholder. Not a snapshot of the whole document.
5. Verified against the real build: ran `npx vite build` and read the produced
   `dist/index.html`, which showed `<title>Planificador semanal</title>` resolved
   correctly; `dist/` was deleted immediately after.

**Second review observation — left as-is, on instruction.** `frontend/.prettierignore`
has no explicit `../prototypes/**` entry. Not added: Prettier ignore patterns resolve
relative to the ignore file, so `../prototypes/**` would almost certainly be inert, and
an inert pattern reads as a false guarantee. The real guarantee — no gate ever
constructs a path outside `frontend/` — is verified empirically in section 4.3 above.

### Fresh verification (post-fix)

`npx prettier --check .`

```
Checking formatting...
All matched files use Prettier code style!
```

`npx eslint .` — exit code 0, no output. Confirmed via `--format json` that the new
`vite-plugins/htmlMessages.js` and `tests/htmlMessages.test.js` were linted and passed,
alongside every previously listed file, all still resolving under `frontend/`.

`npx vitest run`

```
 RUN  v4.1.10 C:/Users/Sergio/projects/proyecto-final-curso-aws/frontend

 Test Files  3 passed (3)
      Tests  5 passed (5)
   Start at  12:40:25
   Duration  204ms (transform 92ms, setup 0ms, import 155ms, tests 23ms, environment 0ms)
```

`npx vite build`

```
vite v8.2.1 building client environment for production...
transforming...✓ 22 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                  0.33 kB │ gzip:  0.24 kB
dist/assets/index-WYb3Sio3.js  191.38 kB │ gzip: 60.48 kB

✓ built in 77ms
```

`dist/` deleted after inspection (confirmed `<title>Planificador semanal</title>` was
present, correctly resolved from `%APP_TITLE%`).

`./init.sh` from the repo root, re-run after the fix: full green —
`ruff format`, `ruff check`, `mypy`, `pytest`, `prettier --check`, `eslint`, `vitest`
all `[OK]`, ending in `Environment ready. You can start working.` (exit code 0). This
run also confirms the shared-root pass has since wired the frontend gates into
`init.sh`, which was not the case when this report's section 4 was first written.
