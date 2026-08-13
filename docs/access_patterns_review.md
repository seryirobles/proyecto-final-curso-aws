# Access-pattern review — working record

## 0. Start here

**What this is.** A review of the project's access-pattern catalogue, conducted
2026-08-02/03 and continued 2026-08-09, against `docs/requirements.md`. It is a
design document, not a spec: nothing here has an approved `specs/<feature>/`
behind it and no code exists yet.

**The artifact under review lives outside the repo**, at
`Desktop/lab-final-patrones-acceso.xlsx`. It is edited live by the human, often
several times within a single session — **re-read it before acting on anything
below; this document may already be stale.** Appendix A holds a snapshot taken
2026-08-03 so this file is readable without opening Excel.

There is **no Python on this machine.** To read the spreadsheet: unzip it (it
is a zip archive) and parse `xl/worksheets/sheet1.xml` against
`xl/sharedStrings.xml` — cell values are `<v>` indices into the shared-string
table. Node is available (v24).

**Scope.** Only the access-pattern catalogue (AP1–AP23) was reviewed. **Data
structures were explicitly out of scope** and are the next pass — the PK/SK
draft below the catalogue in the spreadsheet is still full of the AWS-course
template rows (`CURSO#`, `ESTUDIANTE#`, `MODULO#`) and has not been looked at
at all.

**On the requirement changes in §3.** `CLAUDE.md` forbids agents editing
`docs/requirements.md` and `docs/gaps_and_resolutions.md`. The human authored
those requirements, owns them, and lifted the freeze twice: once on 2026-08-03
for **G-69/G-70/G-71** (Part I), and again on 2026-08-09 for the shopping-list
cuts **G-72/G-73/G-74** (Part J). Neither was a standing permission — do not
edit those files again without a fresh, explicit instruction.

**How to read §6 vs §7.** §6 is *whole areas with no pattern at all*. §7 is
*defects inside patterns that already exist*. Both are open.

---

## 1. Method — what earns a row

Three rules emerged during the review and settled several disagreements:

1. **An access pattern is a question asked of the datastore, not a screen.**
   "Create or edit user" is one screen and two questions; whole-week AI
   generation is one screen and *zero* new questions.
2. **Composition is not a new pattern.** If a run is orchestration over reads
   you already have, it gets no row. This retired both "find rules referencing
   recipe X" (the rule set is a dozen items — filter in memory) and "whole-week
   AI generation" (composition of "Obtener semana", "Obtener biblioteca",
   "Obtener reglas" and "Editar o añadir comida").
   The discriminator is **scale**: the same question earns a row when the answer
   isn't already in a read you perform anyway.
3. **What you ask and how much you carry back are independent axes.** The same
   question routinely needs two payload sizes — week grid vs. recipe detail,
   library index vs. full recipe. Most catalogues track only the first, and
   that is where the surprises live.
4. **The write is the record of what is persisted.** An attribute that appears
   in a return but that **no write ever supplies** is not stored — it is
   resolved live when the question is asked. `nombrePlato` on "Obtener reglas"
   is the worked example: the rule write carries only `idPlato`, so the name
   comes from the library at read time and cannot go stale. Read a return
   payload as *what the caller gets back*, never as *what sits in a row*.
   (Added 2026-08-14, after this reviewer read that exact payload as a
   denormalised copy and raised a staleness risk that does not exist.)

## 2. Key decisions taken

| Decision | Rationale |
|---|---|
| **Immutable surrogate ids** (`idPlato`, `idUsuario`, `idIngrediente`) replace natural keys everywhere | A key must be immutable; a name is a label the user owns. Names as keys made renames a delete+recreate and silently orphaned pin rules. `idPlato` is **globally unique**, not slot-scoped. |
| Author references store the **user id**, never the username | `FR-AUTH-17` permits reusing a removed account's username; storing the name would silently reattribute old content to a new account. |
| Removed users resolve to "Unknown" **at render time** | No fan-out write, no author index, no partial-failure window. `FR-SUM-03` already used render-time language. The lookup is "Pantalla admin - Listar usuarios" (2–10 users, one read). |
| The AI receives a **thin library projection** (`idPlato`, `nombrePlato`, `tipoAlimento`), not full recipes | In library-only/mix mode the model *selects*; the system copies content as a snapshot (`FR-CAND-07`). Ingredients and steps never influence the choice. A two-phase tool loop was considered and rejected — it pays N round trips against a call that already runs seconds to a minute-plus (`G-19`) to save ~3k tokens. |
| Idempotency records are **point lookups by request hash**, never queries, and store the **result payload** | `FR-AI-10` makes single-recipe output a *preview* saved nowhere else; without the payload a dropped response means paying for a recipe that exists nowhere and cannot be returned on retry. |

## 3. Requirement changes made during the review

Logged as **Part I** in `docs/gaps_and_resolutions.md`. All three were directed
by the requirements owner, overriding the freeze in `CLAUDE.md`.

- **G-69** (supersedes G-63) — recipes store exactly one *predominant*
  ingredient category `tipoAlimento`; library gains a category filter.
  Amends `FR-LIB-03`, `FR-LIB-04`, `FR-AI-04`, `FR-RULE-04`.
- **G-70** (supersedes G-38) — the €50/month AI cap is **global**, enforced by
  AWS cost tooling; the application stores no per-user counter.
  Amends `NFR-AI-01`.
- **G-71** — whole-week generation skips slots already holding a definitive
  (a definitive **outranks a pin rule**; the skipped pin is reported via
  `FR-AI-12`), and ingredient-category counts describe the **week's final
  state**, not the generated output. Amends `FR-AI-11`.

