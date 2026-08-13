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

---

## Session — 2026-08-13/14 · Access-pattern compliance pass

**Agent:** leader, acting directly (docs-only work, permitted by `CLAUDE.md`).
**Feature in progress:** none. No feature from `feature_list.json` was started.

### Goal

Answer one question: **are the access patterns in
`Desktop/lab-final-patrones-acceso.xlsx` complete and compliant with
`docs/requirements.md`?** Method was both directions — every `FR-*`/`NFR-*` that
implies a question of the datastore checked for a pattern that asks it, and
every pattern checked against the requirements it serves.

### Result

**Started at 23 patterns with 12 blocking defects. Ended at 27 patterns,
compliant.** Full record in `docs/access_patterns_review.md` §9.

Closed during the session: the definitive-selection invariant (1a/1b), the
missing promotion attribution (2), the homeless per-run rule override (4), the
two-directional `isPassReseteada` write (5), the unstated week ordering (6), the
`-`-returning Login (7), the rules read that could not resolve `idPlato` (8),
rule authorship (12), the `FR-SHOP-08` flag (13), read-by-username (14),
`FR-AUTH-13`'s dead shopping clause (15), `añadidoPor` on week meals (16), and
the ordering column (9).

Six patterns were added by the owner: **Obtener usuario**, **Obtener usuario por
nombre**, **Eliminar elementos marcados de la lista de la compra**,
**Establecer/Desasignar comida definitiva**, plus reshaped Login and rules reads.

### Requirements amended — five freeze lifts, all owner-directed

| Part | Gaps | Change |
|---|---|---|
| **K** | G-75 | `FR-AUTH-13` no longer claims shopping-list items are authored content |
| **L** | G-76 | Rule edits are not attributed in the MVP; a rule stores no author |
| **M** | G-77 | Re-sync never writes to a checked item; the shortfall becomes its own unchecked item carrying the **remainder**. Supersedes G-44 |
| **N** | G-78 | `FR-RT-02`'s attribution scoped to candidates and library only. Completes G-76 |
| **O** | G-79 | `FR-SUM-02` **removed** — who promoted a meal is not recorded |

`FR-SUM-02` and `FR-SHOP-08`'s flag clause were **removed**, not implemented.
Derived artifacts re-synced each time: `docs/coverage_analysis.md`,
`docs/verification.md`, `docs/conventions.md`, `docs/architecture.md`,
`feature_list.json` (#5, #8). `./init.sh` green after every lift.

### Design decisions taken

- **The definitive lives on the slot, not the meal.** `idPlatoDefinitiva` is a
  per-slot pointer; `isDefinitiva` is derived. Promote is one unconditional
  write, "replacing any previous definitive" is what overwriting a field means,
  and `FR-MENU-03`'s one-per-slot cap becomes structurally unbreakable rather
  than enforced. Concurrent promotions resolve to last-write-wins — the race
  becomes benign instead of corrupting.
- **The per-run rule override lives in the request, unpersisted.** Zero new
  patterns; the payload carries it, so a retry recomputes the same `FR-AI-08`
  hash. Rides in the SQS message.
- **Week ordering** is `numeroDia`, then `numeroComida`, then `idPlato`.
- **The ordering column means "must the datastore order or filter?"** — display
  order is UI and does not earn a `Sí`.

### Method rules learned (now §1 of the review)

- **Rule 4, added this session: the write is the record of what is persisted.**
  An attribute in a return that no write supplies is not stored — it is resolved
  live. This reviewer read `nombrePlato` on "Obtener reglas" as a denormalised
  copy and raised a staleness finding that did not exist; withdrawn.
- The write/read symmetry sweep is still worth running — it caught the genuinely
  missing `añadidoPor`. A failure means **either** a missing write **or** live
  resolution; user-authored values need a write, derived values do not.
- **Fixing the shopping list twice meant deleting requirements, not adding
  attributes** (Parts J and M). Both times the attribute existed to reconstruct
  what the check state already carried.

### Closed by owner decision, not by analysis

- **Real-time is out of scope for the catalogue.** Do not raise it again.
- **The two architecture documents are not to be reconciled.**
  `decisiones_arquitectura.md` is the owner's personal record, permanently;
  `architecture.md` stays the agent-facing contract and its §2 remains
  authoritative for what is pending. An agent must **not** read
  `decisiones_arquitectura.md` as unblocking anything.
- **`NFR-AI-01`** wants a real enforcing path — infrastructure, not a pattern.
- **`Frecuencia`'s unstated basis** — ignored deliberately.
