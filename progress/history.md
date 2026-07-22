# Session history

> Append-only. The newest entry goes at the bottom.
> At session close, move the summary from `current.md` here.

---

## 2026-07-22 — Harness bootstrap

- **Feature:** none (harness setup, not a `feature_list.json` entry)
- **Agent:** human + Claude

**Done:**

- Translated the `harness-sdd` reference harness onto this project:
  `AGENTS.md`, `CLAUDE.md`, `CHECKPOINTS.md`, `init.sh`, `feature_list.json`,
  `docs/{architecture,conventions,specs,verification}.md`, `progress/`,
  `.claude/agents/{leader,spec_author,implementer,reviewer}.md`,
  `.claude/settings.json`.
- Encoded the project's own constraints on top of the reference harness:
  requirements are frozen; architecture is human-owned and partially pending;
  agents never generate Terraform or CI (enforced by an `init.sh` tripwire).
- Built the 23-feature backlog, tiered by how much architecture each one needs.
  Tier 1 (ids 2–13) is pure domain logic and is actionable with **zero**
  architecture decided.

**Next steps:**

- Feature 1 `project_scaffold` — the uv workspace, ruff, mypy, pytest, pre-commit.
- Then feature 2 `week_calendar`, the first real SDD cycle.
- Architecture decisions P1–P7 (`docs/architecture.md` §2) remain with the human.

---

## 2026-07-23 — Frontend conventions + backend restructure

- **Feature:** none (harness refinement)
- **Agent:** human + Claude

**Done:**

- Wrote the frontend conventions from the confirmed stack (SPA, HTML + inline
  CSS, JS logic class, React-based DC framework, no templating language),
  including the fluid-first responsive rule (inline CSS cannot do `@media`).
- Restructured the backend from a flat `src/` into a **uv workspace**:
  `backend/{core,lambda_api,lambda_ai}` + `backend/tests/contract`, and a
  separate top-level `frontend/` toolchain root. `core` = `planner-core`, zero
  runtime deps; each Lambda packages its own dependency closure so `api` never
  ships the AI SDK.
- Added the **test tiers** (unit / contract-vs-fake / opt-in `@pytest.mark.aws`)
  and the **contract-test rule** that makes local mocking trustworthy.
- Propagated the new layout across every harness file: `AGENTS.md`, `CLAUDE.md`,
  `CHECKPOINTS.md`, `init.sh`, `settings.json`, all four `docs/`, the four
  agents, and `feature_list.json` (feature 1 now scaffolds the workspace;
  feature 14 gains the contract harness).

**Coverage audit (same day):**

- Mechanical diff of all 103 `FR-*`/`NFR-*` ids in `docs/requirements.md`
  against every `covers` array found **2 orphans**: FR-CAND-02 and FR-CAND-03
  (the three-way authoring flow). Fixed: FR-CAND-02 → features 5 + 20,
  FR-CAND-03 → feature 20. Result: 103/103 covered, 0 phantom ids, all 27 user
  stories transitively reach ≥ 1 feature via the §13 matrix.
- The coverage check is now a **permanent `init.sh` guardrail** (fails on any
  uncovered or unknown id) and a C6 checkbox in `CHECKPOINTS.md`.

**Open decisions (unchanged, human-owned):**

- P1–P7 in `docs/architecture.md` §2. New wrinkle recorded: whether `core` ships
  vendored per-zip or as a shared Lambda **layer** is P6.
- The frontend framework's exact identity/bootstrap idiom and test runner come
  from the human's initial code drop.
