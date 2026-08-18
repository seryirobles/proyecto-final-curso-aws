# Fix: gga non-blocking observations (`$` substitution hazard, literal `0` spacing)

Two isolated fixes from non-blocking observations in a passing `gga` review,
requested by the human before committing. No feature in `feature_list.json`
was touched; this is a maintenance fix to already-merged scaffold code.

## Fix 1 — `frontend/vite-plugins/htmlMessages.js:14` — `$` substitution hazard

### Before

```js
transformIndexHtml(html) {
  return html.replace('%APP_TITLE%', MESSAGES.APP_TITLE);
},
```

`String.prototype.replace(pattern, replacementString)` treats a **string**
replacement specially: `$&`, `` $` ``, `$'`, `$$` and `$<name>` are expanded
as pattern-matching tokens. Any message value containing `$` would have been
silently mangled. Unreachable today (`APP_TITLE` is `'Planificador semanal'`),
but latent and permanent once any message value contains `$`.

### After

```js
transformIndexHtml(html) {
  // Replacement is a callback, not a string: String.replace interprets
  // `$&`, `$'`, `` $` ``, `$$` and `$<name>` as special patterns when the
  // replacement is a string, which would silently mangle any message
  // value containing `$`. A callback's return value is used literally.
  return html.replace('%APP_TITLE%', () => MESSAGES.APP_TITLE);
},
```

The file substitutes only one placeholder (`%APP_TITLE%`), so no other call
site needed the same treatment.

### Regression test added — `frontend/tests/htmlMessages.test.js`

```js
it('substitutes a message value containing `$&` literally, without expanding it', () => {
  const originalTitle = MESSAGES.APP_TITLE;
  MESSAGES.APP_TITLE = "Precio: $& / $' descuento";

  try {
    const plugin = htmlMessages();
    const input = '<html><head><title>%APP_TITLE%</title></head></html>';
    const output = plugin.transformIndexHtml(input);

    expect(output).toContain(`<title>${MESSAGES.APP_TITLE}</title>`);
    expect(output).not.toContain('%APP_TITLE%');
  } finally {
    MESSAGES.APP_TITLE = originalTitle;
  }
});
```

**What it proves**: with a string replacement, `$&` in the replacement value
expands to "the matched substring" (`%APP_TITLE%`), so the output would
either duplicate the placeholder text or otherwise diverge from the literal
message value. Asserting the output contains the message value *exactly as
written* (including `$&` and `$'`) fails against the old string-based
`replace` and passes against the callback-based fix — this is what stops the
bug from coming back.

## Fix 2 — `frontend/src/tokens/spacing.js` + `frontend/src/PlaceholderView.jsx` — literal `0`

### Before

`spacing.js`:

```js
export const SPACE = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  xxl: '48px',
};
```

`PlaceholderView.jsx` (two occurrences, not three — verified against the
current file):

```jsx
<h1 style={{ fontSize: tokens.fontSize.xl, margin: 0 }}>
...
<p style={{ fontSize: tokens.fontSize.md, margin: 0, color: tokens.color.ink2 }}>
```

### After

`spacing.js` — new `none` entry first in the scale, matching the existing
string-value convention (all other steps are `'<n>px'` strings):

```js
export const SPACE = {
  none: '0',
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  xxl: '48px',
};
```

`PlaceholderView.jsx` — both literal `margin: 0` occurrences replaced with
`tokens.space.none`, same dotted access style as every other token use in the
file:

```jsx
<h1 style={{ fontSize: tokens.fontSize.xl, margin: tokens.space.none }}>
  {MESSAGES.SCAFFOLD_PLACEHOLDER_TITLE}
</h1>
<p
  style={{
    fontSize: tokens.fontSize.md,
    margin: tokens.space.none,
    color: tokens.color.ink2,
  }}
>
  {MESSAGES.SCAFFOLD_PLACEHOLDER_BODY}
</p>
```

The `<p>` style object was reflowed to multiple lines by Prettier once the
line exceeded the configured length after the token name got longer; no
other spacing step's value was changed and the tokens module was not
restructured beyond the one new leading entry.

## Verification — verbatim output

### 1. `npx --no -- vitest run`

```
 RUN  v4.1.10 C:/Users/Sergio/projects/proyecto-final-curso-aws/frontend

 Test Files  3 passed (3)
      Tests  6 passed (6)
   Start at  14:42:10
   Duration  286ms (transform 155ms, setup 0ms, import 241ms, tests 28ms, environment 0ms)
```

(includes the new regression test in `tests/htmlMessages.test.js`, and the
pre-existing test in the same file still passes)

### 2. `npx --no -- eslint .`

```
(no output, exit 0)
```

### 3. `npx --no -- prettier --check .`

```
Checking formatting...
All matched files use Prettier code style!
```

### 4. `npx --no -- vite build`

```
vite v8.2.1 building client environment for production...
transforming...✓ 22 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                  0.33 kB │ gzip:  0.24 kB
dist/assets/index-DJwSoRXh.js  191.42 kB │ gzip: 60.50 kB

✓ built in 149ms
```

`dist/index.html` contents confirmed to include `<title>Planificador semanal</title>`.
`dist/` deleted afterwards (`rm -rf dist`).

### 5. `./init.sh` (repo root)

