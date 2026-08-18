# Review — feature 1 (project_scaffold)

**Verdict:** APPROVED

Feature 1 (`sdd: false`, `covers: []`) has no FR-* traceability chain and no
`specs/` folder requirement (CHECKPOINTS C6 only applies to non-pending `sdd:
true` features). All 20 acceptance criteria in `feature_list.json` were
independently re-verified against the files and by re-running commands, not
accepted from the three implementation reports. `./init.sh` is fully green.
No defects found; two low-severity observations recorded below (not
blocking).

## Acceptance criteria (feature_list.json, feature 1)

| # | Criterion (short) | Verdict | Evidence |
|---|---|---|---|
| 1 | backend/pyproject.toml uv workspace root, shared config | PASS | backend/pyproject.toml:1-30 - [tool.uv.workspace] members = ["core","lambda_api","lambda_ai"], shared [tool.ruff]/[tool.mypy]/[tool.pytest.ini_options] |
| 2 | backend/core = planner-core, zero runtime deps, src-layout, domain/application/ports each with __init__.py | PASS | backend/core/pyproject.toml:6 dependencies = []; backend/core/src/planner_core/{domain,application,ports}/__init__.py all present, docstring-only |
| 3 | lambda_api/lambda_ai depend on planner-core only | PASS | backend/lambda_api/pyproject.toml:6-8,17-18, backend/lambda_ai/pyproject.toml:6-8,17-18 - dependencies = ["planner-core"], [tool.uv.sources] planner-core = { workspace = true }; grep across all 3 members shows no other deps |
| 4 | ruff configured (format+check, line-length 100), passing | PASS | uv run ruff format --check . reports 7 files already formatted; uv run ruff check . reports All checks passed; independently re-verified the extend trap: wrote a 102-char line into core/src/planner_core/_scratch_lint_test.py, ruff check correctly flagged E501 Line too long (102 > 100), scratch file deleted after. All 3 members declare extend = "../pyproject.toml" (core/pyproject.toml:13, lambda_api/pyproject.toml:15, lambda_ai/pyproject.toml:15) |
| 5 | mypy strict, passing | PASS | uv run mypy . reports Success, no issues found in 7 source files; [tool.mypy] strict = true (backend/pyproject.toml:23); no type-ignore comment anywhere in backend/ (grep); also re-ran mypy scoped to lambda_api and lambda_ai individually, both green |
| 6 | pytest with aws marker registered and deselected by default; smoke test passing | PASS | backend/pyproject.toml:26-30 registers aws marker, addopts deselects it; uv run pytest -q -m "not aws" reports 1 passed; backend/core/tests/test_scaffold.py asserts concrete __name__ values on all 3 subpackages, not a bare import |
| 7 | pre-commit config runs ruff format/check and mypy on staged files | PASS | .pre-commit-config.yaml:33-57; reproduced the hollow-green trap: pre-commit run --all-files reports all 5 hooks Skipped (operates on tracked files, nearly everything is untracked); re-ran with explicit real paths and all 5 hooks genuinely Passed |
| 8 | uv export --package planner-api --no-dev resolves without the AI SDK | PASS | closure is core plus lambda_api only, no third-party packages, legitimate since neither Lambda has adapters yet (P1/P4 pending, features 16/17 blocked); re-ran --package planner-ai --no-dev too, same shape |
| 9 | frontend/ own toolchain root, private ESM package.json; React+react-dom only runtime deps; Vite/Vitest/ESLint/Prettier devDeps | PASS | frontend/package.json:3,5,14-28 - private: true, type: module, dependencies = react/react-dom only, everything else in devDependencies |
| 10 | src/messages/ and src/tokens/ real modules; every user-facing string UPPER_SNAKE in messages; every colour/spacing/font-size/breakpoint a named token | PASS | frontend/src/messages/es-ES.js:8-9 (SCAFFOLD_PLACEHOLDER_TITLE, SCAFFOLD_PLACEHOLDER_BODY); frontend/src/PlaceholderView.jsx:12-27 references only tokens.* and MESSAGES.*, zero literals; frontend/src/tokens/{colors,spacing,typography,breakpoints,index}.js all real, non-placeholder modules |
| 11 | Locale exported as constant es-ES used by Intl.DateTimeFormat/Intl.NumberFormat; not a runtime setting; no i18n framework | PASS | frontend/src/locale.js:6-14; no i18n package in package.json; frontend/tests/locale.test.js asserts es-ES comma-decimal formatting concretely |
| 12 | package.json declares no CSS framework/component library/CSS-in-JS/templating engine/stylesheet | PASS | frontend/package.json deps list (9 total); no .css file found under frontend/ |
| 13 | Prettier and ESLint lint/format frontend/ only, both passing, both devDeps; flat config, eslint-config-prettier applied last; plain JS/ESM, JSX enabled, no TS parser | PASS | npx prettier --check . and npx eslint . both exit 0 (re-run independently); frontend/eslint.config.js:51 - prettierConfig is the last array entry; no TypeScript-ESLint parser anywhere |
| 14 | Two toolchains mutually isolated; Python gates never read frontend/; JS gate never reads backend/; neither reaches prototypes/ | PASS (see note) | ~~eslint.config.js:10 ignores ../backend/** and ../prototypes/**~~ **AMENDED 2026-08-17 (post-review):** those two entries were **inert** — ESLint flat-config `ignores` match relative to the config's base path and never begin with `../`. They were removed after a `gga` finding; the isolation was always delivered by cwd-scoping, which is what the note below already identified. npx eslint on a prototypes file returns "File ignored because outside of base path", exit 0; .pre-commit-config.yaml top-level exclude of prototypes/ verified, all 5 hooks Skipped on prototype files. Minor observation, not a fail: frontend/.prettierignore has no explicit ../prototypes/** entry (unlike eslint.config.js); npx prettier --check run directly against a prototypes path does report style issues on that file. No real gate (init.sh, pre-commit, npm run format) ever constructs that path, so nothing in this feature actually reaches prototypes/, but Prettier isolation rests on cwd-scoping alone rather than an explicit ignore |
| 15 | pre-commit runs the JS gate on staged frontend files alongside the Python hooks | PASS | .pre-commit-config.yaml:59-77 - eslint/prettier hooks in the same repos list as the Python hooks |
| 16 | React idiomatic (function components and hooks, JSX); Vite build tool; minimal index.html; src/main.jsx mounts single placeholder; no product screens/routing/API layer | PASS | frontend/index.html (12 lines, minimal); frontend/src/main.jsx:7-11 mounts only PlaceholderView; PlaceholderView.jsx is one function component, no fetch, no router import anywhere |
| 17 | Vitest over frontend/ only, at least one smoke test passing, behaviour through state not whole-view snapshots | PASS | npx vitest run reports Test Files 2 passed, Tests 4 passed (independently re-run); both test files assert concrete string/format content, no snapshot API used |
| 18 | Plain JS/ESM, no TypeScript, no tsconfig, no type-checking gate | PASS | no .ts, .tsx or tsconfig file found under frontend/ |
| 19 | init.sh detects both toolchain roots, runs every gate green, skips frontend gate with WARN while frontend/package.json is absent | PASS | Full green run reproduced; independently reproduced the WARN by renaming frontend/package.json away and re-running init.sh, which printed a WARN and kept exit code 0, then restored the file and re-ran green again; init.sh diff against the committed version is purely additive, no line removed or reordered |
| 20 | No Terraform, no CI workflow, no runtime dependency on core added | PASS | no .tf or .tfvars file found anywhere (also confirmed by init.sh section 4 guardrail passing); .github/workflows/ unchanged; core/pyproject.toml:6 dependencies = [] |

## Traps re-verified independently (not accepted from the reports)

1. pre-commit run --all-files hollow green - reproduced: all 5 hooks report Skipped, exit 0. Re-ran with --files and real paths: all 5 genuinely Passed. Confirmed sound.
2. Ruff extend config-discovery trap - reproduced by writing a 102-char line into a scratch file inside core/ and confirming ruff check flags E501; scratch file deleted afterward. All 3 members carry the extend line.
3. prototypes/ unreachable by every gate - re-verified for ESLint (ignored outside base path), Prettier (unreachable via the actual gate scoped to frontend/; see minor observation on criterion 14), pre-commit (all 5 hooks skip explicitly-given prototype files), and by inspection ruff/mypy/pytest never touch a path outside backend/ because the workspace members list and the uv run invocation are scoped to backend/.
4. Python pinned to 3.13 - backend/.python-version is 3.13; uv run python -V reports Python 3.13.13 (re-run independently, not copy-pasted from the report).

## Layering (architecture.md section 3.1)

- planner_core/domain/, application/, ports/ contain only docstring __init__.py files - no imports of each other, no adapter, no handler, no AWS SDK. [x]
- core (backend/core/pyproject.toml:6) declares zero runtime deps. [x]
- No datetime.now() anywhere in backend/ (no domain code exists yet to call it). [x]
- No adapter exists yet anywhere (deferred to features 16/17, both blocked) - nothing to check for the adapter-imported-only-by-wiring.py rule; not violated because not yet applicable. [x]

## No product logic

- No product screens, routing, or API layer in frontend/ - only PlaceholderView.jsx and main.jsx. [x]
- No domain/application code exists in backend/core beyond package docstrings. [x]

## Conventions

- Naming: planner_core/planner_api/planner_ai snake_case modules, PascalCase PlaceholderView, UPPER_SNAKE keys for MESSAGES/SPACE/COLORS/FONT_SIZE/BREAKPOINT - all match docs/conventions.md. [x]
- Language rule: all identifiers/comments/docs in English; the two user-facing strings (SCAFFOLD_PLACEHOLDER_TITLE, SCAFFOLD_PLACEHOLDER_BODY) are es-ES and live solely in frontend/src/messages/es-ES.js. [x]
- Minor observation (low severity, not blocking): frontend/index.html:6 hardcodes a Spanish title and the html lang attribute directly in markup outside the messages module, duplicating the value of SCAFFOLD_PLACEHOLDER_TITLE. docs/conventions.md Castilian Spanish section says no Spanish literals inside components, handlers or markup, and the index.html title is arguably markup, though it sits outside the React tree (standard Vite boilerplate, not dynamically rendered). Worth a one-line fix or an explicit exception note in a future feature; does not block scaffolding.

## Boundaries

- No Terraform / CI files generated: [x] (none found; init.sh section 4 guardrail green)
- No architecture decision from section 2 made silently: [x] (P1/P7 already closed per section 1; nothing else touched)
- Frozen requirement docs unmodified: [x] (git status shows no changes to any of the 5 frozen docs)
- docs/frontend_prototype.md and feature_list.json feature-20 blocked_reason were edited, but only to fix a factual count (13 to 18 colour tokens, verified directly against the prototype file, which genuinely carries 18 custom-property pairs on that line). This is doc-drift correction, not a new architecture decision or a frozen-doc edit (docs/frontend_prototype.md is analysis, not one of the 5 frozen requirement docs). [x]

## init.sh

./init.sh runs fully green, exit 0, both toolchain gate sections run for real (not WARN).

The init.sh diff against the last committed version is purely additive - no existing check reordered, weakened or removed. git status after all verification runs shows no stray node_modules, dist, or scratch files; frontend/dist (created by vite build during verification) was deleted after inspection.

## Checkpoints

- C1: [x] - harness files present, frozen docs unmodified, init.sh exits 0
- C2: [x] - 0 features in_progress; feature 1 correctly still pending (status transition is the leader/human job on approval, not the implementer job); every blocked feature has a blocked_reason; progress/current.md describes only the active session
- C3: [x] - layering rules hold (see above); exactly 2 Lambda packages (lambda_api, lambda_ai); no stray print() or context-free TODO found in the 7 source files
- C4: [x] - ruff check and mypy clean; pytest -q shows 1 test passing (unit tier only, no contract suite yet - expected, feature 14 not started); no AWS/network/real-clock in core tests (only import assertions)
- C5: [x] - no suspicious untracked files beyond expected scaffold output and caches already gitignored
- C6: N/A for this feature - sdd is false, no specs/ folder required, confirmed by init.sh section 4 (specs required only for non-pending sdd features - feature 1 is exempt)
- C7: [x] - no .tf/.tfvars, no .github/workflows files, no section-2 decision made silently, no requirement invented (feature has covers: []), frozen docs unmodified

## Required changes (if any)

None blocking. Two low-severity observations for a future pass, not required before closing this feature:

1. frontend/index.html:6 - consider sourcing the title from the messages module (or documenting the exception) rather than a hardcoded Spanish literal duplicating SCAFFOLD_PLACEHOLDER_TITLE.
2. frontend/.prettierignore - consider adding an explicit prototypes ignore entry to match eslint.config.js defense-in-depth, even though no current gate constructs a path that would reach it.
