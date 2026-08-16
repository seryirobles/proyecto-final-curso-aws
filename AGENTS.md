# AGENTS.md — Navigation map for AI agents

> This file is the **entry point** for any agent working in this repository.
> It is not a rulebook to memorise: it is a **map**. Read only what you need,
> when you need it (progressive disclosure).

---

## 0. What this project is

A collaborative weekly meal planner (web app, Castilian Spanish UI) built as the
final project of an AWS course. The **product requirements are already complete
and frozen**: 27 user stories, ~90 numbered requirements, 67 resolved gaps,
zero open questions. You are not here to invent product scope — you are here to
implement what `docs/requirements.md` already specifies.

**The architecture is owned by the human.** It is partially decided. See
`docs/architecture.md` §1 (decided) and §2 (pending). When a task depends on a
pending decision, you **stop** — you do not choose for them.

---

## 1. Before you start (mandatory)

1. Run `./init.sh` and check it finishes without errors. If it fails, **stop**
   and fix the environment before touching code.
   *(Windows: run it through Git Bash — the Claude Code `Bash` tool already does.)*
2. Read `progress/current.md` to see where the last session left off.
3. Read `feature_list.json`. Every feature with `"sdd": true` goes through
   **Spec Driven Development** — see `docs/specs.md` and §4 below.
4. Read `docs/specs.md` before touching any spec or any `sdd: true` feature.

## 2. Repository map

| File / folder | What it holds | When to read it |
|---|---|---|
| `feature_list.json` | Backlog with status (`pending` / `spec_ready` / `in_progress` / `done` / `blocked`) | Always, at the start |
| `progress/current.md` | State of the active session | Always, at the start |
| `progress/history.md` | Append-only log of previous sessions | When you need historical context |
| `specs/<feature>/` | `requirements.md` + `design.md` + `tasks.md` (Kiro-style) | Before implementing any `"sdd": true` feature |
| `docs/architecture.md` | What "good work" means here; decided vs pending architecture | Before implementing |
| `docs/data_model.md` | **The persistence source of truth.** The `data` table and its 9 item types (§1), **the key formats — which exist nowhere else, and four carry traps (§2)**, all 27 access patterns mapped to concrete operations (§4), the concurrency rules (§5), and what is settled and must not be re-opened (§7) | **Before writing any persistence code** |
| `docs/conventions.md` | Style, naming, structure, error handling, language rules | Before writing code |
| `docs/specs.md` | SDD process: EARS notation, the 3 files, the human approval gate | Before writing or reading a spec |
| `docs/verification.md` | How to prove your work functions (incl. FR traceability) | Before declaring anything `done` |
| `CHECKPOINTS.md` | Objective criteria for "correct final state" | To self-evaluate |
| `.claude/agents/` | Subagent definitions (`leader`, `spec_author`, `implementer`, `reviewer`) | If you orchestrate work |
| `backend/core/` | `planner_core`: pure domain, application, ports. Zero runtime deps. Tier 1 lives here. | To implement domain logic |
| `backend/lambda_api/`, `backend/lambda_ai/` | The two Lambda packages: handler + wiring + adapters | To implement a Lambda |
| `backend/tests/contract/` | Port suites run against both the fake and the real adapter | To verify an adapter |
| `frontend/` | The SPA (own toolchain root) | To implement the UI |

The full tree and its rules are in `docs/architecture.md` §3. Note the backend
is a **uv workspace** (`backend/` is its root), and the frontend is a separate
toolchain root.

### Product source of truth (read-only — never edit these)

| File | What it holds |
|---|---|
| `docs/requirements.md` | The ~90 numbered requirements (`FR-*`, `NFR-*`). **The contract.** |
| `docs/app_user_stories.md` | The 27 original user stories (`US1`–`US27`) |
| `docs/coverage_analysis.md` | Story→requirement coverage audit |
| `docs/gaps_and_resolutions.md` | `G-01`–`G-67`: every ambiguity and *why* it was resolved that way |
| `docs/gaps_pending_stakeholders.md` | `PEND-01`–`PEND-15`, all closed — historical record |

These five files are the frozen output of a completed requirements phase.
**Do not modify them.** If you believe a requirement is wrong, incomplete or
contradictory, mark the feature `blocked` and report it — do not patch the
requirement yourself.

When a resolution seems arbitrary, read its `G-xx` entry before proposing an
alternative. Most "obvious" simplifications were already considered and
rejected there, with reasons.

## 3. Hard rules (non-negotiable)

- **One feature at a time.** Never mix changes from several features in one session.
- **Never declare a feature `done` without green checks.** `./init.sh` must pass.
- **Never skip the spec phase.** Every `"sdd": true` feature goes through
  `spec_author` and gets human approval before any code is written.
- **Never skip the human approval gate.** The leader stops at `spec_ready` and waits.
- **Never write Terraform or CI/CD code.** Infrastructure and pipelines are
  human-owned (see `docs/architecture.md` §5). `init.sh` fails if generated
  IaC/CI files appear.
- **Never make an architecture decision.** If a task needs an undecided one
  (`docs/architecture.md` §2), mark the feature `blocked` and stop.
- **Never invent requirements.** Every `R<n>` in a spec must trace to an
  existing `FR-*` / `NFR-*` id.
- **Never add a dependency** without it being justified in an approved `design.md`.
- **Document as you go** in `progress/current.md`, not at the end.
- **If you do not know something, look in `docs/`** before inventing it.

## 4. Workflow (SDD)

```
pending → [spec_author] → spec_ready → ⏸ HUMAN → in_progress → [implementer → reviewer] → done
```

1. The leader picks the first `pending` feature with `"sdd": true` whose
   `depends_on` are all `done`.
2. The leader launches `spec_author`, which writes
   `specs/<name>/{requirements,design,tasks}.md` and sets the status to `spec_ready`.
3. **Pause.** The human reads the spec and approves (or requests changes).
4. Once approved, the leader sets `in_progress` and launches `implementer`.
5. The implementer executes `tasks.md` one by one, ticking each `[x]`.
6. The reviewer verifies the traceability chain and task completeness,
   then approves or rejects.
7. On approval the implementer sets `done` and moves the summary to
   `progress/history.md`.

### The traceability chain

This project has a longer chain than a typical SDD repo, because the
requirements already exist:

```
US<n>  →  FR-xxx-nn  →  R<n>  →  T<n>  →  test
story     requirement   spec    task     proof
          (frozen)      (EARS)
```

Every `R<n>` you write **must** cite the `FR-*` ids it implements. Every `FR-*`
claimed by a feature **must** end up covered by at least one test. The reviewer
checks both directions and rejects if either fails.

## 5. Session close (lifecycle)

Before finishing:

1. Run `./init.sh` — all green.
2. If the feature is finished: set `"status": "done"` in `feature_list.json`.
3. Move the summary from `progress/current.md` to the end of `progress/history.md`.
4. Reset `progress/current.md` to the empty template.
5. Leave no temp files, no debug `print()`, no context-free TODOs.

## 6. If you get stuck

- Re-read the relevant section of `docs/`.
- Check the matching `G-xx` entry in `docs/gaps_and_resolutions.md` — the
  question you are stuck on was probably already answered there.
- If a tool does not behave as expected, **do not invent a workaround**:
  record the blocker in `progress/current.md`, set the feature to `blocked`,
  and stop the session.
