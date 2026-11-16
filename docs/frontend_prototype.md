# Frontend prototype — what it is and what we can use

## 0. Provenance

`prototypes/wireframe/Sobremesa.dc.html` + `prototypes/wireframe/support.js`,
added by the owner 2026-08-16 and analysed the same day. *(Originally dropped in
`frontend/src/`, then moved to `frontend/wireframe/` during that session. Moved
again to `prototypes/wireframe/` on 2026-08-17 — see §0.1.)*

### 0.1 Why it lives outside `frontend/`

`frontend/` is the SPA's **own toolchain root** (`AGENTS.md` §2; feature 1
`project_scaffold` acceptance). Anything under it is inside the glob reach of
every tool that root will acquire — linter, type checker, bundler, test runner —
and each would have needed its own exclusion for a directory that must never
ship. `prototypes/` puts that beyond configuration: the wireframe is a
**specification input**, and it now sits where it cannot be swept into a build.

It is **read-only reference material**. Do not edit it (`support.js` is a
generated artifact whose build step does not exist in this repository), do not
lint it, do not port it.

**Generated with Claude design** (the "dc" / design-component format — hence the
`.dc.html` extension). It is a **design prototype**, not application code, and it
was never intended as one.

- **`Sobremesa.dc.html`** (1,300 lines) — the whole product in one file: a
  template in a custom DSL (`<x-dc>`, `<sc-if>`, `<sc-for>`, `{{ }}` bindings —
  71 conditionals, 49 loops, 628 bindings) plus an embedded
  `<script type="text/x-dc">` carrying seeded mock state and ~80 handlers.
- **`support.js`** (1,658 lines) — **a generated build artifact.** Its first line
  reads *"GENERATED from dc-runtime/src/*.ts — do not edit."* At runtime it
  fetches React 18.3.1 UMD and Babel standalone **from the unpkg CDN**, then
  renders the DSL through them.

**Neither file is editable source and neither can be evolved into the SPA.**
`support.js` is somebody else's compiled runtime; the HTML is a single file of
inline styles with no components, no modules, no build step and no tests.

> **This did not decide architecture P7** — that the prototype runtime renders
> via React is an implementation detail *of the prototype tool*. **P7 was closed
> separately by the human on 2026-08-17** (idiomatic React: function components,
> hooks, JSX; Vite; Vitest — `docs/architecture.md` §1.1). The "DC" half was
> never obtainable: it is Claude Design's internal runtime, not a framework.
> Feature 20 `frontend_spa` has since been built and is `done`.

---

## 1. Verdict

| | |
|---|---|
| **Reusable as code** | **~0%.** Nothing ships. |
| **Reusable as specification** | **High.** It is the most precise statement of intended UI behaviour the project has. |
| **Reusable as visual design** | **High**, with extraction work — the design language is coherent and complete. |
| **Safe to copy from directly** | **No.** It contradicts eleven frozen requirements (§4). |

Treat it as **an executable wireframe**: read it, mine it, do not port it.

---

## 2. What is genuinely valuable

### 2.1 Complete screen inventory — matches the requirements exactly

Nine screens, all in Castilian Spanish (`FR-UX-01`, `FR-UX-03`):

`Login` · `Nueva contraseña` · `Menú semanal` · `Biblioteca` ·
`Lista de la compra` · `Reglas` · `Resumen` · `Historial` · `Administración`

That is a one-to-one match with the product areas in `docs/requirements.md`. No
screen is missing and none is invented.

### 2.2 Two concrete vocabularies the specs are explicitly waiting for

Both are listed in `feature_list.json` as *"concrete values proposed in
design.md"* — the prototype supplies a first draft for each.

**Ingredient categories** (feature 6, `FR-RULE-04`, G-63/G-69) — matches the
requirement's own example set exactly:

```
carne · pescado · legumbres · vegetariano · carbohidratos
```

**Unit list** (feature 3, `FR-SHOP-03`/`FR-LIB-05`, G-39/G-48):

```
g · kg · ml · L · ud · lomos · dientes · hoja · cda · cdta
manojo · paquete · rollo · al gusto
```

⚠ Review before adopting. `lomos` (fillets) and `hoja` (leaf) are
ingredient-specific rather than general units, and `al gusto` ("to taste") is not
a quantity at all — it is a null-quantity sentinel, which has consequences for
aggregation (`FR-SHOP-03` merges on name + unit, and two "al gusto" rows cannot
be summed). Decide deliberately rather than inheriting.

### 2.3 Behaviour correctly encoded — free specification detail

