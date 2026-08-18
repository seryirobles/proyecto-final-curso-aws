#!/usr/bin/env bash
# init.sh — Environment verification and harness integrity check
#
# The agent runs this at the START of a session and before declaring any task
# `done`. If it fails, the session must not proceed.
#
# On Windows, run it through Git Bash (the Claude Code Bash tool already does).
#
# Expected output: clear exit codes and blocks marked [OK] / [WARN] / [FAIL].

set -u

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

ok()   { printf "${GREEN}[OK]${NC}    %s\n" "$1"; }
warn() { printf "${YELLOW}[WARN]${NC}  %s\n" "$1"; }
fail() { printf "${RED}[FAIL]${NC}  %s\n" "$1"; }

EXIT_CODE=0

echo "── 1. Environment ──────────────────────────────────────"

# Python detection.
#
# On Windows, `command -v python3` finds the Microsoft Store App Execution Alias
# stub, which is NOT a real interpreter (it prints an install advert and exits
# 49). So we probe by ACTUALLY RUNNING each candidate, never by presence alone.
PY_CMD=()
for candidate in "python3" "python" "py" "uv run --no-project python"; do
  # shellcheck disable=SC2206 - deliberate word splitting to build the argv
  probe=($candidate)
  if "${probe[@]}" -c "import sys; sys.exit(0)" >/dev/null 2>&1; then
    PY_CMD=("${probe[@]}")
    break
  fi
done

