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

for f in AGENTS.md CLAUDE.md CHECKPOINTS.md feature_list.json issue_list.json progress/current.md \
         docs/architecture.md docs/conventions.md docs/specs.md docs/issues.md docs/verification.md; do
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

# Guardrail: issue_list.json (docs/issues.md). Same shape of checks as features.
issue_valid = {"reported", "pending", "approved", "in_progress", "done", "wontfix", "blocked"}
issue_needs_plan = {"pending", "approved", "in_progress", "done"}
issues = []
if os.path.isfile("issue_list.json"):
    try:
        with open("issue_list.json", encoding="utf-8") as fh:
            issues = json.load(fh).get("issues", [])
    except Exception as exc:  # noqa: BLE001 - startup check, any failure is fatal
        FAILURES.append(f"issue_list.json is unreadable: {exc}")
else:
    FAILURES.append("Missing base file: issue_list.json")

feature_ids_in_progress = [f["name"] for f in in_progress]
issue_ids = [i["id"] for i in issues]
if len(issue_ids) != len(set(issue_ids)):
    FAILURES.append("issue_list.json has duplicate issue ids")
# No cap among issues themselves -- an approved batch may sit in_progress
# together (one implementer run, one batched reviewer call). A feature and an
# issue batch still never run at the same time. See issue_list.json rules.
issues_in_progress = [i["name"] for i in issues if i["status"] == "in_progress"]
if issues_in_progress and feature_ids_in_progress:
    FAILURES.append(
        "a feature and an issue are in_progress at the same time: "
        + ", ".join(feature_ids_in_progress + issues_in_progress)
    )
for i in issues:
    iid, iname, istatus = i["id"], i["name"], i["status"]
    if istatus not in issue_valid:
        FAILURES.append(f"issue {iid} ({iname}): invalid status '{istatus}'")
        continue
    if istatus == "blocked" and not i.get("blocked_reason", "").strip():
        FAILURES.append(f"issue {iid} ({iname}): blocked without a blocked_reason")
    if istatus == "wontfix" and not i.get("resolution", "").strip():
        FAILURES.append(f"issue {iid} ({iname}): wontfix without a resolution")
    if istatus in issue_needs_plan:
        for fname in ("analysis.md", "plan.md", "tasks.md"):
            if not os.path.isfile(os.path.join("issues", iname, fname)):
                FAILURES.append(
                    f"issue {iid} ({iname}) is {istatus} but issues/{iname}/{fname} is missing"
                )
    for rid in i.get("covers", []):
        if rid not in req_ids:
            FAILURES.append(f"issue {iid} ({iname}): covers unknown requirement id {rid}")

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

icounts = {}
for i in issues:
    icounts[i["status"]] = icounts.get(i["status"], 0) + 1
isummary = ", ".join(f"{k}: {v}" for k, v in sorted(icounts.items())) or "empty"
print(f"[OK]    issue_list.json valid ({len(issues)} issues - {isummary})")
untriaged = [i for i in issues if i["status"] == "reported"]
if untriaged:
    print(f"[OK]    Issues awaiting triage: {', '.join(str(i['id']) for i in untriaged)}")
queued = sorted((i for i in issues if i["status"] == "approved"), key=lambda x: x["id"])
if queued:
    print(f"[OK]    Next approved issue: {queued[0]['id']} - {queued[0]['name']}")
PY

if [ $? -ne 0 ]; then EXIT_CODE=1; fi

# Stop-hook fast path (opt-in): skip the slow gates when backend/ + frontend/
# are unchanged since the last green run. A manual ./init.sh always runs them.
STAMP="$(git rev-parse --git-dir 2>/dev/null)/harness-init.stamp"
TREE_HASH=$( { git rev-parse HEAD; git diff HEAD --binary -- backend frontend terraform init.sh; \
  git ls-files -o --exclude-standard -- backend frontend terraform | git hash-object --stdin-paths; } 2>/dev/null | sha1sum | cut -c1-40 )
if [ "${INIT_SKIP_IF_UNCHANGED:-0}" = 1 ] && [ $EXIT_CODE -eq 0 ] \
   && [ "$(cat "$STAMP" 2>/dev/null)" = "$TREE_HASH" ]; then
  ok "Quality gates skipped — backend/ and frontend/ unchanged since the last green run"
  exit 0
