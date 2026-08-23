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

---

## 2026-08-17/18 — Feature 1 `project_scaffold` (tier 0) — DONE

- **Feature:** 1 `project_scaffold` (`sdd: false`, no spec phase, no approval gate)
- **Agent:** leader + 3 implementer subagents + reviewer
- **Detail reports:** `progress/impl_project_scaffold_{backend,frontend,rootwiring}.md`,
  `progress/review_project_scaffold.md`, `progress/impl_npm_hardening.md`,
  `progress/impl_gga_{findings,observations}_fix.md`

**Done:**

- Decomposed into three parts split so no two writers touch the same file.
  A (backend toolchain root) and B (frontend toolchain root) ran in parallel;
  C (root wiring: `.pre-commit-config.yaml`, `init.sh` frontend gate) ran after.
- **Reviewer APPROVED, 0 blocking defects.** All 20 acceptance criteria
  re-verified independently rather than accepted from the three reports.
- `./init.sh` fully green, exit 0, both toolchains running all seven gates:
  `ruff format`, `ruff check`, `mypy` (strict), `pytest`, `prettier --check`,
  `eslint`, `vitest`.
- **Feature 1 set to `done` in `feature_list.json` by the human.**

**Decisions taken this session:**

- **Backend pinned to Python 3.13** (`backend/.python-version`), provisioned by
  uv rather than reusing the local 3.14.6. Each member declares
  `requires-python = ">=3.13, <3.14"` — a **bounded range, not a floor**, so a
  new minor release cannot silently change the interpreter under the gates.
  (`docs/conventions.md` § *Python style* said 3.12 until 2026-08-18; corrected
  then, along with this line, which had described the constraint as a floor.)
- **2026-08-17: harden npm in place; do NOT migrate to pnpm/yarn/bun.**
  Switching package manager does not reduce registry exposure — all four install
  from `registry.npmjs.org` and differ in *defaults, not capabilities*. Measured
  exposure was small (11 direct deps, 314 transitive, 1 install script —
  `fsevents`, macOS-only, inert here; `npm audit` clean). Migrating would reopen
  feature 1's frontend acceptance criteria, `init.sh`, `.pre-commit-config.yaml`
  and add an `architecture.md` §1.3 entry. **Revisit at feature 22
  `cicd_pipeline`**, where installs run unattended with deploy credentials.
  Applied instead: `frontend/.npmrc` with `ignore-scripts=true`,
  `min-release-age=7` and `audit-level=moderate`. The research doc
  `docs/js_supply_chain_security.md` was written, read and then **deleted on the
  human's instruction** — this entry is its record.
- **A second change was applied without approval, and reverted 2026-08-18.** The
  implementer also changed all five `npx` call sites to `npx --no --`, treating
  "harden npm in place" as authorising it. The human had only asked for the `npx`
  registry fallback to be *analysed*; he never approved the edit. Reverted in
  `init.sh` and `.pre-commit-config.yaml`; `progress/impl_npm_hardening.md`
  carries the struck-through record. **A recorded decision authorises the change
  it names, and nothing else.**

**Traps and gotchas worth carrying forward:**

- **Ruff stops config discovery at the first `pyproject.toml` walking up.** In a
  uv workspace each member needs `[tool.ruff] extend = "../pyproject.toml"` or it
  silently falls back to ruff defaults — wrong line length included — *while the
  gate still reports green*. Proven empirically by the reviewer: a 102-char line
  inside a member fires `E501 (102 > 100)`.
- **`pre-commit run --all-files` can report exit 0 with every hook `Skipped`.**
  It operates on git-*tracked* files, and most of the tree is still untracked.
  Use `pre-commit run --files <real paths>` until the tree is tracked. Re-verified
  that way: all five hooks genuinely Passed, and all five *skip* on
  `prototypes/`.
