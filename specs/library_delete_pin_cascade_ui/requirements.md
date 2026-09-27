# library_delete_pin_cascade_ui — Requirements

> Feature 30 · tier 4 · frontend-only follow-up to feature 20 `frontend_spa`,
> flagged during feature 20's final review (2026-09-14). `feature_list.json`
> `covers` is empty; the id translated below is the one the feature's
> description and acceptance criteria name: `FR-RULE-07`'s pin-cascade half
> (`docs/requirements.md`, see `G-20`). `FR-UX-01`, `FR-UX-03` (Castilian
> Spanish, single messages module) and `FR-UX-04` (explicit confirmation
> before a destructive action) are also cited below — both already owned
> (`R15`, `R18`) by `specs/frontend_spa/requirements.md`, in the same
> "consumed, not re-claimed" pattern that file itself uses for `FR-AUTH-*`.
> No id is added to `feature_list.json`'s `covers` array (empty stays empty,
> the `single_recipe_generation` precedent for a description-sourced `FR-*`).

## Scope

**No backend code.** `docs/rest_api_contract.md` §3.4's two-step cascade
(`DELETE /v1/library/recipes/{id}` → `409 PIN_RULES_AFFECTED` with
`details.pins` → confirmed retry with `?confirmCascade=true` → `204`) is
already implemented in `library_editing.py` (feature 27, `done`). This
satisfies acceptance criterion 1 verbatim: the only files this feature
touches are under `frontend/`. The recipe/rule deletion decision itself —
whether the cascade happens at all — stays server-side (`architecture.md`
§1.1); the client only reacts to the response the server already gives it.

## R1
Implements: FR-RULE-07, FR-UX-04

IF the confirmed `DELETE` request for a library recipe answers `409` with
code `PIN_RULES_AFFECTED`, THEN the system SHALL require a second, explicit
confirmation before retrying the deletion.

## R2
Implements: FR-RULE-07, FR-UX-01, FR-UX-03

WHEN presenting the second confirmation of R1, the system SHALL render the
day and slot of every pin listed in the response's `details.pins`.

## R3
Implements: FR-RULE-07

WHEN the user confirms the second confirmation of R1, the system SHALL retry
the `DELETE` request for the same recipe with `confirmCascade=true`.

## R4
Implements: FR-RULE-07, FR-UX-04

WHEN the user cancels the second confirmation of R1, the system SHALL NOT
retry the `DELETE` request.

## R5
Implements: FR-RULE-07

The system SHALL NOT compute, client-side, whether deleting a library recipe
cascades to a pin rule.

## R6
Implements: FR-RULE-07

WHEN the cascade retry of R3 receives `204`, the system SHALL update the
library view to no longer display the deleted recipe.

## R7
Implements: FR-RULE-07, FR-UX-01, FR-UX-03

IF the `DELETE` request for a library recipe answers a rejection whose `code`
is not `PIN_RULES_AFFECTED`, THEN the system SHALL surface the response's
`detail` verbatim, unchanged from the existing library-removal error
handling.

---

## Coverage check

| `FR-*` (cited, not in `covers` — see header) | `R<n>` |
|---|---|
| FR-RULE-07 | R1, R2, R3, R4, R5, R6, R7 |
| FR-UX-01 (owned by feature 20, `R15`) | R2, R7 |
| FR-UX-03 (owned by feature 20, `R15`) | R2, R7 |
| FR-UX-04 (owned by feature 20, `R18`) | R1, R4 |

Every `SHALL`/`SHALL NOT` count is 1 per `R<n>`, checked mechanically (the
`week_calendar` R4/R8/R16/R22 lesson, `docs/specs.md`).

### Acceptance-criteria map (`feature_list.json` id 30)

| Criterion | Satisfied by |
|---|---|
| 1. No backend code | Scope note above; verified by `tasks.md` T6 (`git diff --stat backend/` empty) |
| 2. Catch 409, show pins in a confirm dialog, retry with `confirmCascade=true` | R1, R2, R3 |
| 3. No client business logic beyond the retry URL and pins rendering | R5 (boundary), R2/R3 (the two things left) |
| 4. Test: 409 opens dialog with correct text; confirm retries + both views update; cancel leaves everything untouched | R1, R2, R3, R6 (library view); rules-view disappearance is the existing real-time poll picking up the server's now-pin-free rule list (`FR-RT-02`, owned/tested by feature 26 — see `design.md` §5); R4 (cancel) |
