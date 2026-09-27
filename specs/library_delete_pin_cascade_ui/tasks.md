# library_delete_pin_cascade_ui — Tasks

Test-first inside each task. No backend file is touched by any task below —
`docs/rest_api_contract.md` §3.4 and `library_editing.py` are already
`done` (feature 27).

- [x] T1 — Add `LIBRARY_REMOVE_PIN_CASCADE_WARNING` and `LIBRARY_REMOVE_PIN_CASCADE_CONFIRM` to `frontend/src/messages/es-ES.js` (design.md §4). Covers: R2.
- [x] T2 — In `frontend/src/hooks/useLibrary.js`, factor the existing DELETE + marker/refetch body out of `remove`'s inline callback into a small `deleteRecipe(recipeId, { confirmCascade })` helper; add the local `formatPin`/`composeCascadeMessage` helpers (design.md §4). Covers: R2, R3.
- [x] T3 — Change `remove`'s catch block to special-case `err.code === 'PIN_RULES_AFFECTED'`: re-arm `confirm` with the composed cascade message and a retry `onConfirm` that calls `deleteRecipe(recipeId, { confirmCascade: true })`; keep the existing `setError(toDetail(err))` path for every other rejection, including the retry's own failure (design.md §3). Covers: R1, R4, R5, R7.
- [x] T4 — Add `frontend/tests/hooks/useLibrary.pinCascade.test.js` with a `fakeLibraryServer` (pattern: `useLibrary.mutationVisibility.test.js`) covering: 409 opens the second dialog with the correct day/slot text; confirming retries with `?confirmCascade=true` and the recipe leaves `recipes` after the poll settles; cancelling issues no retry and leaves the recipe present; a non-cascade rejection still sets `error` to `err.detail` verbatim (design.md §6). Covers: R1, R2, R3, R4, R6, R7.
- [x] T5 — Run `./init.sh`; confirm `git diff --stat -- backend/` is empty (acceptance criterion 1, no backend code); write `progress/impl_library_delete_pin_cascade_ui.md` with the R-to-test traceability. Covers: R1-R7.