- **`TZ` is not honoured for IANA zone names by Node on this Windows machine** —
  only `TZ=UTC` takes effect; everything else silently falls back to
  `Europe/Madrid`. A "passes under 5 timezones" sweep is worth almost nothing
  here. **Prove timezone determinism by construction, not by sweeping `TZ`.**
  This matters directly for feature 2.
- **An inert guard is worse than none.** Two were removed or declined on that
  reasoning: `../prototypes/**` in `.prettierignore` (Prettier resolves ignore
  patterns relative to the ignore file) and `'../backend/**'` /
  `'../prototypes/**'` in `eslint.config.js` (flat-config `ignores` match
  relative to the config base path and never begin with `../`). The real
  guarantee is cwd-scoping, and the comments now say so.
- **Closing an item leaves references that are *actively wrong*, not merely
  dated** (`AGENTS.md` §3.1). This session's own doc fix caused one: correcting
  `docs/frontend_prototype.md` from 13 to 18 colour tokens left
  `frontend/src/tokens/colors.js` citing "the 13 colour tokens is that document's
  own count". Found by `gga`, not by us.
- **`String.replace` with a *string* replacement interprets `$&`, `` $` ``,
  `$'`, `$$` and `$<name>`.** `vite-plugins/htmlMessages.js` now uses a callback,
  with a regression test asserting a message containing `` $& `` substitutes
  literally — the test is what stops someone "simplifying" the callback away.

**Doc drift fixed:**

- `docs/frontend_prototype.md` claimed 13 colour custom properties on
  `Sobremesa.dc.html:33`; the line actually carries **18** (the count omitted the
  `-2` / `-3` / `-deep` / `-soft` variants). Corrected in §2.4 and §6.1, and in
  feature 20's `blocked_reason`. All 18 are now in `frontend/src/tokens/colors.js`
  with their provenance in a comment.
- `frontend/index.html` had hardcoded `<title>Planificador semanal</title>` — an
  es-ES user-facing string outside `src/messages/`, which the acceptance
  criterion forbids unconditionally. Now `APP_TITLE` + an `%APP_TITLE%`
  placeholder resolved by a `transformIndexHtml` plugin, covered by a test and
  verified in a real `vite build`.

**`gga` review round:** first run FAILED with 3 findings, **all three verified
correct against the files before acting**. Second run PASSED with 2 observations,
both actioned. Third run PASSED clean. Note `gga` could not execute the gates in
either run (permission prompts blocked `npm run lint`, `npm test` and
`./init.sh`) — its verdict is a **static** read. The gates were run independently
by the leader.

### Open questions left for the human

1. **Feature 22 `cicd_pipeline`** is human-owned and unwritten. CI runs installs
   unattended with deploy credentials, so the same posture should be reflected
   there: `npm ci` (lockfile-exact) rather than `npm install`; decide whether CI
   inherits `frontend/.npmrc` or needs the settings passed explicitly; and check
   whether `ignore-scripts` is viable there given the build must still run.
2. **Plain `npx` has a registry fallback, at five call sites** (`init.sh` and
   `.pre-commit-config.yaml`). When a binary does not resolve locally — a typo, a
   missing `node_modules`, a renamed package — `npx` downloads and executes
   whatever the registry returns for that name. `npx --no --` removes the
   fallback and changes nothing when the binary resolves locally (verified:
   `npx --no -- eslint --version` → `v9.39.5`, exit 0; `npx --no -- cowsay` →
   refused, exit 1). It was applied without approval and **reverted 2026-08-18**.
   Open for the human to decide on merit. `pnpm dlx` / `yarn dlx` / `bunx` share
   the hole, so migrating would not fix it.
3. **`frontend/src/locale.js` — `formatDate` passes no `timeZone`**, so it renders
   in the browser's zone. Not a violation today (`conventions.md` only requires
   the *locale* pinned, and week computation is backend domain code). But
   `architecture.md` §4 invariant 7 requires every user to agree on which week is
   current, so when feature 20 renders day labels a user outside Madrid could see
   a different day than the backend scoped. **Decide this in feature 20's
   `design.md`, not in the scaffold.**

