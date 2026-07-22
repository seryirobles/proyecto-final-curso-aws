# Collaborative Weekly Meal Planner

Final project for the AWS course ("libre" option). A web application where a
fixed set of users, managed by an admin, collaboratively plan the meals of the
**current week and the next week** (Monday–Sunday, lunch and dinner).

Users propose candidate meals per slot, promote one definitive meal per slot,
maintain a shared recipe library, generate recipes and whole-week plans with AI
under shared rules, build a single shared shopping list, and browse an archive
of past weeks — all in Castilian Spanish, with changes reflected between users
in real time.

> **Status: pre-implementation.** Requirements are complete and frozen.
> Architecture is being decided. No application code exists yet.

## Documentation

### Product (frozen — do not edit)

| File | What it holds |
|---|---|
| [`docs/requirements.md`](docs/requirements.md) | ~90 numbered requirements (`FR-*`, `NFR-*`) — **the contract** |
| [`docs/app_user_stories.md`](docs/app_user_stories.md) | The 27 original user stories |
| [`docs/coverage_analysis.md`](docs/coverage_analysis.md) | Story → requirement coverage audit |
| [`docs/gaps_and_resolutions.md`](docs/gaps_and_resolutions.md) | `G-01`–`G-67`: every ambiguity and why it was resolved that way |
| [`docs/gaps_pending_stakeholders.md`](docs/gaps_pending_stakeholders.md) | `PEND-01`–`PEND-15`, all closed |

### Engineering harness

| File | What it holds |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Entry point and navigation map for AI agents |
| [`docs/architecture.md`](docs/architecture.md) | Quality bar; decided vs pending architecture; domain invariants |
| [`docs/conventions.md`](docs/conventions.md) | Style, naming, error handling, language policy |
| [`docs/specs.md`](docs/specs.md) | The SDD process: EARS, the three files, the human approval gate |
| [`docs/verification.md`](docs/verification.md) | How work is proven to function |
| [`CHECKPOINTS.md`](CHECKPOINTS.md) | Objective criteria for a healthy final state |
| [`feature_list.json`](feature_list.json) | The backlog, tiered by architectural dependency |

## Getting started

```bash
./init.sh
```

On Windows, run it through Git Bash. If everything is green, open `AGENTS.md`
and continue from there. `init.sh` reports the next actionable feature.

## Architecture

⚠️ **Being decided.** See [`docs/architecture.md`](docs/architecture.md) — §1 is
what is settled, §2 is what is not.

Settled so far:

- **Frontend** — single-page app, HTML with inline CSS driven by a JS logic
  class, no separate templating language. Responsive, es-ES.
- **Backend** — exactly two Python Lambdas: `api` (REST, regular operations)
  and `ai` (AI generation only).
- **Toolchain** — uv, pytest, ruff, mypy, SonarQube, pre-commit.
- **Cloud** — AWS, Terraform IaC, ≥ 2 AZ, automated backups, CI/CD on `main`.

### Architecture decisions

_To be written as decisions are made (`NFR-DOC-01`)._

### Diagram

_To be added (`NFR-DOC-01`)._

## Deployment

_Reproducible deploy steps to be documented (`NFR-DOC-01`)._

## Monthly cost estimate

_To be documented (`NFR-DOC-01`). The AI sub-budget is capped at €50/month
(`NFR-AI-01`)._

## Teardown

_To be documented (`NFR-DOC-01`)._

## Development Tools

This project uses two Gentleman-Programming tools to assist AI-driven development and enforce code review standards before commits.

### Gentle AI

Ecosystem for AI coding agents (skills, SDD orchestration, persistent memory).

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/Gentleman-Programming/gentle-ai/main/scripts/install.sh | bash

# Windows
scoop bucket add gentleman https://github.com/Gentleman-Programming/scoop-bucket
scoop install gentle-ai
```

After installing, open your AI agent in this project and run:

```bash
/sdd-init                             # registers SDD project context
gentle-ai skill-registry refresh      # builds the skill registry
```

Run `gentle-ai doctor` at any time for a health check.

### GGA (Gentleman Guardian Angel)

Provider-agnostic AI code review that runs on every commit, validating staged files against this project's `AGENTS.md`.

```bash
# Homebrew (recommended)
brew install gentleman-programming/tap/gga

# Manual
git clone https://github.com/Gentleman-Programming/gentleman-guardian-angel.git
cd gentleman-guardian-angel
./install.sh
```

Then, from this project's root:

```bash
gga init      # create the .gga config file (already present in this repo)
gga install   # install the git pre-commit hook
```

Edit `.gga` to set your `PROVIDER` (e.g. `claude`, `gemini`, `codex`) if needed.
