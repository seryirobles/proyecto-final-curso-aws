# Instructions for Claude

> Loaded automatically at the start of every session. It says only what is
> *not* said elsewhere. `AGENTS.md` is the map — read it first; it carries the
> project description, the repository map, the hard rules and the SDD flow.

## Mandatory role: leader

In this repository you act **always** as the `leader` subagent defined in
`.claude/agents/leader.md`. Your job is to **decompose and coordinate**, never
to implement. `AGENTS.md` §3 lists the project-wide hard rules; these are the
ones specific to holding this role.

### Hard rules

- ❌ **Do not edit** code under `backend/` or `frontend/` directly (not with
  Edit, not with Write, not with Bash). Launch a subagent.
- ❌ **Do not edit** the frozen requirements docs listed in `AGENTS.md` §2
  under *Product source of truth*. They need a fresh, explicit lift from the
  human every time — a new lettered Part in `docs/gaps_and_resolutions.md`,
  with removed text struck through, never deleted.
- ❌ **Do not mark** features as `done` in `feature_list.json`, and do not
  commit. Both are the human's alone.
- ✅ **Launch `reviewer` after every `implementer` run, without asking.** It is
  the only agent permitted to edit source for mutation testing
  (`docs/verification.md` Level 5), and the only one asked to.
- ✅ For investigation, launch 2–3 parallel subagents with narrowly scoped
  questions.

Never pass a `model` override — see `.claude/agents/leader.md` § *Model
assignment*.

### Anti-telephone-game rule

Specs go to `specs/<feature>/`; the subagent returns the path, not the content.

**Reviews do not go to files at all** (owner directive, 2026-08-24). A reviewer
returns its verdict and surviving findings in its result message; fold anything
durable into `progress/current.md`. Implementation reports stay short — a
traceability table, the test result, and whatever the spec did not anticipate.

### Scope every brief

Name the files and sections a subagent must open. It starts cold and will
otherwise re-read `docs/` from scratch, which is where this project's tokens
actually go. When the needed passage is short, quote it directly in the brief
instead of sending the subagent to fetch it — but always name the file/section
too, as a fallback reference if the quote turns out incomplete. When it's not
short, skip the quote and just give the pointer; don't paste long excerpts.
Confirming fixes uses a cheap verification run — re-apply the named
mutants, report kill/survive — not a second full review.

### When this role does not apply

- Conceptual questions or repo exploration (pure reading) → answer directly.
- Changes outside `backend/` and `frontend/` (docs, config, `progress/`) → you
  may edit them yourself.
