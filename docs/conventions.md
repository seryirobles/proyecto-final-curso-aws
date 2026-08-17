# Code conventions

> Extreme homogeneity.

## Language policy (read this first)

| What | Language |
|---|---|
| Identifiers, function names, module names | English |
| Comments, docstrings, type names | English |
| Docs, specs, `progress/`, commit messages, PR bodies | English |
| **User-facing application strings** | **Castilian Spanish (es-ES)** |
| AI-generated recipe content | **Castilian Spanish** (`FR-AI-07`) |

`FR-UX-03` requires *all* texts — validation, error and system messages
included — plus date and number formats to follow es-ES conventions. To keep
that verifiable, **every user-facing string lives in one messages module**.
No Spanish string literals scattered through handlers or domain code.

```python
# good
raise InvalidLimit(messages.SHOPPING_QUANTITY_MUST_BE_POSITIVE)

# bad — untestable, unfindable, and it will leak English on the day it breaks
raise ValueError("quantity must be positive")
```

## Python style

- **Version:** Python 3.12 (pinned in `pyproject.toml`; confirm against the
  Lambda runtime once §2 P6 of `docs/architecture.md` is decided).
- **Formatting and linting:** `ruff format` + `ruff check`. Line length 100.
- **Typing:** `mypy` in strict mode. Every public function is fully annotated.
  No bare `Any` without an inline justification comment.
- **Imports:** stdlib first, then third-party, then local. One module per line.
  `ruff` enforces the ordering — do not hand-sort.
- **Strings:** double quotes `"..."`. f-strings for interpolation, never
  `.format()` or `%`.
- **Dataclasses:** domain entities are `@dataclass(frozen=True)`. Mutating means
  constructing a new instance.

## Naming

| Kind | Convention | Example |
|---|---|---|
| Modules | `snake_case` | `shopping_list.py` |
| Classes | `PascalCase` | `WeekPlan` |
| Functions / variables | `snake_case` | `aggregate_ingredients` |
| Constants | `UPPER_SNAKE` | `DEFAULT_SERVINGS` |
| Private | `_` prefix | `_normalize_name` |
| Ports (interfaces) | `PascalCase` + role noun | `RecipeRepository`, `Clock` |
| Fakes in tests | `Fake` + port name | `FakeRecipeRepository` |

## File structure

Every backend module opens with:

```python
"""One line describing the module's purpose."""

from __future__ import annotations

import json
from datetime import date

from planner_core.domain.recipe import Recipe
```

Imports use the **distribution package name**, never a path-relative `src.`
prefix: `from planner_core.domain...`, `from planner_api.wiring...`. The `src/`
directory is a packaging layout detail (src-layout), not an import root.

## Error handling

Domain exceptions live next to the domain they belong to:

```python
class PlannerError(Exception):
    """Base class for domain errors."""


class RecipeNotFound(PlannerError):
    """Raised when a recipe id does not resolve."""
```

Rules:

- Functions that can fail **raise**. They never return `None` to signal failure.
- The Lambda handler layer catches domain exceptions and maps them to the API
  error format. Stack traces never reach the user.
- Never catch bare `Exception` outside the handler boundary.

## Tests

- `pytest`. A test module per source module, inside the same workspace member:
  `backend/core/tests/domain/test_calendar.py`, `backend/lambda_api/tests/...`.
- Test names describe behaviour:
  `test_rollover_is_idempotent_when_rerun_after_partial_failure`.
- **Fakes, not mocks**, for our own ports. A `FakeClock` returning a fixed
  instant beats `unittest.mock.patch` on `datetime`. Fakes that implement a
  `core` port live in `backend/core/tests/support/` so contract tests can reuse
  them.
- `core` tests need no fake beyond a fixed clock. If a `core` test needs more,
  the layering is wrong.
- Every test maps to at least one `R<n>` of its spec, and through it to an
  `FR-*`. See `docs/verification.md`.
- **No test hits AWS or the network by default.** The one exception is
  explicitly marked (`@pytest.mark.aws`), excluded from `init.sh`, and opt-in —
  see the test tiers in `docs/verification.md`.

## Packaging conventions

