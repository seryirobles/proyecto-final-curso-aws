# Current session

> This file is emptied when each session closes and moved to `history.md`.
> While you work, **keep it updated in real time**, not at the end.

- **Feature in progress:** _none_
- **Agent:** —

## Plan

_Nothing in progress._ The last session's record is in `history.md`
(**2026-08-13/14 · Access-pattern compliance pass**). Read it before starting —
it changed the requirements in five places.

## Where things stand

**The access-pattern catalogue is closed.** 27 patterns in
`Desktop/lab-final-patrones-acceso.xlsx`, audited in both directions against
`docs/requirements.md`, no open defects. The full record, including the clean
areas and the method rules, is `docs/access_patterns_review.md` — start at §0,
verdict in §9.

**The requirements moved.** Parts K–O (`G-75`…`G-79`) in
`docs/gaps_and_resolutions.md` were added on 2026-08-13/14 under explicit,
non-standing freeze lifts. `FR-SUM-02` and `FR-SHOP-08`'s flag clause were
**removed from the product**. Do not work from memory of the old text.

## Next step

**The data-structure / PK-SK pass.** Not started — rows 30+ of the spreadsheet
are still AWS-course template scratch (`USUARIO#<nombre>`, `DIA#…`, `CURSO#…`,
`ESTUDIANTE#…`). **They are not authored decisions; do not audit them.**

Five things to carry in:

1. **Proceed on DynamoDB.** The owner has decided it, even though
   `architecture.md` §2 still lists P1 as pending (see below).
2. **The week reads' `Sí` in the ordering column is a sort-key obligation** —
   it says the SK must encode `numeroDia` and `numeroComida`.
3. **In-slot candidate order is `idPlato`.** A time-sortable id (ULID/KSUID)
   gives insertion order, which is what a user expects; a random UUID gives an
   order that is stable but arbitrary. That is an id-format decision.
4. **Shopping-item identity is the surrogate `idIngrediente`**, settled by
   `G-77`: a checked and an unchecked item may deliberately share a normalized
   name + unit, so name + unit cannot be the key.
5. **Two concurrency questions were parked here deliberately, not solved.**
   `FR-SHOP-10` keeps the word *serialized* — two simultaneous re-sync presses
   can still both create a row. And `FR-AUTH-17` uniqueness is validated by a
   read-then-write, which is a TOCTOU. Both are for this pass. The SQS-worker
   decision puts AI idempotency enforcement in the workers, on a deliberately
   standard queue.

## Standing instructions

- **Re-read the catalogue from disk at the start of any turn that touches
  access patterns.** The owner edits and saves it mid-conversation — it changed
  seven times in the last session. Do not trust Appendix A or a previous turn's
  parse. No Python on this machine: unzip the `.xlsx` and parse
  `xl/worksheets/sheet1.xml` against `xl/sharedStrings.xml` with Node (v24).
- **AP numbers are positions, not identifiers.** Rows get inserted; refer to
  patterns **by title**.
- **The frozen docs need a fresh, explicit lift every time.** No permission is
  standing. Each lift is logged as a new lettered Part with continuous `G-nn`
  numbering, and removed requirements are struck through inline and annotated,
  never deleted.
- **When a decision ripples, name the complete affected set and ask for approval
  on all of it** — do not amend only the ids the owner happened to mention and
  flag the rest.
- **Real-time does not belong in the access patterns.** Do not raise it.
- **The two architecture documents are not to be reconciled.**
  `decisiones_arquitectura.md` is the owner's personal record, permanently.
  `architecture.md` §2 stays authoritative for what is pending — do **not** read
  the other file as unblocking anything.

## Uncommitted

Nothing has been committed across four sessions; the owner has not asked.
`docs/access_patterns_review.md` is untracked. Modified: `docs/architecture.md`,
`docs/app_user_stories.md`, `docs/conventions.md`, `docs/coverage_analysis.md`,
`docs/gaps_and_resolutions.md`, `docs/gaps_pending_stakeholders.md`,
`docs/requirements.md`, `docs/verification.md`, `feature_list.json`, `init.sh`,
`progress/history.md`, this file.
