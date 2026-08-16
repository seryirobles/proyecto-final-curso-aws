# Data model and access patterns — implementation reference

> **This document is the source of truth for persistence.** It supersedes the
> working review records (`data_structure_review.md`, `access_patterns_review.md`)
> that produced it. Where this file and any other document disagree, **this file
> wins**, except for the owner's spreadsheet
> (`Desktop/lab-final-patrones-acceso.xlsx`) when it is actually present — that
> remains the authoring surface.

**Status: closed and verified.** One DynamoDB table, **9 item types**,
**27 access patterns**, **no secondary indexes**, **no scans**. Verified
attribute-by-attribute against the spreadsheet on 2026-08-16.

**Read §2 before writing a single line of persistence code.** It is the section
that exists nowhere else and the one that causes silent, hard-to-find bugs.

---

## 1. The table

Single table, named **`data`**. All nine item types share it.

| PK | SK | Item type | Attributes |
|---|---|---|---|
| `USUARIOS` | `ID#<idUsuario>` | `DatosUsuario` | `nombreUsuario, tipo, isPassReseteada, passHash` |
| `USUARIOS` | `NOMBRE#<nombreUsuario>` | `NombreIDUsuario` | `idUsuario` |
| `SEMANA#<idSemana>` | `DIA#<numeroDia>#COMIDA#<numeroComida>#ID#<idPlato>` | `DatosPlatoSemana` | `nombrePlato, tiempo, numeroComensales, tipoAlimento, lista(nombreIngrediente, cantidad, unidad), lista(nombreUtensilio), lista(numeroPaso, descripcionPaso), añadidoPor` |
| `SEMANA#<idSemana>` | `DIA#<numeroDia>#COMIDA#<numeroComida>#DEFINITIVO` | `DatosDefinitivoSemana` | `idPlatoDefinitivo` |
| `BIBLIOTECA#<idBiblioteca>` | `ID#<idPlato>` | `DatosPlatoBiblioteca` | `nombrePlato, tipoAlimento, tiempo, numeroComensales, añadidoPor, lista(nombreIngrediente, cantidad, unidad), lista(nombreUtensilio), lista(numeroPaso, descripcionPaso)` |
| `COMPRA#<idLista>` | `INGREDIENTE#<idIngrediente>` | `DatosIngredienteLista` | `nombreIngrediente, cantidad, unidad, isComprado` |
| `COMPRA#<idLista>` | `LOCK` | `LockLista` | `ttl, ownerId` |
| `GRUPOREGLAS#<idGrupoReglas>` | `REGLA#<idRegla>` | `DatosRegla` | `tipoRegla, tipoAlimento, cantidad, numeroDia, numeroComida, idPlato` |
| `PETICIONIA#<idPeticionIA>` | `METADATA` | `DatosPeticionIA` | `estado, resultado, ttl` |

**Secondary indexes: none.** That is the finished answer, not an unfinished
column — see §7.

**Persisted attribute names are Spanish**, matching the access patterns that read
them. Python identifiers are English per `docs/conventions.md`; map at the
adapter boundary, not in the domain.

### 1.1 Attribute notes

- **`passHash`** is a hash, never a password. The `pass` appearing in AP4, AP6
  and AP7 is the plaintext *input to the API*, hashed before it reaches the
  table. Policy is `FR-AUTH-15` (NIST SP 800-63B).
- **`tipoAlimento`** is the one predominant ingredient category, from the fixed
  `FR-RULE-04` set. It is `tipoAlimento` everywhere — never `tipoComida`.
- **`añadidoPor`** holds an **`idUsuario`**, never a username. `FR-AUTH-17` lets
  a removed account's username be reused, so storing the name would silently
  reattribute old content to a new person.
- **`idPlatoDefinitivo`** is masculine everywhere (agreeing with *plato*), in
  both the stored attribute and AP8/AP9/AP11.
- **`ttl`** appears on exactly two item types, `DatosPeticionIA` and `LockLista`,
  under the same name. This is **required**: DynamoDB TTL is configured on
  exactly one attribute name per table. No other item type may carry a `ttl`
  attribute, or it will start expiring.

---

## 2. Key formats — the part that exists nowhere else

A key template like `SEMANA#<idSemana>` does not say what the value *looks like*.
Left unwritten, an implementer reaches for a UUID and breaks `FR-MENU-02`
silently. **Four of the five below carry a trap that no test will catch for you.**