- One import namespace per member: `planner_core`, `planner_api`, `planner_ai`.
- **`core` carries zero runtime dependencies.** Adding one is a design smell —
  it usually means adapter code leaked into `core`.
- A Lambda's own dependencies (AWS SDK, AI provider SDK) are declared in **that
  Lambda's** `pyproject.toml`, added only when its adapter is built (P1 / P4),
  and only through an approved `design.md`.
- `handler.py` is **thin**: parse the event, call one application use case, map
  the result or the domain exception to the transport format. No business logic.
- `wiring.py` is the **only** place that names concrete adapters, and it selects
  them **by environment** — never by an import-time side effect.

## Comments

By default, **do not write them**. They are allowed only to explain a non-obvious
*why* — a documented workaround, a subtle invariant, a requirement whose reason
is surprising. Names do the rest.

The exception worth making: when code implements a specific resolved gap, cite it.

```python
# Re-sync never writes to a checked item (G-77): the row records a purchase
# the user actually made. A later shortfall becomes its own unchecked item.
```

## Frontend conventions

The stack: a **single-page app** in **React**, written idiomatically — **function
components and hooks, with JSX**. Plain JavaScript, ESM, built with **Vite** and
tested with **Vitest**. Styling is **inline `style` objects** referencing shared
tokens. No Handlebars, no `.vue`, no string-template engine, no TypeScript.

> **Changed 2026-08-17 (formerly P7).** This section previously mandated a "JS
> logic class" and banned JSX. Both rules were reverse-engineered from the Claude
> Design prototype's runtime, not chosen on merit, and that runtime is not
> obtainable — see `docs/architecture.md` §1.1. **Everything below except the
> component model itself is unchanged.**

### Separation of concerns

The **hook / component** split is the frontend's version of the backend's
layering, and the reviewer treats it the same way.

| Piece | Holds | Never holds |
|---|---|---|
| **Custom hook** | State, event handlers, API calls, derived values | JSX, style values |
| **Component** | Structure and inline styles | Business rules, `fetch`, date maths |

- **One custom hook per view**, named `use<View>` (e.g. `useWeekPlanner`). It
  owns that view's state and returns its handlers.
- A component is a **pure function of its props**. Same props in, same markup
  out. A component that both fetches and renders is the thing this rule exists
  to prevent.
- No DOM lookups (`getElementById`, `querySelector`) scattered through handlers.
  Use refs; React owns the updates.
- No business logic in the frontend. Week boundaries, aggregation, rule
  satisfiability and scoping are **backend domain code** (`planner_core`). The
  SPA displays results — it never recomputes them. Two implementations of
  "which slots are in scope" is exactly how the current-week-from-today rule
  (`FR-AI-11`, `FR-SHOP-05`) silently diverges.

### Styling: inline CSS

- Styles live **on the element**, co-located with the markup that uses them.
- **No external stylesheet. No CSS framework. No CSS-in-JS library.**
- **Design tokens are centralised.** Colours, spacing, font sizes and the greyed
  -out treatment for checked shopping items (`FR-SHOP-08`) live in **one tokens
  module** and are referenced by name. Inline styling without shared tokens
  drifts into forty slightly different greys within a week.

```js
// good
style: { padding: tokens.space.md, color: tokens.color.textMuted }

// bad — unfindable, unchangeable, and it will drift
style: { padding: "12px", color: "#8a8a8a" }
```

#### The responsive constraint — read this before laying anything out

`FR-UX-02` requires desktop **and** mobile. Inline `style` attributes
**cannot express `@media` queries** — that is a structural limit of the
technique, not a preference. So responsiveness comes from layout, not
breakpoints:

- **Default: fluid-first.** Flexbox and Grid with `%`, `fr`, `minmax()`,
  `clamp()`, `min()`/`max()`. A fluid layout needs no breakpoint at all, and it
  is what the week grid (7 days × 2 slots) and the shopping list both want.
- **Where a genuine breakpoint is unavoidable** (e.g. the week grid collapsing
  to a day-by-day view on a narrow phone), a hook observes it with
  `window.matchMedia` and switches state. The breakpoint becomes a state value,
  and the component stays a pure function of its props.
- Breakpoint values are tokens, not literals scattered across views.

