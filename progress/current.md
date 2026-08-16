# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

- **Feature in progress:** _none_
- **Agent:** —

## Plan

_Nothing in progress._ The last session's record is in `history.md`
(**2026-08-16 · Data-model closure, P1, and both reviews brought current**).

## Where things stand

**Design is finished. No code exists. No feature has been through
`spec_author`.**

| Area | Status |
|---|---|
| Requirements | Frozen, complete (~90 `FR-*`/`NFR-*`). Seven owner-directed freeze lifts, Parts I–O |
| Access-pattern catalogue | **Closed.** 27 patterns, compliant. `docs/data_model.md` §4 |
| Data model | **Closed and verified.** 9 item types, one `data` table, no secondary indexes. `docs/data_model.md` §1 |
| Architecture | **P1 closed** (DynamoDB, single table). **P2–P7 still pending and human-owned** |
| Code | None |

**No sheet edit is outstanding. Nothing is awaiting an owner decision.**
Part P (G-80) closed the last one on 2026-08-16.

### Re-verification pass — 2026-08-16

Sheet re-parsed from disk at the **14:23 save** (unchanged since the last pass).
**27 patterns, 9 item types, no secondary indexes — the design is sound and no
defect was found in it.** Both review docs' model tables and Appendix A match
the sheet cell for cell; D34 is applied (`LockLista` = `COMPRA#<idLista>`).

Independently re-checked rather than inherited: all three shared-partition byte
orderings (`I`<`N`, `D`<`I`, `I`<`L`), the `numeroDia`→`numeroComida`→`idPlato`
week ordering, and that every returned attribute is stored, key-derived, or
resolved at read time by an explicit rule.

**Eleven documentation defects found and fixed this pass** (agent's job, not the
owner's). The two that could have misled an implementer:

1. `access_patterns_review.md` §4/§6 still claimed `FR-ARCH-04`'s
   reverse-chronological browse was "a descending range read **for free**".
   **D27 refuted this** — `idSemana` landed in the *partition* key, which
   DynamoDB cannot list or sort. Unparking the archive costs arithmetic id
   generation or an index. Corrected in both sections.
2. `data_structure_review.md` §0 scoped **out** "rows 38–43 (`EJEMPLOS`)". Rows
   have shifted; 38 and 39 are now `DatosRegla` and `DatosPeticionIA` — two live
   item types. Re-anchored to the `EJEMPLOS` marker instead of row numbers.

Also fixed: the stale "last saved 2026-08-15 21:00" header, the D21 row still
reading "open / seven rows", "three implementation notes" listing two, the
row-numbered §3 headings (and `DatosBiblioteca` → `DatosPlatoBiblioteca`), "the
freeze was lifted twice" (it was seven times, Parts I–O), "§6 and §7 are both
open" (neither is), finding 12's ⚠ "amendment outstanding" (Parts L and N did
it), the withdrawn §5 real-time recommendation, and one `idPlatoDefinitiva`.

`feature_list.json` #6 `rules_model` carried a live desync — acceptance required
"rule edits carry author attribution", which **G-76 removed**. Rewritten to state
that a rule stores no author. `init.sh` green, JSON re-validated.

### Part P (G-80) — derived-artifact resync, 2026-08-16

Two explicit owner lifts, one per document. **No requirement was amended and no
new decision taken** — Part P only propagates G-74, G-75, G-76 and G-79 into
derived artifacts that were missed when those decisions landed.

- `app_user_stories.md` **US4** — struck "definitive selections" (G-79), "rule
  edits" (G-76), "shopping list items" (G-75); candidates and library recipes
  survive
- `app_user_stories.md` **US16** — struck "and who made them definitive", which
  *is* the removed `FR-SUM-02` (G-79)
- `requirements.md` **§13 matrix** — dropped `FR-SUM-02` (US16) and `FR-SHOP-11`
  (US22, US23), plus a note recording that removed ids are **dropped** from the
  matrix, not struck. **G-68 already set that convention** when it dropped
  `FR-LIB-06` from US17/US18; G-74 and G-79 struck their requirement rows but
  never cleaned the matrix
- `gaps_and_resolutions.md` — **Part P / G-80** added
- `coverage_analysis.md` — G-80 indexed; counter advanced to "G-01 to G-80,
  Parts A–P". Otherwise verified clean row by row

Freeze lifts now total **eight** (Parts I–P). `init.sh` green after the edits.

### `docs/data_model.md` created — 2026-08-16

**Owner is deleting both review records.** Their content was extracted into
**`docs/data_model.md`**, now the persistence source of truth: the table and its
9 item types (§1), key formats and their traps (§2), shared-partition sort order
(§3), all 27 patterns → concrete operations grouped by entity (§4), concurrency
(§5), read-time resolution (§6), **settled-do-not-reopen (§7)**, verified
constraints (§8), parked scope (§9).