Logged as **Part J** (2026-08-09), the shopping-list cuts. All three are one
idea: **the shopping list stores no provenance.** An item is a name, a
quantity, a unit and a checkbox.

- **G-72** (supersedes G-21) — re-sync is **purely additive**: it adds missing
  ingredients and updates quantities on normalized name + unit, and never
  removes anything. No auto/manual marker, no manual-override state.
  Amends `FR-SHOP-04`, `FR-SHOP-06`, `FR-SHOP-10`.
- **G-73** (supersedes G-53) — rollover clears **every** checked item
  unconditionally and keeps every unchecked one; no per-item week attribution
  is stored. Amends `FR-SHOP-09`, `FR-MENU-06`.
- **G-74** (supersedes G-55) — duplicate grouping removed; merge-on-match
  leaves nothing to group. Removes `FR-SHOP-11`.

---

## 4. Open question — why week rollover earns a row

`FR-MENU-06` and `FR-MENU-08` describe a scheduled job. A scheduled job is a
client like any other, and this one performs the heaviest write in the system.
Enumerated, rollover is five steps:

| Step | Covered by an existing AP? |
|---|---|
| Archive the ending current week | **Dissolved** — see below. |
| Snapshot the shopping list onto the archived week (`FR-ARCH-02`, taken **before** cleanup) | **No.** A genuine copy: read the whole live list, write it under the archived week. Parks with archive. |
| Promote next → current | **Dissolved** — see below. |
| Initialise the new empty next week | **Dissolved** — see below. |
| Clear all checked items (`FR-SHOP-09`, as amended by `G-73`) | **No.** "Eliminar elemento de la lista de la compra" deletes one item by id on user action; this is a bulk delete of every checked item. It no longer needs a read of the new week — see below. |

**Three of the five steps dissolve, and the sort key is why.** Because
`idSemana` is derivable from the date (`FR-MENU-02`: ISO week, Europe/Madrid —
e.g. `2026-W32`) and carries year + zero-padded week, it sorts
**lexicographically in chronological order**. Three consequences follow:

- *Promotion* is a no-op. "Which week is current" is computed, never stored;
  the clock rolls over and last week's id simply stops being the current one.
- *Initialisation* is a no-op if weeks are created lazily on first write.
- *Archiving* is a no-op **too**, which was not obvious when this section was
  first written. Past weeks are already persisted under older keys in the same
  key space, so nothing is copied at rollover, and `FR-ARCH-04`'s
  reverse-chronological selector is a descending range read for free. Even
  `FR-ARCH-02`'s "becomes read-only" needs no stored flag: a week is closed iff
  its id sorts before the computed current week. Read-only is **derivable**.

That is the dividend of keeping the week id computable rather than a random id,
and it is larger than one no-op — it is three.

**What survives.** The shopping-list snapshot of `FR-ARCH-02` is a real copy and
parks with archive. And the whole-week *full-content* read has not vanished, it
has **moved**: `FR-ARCH-03` sends records older than ~3 months to cold storage
(S3 Glacier, per `decisiones_arquitectura.md`), and writing a week out to
Glacier needs its complete content — tools and procedure included, which
"Obtener semana + ingredientes" deliberately does not carry. That read gets
designed when archive comes off the shelf, not now.

**The decisive argument is `FR-MENU-08`.** It requires rollover to be atomic,
idempotent and re-runnable after partial failure, without data loss,
double-archiving or double-cleanup. You cannot design idempotency for an
operation whose reads and writes you have not enumerated. The requirement is
unimplementable until the catalogue names them.

`G-73` made this materially easier. The cleanup used to be a *conditional* bulk
delete — remove checked items **unless** the new current week still needs them
— which required reading the new week and comparing, and which is awkward to
re-run safely. It is now "delete every checked item", which is naturally
idempotent: running it twice is indistinguishable from running it once.

**Scope note:** the shopping-list snapshot is archive work and parks with the
archive decision. The `FR-SHOP-09` cleanup does **not** — it operates on the
live shopping list and needs specifying regardless.

## 5. Open question — what real-time adds

**Blocked on P3** (`docs/architecture.md` §2: WebSocket API? AppSync?
polling?). The answer is 0–3 patterns depending entirely on that choice:

- **Polling** — zero new patterns. Clients re-call "Obtener semana", "Obtener
  biblioteca", "Obtener lista de la compra" and "Obtener reglas" on a timer.
  Entirely defensible for 2–10 users, and it makes `FR-RT-03` (indicate
  connection loss, reconnect, resynchronise) nearly free.
- **API Gateway WebSockets** — three: save a connection on `$connect`
  (`connectionId`, `idUsuario`, `ttl`), delete it on `$disconnect`, and
  **list all active connections** in order to broadcast. The third is the one
  worth noting: it is a full-collection read on *every* change. Trivial at
  household scale, and the first thing that hurts at any other scale. A `ttl`
  is required because clients vanish without ever sending `$disconnect`.
- **AppSync** — subscriptions are managed; no connection registry, but it
  constrains the data layer in exchange.

**The insight that survives all three options:** real-time adds no new *read*
patterns. `FR-RT-03`'s resynchronisation on reconnect is just re-calling the
reads you already have. What it adds is a **fan-out obligation on every write
you already have** — `FR-RT-01` broadcasts changes to both live weeks'
menus, the shopping list, the rules and the library, which is every write and
delete in the catalogue: the two "comida" mutations, the two library ones, the
two shopping-list ones and the two rule ones. That obligation belongs in the
design, not in the catalogue.