fi

# Gates run in parallel: queue_gate starts one in the background, collect_gates
# waits for all of them and reports in queue order. Output goes to a log that is
# shown only when a gate fails (and its last line for pytest/vitest).
GATE_TMP=$(mktemp -d)
G_LABEL=(); G_DIR=(); G_CMD=(); G_PID=()
queue_gate() {
  local label="$1" dir="$2"; shift 2
  local n=${#G_LABEL[@]}
  G_LABEL[n]="$label"; G_DIR[n]="$dir"; G_CMD[n]="$*"
  ( cd "$dir" && "$@" ) >"$GATE_TMP/$n.log" 2>&1 &
  G_PID[n]=$!
}
collect_gates() {
  local i tail1
  for i in "${!G_LABEL[@]}"; do
    if wait "${G_PID[i]}"; then
      tail1=""
      case "${G_LABEL[i]}" in pytest*) tail1=" — $(grep -v '^\s*$' "$GATE_TMP/$i.log" | tail -1)";;
      vitest*) tail1=" — $(grep -E '^\s*Tests ' "$GATE_TMP/$i.log" | tail -1 | sed 's/^ *//')";; esac
      ok "${G_LABEL[i]}$tail1"
    else
      fail "${G_LABEL[i]} — rerun from ${G_DIR[i]}/ to see the output: ${G_CMD[i]}"
      tail -n 30 "$GATE_TMP/$i.log" | sed 's/^/        /'
      EXIT_CODE=1
    fi
  done
  G_LABEL=(); G_DIR=(); G_CMD=(); G_PID=()
}

echo ""
echo "── 5. Quality gates ────────────────────────────────────"

if [ "$BACKEND_READY" -eq 0 ]; then
  warn "No backend/pyproject.toml yet — skipping gates until feature 1 (project_scaffold) is done"
elif [ "$HAS_UV" -eq 0 ]; then
  fail "backend/pyproject.toml exists but uv is missing — cannot run the quality gates"
  EXIT_CODE=1
else
  # Gates run from the workspace root so every member is covered.
  # Default pytest tiers only (unit + contract-vs-fake). Live-AWS and
  # Docker-local tiers are opt-in; an explicit -m here would override
  # pyproject's addopts.
  queue_gate "ruff format" backend uv run ruff format --check .
  queue_gate "ruff check"  backend uv run ruff check .
  queue_gate "mypy"        backend uv run mypy .
  queue_gate "pytest (unit + contract, no AWS, no Docker)" backend uv run pytest -q -m "not aws and not docker"
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
  queue_gate "prettier --check" frontend npx prettier --check .
  queue_gate "eslint"           frontend npx eslint .
  queue_gate "vitest"           frontend npx vitest run --pool=threads
fi

# Terraform: static checks only. Nothing here needs AWS credentials, and
# init.sh never runs `terraform init` for you (same stance as npm install).
if ! ls terraform/*.tf >/dev/null 2>&1; then
  warn "No terraform/*.tf yet — skipping Terraform gates"
elif ! command -v terraform >/dev/null 2>&1; then
  fail "terraform/ has .tf files but terraform is not installed — cannot run the Terraform gates"
  EXIT_CODE=1
else
  queue_gate "terraform fmt" terraform terraform fmt -check -recursive
  if [ -d terraform/.terraform ]; then
    queue_gate "terraform validate" terraform terraform validate
  else
    warn "terraform/.terraform is absent — run 'terraform init -backend=false' inside terraform/ to enable validate"
  fi
  if command -v tflint >/dev/null 2>&1; then
    queue_gate "tflint" terraform tflint
  else
    warn "tflint is not installed — skipping (optional; see https://github.com/terraform-linters/tflint)"
  fi
fi

collect_gates
rm -rf "$GATE_TMP"

echo ""
echo "── 6. Summary ──────────────────────────────────────────"

if [ $EXIT_CODE -eq 0 ]; then
  ok "Environment ready. You can start working."
else
  fail "Environment NOT ready. Fix the errors above before proceeding."
fi

[ $EXIT_CODE -eq 0 ] && echo "$TREE_HASH" > "$STAMP"
exit $EXIT_CODE
