# text_and_units — Design

> Feature 3 · tier 1 · pure `planner_core.domain`
> Read `requirements.md` first. This document records the technical decisions
> taken before any code is written, per `docs/specs.md`.

## 0. The invariant this feature exists to protect

`docs/architecture.md` §4 invariant 10:

> **Text matching is normalised.** Case-, accent- and trim-insensitive for
> ingredient aggregation. No fuzzy matching beyond that — no stemming, no
> synonyms. (`FR-SHOP-03`, `G-56`, `G-68`)

Everything below is subordinate to that sentence and to the sentence it is
paired with in `FR-SHOP-03`: *"aggregating only items with matching name + unit
(no cross-unit conversion in the MVP)"*.

Two consequences drive the whole design:

1. **The fold is a key.** Two call sites that fold slightly differently produce
   keys that never match — `docs/data_model.md` §2 says exactly this about the
   username reservation and instructs: *"put it behind one shared helper."*
   Hence R1 and its mechanical guard R2.
2. **There is no conversion, so the vocabulary must be a function, not a
   relation.** One physical dimension, one unit. Any second unit for the same
   dimension is a permanent, unbridgeable split in the shopping list. Hence §4.

---

## 1. Scope boundary — what this feature owns of each `FR-*`

Both covered requirements are shared with later features. Getting this line
wrong is what bites in features 4, 7, 8 and 12, so it is drawn explicitly.

| Requirement | Owned **here** | Deferred to |
|---|---|---|
| `FR-SHOP-03` | The **fixed unit list** as a closed vocabulary, and the case-/accent-/trim-insensitive **name normalization** with its explicit exclusions. The absence of any conversion API. | The button, the aggregation itself and the merge on normalized name + unit — **feature 7 `shopping_aggregation`**. Applying the merge to the list — **feature 8 `shopping_list_state`** (`G-72`, `G-77`). |
| `FR-LIB-05` | The single vocabulary that ingredient quantities must draw from, and the one entry point (`parse_unit`) that rejects anything else. | The `Ingredient`/`Recipe` shape that carries a quantity and a unit — **feature 4 `recipe_model`**. Validating AI output against the list and reporting the failure in es-ES — **feature 12 `ai_output_validation`** (`G-48`, `FR-AI-12`). The dropdown itself — **feature 20 `frontend_spa`**. |

**The reusable artefacts.** `normalize(name)` and `parse_unit(value)`. Features
4, 7, 8 and 12 must call them, never re-derive them. R2 and R16 are the
mechanical guards that make "must" enforceable rather than aspirational — same
technique as `backend/core/tests/test_no_ambient_time.py`, which feature 2
established.

**One consumer outside this feature's `covers` array.** `docs/data_model.md`
§2, *Username reservation key — folded*, requires the `FR-AUTH-17` reservation
key to be *"lower-cased, accent- and whitespace-stripped. Same treatment
`FR-SHOP-03` defines for ingredient names; put it behind one shared helper."*
That helper is `normalize`. **Feature 9 `password_policy` must import it, not
re-implement it.** No `R<n>` here claims `FR-AUTH-17` — that would be scope
creep into feature 9 — but the obligation is recorded here so it is not
re-derived there. Note also `docs/data_model.md` §5.2: a rename deletes its old
reservation **by lookup, never by re-folding**, precisely because a later
refinement of `normalize` would orphan keys written before it. That is why §5
below settles the `ñ` question **now** rather than leaving it to be "improved"
later.

---

## 2. Layering

`docs/architecture.md` §3 describes `domain/` as *"Pure logic. No IO, no AWS
SDK, no framework, no clock."* Both pieces of this feature are pure functions of
plain values — a `str` in, a `str` or an enum member out. No port is involved,
no clock, no IO.

| Piece | Layer | Why |
|---|---|---|
| `normalize` | `planner_core/domain/text.py` | Pure function of a `str`. |
| `Unit`, `parse_unit`, `UnknownUnit` | `planner_core/domain/units.py` | Pure vocabulary and its validation. `docs/conventions.md` § *Error handling*: domain exceptions live next to the domain they belong to. |

There is **no `application/` piece**: nothing here orchestrates a port. Adding
one would be layering theatre.

