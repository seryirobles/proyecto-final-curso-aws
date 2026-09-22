# close-button-style — plan

## Expected behaviour

- **E1** — The close control of the library recipe-authoring panel SHALL render
  with the shared secondary-button treatment exported by
  `frontend/src/tokens/controlStyles.js` (`secondaryButtonStyle`): its
  background, text colour, border, border-radius, padding and font weight equal
  that object's resolved values.
  *Implements:* `FR-UX-02` (via feature 20 acceptance criterion 1 and
  `docs/conventions.md` § *Frontend conventions* → *Styling*; see
  `analysis.md` § *Requirement citation*).
- **E2** — `LibraryView` SHALL render no `<button>` without an inline style
  while the authoring panel is open on the `scratch` method.
  *Implements:* `FR-UX-02` (same chain).
- **E3** — The close control SHALL call `closeAuthoring` exactly once when
  clicked.
  *Implements:* `FR-LIB-02`.

## Fix design

**One file, one element.** Layer: frontend presentational component
(`docs/architecture.md` §3; `specs/frontend_spa/design.md` §130 — "components
own `style` objects off `tokens`").

`frontend/src/components/LibraryView.jsx`

1. Add the import already used by `ShoppingListView`/`AccountRow`:
   `import { secondaryButtonStyle } from '../tokens/controlStyles.js';`
2. Apply it at line 207:

```jsx
<button
  type="button"
  onClick={closeAuthoring}
  style={{ ...secondaryButtonStyle, marginTop: tokens.space.sm }}
>
  {MESSAGES.RECIPE_DETAIL_CLOSE}
</button>
```

The `marginTop` spread mirrors the existing pattern at
`ShoppingListView.jsx:191` (`{ ...primaryButtonStyle(false), marginTop:
tokens.space.sm }`) and separates the button from the panel it closes; the
staged tests assert the treatment properties only, so the extra margin is
allowed but not required. No new token, no new style object, no new
dependency, no hook change.

Precedent for choosing the *secondary* variant: `ShoppingListView.jsx:140`
styles its "Cancelar" — the dismiss half of the same save/cancel pair inside an
open form — with `secondaryButtonStyle`. The authoring panel's submit is the
primary, so its dismiss is the secondary.

### Rejected alternatives

1. **Reuse `RecipeDetailView`'s `CloseButton` treatment** (`surface2`
   background, `fontSize.xs`, an `×` icon). Rejected: that treatment belongs to
   the detail sheet's corner dismiss and the library card's row actions, not to
   a form-dismiss button, and copying its literal object into `LibraryView`
   would add a fourth local one-off button style — the drift
   `docs/conventions.md` § *Styling* exists to prevent.
2. **Move the close control into `RecipeAuthoringForm`, beside the submit
   button.** Rejected: that component is shared with the candidate authoring
   flow, so it means a new prop and a behaviour change in a second screen — a
   refactor, not the smallest fix, and layout is not what the report is about.

## Test plan

One staged file, all three `E<n>` in it.

| Staged | Destination |
|---|---|
| `issues/close-button-style/tests/frontend/tests/components/LibraryView.closeButton.test.jsx` | `frontend/tests/components/LibraryView.closeButton.test.jsx` |

| Test | Covers | Kind |
|---|---|---|
| `carries the shared secondary-button treatment (E1)` | E1 | **reproduction** |
| `leaves no button unstyled while the authoring panel is open (E2)` | E2 | reproduction / drift guard |
| `still calls closeAuthoring when clicked (E3)` | E3 | regression |

The treatment is resolved from `secondaryButtonStyle` through a detached probe
element, so the assertion is about the treatment the app defines, not about how
a component imports it: any application of those values passes, and extra
decoration (margin, icon layout) is not asserted.

### Red recorded at triage (2026-09-21)

Copied to the destination, run, then deleted:

```
cd frontend && npx vitest run tests/components/LibraryView.closeButton.test.jsx
Tests  2 failed | 1 passed (3)
```

- **E1 — FAILS.** Expected `{backgroundColor: "rgb(255, 254, 246)", borderColor:
  "rgb(203, 208, 172)", borderRadius: "8px", borderStyle: "solid", borderWidth:
  "1px", color: "rgb(92, 106, 76)", fontWeight: "600", padding: "4px 8px"}`,
  received every property `""` — the element has no inline style, which is the
  root cause in `analysis.md`.
- **E2 — FAILS.** `expected [ 'Cerrar' ] to deeply equal []` — exactly one
  unstyled button in the open panel, and it is the reported one.
- **E3 — PASSES today**, as expected: the click behaviour is not broken and must
  survive the restyle.

A throwaway probe (deleted) confirmed the same comparison goes **green** when
`secondaryButtonStyle` is applied through React, both plain and spread with an
extra `marginTop` — so the staged assertions are red for the stated reason, not
for a technique artefact.

`npx prettier --check` and `npx eslint` both pass on the staged file, so it will
not turn `./init.sh` red on style once moved.
