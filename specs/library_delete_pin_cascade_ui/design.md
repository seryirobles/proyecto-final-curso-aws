# library_delete_pin_cascade_ui — Design

> Feature 30 · read `requirements.md` first. Builds on feature 20
> `frontend_spa` (`useLibrary.js`, `useConfirm.js`, `ConfirmDialog.jsx`,
> `api/client.js`, `domain/labels.js`, `messages/es-ES.js`) and feature 27
> `library_editing` (server-side cascade, already `done`). No
> `docs/architecture.md` §2 item is needed. No `docs/data_model.md` change is
> needed — no new item type, key format or access pattern; the retry is a
> query-string flag the server already reads.

## 1. Files touched

| File | Change |
|---|---|
| `frontend/src/hooks/useLibrary.js` | `remove`'s catch block special-cases `PIN_RULES_AFFECTED`; adds a local pin-label helper and a cascade-retry thunk. |
| `frontend/src/messages/es-ES.js` | Two new `MESSAGES` keys (§4 below). |
| `frontend/tests/hooks/useLibrary.pinCascade.test.js` | New test file (§6 below). |

No other production file changes. `useConfirm.js` and `ConfirmDialog.jsx` are
unchanged — `pending.message` already accepts a composed string, which is all
this feature needs.

## 2. Layering (`architecture.md` §3)

Everything lives in `frontend/src/hooks` — the SPA's one layer for
view-state + API orchestration. No `domain/` addition: there is no client
domain layer for this app in the `planner_core` sense, and nothing here is
logic the way §1.1 uses the term (the branch is "which message did the
server send", not a decision).

## 3. Sequencing the two confirmations (R1, R3, R4)

`useLibrary` already owns one `confirm = useConfirm()` instance for the
plain "¿Eliminar esta receta...?" gate (R18, existing). `useConfirm`'s
`pending` is a single `{ message, onConfirm } | null` — `ConfirmDialog`
renders exactly one dialog. The two confirmations are never live at once (the
cascade warning only exists because the *first* confirmation's resulting
`DELETE` was rejected), so they can share that one instance instead of
needing a second `useConfirm()`:

```javascript
const remove = useCallback(
  (recipeId) => {
    confirm.requestConfirm(MESSAGES.CONFIRM_REMOVE_LIBRARY_RECIPE, async () => {
      try {
        await deleteRecipe(recipeId, { confirmCascade: false });
      } catch (err) {
        if (err instanceof ApiError && err.code === 'PIN_RULES_AFFECTED') {
          // R1, R2: re-arm the same confirm instance with the cascade prompt.
          confirm.requestConfirm(composeCascadeMessage(err.details?.pins ?? []), async () => {
            try {
              await deleteRecipe(recipeId, { confirmCascade: true }); // R3
            } catch (retryErr) {
              setError(toDetail(retryErr)); // R7 fallback, same path as any other failure
            }
          });
        } else {
          setError(toDetail(err)); // R7
        }
      }
    });
  },
  [confirm, picker],
);
```

`deleteRecipe` factors the existing marker/refetch body (`apiFetch` DELETE +
`picker.applyMutationMarker` + `picker.refetchNow()` + `setError(null)`) out
of the current inline callback so both the first attempt and the cascade
retry share it — the only difference is the query string.

This works because `useConfirm.confirm()` calls `pending.onConfirm()` without
awaiting it, then synchronously clears `pending`. The cascade re-arm happens
later, inside the still-running async `onConfirm`, after `pending` has
already been reset to `null` — so it lands cleanly as a fresh dialog rather
than racing the reset. `useConfirm.js` itself needs no change for this.

## 4. Retry request and pins rendering (R2, R3)

Retry URL: `` `/v1/library/recipes/${recipeId}?confirmCascade=true` `` —
literally the plain DELETE URL plus the query flag `rest_api_contract.md`
§3.4 defines. Assembling it is the one piece of "logic" R5 allows.

Pin rendering reuses `DAY_LABELS`/`SLOT_LABELS` from `domain/labels.js`
(already imported by `useRules.js` for the same `{day, slot}` shape) through
a small local helper, not a cross-hook import (see §7 rejected alternatives):

```javascript
function formatPin(pin) {
  return `${DAY_LABELS[pin.day]} · ${SLOT_LABELS[pin.slot]}`;
}

function composeCascadeMessage(pins) {
  const list = pins.map(formatPin).join(', ');
  return `${MESSAGES.LIBRARY_REMOVE_PIN_CASCADE_WARNING} ${list}. ${MESSAGES.LIBRARY_REMOVE_PIN_CASCADE_CONFIRM}`;
}
```

New `es-ES.js` keys (fixed Spanish prose only — no inline string in the
hook, `R15`/`FR-UX-01`/`FR-UX-03`), following the `RULES_CONFLICT_PREFIX`
prefix-plus-composed-list shape already established for `useRules.js`:

```javascript
LIBRARY_REMOVE_PIN_CASCADE_WARNING: 'Esta receta está fijada por una regla en:',
LIBRARY_REMOVE_PIN_CASCADE_CONFIRM: '¿Eliminarla igualmente? También se eliminará esa regla.',
```

## 5. Rules-view propagation is out of scope for new code

Acceptance criterion 4 says the item disappears "from both the library and
rules views". The library half is R6 (this feature's own refetch, same
pattern `remove` already uses today). The rules half needs **no new code**:
`RulesView`/`useRules.js` already polls `GET /v1/rules` on its own interval
(`FR-RT-02`, owned and tested by feature 26 `realtime_channel_*`, `done`).
Once the server-side cascade removes the pin row, that poll's next cycle
returns a rule list without it — the same mechanism that already makes any
other user's rule edit show up. Wiring `useLibrary` to also refetch
`useRules`'s poll would be new cross-view coupling this feature does not
need and `architecture.md` §1.1 does not ask for; it is not built, and the
Level-5 test suite (§6) does not re-test feature 26's polling contract.

