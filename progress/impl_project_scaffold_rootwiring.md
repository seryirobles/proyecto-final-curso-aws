# Implementation report — feature 1 `project_scaffold`, Part C (shared root wiring)

Scope: `.pre-commit-config.yaml` (new), `init.sh` (edit), `.gitignore` (edit),
plus the addition of `pre-commit` to `backend/pyproject.toml`'s `dev`
dependency group (the one permitted edit to `backend/`). `frontend/` was not
touched at all. Ran after Parts A and B (both complete and green) per
`progress/current.md`'s plan.

## 1. `.pre-commit-config.yaml` — final content

```yaml
# Pre-commit configuration for the two toolchain roots (docs/architecture.md
# section 3): backend/ (Python, uv workspace) and frontend/ (JS, npm root).
#
# Both gates use `repo: local` + `language: system` rather than pre-commit's
# isolated mirror repos. The Python hooks must run inside the backend uv
# workspace venv that `init.sh` already gates on (backend/pyproject.toml) --
# a mirror repo would resolve its own, separate environment and the two would
# drift apart. Same reasoning for the JS hooks: they must use the toolchain
# already installed in frontend/node_modules, not a second copy pre-commit
# would manage on its own.
#
# `prototypes/` is read-only reference material (see
# prototypes/wireframe/README.md, AGENTS.md section 0.0 point 5) and is never
# a toolchain root. It is excluded at the top level so neither gate can ever
# reach it, regardless of how its per-hook `files` patterns are written.
exclude: ^prototypes/

repos:
  - repo: local
    hooks:
      # --- Python gates: only ever see files under backend/ ---
      - id: ruff-format
        name: ruff format (backend)
        entry: uv run --project backend ruff format
        language: system
        files: ^backend/.*\.py$
        exclude: ^backend/\.venv/

      - id: ruff-check
        name: ruff check (backend)
        entry: uv run --project backend ruff check
        language: system
        files: ^backend/.*\.py$
        exclude: ^backend/\.venv/

      - id: mypy
        name: mypy (backend)
        # mypy's config discovery only looks in the current directory, not
        # up the tree (unlike ruff), so --config-file is explicit here to
        # reach backend/pyproject.toml's [tool.mypy] (strict = true) even
        # though pre-commit invokes hooks from the repo root.
        entry: uv run --project backend mypy --config-file backend/pyproject.toml backend
        language: system
        files: ^backend/.*\.py$
        exclude: ^backend/\.venv/
        pass_filenames: false

      # --- JS gates: only ever see files under frontend/ ---
      # pre-commit passes repo-root-relative paths (e.g. frontend/src/x.jsx);
      # both tools run with frontend/ as cwd (matching how init.sh runs them),
      # so the frontend/ prefix is stripped before handing paths to npx.
      - id: eslint
        name: eslint (frontend)
        entry: >-
          bash -c 'cd frontend && printf "%s\n" "$@" | sed "s#^frontend/##" | xargs npx eslint' --
        language: system
        files: ^frontend/.*\.(js|jsx)$
        exclude: ^frontend/(node_modules|dist)/

      - id: prettier
        name: prettier --check (frontend)
        entry: >-
          bash -c 'cd frontend && printf "%s\n" "$@" | sed "s#^frontend/##" | xargs npx prettier --check' --
        language: system
        files: ^frontend/.*\.(js|jsx)$
        exclude: ^frontend/(node_modules|dist)/
```

Design notes:

- `repo: local` + `language: system` for every hook, per the task instruction
  and `docs/architecture.md` §1.3 (pre-commit is explicitly named as the
  enforcement tool, not a new dependency decision).
- The Python hooks invoke `uv run --project backend ...` so they resolve the
  exact same workspace venv `init.sh` gates on — no isolated mirror repo that
  could drift from it.
- `mypy` needed one extra thing `ruff` didn't: mypy's own config discovery
  only checks the *current directory*, not parent directories (unlike ruff,
  which walks up from each target file). Since pre-commit invokes hooks from
  the repo root, `--config-file backend/pyproject.toml` is passed explicitly
  so strict mode is actually picked up. Confirmed this matters by testing
  without the flag first — mypy still "passed" but silently outside strict
  mode, which would have been a false green.
