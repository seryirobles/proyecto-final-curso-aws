# close-button-style — analysis

## Defect, one sentence

The "Cerrar" button that dismisses the recipe-authoring panel in the library is
rendered with **no `style` prop at all**, so it falls back to the browser's
default button chrome while every sibling control in the same panel is styled
off the shared token module.

## Reproduction

Automated, from the staged test (`issues/close-button-style/tests/`, copied to
its destination and deleted again):

```
cd frontend && npx vitest run tests/components/LibraryView.closeButton.test.jsx
```

- **Observed:** the close control's inline style is empty — every treatment
  property (`backgroundColor`, `color`, `border*`, `borderRadius`, `padding`,
  `fontWeight`) reads `""`, and `button.style.length === 0`. It is the only
  button in the open panel in that state.
- **Expected:** the shared secondary-button treatment, the same one
  `ShoppingListView`'s "Cancelar" carries when its form is open
  (`rgb(255, 254, 246)` background, `rgb(92, 106, 76)` text,
  `1px solid rgb(203, 208, 172)` border, `8px` radius, `4px 8px` padding,
  weight `600`).

Visually this is what the report describes: a grey, square, system-font button
under a panel of rounded, token-coloured ones.

## Root cause

`frontend/src/components/LibraryView.jsx:207`

```jsx
<button type="button" onClick={closeAuthoring}>
  {MESSAGES.RECIPE_DETAIL_CLOSE}
</button>
```

The element carries no `style`. This is the single site; the symptom surfaces
exactly where the cause is.

The control was missed by the styling pass that restyled this file:
`specs/frontend_spa/tasks.md` **T85** ("Style `LibraryView.jsx` /
`LibraryRecipePicker.jsx`", marked `[x]`) covered the card grid, the category
dot and the edit/remove icon buttons, and **T87** covered
`RecipeAuthoringForm.jsx`'s non-AI parts — the authoring panel's close button
sits in `LibraryView.jsx` between the two and was styled by neither.
`specs/frontend_spa/design.md` §10.6 lists the *only* deliberate exclusions for
that pass: the AI-tab stub (feature 28) and the archive screen. This button is
in neither list.

Standard violated: `docs/conventions.md` § *Frontend conventions* → *Styling:
inline CSS* ("Styles live **on the element**… Design tokens are centralised…
and are referenced by name"), restated as feature 20's acceptance criterion 1
in `feature_list.json` ("inline style objects off a shared tokens module").

## Requirement citation — read this before approving

No `FR-*`/`NFR-*` names button styling or visual consistency directly;
`FR-UX-01/03` cover language, `FR-UX-04/05/06` cover confirmation / empty
states / week labelling, `FR-UX-07` excludes accessibility work. Nothing in
`docs/gaps_and_resolutions.md` makes an unstyled control deliberate.

The closest frozen id is **`FR-UX-02`** (responsive website across a fixed
desktop/mobile browser matrix): a `<button>` with no style renders as the
user-agent default, which is precisely what differs across that matrix — Safari
on iOS, Chrome on Windows and Firefox each draw a different control, while a
token-styled button draws identically everywhere. This is not a new reading:
`specs/frontend_spa/design.md` §10.1 already cites `FR-UX-02` for exactly this
kind of design-language decision ("no single system stack fills both roles
consistently across `FR-UX-02`'s browser/OS matrix"), and §10.0 records that
the whole visual-design pass carries **no new `FR-*`/`R<n>`** because feature
20's approved acceptance criteria already bind it.

So the chain here is `FR-UX-02` → feature 20 acceptance criterion 1 →
`docs/conventions.md` styling rule → T85, not a direct requirement sentence.
**If that chain is rejected, the issue is a `spec_gap`, not a `defect`** — but
no frozen-doc lift is needed to fix it either way, since the behaviour is
already mandated by an approved spec artifact.

## Blast radius

A mechanical scan of every `<button>` opening tag in `frontend/src/**/*.jsx`
finds exactly **two** without a `style` prop:

| Site | Status |
|---|---|
| `LibraryView.jsx:207` ("Cerrar") | this issue |
| `RecipeAuthoringForm.jsx:284` (AI-tab stub submit) | **out of scope by decision** — `design.md` §10.6 / T87 keep the `ai` tab's stub untouched, feature 28's territory |

No other caller renders this close control: `closeAuthoring` is produced by
`useLibrary.js:68` and consumed only at `LibraryView.jsx:207`. The candidate
authoring flow reuses `RecipeAuthoringForm` but not this button.

**Correction (2026-09-23, scope extension).** The scan above was wrong about
the candidate flow. `MESSAGES.RECIPE_DETAIL_CLOSE` labels three buttons:

| Site | Status |
|---|---|
| `LibraryView.jsx:213` | fixed (E1-E3), now `{ ...secondaryButtonStyle, marginTop: tokens.space.sm }` |
| `CandidateAuthoring.jsx:23-25` | **unstyled** — plain `<button type="button" onClick={onClose}>`; the week view's "Añadir plato" panel (header comment, `:1-4`). Added as **E4/E5**. |
| `RecipeDetailView.jsx:98` | styled (`CloseButton` treatment, detail sheet); not reported, out of scope |

`CandidateAuthoring.jsx` postdates this triage (issue `add-dish-button-inert`,
same day), which is why the scan missed it. It is the likelier referent of
"recipe creation menu": the owner reported it still broken after E1-E3
landed. Reproduced by the staged `CandidateAuthoring.closeButton.test.jsx`
(E4 red, every treatment property `""`).

Regression risk of the fix is limited to the same element's click behaviour,
which `E3` pins.

## Severity

As reported: **low**. Cosmetic; no data, state or flow is affected.

## Classification

**`defect`** — code violates the approved styling standard for feature 20
(`docs/conventions.md` § *Frontend conventions*, acceptance criterion 1,
`specs/frontend_spa/design.md` §10 / T85), traced to `FR-UX-02` through the
chain recorded above. See the caveat in *Requirement citation*.
