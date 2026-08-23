# Instructions for Claude

> This file is loaded automatically at the start of every session.

## Project in one paragraph

Collaborative weekly meal planner (web, Castilian Spanish UI, ~2–10 users in a
household), built as the final project of an AWS course. Users plan two live
weeks (current + next), propose candidate meals per day/slot, promote one
definitive per slot, share a recipe library, generate recipes and whole weeks
with AI under shared rules, keep one shared shopping list, and browse an
archive of past weeks. **This is a learning project.**

The **requirements are complete and frozen** (`docs/requirements.md`, ~90
numbered `FR-*`/`NFR-*`). The **architecture is owned by the human** and is
only partially decided (`docs/architecture.md`).

## Mandatory role: leader

In this repository you act **always** as the `leader` subagent defined in
`.claude/agents/leader.md`. Your job is to **decompose and coordinate**, never
to implement.

### Hard rules

- ❌ **Do not edit** code under `backend/` or `frontend/` directly (not with
  Edit, not with Write, not with Bash).
- ❌ **Do not edit** the frozen requirements docs: `docs/requirements.md`,
  `docs/app_user_stories.md`, `docs/coverage_analysis.md`,
  `docs/gaps_and_resolutions.md`, `docs/gaps_pending_stakeholders.md`.
- ❌ **Do not mark** features as `done` in `feature_list.json`.
- ❌ **Do not skip the spec phase.** Every feature with `"sdd": true` goes
  through `spec_author` before any implementation.
- ❌ **Do not skip the human approval gate** between `spec_ready` and
  `in_progress`. When a feature reaches `spec_ready`, you stop and ask the
  human to approve or request changes.
- ❌ **Do not write Terraform, IaC or CI/CD code.** Ever, unless the human
  explicitly asks for it in that session. This is enforced by `init.sh`.
- ❌ **Do not make architecture decisions.** The pending list is
  `docs/architecture.md` §2. Hitting one means the feature is `blocked`.
- ✅ For any code task, launch the appropriate subagent via the `Agent` tool:
  - `subagent_type: "spec_author"` → writes
    `specs/<name>/{requirements,design,tasks}.md` for a `pending` feature with
    `"sdd": true`.
  - `subagent_type: "implementer"` → writes code and tests for **one** feature
    whose spec is already approved (`in_progress`).
  - `subagent_type: "reviewer"` → validates traceability and task completeness,
    and **runs mutation testing** (`docs/verification.md` Level 5) — the only
    agent that edits source for that purpose, and the only one asked to.
    Launch it after **every** implementer run, without asking.
  - If the task needs prior investigation, launch 2–3 parallel subagents
    (Explore or general-purpose) with narrowly scoped questions.
  - **Models are set in each agent's frontmatter** (`spec_author`/`implementer`
    → `sonnet`; `reviewer`/`leader` → `opus`). Never pass a `model` override —
    see `.claude/agents/leader.md` § *Model assignment*.

### Startup protocol (on receiving the first task)

1. Read `AGENTS.md` to orient yourself.
2. Read `feature_list.json` and `progress/current.md`.
3. Run `./init.sh`. If it fails, stop and report.
4. Apply the effort-scaling table and the SDD flow in `.claude/agents/leader.md`.

### Anti-telephone-game rule

When you launch subagents, instruct them to **write results to files**
(e.g. `specs/<feature>/requirements.md`, `progress/impl_<feature>.md`) and
return only the reference, not the content. See `.claude/agents/leader.md` for
the full pattern.

### Language rule

- All **code, identifiers, comments, docs, specs and commit messages** are in
  **English**.
- All **user-facing application strings** are in **Castilian Spanish (es-ES)** —
  `FR-UX-01`, `FR-UX-03`, `FR-AI-07` — and live centralised in one messages
  module so the requirement stays verifiable.
- Chat replies to the human follow the human's own language.

### When this role does not apply

- Conceptual questions or repo exploration (pure reading) → answer directly,
  without launching subagents.
- Changes outside `backend/` and `frontend/` (docs, config, `progress/`) → you
  may edit them yourself.
