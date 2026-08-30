# Data model and access patterns — implementation reference

> **This document is the source of truth for persistence.** It supersedes the
> working review records (`data_structure_review.md`, `access_patterns_review.md`)
> that produced it. Where this file and any other document disagree, **this file
> wins**, except for the owner's spreadsheet
> (`Desktop/lab-final-patrones-acceso.xlsx`) when it is actually present — that
> remains the authoring surface.

**Status: closed and verified.** One DynamoDB table, **10 item types**,
**29 access patterns**, **no secondary indexes**, **no scans**. Verified
attribute-by-attribute against the spreadsheet on 2026-08-16; AP28 added
2026-08-27 by `G-87`/feature 15 `auth_flow`, `MarcaCambio` and AP29 added
2026-08-27 by `G-88`/architecture P3 (both human-approved, not yet in the
owner's spreadsheet).

**Read §2 before writing a single line of persistence code.** It is the section
that exists nowhere else and the one that causes silent, hard-to-find bugs.

---

## 1. The table

Single table, named **`data`**. All ten item types share it.

| PK | SK | Item type | Attributes |
|---|---|---|---|
| `USUARIOS` | `ID#<idUsuario>` | `DatosUsuario` | `nombreUsuario, tipo, isPassReseteada, passHash, validoDesde` |
| `USUARIOS` | `NOMBRE#<nombreUsuario>` | `NombreIDUsuario` | `idUsuario` |
| `SEMANA#<idSemana>` | `DIA#<numeroDia>#COMIDA#<numeroComida>#ID#<idPlato>` | `DatosPlatoSemana` | `nombrePlato, tiempo, numeroComensales, tipoAlimento, lista(nombreIngrediente, cantidad, unidad), lista(nombreUtensilio), lista(numeroPaso, descripcionPaso), añadidoPor` |
| `SEMANA#<idSemana>` | `DIA#<numeroDia>#COMIDA#<numeroComida>#DEFINITIVO` | `DatosDefinitivoSemana` | `idPlatoDefinitivo` |
| `SEMANA#<idSemana>` | `MARCA` | `MarcaCambio` | `marcaCambio` |
| `BIBLIOTECA#<idBiblioteca>` | `ID#<idPlato>` | `DatosPlatoBiblioteca` | `nombrePlato, tipoAlimento, tiempo, numeroComensales, añadidoPor, lista(nombreIngrediente, cantidad, unidad), lista(nombreUtensilio), lista(numeroPaso, descripcionPaso)` |
| `BIBLIOTECA#<idBiblioteca>` | `MARCA` | `MarcaCambio` | `marcaCambio` |
| `COMPRA#<idLista>` | `INGREDIENTE#<idIngrediente>` | `DatosIngredienteLista` | `nombreIngrediente, cantidad, unidad, isComprado` |
| `COMPRA#<idLista>` | `LOCK` | `LockLista` | `ttl, ownerId` |
| `COMPRA#<idLista>` | `MARCA` | `MarcaCambio` | `marcaCambio` |
| `GRUPOREGLAS#<idGrupoReglas>` | `REGLA#<idRegla>` | `DatosRegla` | `tipoRegla, tipoAlimento, cantidad, numeroDia, numeroComida, idPlato` |
| `GRUPOREGLAS#<idGrupoReglas>` | `MARCA` | `MarcaCambio` | `marcaCambio` |
| `PETICIONIA#<idPeticionIA>` | `METADATA` | `DatosPeticionIA` | `estado, resultado, ttl` |

**`MarcaCambio` is one item type, instantiated once per pollable
partition** (weeks, library, shopping list, rules) — four instances, not a
new item family per resource. It exists to serve `FR-RT-01`/`-03`'s
polling design (`G-88`, `docs/architecture.md` §1.2.4); see §1.1 for what
it is and, more importantly, what it must never be used for.

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
- **`validoDesde`** (`G-87`, feature 15 `auth_flow`) is the auth-token revocation
  marker: a token is trusted only if its `issued_at` is after this timestamp.
  Set at account creation to the creation instant. **AP4** advances it to now
  on an admin-driven password change/reset, and the new **AP28** (Cerrar
  sesión) advances it to now on a self-service logout — both revoke every
  token issued to the account before that moment, on every device. **AP7**
  (the account holder's own mandatory set-password step) deliberately leaves
  it untouched: bumping it there would invalidate the very token the caller
  is using to complete that same request.
- **`marcaCambio`** (`G-88`, architecture P3) is a per-resource change
  counter powering the polling design's conditional GET — a poll compares
  its held value against `AP29`'s cheap read and only fetches the full
  resource if they differ. It is a **counter, incremented atomically**
  (`ADD marcaCambio 1`), never a timestamp — two racing writes both land
  correctly with no lost update, and there is no clock-skew-between-Lambdas
  failure mode to worry about.
  ⚠ **The bump is always inside the same `TransactWriteItems` as the data
  change it marks — never a separate call, and never before the data
  write.** Either ordering otherwise leaves a window where a poll can
  observe a marker without its matching data, or a write without its
  matching marker, and either way another client misses the change
  *permanently*, not just until the next poll. This is not a standalone
  access pattern — each amended write in §4.2–§4.5 carries its own bump as
  the second leg of its transaction, the same way `AP4` already carries a
  username reservation as a second leg (§5.1/§5.2).
  **Ideally the bump happens once per logical action**, not once per item,
  so a bulk operation (whole-week AI generation, shopping-list re-sync)
  doesn't cause a burst of redundant "changed" polls while it runs — but
  as documented in §4.2/§4.4, an operation composed of several single-item
  access-pattern calls (`AP13`, `AP19`) bumps once per call today, which is
  safe, just not optimal. Collapsing it to one bump is a future
  transaction-shape decision, not settled here.
  ⚠ **It is deliberately not named `version`, and it must never appear in
  a write's `ConditionExpression`.** It is read-only metadata for clients
  deciding whether to refetch — conditioning a write on it would silently
  turn `FR-RT-02`'s settled last-write-wins policy (`G-07`) into optimistic
  locking with conflict errors nothing here is designed to produce.

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
| `isoYear` is the **ISO week-numbering year**, never the calendar year | ⚠ They differ at year boundaries: **2025-12-31 belongs to `2026-W01`** (taking `date.year` would give `2025-W01`, off by a full year), and **2027-01-01 belongs to `2026-W53`** (`date.year` would give `2027-W53`, a week that does not exist). Taking the year from the date and the week from the ISO calendar is wrong once a year — on a rollover week. *Corrected 2026-08-18: this cell previously cited 2026-12-28 → `2027-W01`. That is wrong — 2026 is a 53-week ISO year, so 2026-12-28 is `2026-W53` (a Monday) and its two years agree, which is precisely the case that does **not** demonstrate the trap.* |
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

Five partitions hold more than one item type. Their byte ordering is
load-bearing. `MarcaCambio`'s `MARCA` sort key (`G-88`) newly shares all
four resource partitions — weeks, library, shopping list and rules — so
every whole-partition read among them now needs an explicit key-condition
scope to exclude it, even the three that previously got away without one.

| Partition | Order | Consequence |
|---|---|---|
| `USUARIOS` | `ID#…` before `NOMBRE#…` (`I` < `N`) | AP1 is `begins_with(SK, 'ID#')` — reservations are never mistaken for accounts. The rename lookup is the mirror image, `begins_with(SK, 'NOMBRE#')`. |
| `SEMANA#<idSemana>` | within a slot, `DEFINITIVO` before `ID#…` (`D` < `I`); `MARCA` sorts after every `DIA#…` row | Parsing a slot from AP8 meets the definitive pointer **before** the candidates it must be validated against. No second pass. **AP8/AP9 are amended** to `begins_with(SK, 'DIA#')` — previously a bare partition `Query`, since every prior item type happened to start with `DIA#`; `MarcaCambio` is the first that does not. |
| `BIBLIOTECA#<idBiblioteca>` | `ID#…` before `MARCA` (`I` < `M`) | **AP14 is amended** to `begins_with(SK, 'ID#')` — same reason as AP8/AP9: previously bare, now needs the exclusion. |
| `COMPRA#<idLista>` | `INGREDIENTE#…` before `LOCK` before `MARCA` (`I` < `L` < `M`) | AP18 and AP21 already read with `begins_with(SK, 'INGREDIENTE#')`, so the lock is never returned as a blank shopping row — **unamended**, that scope already excludes `MarcaCambio` for free. |
| `GRUPOREGLAS#<idGrupoReglas>` | `MARCA` before `REGLA#…` (`M` < `R`) | **AP22 is amended** to `begins_with(SK, 'REGLA#')` — previously bare, same reason as AP8/AP9/AP14. |

> **`begins_with` on the sort key is a `KeyConditionExpression`, not a
> `FilterExpression`.** DynamoDB never reads the excluded items, so none of
> these clauses costs a single RCU. Sharing these partitions is **free**,
> not a compromise — do not "optimise" them apart.

**Week ordering** falls out of the sort key: `numeroDia` → `numeroComida` →
`idPlato`. Both numbers are single-digit, so no padding is required.

**Alias every attribute name with `ExpressionAttributeNames`** in condition and
update expressions. `ttl` in particular must be checked against DynamoDB's
reserved-word list; aliasing unconditionally sidesteps the question.

---

## 4. The 29 access patterns

Every pattern below resolves to a `GetItem`, a single-partition `Query`, or a
transactional/batch write. **No scans. No indexes.**

`Frec.` is indicative only — at 2–10 household users every figure is low.

### 4.1 Users — `FR-AUTH-*`

| AP | Title | Params | Returns | Frec. | Operation |
|---|---|---|---|---|---|
| AP1 | Pantalla admin - Listar usuarios | — | `lista(idUsuario, nombreUsuario, tipo, isPassReseteada)` | Baja | `Query` `PK=USUARIOS AND begins_with(SK,'ID#')` |
| AP2 | Obtener usuario | `idUsuario` | `idUsuario, nombreUsuario, tipo, isPassReseteada` | Baja | `GetItem` `USUARIOS / ID#<idUsuario>` |
| AP3 | Obtener usuario por nombre | `nombreUsuario` | `idUsuario, nombreUsuario, tipo, isPassReseteada` | Baja | `GetItem` ×2 — `NOMBRE#<fold>` → `ID#<idUsuario>` |
| AP4 | Pantalla admin - Crear o editar usuario | `nombreUsuario, idUsuario, tipo, pass, isPassReseteada` | `idUsuario, nombreUsuario, tipo, isPassReseteada` | Baja | `TransactWriteItems` — see §5.1 / §5.2. Sets `validoDesde` to the creation instant on create, or to now on an admin-driven password change/reset of an existing account (revokes that account's outstanding tokens) |
| AP5 | Pantalla admin - Eliminar usuario | `idUsuario` | — | Baja | `Query` + `TransactWriteItems` — see §5.2 |
| AP6 | Login | `nombreUsuario, pass` | `idUsuario, tipo, isPassReseteada` | **Alta** | `GetItem` ×2 as AP3, then compare `passHash` |
| AP7 | Establecer contraseña | `idUsuario, pass` | — | Media | `UpdateItem` `USUARIOS / ID#<idUsuario>` — sets `passHash`, clears `isPassReseteada`. Does **not** touch `validoDesde` (§1.1) |
| AP28 | Cerrar sesión | `idUsuario` | — | Baja | `UpdateItem` `USUARIOS / ID#<idUsuario>` — sets `validoDesde = now`, revoking every outstanding token for the account |

### 4.2 Weeks — `FR-MENU-*`, `FR-CAND-*`

| AP | Title | Params | Returns | Frec. | Operation |
|---|---|---|---|---|---|
| AP8 | Obtener semana | `idSemana` | `idSemana, lista(numeroDia, lista(numeroComida, idPlatoDefinitivo, lista(idPlato, añadidoPor, nombrePlato, tipoAlimento)))` | **Alta** | `Query` `PK=SEMANA#<idSemana> AND begins_with(SK,'DIA#')` |
| AP9 | Obtener semana + ingredientes | `idSemana` | as AP8, plus `lista(nombreIngrediente, cantidad, unidad)` per meal | Media | same partition and key condition as AP8, richer projection |
| AP10 | Obtener comida - Semana | `idSemana, numeroDia, numeroComida, idPlato` | `idSemana, numeroDia, numeroComida, idPlato,` *[receta]*`, añadidoPor` | **Alta** | `GetItem` `DIA#<d>#COMIDA#<c>#ID#<idPlato>` |
| AP11 | Establecer/Desasignar comida definitiva | `idSemana, numeroDia, numeroComida, idPlatoDefinitivo` | same | Media | `TransactWriteItems`: `PutItem`/`DeleteItem` on `…#DEFINITIVO` + bump `SEMANA#<idSemana>` `marcaCambio` (§4.7) |
| AP12 | Eliminar comida | `idSemana, numeroDia, numeroComida, idPlato` | — | Media | `TransactWriteItems`: `DeleteItem` `…#ID#<idPlato>` + bump `SEMANA#<idSemana>` `marcaCambio` (§4.7) |
| AP13 | Editar o añadir comida | `idSemana, idPlato, numeroDia, añadidoPor, numeroComida,` *[receta]* | same | Media | `TransactWriteItems`: `PutItem` `…#ID#<idPlato>` + bump `SEMANA#<idSemana>` `marcaCambio` (§4.7) |

*[receta]* = `nombrePlato, tiempo, numeroComensales, tipoAlimento,
lista(nombreIngrediente, cantidad, unidad), lista(nombreUtensilio),
lista(numeroPaso, descripcionPaso)`

**`FR-MENU-03`'s "at most one definitive per slot" is a property of the primary
key**, not an application check: one slot, one `DEFINITIVO` item. Clearing the
slot (`FR-CAND-08`) is a single `DeleteItem`.

**Whole-week AI generation writes up to 14 slots via repeated `AP13`
calls, each bumping `SEMANA#<idSemana>`'s `marcaCambio` once** (§1.1) —
safe, not optimal, same caveat as shopping re-sync (§4.4). A client
polling mid-generation may see several "changed" responses in quick
succession rather than one at the end.

### 4.3 Library — `FR-LIB-*`

| AP | Title | Params | Returns | Frec. | Operation |
|---|---|---|---|---|---|
| AP14 | Obtener biblioteca | `idBiblioteca` | `idBiblioteca, lista(idPlato, nombrePlato, tiempo, tipoAlimento, añadidoPor)` | **Alta** | `Query` `PK=BIBLIOTECA#… AND begins_with(SK,'ID#')` — **name search and category filter are in-memory** |
| AP15 | Obtener comida de la biblioteca | `idBiblioteca, idPlato` | `idBiblioteca, idPlato,` *[receta]*`, añadidoPor` | **Alta** | `GetItem` `ID#<idPlato>` |
| AP16 | Añadir o editar comida (biblioteca) | `idBiblioteca, idPlato,` *[receta]*`, añadidoPor` | same | Media | `TransactWriteItems`: `PutItem` `ID#<idPlato>` + bump `BIBLIOTECA#<idBiblioteca>` `marcaCambio` (§4.7) |
| AP17 | Eliminar comida (biblioteca) | `idBiblioteca, idPlato` | — | Media | `TransactWriteItems`: `DeleteItem` `ID#<idPlato>` + bump `BIBLIOTECA#<idBiblioteca>` `marcaCambio` (§4.7) |

`FR-LIB-04`'s two filters are both applied in the Lambda, deliberately — see §7.

### 4.4 Shopping list — `FR-SHOP-*`

| AP | Title | Params | Returns | Frec. | Operation |
|---|---|---|---|---|---|
| AP18 | Obtener lista de la compra | `idLista` | `lista(idIngrediente, nombreIngrediente, cantidad, unidad, isComprado)` | **Alta** | `Query` `PK=COMPRA#… AND begins_with(SK,'INGREDIENTE#')` |
| AP19 | Añadir o editar elemento | `idLista, idIngrediente, nombreIngrediente, cantidad, unidad, isComprado` | `idIngrediente, nombreIngrediente, cantidad, unidad, isComprado` | **Alta** | `TransactWriteItems`: `PutItem` `INGREDIENTE#<idIngrediente>` + bump `COMPRA#<idLista>` `marcaCambio` (§4.7) |
| AP20 | Eliminar elemento | `idLista, idIngrediente` | — | **Alta** | `TransactWriteItems`: `DeleteItem` `INGREDIENTE#<idIngrediente>` + bump `COMPRA#<idLista>` `marcaCambio` (§4.7) |
| AP21 | Eliminar elementos marcados | `idLista` | `lista(idIngrediente, nombreIngrediente, cantidad, unidad, isComprado)` | Media | `Query` as AP18, filter `isComprado`, then **`TransactWriteItems`** deletes + bump `COMPRA#<idLista>` `marcaCambio` (§4.7) — **amended from `BatchWriteItem`**: a `BatchWriteItem` cannot join the same transaction as the marker bump, and a household shopping list is far under `TransactWriteItems`'s 100-item limit |

**Re-sync is not an access pattern.** It is composition over AP18 + AP19,
so as documented here it bumps `COMPRA#<idLista>`'s `marcaCambio` **once
per differing item**, not once for the whole re-sync — each `AP19` call is
already its own correct transaction. That is safe (§4.7's atomicity rule
still holds for every individual write) but not optimal: other clients may
see a few redundant "changed" polls mid-re-sync instead of one at the end.
Collapsing that to a single bump requires re-sync to become its own
transaction rather than a loop of `AP19` calls — a design choice for
whoever builds feature 26, not settled here. Its serialization is §5.3;
§5.3's lock release is the natural place to add that single bump if the
collapse is done.

### 4.5 Rules — `FR-RULE-*`

| AP | Title | Params | Returns | Frec. | Operation |
|---|---|---|---|---|---|
| AP22 | Obtener reglas | `idGrupoReglas` | `idGrupoReglas, lista(idRegla, tipoRegla, tipoAlimento, cantidad, numeroDia, numeroComida, idPlato, nombrePlato)` | Media | `Query` `PK=GRUPOREGLAS#… AND begins_with(SK,'REGLA#')`, then `BatchGetItem` on the library for `nombrePlato` |
| AP23 | Añadir o editar regla | `idGrupoReglas, idRegla, tipoRegla, tipoAlimento, cantidad, numeroDia, numeroComida, idPlato` | same minus `idGrupoReglas` | Media | `TransactWriteItems`: `PutItem` `REGLA#<idRegla>` + bump `GRUPOREGLAS#<idGrupoReglas>` `marcaCambio` (§4.7) |
| AP24 | Eliminar regla | `idGrupoReglas, idRegla` | — | Media | `TransactWriteItems`: `DeleteItem` `REGLA#<idRegla>` + bump `GRUPOREGLAS#<idGrupoReglas>` `marcaCambio` (§4.7) |

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

`LockLista` is the only item type with **no** access pattern of its own —
it is the `FR-SHOP-10` serialization mechanism (§5.3), not a user-facing
operation. `MarcaCambio` has one, `AP29` below, plus the amended write in
every mutating pattern across §4.2–§4.5.

### 4.7 Change markers — cross-cutting, `FR-RT-01`/`-03`, `G-88`

| AP | Title | Params | Returns | Frec. | Operation |
|---|---|---|---|---|---|
| AP29 | Obtener marca de cambio | clave de partición del recurso (`idSemana`, `idLista`, `idGrupoReglas` o `idBiblioteca`) | `marcaCambio` | **Muy alta** | `GetItem` `<PK del recurso> / MARCA`, `ProjectionExpression = marcaCambio`, **strongly consistent** |

One `AP29` call serves all four resources — the shape is identical, only
the partition key changes. **Strongly consistent, not eventually
consistent**, despite costing 1 RCU instead of 0.5 on an item this small:
an eventually-consistent read can return a marker one write behind, which
breaks the interaction with optimistic client-side updates — a user
writes, gets back the new marker, and the very next poll reads a replica
still on the old one, refetches, and can clobber what they just saw on
screen with a payload that may not even contain their own write yet.

**The write side has no standalone access pattern.** `marcaCambio`'s bump
is always the second leg of the `TransactWriteItems` that performs the
data write it marks — see §1.1 for the atomicity rule, and each amended
row in §4.2–§4.5 for exactly which write it rides on. A poll implementation
needs nothing beyond `AP29` and the resource's own existing read (`AP8`/
`AP9`, `AP14`, `AP18`, `AP22`): read the marker, compare, fetch the
payload only on a mismatch.

**Where `AP29` is consumed:** the `api` Lambda's conditional-GET handling
(the actual `If-None-Match`/`304` mechanics are the REST contract's job —
`docs/rest_api_contract.md` §6, `ETag`/`If-None-Match` with the
`marcaCambio` value; `AP29` only supplies the comparison value).

---

## 5. Concurrency and correctness

The five places where a naive implementation is wrong.

### 5.1 Username uniqueness is enforced by the write, not by a check

`FR-AUTH-17` uniqueness is **not** a read-then-write validation — that is a
TOCTOU, and two admins racing would both see a name free. Write
`NombreIDUsuario` in the **same `TransactWriteItems`** as `DatosUsuario`, with
`attribute_not_exists(SK)` on the reservation. The condition *is* the check, so
there is no window.

The "unknown user" placeholder name is reserved by seeding its reservation item
at deploy time, which makes it permanently uncreatable (`FR-AUTH-17`).

**The seeded account's `idUsuario` is exactly `unknown-user`.** Decided at
feature 5's spec gate on 2026-08-24 (`specs/week_plan_model/design.md` §9, gate
question 1). `planner_core.domain.candidate.UNKNOWN_USER_ID` carries the same
literal, and `resolve_author` compares against it: if the seeded account and the
domain constant disagree, a removed author resolves to nothing instead of to the
placeholder and `FR-SUM-03` silently breaks. **Feature 15 does not get to pick
this value** — it is fixed here. Note the two are different things: the reserved
*name* is the es-ES `usuario desconocido`; the *id* is the ASCII `unknown-user`.

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

### 5.5 The change marker must be bumped atomically with its data, and read before the payload

⚠ **Two ordering traps, both silent and both permanent** (`G-88`,
`FR-RT-01`/`-03`). Full reasoning in §1.1/§4.7; the two failure shapes:

- **Write side.** `marcaCambio` bumped as a separate call, not the same
  `TransactWriteItems` as the data write — a crash between the two leaves
  the marker stale, and every polling client misses that change forever,
  until some unrelated later write happens to bump it.
- **Read side.** On a changed poll, reading the payload before the marker
  returns a marker newer than the body actually delivered. The client
  stores that marker, matches it on every subsequent poll, and never
  refetches the gap. Reading the marker **first** bounds the failure to at
  most one redundant refetch next interval, which converges — the
  asymmetry is why this ordering is not optional.

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
| **`USUARIOS`, `BIBLIOTECA#…`, `COMPRA#…`, `GRUPOREGLAS#…` are single-value partitions — isn't that a hot-partition risk?** | **This is the one choice a reviewer will question on sight.** It does not bite here: ≤10 users, `Baja`–`Media` writes, partitions that stay small indefinitely, against a ~3000 RCU / 1000 WCU per-partition ceiling. The alternatives are worse in a single-table design — a `Scan` sweeps every week, recipe and shopping item, and a GSI with a constant partition key has the *identical* cardinality property plus a full index copy. The ids are kept (rather than collapsed to literals) so a future multi-group model is a prefix change, not a key-schema rewrite. **Polling's `AP29` (`G-88`) adds the highest-frequency read in the whole catalogue to these same partitions** — even at an aggressive 3-second active interval across 10 users and all four resources, that is roughly one `AP29` `GetItem` per second per partition, nowhere near the ceiling above. |
| **Add a thin index item so AP14 / AP8 read less?** | **Not now.** Measured: recipes are ~2–4KB, so the 1MB Query page holds roughly 250–500 — years of household cooking. AP8 does read full recipe content it does not return (1MB applies *before* projection). Recorded so it is not rediscovered as a surprise, not so it is fixed. |
| **Isn't `MarcaCambio` (`G-88`) exactly the "thin index item" rejected above?** | **No — different problem, no contradiction.** The rejected item above would have *duplicated recipe content* to answer `AP14`/`AP8` with less data per read — it carries staleness risk and needs fan-out maintenance the moment the duplicated content changes. `MarcaCambio` duplicates no content; it is written by the same transaction as the change it marks, so it cannot go stale relative to what it describes, and it exists to avoid a full `AP8`/`AP14` read *at all* on an unchanged poll, not to make that read itself cheaper. |

---

## 8. Verified constraints

| Check | Result |
|---|---|
| Item size vs the 400KB limit | ✅ Largest is `DatosPlatoSemana` / `DatosPlatoBiblioteca` at ~2–4KB |
| 1MB Query page | ✅ A week is ~42 candidate items; the library ~250–500 recipes |
| Item-collection 10GB limit | ✅ Not applicable — that limit exists only for tables with an LSI, and there are none |
| TTL configured on one attribute name | ✅ `ttl` on `DatosPeticionIA` and `LockLista` only — `MarcaCambio` carries no `ttl` |
| Attribute naming vs the patterns | ✅ Every stored name agrees with every pattern that reads it |
| Write/read symmetry | ✅ Every stored attribute has a pattern that writes it; every returned attribute is stored, key-derived, or resolved by an explicit §6 rule |
| Scans | ✅ None |
| Secondary indexes | ✅ None |
| `MarcaCambio` item size | ✅ One number, well under any limit |
| Every partition sharing `MARCA` has an amended key-condition scope | ✅ `SEMANA#` (`AP8`/`AP9`), `BIBLIOTECA#` (`AP14`), `GRUPOREGLAS#` (`AP22`) amended; `COMPRA#` (`AP18`/`AP21`) already scoped, needs nothing (§3) |

---

## 9. Out of scope — parked by decision, not overlooked

Do not report these as gaps.

| Area | Status |
|---|---|
| **Archive** (`FR-ARCH-01`…`-04`) | Parked, MVP scope. Reading a past week *is* AP8 pointed at an older `idSemana`, and read-only needs no stored flag — a week is closed iff its id sorts before the computed current week. ⚠ But `FR-ARCH-04`'s reverse-chronological browse is **not** free: `idSemana` is in the **partition** key and DynamoDB cannot list or sort partition keys. Unparking costs ids generated backwards arithmetically, or an index. The `FR-ARCH-02` shopping-list snapshot has no item type and parks with it. |
| **Real-time** (`FR-RT-01`…`-03`) | **Resolved by `G-88` (2026-08-27, human-approved): adaptive polling with a conditional-GET version marker.** The pre-decision note above was half right: reconnect resynchronisation genuinely is re-calling existing reads (§4.7, no new mechanism needed for `FR-RT-03`), but the claim of "no new read patterns" did not survive contact with a real transport choice — polling added `AP29` and amended three existing whole-partition reads (§3, §4.2–§4.5). The "fan-out obligation on existing writes" became one marker item (`MarcaCambio`) bumped inside each write's own transaction (§1.1, §5.5) — not a fan-out to other clients, since polling clients pull rather than being pushed to. |
| **Sessions** (`FR-AUTH-09`, `-11`, `-14`, `-16`) | **Resolved by `G-87` (2026-08-27, human-approved): no dedicated item type.** Authentication is stateless — a token carries `user_id` + `issued_at`, signed, and expires 30 days after issuance with no database access (`FR-AUTH-16`, amended). "Invalidate all sessions of an account" (`FR-AUTH-11`, `-14`) and voluntary logout (`FR-AUTH-09`) are both satisfied by `DatosUsuario.validoDesde` (§1.1, AP4, AP28) — one revocation-marker attribute, not a session table. Removal needs no write at all — deleting the account already fails every token lookup. |
| **Cold storage** (`FR-ARCH-03`) | Parked, MVP scope — reaffirmed 2026-08-30 when P6 was decided. Export needs a whole-week full-content read that no pattern provides. Unpark needs an explicit owner decision. |

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
table) and **§1.1** the P7 decision (React/Vite/Vitest, 2026-08-17). **P2–P6
are all decided** as of 2026-08-30 (§1.2.3–§1.2.7); no architecture item
remains pending.

---

## Working with the access-pattern workbook

Moved here from `AGENTS.md` §3.1 on 2026-08-24: it is needed rarely and that
file is loaded every session.

- **Key formats belong in §2 of this document, never in the spreadsheet** (D28).
  The workbook is the catalogue plus key *templates*; formats, folding rules and
  id-generation constraints do not belong in it — no column, no note, no example.
- **Re-read the workbook from disk at the start of any turn that touches it.**
  The owner edits and saves mid-conversation. Unzip **inside the scratchpad with
  an absolute path** — a `$TMPDIR` fallback once scattered `xl/` and
  `[Content_Types].xml` across the repo root — then parse
  `xl/worksheets/sheet1.xml` against `xl/sharedStrings.xml` with Node. Match
  `<si\s*/>|<si>([\s\S]*?)</si>`, use a lazy attribute group, and print with
  explicit column letters: a naive regex silently misaligns the table and
  produces a plausible but wrong reading.
- **Row numbers and `AP` numbers are positions, not identifiers.** Rows get
  inserted. Refer to patterns by title and item types by name.
