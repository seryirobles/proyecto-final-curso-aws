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

---

## Session — 2026-08-16 · Data-model closure, P1, and both reviews brought current

**Agent:** leader, acting directly (docs-only work, permitted by `CLAUDE.md`).
**Feature in progress:** none. No feature from `feature_list.json` was started —
the owner explicitly said not to.

### Goal

Re-audit everything from the previous sessions and answer whether the data model
is correct and compliant. It ended up closing the model, closing an architecture
decision, and bringing both review documents current.

### Result

**The data model is closed and verified compliant.** Nine item types in one
`data` table serving all 27 access patterns. Verified by re-parsing the sheet
from disk three times across the session — it changed twice while we worked.

**P1 (datastore) closed: DynamoDB, single table.** Written up as
`docs/architecture.md` §1.2.1; §2's P1 row struck through.
`feature_list.json` #14 `persistence_ports` moved `blocked` → `pending`;
#19's reason narrowed to P6 alone. `./init.sh` green — 9 blocked, 14 pending.

> **The owner granted a one-time, this-decision-only exception** to the
> "agents must not decide architecture" rule, so the already-made decision could
> be recorded. Verbatim: *"DynamoDb, yes, i think thats obvious. Close it. I
> allow you, this one only."* **P2–P7 remain human-owned. Not standing
> permission.**

### Findings closed this session

| # | Finding | Outcome |
|---|---|---|
| **D31** | A user rename leaked its old `NOMBRE#` reservation — old username stayed a working login and could never be reused, contradicting `FR-AUTH-17` | **Look the reservation key up** (`begins_with(SK,'NOMBRE#')`, match `idUsuario`) and delete it by the SK it actually has. Never re-fold the old name. No normalized attribute stored |
| **D32** | `LockLista` shared the shopping partition and would read back as a blank shopping row | Owner moved it out, then chose consistency instead — see D34 |
| **D34** | The lock's move left `LISTA#<idLista>` and `COMPRA#<idLista>` naming one entity | **`COMPRA#` for both.** The lock returns to the items partition; the two list reads use `begins_with(SK,'INGREDIENTE#')`, which is a *key condition* and costs nothing |
| **D33** | AP8 reads full recipe content it does not return | Measured, inside one 1MB page. Recorded, not fixed. Do not build a thin index item |
| **D21** | The `Índices secundarios` column was blank | **Blank is the finished answer** — no index is required anywhere. Stated in prose rather than annotated in the sheet, per D28 |

### Two corrections to this reviewer's own earlier verdict

1. **"All 27 patterns resolve to a single `GetItem`/`Query`/`TransactWriteItems`"
   was overstated.** Four take a second read *by design*: AP3/AP6 (login
   two-hop), AP22 (`nombrePlato` resolved from the library, because B2
   deliberately removed it from storage), AP8/AP9 (`añadidoPor` is an id). Every
   second read is itself a key lookup. **The no-index result survives; the "one
   operation" phrasing does not.** Use *"no secondary indexes, and no access path
   that is not a key lookup or a single-partition `Query`."*
2. **D23's note named AP8, AP9 and AP10** as needing `idPlatoDefinitivo`
   validation. AP10 returns a single meal and no `idPlatoDefinitivo` — nothing to
   validate. AP8 and AP9 only.

### Structural properties confirmed (recorded in `data_structure_review.md` §7.2)

- **Both `ttl` users share the attribute name** — mandatory, since DynamoDB TTL
  is configured on exactly one attribute per table. No other item type carries
  `ttl`, so nothing expires by accident.
- **The 10GB item-collection limit does not apply** — it exists only for tables
  with an LSI, and there are none. This retires the last objection to D20.
- **Two dangling-reference cases exist by design**, both resolved at read time:
  `idPlatoDefinitivo` (D23) and removed authors (`FR-SUM-03`). Deleting a library
  recipe **cannot** dangle a week meal — week meals are snapshots
  (`FR-CAND-07`), not references.

### Documents brought current

