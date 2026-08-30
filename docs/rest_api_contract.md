# REST API contract for the `api` Lambda

> **Status: DECIDED 2026-08-30.** Authoritative for the `api` Lambda.
> `docs/architecture.md` §1.2.5 records the load-bearing shape; this document is
> the full contract. The 13 gate questions are resolved in §7.
>
> **Scope.** Resources, verbs, payload shapes, error format, plus the two
> sub-decisions explicitly deferred to P5: session-token transport
> (`architecture.md` §1.2.3 last paragraph) and version-marker transport
> (`architecture.md` §1.2.4 last paragraph / `G-88`'s boundary note).
>
> **Sources.** Every endpoint below traces to an access pattern in
> `docs/data_model.md` §4 and/or an `FR-*` in `docs/requirements.md`. Access
> patterns are named by title, with `AP<n>` as a secondary reference only
> (`data_model.md` § *Working with the access-pattern workbook*).
>
> **P4 did not block this.** P4 is decided — AWS Bedrock + Claude — and the AI
> HTTP surface below is unchanged: submit a generation request, poll for the
> result. The `api`→`ai` hop is a standard SQS queue (§7 Q12, recorded in
> `architecture.md` §1.2 / §1.2.6), so the REST surface stays provider-agnostic.

---

## 1. Resource model

Base path **`/v1`**. The API Gateway stage name is deployment topology (P6) and
is deliberately *not* the version — a stage rename must not be an API version
bump.

| Resource | Path template | Backing patterns |
|---|---|---|
| Session | `/v1/session` | Login, Cerrar sesión (`AP6`, `AP28`) |
| Session password | `/v1/session/password` | Establecer contraseña (`AP7`) |
| Accounts | `/v1/users`, `/v1/users/{userId}` | `AP1`–`AP5` |
| Live-week calendar | `/v1/live-weeks` | none — computed (`FR-MENU-02`) |
| Week | `/v1/weeks/{weekId}` | Obtener semana (`AP8`); `AP9` (+ ingredientes) is internal-only, §7 Q13 |
| Week summary | `/v1/weeks/{weekId}/summary` | same reads, definitive-only projection |
| Slot definitive | `/v1/weeks/{weekId}/days/{day}/slots/{slot}/definitive` | Establecer/Desasignar comida definitiva (`AP11`) |
| Candidates | `…/slots/{slot}/candidates`, `…/candidates/{candidateId}` | `AP10`, `AP12`, `AP13` |
| Library | `/v1/library/recipes`, `/v1/library/recipes/{recipeId}` | `AP14`–`AP17` |
| Rules | `/v1/rules`, `/v1/rules/{ruleId}` | `AP22` (list), `AP23`/`AP24` (per-rule) |
| Shopping list | `/v1/shopping-list` | Obtener lista de la compra (`AP18`) |
| Shopping items | `/v1/shopping-list/items`, `…/items/{itemId}` | `AP19`, `AP20` |
| Checked items | `/v1/shopping-list/checked-items` | Eliminar elementos marcados (`AP21`) |
| Re-sync action | `/v1/shopping-list/resync` | composition over `AP18` + `AP19` (`FR-SHOP-06`) |
| Generation requests | `/v1/generations`, `/v1/generations/{generationId}` | `AP25`–`AP27` |

**Path parameter formats** (all from `data_model.md` §2 — the formats exist
nowhere else):

| Param | Format | Note |
|---|---|---|
| `weekId` | `<isoYear>-W<ww>`, e.g. `2026-W33` | ISO week-numbering year, zero-padded week. Never the calendar year. |
| `day` | `1`–`7`, Monday = 1 | `numeroDia` = `date.isocalendar()[2]`, not `date.weekday()`. |
| `slot` | `1` = lunch, `2` = dinner | `numeroComida`. |
| `candidateId` | server-minted ULID/KSUID | `idPlato` **is** the in-slot ordering; a client-supplied id is rejected. |
| `recipeId`, `itemId`, `userId` | opaque server-minted | |
| `generationId` | deterministic hash of the request | `idPeticionIA`; server-computed, never client-supplied (`FR-AI-08`). |

**The client never computes a week id.** `GET /v1/live-weeks` returns both live
weeks with their Monday–Sunday ranges; every week-scoped path then carries an
explicit `weekId`. This keeps ISO-week maths in `planner_core`
(`architecture.md` §1.1 "no business logic in the client") and gives the polling
hook a stable target that only changes when the server says so.

*Rejected:* `/v1/weeks/current` and `/weeks/next` aliases. The polling target
would silently change meaning at rollover — the same URI returning a different
week — which is exactly the ambiguity `FR-UX-06` forbids in the UI.

**Not exposed, by decision:**

- **Reverse-chronological archive browse** (`FR-ARCH-04`) — parked in
  `data_model.md` §9: `idSemana` is a partition key and DynamoDB cannot list or
  sort partition keys. No endpoint.
- **Cold storage / restore** (`FR-ARCH-03`) — parked, MVP scope (`data_model.md`
  §9; reaffirmed 2026-08-30). No endpoint, no `restoring` state in any payload.
- **Week rollover** (`FR-MENU-06`, `-08`) — a job, not a request. Triggered by a
  scheduled EventBridge rule invoking the `api` Lambda (§7 Q8).
- **Obtener semana + ingredientes** (`AP9`) — internal-only (§7 Q13). Its one
  consumer is the re-sync composition (`FR-SHOP-06`), which calls the repository
  method directly inside the Lambda. No `?include=ingredients` on the public
  surface.
- **Obtener usuario por nombre** (`AP3`) — internal to the login path only; the
  admin screen filters ≤10 rows from `AP1` client-side.
- **Obtener marca de cambio** (`AP29`) — has no endpoint of its own by design.
  It is the short-circuit inside the four pollable GETs (§6).

**No pagination anywhere.** Verified sizes (`data_model.md` §7/§8): library
~250–500 recipes in one 1 MB `Query` page, a week ~42 items, users ≤10,
household shopping list. Adding cursors now would be machinery for a bound the
data model already proves is not reached.

**No content negotiation.** `application/json; charset=utf-8` in and out. The
locale is a constant, not a runtime setting (`conventions.md` § *Castilian
Spanish*), so `Accept-Language` is ignored.

---

## 2. Endpoint table

**Poll** column: ✅ = conditional-GET pollable, backed by a `MarcaCambio`
partition (`data_model.md` §4.7). The four pollable resources are exactly the
four `FR-RT-01` names — weeks, library, shopping list, rules. Nothing else
carries an `ETag`.

### Session and accounts

| Method + path | Pattern / `FR-*` | Poll | Semantics |
|---|---|---|---|
| `POST /v1/session` | Login (`AP6`) · `FR-AUTH-02` | — | Username + password → session token; body carries `role` and `passwordResetRequired`. |
| `DELETE /v1/session` | Cerrar sesión (`AP28`) · `FR-AUTH-09` | — | Advances `validoDesde`, revoking every token for the account on every device. |
| `PUT /v1/session/password` | Establecer contraseña (`AP7`) · `FR-AUTH-10`, `-15` | — | The mandatory set-password step. Deliberately does **not** touch `validoDesde` (`data_model.md` §1.1). |
| `GET /v1/users` | Pantalla admin - Listar usuarios (`AP1`) · `FR-AUTH-12` | — | Admin only. |
| `GET /v1/users/{userId}` | Obtener usuario (`AP2`) · `FR-AUTH-12` | — | Admin only. |
| `POST /v1/users` | Pantalla admin - Crear o editar usuario (`AP4`) · `FR-AUTH-03`, `-11` | — | Create. Admin-assigned password is always temporary. |
| `PATCH /v1/users/{userId}` | same (`AP4`) · `FR-AUTH-05`, `-11`, `-17` | — | Rename and/or reset password. A reset advances `validoDesde`. |
| `DELETE /v1/users/{userId}` | Pantalla admin - Eliminar usuario (`AP5`) · `FR-AUTH-13`, `-18` | — | User accounts only; admin accounts are not removable. |

### Weeks

| Method + path | Pattern / `FR-*` | Poll | Semantics |
|---|---|---|---|
| `GET /v1/live-weeks` | — · `FR-MENU-01`, `-02`, `FR-UX-06` | — | `{today, current:{weekId,monday,sunday}, next:{…}}`. |
| `GET /v1/weeks/{weekId}` | Obtener semana (`AP8`) · `FR-MENU-01`, `-03`, `FR-CAND-04`, `FR-ARCH-01` | ✅ | Whole week: 7 days × 2 slots, candidates + validated definitive pointer. A past `weekId` is the archive read. |
| `GET /v1/weeks/{weekId}/summary` | `AP8` projection · `FR-SUM-01`, `-03` | ✅ | Definitive meals only, read-only view. No ingredients (§7 Q13); recipe detail is one click away via `FR-MENU-05`. No new access pattern. |
| `GET …/candidates/{candidateId}` | Obtener comida - Semana (`AP10`) · `FR-MENU-04`, `-05` | — | Full recipe detail of one candidate. Returns no `definitiveId` — nothing to validate (`data_model.md` §5.4). |
| `POST …/slots/{slot}/candidates` | Editar o añadir comida (`AP13`) · `FR-CAND-01`, `-02` | — | The three-way authoring flow (§3.1). Returns `duplicateWarning`, never an error. |
| `PUT …/candidates/{candidateId}` | same (`AP13`) · `FR-CAND-01`, `-05` | — | Edit in place. A definitive meal edits like any candidate (`G-67`). |
| `DELETE …/candidates/{candidateId}` | Eliminar comida (`AP12`) · `FR-CAND-01`, `FR-UX-04` | — | |
| `PUT …/slots/{slot}/definitive` | Establecer comida definitiva (`AP11`) · `FR-CAND-05`, `FR-MENU-03` | — | Body `{"candidateId": …}`. At most one per slot is a primary-key property, not a check. |
| `DELETE …/slots/{slot}/definitive` | Desasignar (`AP11`) · `FR-CAND-08` | — | Clears the slot; all meals return to candidate status. |

`AP9` (Obtener semana + ingredientes) has **no public endpoint** (§7 Q13). The
re-sync composition is its only consumer and calls `WeekRepository` directly
inside the Lambda.

### Library

| Method + path | Pattern / `FR-*` | Poll | Semantics |
|---|---|---|---|
| `GET /v1/library/recipes` | Obtener biblioteca (`AP14`) · `FR-LIB-01`, `-04` | ✅ | Optional `?name=` / `?category=`, applied in the Lambda (`data_model.md` §7). The polling hook requests the unfiltered URI. |
| `GET /v1/library/recipes/{recipeId}` | Obtener comida de la biblioteca (`AP15`) · `FR-MENU-04`, `-05` | — | |
| `POST /v1/library/recipes` | Añadir o editar comida (`AP16`) · `FR-LIB-02`, `FR-CAND-03`, `FR-CAND-06` | — | Three sources: from scratch, from a generation preview, or from a week meal's snapshot (`FR-CAND-06` — always a **new** entry). Returns `duplicateWarning`. |
| `PUT /v1/library/recipes/{recipeId}` | same (`AP16`) · `FR-LIB-02` | — | Edits never mutate existing week snapshots (`FR-CAND-07`). |
| `DELETE /v1/library/recipes/{recipeId}` | Eliminar comida (`AP17`) · `FR-LIB-02`, `FR-RULE-07` | — | Two-step when pin rules reference it (§3.4). |

### Rules

| Method + path | Pattern / `FR-*` | Poll | Semantics |
|---|---|---|---|
| `GET /v1/rules` | Obtener reglas (`AP22`) · `FR-RULE-01`, `-02` | ✅ | Pin rules carry `recipeName`, resolved at read time from the library — never stored (`data_model.md` §6). |
| `PUT /v1/rules/{ruleId}` | Añadir o editar regla (`AP23`) · `FR-RULE-03`, `-06`, `-07` | — | Single-item `PutItem` (`AP23`), giving genuine per-rule last-write-wins. Satisfiability (`FR-RULE-07`) is re-validated whole-set in the adapter on each write: load the full set (`AP22`), apply the candidate change in memory, check, then commit the one item. See §7 Q5. |
| `DELETE /v1/rules/{ruleId}` | Eliminar regla (`AP24`) · `FR-RULE-03`, `-06`, `-07` | — | Single-item `DeleteItem` (`AP24`). Whole-set satisfiability re-validated as above. |

### Shopping list

| Method + path | Pattern / `FR-*` | Poll | Semantics |
|---|---|---|---|
| `GET /v1/shopping-list` | Obtener lista de la compra (`AP18`) · `FR-SHOP-01`, `-08` | ✅ | Flat list; the two-section display (`FR-SHOP-08`) is presentation. |
| `POST /v1/shopping-list/items` | Añadir o editar elemento (`AP19`) · `FR-SHOP-02` | — | |
| `PUT /v1/shopping-list/items/{itemId}` | same (`AP19`) · `FR-SHOP-02` | — | |
| `PATCH /v1/shopping-list/items/{itemId}` | same (`AP19`) · `FR-SHOP-07` | — | `{"checked": true|false}` — the check/uncheck path. |
| `DELETE /v1/shopping-list/items/{itemId}` | Eliminar elemento (`AP20`) · `FR-SHOP-02`, `FR-UX-04` | — | |
| `DELETE /v1/shopping-list/checked-items` | Eliminar elementos marcados (`AP21`) · `FR-SHOP-09` | — | Idempotent. With nothing checked it is a no-op that does **not** bump the marker (feature 18 acceptance) — the response echoes the unchanged `ETag`. |
| `POST /v1/shopping-list/resync` | `AP18` + `AP19` · `FR-SHOP-03`, `-05`, `-06`, `-10` | — | The button. Serialized by the `FR-SHOP-10` lock; `409` while held (§3.3). |

### AI generation — HTTP shape

| Method + path | Pattern / `FR-*` | Poll | Semantics |
|---|---|---|---|
| `POST /v1/generations` | Añadir o editar petición IA (`AP25`) · `FR-AI-01`, `-02`, `-03`, `-05`, `-08`, `-09` | — | Submit. `202 Accepted` on a fresh request, `200 OK` with the stored result on an idempotent hit. `409` if the target slot already has a `pending`/`running` generation (`FR-AI-09` per-slot concurrency). `attempt` is server-authoritative — the count of *completed* generations for the slot, folded into `idPeticionIA` (§7 Q3), never a client field. Both are feature 17 spec inputs. |
| `GET /v1/generations/{generationId}` | Obtener petición IA (`AP26`) · `FR-AI-10`, `-12` | — | Status + result. Per-slot status for whole-week runs. Short-interval poll, **not** conditional-GET pollable (no `MarcaCambio` on `PETICIONIA#`). |
| `DELETE /v1/generations/{generationId}` | Eliminar petición IA (`AP27`) · `FR-AI-10` | — | Discards a preview and its idempotency record. |

**All 29 access patterns are accounted for:** `AP1`–`AP2`, `AP4`–`AP8`,
`AP10`–`AP28` above (`AP23`/`AP24` are the per-rule `PUT`/`DELETE`); `AP3`
internal to login; `AP9` internal-only — the re-sync composition calls the
repository directly (§7 Q13); `AP29` is the conditional-GET short-circuit (§6).

---

## 3. Payload shapes

### 3.0 Shape strategy

1. **JSON keys are English `camelCase`.** `conventions.md` puts identifiers in
   English and reserves es-ES for user-facing *strings*. Persisted attribute
   names are Spanish and are mapped at the adapter boundary (`data_model.md`
   §1); making the wire Spanish too would mean two mappings in opposite
   directions inside one Lambda. See §7 Q6.
2. **All ids are server-minted.** A create body carrying an `id` is rejected
   `400`. This is load-bearing for `idPlato`, which *is* the in-slot ordering
   (`data_model.md` §2) — a client-chosen id shuffles the candidate list.
3. **`author` is never in a request body.** `añadidoPor` comes from the
   authenticated token, always.
4. **Read-time-resolved fields are response-only.** `recipeName` on a pin rule,
   the `"unknown user"` placeholder for a removed author. Sending one back on a
   write is a `400` (`data_model.md` §6 — do not denormalize these).
5. **Mutations return the affected entity, not the whole resource**, plus the
   resource's new marker as an `ETag` (§6).
6. **A duplicate is a warning, never a rejection** (`architecture.md` §4
   invariant 3): `201` with `"duplicateWarning": true`.
7. **The shopping item has four fields and a checkbox.** No `auto`, no `edited`,
   no `weeks`, no `qtyChanged` — all removed by `G-72`/`G-73`/`G-77`
   (`frontend_prototype.md` §4.4). The prototype's shape is the superseded one.
8. **A recipe has no `cuisine`, `diff` or `kcal`** (`FR-LIB-03`; prototype
   divergence §4.1). `servings` and `estimatedTime` are freeform and purely
   informational (`G-85`) — no validation, no downstream logic.

### 3.1 The three-way authoring flow (`FR-CAND-02`, `FR-CAND-03`)

One endpoint, a discriminated body. Only `manual` carries client-supplied recipe
content; the other two are server-side copies, which is both cheaper (no extra
round-trip) and non-tamperable.

```jsonc
// POST /v1/weeks/2026-W33/days/3/slots/1/candidates
{ "source": "library",    "recipeId": "01J8…" }        // (a) FR-CAND-02a — server copies AP15 content
{ "source": "generation", "generationId": "9f2c…" }    // (c) FR-AI-10 — server copies the accepted preview
{ "source": "manual",                                  // (b) from scratch
  "recipe": {
    "name": "Lentejas al curry",
    "category": "legumbres",
    "servings": 4,
    "estimatedTime": "45 min",
    "ingredients": [ { "name": "lentejas", "quantity": 300, "unit": "g" } ],
    "tools": ["olla"],
    "procedure": ["Sofreír la cebolla.", "Añadir las lentejas."]
  } }
```

```jsonc
// 201 Created,  ETag: "18",  Location: …/candidates/01J9…
{ "candidate": { "id": "01J9…", "author": { "userId": "u-3", "displayName": "Marta" },
                 "recipe": { /* the snapshot, FR-CAND-07 */ } },
  "duplicateWarning": true }
```

A library pick copies into a **new** `idPlato` — the week item is a snapshot,
not a reference (`data_model.md` §2, `FR-CAND-07`). `POST /v1/library/recipes`
takes the mirror-image body, with `"source": "weekCandidate"` carrying
`weekId`/`day`/`slot`/`candidateId` for `FR-CAND-06`, and no `"source":
"library"` variant (the target *is* the library, `FR-CAND-03`).

### 3.2 Candidate selection (`AP11`, `FR-CAND-05`, `FR-CAND-08`)

```jsonc
// PUT …/slots/1/definitive          → 200, ETag: "19"
{ "candidateId": "01J9…" }
// DELETE …/slots/1/definitive       → 204, ETag: "20"   (FR-CAND-08)
```

`404 CANDIDATE_NOT_FOUND` if the id is not a candidate of that slot. The week
read validates `idPlatoDefinitivo` against the meals in the same response and
reports *no definitive* when it dangles (`data_model.md` §5.4) — a dangling
pointer is never an error to the client.

### 3.3 Re-sync (`FR-SHOP-03`, `-05`, `-06`, `-10`)

```jsonc
// POST /v1/shopping-list/resync     (no body)
// 200 OK,  ETag: "42"
{ "items": [ { "id": "s-1", "name": "arroz", "quantity": 500, "unit": "g", "checked": true },
             { "id": "s-9", "name": "arroz", "quantity": 300, "unit": "g", "checked": false } ] }
```

The full list comes back because re-sync can touch many rows at once. The
example is `G-77`'s canonical case: 500 g bought, requirement risen to 800 g →
the checked row is **untouched** and a new unchecked row carries the 300 g
remainder. Scope is the current week from today onward plus the whole next week
(`FR-SHOP-05`), computed server-side.

`409 SHOPPING_LIST_LOCK_HELD` while another press holds the `FR-SHOP-10` lock.
The es-ES message tells the user to retry; the client does not auto-retry, since
a second press is by definition a duplicate of the one already running.

Feature 26 collapses the marker bump to one per re-sync (`data_model.md` §4.4 /
§5.3), so the returned `ETag` is a single post-resync value. Until then the
response still carries the final marker; only the *number* of intermediate
"changed" polls other clients see differs.

### 3.4 Library delete with a pin cascade (`FR-RULE-07`)

Two steps, safe by default:

```jsonc
// DELETE /v1/library/recipes/01J8…                  → 409  application/problem+json
{ "type": "urn:planner:pin-rules-affected", "title": "Pin rules affected",
  "status": 409, "detail": "Hay reglas que fijan esta receta…",
  "code": "PIN_RULES_AFFECTED",
  "details": { "pins": [ { "day": 7, "slot": 1 } ] } }

// DELETE /v1/library/recipes/01J8…?confirmCascade=true   → 204
```

The confirmed call deletes the recipe and the affected pins. Matching pins is on
`idPlato`, never on the name — `FR-CAND-06` allows two library recipes to share
one (`data_model.md` §4.5).

### 3.5 Whole-week generation (`FR-AI-03`, `-05`, `-11`, `-12`)

```jsonc
// POST /v1/generations
{ "type": "week",
  "weekId": "2026-W34",
  "mode": "mix",                       // library_only | ai_only | mix
                                       // no `attempt` field — server-authoritative, §7 Q3
  "ruleOverride": {                    // FR-RULE-05, per-run, never persisted
    "categoryCounts": [ { "category": "pescado", "count": 2 } ],
    "disabledDays": [6] } }
```

```jsonc
// 202 Accepted,  Location: /v1/generations/9f2c…
{ "generationId": "9f2c…", "status": "pending",
  "targets": {                                    // resolved deterministically before enqueueing
    "openSlots":   [ { "day": 1, "slot": 1 }, … ],
    "pinnedSlots": [ { "day": 7, "slot": 1, "recipeId": "01J8…" } ],
    "skippedPins": [ { "day": 3, "slot": 2, "recipeId": "01J7…" } ] } }
```

`skippedPins` is `FR-AI-11`'s "an existing definitive outranks a pin, and the
skip is reported, never applied silently" — it is in the **submit** response
because the resolution is deterministic and needs no model call.

**`attempt` is not a request field** (§7 Q3). The server derives it from the
count of *completed* generations for the slot and folds it into `idPeticionIA`
(`FR-AI-08`), so a retry (same `attempt`) dedupes, a regenerate (next `attempt`)
misses, and two fast clicks compute the same value and dedupe. A generation
request for a slot that already holds a `pending`/`running` generation returns
`409` (`FR-AI-09` per-slot concurrency). Both belong in feature 17's spec.

```jsonc
// GET /v1/generations/9f2c…          → 200
{ "generationId": "9f2c…", "status": "running",
  "slots": [ { "day": 1, "slot": 1, "status": "done" },
             { "day": 1, "slot": 2, "status": "failed",
               "error": { "code": "AI_SLOT_FAILED", "message": "…" } } ] }
```

Per-slot status and per-slot failure satisfy `FR-AI-12`; partial results are
kept (`FR-AI-09`). Whole-week results are **written by the `ai` Lambda through
`WeekRepository`**, never returned in this payload (feature 17's recorded
constraint) — so the week's `MarcaCambio` bumps and every client's ordinary poll
picks the candidates up. Single-recipe results are the opposite: a **preview**
carried in `result`, persisted nowhere else (`FR-AI-10`, `data_model.md` §4.6),
and saved only when the user POSTs it as a candidate or library recipe (§3.1).

`GET /v1/generations/{id}` is polled on its own short interval by the AI
progress UI. It is deliberately **not** conditional-GET pollable — `PETICIONIA#`
carries no `MarcaCambio` and is not one of `FR-RT-01`'s four resources.

---

## 4. Error format

The envelope is RFC 9457 `application/problem+json`, adopted upfront (owner,
2026-08-30 — §7 Q10).

```jsonc
{ "type":   "urn:planner:session-expired",                      // stable URN, non-dereferenceable — not required to be a URL
  "title":  "Session expired",                                  // short generic English phrase, one per code
  "status": 401,                                                // duplicates the HTTP status
  "detail": "La sesión ha caducado. Vuelve a iniciar sesión.",  // verbatim from planner_core.messages (es-ES)
  "code":   "SESSION_EXPIRED",                                  // extension member — what the SPA branches on
  "details": { } }                                              // extension member — optional, structured, code-specific
```

Rules:

- **`code` is what the SPA branches on.** SCREAMING_SNAKE, derived from the
  domain exception class name, stable across releases. It is a `problem+json`
  **extension member**, not part of the standard vocabulary.
- **`detail` is copied from `planner_core.messages`, never composed in the
  handler.** `FR-UX-03` requires every user-facing string in es-ES, and
  `conventions.md` requires every one of them to live in the one messages
  module. A handler that formats its own message defeats both.
- **`title` is a short, generic English phrase, one per `code`** — a stable
  label, not a user-facing string (that is `detail`'s job).
- **`status` duplicates the HTTP status** for clients that only read the body.
- **`type` is a non-dereferenceable URN** (`urn:planner:<slug>`); it is not
  required to resolve to a real URL.
- **`details` exists only where the SPA needs structure** — the affected pins on
  a cascade, the conflicting rules on an unsatisfiable set. Never a stack trace
  (`conventions.md` § *Error handling*). Also an extension member.

Status convention: **`400`** = malformed request (bad JSON, missing field, bad
path parameter). **`422`** = well-formed but rejected by a domain rule.

| Domain exception | Status | `code` |
|---|---|---|
| `InvalidCredentials` | 401 | `INVALID_CREDENTIALS` — generic, never reveals whether the username exists (`NFR-SEC-04`) |
| `SessionExpired` | 401 | `SESSION_EXPIRED` — raised uniformly for bad signature, expiry, revocation or removed account; the caller does not get to distinguish them |
| `Forbidden` | 403 | `FORBIDDEN` — the `FR-AUTH-05`/`-06` role split |
| `PasswordResetPending` | 403 | `PASSWORD_RESET_PENDING` — `FR-AUTH-10`; the SPA routes to the set-password screen |
| `AccountNotFound` | 404 | `ACCOUNT_NOT_FOUND` |
| `RecipeNotFound` | 404 | `RECIPE_NOT_FOUND` |
| `CandidateNotFound` | 404 | `CANDIDATE_NOT_FOUND` |
| `ShoppingItemNotFound` | 404 | `SHOPPING_ITEM_NOT_FOUND` |
| `UsernameAlreadyTaken` | 409 | `USERNAME_ALREADY_TAKEN` (`FR-AUTH-17`) |
| `SetPasswordNotPending` | 409 | `SET_PASSWORD_NOT_PENDING` |
| `ShoppingListLockHeld` | 409 | `SHOPPING_LIST_LOCK_HELD` (`FR-SHOP-10`) |
| *(no exception — handler check)* | 409 | `PIN_RULES_AFFECTED` (§3.4), `WEEK_ARCHIVED` (§7 Q11); the per-slot in-flight `409` (§3.5, `FR-AI-09`) — code named in feature 17's spec |
| `UsernameReserved` | 422 | `USERNAME_RESERVED` (`FR-AUTH-17` placeholder) |
| `PasswordTooShort` | 422 | `PASSWORD_TOO_SHORT` (`FR-AUTH-15`) |
| `UnknownUnit` | 422 | `UNKNOWN_UNIT` (`FR-LIB-05`) |
| `UnknownIngredientCategory` | 422 | `UNKNOWN_INGREDIENT_CATEGORY` (`FR-RULE-04`) |
| `InvalidWeekday` | 422 | `INVALID_WEEKDAY` |
| `UnsatisfiableRuleSet` | 422 | `UNSATISFIABLE_RULE_SET`, `details.conflicts` (`FR-RULE-07`) |
| `InvalidIsoWeek` | 400 in a path, 422 in a body | `INVALID_ISO_WEEK` |
| `NaiveInstant`, `InsufficientNewIds`, `UnknownPromptVersion` | 500 | `INTERNAL_ERROR` — server-side faults, not user input; logged, never explained |
| any unmapped `PlannerError` | 500 | `INTERNAL_ERROR` |

**Not errors.** A duplicate name (`FR-CAND-01`, `FR-CAND-06`) is `201` +
`duplicateWarning`; a dangling `idPlatoDefinitivo` or `añadidoPor` is resolved at
read time (`data_model.md` §5.4). Turning either into a `4xx` would contradict
`architecture.md` §4 invariants 3 and 9.

**One gap this format cannot cover alone.** API Gateway's own 401/403 (from the
authorizer, from throttling) use *its* body shape, not `problem+json`. Matching
them needs API Gateway Gateway Response templates — a feature 21 infra detail,
flagged so the SPA is not written against a shape that has two variants in
production.

**Adopted upfront (owner, 2026-08-30).** RFC 9457's vocabulary (`type`, `title`,
`detail`, `instance`) buys interoperability this project has no consumer for —
one SPA, one server. It was adopted anyway because lock-in is low either way, so
skipping the later `code`→`type` / `message`→`detail` rename wins; and with §7
Q1 same-origin, the CORS friction the non-standard content type would otherwise
add is gone. The residual cost is the Gateway Response templates noted above.