If a real `@media` block ever becomes unavoidable, that is a deviation from
"inline CSS" and needs an approved `design.md` — do not quietly add a
stylesheet.

### Castilian Spanish

Same rule as the backend, same reason (`FR-UX-01`, `FR-UX-03`):

- **Every user-facing string lives in one frontend messages module.** No
  Spanish literals inside components, handlers or markup.
- Dates and numbers are formatted with `Intl.DateTimeFormat` /
  `Intl.NumberFormat` pinned to **`"es-ES"`** — never manual `toString()`,
  never hand-built `dd/mm/yyyy`. Day names in the week grid come from `Intl`.
- The locale is a **constant**, not a runtime setting. This app has one locale;
  do not add an i18n framework.

### UI obligations the requirements impose

These are not optional polish — they are numbered requirements, and the
reviewer checks for them:

| Obligation | Requirement |
|---|---|
| Every week view, summary and week-scoped action is labelled with `current`/`next` **and** its Monday–Sunday date range | `FR-UX-06`, `G-57` |
| Destructive actions require explicit confirmation | `FR-UX-04`, `G-24` |
| Every view defines an **empty state** with guidance, and a **loading state** | `FR-UX-05`, `G-25` |
| AI operations show progress; whole-week runs show it **per slot**, with per-slot retry | `FR-AI-12`, `G-19` |
| Loss of the real-time connection is **visible**, with automatic reconnect | `FR-RT-03`, `G-22` |
| Checked shopping items render in a separate section below, greyed out | `FR-SHOP-08`, `G-32` |
| A recipe opens its detail view from **every** place a meal appears | `FR-MENU-05`, `G-14` |

Empty states are not an edge case here: every rollover produces an empty next
week, and day one produces an empty everything (`G-25`).

### Naming

| Kind | Convention | Example |
|---|---|---|
| Components | `PascalCase` + view noun | `WeekPlannerView`, `ShoppingListView` |
| Component files | `PascalCase` matching the component, `.jsx` | `WeekPlannerView.jsx` |
| Hooks | `use` + view noun, `.js` | `useWeekPlanner.js` |
| Methods / variables | `camelCase` | `handlePromoteCandidate` |
| Event handlers | `handle` + event | `handleToggleChecked` |
| Constants / tokens | `UPPER_SNAKE` or a `tokens.*` path | `DEFAULT_WEEK_VIEW` |
| Messages | `UPPER_SNAKE` in the messages module | `EMPTY_LIBRARY_HINT` |

### Testing

Frontend tests assert **behaviour through state**, not rendered pixels: given a
state, the expected markup shape and handler effects. No snapshot tests of whole
views — they break on every styling tweak and assert nothing about correctness.

The runner is **Vitest** (decided 2026-08-17). Test the **hook** directly wherever
the logic lives there — it is a plain function, and that is the cheapest place to
assert behaviour. Reach for rendering only when the assertion is genuinely about
what the component produces.

### Do not

- ❌ Do not add a CSS framework, component library or UI kit.
- ❌ Do not introduce a templating language (Handlebars, `.vue`, string
  templates). **JSX is not one of these** — it is React's own markup syntax and
  is the required form here.
- ❌ Do not duplicate backend domain logic in the client.
- ❌ Do not hardcode Spanish strings, dates or number formats in components.
- ❌ Do not add accessibility work beyond browser defaults — explicit scope
  exclusion (`FR-UX-07`, `G-62`).
- ❌ Do not add offline support, export/print, or presence indicators — all
  explicitly rejected (`docs/gaps_and_resolutions.md`, Part H).

### ~~Confirmed at the initial code drop~~ — resolved 2026-08-17

~~The human supplies the initial frontend code. Three things get pinned down from
it: the framework's identity and bootstrap idiom, the component/lifecycle API the
logic class extends, and the test runner. Until that code exists, no agent writes
frontend code.~~

**There is no code drop coming — it already happened, and it was the prototype in
`prototypes/wireframe/`.** All three items are now settled (`architecture.md`
§1.1): React with function components and hooks, bootstrapped by Vite, tested
with Vitest. There is no base class to extend — a component is a plain function.

`frontend_spa` (feature 20) remains `blocked`, but on **feature 16** alone: the
SPA needs the REST contract (P5). The stack no longer blocks it.