- **`docs/data_structure_review.md`** — §1 refreshed to the live model on every
  re-parse; §1.0.1 (shared-partition sort order) and §7.2 (full AP→operation
  compliance matrix) added; `idPlato` added to §1.1; §3.9's status tables rebuilt
  (they had listed six findings as both closed and open).
- **`docs/access_patterns_review.md`** — §0 still claimed data structures were
  "the next pass"; §4/§5/§6/§7 headings still said "open"; **Appendix A was a
  stale 23-pattern snapshot using superseded numbering**, replaced with the live
  27. §9.0 final verdict added, §10 carries the data model, §8.3 notes the P1
  closure.

### Method lessons

- **State the defect in one sentence before the fix.** The owner asked "what is
  the issue" three times on D31 because each answer led with the remedy and the
  trade-off. The sentence that worked: *"to rename a user you must delete the old
  `NOMBRE#` item, to delete an item you need its key, its key is the folded name,
  and nothing stores the folded name."*
- **Check whether a value needs reconstructing at all** before debating how to
  reconstruct it. D31 was framed as store-vs-re-derive; both were wrong.
- **Doc drift is agent work, not a finding to hand the owner.**

### Housekeeping

An early `unzip` landed in the repo root instead of the scratchpad, leaving
`xl/`, `_rels/`, `docProps/`, `[Content_Types].xml` and `sheet.xlsx` untracked.
Removed. **Always unzip the workbook inside the scratchpad with an absolute
path** — `cd "$TMPDIR" || cd <scratchpad>` silently resolved elsewhere.

### Noticed, not opened

`frontend/src/Sobremesa.dc.html` and `frontend/src/support.js` appeared untracked
during the session. These look like the **initial frontend code drop** that P7
and feature 20 are waiting on. The owner was told and has not yet said to read
them.

---

## Session — 2026-08-16 (continued) · Parts P and Q, `data_model.md`, discoverability

**Agent:** leader, acting directly (docs-only).
**Feature in progress:** none.

Continuation of the entry above; that summary was written before this work landed.

### Part P (G-80) — derived-artifact resync

Two explicit owner lifts, one per document. **No requirement amended, no new
decision taken** — Part P only propagated G-74, G-75, G-76 and G-79 into derived
artifacts missed when those decisions landed.

- `app_user_stories.md` **US4** — struck "definitive selections" (G-79), "rule
  edits" (G-76), "shopping list items" (G-75); candidates and library recipes survive.
- `app_user_stories.md` **US16** — struck "and who made them definitive", which
  *is* the removed `FR-SUM-02`.
- `requirements.md` **§13 matrix** — dropped `FR-SUM-02` and `FR-SHOP-11`, plus a
  note recording that removed ids are **dropped** from the matrix, not struck.
  G-68 already set that convention; G-74 and G-79 struck their rows but never
  cleaned the matrix.

### `docs/data_model.md` created — now the persistence source of truth

The owner deleted both review records (`access_patterns_review.md`,
`data_structure_review.md`). Their content was extracted first: the table and its
9 item types (§1), key formats and their traps (§2), shared-partition sort order
(§3), all 27 patterns to operations (§4), concurrency (§5), read-time resolution
(§6), **settled-do-not-reopen (§7)**, verified constraints (§8), parked scope (§9).

**§7 is the section that earns its place** — it carries the rejected alternatives
(login GSI, indexed library filters, separate lock partition, denormalized
`nombrePlato`), which is what stops a future session re-litigating settled ground
once the review history is gone.

### Part Q (G-81) — the last dangling reference

`coverage_analysis.md` §4 closed with the project's one outstanding human-owned
question — `NFR-AI-01` needs an *enforcing* cost-cap path, and AWS Budgets only
alert — then deferred to a review doc about to be deleted. Made self-contained,
and the question given a durable home in **`feature_list.json` #17 `ai_lambda`**:
the feature whose code the answer changes, and read every session by `init.sh`.

**A review document was never a good home for an open question** — it is a
working record, deleted when the work finishes, which is exactly what happened.