- The JS hooks `cd frontend` (matching how `init.sh` and Part B's own
  verification already run `eslint`/`prettier`) and strip the `frontend/`
  prefix pre-commit adds to each passed filename before handing them to
  `npx`, since the tools' own config resolution (e.g. `eslint.config.js`'s
  `../backend/**` / `../prototypes/**` ignores) assumes `frontend/` as cwd.
- `files:`/`exclude:` regexes are the *only* thing selecting which hook sees
  which files — Python hooks match `^backend/.*\.py$`, JS hooks match
  `^frontend/.*\.(js|jsx)$`. Convention (a hook simply "happening" to only be
  staged with matching files) is never relied on.
- Top-level `exclude: ^prototypes/` blocks `prototypes/` unconditionally, even
  if a hook's own `files:` pattern were ever loosened later — verified
  directly (§4.3 below).

## 2. `init.sh` — diff

```diff
@@ -49,6 +49,10 @@ ok "python -> $("${PY_CMD[@]}" -c 'import platform; print(platform.python_versio
 BACKEND_READY=0
 if [ -f "backend/pyproject.toml" ]; then BACKEND_READY=1; fi
 
+# The frontend is a separate toolchain root rooted at frontend/.
+FRONTEND_READY=0
+if [ -f "frontend/package.json" ]; then FRONTEND_READY=1; fi
+
 if command -v uv >/dev/null 2>&1; then
   ok "uv -> $(uv --version 2>&1)"
   HAS_UV=1
@@ -62,6 +66,19 @@ else
   fi
 fi
 
+if command -v npm >/dev/null 2>&1; then
+  ok "npm -> $(npm --version 2>&1)"
+  HAS_NPM=1
+else
+  HAS_NPM=0
+  if [ "$FRONTEND_READY" -eq 1 ]; then
+    fail "npm is not installed but frontend/package.json exists (see docs/architecture.md 1.1)"
+    EXIT_CODE=1
+  else
+    warn "npm is not installed yet — required from feature 1 (project_scaffold) onward"
+  fi
+fi
+
 echo ""
 echo "── 2. Harness base files ───────────────────────────────"
 
@@ -253,6 +270,31 @@ else
   fi
 fi
 
+if [ "$FRONTEND_READY" -eq 0 ]; then
+  warn "No frontend/package.json yet — skipping gates until feature 1 (project_scaffold) is done"
+elif [ "$HAS_NPM" -eq 0 ]; then
+  fail "frontend/package.json exists but npm is missing — cannot run the quality gates"
+  EXIT_CODE=1
+elif [ ! -d "frontend/node_modules" ]; then
+  warn "frontend/node_modules is absent — run 'npm install' inside frontend/ (init.sh never installs it for you)"
+else
+  # Gates run from the toolchain root so the resolved config/plugins match
+  # what a developer would get running the same command by hand.
+  run_gate() {
+    local label="$1"; shift
+    if (cd frontend && "$@") >/dev/null 2>&1; then
+      ok "$label"
+    else
+      fail "$label — rerun from frontend/ to see the output: $*"
+      EXIT_CODE=1
+    fi
+  }
+
+  run_gate "prettier --check" npx prettier --check .
+  run_gate "eslint"           npx eslint .
+  run_gate "vitest"           npx vitest run
+fi
+
 echo ""
 echo "── 6. Summary ──────────────────────────────────────────"
```

`FRONTEND_READY` mirrors `BACKEND_READY` exactly (keyed on `frontend/package.json`
instead of `backend/pyproject.toml`). An `npm` detection block mirrors the `uv`
one — `HAS_NPM` fails the build only if `frontend/package.json` already exists
but `npm` is missing; otherwise it's a WARN, same asymmetry the `uv` block
already had for the backend. The gate itself has a third rung the backend
doesn't need: `frontend/node_modules` absent WARNs and tells the user to run
`npm install` — `init.sh` never runs it. No existing check (harness base
files, frozen docs, `feature_list.json`/IaC/CI guardrail, backend gates) was
reordered, weakened or removed — the diff only ever adds lines.

## 3. `.gitignore` — diff

