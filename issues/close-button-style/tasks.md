# close-button-style — tasks

- [ ] T1 — Move `issues/close-button-style/tests/frontend/tests/components/LibraryView.closeButton.test.jsx`
  to `frontend/tests/components/LibraryView.closeButton.test.jsx` **verbatim**;
  run `cd frontend && npx vitest run tests/components/LibraryView.closeButton.test.jsx`
  and confirm E1 and E2 fail (empty inline style / `[ 'Cerrar' ]`) and E3
  passes. Covers: E1, E2, E3.
- [ ] T2 — In `frontend/src/components/LibraryView.jsx`, import
  `secondaryButtonStyle` from `../tokens/controlStyles.js` and apply it to the
  authoring-panel close button (line 207), spread with
  `marginTop: tokens.space.sm`. No other change to the file. Covers: E1, E2.
- [ ] T3 — Re-run the moved test file: all three green. Confirm the file is
  byte-identical to the staged one (`git diff --no-index`). Covers: E1, E2, E3.
- [ ] T4 — Run `./init.sh` green (frontend lint/format/test included) and record
  the `E<n> → T<n> → test` map in `progress/impl_close-button-style.md`.