**Deliberately left:** three references in `gaps_and_resolutions.md` (Parts I, K,
L). They are historical citations inside dated records. **A dangling reference in
a historical log is correct; one attached to an open question is not.**

### Re-verification pass

Sheet re-parsed from disk (unchanged since the previous pass). 27 patterns, 9
item types, no secondary indexes — **no defect found in the design.** Eleven
*documentation* defects found and fixed. The two that could have misled an
implementer:

1. `access_patterns_review.md` §4/§6 still called `FR-ARCH-04`'s
   reverse-chronological browse "a descending range read **for free**". **D27
   refuted this** — `idSemana` is in the *partition* key, which DynamoDB cannot
   list or sort.
2. `data_structure_review.md` §0 scoped out "rows 38–43 (`EJEMPLOS`)". Rows had
   shifted; 38 and 39 were by then two live item types. Re-anchored to the
   `EJEMPLOS` marker instead of row numbers.

`feature_list.json` #6 `rules_model` carried a live desync — acceptance still
required rule author attribution, which **G-76 removed**.

### Discoverability fix

`architecture.md` §1.2.1 sourced the 27 patterns to a **file outside the repo**
(`Desktop/lab-final-patrones-acceso.xlsx`) and never named the in-repo copy;
`AGENTS.md`'s map listed neither review document. An agent following the
documented cold-start path could reach the model only by accident. Both fixed.

Gap numbering closed at **G-01–G-81, Parts A–Q** (nine freeze lifts).

---

## Session — 2026-08-17 · gga triage, prototype relocation, and P7 closed

**Agent:** leader, acting directly (docs, config and `feature_list.json` only —
no code written, permitted by `CLAUDE.md`).
**Feature in progress:** none. Feature 1 `project_scaffold` prepared but not started.

### Goal

The owner tried to commit and `gga` (Gentleman Guardian Angel, a pre-commit AI
review) failed on `frontend/wireframe/support.js`. Triage that, then decide
whether the repo was ready to start feature 1.

### Result

**Of gga's four findings, one was real.** The headline finding was false and was
the one that would have been acted on.

| Finding | Verdict |
|---|---|
| CDN-loaded React "quietly pre-decides" the frontend framework, so mark it `blocked` | **Refuted.** `architecture.md` §1.1 — the *Decided* section — already specified a React-based stack, before the prototype existed. There is no `package.json` under `frontend/`, so nothing in the repo *declared* React at all; the `unpkg` URLs are the prototype runtime's own boot |
| `support.js` cannot be regenerated here | True, and **what a read-only reference input is.** Not a defect |
| No `specs/` entry backs it | Same category error |
| It sits under `frontend/`, the SPA's own toolchain root, with nothing marking it non-shippable | **Upheld** |

### Prototype relocated

`frontend/wireframe/` to **`prototypes/wireframe/`**, with a new `README.md` as the
in-tree marker that was missing. Feature 1 turns `frontend/` into a real toolchain
root, and every tool it acquires would have globbed into `wireframe/` and needed
its own exclusion. Moving it makes contamination **structural rather than
configuration-dependent**.

Repointed: `AGENTS.md` §2 (plus a new `prototypes/wireframe/` row),
`frontend_prototype.md` §0/§0.1, `architecture.md` §3 tree, `feature_list.json` #20.

### gga coverage corrected — two errors of mine

1. **Framing.** I called this "a Python backend project". **It is full-stack.**
   gga's `*.ts,*.tsx,*.js,*.jsx` was therefore the *right* pattern set for
   `frontend/` and simply had **no pattern for `backend/`** — every line of
   Python, features 2–13 included, would have passed review unread. `*.py` added.
2. **"gga cannot see `architecture.md`."** False. `lib/gga/providers.sh:322` runs
   `claude --print`, so the reviewer is Claude Code *with file access*. It could
   have opened §1.1 and instead wrote "**if** `docs/architecture.md` §2 still
   lists the frontend stack as pending". It guessed where it could have checked.

