# impl_close-button-style

Issue 9. One file, one element.

## Red at T1

```
cp issues/close-button-style/tests/frontend/tests/components/LibraryView.closeButton.test.jsx frontend/tests/components/
cd frontend && npx vitest run tests/components/LibraryView.closeButton.test.jsx
Tests  2 failed | 1 passed (3)
```
Matches `plan.md`'s recorded red exactly (E1/E2 red — empty inline style,
`['Cerrar']` unstyled — E3 green).

## Fix

`frontend/src/components/LibraryView.jsx`: imported `secondaryButtonStyle`
from `../tokens/controlStyles.js`; applied it (spread, `marginTop:
tokens.space.sm`, matching `ShoppingListView.jsx`'s established pattern) to
the authoring-panel close button. No other line touched — verified via
`git diff`.

## Traceability

| E<n> | FR-* | T<n> | Test |
|---|---|---|---|
| E1 | FR-UX-02 (via feature 20 acceptance criterion 1) | T2 | `LibraryView.closeButton.test.jsx` "carries the shared secondary-button treatment (E1)" |
| E2 | FR-UX-02 (same chain) | T2 | same file "leaves no button unstyled while the authoring panel is open (E2)" |
| E3 | FR-LIB-02 | T2 (regression, unchanged) | same file "still calls closeAuthoring when clicked (E3)" |

## Result

`cd frontend && npx vitest run tests/components/LibraryView.closeButton.test.jsx
tests/components/LibraryView.test.jsx` — 10/10. Moved file confirmed
byte-identical to the staged copy (`diff`, no output). Full suite: `npx
vitest run` — **431/431**. `npx eslint .` / `npx prettier --check .` clean.
`./init.sh` green.

`issue_list.json`/`feature_list.json` untouched by this implementer. Not
`done` — reviewer next (batched with the other five issues in this run).

## Scope extension (2026-09-23): CandidateAuthoring close button

Resumed session (prior implementer run stalled on infra timeout, not a logic
error); fix and staged test were already present in the working tree, verified
directly rather than redone.

`frontend/src/components/CandidateAuthoring.jsx` mirrors `LibraryView.jsx`:
imported `tokens` and `secondaryButtonStyle`, applied
`style={{ ...secondaryButtonStyle, marginTop: tokens.space.sm }}` to the close
button. `RecipeDetailView.jsx` untouched.

| E<n> | FR-* | T<n> | Test |
|---|---|---|---|
| E4 | FR-UX-02 (via feature 20 acceptance criterion 1) | T6 | `CandidateAuthoring.closeButton.test.jsx` "carries the shared secondary-button treatment (E4)" |
| E5 | FR-CAND-02 | T6 (regression, unchanged) | same file "still calls onClose when clicked (E5)" |

Moved file confirmed byte-identical to the staged copy (`diff -q`, no output).
`cd frontend && npx vitest run tests/components/CandidateAuthoring.closeButton.test.jsx
tests/components/LibraryView.closeButton.test.jsx` — 5/5 green.