### `idSemana` — ISO week identifier

```
SEMANA#<isoYear>-W<ww>          example:  SEMANA#2026-W33
```

| Rule | Why |
|---|---|
| `isoYear` is the **ISO week-numbering year**, never the calendar year | ⚠ They differ at year boundaries: **2026-12-28 belongs to `2027-W01`**. Taking the year from the date and the week from the ISO calendar is wrong once a year — on a rollover week. |
| `ww` is **zero-padded to two digits**, `W01`–`W53` | Keys sort as bytes. Unpadded, `W9` sorts after `W10`. |
| Weeks run **Monday→Sunday**, resolved in **Europe/Madrid** | `FR-MENU-01`, `FR-MENU-02`. |
| The id is **derived from the clock, never stored as state** | Nothing marks a week "current". That is what makes rollover cheap — no week data moves; weeks simply stop being current. |

```python
iso_year, iso_week, numero_dia = fecha.isocalendar()
id_semana = f"{iso_year}-W{iso_week:02d}"
```

Use `date.isocalendar()[0]` for the year. **Never `date.year`.**

### `idPlato` — meal identifier

```
time-sortable surrogate id (ULID or KSUID) — NOT a UUIDv4
```

⚠ **`idPlato` is the last segment of `DatosPlatoSemana`'s sort key, so it *is*
the in-slot candidate ordering.** A random UUIDv4 satisfies every other
constraint — unique, immutable, opaque — so nothing errors. The candidates
simply come back shuffled, and no test written against a single insertion
catches it.

This matters because `FR-CAND-01` permits two candidates with the same name in
one slot. Insertion order is then the *only* thing distinguishing them on screen.

A library recipe copied into a week takes a **new** `idPlato`: the week item is a
snapshot (`FR-CAND-07`), not a reference. Sharing the id would re-couple them.

### `numeroDia` — day of week

```
Monday = 1   Tuesday = 2   Wednesday = 3   Thursday = 4
Friday = 5   Saturday = 6  Sunday = 7
```

⚠ **One-based — this is `date.isocalendar()[2]`, NOT `date.weekday()`.** The two
differ by one. Mixing them shifts every day and lands Sunday in the next week's
partition, **and it passes every test written on a Monday.**

Single digit, so no padding is needed.

### `numeroComida` — meal slot

```
lunch = 1        dinner = 2
```

One-based, matching `numeroDia`, so the whole key speaks one numbering system.
`COMIDA#1` sorts before `COMIDA#2`, preserving lunch-before-dinner. Numeric
rather than `ALMUERZO`/`CENA` because those sort correctly only by alphabetical
accident, which breaks the moment a third slot exists.

### `idPeticionIA` — AI idempotency key

⚠ **A deterministic hash of the generation request — never a freshly minted id.**
`FR-AI-08` requires that resubmitting the same request (same week, slots and
effective rules) produces neither duplicate candidates nor duplicate AI charges.
A random id makes every retry a cache miss and pays for the model call twice.

The hash must cover exactly the fields defining request identity: two genuinely
different requests must never collide, and one retried request must always hit.
The per-run rule override lives in the request payload and is **not persisted**,
so a retry recomputes the same hash.

### Username reservation key — folded

Usernames are unique **case- and accent-insensitively**. The fold happens in
**application code**; the sheet keeps `NOMBRE#<nombreUsuario>`.