| Area | What the prototype gets right |
|---|---|
| Password policy | "Mínimo 10 caracteres, hasta 64. Sin obligación de mayúsculas, números ni símbolos, y sin caducidad. Se rechazan las contraseñas más comunes y filtradas, **también en castellano**." — `FR-AUTH-15` and G-60, verbatim |
| Set-password flow | Forced on first login and after admin reset, with a cancel path (`FR-AUTH-10`) |
| Brute-force lockout | `loginFails` / `lockedUntil` (`NFR-SEC-04`) |
| Two live weeks | `cur` / `next`, both fully featured, ISO week numbers and Monday–Sunday ranges (`FR-MENU-01`, `-02`, `FR-UX-06`) |
| Today-onward scoping | `todayIdx` gates the current week in aggregation (`FR-SHOP-05`, G-45) |
| Slot model | Per day: `Comida` / `Cena`, each a candidate list plus one `defId` (`FR-MENU-03`) |
| Three rule types | count / pin / disable — exactly `FR-RULE-04` |
| Rule effects rendered | Pinned Sunday lunch, disabled Saturday dinner shown in the grid |
| Per-run override | `overrideRules` separate from shared `rules` (`FR-RULE-05`, G-06) |
| AI preview lifecycle | accept / discard / regenerate, per-slot retry, nothing persisted until accepted (`FR-AI-10`, `FR-AI-12`) |
| Servings in prompts | `servings: 4` (`FR-AI-13`, G-64) |
| Archive | Reverse-chronological, with a `cold` flag and a `pastRestoring` state (`FR-ARCH-03`, `-04`) |
| Real-time | Offline banner, reconnect toast, `editingBy` presence (`FR-RT-03`) |
| Responsive | Mobile/desktop toggle (`FR-UX-02`) |
| Confirmations | Destructive actions gated behind `askConfirm` (`FR-UX-04`) |

The ~80 handler names are themselves a use-case inventory
(`makeDefinitive`, `clearDefinitive`, `acceptPreview`, `do_rollover`,
`addPinRule`, `retrySlot`…) and map cleanly onto the tier-1 features.

### 2.4 A complete, coherent design language

Worth extracting into design tokens rather than re-inventing:

- **Palette** — paper/surface/ink scales plus four semantic accents
  (`--terra` green, `--olive`, `--aub` purple for AI, `--honey`), all already
  expressed as CSS custom properties on one root element.
- **Type** — Baloo 2 (headings), Nunito (body), DM Mono (labels/metadata).
  ⚠ Loaded from Google Fonts; self-host for `NFR-SEC-03` and offline behaviour.
- **Motion** — seven named keyframes (`toastIn`, `sheetIn`, `popIn`, `shimmer`…).
- **Idioms** — pill badges, dashed-border empty states, bottom sheets on mobile,
  toast stack, skeleton shimmer.

The colour choice for AI content (`--aub` purple, consistently applied to the
`IA` badge and generation buttons) is a genuinely good decision worth keeping:
it makes AI-authored content scannable at a glance.