if [ ${#PY_CMD[@]} -eq 0 ]; then
  fail "No working Python interpreter found (tried python3, python, py, uv run)"
  fail "On Windows, python3/python may be Microsoft Store stubs. Install uv or a real Python."
  exit 1
fi
ok "python -> $("${PY_CMD[@]}" -c 'import platform; print(platform.python_version())' 2>&1) via '${PY_CMD[*]}'"

# The backend is a uv workspace rooted at backend/.
BACKEND_READY=0
if [ -f "backend/pyproject.toml" ]; then BACKEND_READY=1; fi

# The frontend is a separate toolchain root rooted at frontend/.
FRONTEND_READY=0
if [ -f "frontend/package.json" ]; then FRONTEND_READY=1; fi

if command -v uv >/dev/null 2>&1; then
  ok "uv -> $(uv --version 2>&1)"
  HAS_UV=1
else
  HAS_UV=0
  if [ "$BACKEND_READY" -eq 1 ]; then
    fail "uv is not installed but backend/pyproject.toml exists (see docs/architecture.md 1.3)"
    EXIT_CODE=1
  else
    warn "uv is not installed yet — required from feature 1 (project_scaffold) onward"
  fi
fi

if command -v npm >/dev/null 2>&1; then
  ok "npm -> $(npm --version 2>&1)"
  HAS_NPM=1
else
  HAS_NPM=0
  if [ "$FRONTEND_READY" -eq 1 ]; then
    fail "npm is not installed but frontend/package.json exists (see docs/architecture.md 1.1)"
    EXIT_CODE=1
  else
    warn "npm is not installed yet — required from feature 1 (project_scaffold) onward"
  fi
fi

echo ""
echo "── 2. Harness base files ───────────────────────────────"

for f in AGENTS.md CLAUDE.md CHECKPOINTS.md feature_list.json progress/current.md \
         docs/architecture.md docs/conventions.md docs/specs.md docs/verification.md; do
  if [ ! -f "$f" ]; then
    fail "Missing base file: $f"
    EXIT_CODE=1
  else
    ok "Found $f"
  fi
done

echo ""
echo "── 3. Frozen requirement docs ──────────────────────────"

for f in docs/requirements.md docs/app_user_stories.md docs/coverage_analysis.md \
         docs/gaps_and_resolutions.md docs/gaps_pending_stakeholders.md; do
  if [ ! -f "$f" ]; then
    fail "Missing frozen requirement doc: $f (these are read-only, never delete)"
    EXIT_CODE=1
  else
    ok "Found $f"
  fi
done

echo ""
echo "── 4. feature_list.json, specs and guardrails ──────────"

"${PY_CMD[@]}" - <<'PY'
import glob
import json
import os
import re
import sys

FAILURES = []

try:
    with open("feature_list.json", encoding="utf-8") as fh:
        data = json.load(fh)
except Exception as exc:  # noqa: BLE001 - startup check, any failure is fatal
    print(f"[FAIL]  feature_list.json is unreadable: {exc}")
    sys.exit(1)

features = data.get("features", [])
valid = {"pending", "spec_ready", "in_progress", "done", "blocked"}
requires_spec = {"spec_ready", "in_progress", "done"}
by_id = {f["id"]: f for f in features}

in_progress = [f for f in features if f["status"] == "in_progress"]
if len(in_progress) > 1:
    names = ", ".join(f["name"] for f in in_progress)
    FAILURES.append(f"{len(in_progress)} features in in_progress (max 1): {names}")

for f in features:
    fid, name, status = f["id"], f["name"], f["status"]

    if status not in valid:
        FAILURES.append(f"feature {fid} ({name}): invalid status '{status}'")
        continue

    if status == "blocked" and not f.get("blocked_reason", "").strip():
        FAILURES.append(f"feature {fid} ({name}): blocked without a blocked_reason")

    if f.get("sdd") and status in requires_spec:
        for fname in ("requirements.md", "design.md", "tasks.md"):
            if not os.path.isfile(os.path.join("specs", name, fname)):
                FAILURES.append(
                    f"feature {fid} ({name}) is {status} but specs/{name}/{fname} is missing"
                )

    for dep in f.get("depends_on", []):
        if dep not in by_id:
            FAILURES.append(f"feature {fid} ({name}): depends_on unknown id {dep}")
        elif status in {"in_progress", "done"} and by_id[dep]["status"] != "done":
            FAILURES.append(
                f"feature {fid} ({name}) is {status} but dependency "
                f"{dep} ({by_id[dep]['name']}) is not done"
            )

# Guardrail: agents never generate IaC or CI. See docs/architecture.md section 5.
def _status_of(name):
    for f in features:
        if f["name"] == name:
            return f["status"]
    return "blocked"

tf_files = [
    p for pattern in ("**/*.tf", "**/*.tfvars")
    for p in glob.glob(pattern, recursive=True)
    if ".terraform" not in p
]
if tf_files and _status_of("infrastructure_terraform") == "blocked":
    FAILURES.append(
        "Terraform files exist while 'infrastructure_terraform' is blocked "
        f"(human-owned): {', '.join(sorted(tf_files)[:5])}"
    )

ci_files = glob.glob(".github/workflows/*.yml") + glob.glob(".github/workflows/*.yaml")
if ci_files and _status_of("cicd_pipeline") == "blocked":
    FAILURES.append(
        "CI workflow files exist while 'cicd_pipeline' is blocked "
        f"(human-owned): {', '.join(sorted(ci_files))}"
    )

# Guardrail: feature_list.json is the source of truth for implementation.
# Every requirement id defined in docs/requirements.md must be covered by at
# least one feature, and no feature may claim an id that does not exist.
#
# A requirement retired by a gap resolution keeps its row (struck through and
# annotated "**Removed**") so the id is never silently reused -- see FR-LIB-06
# (G-68) and FR-SHOP-11 (G-74). Those rows are not live requirements and must
# not be reported as a coverage regression, but they stay valid ids so a stale
# "covers" entry is still caught as a typo below.
req_ids = set()
removed_ids = set()
with open("docs/requirements.md", encoding="utf-8") as fh:
    for line in fh:
        m = re.match(r"^\|\s*((?:FR|NFR)-[A-Z]+-\d{2})\s*\|", line)
        if m:
            req_ids.add(m.group(1))
            if "**Removed**" in line:
                removed_ids.add(m.group(1))
covered = {rid for f in features for rid in f.get("covers", [])}
for rid in sorted(req_ids - covered - removed_ids):
    FAILURES.append(f"requirement {rid} is covered by no feature (coverage regression)")
for rid in sorted(covered - req_ids):
    FAILURES.append(f"covers cites unknown requirement id {rid} (typo?)")

if FAILURES:
    for message in FAILURES:
        print(f"[FAIL]  {message}")
    sys.exit(1)

counts = {}
for f in features:
    counts[f["status"]] = counts.get(f["status"], 0) + 1
summary = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
print(f"[OK]    feature_list.json valid ({len(features)} features - {summary})")
print("[OK]    Specs present for every non-pending sdd feature")
print("[OK]    No agent-generated IaC or CI files")
print(f"[OK]    Requirement coverage: all {len(req_ids)} FR/NFR ids covered by features")

nxt = next(
    (f for f in sorted(features, key=lambda x: x["id"])
     if f["status"] == "pending"
     and all(by_id[d]["status"] == "done" for d in f.get("depends_on", []))),
    None,
)
if nxt:
    print(f"[OK]    Next actionable feature: {nxt['id']} - {nxt['name']}")
else:
    print("[WARN]  No actionable pending feature (all blocked or done)")
PY

if [ $? -ne 0 ]; then EXIT_CODE=1; fi

echo ""
echo "── 5. Quality gates ────────────────────────────────────"

if [ "$BACKEND_READY" -eq 0 ]; then
  warn "No backend/pyproject.toml yet — skipping gates until feature 1 (project_scaffold) is done"
elif [ "$HAS_UV" -eq 0 ]; then
  fail "backend/pyproject.toml exists but uv is missing — cannot run the quality gates"
  EXIT_CODE=1
else
  # Gates run from the workspace root so every member is covered.
  run_gate() {
    local label="$1"; shift
    if (cd backend && "$@") >/dev/null 2>&1; then
      ok "$label"
    else
      fail "$label — rerun from backend/ to see the output: $*"
      EXIT_CODE=1
    fi
  }

  run_gate "ruff format"  uv run ruff format --check .
  run_gate "ruff check"   uv run ruff check .
  run_gate "mypy"         uv run mypy .

  # Default tiers only (unit + contract-vs-fake). The live-AWS tier is opt-in.
  if (cd backend && uv run pytest -q -m "not aws"); then
    ok "pytest (unit + contract, no AWS)"
  else
    fail "pytest — there are failing tests"
    EXIT_CODE=1
  fi
fi

if [ "$FRONTEND_READY" -eq 0 ]; then
  warn "No frontend/package.json yet — skipping gates until feature 1 (project_scaffold) is done"
elif [ "$HAS_NPM" -eq 0 ]; then
  fail "frontend/package.json exists but npm is missing — cannot run the quality gates"
  EXIT_CODE=1
elif [ ! -d "frontend/node_modules" ]; then
  warn "frontend/node_modules is absent — run 'npm install' inside frontend/ (init.sh never installs it for you)"
else
  # Gates run from the toolchain root so the resolved config/plugins match
  # what a developer would get running the same command by hand.
  run_gate() {
    local label="$1"; shift
    if (cd frontend && "$@") >/dev/null 2>&1; then
      ok "$label"
    else
      fail "$label — rerun from frontend/ to see the output: $*"
      EXIT_CODE=1
    fi
  }

  run_gate "prettier --check" npx prettier --check .
  run_gate "eslint"           npx eslint .
  run_gate "vitest"           npx vitest run
fi

echo ""
echo "── 6. Summary ──────────────────────────────────────────"

if [ $EXIT_CODE -eq 0 ]; then
  ok "Environment ready. You can start working."
else
  fail "Environment NOT ready. Fix the errors above before proceeding."
fi

exit $EXIT_CODE