---

## 5. Auth transport — **`HttpOnly` cookie**

### What is already decided

`G-87` (`architecture.md` §1.2.3, `gaps_and_resolutions.md` Part W): a signed
token carrying `user_id` + `issued_at`, flat 30-day expiry, no session table.
Verified against the code that already exists: `planner_core.ports.tokens`
(HMAC-SHA256 over `user_id|issued_at`) and
`planner_core.application.authentication.authenticate`.

⚠ **Correction to a claim that circulates in the briefs.** The *expiry* check is
free — `is_expired` needs only the token and the clock. The whole authenticated
request is **not** free: `authenticate()` calls `accounts.get_by_id(...)` to
read `credentials_valid_since` for the revocation check
(`domain/session_policy.is_revoked`), which is one `GetItem` (Obtener usuario,
`AP2`) **per authenticated request**. That is `G-87`'s design working as
intended — a read, not the per-request *write* the owner rejected — but any
"stateless, no DB access" wording in the P5 brief is half right and should not
survive into `architecture.md`.

### The two options

| | `Authorization: Bearer` | `HttpOnly` cookie |
|---|---|---|
| Token theft via XSS | Readable by any script; one XSS yields a 30-day token | Not readable by script |
| CSRF | Structurally impossible (a cross-site request cannot set the header) | Needs `SameSite`, or a CSRF token |
| Persistence across browser restarts | SPA must use `localStorage` (the XSS surface above) — `sessionStorage` would make `FR-AUTH-16`'s 30 days meaningless | `Max-Age=2592000`, free, mirrors `FR-AUTH-16` exactly |
| Cross-origin SPA↔API | Works unchanged | Needs same-site, or `SameSite=None` + CSRF token |
| API Gateway authorizer | `TOKEN` type, identity source `Authorization` | `REQUEST` type, identity source `Cookie` |
| Logout | Client must remember to drop it | `Set-Cookie … Max-Age=0` on the same response that advances `validoDesde` |