**Zero runtime dependencies preserved.** `unicodedata` and `enum` are standard
library, so `backend/core/pyproject.toml` keeps `dependencies = []`
(`docs/architecture.md` §6, `docs/conventions.md` § *Packaging conventions*).
No dependency is proposed by this feature — not even a dev-group one.

---

## 3. Files

### Created

| Path | Contents |
|---|---|
| `backend/core/src/planner_core/domain/text.py` | `normalize`. |
| `backend/core/src/planner_core/domain/units.py` | `Unit`, `parse_unit`, `UnknownUnit`. |
| `backend/core/tests/domain/test_text.py` | R3–R13. |
| `backend/core/tests/domain/test_units.py` | R14, R15, R17–R21. |
| `backend/core/tests/test_shared_kernel_guards.py` | R1, R2, R16, R22 — the three mechanical scans. Cross-cutting, so it sits beside `test_no_ambient_time.py` at the `tests/` root rather than under `tests/domain/`, following that module's precedent. |

### Modified

None. `planner_core/domain/errors.py` already declares `PlannerError` (added by
feature 2, task T4, *"the base class for every domain exception in features
3–13"*) — R19 subclasses it and changes nothing there.

Nothing is added to `backend/core/tests/support/`: this feature implements no
port and needs no fake. Review finding **F7** (`ruff`'s isort groups `support`
as third-party, left open by the human's decision) therefore does not touch this
task list.

---

## 4. The unit vocabulary — the `docs/architecture.md` §2.1 item

`G-39` confirmed the *approach* — fixed list, no cross-unit conversion — and
left *"the literal enumeration of units … as an implementation detail (a static
config list), not a further business decision"*. `docs/architecture.md` §2.1
lists it as a **decide-in-a-spec** item: proposed here, approved by the human at
the gate.

### Proposed vocabulary

| Member | Code (stored in `unidad`) | Dimension | es-ES label, owned by feature 20 |
|---|---|---|---|
| `Unit.GRAM` | `"g"` | mass | `g` |
| `Unit.MILLILITRE` | `"ml"` | volume | `ml` |
| `Unit.UNIT` | `"unit"` | count | `ud.` |

**Exactly one unit per dimension.** This is the whole argument. `FR-SHOP-03`
forbids cross-unit conversion, so nothing in the system can ever reconcile
`2 kg de patatas` with `500 g de patatas`: they would sit in the shopping list
as two lines forever. Every redundant unit in the vocabulary is therefore a
*guaranteed*, silent aggregation failure of exactly the kind `G-48` and `G-56`
were written to prevent. Three units make that failure impossible by
construction rather than by discipline.

**The accepted cost, stated plainly.** Recipes and the shopping list read in
grams and millilitres: `2500 g de patatas`, not `2,5 kg`. A display-time
conversion is **not** available as a mitigation — no `FR-*` authorises one, and
`docs/architecture.md` §1.1 and `docs/conventions.md` § *Frontend conventions*
both forbid the client from computing what the backend did not
(*"the SPA displays results — it never recomputes them"*). So this is a real
readability cost, paid once per large quantity, in exchange for aggregation
that always works. **Gate question 1 in §10 offers the human the alternative.**

**Why the codes are not Spanish.** `docs/conventions.md` § *Language policy*
puts identifiers and stored technical values in English and confines Castilian
Spanish to user-facing strings in one messages module. `g` and `ml` are SI
symbols and language-neutral; `unit` is the English token, rendered as `ud.` by
feature 20's messages module. The attribute *name* `unidad` stays Spanish
because `docs/data_model.md` §1 names the whole schema in Spanish — that is the
schema's convention, not the value's.

**Where the vocabulary is stored.** `unidad` on `DatosPlatoSemana`,
`DatosPlatoBiblioteca` and `DatosIngredienteLista` (`docs/data_model.md` §1). A
unit code is an **attribute value, not a key segment**, so `docs/data_model.md`
§2 — the home of the five key formats — needs nothing added. This spec and
`units.py` are the vocabulary's home.

**What is deliberately absent.** No `kg`, no `l`, no `cucharada`, `pizca`,
`diente`, `taza` or `lata`. Ingredients with no meaningful measure use
`Unit.UNIT` and carry the detail in the name (`"diente de ajo"`), which costs
nothing: the name is already the other half of the merge key.

---

## 5. What `normalize` does, and what it must never be "improved" into

### 5.1 The algorithm, in order

1. **`strip()`** — leading/trailing whitespace (R3). Python's `str.strip()`
   removes the non-breaking space `U+00A0` too, which matters because ingredient
   names get pasted from web recipes.
2. **`casefold()`** — lower case (R5).
3. **NFD decompose**, then **drop every combining mark except `U+0303`** (R6,
   R7).
4. **NFC recompose** (R8), so `n` + `U+0303` becomes the single codepoint `ñ`
   and two spellings of the same surviving letter compare equal.

**Why case-folding comes before mark removal.** *Corrected 2026-08-23, after
the reviewer's mutation pass on this feature. The original claim here was
wrong; it is replaced rather than struck through because `design.md` is a spec,
not one of the frozen requirement docs.*

The original rationale argued that `"İ".casefold()` is `i` + `U+0307`, so
case-folding *introduces* a combining mark that a later fold would leave
behind. **That reasoning does not hold.** Step 3 decomposes with NFD first, and
`unicodedata.normalize("NFD", "İ")` is already `I` + `U+0307` — the dot is a
separate combining mark under either ordering, and step 3 strips it either way.

The two orderings were swept exhaustively over `U+0000`–`U+2FFFF`: they diverge
on **64 codepoints, every one of them Greek with iota subscript, and not one of
them Latin**. On this feature's domain — Castilian ingredient names and
usernames (`docs/data_model.md` §5.2) — the orderings are **equivalent**.

The order is kept as specified because it is harmless and already implemented,
**not** because it is load-bearing. Anyone reversing it should know they are
changing nothing that this project can observe. The `"İ"` → `"i"` value in §8
stays a good test of R6 — it just does not test an ordering rule, because there
is no ordering rule to test.

Internal whitespace is untouched (R4): `FR-SHOP-03` says *leading- and
trailing*-whitespace-insensitive and no more, and `docs/data_model.md` §5.2
names *"collapsing internal whitespace"* as a hypothetical **future** refinement
— i.e. not now.

### 5.2 The exclusions, and why they are requirements rather than a comment

`G-56`: *"Singular/plural stemming and synonym matching ('tomate cherry' vs
'tomatitos') are genuinely hard, error-prone, and were already implicitly
rejected with cross-unit conversion (G-39) — the fixed-vocabulary philosophy
stops at what can be normalized losslessly."*