The remedy was therefore in the rules file, not a workaround: **`AGENTS.md` §0.0
is new** — a block addressed to automated reviewers telling them to verify against
`architecture.md` §1, `conventions.md`, `data_model.md` §2 and
`gaps_and_resolutions.md` before asserting a violation, and to lower an
unverifiable claim to a question.

**gga gotcha, verified against the matcher at `~/bin/gga:1072`:** an
`EXCLUDE_PATTERNS` entry starting with `*` is a plain **suffix match on the full
path** and cannot express a directory — `*prototypes/*` would silently never
match. Patterns *without* a leading star are glob-matched against the full path,
so `prototypes/*` works. Recorded in `.gga`'s comments.

Also: gga reviews only the **staged** set (`--diff-filter=ACM`, so deletions and
renames are skipped), sends **whole files rather than diffs**, and its prompt is
only `RULES_FILE` plus those files.

### P7 CLOSED — idiomatic React

Two premises collapsed in sequence:

1. The owner confirmed **there is no frontend code drop coming — the prototype
   was it.** So `architecture.md` §1.1 and `conventions.md` § *Confirmed at the
   initial code drop* both described a mechanism that could never happen.
2. Web search confirmed **"DC" is Claude Design's internal authoring runtime**,
   not a distributable framework. So §1.1's "React-based **DC** framework" never
   named anything obtainable.

The owner asked for the options to be explained (he does not work in JS) and
chose **idiomatic React: function components, hooks, JSX; Vite; Vitest; ESLint +
Prettier; plain JS/ESM, no TypeScript.**

**Decided on reachable help, not on merit of style.** The alternative was
honouring `conventions.md` as written — class components and `createElement` — a
legacy shape whose every online answer would need translating first. Identical
reasoning to Prettier + ESLint over Biome. Worth remembering that the "no JSX"
and "logic class" rules were **reverse-engineered from the DC runtime**, never
chosen on merit.

Recorded following the P1 precedent: struck in §2, decided in §1.1 under
*Formerly P7*. `conventions.md` was **amended, not replaced** — the stack
paragraph, the separation table (*Logic class* to *Custom hook*), the naming table,
`matchMedia`, Testing and the templating prohibition (JSX explicitly carved out).
**Unchanged, and it is the bulk of the section:** inline CSS with a tokens module,
no CSS framework, the single es-ES messages module, no business logic in the
client, fluid-first responsiveness, the whole Do-not list.

Feature 20 `frontend_spa` is now blocked on **feature 16 alone** (REST contract, P5).
This also closes the "Noticed, not opened" item at the end of the previous entry.

### Feature 1 rescoped: 11 to 20 acceptance criteria

Now covers **both** toolchain roots. Frontend half: `package.json`, React + Vite +
Vitest + ESLint + Prettier, the `messages` and `tokens` modules, the `es-ES`
locale constant, mutual isolation of the two toolchains from each other and from
`prototypes/`, and a bootstrap mounting **one placeholder component** — no
product screens.

### Prototype extraction rule — measured, not assumed

**Colour lifts. Type and spacing must not.** The 13 colour custom properties are
all on `Sobremesa.dc.html:33` and copy verbatim. The rest was never tokenised:

| Property | Distinct values |
|---|---|
| `font-size` | **24** — including `10.5px`, `11.5px`, `12.5px`, `13.5px`, `14.5px`, `15.5px` |
| `padding` | **91** |
| `border-radius` | 19 |
| `gap` | 15 |

Twenty-four font sizes in half-pixel steps is drift, not a scale — exactly what
`conventions.md` predicts when inline styles have no shared tokens. Copying those
numbers into `src/tokens/` would defeat the module built to prevent it. Written
into `frontend_prototype.md` §2.4.

### Method lessons

- **An automated reviewer's findings get verified against the docs before acting.**
  gga reads `AGENTS.md` but not `architecture.md`, so it reasons about what P2–P7
  *might* cover and guesses wide.
