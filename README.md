todo

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