```
── 1. Environment ──────────────────────────────────────
[OK]    python -> 3.14.6 via 'python'
[OK]    uv -> uv 0.11.7 (9d177269e 2026-04-15 x86_64-pc-windows-msvc)
[OK]    npm -> 12.0.2

── 2. Harness base files ───────────────────────────────
[OK]    Found AGENTS.md
[OK]    Found CLAUDE.md
[OK]    Found CHECKPOINTS.md
[OK]    Found feature_list.json
[OK]    Found progress/current.md
[OK]    Found docs/architecture.md
[OK]    Found docs/conventions.md
[OK]    Found docs/specs.md
[OK]    Found docs/verification.md

── 3. Frozen requirement docs ──────────────────────────
[OK]    Found docs/requirements.md
[OK]    Found docs/app_user_stories.md
[OK]    Found docs/coverage_analysis.md
[OK]    Found docs/gaps_and_resolutions.md
[OK]    Found docs/gaps_pending_stakeholders.md

── 4. feature_list.json, specs and guardrails ──────────
[OK]    feature_list.json valid (23 features - blocked: 9, done: 1, pending: 13)
[OK]    Specs present for every non-pending sdd feature
[OK]    No agent-generated IaC or CI files
[OK]    Requirement coverage: all 103 FR/NFR ids covered by features
[OK]    Next actionable feature: 2 - week_calendar

── 5. Quality gates ────────────────────────────────────
[OK]    ruff format
[OK]    ruff check
[OK]    mypy
.                                                                        [100%]
1 passed in 0.02s
[OK]    pytest (unit + contract, no AWS)
[OK]    prettier --check
[OK]    eslint
[OK]    vitest

── 6. Summary ──────────────────────────────────────────
[OK]    Environment ready. You can start working.
```

Exit code 0, fully green.

## Files touched

- `frontend/vite-plugins/htmlMessages.js`
- `frontend/src/tokens/spacing.js`
- `frontend/src/PlaceholderView.jsx`
- `frontend/tests/htmlMessages.test.js`

No other files were modified. Git staging was left untouched (`git status`
confirms only these four files show as modified on top of the pre-existing
staged scaffold changes).

## Follow-up — docstring drift after Fix 2

The coordinator flagged that `spacing.js`'s docstring still said "Six steps
on a 4px/8px grid" after `SPACE` grew a seventh entry (`none`). The count no
longer matched the comment.

### Before

```js
/**
 * Spacing scale, authored deliberately for this project (not lifted from the
 * prototype, which has 91 distinct padding values — drift, not a system; see
 * docs/frontend_prototype.md section 2.4).
 *
 * Six steps on a 4px/8px grid, the smallest scale that still separates
 * "tight" (inline gaps, badge padding) from "loose" (section spacing) without
 * inventing a value per component.
 */
```

### After

```js
/**
 * Spacing scale, authored deliberately for this project (not lifted from the
 * prototype, which has 91 distinct padding values — drift, not a system; see
 * docs/frontend_prototype.md section 2.4).
 *
 * Six steps on a 4px/8px grid, the smallest scale that still separates
 * "tight" (inline gaps, badge padding) from "loose" (section spacing) without
 * inventing a value per component — plus an explicit `none` for zero, so that
 * every spacing value in a component is a named token with no literal `0`
 * (the acceptance criterion is unconditional).
 */
```

No token value was changed; only the comment was corrected. Only
`frontend/src/tokens/spacing.js` was touched for this follow-up.

### Re-verification — verbatim output

`npx --no -- vitest run`:

```
 RUN  v4.1.10 C:/Users/Sergio/projects/proyecto-final-curso-aws/frontend

 Test Files  3 passed (3)
      Tests  6 passed (6)
   Start at  14:44:07
   Duration  207ms (transform 98ms, setup 0ms, import 167ms, tests 22ms, environment 0ms)
```

`npx --no -- eslint .` and `npx --no -- prettier --check .`:

```
npm notice run planner-frontend@0.0.0 npx
npm notice run eslint .
---EXIT:0---
npm notice run planner-frontend@0.0.0 npx
npm notice run prettier --check .
Checking formatting...
All matched files use Prettier code style!
---EXIT:0---
```

`./init.sh` (repo root):

```
── 1. Environment ──────────────────────────────────────
[OK]    python -> 3.14.6 via 'python'
[OK]    uv -> uv 0.11.7 (9d177269e 2026-04-15 x86_64-pc-windows-msvc)
[OK]    npm -> 12.0.2

── 2. Harness base files ───────────────────────────────
[OK]    Found AGENTS.md
[OK]    Found CLAUDE.md
[OK]    Found CHECKPOINTS.md
[OK]    Found feature_list.json
[OK]    Found progress/current.md
[OK]    Found docs/architecture.md
[OK]    Found docs/conventions.md
[OK]    Found docs/specs.md
[OK]    Found docs/verification.md

── 3. Frozen requirement docs ──────────────────────────
[OK]    Found docs/requirements.md
[OK]    Found docs/app_user_stories.md
[OK]    Found docs/coverage_analysis.md
[OK]    Found docs/gaps_and_resolutions.md
[OK]    Found docs/gaps_pending_stakeholders.md

── 4. feature_list.json, specs and guardrails ──────────
[OK]    feature_list.json valid (23 features - blocked: 9, done: 1, pending: 13)
[OK]    Specs present for every non-pending sdd feature
[OK]    No agent-generated IaC or CI files
[OK]    Requirement coverage: all 103 FR/NFR ids covered by features
[OK]    Next actionable feature: 2 - week_calendar

── 5. Quality gates ────────────────────────────────────
[OK]    ruff format
[OK]    ruff check
[OK]    mypy
.                                                                        [100%]
1 passed in 0.02s
[OK]    pytest (unit + contract, no AWS)
[OK]    prettier --check
[OK]    eslint
[OK]    vitest

── 6. Summary ──────────────────────────────────────────
[OK]    Environment ready. You can start working.
```

Exit code 0, fully green.