- **Closing an architecture item leaves stale references that are actively
  wrong**, not merely dated. Closing P7 left feature 1's ESLint criterion reading
  *"no JSX plugin — conventions.md forbids JSX files"*, which would have had an
  implementer configure a linter that rejects the required markup format. Grep
  the item's name afterwards — and note `AP7` is an access pattern, a false positive.
- **Check `git status` before claiming a filesystem move is done.** The move left
  the old paths staged (`AD`), so gga would have flagged the same file at the same
  path; the exclusion was inert until the index was synced.

### Housekeeping

`docs/decisiones_arquitectura.md` was referenced **nowhere durable** — the rule
that it is the owner's personal record and must not be reconciled with
`architecture.md` lived only in `progress/current.md`, which is wiped at session
close. Added to the `AGENTS.md` §2 map, where a fresh session will actually see it.

### Standing instructions as they stood at session close

Carried here because `progress/current.md` resets to its template. These are
working rules accumulated across sessions, not findings from this one.

- **Do not raise committing, staging or version control.** The owner commits on
  his own schedule and has said so.
- **State a defect in one sentence before giving the fix.** Leading with the
  remedy and the trade-off cost three round trips on D31.
- **Verify an automated reviewer's findings against the docs before acting.**
  `gga` reads `AGENTS.md` but never `architecture.md`, so it guesses wide about
  what P2–P6 cover. Its headline finding has already been flat wrong once.
- **When a decision ripples, name the complete affected set and ask for approval
  on all of it** — do not amend only the ids the owner happened to mention.
- **Closing an architecture item leaves stale references that are actively
  wrong.** Grep the item's name across `docs/`, `AGENTS.md` and
  `feature_list.json` afterwards.
- **The frozen docs need a fresh, explicit lift every time.** No permission is
  standing. Each lift is a new lettered Part with continuous `G-nn` numbering;
  removed requirements are struck through inline, never deleted.
- **Doc drift is agent work, not a finding for the owner to action** — fix it.
- **Before debating how to reconstruct a value, check whether it needs
  reconstructing at all.** D31 was framed as store-vs-re-derive; the answer was
  neither.
- **Verify claims about what was parked before raising them as defects.** The
  parked list is `data_model.md` §9; the do-not-reopen list is §7.
- **Real-time does not belong in the access patterns.** Do not raise it.
- **`prototypes/` is read-only reference material.** Never edit, lint or port it.
  If a tool reaches it, exclude the tool. Colour tokens lift; type and spacing
  must not (`frontend_prototype.md` §2.4).
- **Row numbers and AP numbers are positions, not identifiers.** Refer to
  patterns by title and item types by name.
- **If the spreadsheet is in play, re-read it from disk at the start of any turn
  that touches it** — the owner edits and saves mid-conversation. Unzip inside
  the scratchpad with an absolute path and parse `xl/worksheets/sheet1.xml`
  against `xl/sharedStrings.xml` with Node. Match `<si\s*/>|<si>([\s\S]*?)</si>`,
  use a lazy attribute group, print with explicit column letters — a naive regex
  silently misaligns the table.
- **Key formats go in `data_model.md` §2, never in the spreadsheet** (D28).
- **`docs/decisiones_arquitectura.md` is the owner's personal record,
  permanently.** Never reconcile it with `architecture.md`; it unblocks nothing.
  *(Now also recorded in the `AGENTS.md` §2 map, which a fresh session reads.)*

### State at close

- **P1 closed** (DynamoDB, single table) · **P7 closed** (React/Vite/Vitest).
  **P2–P6 pending and human-owned.**
- Requirements frozen, `G-01`–`G-81`, Parts A–Q, nine freeze lifts.
- Data model closed and verified: 9 item types, one `data` table, no secondary
  indexes. `docs/data_model.md`.
- **No code exists. No feature has been through `spec_author`.**
- Next actionable: **feature 1 `project_scaffold`**, 20 acceptance criteria,
  nothing open on it. Owner gates every feature start — confirm before launching.
- Still owed by the human: P2–P6; the `NFR-AI-01` enforcing cost cap (G-81); the
  `al gusto` / `lomos` / `hoja` unit decision.
