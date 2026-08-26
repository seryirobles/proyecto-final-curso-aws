# password_policy — Requirements

> Feature 9 · tier 1 · `sdd: true`
> Covers: `FR-AUTH-15`, `FR-AUTH-17`
> Notation: strict EARS (`docs/specs.md`). Every `R<n>` cites the frozen
> requirement ids it implements and is verifiable by at least one concrete
> test that asserts a value.

## Purpose in one sentence

Password acceptability for the mandatory set-password step under NIST SP
800-63B (length floor, no composition rules, no rotation — the
common-password blocklist is deferred, see note below), plus username
uniqueness among active accounts and the reservation of the "unknown user"
placeholder name — both raising distinguishable, named exceptions carrying
es-ES rejection text.

## Revision note — blocklist requirements removed (2026-08-26)

`FR-AUTH-15`'s blocklist-rejection clause has been struck (not this feature's
call — the amendment is in `docs/requirements.md` itself) and
`docs/gaps_and_resolutions.md` `G-83` records why: a domain-pure, zero-IO,
zero-dependency module cannot hold a real breach corpus, and a hand-curated
literal would be barely better than the English-only list `G-60` already
rejected. The blocklist is deferred to a future feature, once an injectable
port (the `Clock` pattern, `docs/architecture.md` §1.2.2/§3.1 rule 6) can be
fed by a real corpus through an adapter. The two requirements that implemented
the struck clause — blocklist match and the Spanish-entry guarantee — are
removed from this revision, not renumbered around: this spec is still
`spec_ready` (unimplemented), so the remaining requirements were renumbered
sequentially rather than left with a gap.

## One `SHALL` per requirement

Every `R<n>` below carries exactly one `SHALL` or one `SHALL NOT`, counted
mechanically rather than by eye, per the checklist in `AGENTS.md` /
`docs/specs.md`.

## Scope note — `FR-UX-03` is cited though absent from `covers`

`feature_list.json`'s `covers` array for this feature lists only
`FR-AUTH-15` and `FR-AUTH-17`, but its own acceptance criteria add: "Rejection
messages come from the es-ES messages module (`FR-UX-03`)". This is not an
invented requirement: `specs/text_and_units/design.md` §6 already anticipated
it — `UnknownUnit` deliberately carries no message text because *"the
Castilian rejection text is not this feature's job: `feature_list.json`
assigns it to the features that own the user-facing flow — feature 12
`ai_output_validation` ... and feature 9 `password_policy` (same wording)"* —
and that document's gate question 3 asked the human to confirm exactly this
assignment. `R1`, `R6` and `R7` below cite `FR-UX-03` alongside
`FR-AUTH-15`/`FR-AUTH-17` for that reason. See `design.md` §4 for where the
es-ES text this feature owns is stored.

## Depends on

Feature 1 (`project_scaffold`, done) per `feature_list.json`. This feature
also reuses `normalize` from `planner_core.domain.text` (feature 3
`text_and_units`, done) — not listed in `depends_on` because it is a shipped
shared-kernel function, the same pattern feature 8's `design.md` used for its
own reuse of feature 3. `docs/data_model.md` §2 *mandates* this reuse for the
username fold specifically: *"Same treatment `FR-SHOP-03` defines for
ingredient names; put it behind one shared helper."*

---

## R1
Implements: FR-AUTH-15, FR-UX-03

IF a password's length is less than 10 characters, THEN the system SHALL
raise `PasswordTooShort` carrying the es-ES message `PASSWORD_TOO_SHORT`.

## R2
Implements: FR-AUTH-15

The system SHALL NOT enforce a maximum password length shorter than 64
characters.

## R3
Implements: FR-AUTH-15

The system SHALL NOT reject a password based on which character classes —
uppercase letters, lowercase letters, digits or symbols — it contains.

## R4
Implements: FR-AUTH-15

The system SHALL NOT accept, as an input to password validation, any
parameter representing a password's age, last-changed date, or rotation
count.

## R5
Implements: FR-AUTH-17

WHEN comparing two usernames for uniqueness or reservation, the system SHALL
treat them as equal exactly when their normalized forms — case-, accent- and
whitespace-insensitive, per `planner_core.domain.text.normalize` — are
identical.

## R6
Implements: FR-AUTH-17, FR-UX-03

IF a candidate username's normalized form matches the normalized form of an
existing active account's username, THEN the system SHALL raise
`UsernameAlreadyTaken` carrying the es-ES message `USERNAME_ALREADY_TAKEN`.

## R7
Implements: FR-AUTH-17, FR-UX-03

IF a candidate username's normalized form matches the normalized form of the
reserved "unknown user" placeholder name, THEN the system SHALL raise
`UsernameReserved` carrying the es-ES message `USERNAME_RESERVED`.

---

## Coverage map

| Frozen requirement | Covered by |
|---|---|
| `FR-AUTH-15` (blocklist clause struck, `G-83`) | R1, R2, R3, R4 |
| `FR-AUTH-17` | R5, R6, R7 |
| `FR-UX-03` (cited, see scope note) | R1, R6, R7 |

| `feature_list.json` acceptance criterion | Covered by |
|---|---|
| Minimum length 10, accepted up to at least 64 characters without truncation (`FR-AUTH-15`) | R1, R2 (`design.md` §3 — `validate_password` never slices its input, so "untruncated" holds by construction) |
| No mandatory character-composition rules and no forced periodic rotation are enforced (`FR-AUTH-15`) | R3, R4 |
| Username validation enforces uniqueness among active accounts and reserves the unknown-user placeholder name (`FR-AUTH-17`, `G-42`, `G-58`) | R5, R6, R7 |
| Rejection messages come from the es-ES messages module (`FR-UX-03`) | R1, R5, R6, R7 |

The blocklist acceptance bullets ("A common/breached-password blocklist
rejects matches"; "The blocklist includes common Spanish-language
passwords...") were removed from `feature_list.json` — deferred by `G-83`,
not covered here.