**Recommendation:** put a row in the sheet marked *blocked on P3* rather than
leaving the section absent. An empty row is a decision you can see; a missing
one looks like an oversight.

---

## 6. Still open

| Item | Status |
|---|---|
| **Archive** (`FR-ARCH-01`…`-04`) | **Parked by decision** — MVP scope. While a week is still in the main store, reading it *is* "Obtener semana" pointed at an older `idSemana`, and `FR-ARCH-04`'s reverse-chronological selector is a descending range read (§4). What is not free is `FR-ARCH-03`: once a record has moved to cold storage, retrieval takes minutes-to-hours and the UI shows "restoring…", making it an **async two-step read**. The export to Glacier also needs a whole-week **full-content** read that no pattern provides. |
| **Week rollover** (`FR-MENU-06`, `-08`) | **Mostly closed** (2026-08-09). Three of the five steps dissolve into the sort key (§4); the shopping-list snapshot parks with archive; the `FR-SHOP-09` cleanup is now an unconditional bulk delete of checked items (`G-73`) and still needs a row. |
| **Shopping-list re-sync button** (`FR-SHOP-03`, `-06`, `-10`) | **Read half closed** (2026-08-09) by "Obtener semana + ingredientes". The write half is still open: `G-72` made re-sync purely additive, so it is an upsert-many on normalized name + unit with no deletes — which the per-item write ("Añadir o editar elemento de lista de la compra") does not express as a batch. |
| **Real-time** (`FR-RT-01`…`-03`) | Blocked on P3. |
| **Sessions** (`FR-AUTH-11`, `-14`, `-16`) | Parked. Blocked on P2 (Cognito vs. application-managed) — if Cognito, the table may not exist at all. |

## 7. Raised and not yet addressed

Re-verified against the catalogue as of 2026-08-09 (AP1–AP23). Everything else
raised during the review has been resolved in the spreadsheet and is not
repeated here.

### Substantive

1. **"Editar o añadir comida" hides the definitive-selection invariant.**
   `isDefinitiva` is carried as an ordinary field. But `FR-CAND-05` says
   promotion *replaces any previous definitive* — two items change, not one —
   and `FR-MENU-03` caps a slot at one definitive, an invariant no single-field
   write can hold. `FR-CAND-08` (clear the slot, all meals return to candidate)
   is a third shape again. Promote and clear are conditional/transactional
   writes and are currently invisible.

2. **Nothing records who made a meal definitive.** `FR-SUM-02` requires the
   summary to display **who promoted** each meal; `FR-CAND-04` separately
   requires each candidate to display **its author**. These are different
   people. Every week read returns only `añadidoPor`. A second attribution
   attribute is missing, and `FR-SUM-03` says it must resolve to the "unknown
   user" placeholder too.

3. ~~**The shopping list is missing three required attributes.**~~
   **Closed 2026-08-09 — by cutting the requirements, not by adding
   attributes.** The finding was that "Obtener/Añadir elemento de lista de la
   compra" carry only
   `idIngrediente, nombreIngrediente, cantidad, unidad, isComprado`, while four
   requirements demanded more: an auto/manual marker (`FR-SHOP-04`), a
   manual-override state (`FR-SHOP-06`), a per-item record of which live weeks
   require the item (`FR-SHOP-09`), and an updated-since-checked flag
   (`FR-SHOP-08`/`G-44`).

   The requirements owner judged the first three over-specified for the MVP and
   removed the behaviours that needed them — logged as **Part J (G-72, G-73,
   G-74)** in `docs/gaps_and_resolutions.md`. Re-sync is now purely additive, so
   it needs no provenance to delete safely; rollover clears all checked items
   unconditionally, so it needs no week attribution; duplicate grouping is gone
   with `FR-SHOP-11`. **Only the `FR-SHOP-08` flag survives** — one boolean.
   The catalogue rows were closer to right than the requirements were.

   **Confirmed by the owner 2026-08-09:** the amended `FR-SHOP-06` reads
   *additive* as "adds missing items and **updates the quantity** of ones
   matching on normalized name + unit; never deletes". The alternative reading
   — append only, never touch an existing row — was rejected because it makes
   repeated presses duplicate every ingredient, which `FR-SHOP-10` forbids.

4. **The per-week rule override has no home.** `FR-AI-05` / `FR-RULE-05` allow
   editing the rules *for one generation run only*, without touching the shared
   set. Nothing in the catalogue says whether that override is persisted or
   passed through the generation call. Either answer is defensible, but it is
   not free: `FR-AI-08` hashes the **effective** rules into the idempotency
   key, so the override has to be reconstructible for a retry to produce the
   same key.

5. **"Restablecer contraseña" still spans two different writes.** `isPassReseteada` moves to
   opposite values depending on which one it is — an admin reset sets it
   (`FR-AUTH-11`) and additionally invalidates all of the account's sessions;
   the user's forced set-password step clears it (`FR-AUTH-10`) and keeps the
   session. The session half parks with P2; the `isPassReseteada` half does
   not.

6. **The week reads' ordering criterion is unstated.** "Obtener semana" and
   "Obtener semana + ingredientes" are both marked as requiring ordering, with
   no column saying ordered *by what*. Day, then slot, then — insertion order?
   Author? Definitive first? Unanswered, and the first of the two is the
   highest-frequency read in the product.

### Added by the 2026-08-13 compliance pass

New findings. Numbering continues from 11 — **positions are not identifiers**,
the same lesson as Appendix A, so nothing above was renumbered.