- The **reservation key** (`NombreIDUsuario`'s SK) holds the folded form —
  lower-cased, accent- and whitespace-stripped. Same treatment `FR-SHOP-03`
  defines for ingredient names; **put it behind one shared helper.** Two call
  sites that fold slightly differently produce reservations that never match.
- The **display form** is `DatosUsuario.nombreUsuario`, stored with the exact
  casing the admin typed. Normalizing the key does **not** lowercase what the
  user sees.

⚠ **Fold only when *creating* a reservation. To delete one, look its key up —
never re-fold the old name.** See §5.2; this is the trap.

Why case-insensitive when `FR-AUTH-17` does not say so: the placeholder
reservation depends on it (reserving `Usuario Desconocido` case-sensitively
leaves `usuario desconocido` free), there is no self-service password recovery
(`FR-AUTH-04` + `NFR-SEC-04` means a capitalisation typo gives an error that
explains nothing), and `José`/`Jose` is the collision an es-ES user base will
actually produce.

---

## 3. Shared partitions and sort order

Three partitions hold more than one item type. Their byte ordering is
load-bearing.

| Partition | Order | Consequence |
|---|---|---|
| `USUARIOS` | `ID#…` before `NOMBRE#…` (`I` < `N`) | AP1 is `begins_with(SK, 'ID#')` — reservations are never mistaken for accounts. The rename lookup is the mirror image, `begins_with(SK, 'NOMBRE#')`. |
| `SEMANA#<idSemana>` | within a slot, `DEFINITIVO` before `ID#…` (`D` < `I`) | Parsing a slot from AP8 meets the definitive pointer **before** the candidates it must be validated against. No second pass. |
| `COMPRA#<idLista>` | `INGREDIENTE#…` before `LOCK` (`I` < `L`) | AP18 and AP21 read with `begins_with(SK, 'INGREDIENTE#')` so the lock is never returned as a blank shopping row. |

> **`begins_with` on the sort key is a `KeyConditionExpression`, not a
> `FilterExpression`.** DynamoDB never reads the excluded items, so none of these
> three clauses costs a single RCU. Sharing these partitions is **free**, not a
> compromise — do not "optimise" them apart.

**Week ordering** falls out of the sort key: `numeroDia` → `numeroComida` →
`idPlato`. Both numbers are single-digit, so no padding is required.

**Alias every attribute name with `ExpressionAttributeNames`** in condition and
update expressions. `ttl` in particular must be checked against DynamoDB's
reserved-word list; aliasing unconditionally sidesteps the question.

---

## 4. The 27 access patterns

Every pattern below resolves to a `GetItem`, a single-partition `Query`, or a
transactional/batch write. **No scans. No indexes.**

`Frec.` is indicative only — at 2–10 household users every figure is low.

### 4.1 Users — `FR-AUTH-*`

| AP | Title | Params | Returns | Frec. | Operation |
|---|---|---|---|---|---|
| AP1 | Pantalla admin - Listar usuarios | — | `lista(idUsuario, nombreUsuario, tipo, isPassReseteada)` | Baja | `Query` `PK=USUARIOS AND begins_with(SK,'ID#')` |
| AP2 | Obtener usuario | `idUsuario` | `idUsuario, nombreUsuario, tipo, isPassReseteada` | Baja | `GetItem` `USUARIOS / ID#<idUsuario>` |
| AP3 | Obtener usuario por nombre | `nombreUsuario` | `idUsuario, nombreUsuario, tipo, isPassReseteada` | Baja | `GetItem` ×2 — `NOMBRE#<fold>` → `ID#<idUsuario>` |
| AP4 | Pantalla admin - Crear o editar usuario | `nombreUsuario, idUsuario, tipo, pass, isPassReseteada` | `idUsuario, nombreUsuario, tipo, isPassReseteada` | Baja | `TransactWriteItems` — see §5.1 / §5.2 |
| AP5 | Pantalla admin - Eliminar usuario | `idUsuario` | — | Baja | `Query` + `TransactWriteItems` — see §5.2 |
| AP6 | Login | `nombreUsuario, pass` | `idUsuario, tipo, isPassReseteada` | **Alta** | `GetItem` ×2 as AP3, then compare `passHash` |
| AP7 | Establecer contraseña | `idUsuario, pass` | — | Media | `UpdateItem` `USUARIOS / ID#<idUsuario>` — sets `passHash`, clears `isPassReseteada` |

### 4.2 Weeks — `FR-MENU-*`, `FR-CAND-*`

| AP | Title | Params | Returns | Frec. | Operation |
|---|---|---|---|---|---|
| AP8 | Obtener semana | `idSemana` | `idSemana, lista(numeroDia, lista(numeroComida, idPlatoDefinitivo, lista(idPlato, añadidoPor, nombrePlato, tipoAlimento)))` | **Alta** | `Query` `PK=SEMANA#<idSemana>` |
| AP9 | Obtener semana + ingredientes | `idSemana` | as AP8, plus `lista(nombreIngrediente, cantidad, unidad)` per meal | Media | same partition, richer projection |
| AP10 | Obtener comida - Semana | `idSemana, numeroDia, numeroComida, idPlato` | `idSemana, numeroDia, numeroComida, idPlato,` *[receta]*`, añadidoPor` | **Alta** | `GetItem` `DIA#<d>#COMIDA#<c>#ID#<idPlato>` |
| AP11 | Establecer/Desasignar comida definitiva | `idSemana, numeroDia, numeroComida, idPlatoDefinitivo` | same | Media | `PutItem` / `DeleteItem` on `…#DEFINITIVO` |
| AP12 | Eliminar comida | `idSemana, numeroDia, numeroComida, idPlato` | — | Media | `DeleteItem` `…#ID#<idPlato>` |
| AP13 | Editar o añadir comida | `idSemana, idPlato, numeroDia, añadidoPor, numeroComida,` *[receta]* | same | Media | `PutItem` `…#ID#<idPlato>` |

*[receta]* = `nombrePlato, tiempo, numeroComensales, tipoAlimento,
lista(nombreIngrediente, cantidad, unidad), lista(nombreUtensilio),
lista(numeroPaso, descripcionPaso)`

**`FR-MENU-03`'s "at most one definitive per slot" is a property of the primary
key**, not an application check: one slot, one `DEFINITIVO` item. Clearing the
slot (`FR-CAND-08`) is a single `DeleteItem`.

### 4.3 Library — `FR-LIB-*`

| AP | Title | Params | Returns | Frec. | Operation |
|---|---|---|---|---|---|
| AP14 | Obtener biblioteca | `idBiblioteca` | `idBiblioteca, lista(idPlato, nombrePlato, tiempo, tipoAlimento, añadidoPor)` | **Alta** | `Query` `PK=BIBLIOTECA#…` — **name search and category filter are in-memory** |
| AP15 | Obtener comida de la biblioteca | `idBiblioteca, idPlato` | `idBiblioteca, idPlato,` *[receta]*`, añadidoPor` | **Alta** | `GetItem` `ID#<idPlato>` |
| AP16 | Añadir o editar comida (biblioteca) | `idBiblioteca, idPlato,` *[receta]*`, añadidoPor` | same | Media | `PutItem` `ID#<idPlato>` |
| AP17 | Eliminar comida (biblioteca) | `idBiblioteca, idPlato` | — | Media | `DeleteItem` `ID#<idPlato>` |

`FR-LIB-04`'s two filters are both applied in the Lambda, deliberately — see §7.

### 4.4 Shopping list — `FR-SHOP-*`

| AP | Title | Params | Returns | Frec. | Operation |
|---|---|---|---|---|---|
| AP18 | Obtener lista de la compra | `idLista` | `lista(idIngrediente, nombreIngrediente, cantidad, unidad, isComprado)` | **Alta** | `Query` `PK=COMPRA#… AND begins_with(SK,'INGREDIENTE#')` |
| AP19 | Añadir o editar elemento | `idLista, idIngrediente, nombreIngrediente, cantidad, unidad, isComprado` | `idIngrediente, nombreIngrediente, cantidad, unidad, isComprado` | **Alta** | `PutItem` `INGREDIENTE#<idIngrediente>` |
| AP20 | Eliminar elemento | `idLista, idIngrediente` | — | **Alta** | `DeleteItem` `INGREDIENTE#<idIngrediente>` |
| AP21 | Eliminar elementos marcados | `idLista` | `lista(idIngrediente, nombreIngrediente, cantidad, unidad, isComprado)` | Media | `Query` as AP18, filter `isComprado`, then `BatchWriteItem` |

**Re-sync is not an access pattern.** It is composition over AP18 + AP19. Its
serialization is §5.3.

### 4.5 Rules — `FR-RULE-*`

| AP | Title | Params | Returns | Frec. | Operation |
|---|---|---|---|---|---|
| AP22 | Obtener reglas | `idGrupoReglas` | `idGrupoReglas, lista(idRegla, tipoRegla, tipoAlimento, cantidad, numeroDia, numeroComida, idPlato, nombrePlato)` | Media | `Query` `PK=GRUPOREGLAS#…`, then `BatchGetItem` on the library for `nombrePlato` |
| AP23 | Añadir o editar regla | `idGrupoReglas, idRegla, tipoRegla, tipoAlimento, cantidad, numeroDia, numeroComida, idPlato` | same minus `idGrupoReglas` | Media | `PutItem` `REGLA#<idRegla>` |
| AP24 | Eliminar regla | `idGrupoReglas, idRegla` | — | Media | `DeleteItem` `REGLA#<idRegla>` |

⚠ **`DatosRegla` stores no `nombrePlato`, even though AP22 returns it.** See §6.

**A rule stores no author.** Rule attribution is out of MVP scope (G-76/G-78);
`FR-RULE-06`, `FR-SUM-03`, `FR-AUTH-13` and `FR-RT-02` were all amended to match.

`FR-RULE-07`'s cascade (find pin rules referencing a deleted recipe) is a `Query`
on the single rules partition filtered on `idPlato` — **match on the id, never on
the name**, since `FR-CAND-06` allows two library recipes to share a name.

### 4.6 AI idempotency — `FR-AI-08`

| AP | Title | Params | Returns | Frec. | Operation |
|---|---|---|---|---|---|
| AP25 | Añadir o editar petición IA | `idPeticionIA, estado, resultado, ttl` | `idPeticionIA` | Media | `PutItem` `PETICIONIA#<hash> / METADATA` |
| AP26 | Obtener petición IA | `idPeticionIA` | `idPeticionIA, estado, resultado, ttl` | Media | `GetItem` `PETICIONIA#<hash> / METADATA` |
| AP27 | Eliminar petición IA | `idPeticionIA` | — | Media | `DeleteItem` `PETICIONIA#<hash> / METADATA` |

The item stores the **result payload**, not just a status flag. `FR-AI-10` makes
single-recipe output a *preview* saved nowhere else; without the payload a
dropped response means paying for a recipe that exists nowhere and cannot be
returned on retry.

`LockLista` is the only item type with **no** access pattern — it is the
`FR-SHOP-10` serialization mechanism (§5.3), not a user-facing operation.

---

## 5. Concurrency and correctness

The four places where a naive implementation is wrong.

### 5.1 Username uniqueness is enforced by the write, not by a check

`FR-AUTH-17` uniqueness is **not** a read-then-write validation — that is a
TOCTOU, and two admins racing would both see a name free. Write
`NombreIDUsuario` in the **same `TransactWriteItems`** as `DatosUsuario`, with
`attribute_not_exists(SK)` on the reservation. The condition *is* the check, so
there is no window.

The "unknown user" placeholder name is reserved by seeding its reservation item
at deploy time, which makes it permanently uncreatable (`FR-AUTH-17`).

### 5.2 A rename must release its old reservation — by lookup, never by re-folding

⚠ **The trap:** to rename a user you must delete the old `NOMBRE#…` item; to
delete an item you need its key; and its key is the *folded old name*, which
nothing stores. AP4 receives the **new** name; AP5 receives only `idUsuario`.
Neither carries the current name.

Left unhandled, a rename abandons the old reservation: **the old username stays a
working login indefinitely**, and it can never be reused, contradicting
`FR-AUTH-17`.

**Three steps:**

1. **Look up the current reservation** — `Query` the `USUARIOS` partition with
   `begins_with(SK, 'NOMBRE#')`, take the item whose `idUsuario` matches. That
   item's SK **is** the key to delete, read off the record.
2. **Delete it.**
3. **Write the new name and its reservation.**

Steps 2 and 3 are one transaction:

```
Delete  USUARIOS / <oldSK, exactly as read in step 1>
                                        condition: attribute_exists(SK)
                                               AND idUsuario = :me
Put     USUARIOS / NOMBRE#<newFolded>   condition: attribute_not_exists(SK)
Update  USUARIOS / ID#<idUsuario>       SET nombreUsuario = :new
```

**Why look it up rather than re-fold the old name.** `fold()` is shared with
`FR-SHOP-03`'s ingredient normalization. If it is ever refined — collapsing
internal whitespace, handling `ñ` differently — a key re-derived today stops
matching a key written yesterday. The `Delete` silently no-ops on a non-existent
item and the stale reservation becomes permanent and unaddressable. Reading the
key removes the failure mode instead of documenting it. **No normalized form
needs storing anywhere.**

**Why the conditions are still needed.** The lookup is a read before a write, so
it has a window. `attribute_exists(SK)` closes it — a concurrent rename that
already removed the reservation makes the delete *fail* rather than no-op, and
the transaction rolls back. `idUsuario = :me` guards against deleting a
reservation since re-pointed.

**AP5 "Eliminar usuario" is the same shape:** look up the reservation, then one
transaction deleting both it and `ID#<idUsuario>`. That conditional delete is
what actually makes "a removed account's username may be reused" true.

### 5.3 The shopping-list lock must compare `ttl` itself

⚠ **The one item that causes a real outage if implemented naively.**

**DynamoDB TTL deletion is best-effort and may lag up to 48 hours.** The lock
must treat `ttl` as *data it compares*, never as a guarantee the item is gone.

```
Acquire:  condition  attribute_not_exists(SK) OR ttl < :now
Release:  condition  ownerId = :me
```

Releasing conditionally on `ownerId` stops a holder whose lease already expired
from deleting its successor's lock. Trusting TTL to expire the lock leaves
re-sync wedged for up to two days.

This is `FR-SHOP-10`'s *serialized* clause. Without it, two simultaneous re-sync
presses can each find no matching unchecked row and each create one.

### 5.4 Dangling references resolve at read time — both of them

Two references can dangle by design. **Neither gets a transaction or a cleanup
job; both are resolved when read.** One consistent rule, not two.

| Reference | Resolution |
|---|---|
| `idPlatoDefinitivo` pointing at a deleted meal | **AP8 and AP9 must validate `idPlatoDefinitivo` against the meals in the same response** before returning it. No match ⇒ read as *no definitive*. The check is free — the Query already returned every meal in the week. A dangling slot item is inert: the next promotion overwrites it. *(AP10 returns a single meal and no `idPlatoDefinitivo`, so it has nothing to validate.)* |
| `añadidoPor` pointing at a removed account | Renders as the "unknown user" placeholder (`FR-SUM-03`). Resolved against the user list (AP1, ≤10 rows, cacheable). No fan-out write, no author index. |

Week meals are **snapshots** (`FR-CAND-07`), so deleting a library recipe cannot
dangle one — editing or deleting the library entry leaves existing snapshots
untouched.

---

## 6. Read-time resolution — do NOT denormalize these

**The governing rule: a write is the record of what is persisted.** An attribute
that appears in a *return* but that no *write* ever supplies is **not stored** —
it is resolved live when the question is asked.

**Four patterns take a second read by design.** Every one of those second reads
is itself a key lookup, so none needs an index.

| Pattern | Second read | Why it is not stored |
|---|---|---|
| AP3, AP6 (login) | `GetItem NOMBRE#…` → `GetItem ID#…` | The reservation item exists for uniqueness; the account data lives once. |
| AP22 (Obtener reglas) | `BatchGetItem` on the library for each pin rule's `nombrePlato` | ⚠ Storing it would mean renaming a library recipe leaves every pin rule showing the old name. |
| AP8, AP9 | `añadidoPor` is an id; rendering a name needs the user set | `FR-AUTH-17` allows username reuse — a stored name would reattribute old content to a new person. |

> **Do not "fix" these by denormalizing.** Each one reintroduces exactly the
> staleness the rule exists to prevent. This was raised as a defect during review,
> investigated, and withdrawn — the premise was wrong.

Accurate claim for the README: **"no secondary indexes, and no query that is not
a key lookup or a single-partition scan-free `Query`."** Not "one operation per
pattern" — that is overstated and is the claim a reviewer will probe.

---

## 7. Settled — do not re-open

Each of these looks like an improvement and was already considered and rejected.
The reason is given so the analysis is not repeated.

| Question | Answer, and why |
|---|---|
| **Add a GSI for the login path?** | **No.** `NombreIDUsuario` answers AP3 and AP6 as a point lookup. A GSI would add eventual consistency to authentication for nothing. |
| **Index `FR-LIB-04`'s name search or category filter?** | **No — both filter in memory.** A sort key cannot do substring matching at all, only `begins_with`; a user typing `curry` expects "Lentejas al curry". Indexing buys a partial answer at full cost. Name search is also needed in *every picker*, the category filter only in the library view — a key would serve the rarer need. And `nombrePlato` is mutable. |
| **Move `LockLista` to its own `LISTA#` partition so the list reads need no `begins_with`?** | **No.** It was tried and reverted. It gave one entity two prefixes, and the clause it removed was already free (key condition, not filter). One concept, one name. |
| **Store the normalized ingredient name on `DatosIngredienteLista`?** | **Declined.** Re-sync re-derives it each press; not worth an attribute at household scale. |
| **Rename `NombreIDUsuario` to fit the `Datos*` convention?** | **Declined.** Cosmetic. |
| **`USUARIOS`, `BIBLIOTECA#…`, `COMPRA#…`, `GRUPOREGLAS#…` are single-value partitions — isn't that a hot-partition risk?** | **This is the one choice a reviewer will question on sight.** It does not bite here: ≤10 users, `Baja`–`Media` writes, partitions that stay small indefinitely, against a ~3000 RCU / 1000 WCU per-partition ceiling. The alternatives are worse in a single-table design — a `Scan` sweeps every week, recipe and shopping item, and a GSI with a constant partition key has the *identical* cardinality property plus a full index copy. The ids are kept (rather than collapsed to literals) so a future multi-group model is a prefix change, not a key-schema rewrite. |
| **Add a thin index item so AP14 / AP8 read less?** | **Not now.** Measured: recipes are ~2–4KB, so the 1MB Query page holds roughly 250–500 — years of household cooking. AP8 does read full recipe content it does not return (1MB applies *before* projection). Recorded so it is not rediscovered as a surprise, not so it is fixed. |

---

## 8. Verified constraints

| Check | Result |
|---|---|
| Item size vs the 400KB limit | ✅ Largest is `DatosPlatoSemana` / `DatosPlatoBiblioteca` at ~2–4KB |
| 1MB Query page | ✅ A week is ~42 candidate items; the library ~250–500 recipes |
| Item-collection 10GB limit | ✅ Not applicable — that limit exists only for tables with an LSI, and there are none |
| TTL configured on one attribute name | ✅ `ttl` on `DatosPeticionIA` and `LockLista` only |
| Attribute naming vs the patterns | ✅ Every stored name agrees with every pattern that reads it |
| Write/read symmetry | ✅ Every stored attribute has a pattern that writes it; every returned attribute is stored, key-derived, or resolved by an explicit §6 rule |
| Scans | ✅ None |
| Secondary indexes | ✅ None |

---

## 9. Out of scope — parked by decision, not overlooked

Do not report these as gaps.

| Area | Status |
|---|---|
| **Archive** (`FR-ARCH-01`…`-04`) | Parked, MVP scope. Reading a past week *is* AP8 pointed at an older `idSemana`, and read-only needs no stored flag — a week is closed iff its id sorts before the computed current week. ⚠ But `FR-ARCH-04`'s reverse-chronological browse is **not** free: `idSemana` is in the **partition** key and DynamoDB cannot list or sort partition keys. Unparking costs ids generated backwards arithmetically, or an index. The `FR-ARCH-02` shopping-list snapshot has no item type and parks with it. |
| **Real-time** (`FR-RT-01`…`-03`) | Out of scope for the data layer by owner decision. Adds no new *read* patterns — reconnect resynchronisation is re-calling existing reads. What it adds is a fan-out obligation on existing writes, which belongs in the design. Blocked on architecture **P3**. |
| **Sessions** (`FR-AUTH-09`, `-11`, `-14`, `-16`) | Blocked on architecture **P2**. If a managed identity provider is chosen these items may not exist at all. Note the shape when it unblocks: "invalidate **all** sessions of an account" is a query by `idUsuario`, not a point delete. |
| **Cold storage** (`FR-ARCH-03`) | Blocked on **P6**. Export needs a whole-week full-content read that no pattern provides. |

**Week rollover needs no dedicated pattern.** Three of its five steps dissolve
because `idSemana` is computed from the clock: promotion is a no-op ("current" is
derived, never stored), initialisation is a no-op if weeks are created lazily on
first write, and archiving is a no-op because past weeks already sit under older
keys in the same key space. What survives is the `FR-SHOP-09` cleanup (AP21,
naturally idempotent — "delete every checked item") and the archive snapshot,
which parks above.

---

## 10. Provenance

Derived from the closed access-pattern catalogue and PK/SK design, authored by
the owner in `Desktop/lab-final-patrones-acceso.xlsx` and reviewed across
sessions from 2026-08-02 to 2026-08-16. Verified attribute-by-attribute against
the spreadsheet at its 2026-08-16 14:23 save.

Requirement changes made during that work are recorded as **Parts I–P
(`G-69`–`G-80`)** in `docs/gaps_and_resolutions.md`, which remains the
authoritative record of *why* each requirement reads as it does.

`docs/architecture.md` **§1.2.1** carries the P1 decision (DynamoDB, single
table). **P2–P7 remain pending and human-owned** — hitting one means the feature
is `blocked`.