### The decision

**`Set-Cookie: session=<token>; HttpOnly; Secure; SameSite=Lax; Path=/;
Max-Age=2592000`.**

1. **There is no per-token revocation and no refresh token.** Revocation is
   account-level (`validoDesde`, `AP4`/`AP28`), so a stolen token is only killed
   by an admin reset or a logout that hits *every* device. That asymmetry makes
   token theft the dominant risk, and `HttpOnly` is the only control here that
   addresses it.
2. **`Max-Age` mirrors `FR-AUTH-16` with no client code.** The browser drops the
   cookie at 30 days; the server rejects it at 30 days. One rule, two enforcers.
3. **`SameSite=Lax` covers CSRF without a token**, on one condition this
   contract already meets: **no state-changing `GET`**. `Lax` attaches the
   cookie to cross-site *top-level GET navigations* only, and every mutation
   above is `POST`/`PUT`/`PATCH`/`DELETE` via `fetch`, which gets no cookie
   cross-site. Treat "no state-changing GET" as a contract invariant, not a
   coincidence — adding one would silently open CSRF.
4. **Logout becomes atomic on both sides**: `DELETE /v1/session` advances
   `validoDesde` (`AP28`) *and* clears the cookie in one response.

**The condition, met by decision.** `SameSite=Lax` requires the SPA and the API
to be **same-site**. Per §7 Q1 the owner ruled (a): `/v1/*` routes through the
same CloudFront distribution that serves the SPA, making them same-origin —
which also removes the CORS preflight on every poll.