§7 is the section that earns its place: it carries the **rejected alternatives**
— why a login GSI, indexed library filters, a separate lock partition and a
denormalized `nombrePlato` were each considered and rejected. That is what stops
a future session re-litigating settled ground once the review history is gone.

All live references repointed: `AGENTS.md` §2, `architecture.md` §1.2.1,
`feature_list.json` #19, and this file's authority table. Two persistent agent
memories that named `data_structure_review.md` §1.1 were updated to
`data_model.md` §2.

### Part Q (G-81) — the last dangling reference, 2026-08-16

Owner lift for `coverage_analysis.md`. **No requirement amended**; like Part P,
pure repair.

`coverage_analysis.md` §4 closed with the project's one outstanding human-owned
question — `NFR-AI-01` needs an *enforcing* cost-cap path, and AWS Budgets only
alert — then deferred with "See `access_patterns_review.md` §7". **That question
is still open**, so unlike the other surviving references this one was not
historical: it pointed at reasoning for a live decision that was about to be
deleted.

Fixed by making the paragraph self-contained and giving the question a durable
home in **`feature_list.json` #17 `ai_lambda`** — the feature whose code the
answer changes, already `blocked` on P4, and read every session by `init.sh`. A
review document was never a good home for an open question: it is a working
record, deleted when the work finishes, which is exactly what happened.

**Deliberately left:** three references in `gaps_and_resolutions.md` (Parts I, K,
L). They are historical citations inside dated records — accurate about where
reasoning lived when each decision was taken. **A dangling reference in a
historical log is correct; one attached to an open question is not.** Recorded in
Part Q so nobody "fixes" them later.

Gap numbering now **G-01–G-81, Parts A–Q** (nine freeze lifts).

### Discoverability fix — 2026-08-16

The catalogue and model are fully documented, but the **entry path pointed
outside the repo**. `architecture.md` §1.2.1 sourced the 27 patterns to
`Desktop/lab-final-patrones-acceso.xlsx` — not in git, not on any other machine —
and never named **Appendix A**, the in-repo copy that exists so the catalogue can
be read without Excel. `AGENTS.md`'s repository map listed neither review
document, so an agent following the documented cold-start path could reach the
model only by accident.

Fixed: `architecture.md` §1.2.1 now names Appendix A and §7.2 as the in-repo
sources (spreadsheet still wins when present); `AGENTS.md` §2 now lists both
review docs with when to read them. This matters because the pointer table in
**this file is deleted at session close** — it was the only durable link.

## Next step

The next real pass is **specs**. Two features are actionable today:

1. **Feature 1 `project_scaffold`** — tier 0, `"sdd": false`, so it skips the
   spec gate and goes straight to `implementer`. The uv workspace, ruff, mypy,
   pytest, pre-commit. `./init.sh` names it as the next actionable feature.
2. **Feature 2 `week_calendar`** — the first real SDD cycle, through
   `spec_author`. Tier 1, needs zero architecture, and it consumes the
   `idSemana` format below.

Features 2–13 are all tier 1 — pure domain logic, buildable with only P1
decided. Feature 14 `persistence_ports` became actionable when P1 closed.

> **The owner said not to start any features yet (2026-08-16).** Confirm before
> launching `spec_author` or `implementer`.

## Read before writing any persistence code

`docs/data_model.md` **§2**. The spreadsheet carries key *templates*; §2 carries
the *formats*, and they exist nowhere else. Four carry a trap:

- **`idSemana`** = `<isoYear>-W<ww>` — the ISO week-numbering **year**, not the
  calendar year (2026-12-28 → `2027-W01`). Wrong once a year, on a rollover week
- **`idPlato`** = a **time-sortable** id (ULID/KSUID), never a UUIDv4. It is the
  last SK segment, so it *is* the in-slot candidate ordering. A UUID satisfies
  every other constraint and shuffles the list silently
- **`numeroDia`** 1–7 and **`numeroComida`** 1–2 — both 1-based. `numeroDia` is
  `date.isocalendar()[2]`, **not** `date.weekday()`; they differ by one and the
  mistake passes every test written on a Monday
- **`idPeticionIA`** = a deterministic hash of the AI request, never a fresh id
- **The username reservation key** is folded (case + accents) in application
  code. **Fold only when creating a reservation. To delete one, look its key up
  (`begins_with(SK, 'NOMBRE#')`, match on `idUsuario`) — never re-fold the old
  name** (D31)

## Implementation notes to carry into specs

1. **D30** — the shopping-list lock must compare `ttl` explicitly
   (`attribute_not_exists(SK) OR ttl < :now`) and release conditionally on
   `ownerId`. DynamoDB TTL deletion lags up to 48h; trusting it to expire the
   lock wedges re-sync. **The one note that causes a real outage if implemented
   naively.**