`G-74` then **depends** on that refusal: `FR-SHOP-11` (duplicate grouping) was
removed partly because *"a 'likely duplicate' marker would have to be driven by
the same matching that requirement rejected"*. So adding stemming here would
silently reopen a removed requirement. R10, R11 and R12 exist so a later reader
who thinks plural folding is an obvious win has to argue with a failing test,
not with a comment.

### 5.3 `ñ` is a letter, not an accented `n` — the one real judgement call

The naive implementation of "accent-insensitive" is NFD + drop all combining
marks. Applied to Castilian it merges distinct lexemes:

| Naive fold | Merges |
|---|---|
| `ñ` → `n` | `año` / `ano`, `piña` / `pina`, `caña` / `cana`, `peña` / `pena` |

`ñ` is a separate letter of the Spanish alphabet; the *written accent* the
requirement means is the acute on vowels, plus the diaeresis on `ü`. Folding
`ü` → `u` is right (`pingüino` / `pinguino` is one word, misspelled); folding
`ñ` → `n` is wrong (`piña` / `pina` is two words). R6 and R7 encode exactly
that split, and the implementation is one rule — *keep `U+0303`* — not a table.

**Why this is settled now and not later.** `docs/data_model.md` §5.2 names
*"handling `ñ` differently"* as the example of a refinement that would break the
username reservation keys already written: *"a key re-derived today stops
matching a key written yesterday … the stale reservation becomes permanent and
unaddressable."* The cheapest moment to get the fold right is before the first
key exists. **Gate question 2 in §10.**

---

## 6. Signatures

### `planner_core/domain/text.py`

```python
def normalize(name: str) -> str:
    """Return the matching form of an ingredient name (FR-SHOP-03)."""
```