### Wiring

- **`REQUEST`-type Lambda authorizer**, identity source `method.request.header.Cookie`.
- The authorizer runs `authenticate()` and passes `userId`, `role` and
  `passwordResetRequired` to the handler in the authorizer **context**, so the
  handler enforces `FR-AUTH-05`/`-06` and `FR-AUTH-10` without a second `AP2`
  read.
- **Authorizer result cache TTL is 0** (§7 Q2). `FR-AUTH-14` says removing a user
  invalidates sessions *immediately*; any TTL of *n* seconds makes that "within
  *n* seconds". At 2–10 users the per-request `AP2` read is free.
- Bearer is retained only as a break-glass fallback should same-origin routing
  ever be undone — the token, the domain code and every endpoint above are
  unchanged; only the authorizer's identity source and the SPA's storage differ.

*Rejected:* bearer with `localStorage` (reason 1 above); bearer with in-memory
storage only (loses the session on every reload, making a 30-day expiry
theatre); cookie with `SameSite=None` + a double-submit CSRF token (works
cross-site, but adds a token the MVP has no other need for — moot now that §7 Q1
landed on same-origin).

---

## 6. Marker transport — **`ETag` / `If-None-Match`**

### The mechanism

```
GET /v1/shopping-list
If-None-Match: "41"

→ 304 Not Modified          ETag: "41"      (no body)
→ 200 OK                    ETag: "42"      { "items": [ … ] }
```