2. **Read AP18 and AP21 with `begins_with(SK, 'INGREDIENTE#')`** so `LockLista`
   is never returned as a shopping row. It is a *key condition*, not a filter —
   it costs nothing.
3. **Alias attribute names with `ExpressionAttributeNames`** in every condition
   and update expression. `ttl` in particular must be checked against DynamoDB's
   reserved-word list; aliasing unconditionally sidesteps the question.
4. **Four patterns take a second read by design** — AP3/AP6 (login two-hop),
   AP22 (`nombrePlato` resolved from the library, B2), AP8/AP9 (`añadidoPor` is
   an id). All are key lookups; none needs an index. **Do not "fix" these by
   denormalizing** — that is exactly what §1 rule 4 forbids.
5. **D33** — AP8 reads full recipe content it does not return. Inside one 1MB
   page at this scale. Recorded so it is not rediscovered as a surprise; do not
   build a thin index item now.

## Waiting on the human

- **P2–P7** in `docs/architecture.md` §2. Hitting one means the feature is
  `blocked` — that rule is unchanged. P1's closure was a **one-time exception**
  and is not standing permission.
- **`frontend/src/Sobremesa.dc.html`** and **`frontend/src/support.js`** appeared
  untracked on 2026-08-16. They look like the **initial frontend code drop** that
  P7 and feature 20 wait on. **Not opened** — the owner has not said to.

## Standing instructions

- **Re-read the spreadsheet from disk at the start of any turn that touches
  it.** The owner edits and saves mid-conversation — it changed nine times in
  one session, and twice during 2026-08-16. No Python on this machine: unzip the
  `.xlsx` and parse `xl/worksheets/sheet1.xml` against `xl/sharedStrings.xml`
  with Node (v24). **Match `<si\s*/>|<si>([\s\S]*?)</si>`, use a lazy attribute
  group, then print with explicit column letters** — a naive regex silently
  misaligns the table and produces a plausible but wrong reading.
  **Unzip inside the scratchpad using an absolute path.** `cd "$TMPDIR" || cd
  <scratchpad>` once resolved elsewhere and scattered `xl/`, `_rels/`,
  `docProps/` and `[Content_Types].xml` across the repo root.
- **Key formats go in `data_model.md` §2, never in the spreadsheet.** The workbook is the catalogue plus key *templates*; formats,
  folding rules and id-generation constraints do not belong in it — no extra
  column, no note, no example row. Settled convention (D28), reaffirmed
  2026-08-16.
- **Keeping the review documents current is the agent's job, not the owner's.**
  Refresh §1 from disk on every pass, and never let a status table contradict
  the prose above it. Do not report doc drift as a finding for the owner to
  action — fix it.
- **Do not raise committing, staging or version control.** The owner commits on
  his own schedule and has said so.
- **State a defect in one sentence before giving the fix.** Leading with the
  remedy and the trade-off cost three round trips on D31.
- **Before debating how to reconstruct a value, check whether it needs
  reconstructing at all.** D31 was framed as store-vs-re-derive; the answer was
  neither.
- **Row numbers and AP numbers are positions, not identifiers.** Rows get
  inserted; refer to patterns by title and item types by name. This applies to
  `APn` references written in earlier sections of the review documents too.
- **Rows below `EJEMPLOS` are AWS-course template scratch** (`CURSO#`,
  `ESTUDIANTE#`, `MODULO#`). Not authored decisions; do not audit them.
- **The frozen docs need a fresh, explicit lift every time.** No permission is
  standing. Each lift is a new lettered Part with continuous `G-nn` numbering;
  removed requirements are struck through inline, never deleted.
- **When a decision ripples, name the complete affected set and ask for approval
  on all of it** — do not amend only the ids the owner happened to mention.
- **Real-time does not belong in the access patterns.** Do not raise it.
- **The two architecture documents are not to be reconciled.**
  `decisiones_arquitectura.md` is the owner's personal record, permanently.
  `architecture.md` §2 stays authoritative for what is pending — do **not** read
  the other file as unblocking anything.
- **Verify claims about what was parked before raising them as defects.** A past
  session listed the archive as a gap that had already been parked by decision.
  The parked list is `data_model.md` §9; the do-not-reopen list is §7.

## Which document is authoritative for what

| Document | Authoritative for |
|---|---|
| `Desktop/lab-final-patrones-acceso.xlsx` | The **authoring surface**, when present. Re-read from disk before acting |
| `docs/data_model.md` | **Persistence, everything.** The table (§1), key **formats** (§2), sort order (§3), all 27 patterns → operations (§4), concurrency (§5), read-time resolution (§6), settled/do-not-reopen (§7), parked scope (§9) |
| `docs/gaps_and_resolutions.md` | **Why** each requirement reads as it does — `G-01`–`G-80`, Parts A–P |
| `docs/architecture.md` §2 | What is still **pending**. P1 is closed; P2–P7 are not |
