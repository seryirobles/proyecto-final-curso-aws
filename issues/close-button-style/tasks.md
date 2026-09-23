# close-button-style — tasks

- [x] T1 — Move `issues/close-button-style/tests/frontend/tests/components/LibraryView.closeButton.test.jsx`
  to `frontend/tests/components/LibraryView.closeButton.test.jsx` **verbatim**;
  run `cd frontend && npx vitest run tests/components/LibraryView.closeButton.test.jsx`
  and confirm E1 and E2 fail (empty inline style / `[ 'Cerrar' ]`) and E3
  passes. Covers: E1, E2, E3.
- [x] T2 — In `frontend/src/components/LibraryView.jsx`, import
  `secondaryButtonStyle` from `../tokens/controlStyles.js` and apply it to the
  authoring-panel close button (line 207), spread with
  `marginTop: tokens.space.sm`. No other change to the file. Covers: E1, E2.
- [x] T3 — Re-run the moved test file: all three green. Confirm the file is
  byte-identical to the staged one (`git diff --no-index`). Covers: E1, E2, E3.
- [x] T4 — Run `./init.sh` green (frontend lint/format/test included) and record
  the `E<n> → T<n> → test` map in `progress/impl_close-button-style.md`.

Scope extension (2026-09-23):

- [x] T5 — Move `issues/close-button-style/tests/frontend/tests/components/CandidateAuthoring.closeButton.test.jsx`
  to `frontend/tests/components/CandidateAuthoring.closeButton.test.jsx`
  **verbatim**; run it and confirm E4 fails (empty inline style) and E5 passes.
  Covers: E4, E5.
- [x] T6 — In `frontend/src/components/CandidateAuthoring.jsx`, import `tokens`
  and `secondaryButtonStyle` and give the close button
  `style={{ ...secondaryButtonStyle, marginTop: tokens.space.sm }}`, mirroring
  `LibraryView.jsx`. Do not touch `RecipeDetailView.jsx`. Covers: E4.
- [x] T7 — Re-run both close-button test files green, confirm the moved file is
  byte-identical to the staged one, run `./init.sh` green and extend the map in
  `progress/impl_close-button-style.md`. Covers: E4, E5.