The `ETag` value is `marcaCambio` — a counter incremented atomically inside the
same `TransactWriteItems` as the write it marks (`data_model.md` §1.1), read via
Obtener marca de cambio (`AP29`) with `ProjectionExpression = marcaCambio`,
**strongly consistent**. A strong (unquoted-`W/`) ETag is correct precisely
because the marker cannot go stale relative to the payload it describes.

**Ordering is not negotiable** (`data_model.md` §5.5, read side): read the
marker **first**, then the payload, and return the marker read *first*. The
reverse returns a marker newer than the body delivered; the client stores it,
matches it forever, and never refetches the gap. Reading first bounds the
failure to one redundant refetch next interval.

### Every response carries the marker, including mutations

`WeekRepository.save_slot`, `RecipeRepository.save`, `RuleRepository.save`,
`ShoppingListRepository.save_item` and friends already return the new version
(feature 18, done). Surface it as the `ETag` of the mutation response. That is
what makes the optimistic-update path in `data_model.md` §4.7 work: the writer
applies its own change locally, stores the returned marker, and its next poll
`304`s instead of refetching what it already has.

⚠ **A stale-marker trap the client must handle, and it belongs in this
contract.** If another user's write lands between the writer's read and its own
write, the marker the write returns is *ahead* of the writer's local state — it
already includes the other user's change. Storing it blindly means that change
is missed **permanently**. The counter makes the fix exact: **the client stores
the marker a mutation returns only when it equals the marker it held + 1;
otherwise it discards it and refetches.** `ADD marcaCambio 1` guarantees the
step is exactly one (`data_model.md` §1.1). Feature 26 owns implementing this.

