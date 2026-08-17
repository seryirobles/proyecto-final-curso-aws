# AGENTS.md — Navigation map for AI agents

> This file is the **entry point** for any agent working in this repository.
> It is not a rulebook to memorise: it is a **map**. Read only what you need,
> when you need it (progressive disclosure).

---

## 0.0 If you are an automated code reviewer — read this first

You were handed this file as your rule set, plus the contents of some changed
files. **This file is a map, not the full standard.** It deliberately does not
restate what the other documents decide. Reviewing against this file alone
produces confident, wrong findings.

**You have file access. Use it before you conclude anything.**

1. **Never call something an undecided architecture question without opening
   `docs/architecture.md` and checking §1 first.** §1 is *Decided*; §2 is
   *Pending*. A decision recorded in §1 is settled — flagging it as pending is
   a false finding, and it has already happened once — a reviewer called the
   frontend framework "undecided" when §1.1 had already decided it.
2. **Read `docs/conventions.md` before flagging style, layering, naming,
   testing or language.** That file, not this one, is the standard.
3. **Read `docs/data_model.md` §2 before flagging anything about keys or
   persistence.** Four key formats carry traps and exist nowhere else.
4. **Check `docs/gaps_and_resolutions.md` before flagging a missing feature.**
   Roughly 80 gaps are resolved there, many by *deliberate removal*. Absence is
   usually a decision, not an oversight.
5. **`prototypes/` is read-only reference material and is excluded from review.**
   If a file from it ever reaches you, the correct finding is that the exclusion
   is broken — not anything about the file's contents.

If you cannot verify a claim against a document, **say so and lower the finding
to a question.** Do not phrase a guess as a violation.

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
| `docs/architecture.md` | What "good work" means here; decided vs pending architecture. **§1 = decided, §2 = pending. Authoritative for both** | Before implementing |
| `docs/decisiones_arquitectura.md` | The owner's **personal** working record, permanently. **Not authoritative and not to be reconciled with `architecture.md`.** It never unblocks anything — if it and §2 disagree, §2 wins | Only if the owner points you at it |
| `docs/data_model.md` | **The persistence source of truth.** The `data` table and its 9 item types (§1), **the key formats — which exist nowhere else, and four carry traps (§2)**, all 27 access patterns mapped to concrete operations (§4), the concurrency rules (§5), and what is settled and must not be re-opened (§7) | **Before writing any persistence code** |
| `docs/conventions.md` | Style, naming, structure, error handling, language rules | Before writing code |
| `docs/specs.md` | SDD process: EARS notation, the 3 files, the human approval gate | Before writing or reading a spec |
| `docs/verification.md` | How to prove your work functions (incl. FR traceability) | Before declaring anything `done` |
| `CHECKPOINTS.md` | Objective criteria for "correct final state" | To self-evaluate |
| `.claude/agents/` | Subagent definitions (`leader`, `spec_author`, `implementer`, `reviewer`) | If you orchestrate work |
| `backend/core/` | `planner_core`: pure domain, application, ports. Zero runtime deps. Tier 1 lives here. | To implement domain logic |
| `backend/lambda_api/`, `backend/lambda_ai/` | The two Lambda packages: handler + wiring + adapters | To implement a Lambda |
| `backend/tests/contract/` | Port suites run against both the fake and the real adapter | To verify an adapter |
| `frontend/` | The SPA (own toolchain root). **Contains source only** — reference material lives in `prototypes/` | To implement the UI |
| `prototypes/wireframe/` | The **Claude design prototype**. **Read-only reference material, outside every toolchain root**: never edit it, never lint it, never port it, and never let a build reach it | Only through `docs/frontend_prototype.md` |
| `docs/frontend_prototype.md` | Analysis of the prototype in `prototypes/wireframe/`. Executable wireframe: read it, mine it, **do not port it**. **§4 lists eleven places where it contradicts the frozen requirements** | Before writing any spec or code for a UI-facing feature |