Total: every `str` maps to a `str`, and a blank name maps to `""` (R9). It
raises nothing. Whether a blank ingredient name is *acceptable* is not decided
here — no `FR-*` covers it, and the answer belongs to the entities that hold a
name (feature 4 `recipe_model`, feature 8 `shopping_list_state`). Inventing a
rejection here is exactly what `docs/specs.md` forbids.

**The normalized form is never persisted.** `docs/data_model.md` §7 already
declined it: *"Store the normalized ingredient name on
`DatosIngredienteLista`? **Declined.** Re-sync re-derives it each press."* Same
display/key split as the username: `nombreIngrediente` keeps the exact casing
the user typed.

### `planner_core/domain/units.py`

```python
class Unit(StrEnum):
    GRAM = "g"
    MILLILITRE = "ml"
    UNIT = "unit"


class UnknownUnit(PlannerError):
    """Raised when a value is not a member of the fixed unit list."""

    def __init__(self, value: str) -> None: ...

    value: str


def parse_unit(value: str) -> Unit:
    """Resolve a unit code to its member, or raise UnknownUnit."""
```

`StrEnum` because the member's value **is** the persisted `unidad` code, so
serialisation is the identity function and no second mapping table can drift
from the enum. `parse_unit` is the only way in, so the looser `==` comparison
`StrEnum` allows against a bare string is not a way to bypass validation.

The module's public API is **exactly** these three names. R21's test asserts
that set, which is how "no conversion exists" is proved rather than asserted.

### Exceptions

| Exception | Base | Raised when |
|---|---|---|
| `UnknownUnit` | `PlannerError` | `parse_unit` receives a value that is not exactly a member's code (R18). |

Named `UnknownUnit`, not `InvalidUnit`, because the condition is not
malformedness: the token may be a perfectly good unit in the world (`"kg"`,
`"cucharada"`) and is simply absent from a **closed vocabulary**. It reads
correctly at both call sites `G-48` names — the human dropdown path and the AI
output-validation path.