The `+1` rule does not hold for operations that bump several times — whole-week
generation via repeated `AP13`, and re-sync until feature 26 collapses it
(`data_model.md` §4.2/§4.4). Both are server-side or asynchronous, so the client
refetches in those cases anyway; the rule only ever governs a client's own
single mutation.

### Client-held stale markers

| Client holds | Server has | Result |
|---|---|---|
| `"41"` | `41` | `304`, `ETag: "41"`. Client keeps its state. |
| `"41"` | `42` | `200` + full payload, `ETag: "42"`. |
| nothing / first load | `42` | `200` + full payload, `ETag: "42"`. |
| `"41"` for the wrong resource | `42` | `200`. Markers are per-partition; a mismatch is always safe. |
| `If-None-Match: *` or a list | any | `200`. Only single exact-match values are honoured; anything else falls back to the full payload, which is never wrong, only slower. |

There is no false-`304` path except equal values, and a counter only ever
increases within the life of a partition. (A table rebuild resetting a counter
below a client's held value is a development-environment concern; a client
reload clears it.)

Caching headers: `Cache-Control: no-store` on every response. The poll is an
explicit conditional request from the polling hook, which holds the marker in
its own state; the browser's HTTP cache must not sit in between.

**Two CORS facts, now moot under §7 Q1's same-origin routing but recorded in
case it is ever undone:** `ETag` is **not** a CORS-safelisted response header, so
`Access-Control-Expose-Headers: ETag` would be required or the hook reads `null`;
and `If-None-Match` is **not** a safelisted request header, so every poll would
trigger a preflight `OPTIONS` (mitigable with `Access-Control-Max-Age`).
Same-origin routing removes both.