12. ~~**Rules carry no author.**~~ **Discarded by the owner 2026-08-13 — rule
    attribution is out of MVP scope.** The finding stands as stated: `FR-RULE-06`
    requires every shared-rule edit to be **attributed**, and `FR-SUM-03` names
    "rule edits (`FR-RULE-06`)" explicitly among the attributions that must
    resolve to the "unknown user" placeholder. Neither rules pattern carries an
    author attribute, and the catalogue will not gain one.

    > **⚠ Consequence not yet actioned.** Dropping the attribute does not close
    > the finding, it moves it: **three frozen requirements now assert
    > behaviour the MVP will not have** — `FR-RULE-06` ("all edits are
    > attributed"), `FR-SUM-03` (its rule-edit clause), and `FR-AUTH-13`, whose
    > enumeration still lists "rule edits" as content to reattribute. This is
    > the same desync class as G-75, one requirement earlier in the same
    > sentence. Until those are amended the catalogue remains formally
    > non-compliant on this point — the decision is sound, the paperwork is
    > outstanding. Needs an explicit owner instruction, as Parts I, J and K did.

13. ~~**The `FR-SHOP-08` flag is still absent from the catalogue.**~~
    **Closed 2026-08-14 — by cutting the flag, not by adding the attribute.
    Logged as Part M (G-77), which supersedes G-44.** Re-sync now **never writes
    to a checked item at all**. Per normalized name + unit it computes the
    **outstanding** amount — required minus what checked items already carry —
    and writes that to the matching unchecked item, creating one if none
    exists. Buy 500 g of rice, requirement rises to 800 g: the checked
    `arroz 500 g` is untouched and a new unchecked `arroz 300 g` appears. The
    remainder, not the gross amount — a user shown 800 after buying 500 would
    buy 800 more.

    **This is the second time the shopping list has been fixed by deleting a
    requirement rather than adding an attribute** (Part J was the first), and
    the reason is the same both times: the attribute existed to reconstruct
    information the check state already carries. **The catalogue needed no
    change at all** — no new field on "Obtener/Añadir elemento de lista de la
    compra", no new pattern. Re-sync already reads checked quantities through
    "Obtener lista de la compra", and the per-item write already creates rows.
    Two consequences worth carrying into the PK/SK pass: a checked and an
    unchecked item may **deliberately share a normalized name + unit**, which
    kills option (b) of the shopping-item key question and settles it on the
    surrogate `idIngrediente`; and `FR-SHOP-10` keeps the word *serialized*
    with the concurrency question **explicitly parked**, not resolved.

    The original finding, for the record: Finding 3
    concluded that of the four attributes the shopping list was missing, the
    Part J cuts removed the need for three and **"only the `FR-SHOP-08` flag
    survives — one boolean"**. That conclusion was recorded; the catalogue was
    never updated. "Obtener/Añadir elemento de lista de la compra" still carry
    `idIngrediente, nombreIngrediente, cantidad, unidad, isComprado` and
    nothing else, so a re-sync that changes a checked item's quantity has
    nowhere to record that it must render as *updated since checked*.

14. **No pattern reads a user by username, so `FR-AUTH-17` cannot be
    enforced.** Uniqueness is required "among active accounts, validated on
    creation **and rename**". Validating it means asking "does this username
    exist?" — a question no pattern asks. "Login" is the only pattern taking
    `nombreUsuario` and it is typed as a login, not a lookup. Note this is a
    *question* that is missing, not a key design: it stays open whichever way
    the PK/SK pass goes.

    > **Still open after the 2026-08-13 revision.** A new row **"Obtener
    > usuario"** was added (`idUsuario` → `idUsuario, nombreUsuario, tipo,
    > isPassReseteada`). It is a good addition and closes a different gap — the
    > point read by id that `FR-AUTH-18` needs to refuse deleting an admin, and
    > that "Restablecer contraseña" needs to act on a single account, both of
    > which previously had to go through the full user list. **But it reads by
    > id, and this finding is about reading by name.** `FR-AUTH-17` is unmoved.
    >
    > Two ways to close it, and the cheap one may be right: *(a)* add "Obtener
    > usuario por nombre" (`nombreUsuario` → existence + `idUsuario`); or
    > *(b)* declare it **composition** under §1 rule 2 — the admin creates and
    > renames from the account list of `FR-AUTH-12`, which has already read
    > every account with its `nombreUsuario`, and at 2–10 users that filter
    > happens in memory. (b) costs nothing and is defensible at this scale, but
    > it must be **stated**, because it is a read-then-write check and therefore
    > a TOCTOU: two admins racing can both see the name free. That is the same
    > shape as the shopping-item key question, and like it, *enforcement* (as
    > opposed to validation) is a PK/SK-pass question, not a catalogue one.

15. ~~**`FR-AUTH-13` lists shopping-list items as authored content.**~~
    **Fixed 2026-08-13 by amending the requirement — logged as Part K (G-75).**
    It required content authored by a removed account — "candidate meals,
    library recipes, definitive-meal promotions, rule edits, **shopping-list
    items**" — to be retained and reattributed. After `G-72` a shopping item is
    a name, a quantity, a unit and a checkbox: it has no author to reattribute.
    The catalogue was right and the requirement carried a clause that no longer
    referred to anything, so the clause was struck under an explicit owner
    instruction. See `docs/gaps_and_resolutions.md` Part K.

### Minor

7. **"Login"** is typed `Lectura` and returns `-`. A login returns
   something — at minimum a session reference and the role. Parks with P2.

    > **Upgraded to substantive, 2026-08-13.** Only the *session* half parks
    > with P2. The rest does not: `FR-AUTH-10` forces the set-password step
    > when the account is new or reset, which the client can only know if the
    > login returns `isPassReseteada`; and `FR-AUTH-06` routes admins away from
    > every planning feature, which needs `tipo`. Both are decided
    > requirements, and both are unimplementable while the return is `-`.
    > The minimum return is `idUsuario, tipo, isPassReseteada` plus whatever
    > P2 later adds.
    >
    > **Fixed 2026-08-13** — "Login" now returns exactly
    > `idUsuario, tipo, isPassReseteada`. The session reference is still absent
    > and correctly parks with P2.

8. **"Obtener reglas"** returns `nombrePlato` for pin rules but not
   `idPlato`, while "Añadir o editar regla" now *writes* `idPlato`. The read
   should carry both: the id to resolve the reference (`FR-RULE-07` removes
   rules whose recipe is deleted), the name denormalised so the rules screen
   needs no second read.

    > **Upgraded to substantive, 2026-08-13.** This is not a convenience. The
    > `FR-RULE-07` cascade deletes by `idPlato`, and the only way to find the
    > affected rules is to read them and match — but the read returns a name.
    > Matching by name is not merely awkward, it is **wrong**: `FR-CAND-06`
    > explicitly allows two library recipes to share a name, so a name match
    > can remove a rule pinned to a *different* recipe that happens to be
    > called the same thing. `FR-RULE-07` is unimplementable as the catalogue
    > stands.
    >
    > **Fixed 2026-08-13** — "Obtener reglas" now returns **both** `idPlato`
    > and `nombrePlato`: the id resolves the reference for the cascade, the name
    > stays denormalised so the rules screen needs no second read.
9. **The four delete patterns** ("Eliminar comida", "Eliminar comida
   (biblioteca)", "Eliminar elemento de la lista de la compra", "Eliminar
   petición IA") are marked as requiring ordering/filtering, but each is a
   point operation on a globally-unique id. Cosmetic — but the column should
   mean something, or it will be read as meaningful later.
10. **The `Frecuencia` column has no stated basis.** Alta/Media/Baja relative
    to what, over what period? At 2–10 household users every figure is low and
    the column will not drive a capacity decision — item size and query shape
    will. Worth either grounding in rough orders of magnitude or stating
    outright that it is indicative only.
11. ~~**"Obtener comida de la biblioteca" has no `Frecuencia` and no ordering
    entry.**~~ **Fixed 2026-08-09** — now `Alta` / `No`.

### Notes carried forward

- **AWS Budgets alert; they do not stop spend.** `NFR-AI-01` now requires an
  actual enforcing path (Budget action or equivalent). **Unanswered:** whether
  a real kill switch is wanted, or an email plus reaction time is acceptable
  for a course project. This decides whether the `ai` Lambda needs a flag it
  can read.
- The `idBiblioteca` / `idLista` / `idGrupoReglas` parameters are singletons
  today, pinned to a constant. Kept deliberately so a future multi-group model
  is a prefix change rather than a key-schema rewrite. The feature itself
  (membership, invitations, per-group permissions and subscriptions) was judged
  out of MVP scope.

---

## 8. Desync register

Two independent problems, both found on the final recheck.

### 8.1 Fixed — derived artifacts stale after the §3 amendments

| Where | Was | Now |
|---|---|---|
| `docs/requirements.md` FR-AI-10 | "Regenerations count toward the generation caps" — a dangling reference to the per-user counter G-70 deleted | each regeneration is a fresh invocation consuming the global budget |
| `feature_list.json` #11 acceptance | category counts "honored best-effort (G-63)" | verifiable against the stored `tipoAlimento` (G-69) |
| `feature_list.json` #12 acceptance | "Regenerations count toward the generation caps" | global budget, no per-user quota (G-70) |
| `feature_list.json` #17 `blocked_reason` | blocked partly on deriving the per-user daily cap (G-38) | cap is global via AWS tooling; app stores no counter (G-70) |
| `feature_list.json` #10 acceptance | no mention of G-71 | two criteria added: definitive slots skipped / definitive outranks pin; final-state category counting |
| `feature_list.json` #4 acceptance | recipe carries no classification attribute | criterion added for exactly one `tipoAlimento` (G-69) |

`feature_list.json` was re-validated as parseable JSON after editing.

### 8.1b Fixed — artifacts re-synced after the Part J cuts (2026-08-09)

| Where | Change |
|---|---|
| `docs/requirements.md` | `FR-SHOP-04`, `-06`, `-09`, `-10` amended; `FR-SHOP-11` struck through and marked removed (FR-LIB-06 precedent); `FR-MENU-06` cleanup clause reworded |
| `docs/gaps_and_resolutions.md` | **Part J** added with G-72, G-73, G-74 |
| `docs/coverage_analysis.md` | US22/23/24 notes amended; G-21/G-53/G-55 marked superseded; G-69–G-74 added to the index; closing sentence updated to Parts A–J |
| `docs/app_user_stories.md` | US24 reworded — cleanup is unconditional on checked items |
| `feature_list.json` | #7 acceptance (no provenance attributes), #8 rewritten and `FR-SHOP-11` dropped from `covers`, #13 cleanup criterion |

Also cleared in the same pass, from §8.2 below: the stale G-63 and G-38
descriptions in `docs/coverage_analysis.md` (lines 123, 137, 175, 200), which
the Part I amendments had left behind. `feature_list.json` re-validated.

### 8.2 Flagged, not fixed — frozen or human-owned

- `docs/architecture.md` **line 92** (the P4 row) and **line 106** (§2.1) both
  still cite the per-user daily cap. Human-owned.
- ~~`docs/coverage_analysis.md` lines 123, 137, 175, 200~~ — **fixed
  2026-08-09** under the same instruction that authorised Part J.
- `docs/gaps_pending_stakeholders.md` PEND-03 records the per-user cap in its
  answer. Frozen — and arguably **should** stay: it is a record of what the
  stakeholder was asked and answered at the time, not a live requirement.
- `docs/verification.md` line 74 tests additive bulk ops by asserting nothing
  was removed. Still correct, now **incomplete** — under G-71 it should also
  assert that a slot holding a definitive was skipped entirely. Note that the
  same line now describes the shopping re-sync exactly right: under G-72 it
  *is* an additive bulk op that removes nothing.

### 8.3 Two architecture documents disagree — the human's to reconcile

`docs/architecture.md` §2 lists **P1 (datastore), P2 (auth), P3 (real-time),
P6 (deployment topology)** as pending and human-owned: an agent hitting one
must mark the feature `blocked` and stop. §6 additionally forbids adding "a
third Lambda, a queue, a cache, or any service without an approved `design.md`
and human sign-off".

`docs/decisiones_arquitectura.md` — human-authored, Spanish, not referenced
from `CLAUDE.md` — **already decides several of them**:

| Decision recorded there | Status in `architecture.md` |
|---|---|
| **DynamoDB** as the datastore | P1, listed pending |
| CloudFront + S3 static site; **API Gateway** fronting the Lambdas | P6, listed pending |
| **S3 Glacier** for week history | P6 / relates to `FR-ARCH-03` |
| **Standard SQS queue** driving the `ai` Lambda as workers, idempotency enforced in the workers (FIFO rejected so workers stay parallel) | §6 forbids adding a queue without sign-off |
| Cognito vs. DynamoDB-backed auth still being explored | P2 — genuinely still open |

**Consequence for a new agent:** following `CLAUDE.md` it reads
`architecture.md`, marks persistence work `blocked` on P1, and refuses to touch
the datastore — while DynamoDB has in fact been chosen. It may also flag the
queue as a violation of §6, when the human authored it.

**Consequence for this review:** the advice given throughout was "P1 is
undecided, keep the patterns datastore-agnostic." That was correct against
`architecture.md` and stale against `decisiones_arquitectura.md`. Nothing needs
redoing — a datastore-agnostic catalogue is still the right artifact — but the
**next pass (data structures / PK-SK) should proceed on DynamoDB**, and the SQS
decision directly shapes the three idempotency patterns: enforcement is in the
workers, and
the queue is deliberately standard rather than FIFO.

**Resolved by owner decision, 2026-08-14 — no reconciliation.** The two
documents are **not** meant to say the same thing and will not be merged.
`decisiones_arquitectura.md` is the owner's personal decision record and stays
that way permanently; `architecture.md` is the agent-facing contract. An agent
should therefore keep treating `architecture.md` §2 as authoritative for what
is "pending", and should **not** read `decisiones_arquitectura.md` as
unblocking anything.

The one practical carry-over stands: the **next pass (data structures / PK-SK)
proceeds on DynamoDB**, because the owner has decided it, and the SQS-worker
decision shapes the three idempotency patterns — enforcement in the workers, on
a deliberately standard queue.

---

## 9. Compliance verdict — 2026-08-13

**Question asked:** are AP1–AP23 complete and compliant with
`docs/requirements.md`? **Answer: not yet.** The catalogue was re-read from
disk (mtime 2026-08-09 21:06) and is unchanged from Appendix A.

Method: both directions. Every `FR-*`/`NFR-*` that implies a question of the
datastore was checked for a pattern that asks it; every pattern was checked
against the requirements it serves. Requirements with no datastore question
(password policy, prompt content, UX, browser support, IaC) are out of scope
by construction and are not listed.

### Clean — no action

| Area | Why it passes |
|---|---|
| Week structure and viewing (`FR-MENU-01`, `-02`, `-04`, `-05`, `-07`) | "Obtener semana" plus the two detail reads cover every display site; both live weeks are the same question parameterised by `idSemana` |
| Candidate authoring (`FR-CAND-01`, `-02`, `-03`, `-06`, `-07`) | All three authoring methods land on one write; the snapshot is carried in full; the duplicate warnings read data already in hand |
| Library (`FR-LIB-01`…`-05`) | Index read, detail read, write and delete; `nombrePlato` + `tipoAlimento` as parameters serve the `FR-LIB-04` search and filter directly |
| AI idempotency (`FR-AI-08`, `-10`) | The three request patterns are point operations by hash and store the result payload |
| AI generation flow (`FR-AI-03`, `-04`, `-09`, `-11`, `-12`) | Composition over reads that already exist; per-slot writes are independent |
| Shopping list, read side (`FR-SHOP-01`, `-02`, `-05`, `-07`) | The list read plus per-item write and delete; "Obtener semana + ingredientes" closes the aggregation read |
| Cost cap (`NFR-AI-01`) | No counter stored, by `G-70` — correctly absent from the catalogue |
| Attribution of removed users (`FR-SUM-03`, `FR-AUTH-13`) | Render-time resolution against the user list; no fan-out write |

### Blocking — a decided requirement has no pattern, or a pattern contradicts one

| # | Requirement at risk | Defect |
|---|---|---|
| ~~17~~ | ~~`FR-RULE-07`, `FR-LIB-02`~~ | **Withdrawn 2026-08-14 — the premise was wrong.** I read the `nombrePlato` on "Obtener reglas" as a denormalised copy and raised a staleness risk against `FR-LIB-02` renames. It is **not a copy**. The owner's rule: *the write is the record of what is persisted*, so an attribute no write ever supplies is not stored. "Añadir o editar regla" writes only `idPlato`; the name is **resolved live from the library** on every read. There is nothing to go stale |
| ~~9~~ | ~~ordering column~~ | **Four of five fixed 2026-08-14.** One cell left: **"Establecer/Desasignar comida definitiva" is still `Sí`**. With `idSemana, numeroDia, numeroComida` it is now a fully-qualified single-item write — nothing to order, nothing to filter |
| ~~1a~~ | ~~`FR-MENU-03`, `FR-CAND-05`, `FR-CAND-08`~~ | **Closed 2026-08-14.** The pointer sits at slot level in all three reads (14 per week), and the write now takes `idSemana, numeroDia, numeroComida, idPlatoDefinitiva`. `FR-SUM-01` and `FR-SHOP-05` clear with it |
| ~~16~~ | ~~`FR-CAND-04`, `FR-AUTH-13`~~ | **Closed 2026-08-14** — `añadidoPor` added to "Editar o añadir comida", parameters and return |
| ~~1b~~ | ~~`FR-MENU-03`~~ | **Fixed 2026-08-14** — `isDefinitiva` removed from "Editar o añadir comida". The flag is now derived |
| ~~2~~ | ~~`FR-SUM-02`~~ | **Closed 2026-08-14** — FR-SUM-02 removed. Part O (G-79). The summary shows the meal's own author |
| ~~4~~ | ~~`FR-AI-05`, `FR-RULE-05`, `FR-AI-08`~~ | **Closed 2026-08-14** — the override **lives in the request and is not persisted**. Zero new patterns: the payload carries it, so a retry recomputes the same idempotency hash |
| ~~5~~ | ~~`FR-AUTH-10`, `FR-AUTH-11`~~ | **Closed 2026-08-14** — `isPassReseteada` is now a parameter of "Crear o editar usuario", and "Restablecer contraseña" was renamed **"Establecer contraseña"**: one direction only, so no parameter is needed to disambiguate |
| ~~6~~ | ~~`FR-MENU-01`~~ | **Closed 2026-08-14** — ordering is `numeroDia`, then `numeroComida`, then `idPlato` |
| ~~7~~ | ~~`FR-AUTH-06`, `FR-AUTH-10`~~ | **Fixed 2026-08-13** — "Login" now returns `idUsuario, tipo, isPassReseteada` |
| ~~8~~ | ~~`FR-RULE-07`~~ | **Fixed 2026-08-13** — "Obtener reglas" now returns both `idPlato` and `nombrePlato` |
| ~~12~~ | ~~`FR-RULE-06`, `FR-SUM-03`~~ | **Discarded 2026-08-13** — rule attribution out of MVP. ⚠ Three requirements now over-assert; amendment outstanding (see §7 finding 12) |
| ~~13~~ | ~~`FR-SHOP-08`~~ | **Closed 2026-08-14** — the flag was cut, not the attribute added. Part M (G-77), supersedes G-44. Catalogue unchanged |
| ~~14~~ | ~~`FR-AUTH-17`~~ | **Closed 2026-08-14** — "Obtener usuario por nombre" (`nombreUsuario` → user record) added. Uniqueness is now a question the catalogue asks |
| — | `FR-SHOP-06`, `-10` | The re-sync **write** is an upsert-many on normalized name + unit; the per-item write does not express it as a batch. **The key question underneath it is now settled** by G-77 — a checked and an unchecked item may share a normalized name + unit, so identity is the surrogate `idIngrediente`, not name + unit |
| ~~—~~ | ~~`FR-SHOP-09`~~ | **Closed 2026-08-14** — "Eliminar elementos marcados de la lista de la compra" (`idLista`, bulk) added |

### Not blocking — parked or awaiting a human decision

| Item | Status |
|---|---|
| Archive (`FR-ARCH-01`…`-04`) | Parked by decision, MVP scope (§6) |
| Real-time (`FR-RT-01`…`-03`) | **Out of scope for the catalogue by owner decision, 2026-08-14.** Real-time does not belong in the access patterns. Do not raise it again unless the owner does. §5's analysis is kept as background only |
| Sessions (`FR-AUTH-09`, `-11`, `-14`, `-16`) | Blocked on P2. Note the shape when it unblocks: "invalidate **all** sessions of an account" is a query by `idUsuario`, not a point delete |
| ~~Finding 15 (`FR-AUTH-13` names shopping items as authored content)~~ | **Fixed 2026-08-13** — requirement amended under an explicit owner instruction, logged as **Part K (G-75)** |
| New pattern "Obtener usuario" (`idUsuario` → user record) | **Added 2026-08-13.** Closes the point read by id that `FR-AUTH-18`'s admin-deletion refusal and "Restablecer contraseña" both needed, which previously had to go through the whole account list |
| Finding 9 (ordering column on point operations) | **Rule stated by the owner 2026-08-14.** The column means **"does the datastore have to do this ordering or filtering?"** — not "does the user see an order somewhere". Display order is UI and does not earn a `Sí`. Consequences: the five point operations (the definitive write, the three single-item deletes, the AI-request delete) → **No**; "Obtener lista de la compra" stays **No**, because `FR-SHOP-08`'s checked-below-unchecked split is presentation over a few dozen flat rows; the two week reads stay **Sí**, because their day → slot order is a **sort-key** obligation, not a preference, and that cell is a direct input to the PK/SK pass; "Obtener biblioteca" and "Obtener reglas" stay **Sí** on real filter parameters. Borderline, left at `Sí`: "Eliminar elementos marcados", which selects on `isComprado` — that cell is where a sparse index gets considered |
| Finding 10 (`Frecuencia` basis) | Cosmetic, unchanged |
| `NFR-AI-01` enforcing kill switch | **Closed 2026-08-14** — a real enforcing path is wanted. It is an infrastructure concern (Budget action or equivalent), **not an access pattern** |

## Appendix A — catalogue snapshot (2026-08-03)

Verbatim from the spreadsheet, so this document can be read on its own.
**Authoritative source is the xlsx**, which changes; treat this as a dated
copy. Recipe payloads are abbreviated as *[receta]* =
`nombrePlato, tiempo, numeroComensales, tipoAlimento, lista(nombreIngrediente,
cantidad, unidad), lista(nombreUtensilio), lista(numeroPaso, descripcionPaso)`.

| AP | Título | Tipo | Parámetros | Devolución | Frec. | Ord./filtro |
|---|---|---|---|---|---|---|
| AP1 | Pantalla admin - Listar usuarios | Lectura | — | `lista(idUsuario, nombreUsuario, tipo, isPassReseteada)` | Baja | No |
| AP2 | Pantalla admin - Crear o editar usuario | Escritura | `nombreUsuario, idUsuario, tipo, pass` | `idUsuario, nombreUsuario, tipo, isPassReseteada` | Baja | No |
| AP3 | Pantalla admin - Eliminar usuario | Eliminación | `idUsuario` | — | Baja | No |
| AP4 | Login | Lectura | `nombreUsuario, pass` | — | Alta | No |
| AP5 | Restablecer contraseña | Escritura | `idUsuario, pass` | — | Media | No |
| AP6 | Obtener semana | Lectura | `idSemana` | `idSemana, lista(numeroDia, lista(numeroComida, lista(idPlato, añadidoPor, nombrePlato, tipoAlimento, isDefinitiva)))` | Alta | Sí |
| **AP7** | **Obtener semana + ingredientes** | Lectura | `idSemana` | `idSemana, lista(numeroDia, lista(numeroComida, lista(idPlato, añadidoPor, nombrePlato, tipoAlimento, isDefinitiva, lista(nombreIngrediente, cantidad, unidad))))` | Media | Sí |
| AP8 | Obtener comida - Semana | Lectura | `idPlato` | `idSemana, numeroDia, numeroComida, idPlato,` *[receta]*`, isDefinitiva, añadidoPor` | Alta | No |
| AP9 | Eliminar comida | Eliminación | `idPlato` | — | Media | Sí |
| AP10 | Editar o añadir comida | Escritura | `idSemana, idPlato, numeroDia, numeroComida,` *[receta]*`, isDefinitiva` | same + `idPlato` | Media | No |
| AP11 | Obtener biblioteca | Lectura | `idBiblioteca, nombrePlato, tipoAlimento` | `lista(idPlato, nombrePlato, tiempo, tipoAlimento, añadidoPor)` | Alta | Sí |
| AP12 | Obtener comida de la biblioteca | Lectura | `idPlato` | `idPlato,` *[receta]*`, añadidoPor` | Alta | No |
| AP13 | Añadir o editar comida (biblioteca) | Escritura | `idBiblioteca, idPlato,` *[receta]*`, añadidoPor` | `idPlato,` *[receta]*`, añadidoPor` | Media | No |
| AP14 | Eliminar comida (biblioteca) | Eliminación | `idPlato` | — | Media | Sí |
| AP15 | Obtener lista de la compra | Lectura | `idLista` | `lista(idIngrediente, nombreIngrediente, cantidad, unidad, isComprado)` | Alta | No |
| AP16 | Añadir o editar elemento de lista de la compra | Escritura | `idLista, idIngrediente, nombreIngrediente, cantidad, unidad, isComprado` | `idIngrediente, nombreIngrediente, cantidad, unidad, isComprado` | Alta | No |
| AP17 | Eliminar elemento de la lista de la compra | Eliminación | `idLista, idIngrediente` | — | Alta | Sí |
| AP18 | Obtener reglas | Lectura | `idGrupoReglas, tipoRegla` | `idGrupoReglas, lista(idRegla, tipoRegla, tipoComida, cantidad, numeroDia, numeroComida, nombrePlato)` | Media | Sí |
| AP19 | Añadir o editar regla | Escritura | `idRegla, tipoRegla, tipoComida, cantidad, numeroDia, numeroComida, idPlato` | same | Media | No |
| AP20 | Eliminar regla | Eliminación | `idRegla` | — | Media | No |
| AP21 | Añadir o editar petición IA (idempotencia) | Escritura | `requestId, status, result, ttl` | `requestId` | Alta | No |
| AP22 | Obtener petición IA (idempotencia) | Lectura | `requestId` | `requestId, status, result, ttl` | Alta | No |
| AP23 | Eliminar petición IA (idempotencia) | Eliminación | `requestId` | — | Alta | Sí |

**AP numbers are positions, not identifiers.** Inserting "Obtener semana +
ingredientes" at row 7 on 2026-08-09 pushed every pattern below it down by one,
so any `APn` reference written earlier than that points at the wrong row. This
document now refers to patterns **by title** in prose for exactly that reason,
and keeps numbers only in this table. It is the same lesson as §2's move from
natural keys to immutable surrogate ids, applied to the catalogue itself.