> ⚠ **Colour lifts. Type and spacing must not.** The 18 colour custom properties
> sit on one line (`Sobremesa.dc.html:33`) and can be copied verbatim. The rest of
> the visual system was never tokenised — it is inline literals, and it has
> already drifted:
>
> | Property | Distinct values in the file |
> |---|---|
> | `font-size` | **24** — including `10.5px`, `11.5px`, `12.5px`, `13.5px`, `14.5px`, `15.5px` |
> | `padding` | **91** |
> | `border-radius` | 19 |
> | `gap` | 15 |
>
> Twenty-four font sizes in half-pixel steps is not a type scale. Copying those
> numbers into `src/tokens/` would bake the drift into the exact module
> `docs/conventions.md` created to prevent it ("forty slightly different greys
> within a week"). **Design them down to a real scale — roughly six sizes and six
> spacings — reading the prototype for intent, not for values.**

---

## 3. What cannot be reused

| Blocker | Detail |
|---|---|
| **CDN dependency at runtime** | `support.js` fetches React and Babel from unpkg on load. No offline, no integrity pinning, no bundling. Fails `NFR-SEC-03` posture and cannot be deployed as-is. |
| **Generated runtime** | `support.js` is marked *do not edit* and is rebuilt from a toolchain we do not have. |
| **Not a component model** | One 1,300-line file. Every style is inline; there is no reuse boundary, so the container/presentational split in `docs/conventions.md` has nothing to attach to. |
| **Custom DSL** | `<sc-if>` / `<sc-for>` / `{{ }}` is the prototype tool's template language. It is not JSX, Vue, Svelte or anything with a future here. |
| **Mock state is the app** | All ~80 handlers mutate local component state. There is no HTTP layer, no error handling, no loading states beyond cosmetic ones. |
| **No tests** | `frontend/tests/` contains only `.gitkeep`. |

---

## 4. ⚠ Where it contradicts the frozen requirements

**This is the most important section.** The prototype encodes an **earlier state
of the requirements** — it predates or ignores the cuts made in Parts I–O. Eleven
divergences, clustered precisely on the areas that were most heavily revised.

**Do not copy these behaviours. Where the prototype and `docs/requirements.md`
disagree, the requirements win.**

### 4.1 Recipes carry three removed attributes

`FR-LIB-03` is explicit: *"No cuisine, difficulty, or nutritional (kcal)
attributes are stored."*

The prototype's recipe constructor is
`R(name, cat, cuisine, diff, time, kcal, author, …)` — it stores **`cuisine`**,
**`diff`** and **`kcal`**, all removed by **G-68** and **G-36**.

### 4.2 The library offers removed filters

`FR-LIB-04`: *"No other attribute filters are offered."* — name search plus the
category filter, nothing else.

The prototype carries six filter states: `libFilterCuisine`, `libFilterDiff`,
`addLibFilterCuisine`, `addLibFilterDiff`, `aiRefFilterCuisine`,
`aiRefFilterDiff`, `pinCuisineFilter`, `pinDiffFilter` — cuisine and difficulty
filters in the library view, the add flow, the AI reference picker and the pin
picker.

### 4.3 It records who made a meal definitive

`defBy` is stored on every slot and rendered. That is **`FR-SUM-02`, removed by
G-79** — promotion attribution is out of MVP scope. The summary shows the meal's
own author (`añadidoPor`, `FR-CAND-04`) and nothing else.

### 4.4 The shopping list carries four removed provenance attributes

This is the worst cluster. `S(name, unit, qty, auto, checked, wk)` produces items
with:

| Prototype attribute | Status |
|---|---|
| `auto` | Auto/manual marker — **removed by G-72** |
| `edited` | Manual-override state — **removed by G-72** |
| `weeks: ['cur','next']` | Per-item week attribution — **removed by G-73** |
| `qtyChanged` | Updated-since-checked flag — **removed by G-77** (supersedes G-44) |

A shopping item is **a name, a quantity, a unit and a checkbox.** Nothing else.

### 4.5 Re-sync writes to checked items — the single most-revised rule in the project

The prototype's `autoSync` contains:

```js
if(old){ const changed = old.checked && old.qty!==qty && !old.edited;
         out.push({...old, qty: old.edited?old.qty:qty, ...}) }
```

It **updates the quantity of a checked item** and flags it. **G-77 forbids this
outright**: re-sync never writes to a checked item at all — not its state, not
its quantity. Per normalized name + unit it computes the **outstanding** amount
(required minus what checked items already carry) and writes that to the matching
**unchecked** item, creating one if none exists.

Buy 500 g of rice, requirement rises to 800 g → the checked `arroz 500 g` is
untouched and a **new unchecked `arroz 300 g`** appears. The remainder, not the
gross amount — a user shown 800 after buying 500 would buy 800 more.

This rule cost two freeze lifts (Parts J and M) and four gaps to settle. The
prototype implements the superseded version. **Feature 8's acceptance criteria
are the authority.**

### 4.6 It displays a per-user AI counter

`aiUsed: 3, aiCap: 10`. **G-70 removed the per-user counter**: the €50/month cap
is **global**, enforced by AWS cost tooling, and **the application stores no
counter**. There is nothing to display.

---

## 5. How to use it

1. **Do not port it.** No file here becomes a source file.
2. **Read it before writing any spec for a UI-facing feature.** It resolves
   layout and interaction questions faster than prose.
3. **Extract the design language first** — palette, type scale, spacing, motion —
   into real tokens, once P7 is decided.
4. **Cross-check every behaviour against `docs/requirements.md` before
   implementing it**, and specifically against §4 above.
5. **Keep it as reference material.** It is the only artifact showing the whole
   product working end to end.

**P7 is decided (2026-08-17)**, and the prototype has been re-expressed as React
components with a real toolchain: feature 20 `frontend_spa`, `done`, in
`frontend/`.

---

## 6. Follow-ups for the owner

Not blocking; recorded so they are not lost.

1. ~~**P7 is still open.**~~ **CLOSED 2026-08-17** — idiomatic React, Vite,
   Vitest (`docs/architecture.md` §1.1). Note what the prototype supplies and
   what it must not: the **18 colour tokens** on line 33 lift cleanly, but the
   **type and spacing scales must not be copied** — 24 distinct `font-size`
   values with half-pixel steps and 91 distinct `padding` values are drift, not
   a system, and lifting them would defeat the tokens module.
2. ~~**The unit list needs a decision** on `al gusto`, `lomos` and `hoja` (§2.2).~~
   **Settled** — the code ships `g`, `ml`, `unit` (`planner_core.domain.units`).
3. ~~**The category list can be adopted as-is** if you are happy with the five
   values — it matches `FR-RULE-04`'s own example set.~~ **Settled** — six
   categories (`planner_core.domain.ingredient_category`).
4. **These two files are outside every quality gate.** `init.sh`
   ignores them and will keep ignoring them; they carry no lint, type or test
   obligation. That is correct for reference material — noted so their absence
   from the gates is not later read as a hole.