### Rejected alternatives

**A custom header** (`X-Change-Marker` / `X-If-Marker`). Avoids any interaction
with the browser cache and with 304 semantics, and it is trivially explicit. But
it needs the same CORS exposure and the same preflight, so it costs the same and
buys nothing except a hand-rolled version of a standard every proxy, log and
debugging tool already understands.

**A payload field** (`{"version": 42, "data": …}` with `?since=41`). The least
infrastructure-sensitive option — no header exposure, no preflight beyond what
the request already causes, works identically behind any proxy. Rejected because
the whole point of `G-88`'s design is that an unchanged poll is cheap: a `200`
with an envelope still pays response serialization, gzip and body transfer on
every poll, where a `304` pays a header frame. It also makes "unchanged" an
application-level convention that nothing but our own client can read.

**Weak ETags / `Last-Modified`.** `Last-Modified` has one-second granularity and
would need a timestamp — but `marcaCambio` is deliberately a counter, not a
timestamp, precisely to avoid clock skew between Lambdas and lost updates on
racing writes (`data_model.md` §1.1). Reintroducing a timestamp at the transport
layer would reintroduce the problem the storage layer removed.

---

## 7. Gate questions — resolved (2026-08-30)

The owner ruled on all 13 on 2026-08-30. Question and options are kept for
context; the ruling is the **Decided** line.

1. **Same-origin deployment.** The `HttpOnly` cookie with `SameSite=Lax` needs
   the SPA and the API to be same-site; `ETag`/`If-None-Match` polling is
   materially cheaper same-origin (no preflight, no header exposure). Options:
   (a) route `/v1/*` through the same CloudFront distribution that serves the
   SPA; (b) separate origins → `SameSite=None` + a CSRF token, or fall back to
   bearer. **Decided: (a).** `/v1/*` routes through the same CloudFront
   distribution as the SPA.
2. **Authorizer result caching vs. `FR-AUTH-14`.** Every authenticated request
   costs one `AP2` `GetItem` for the revocation check. Options: (a) TTL 0 —
   removal and reset take effect immediately, one `GetItem` per request; (b) a
   short TTL (30–300 s) — cheaper, but "immediately invalidate" becomes "within
   the TTL". **Decided: (a).** Authorizer cache TTL 0 — at 2–10 users the read
   is free and (b) would weaken a requirement's own wording.
3. **How does `FR-AI-10`'s "regenerate" get past `FR-AI-08`'s idempotency?**
   `idPeticionIA` is a deterministic hash of the request, so regenerating with
   unchanged specifications hits the cache and returns the same recipe. Options:
   (a) an explicit `attempt` integer folded into the hash — a retry (same
   attempt) hits, a regenerate (attempt + 1) misses; (b) client `DELETE`s the
   record then resubmits (`AP27`, two round-trips, racy); (c) a
   `POST /v1/generations/{id}/regenerate` endpoint. **Decided: (a)**, with one
   added constraint: `attempt` is **server-authoritative** — derived from the
   count of *completed* generations for that slot, never a client-side click
   counter (two fast clicks must both compute the same `attempt` and dedupe).
   Additionally the server returns `409` on a generation request for a slot that
   already has one `pending`/`running` (`FR-AI-09` per-slot concurrency). Both
   belong in feature 17's spec.
