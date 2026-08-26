# password_policy — Design

> Feature 9 · tier 1 · pure `planner_core.domain`, plus the first backend
> es-ES messages module
> Read `requirements.md` first. This document records the technical decisions
> taken before any code is written, per `docs/specs.md`.
> Depends on feature 1 `project_scaffold` (done) and reuses feature 3
> `text_and_units` (done — `normalize`), per `requirements.md`'s "Depends on".

## 0. The invariant this feature exists to protect

`docs/gaps_and_resolutions.md`, `G-30`:

> NIST 800-63B is the current industry baseline, explicitly superseding the
> older complexity-mandate model, which research has shown pushes users
> toward predictable, easily-guessed patterns... a breach/common-password
> blocklist check is the control that actually stops the realistic attack
> (credential stuffing with previously-leaked passwords), which composition
> rules do not.

**Revision note (`G-83`, 2026-08-26): the blocklist is deferred, not shipped
in this feature.** `G-30`'s blocklist clause and `G-60`'s Spanish-inclusivity
requirement on it are both still true in principle, but `FR-AUTH-15`'s
blocklist-rejection clause has since been struck from the MVP: a
domain-pure, zero-IO, zero-dependency module (`docs/architecture.md` §3.1
rule 1; `backend/core`'s `dependencies = []`) cannot hold a real breach
corpus, and a hand-typed literal would be small and arbitrary — not
markedly better than the English-only list `G-60` already rejected as
missing the point. The right shape for a real blocklist is an **injectable**
dependency — the same pattern already used for `Clock`
(`docs/architecture.md` §1.2.2/§3.1 rule 6: a port plus a sanctioned default,
chosen by `wiring.py`, not by `domain/`) — fed by a real corpus through an
adapter that does not exist yet. That is a future feature's shape to design,
not this one's; this document does not design it. Everything below this note
covers only what remains in scope: the length floor and the absence of
composition/rotation rules.

---

## 1. Scope boundary — what this feature owns

| Requirement | Owned **here** | Deferred to |
|---|---|---|
| `FR-AUTH-15` | The pure validation function, and the length floor/no-forced-ceiling rule and the absence of composition/rotation checks. | Hashing the accepted password, the set-password UI flow itself, any password-hashing-algorithm-driven length ceiling (e.g. bcrypt's 72-byte cap) — **feature 15 `auth_flow`**, tier 3, blocked on **P2** — and the breached-password blocklist itself, deferred whole by `G-83` to a future feature once an injectable corpus adapter exists (post feature 14/15). |
| `FR-AUTH-17` | The uniqueness/reservation check as a pure function over a caller-supplied set of active usernames. | The actual reservation write (`TransactWriteItems` with `attribute_not_exists`, `docs/data_model.md` §5.1) and the rename lookup-by-key trap (§5.2) — **feature 14 `persistence_ports`** onward. The account id `unknown-user` and the fact that it is seeded — already settled at feature 5's gate (`docs/data_model.md` §5.1); this feature does not re-decide it. |
| `FR-UX-03` (cited) | The es-ES text for every rejection this feature raises, in a new backend messages module (§4). | Rendering that text in an HTTP error body — **P5**, undecided. Rendering *any* other feature's rejection text — out of scope; retrofitting `UnknownUnit`/`UnknownIngredientCategory`/etc. to use this module is not this feature's job. |

---

## 2. Layering

`docs/architecture.md` §3: `domain/` is pure logic, no IO, no port, no clock.
Both new domain modules are pure functions of plain values.

| Piece | Layer | Why |
|---|---|---|
| `PASSWORD_TOO_SHORT`, `USERNAME_ALREADY_TAKEN`, `USERNAME_RESERVED` | `planner_core/messages.py` (new, top level) | String constants only — no logic, no IO. Not domain-specific: `application/` and, through `planner_core` as a path dependency, `lambda_api`/`lambda_ai` may need the same strings later (§7 alternative C). |
| `MIN_LENGTH`, `PasswordTooShort`, `validate_password` | `planner_core/domain/password_policy.py` (new) | Pure function over a `str`; no IO, no port, no clock. |
| `UNKNOWN_USER_NAME`, `UsernameAlreadyTaken`, `UsernameReserved`, `validate_username` | `planner_core/domain/username_policy.py` (new) | Pure function over a `str` and a caller-supplied `Iterable[str]`; no IO, no port, no clock. |

No `application/` piece is added. A future use case (feature 15+, once P2 is
decided) reads the persisted active-username set through a port, calls
`validate_username` then `validate_password`, and only then hashes and
persists — none of that orchestration exists yet.

**Zero runtime dependencies preserved.** Both new domain modules import only
`planner_core.domain.errors` and `planner_core.messages`
(`username_policy.py` additionally imports `planner_core.domain.text`) —
all standard-library-only. `backend/core/pyproject.toml` keeps
`dependencies = []`.

---

## 3. Files

### Created

| Path | Contents |
|---|---|
| `backend/core/src/planner_core/messages.py` | `PASSWORD_TOO_SHORT`, `USERNAME_ALREADY_TAKEN`, `USERNAME_RESERVED` — the backend es-ES messages module (§4). |
| `backend/core/src/planner_core/domain/password_policy.py` | `MIN_LENGTH`, `PasswordTooShort`, `validate_password`. |
| `backend/core/src/planner_core/domain/username_policy.py` | `UNKNOWN_USER_NAME`, `UsernameAlreadyTaken`, `UsernameReserved`, `validate_username`. |
| `backend/core/tests/domain/test_password_policy.py` | R1–R4. |
| `backend/core/tests/domain/test_username_policy.py` | R5–R7. |

### Modified

None. `planner_core/domain/errors.py` already declares `PlannerError`
(feature 2) — both new exception families subclass it and change nothing
there.

---

## 4. The backend es-ES messages module — a design decision, not an invention

`docs/conventions.md` § *Language policy* requires every user-facing string
to live in **one messages module**, and its own worked example is backend
Python: `raise InvalidLimit(messages.SHOPPING_QUANTITY_MUST_BE_POSITIVE)`.
`frontend/src/messages/` already exists (feature 1) as the frontend's
instance of that rule; nothing backend-side exists yet, because no feature
before this one owned a genuinely user-facing backend rejection.
`specs/text_and_units/design.md` §6 explicitly declined to build it and named
this feature and feature 12 as the two that would: *"the single messages
module does not exist yet ... creating one here would pre-empt it"* — and
its gate question 3 asked the human to confirm that assignment. This feature
is the first to reach that point, so it builds the module — not a new
messages-module *design*, but the one already assigned.

**What it does not decide.** `planner_core/messages.py` holds Castilian
string constants only. It does not decide the HTTP error format (**P5**), and
it adds no dependency — plain `str` constants, standard library.

**Location: top level (`planner_core/messages.py`), not `domain/messages.py`.**
See §7 alternative C.

```python
"""The single backend es-ES messages module (FR-UX-03): every user-facing
string a backend package raises lives here, in UPPER_SNAKE constants — the
backend counterpart of frontend/src/messages/."""

from __future__ import annotations

PASSWORD_TOO_SHORT = "La contraseña debe tener al menos 10 caracteres."
USERNAME_ALREADY_TAKEN = "Este nombre de usuario ya está en uso."
USERNAME_RESERVED = "Este nombre de usuario está reservado y no puede utilizarse."
```

---

## 5. Signatures

### `planner_core/domain/password_policy.py`

```python
"""Password acceptability under NIST SP 800-63B for the mandatory
set-password step (FR-AUTH-15): a length floor, no composition rules, no
rotation (G-30). The breached-password blocklist clause is deferred, not
implemented here — see design.md section 0 and G-83."""

from __future__ import annotations

from typing import Final

from planner_core import messages
from planner_core.domain.errors import PlannerError

MIN_LENGTH: Final[int] = 10


class PasswordTooShort(PlannerError):
    """Raised when a password is shorter than MIN_LENGTH (R1)."""

    min_length: int
    actual_length: int

    def __init__(self, min_length: int, actual_length: int) -> None:
        super().__init__(messages.PASSWORD_TOO_SHORT)
        self.min_length = min_length
        self.actual_length = actual_length


def validate_password(password: str) -> None:
    """Raise on the first rule violated; return None if password is acceptable.

    No parameter represents age, last-changed date or rotation count (R4) —
    there is nothing to omit, since none exists in this signature at all.
    """
    length = len(password)
    if length < MIN_LENGTH:
        raise PasswordTooShort(MIN_LENGTH, length)
```

### `planner_core/domain/username_policy.py`

```python
"""Username uniqueness among active accounts, and the reservation of the
"unknown user" placeholder name (FR-AUTH-17, G-42, G-58)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

from planner_core import messages
from planner_core.domain.errors import PlannerError
from planner_core.domain.text import normalize

# Value settled at feature 5's gate (docs/data_model.md section 5.1);
# enforced, not chosen here.
UNKNOWN_USER_NAME: Final[str] = "usuario desconocido"


class UsernameReserved(PlannerError):
    """Raised when a candidate username folds to the placeholder's name (R7)."""

    username: str

    def __init__(self, username: str) -> None:
        super().__init__(messages.USERNAME_RESERVED)
        self.username = username


class UsernameAlreadyTaken(PlannerError):
    """Raised when a candidate username folds to an existing active one (R6)."""

    username: str

    def __init__(self, username: str) -> None:
        super().__init__(messages.USERNAME_ALREADY_TAKEN)
        self.username = username


def validate_username(username: str, active_usernames: Iterable[str]) -> None:
    """Raise on a case-/accent-insensitive collision; return None otherwise.

    Caller contract: active_usernames holds only ACTIVE accounts' current
    usernames (a removed account's name may be reused, FR-AUTH-17) and, on a
    rename, excludes the account's own current username first (self-rename
    to an unchanged name must not collide with itself).
    """
    folded = normalize(username)
    if folded == normalize(UNKNOWN_USER_NAME):
        raise UsernameReserved(username)
    if any(folded == normalize(existing) for existing in active_usernames):
        raise UsernameAlreadyTaken(username)
```

---

## 6. A determinism note

**Check order in `validate_username` is reservation, then uniqueness.** Not
FR-mandated — either order is observably identical to a caller who only
checks the exception type — but a fixed order is needed for a test to assert
which exception a colliding-and-reserved candidate raises. It also means a
buggy caller who accidentally includes the placeholder name in
`active_usernames` still gets `UsernameReserved`, the more specific and more
actionable of the two.

`validate_password` has only one check left (length) since the blocklist
check was removed (`G-83`); there is no order left to fix.

---

## 7. Rejected alternatives

**A. A `PasswordTooLong` exception with a concrete maximum (e.g. 64).**
Rejected as invention. `FR-AUTH-15` says the accepted range extends "up to at
least 64, untruncated" — a floor on how far acceptance must reach, not a
requirement to reject anything past it. No `FR-*` or `G-*` asks for an upper
bound; a hashing-algorithm-driven ceiling (e.g. bcrypt's 72-byte limit) is a
consequence of the still-undecided auth mechanism (**P2**) and belongs to
feature 15, not here. `R2` proves the floor holds by testing acceptance of a
200-character password, without asserting anything about what happens
beyond it.

**B. Shipping a hand-curated blocklist anyway, scoped down to "course-project
illustrative" rather than removed.**
Considered, rejected by the owner — recorded as `G-83`, not this document's
own call. A hand-typed literal small enough for a zero-IO, zero-dependency
domain module would be no better than the English-only list `G-60` already
judged insufficient for this app's Spanish-speaking attacker model; shipping
it would check `FR-AUTH-15`'s letter while missing the point `G-30` states
the control exists for. The right shape is an injectable port fed by a real
corpus (§0), which does not exist yet — deferred whole, not shipped thin.

**C. `planner_core/domain/messages.py` instead of top-level
`planner_core/messages.py`.**
Considered, not chosen. Message strings are not domain logic — they carry no
behavior — and nothing in `docs/architecture.md` §3 says `domain/` owns
cross-cutting text. Top level keeps the module reachable, unchanged, from a
future `application/` or Lambda `handler.py` piece that also needs to render
one of these strings (e.g. a session-expiry message, `FR-AUTH-16`) without
that piece reaching into `domain/` for something that is not a domain type.

**D. One combined module `account_policy.py` instead of
`password_policy.py` + `username_policy.py`.**
Rejected. The two concerns share no code — `username_policy.py` does not
import `password_policy.py` — and `docs/conventions.md` § *Tests* wants a
test module per source module, the same reasoning `specs/text_and_units/design.md`
§9 alternative I already gave for keeping `text.py` and `units.py` separate.

**E. `validate_password`/`validate_username` returning a bool or an error
code instead of raising.**
Rejected. `docs/architecture.md` §4 invariant 12: functions that can fail
raise; they never return a sentinel that a caller might forget to check.

---

## 8. Boundary checks and gate questions

### Boundary checks

- **`docs/architecture.md` §2 (pending, human-owned):** nothing here needs
  P2–P6. This feature is pure `domain/` plus one new constants module; no
  port, no adapter, no Lambda, no hashing algorithm.
- **§2.1 decide-in-a-spec items:** none of the four listed items (unit list,
  ingredient-category list, servings count, per-user cap) are touched. The
  blocklist content is no longer a value this spec proposes — it was removed
  from scope entirely by `G-83`; no §2.1-style value remains to gate.
- **Frozen docs:** none modified. `docs/data_model.md` §5.1's
  `UNKNOWN_USER_ID = "unknown-user"` and reserved-name value are read, not
  re-decided.
- **User-facing strings:** three, all in `planner_core/messages.py` (§4).
- **Runtime dependencies:** none added; `planner-core` keeps
  `dependencies = []`.
- **Requirements invented:** none. Every `R<n>` cites `FR-AUTH-15`,
  `FR-AUTH-17`, or the pre-anticipated `FR-UX-03` (scope note,
  `requirements.md`).

### Gate questions for the human

1. **`planner_core/messages.py` as the backend's single es-ES messages
   module, and the three literal strings in §4.** Recommended: yes — this is
   the assignment `specs/text_and_units/design.md` §6/§10 gate question 3
   already flagged as belonging to this feature. What turns on it: whether
   this feature ships any Castilian text at all, or whether `PasswordTooShort`
   etc. stay silent like `UnknownUnit` and wait for feature 15/20 instead.

2. **No enforced maximum password length (§7 alternative A).** Recommended:
   yes — confirms this feature does not invent a ceiling `FR-AUTH-15` never
   asked for. What turns on it: whether an extremely long input is ever
   rejected before it reaches feature 15's hashing step; if the human wants a
   generous resource-exhaustion ceiling now, it needs its own `FR-*`-traceable
   reasoning or an explicit note that it is accepted as an unstated,
   non-functional safeguard.