### State at close

- **Feature 1 `done`.** First code in the repo. Both toolchain roots green.
- Work is **staged but not committed** (`git status`: 50 paths in the index).
- **P1 closed** (DynamoDB, single table) · **P7 closed** (React/Vite/Vitest).
  **P2–P6 pending and human-owned.**
- Next actionable: **feature 2 `week_calendar`** (tier 1, `"sdd": true`,
  `depends_on: [1]`) — the **first real SDD cycle**: full `spec_author` pass and
  the human approval gate at `spec_ready` before any code.
- Still owed by the human: P2–P6; the `NFR-AI-01` enforcing cost cap (G-81); the
  `al gusto` / `lomos` / `hoja` unit decision.

---

## 2026-08-18 — Feature 1 committed in slices · Feature 2 `week_calendar` implemented and approved

- **Features:** 1 `project_scaffold` (committed) · 2 `week_calendar` (`in_progress`, approved by the reviewer, **awaiting the human's `done`**)
- **Agents:** leader + `spec_author` + `implementer` ×2 + `reviewer` ×2
- **Detail reports:** `specs/week_calendar/{requirements,design,tasks}.md`,
  `progress/impl_week_calendar.md`, `progress/review_week_calendar.md`

**Done:**

- **Feature 1 committed as five work-unit slices** (`be30f54` → `d48fdbe`):
  backend workspace, frontend toolchain, root wiring, npm hardening, closure.
  Each slice leaves the repo working on its own.
- **Feature 2 through the full SDD cycle** — the first real one in this repo.
  22 EARS requirements, 41 tasks, **30 tests**, all seven gates green.
  Reviewer verdict: CHANGES_REQUESTED (F1–F7), then **APPROVED** after fixes.

**Decisions taken by the human this session:**

- **The unapproved `npx --no --` change was REVERTED.** It had been applied under
  cover of the 2026-08-17 "harden npm in place" decision, which never named it.
  `frontend/.npmrc` stands; the `npx` registry fallback is back to being an
  **open finding awaiting a decision**, recorded in the feature 1 entry above.
- **RULING: `domain/` functions take a plain `date` or instant, never a `Clock`.**
  The `Clock` protocol lives in `ports/`; only `application/` reads it, once.
  Binding on **all of tier 1 (features 3–13)**, not just feature 2. Raised
  because `docs/architecture.md` §3 ("domain: … no clock") and `docs/specs.md`'s
  own task example (`current_week(clock)` in `domain/`) contradicted each other.
  `docs/specs.md` has been corrected.
- **`tzdata` approved, dev group only.** Required: `ZoneInfo("Europe/Madrid")`
  raises `ZoneInfoNotFoundError` on this Windows machine, so nothing in this
  feature is testable without it. Verified absent from all three
  `uv export --no-dev` closures; `planner-core` still declares
  `dependencies = []`.
- **The reviewer now runs automatically** after every implementer, never asked.
- **Standing rule: never commit or touch the repo unasked.** Read-only checks
  are always fine. The **human** commits, and the **human** marks a feature
  `done` — no agent does either.
- **`FR-MENU-01` added to feature 20 `frontend_spa`'s `covers`** (review F6):
  "shall **present** two live weeks" is not backend work, and feature 2 was the
  only feature citing it.
- **Contract-suite gap deferred, dated** (review F2), recorded in
  `CHECKPOINTS.md` under C4 itself: **feature 14 `persistence_ports`** adds the
  `Clock` contract suite, and the first `SystemClock` must not land before it.

**Traps and lessons worth carrying forward:**

- **A recorded decision authorises the change it names, and nothing else.**
  Research surfaces a second defect next to the one being decided; fixing it
  under the first decision's cover means it ships unreviewed. That is exactly
  how the `npx` change got in — and because feature 1 was never committed, it
  never appeared as an isolated diff anywhere.
- **The telephone game is real and it happened here.** `design.md` §5 correctly
  reported two doc defects at spec time. The human fixed both. The implementer
  then **copied the claims forward without re-reading the files**, so its report
  told the human to redo work already done. Caught as review finding F1. This is
  `AGENTS.md` §3.1: a closed item's references become *actively wrong*, not
  merely dated.
- **Count, do not eyeball.** Review finding F5 listed three requirements
  combining two `SHALL`s (R4, R8, R22). A mechanical count of every requirement
  found a **fourth — R16** — that a review specifically hunting for the pattern
  had missed. The rule is now an explicit checklist item in
  `.claude/agents/spec_author.md`, with "check this mechanically" spelled out.
- **`gga` is not deterministic.** Two `--no-cache` runs on an identical tree
  returned FAILED then PASSED, classifying the same item as a violation once and
  an observation once. It also caches by file content (so the pre-commit hook's
  bare `gga run` may review nothing), its `STRICT_MODE` parser rejects its own
  passing review when the model emits `## STATUS: PASSED`, and its
  `FILE_PATTERNS` exclude `.sh`, `.yaml` and Markdown — three of feature 1's
  five commits got "No matching files staged". **A FAILED from gga is a prompt
  to go look, not a fact**, and it cannot execute the gates at all.
- **Mutation testing is now the standard for "is this green real?"** The
  implementer falsified seven guarantees; the reviewer refused to relay those as
  evidence and ran **eleven of its own**, reporting where its counts disagreed.
  Both restored from scratchpad copies and verified byte-identical. No git write
  command was used at any point by any agent.

**Still open, for the human:**

1. **Feature 2 is not `done`.** Reviewer approved; the sign-off is the human's.
2. **Feature 2 is uncommitted**, along with this session's doc and process
   corrections. Nothing is staged.
3. **`npx` registry fallback** (feature 1 entry, open question 2) — decide on
   merit.
4. **Review F7:** `ruff`'s isort treats `support` as third-party in the test
   modules, so `from support.fakes import FakeClock` sorts above `planner_core`.
   Fixing it means a `known-first-party` setting in shared config. Cosmetic.
5. `formatDate` pins no `timeZone` — still deferred to feature 20's `design.md`.

### State at close

- **Feature 1 `done` and committed** (5 commits, `be30f54`…`d48fdbe`).
- **Feature 2 `in_progress`**, spec approved, implementation approved,
  **uncommitted**. `./init.sh` green, 30 tests.
- **P1 closed** (DynamoDB) · **P7 closed** (React/Vite/Vitest). **P2–P6 pending
  and human-owned.** New this session: the domain/`Clock` layering ruling.
- Next actionable: **feature 3 `text_and_units`** (tier 1, `"sdd": true`,
  `depends_on: [1]`) — needs the full `spec_author` pass and the human approval
  gate before any code.

---

## 2026-08-19 — Feature 2 `week_calendar`: `SystemClock` decision, six review rounds, APPROVED

- **Feature:** 2 `week_calendar` — **`in_progress`, reviewer-APPROVED, awaiting the human's `done`**
- **Agents:** leader + `implementer` ×2 + `reviewer` ×4 (rounds three to six)
- **Record:** `progress/review_week_calendar.md` (six rounds, append-only),
  `progress/impl_week_calendar.md` (Addenda 2–3)

**The decision that drove the session.**

**`SystemClock` is a default implementation, not an adapter** — `docs/architecture.md`
**§1.2.2**, decided by the human 2026-08-18. A port implementation importing
nothing outside the standard library ships **beside its `Protocol`** in
`planner_core/ports/`; only implementations pulling an external dependency
(`boto3`, an AI SDK) are adapters and live in the Lambda that owns it.

It began as a challenge to a claim the leader had repeated without checking —
*"adapters are Lambda-owned"*. `architecture.md` §3.1 rule 3 scopes that to
adapters **that import an AWS SDK**; a `SystemClock` imports nothing, so the
reasoning never applied. Java ships `Clock.systemUTC()` in `java.time`; .NET
ships `TimeProvider.System` in the BCL. Duplicating a three-line clock across two
Lambdas would have meant two chances to write `datetime.utcnow()`, which returns
a **naive** value — the exact footgun `NaiveInstant` exists to catch.

**The lesson of the six rounds, and it is the durable one.**

Rounds three and four each fixed stale prose **by writing new prose**, and every
restatement became the next round's finding:

- Round 3 — five statements of "no `datetime.now()` in `core`" left absolute
  after the exception landed. **Two were agent definitions**: `reviewer.md` would
  have rejected code the human had just approved, `implementer.md` would have
  refused to write `SystemClock`.
- Round 4 — three more, **two introduced by round three's own fixes**. One told a
  reviewer to reject `SystemClock()` construction outside `wiring.py`, which the
  guard *requires* the port's test to do.
- Round 5 — the strategy changed to **pointer-not-paraphrase**: delete the
  restatements, name `test_no_ambient_time.py` as the authority. One residue left.
- Round 6 — that residue closed by **making the claim true rather than smaller**.

> **Standing pattern: do not restate a rule in prose next to the mechanical check
> that enforces it. Point at the check.** A paraphrase is a second claim needing
> its own verification; `.claude/agents/` is the worst place for one, because a
> stale instruction makes an agent act against the architecture.
>
> And when a rule gains an exception, **`grep` for every statement of that rule** —
> `docs/`, `CHECKPOINTS.md`, `.claude/agents/` — then **judge each hit**. Two
> candidates were correctly left alone (`docs/verification.md:89` forbids
> *mocking*, still true; `tasks.md` T44 already stated its exclusions inline).

**Other decisions by the human this session:**

- **R2 amended** to carry its own exception. It had become **false as written**:
  `clock.py` calls `datetime.now(UTC)` while R2 forbade it "anywhere in
  `planner_core`", and the test proving R2 passed only because the scan skipped
  that line. `docs/specs.md:73` makes a requirement unverifiable if no test proves
  its exact statement.
- **A fourth double-`SHALL` requirement, R16**, found by counting mechanically
  after a review listed only three. The rule is now an explicit item in
  `.claude/agents/spec_author.md` — *"check this mechanically"*.
- **P3 closed by adding enforcement, not by weakening the claim.** Rule 6 said the
  guard *"enforces both halves mechanically"*; it enforced one. Proven: an
  `application/`-layer `SystemClock()` passed 34/34. Now
  `test_no_core_module_but_the_port_names_the_real_clock` catches it — verified
  independently by the leader on a scratchpad copy. **Rule 6 needed no edit: its
  sentence became true.**

**Verification standard now established:** mutation testing. The implementer
falsified seven guarantees, then four, then four more; the reviewer refused to
relay any of them and ran **eleven, ten and its own P3 case**, reporting where
counts disagreed. Every mutation on scratchpad copies, byte-identity confirmed by
SHA-256. **No agent ran a git write command at any point.**

### State at close

- ~~**Feature 2 `in_progress`, APPROVED, ready to close.**~~ **CLOSED 2026-08-19:
  status set to `done` on the human's instruction.** Round six: *"Nothing
  remains."* 46/46 tasks, 23 requirements, **35 backend tests**, `./init.sh` exit 0.
- ~~**Everything is uncommitted** — feature 2, §1.2.2, and every doc correction.
  Last commit is still `d48fdbe` (feature 1). Nothing staged.~~ **Superseded
  2026-08-19: committed as `25ab9ea`, working tree clean.**
- **P1** (DynamoDB) · **P7** (React/Vite/Vitest) · **§1.2.2** (default
  implementations) closed. **P2–P6 pending, human-owned.**
- Next actionable: **feature 3 `text_and_units`** (tier 1, `"sdd": true`) — full
  `spec_author` pass and the approval gate before any code.
- Open by the human's own decision, none owned by feature 2: review **F5**
  (four accepted double-`SHALL` requirements), **F7** (`ruff` isort groups
  `support` as third-party), the **C4** `Clock` contract-suite deferral to
  feature 14, and the `npx` registry fallback from feature 1.

---

## Session 2026-08-19 — close feature 2, spec feature 3

**Goal:** close feature 2 `week_calendar` now that it is committed, then take
feature 3 `text_and_units` through `spec_author` to the approval gate.

### Accomplished

- **Feature 2 `week_calendar` CLOSED.** Committed by the human as `25ab9ea`
  (*"feat(backend): add main clock for calendar"*), then set `in_progress` ->
  `done` on his explicit instruction. `./init.sh` exit 0, all seven gates green,
  35 backend tests. `done: 2`, no `in_progress`.
- **The previous session's own close-out record was annotated**, not left to
  rot. Its "State at close" claimed feature 2 was still open and the tree
  uncommitted — both true when written, both false the moment he committed.
  Struck through inline and dated, per the house strike-through-not-delete
  pattern.
- **Feature 3 `text_and_units` specced and left at the gate.**
  `specs/text_and_units/{requirements,design,tasks}.md`, **22 requirements,
  27 tasks**, status `pending` -> `spec_ready`. No code written.

### Verified independently, against the source files

The `spec_author` report was checked rather than relayed — the failure mode that
cost feature 2 three review rounds:

- 22 R-blocks, **exactly one `SHALL` each**, every one carrying an `Implements:`
  line. Counted mechanically, 0 violations.
- The only ids cited are `FR-SHOP-03` and `FR-LIB-05` — exactly feature 3's
  `covers`. Both quoted accurately from `docs/requirements.md`.
- `docs/architecture.md` **§2.1** lists the literal unit list as *"decide these
  in a spec, not in chat"*. Proposing it is correct and it is **not** a pending
  §2 item, so nothing here is blocked.
- `G-39` confirms the enumeration was left to the design as an implementation
  detail — and, importantly, calls it *"freely revisable in code"*. The design
  frames the choice as more permanent than `G-39` does. What does not
  retro-convert is data already stored; the vocabulary itself can widen later.
- `docs/data_model.md` §2 (line 147, *"Same treatment `FR-SHOP-03`"*) and §5.2
  (line 331, *"`fold()` is shared with `FR-SHOP-03`'s ingredient
  normalization"*) confirm the fold is shared with the **username reservation
  key**. That is what makes the `ñ` question a data decision rather than a
  code one.

### State at close

- **Feature 3 `spec_ready`, waiting at the human approval gate. No code until
  he answers.** Three decisions, all in `specs/text_and_units/design.md` §10:
  1. **The unit vocabulary.** Proposed: `g`, `ml`, `unit` — one per dimension,
     because `FR-SHOP-03` forbids cross-unit conversion, so `kg` beside `g`
     splits the shopping list permanently. Cost: the list reads `2500 g`.
     Alternative: `G-39`'s parenthetical five.
  2. **`ñ` survives the fold** (`piña` != `pina`); only vowel accents and `ü`
     fold. Load-bearing because of the shared `fold()` above.
  3. **`UnknownUnit` carries no Castilian text**, only the rejected value.
     Features 9 and 12 own their own messages; the backend messages module's
     shape still depends on P5.
- **Uncommitted:** `feature_list.json`, `progress/current.md`,
  `progress/history.md`, and the untracked `specs/text_and_units/`. Last commit
  is `25ab9ea`. Nothing staged — no agent ran a git write command.
- `./init.sh` exit 0: `done: 2, spec_ready: 1, pending: 11, blocked: 9`.
- **P1** (DynamoDB) · **P7** (React/Vite/Vitest) · **§1.2.2** (default
  implementations) closed. **P2-P6 pending, human-owned.**
- Open by the human's own decision, none owned by any active feature: review
  **F5** (four accepted double-`SHALL` requirements in feature 2's spec),
  **F7** (`ruff` isort groups `support` as third-party), the **C4** `Clock`
  contract-suite deferral to feature 14, and the `npx` registry fallback.