4. **Per-slot retry shape (`FR-AI-12`).** Options: (a)
   `POST /v1/generations/{id}/slots/{day}/{slot}/retry`, reusing the parent
   run's effective rules; (b) a fresh single-slot `POST /v1/generations`.
   **Decided: (a).** A dedicated per-slot retry endpoint — (b) would need the
   client to re-send the per-run override to reproduce the effective rules.
5. **Rules: whole-set `PUT` or per-rule endpoints?** The port is
   `RuleRepository.get()/save(RuleSet)` and `FR-RULE-07`'s satisfiability check
   is naturally whole-set, but `AP23`/`AP24` are per-rule item writes and
   `FR-RT-02`'s last-write-wins then applies to the *entire* set — one user's
   edit discards another's concurrent edit of a different rule. Options: (a)
   whole-set `PUT` (matches the port, simplest validation); (b) per-rule
   `PUT`/`DELETE` on `/v1/rules/{ruleId}`, with the adapter re-validating the
   whole set on each write. **Decided: (b) — per-rule endpoints.** `data_model.md`
   §4.5 stores rules as separate items (`REGLA#<idRegla>` per rule under the
   `GRUPOREGLAS#` partition); `AP23`/`AP24` are single-item `PutItem`/`DeleteItem`
   writes, so per-rule endpoints map 1:1 and give genuine per-rule
   last-write-wins.

   Consequences: (i) satisfiability (`FR-RULE-07`) is still validated whole-set
   in the adapter on each write — it loads the full set (`AP22`), applies the
   candidate change in memory, checks, then commits the single item; a small
   TOCTOU window between two concurrent per-rule edits is acceptable at 2–10
   users. (ii) The `RuleRepository` port likely grows `save_rule` /
   `delete_rule` to match `AP23`/`AP24` instead of today's `save(RuleSet)` blob
   — a feature 16 spec input.
6. **Wire naming.** Options: (a) English `camelCase` keys (matches
   `conventions.md`'s identifier rule and the domain dataclasses; one mapping,
   at the persistence adapter); (b) Spanish keys matching the persisted
   attributes and the owner's spreadsheet (no adapter mapping on the read path,
   but two mappings inside the Lambda and English domain objects producing
   Spanish JSON). **Decided: (a).** English `camelCase` wire keys.
7. **Library filtering: server or client?** `data_model.md` §7 says
   `FR-LIB-04`'s two filters are "applied in the Lambda, deliberately" — which
   settles *not indexing them*, not *where the SPA runs them*. Options: (a)
   query parameters on `GET /v1/library/recipes`, with the polling hook using
   the unfiltered URI; (b) server-side only, and the pickers re-request on every
   keystroke; (c) the SPA filters the payload it already polls. **Decided: (a).**
   Query params on `GET /v1/library/recipes` — honours §7 literally and leaves
   (c) available to the pickers as a latency optimisation.
8. **What triggers week rollover (`FR-MENU-06`, `-08`)?** It has no REST surface
   and it is not one of the 29 access patterns, but the logic exists
   (feature 13). Options: (a) a scheduled EventBridge invocation of the `api`
   Lambda through a non-HTTP entry point; (b) lazily, on the first read after
   the boundary; (c) a third Lambda — which `architecture.md` §6 forbids without
   sign-off. **Decided: (a).** A scheduled EventBridge rule triggers the `api`
   Lambda directly via a non-HTTP entry point. The *decision* is architectural;
   the *wiring* is deployment.
9. **Server-side copy for `library` and `generation` candidate sources (§3.1).**
   Options: (a) the client sends only the source id and the server copies the
   snapshot (one round-trip, non-tamperable, `FR-CAND-07` enforced in one
   place); (b) the client sends the full recipe body it already holds from
   `AP15`/`AP26` (no extra read, but the snapshot becomes client-supplied
   content). **Decided: (a).** Server-side copy from the source id.
10. **Error body: custom or RFC 9457?** Options: (a) `{"error":{code,message,
    details}}`; (b) `application/problem+json`. **Decided: (b) — RFC 9457
    `application/problem+json`, adopted upfront.** Lock-in is low either way, so
    skipping the later rename wins; with Q1 same-origin the CORS friction is
    gone. The remaining cost is that API Gateway's own authorizer/throttle error
    responses need Gateway Response templates to match the shape (a feature 21
    infra detail). The machine-readable `code` stays as a `problem+json`
    extension member so the SPA still branches on it; `type` may be a
    non-dereferenceable URN like `urn:planner:session-expired` — a real URL is
    not required. §4 is written to this decision.
11. **Mutating an archived week.** A week is closed iff its id sorts before the
    computed current week — no stored flag (`data_model.md` §9). Options:
    (a) `409 WEEK_ARCHIVED`; (b) `403 FORBIDDEN`. **Decided: (a).**
    `409 WEEK_ARCHIVED` — a state conflict, not a permission failure, and
    `Forbidden` is already the role-split code (`FR-AUTH-05`/`-06`).
12. **The `api`→`ai` hop.** **Decided: a standard SQS queue** (owner, definitive
    decision). Recorded in `architecture.md` §1.2 / §1.2.6. The earlier concern
    was only a documentation gap — `architecture.md` §1.2 described the two
    Lambdas without the queue and §6 forbids adding one without an approved
    `design.md`; that is now reconciled.
13. **Does the summary need ingredients?** `FR-SUM-01` specifies a read-only
    view of a week's definitive meals without saying whether ingredients are
    shown. Options: (a) summary reads `AP8` (no ingredients, recipe detail one
    click away via `FR-MENU-05`); (b) summary reads `AP9`. **Decided: (a).**
    Summary reads `AP8`, no ingredients. Consequence: `AP9` (Obtener semana +
    ingredientes) then has exactly one consumer — the internal re-sync
    composition — so `GET /v1/weeks/{weekId}?include=ingredients` is **not** a
    public endpoint. `AP9` is marked internal-only in §1 and §2; the re-sync
    path calls the repository method directly inside the Lambda.