**`UnknownUnit` carries no message — deliberately.** It carries the rejected
value (R20) and nothing else. The Castilian rejection text is **not this
feature's job**: `feature_list.json` assigns it to the features that own the
user-facing flow — feature 12 `ai_output_validation` (*"Failure messages come
from the es-ES messages module (FR-UX-03)"*) and feature 9 `password_policy`
(same wording). `docs/conventions.md` § *Language policy* requires every
user-facing string to live in **one** messages module; that module does not
exist yet, its location depends on the error format of **P5** (undecided,
`docs/architecture.md` §2), and creating one here to hold a single string would
pre-empt it. R20 exists precisely so the caller can build the sentence.

---

## 7. The three mechanical guards

R2, R16 and R22 are enforced by scans in
`backend/core/tests/test_shared_kernel_guards.py`, built to the discipline
feature 2 arrived at in tasks T44 and T46 — every scan **self-tests first**, so
none can pass by matching nothing:

| Guard | Scans for | Self-test |
|---|---|---|
| R2 — one fold | `unicodedata`, `casefold`, `.lower()` in any `.py` under `src/planner_core` except `domain/text.py` | The same pattern is asserted to match inside `domain/text.py`, and the scanned file list is asserted non-empty and to contain `domain/units.py` and `domain/calendar.py`. |
| R16 — one vocabulary | a class definition whose name contains `Unit`, and assignments to `GRAM`/`MILLILITRE`/`LITRE`/`KILOGRAM`, outside `domain/units.py` | Asserted to match inside `domain/units.py`; file list asserted non-empty. |
| R22 — ASCII only | any non-ASCII codepoint in `domain/text.py` and `domain/units.py` | The file list is asserted to be exactly those two modules and to be non-empty. |

`.lower()` is included in the R2 scan on purpose, even though it cannot on its
own implement the accent rule: a bare `.lower()` used as a merge key in feature
7 or 8 would be a second fold, and a wrong one. A later feature with a genuine
unrelated need for `.lower()` should route it through `normalize` or come back
through review — that is the intended friction.

R22 also buys something specific: with the module restricted to ASCII, the
accent fold **cannot** be implemented as a hard-coded `str.maketrans` table of
accented characters. It has to be the `U+0303` rule, which is the only form that
also handles decomposed input. The honest limitation, recorded by feature 2 in
`progress/impl_week_calendar.md` §4, still applies: an *unaccented* Spanish
string such as `"unidad"` would slip past an ASCII check.

---

## 8. Concrete test values

Use these exact values. Do not invent new ones.

### 8.1 `normalize`

| Input | Output | Proves |
|---|---|---|
| `"Tomate"` | `"tomate"` | R5 |
| `"tomate "` | `"tomate"` | R3 |
| `"tomáte"` | `"tomate"` | R6 |
| all three above | one identical value | **R13** — the `feature_list.json` criterion and the `docs/verification.md` Level 4 row for `G-56` |
| `"  Jamón  "` | `"jamon"` | R3, R5, R6 |
| `chr(0xa0) + "jamón" + chr(0xa0)` | `"jamon"` | R3 — wrapped in **non-breaking spaces**, as pasted from a web recipe |
| `"jamo" + chr(0x0301) + "n"` | `"jamon"` | R6, R8 — **decomposed** input |
| `"Pingüino"` | `"pinguino"` | R6 |
| `"Piña"` | `"piña"` — length 4, its third codepoint `U+00F1` | R7, R8 |
| `"Pin" + chr(0x0303) + "a"` | equal to `normalize("Piña")`, length 4 | R7, R8 — **decomposed** `ñ` recomposes |
| `"pina"` | `"pina"` — **not** equal to `normalize("Piña")` | R7 |
| `"año"` / `"ano"` | `"año"` / `"ano"` — different | R7 |
| `chr(0x0130)` (Turkish dotted capital I) | `"i"` — length 1, no `U+0307` | R6 (NOT an ordering test — see §5.1, corrected 2026-08-23) |
| `"tomate  cherry"` | `"tomate  cherry"` — both spaces kept | R4 |
| `"tomates"` | `"tomates"` — **not** equal to `normalize("tomate")` | R10 |
| `"tomatitos"` | `"tomatitos"` — **not** equal to `normalize("tomate")` | R11 |
| `"papa"` / `"patata"` | different values | R12 |
| `""` | `""` | R9 |
| `"   "` | `""` | R9 |

### 8.2 `parse_unit`

| Input | Result | Proves |
|---|---|---|
| `"g"` | `Unit.GRAM` | R17 |
| `"ml"` | `Unit.MILLILITRE` | R17 |
| `"unit"` | `Unit.UNIT` | R17 |
| `"G"` | `UnknownUnit`, `exc.value == "G"` | R18, R20 |
| `" g"` | `UnknownUnit` | R18 |
| `"gramos"` | `UnknownUnit`, `exc.value == "gramos"` | R18, R20 |
| `"kg"` | `UnknownUnit` | R18 — the unit the vocabulary deliberately excludes (§4) |
| `""` | `UnknownUnit` | R18 |
| `[u.value for u in Unit]` | `["g", "ml", "unit"]` | R14, R15 |

---

## 9. Rejected alternatives

**A. The five-unit list `g`, `kg`, `ml`, `l`, `unit` sketched in `G-39`.**
Rejected — see §4. `G-39`'s parenthetical *"(g, kg, ml, l, units, …)"* is the
gap author's illustration of the *problem*, in the same sentence that leaves the
enumeration open; the gap's decision is the approach, not the list. With no
conversion, `kg` and `l` do not add expressiveness, they add a permanent split:
`2 kg` and `500 g` of the same ingredient can never merge, in a feature whose
entire purpose is merging. Offered to the human as **gate question 1** because
the cost it avoids — grams on screen — is a taste judgement, not a technical
one.

**B. Blanket accent folding: NFD, drop every combining mark.**
Rejected — see §5.3. It merges `año`/`ano`, `piña`/`pina`, `caña`/`cana`. One
extra rule (*keep `U+0303`*) removes the whole class of error, and
`docs/data_model.md` §5.2 makes fixing it later expensive, because the same fold
generates username reservation keys.

**C. A `str.maketrans` table of accented characters.**
Rejected. It fails on decomposed input (`"jamón"` arrives from macOS and
from some web sources), it puts non-ASCII literals in domain source — which R22
forbids and which feature 2's guard already treats as the smell of leaked
Castilian — and it needs an edit every time a new character appears. The
`U+0303` rule is one line and total.

**D. Case-insensitive or whitespace-tolerant `parse_unit`.**
Rejected. `G-48`: *"the alternative — fuzzy unit parsing at aggregation time —
is exactly the cross-unit-conversion complexity the MVP explicitly rejected
(G-39)"*. Units reach the domain from a dropdown (`FR-LIB-05`) or from AI output
that is *"instructed and validated"* against the same list, with failures
surfaced through `FR-AI-12`. A `"G"` arriving at `parse_unit` is a bug in the
caller, and the loud rejection is what makes feature 12's validation meaningful.
Accepting variants would also make R21 hollow: tolerating `"kg"` as `"g"` is a
conversion in disguise.

**E. Applying `normalize` to unit values.**
Rejected, same reason as D, plus a sharper one: `normalize` exists to make two
*user-authored free-text* names match. A unit is not free text — it is a closed
vocabulary — so the two must not share a validation path or the vocabulary stops
being closed.

**F. Collapsing internal whitespace in `normalize`.**
Rejected. `FR-SHOP-03` says leading- and trailing-whitespace-insensitive and
nothing more, and `docs/data_model.md` §5.2 lists it as a *hypothetical future*
refinement, in a paragraph explaining why refining the fold after keys exist is
dangerous. R4 pins the current reading with a test.

**G. Raising on an empty ingredient name.**
Rejected as invention. No `FR-*` says a name may not be blank; the entities that
hold names (features 4 and 8) are where such a rule would belong if one is ever
written. R9 defines the behaviour instead of guessing at a rule.

**H. Storing the normalized name alongside the display name.**
Rejected — already decided against in `docs/data_model.md` §7: *"Re-sync
re-derives it each press; not worth an attribute at household scale."* Storing
it would also freeze one version of the fold into the data, which is the failure
mode §5.2 describes.

**I. One module, `domain/text_and_units.py`.**
Rejected. The feature name is a backlog label, not a module name. The two
concerns share no code — `units.py` does not import `text.py` — and
`docs/conventions.md` § *Tests* wants a test module per source module.

**J. Putting `normalize` in `application/`, or in a `planner_core/shared/`
utilities package.**
Rejected. It is a pure function of plain values with no port, which
`docs/architecture.md` §3 places in `domain/`; and §6 forbids building a
configuration or utilities framework — *"Configuration is explicit values passed
in, or a single documented constants module."*

**K. An es-ES message on `UnknownUnit`.**
Rejected — see §6. Features 9 and 12 own their rejection messages by their own
acceptance criteria, the single messages module does not exist yet, and its
shape depends on **P5**.

---

## 10. Boundary checks and gate questions

### Boundary checks

- **`docs/architecture.md` §2 (pending, human-owned):** nothing here needs P2,
  P3, P4, P5 or P6. P5 is *touched* — the error format that will render
  `UnknownUnit` — but not needed: this feature deliberately emits no message
  (§6).
- **§2.1 decide-in-a-spec items:** exactly one is touched, **the literal unit
  list**. Proposed in §4. The ingredient-category list (`G-69`) belongs to
  features 4 and 6; the servings count (`G-64`) to feature 11. Neither is
  proposed here.
- **Frozen docs:** none modified. `docs/data_model.md` needs no change either —
  a unit code is an attribute value, not one of the five key formats of §2.
- **User-facing strings:** none, enforced by R22.
- **Runtime dependencies:** none added; `planner-core` keeps
  `dependencies = []`.
- **Requirements invented:** none. Every `R<n>` cites `FR-SHOP-03` or
  `FR-LIB-05`.

### Gate questions for the human

1. **The unit vocabulary (§4).** Recommended: three units — `g`, `ml`, `unit`.
   The alternative is five (`+ kg`, `+ l`), which reads better on screen and
   splits the shopping list whenever two recipes pick different units for the
   same ingredient. Approve one.
2. **`ñ` survives the fold (§5.3).** Recommended: yes — `piña` and `pina` stay
   different keys. Worth an explicit yes/no because `docs/data_model.md` §5.2
   makes reversing it after the first username reservation exists a data
   problem, not a code change.
3. **`UnknownUnit` carries no Castilian message (§6, rejected alternative K).**
   Confirming that features 9 and 12 own their rejection text, as their
   acceptance criteria already state, and that this feature adds no messages
   module ahead of P5.