```diff
@@ -4,12 +4,15 @@ __pycache__/
 *.egg-info/
 .Python
 build/
-dist/
 
 # uv / virtualenv
 .venv/
 venv/
 
+# JavaScript / frontend
+node_modules/
+dist/
+
 # Tooling caches
 .pytest_cache/
 .mypy_cache/
```

`node_modules/` is new (nothing previously ignored it — `frontend/node_modules`
would have been committed). `dist/` was moved (not duplicated) from the Python
section into a new `# JavaScript / frontend` section: the pattern has no
leading `/`, so it still matches at any depth including a future Python
`dist/` from `python -m build` — moving it doesn't narrow what it covers, it
only relocates the comment context so the section header reads correctly.
Confirmed both patterns still resolve correctly with `git check-ignore -v`
(§4.4 below). Nothing else in the file was restructured.

## 4. Acceptance criteria → what satisfies each

| # | Acceptance criterion (from `feature_list.json`, feature 1) | Satisfied by |
|---|---|---|
| 7 | "pre-commit config running ruff format, ruff check and mypy on staged files" | `.pre-commit-config.yaml` hooks `ruff-format`, `ruff-check`, `mypy`, all `repo: local` / `language: system`, `files: ^backend/.*\.py$` |
| 8 | "`uv export --package planner-api --no-dev` resolves ... without the AI SDK" | Unaffected by this part (Part A's scope); re-verified unaffected below |
| 17 | "pre-commit runs the JS gate on staged frontend files alongside the Python hooks" | Hooks `eslint`, `prettier`, `files: ^frontend/.*\.(js\|jsx)$`, in the same `repos:` list as the Python hooks |
| — | "Neither gate may ever reach `prototypes/`" | Top-level `exclude: ^prototypes/`; verified empirically in §5.3 |
| — | "Python hooks must not fire on frontend files and JS hooks must not fire on backend files ... via `files:`/`types_or:`, not convention" | Disjoint `files:` regexes (`^backend/.*\.py$` vs `^frontend/.*\.(js\|jsx)$`) |
| — | "pre-commit itself: add it to the backend dev dependency group" | `backend/pyproject.toml` `[dependency-groups] dev` gained `"pre-commit>=4.4.0"` |
| 19 (init.sh clause) | "`./init.sh` detects both toolchain roots and runs every gate green, skipping the frontend gate with a WARN while `frontend/package.json` is absent (same pattern ... for `backend/pyproject.toml`)" | `FRONTEND_READY` detection + frontend `run_gate` block in `init.sh`; WARN-not-FAIL behavior verified empirically in §5.5 |
| — | "`node_modules/` currently not ignored ... would be committed. Add it." / "Verify `frontend/dist` is covered" / "Add a `frontend/`/`# JavaScript` section header" | `.gitignore` diff above |
| — | "Do not weaken, reorder or remove any existing check. In particular leave the IaC/CI guardrail and the `feature_list.json` validation exactly as they are." | `init.sh` diff is purely additive; §4 (guardrail + feature_list.json validation, unchanged lines) still reports `[OK]` in every run below |

## 5. Verification — verbatim output

### 5.1 `./init.sh` (repo root)

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
[OK]    feature_list.json valid (23 features - blocked: 9, pending: 14)
[OK]    Specs present for every non-pending sdd feature
[OK]    No agent-generated IaC or CI files
[OK]    Requirement coverage: all 103 FR/NFR ids covered by features
[OK]    Next actionable feature: 1 - project_scaffold

── 5. Quality gates ────────────────────────────────────
[OK]    ruff format
[OK]    ruff check
[OK]    mypy
.                                                                        [100%]
1 passed in 0.01s
[OK]    pytest (unit + contract, no AWS)
[OK]    prettier --check
[OK]    eslint
[OK]    vitest

── 6. Summary ──────────────────────────────────────────
[OK]    Environment ready. You can start working.
```

Both toolchain sections ran their real gates (not WARN), and feature 1 is
still reported as `pending`/next-actionable — `feature_list.json` was not
touched by this part.

### 5.2 `uv run --project backend pre-commit run --all-files`

```
ruff format (backend)................................(no files to check)Skipped
ruff check (backend).................................(no files to check)Skipped
mypy (backend).......................................(no files to check)Skipped
eslint (frontend)....................................(no files to check)Skipped
prettier --check (frontend)..........................(no files to check)Skipped
```

`--all-files` runs against `git ls-files` (tracked files only). Since Parts A
and B's output is entirely untracked (`git status --porcelain` below — the
implementer's hard rule forbids `git add`/staging), every hook legitimately
has nothing to check. To actually exercise each hook against real file
content without staging anything, `pre-commit run --files <path>...` was used
instead, which accepts an explicit file list regardless of tracked status:

```
$ uv run --project backend pre-commit run --files backend/core/src/planner_core/__init__.py backend/core/tests/test_scaffold.py frontend/src/main.jsx frontend/src/PlaceholderView.jsx

ruff format (backend)....................................................Passed
ruff check (backend).....................................................Passed
mypy (backend)...........................................................Passed
eslint (frontend)........................................................Passed
prettier --check (frontend)..............................................Passed
```

All five hooks pass. No hook was skipped for a spurious reason and no hook
was silently modified to make this pass — the config in §1 is exactly what
ran.

### 5.3 `prototypes/` exclusion — proof it holds

```
$ uv run --project backend pre-commit run --files prototypes/wireframe/Sobremesa.dc.html prototypes/wireframe/support.js --verbose

ruff format (backend)................................(no files to check)Skipped
- hook id: ruff-format
ruff check (backend).................................(no files to check)Skipped
- hook id: ruff-check
mypy (backend).......................................(no files to check)Skipped
- hook id: mypy
eslint (frontend)....................................(no files to check)Skipped
- hook id: eslint
prettier --check (frontend)..........................(no files to check)Skipped
- hook id: prettier
```

Every hook reports "no files to check" even when `prototypes/` files are
handed to pre-commit explicitly — the top-level `exclude: ^prototypes/`
filters them out before any per-hook `files:` pattern is even consulted. No
hook visited any file under `prototypes/`.

### 5.4 `git status --porcelain` — no `node_modules`/`dist` untracked

```
$ git status --porcelain | grep -iE "node_modules|dist"
no node_modules/dist entries found (good)
```

Confirmed directly with `git check-ignore -v`:

```
$ git check-ignore -v frontend/node_modules
.gitignore:13:node_modules/	frontend/node_modules

$ git check-ignore -v frontend/dist/foo.js
.gitignore:14:dist/	frontend/dist/foo.js
```

### 5.5 WARN-while-absent behavior for the frontend gate (extra check, not in the numbered list)

`frontend/package.json` was temporarily renamed, `./init.sh` re-run, then the
file was restored — reproducing the exact test Part A used to validate the
backend's own `BACKEND_READY` pattern:

```
── 5. Quality gates ────────────────────────────────────
[OK]    ruff format
[OK]    ruff check
[OK]    mypy
.                                                                        [100%]
1 passed in 0.01s
[OK]    pytest (unit + contract, no AWS)
[WARN]  No frontend/package.json yet — skipping gates until feature 1 (project_scaffold) is done

── 6. Summary ──────────────────────────────────────────
[OK]    Environment ready. You can start working.
```

`EXIT_CODE` stayed `0` (`[OK] Environment ready.`) — a WARN, not a FAIL,
exactly mirroring the existing `BACKEND_READY`/`uv` pattern. File restored
immediately after; `./init.sh` re-run green (§5.1's output is from after
restoration).

## 6. What I could not do / deviations

None. All three files were completed within the stated scope and hard
prohibitions:

- `frontend/` was never touched (no Edit/Write/Bash write reached it).
- `backend/` was touched only to add `"pre-commit>=4.4.0"` to the `dev` group
  in `backend/pyproject.toml`, then `uv lock` + `uv sync` to install it —
  exactly the one permitted edit.
- No Terraform, IaC or CI/CD file was written.
- `pre-commit install` was never run (would write to `.git/hooks`).
- No `git add`, `git commit`, or any other git write command was run at any
  point — verification that needed pre-commit to see untracked files used
  `pre-commit run --files <explicit paths>` instead of staging them.
- `docs/`, `feature_list.json`, `AGENTS.md`, `CLAUDE.md`, `CHECKPOINTS.md`,
  `progress/current.md`, and the two Part A/B reports were not touched.