## 6. Test strategy

New file `frontend/tests/hooks/useLibrary.pinCascade.test.js`, following the
real-`usePolling`-plus-faked-`fetch` pattern already used in
`useLibrary.mutationVisibility.test.js` (a `fakeLibraryServer` closure) so
the marker/refetch interaction is exercised for real, not mocked away:

- First `DELETE /v1/library/recipes/r-1` (no query) → `409`
  `{ code: 'PIN_RULES_AFFECTED', details: { pins: [{ day: 7, slot: 1 }] } }`.
  Confirming the plain removal opens the second dialog; its message contains
  the rendered day/slot text (R1, R2).
- Confirming the second dialog re-issues `DELETE` with
  `?confirmCascade=true` on the query string; the fake server then answers
  `204` and the recipe is gone from `result.current.recipes` after the poll
  settles (R3, R6).
- Cancelling the second dialog: assert `fetch` was called exactly once for
  `DELETE` (no `confirmCascade` retry) and the recipe is still present (R4).
- A `DELETE` rejected with a different code (e.g. `409 DUPLICATE`, or any
  existing non-cascade rejection) still sets `error` to `err.detail`
  verbatim, unchanged from `useLibrary.test.js`'s existing R15 case — the
  regression guard for R7.

Rules-view propagation is intentionally not asserted here (§5) — it is
already covered by feature 26's own polling tests and requires no code this
feature adds.

## 7. Rejected alternatives

**A second, independent `useConfirm()` instance for the cascade warning.**
Rejected: `ConfirmDialog` renders exactly one `pending` at a time, so a
second live instance would force the app shell to arbitrate which of two
dialogs to show — unnecessary, since the cascade dialog only ever appears
after the first one's `onConfirm` has already run and been cleared (§3). One
instance, re-armed, keeps `ConfirmDialog`'s `pending: object | null` contract
exactly as-is.

**Extending `ConfirmDialog`/`useConfirm` with a structured "details list"
prop to render day/slot rows instead of composing plain text.** Rejected as
over-general for a single caller: `pending.message` is already a plain
string everywhere else (including `RulesView`'s existing conflict list via
`RULES_CONFLICT_PREFIX`), and the acceptance criteria call for reusing
`useConfirm.js`/`ConfirmDialog.jsx` as they are, not adding new props to
them.

**Importing `useRules.js`'s `describeRule` to format the pins instead of a
local `formatPin`.** Both produce the same `"<day> · <slot>"` string from a
`{day, slot}` shape, but `describeRule` dispatches on a `rule.type`
`useLibrary` never has (`categoryCount`/`pin`/`disabledDay`) and pulls in
`CATEGORY_LABELS` this feature does not need. A three-line local helper using
the same `DAY_LABELS`/`SLOT_LABELS` avoids a cross-hook import for one line
of formatting logic.