The full tree and its rules are in `docs/architecture.md` §3. Note the backend
is a **uv workspace** (`backend/` is its root), and the frontend is a separate
toolchain root.

### Product source of truth (read-only — never edit these)

| File | What it holds |
|---|---|
| `docs/requirements.md` | The ~90 numbered requirements (`FR-*`, `NFR-*`). **The contract.** |
| `docs/app_user_stories.md` | The 27 original user stories (`US1`–`US27`) |
| `docs/coverage_analysis.md` | Story→requirement coverage audit |
| `docs/gaps_and_resolutions.md` | `G-01`–`G-81`, Parts A–Q: every ambiguity and *why* it was resolved that way |
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

## 3.1 Working conventions

Accumulated with the owner across sessions. §3 is what you must not do; these are
how the work actually goes. Each one is here because ignoring it cost real time.

**Talking to the owner**

- **Do not raise committing, staging or version control.** He commits on his own
  schedule and has said so. Mention it only when it is load-bearing for the
  question he actually asked.
- **State the defect in one sentence before giving the fix.** Leading with the
  remedy and its trade-off cost three round trips on D31. The sentence that
  worked named the broken chain, not the repair.
- **When a decision ripples, name the complete affected set and ask for approval
  on all of it.** Do not amend the ids he happened to mention and flag the rest —
  that hands his review work back to him.
- **Doc drift is agent work, not a finding to hand him.** Fix it and say you did.
- **Follow the templates as written.** `progress/current.md` resets to *its*
  template at session close, not to an improved version of it. If a template
  seems to lose something important, say so — do not quietly redesign it.

**Before asserting anything**

- **Verify an automated reviewer's findings against the docs before acting.**
  `gga` receives only `AGENTS.md` and reasons about what §2 *might* still cover;
  its headline finding has already been flat wrong once, calling the frontend
  framework undecided when §1.1 had decided it. Same standard applies to any
  agent report.
- **Verify what was parked before raising it as a defect.** The parked list is
  `docs/data_model.md` §9; the settled-do-not-reopen list is §7. A past session
  raised the archive as a gap that had already been parked by decision.
- **Before debating how to reconstruct a value, check whether it needs
  reconstructing at all.** D31 was framed as store-vs-re-derive; the answer was
  neither.

**When something changes**

- **Closing an architecture item leaves stale references that are actively
  wrong**, not merely dated. After closing one, grep its name across `docs/`,
  `AGENTS.md` and `feature_list.json`. Closing P7 left a criterion instructing an
  implementer to configure a linter that rejects the required markup format.
- **The frozen docs need a fresh, explicit lift every time** — no permission is
  standing. Each lift is a new lettered Part with continuous `G-nn` numbering,
  and removed requirements are struck through inline, never deleted.
- **Row numbers and `AP` numbers are positions, not identifiers.** Rows get
  inserted. Refer to patterns by title and item types by name.

**Persistence and the spreadsheet**

- **Key formats go in `docs/data_model.md` §2, never in the spreadsheet** (D28).
  The workbook is the catalogue plus key *templates*; formats, folding rules and
  id-generation constraints do not belong in it — no column, no note, no example.
- **If the spreadsheet is in play, re-read it from disk at the start of any turn
  that touches it.** The owner edits and saves mid-conversation. Unzip **inside
  the scratchpad with an absolute path** (a `$TMPDIR` fallback once scattered
  `xl/` and `[Content_Types].xml` across the repo root), then parse
  `xl/worksheets/sheet1.xml` against `xl/sharedStrings.xml` with Node. Match
  `<si\s*/>|<si>([\s\S]*?)</si>`, use a lazy attribute group, and print with
  explicit column letters — a naive regex silently misaligns the table and
  produces a plausible but wrong reading.

**Do not raise**

- **Real-time does not belong in the access patterns.** Settled; do not reopen.

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
