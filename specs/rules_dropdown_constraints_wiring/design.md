# rules_dropdown_constraints_wiring — Design

> Feature 29 · read `requirements.md` first. Depends on feature 6
> `rules_model` (`planner_core/domain/rules.py`, closed) and feature 20
> `frontend_spa` (`RulesView.jsx` / `useRules.js`, closed). No
> `docs/architecture.md` §2 item is needed. No `docs/data_model.md` change is
> needed — nothing new is persisted; `availableOptions` is derived on every
> read, never stored.

## 1. HUMAN GATE — proposed `docs/rest_api_contract.md` shape (not yet edited)

**This is the stopping point `feature_list.json`'s acceptance criterion 1
names.** The shape below is a proposal for the owner to land in
`docs/rest_api_contract.md`; this spec does not edit that file, and no task
in `tasks.md` starts before it is edited there.

### 1.1 Response shape

`GET /v1/rules`'s existing row (`docs/rest_api_contract.md` line 151) gains a
second field on the same `200` body:

```jsonc
// GET /v1/rules  ->  200 OK,  ETag: "7"
{
  "rules": [ /* unchanged — categoryCount / pin / disabledDay, as today */ ],
  "availableOptions": {
    "maxCountByCategory": {
      "meat": 4, "fish": 6, "carbohydrate": 2,
      "legume": 6, "vegetable": 6, "eggs": 6
    },
    "daysAvailableForPin": [1, 2, 4, 6, 7],
    "daysAvailableToDisable": [2, 6]
  }
}
```

- **`maxCountByCategory`** — one entry per `IngredientCategory` member
  (all six, always present, even a category with no rule yet), value =
  `max_selectable_count(rule_set, category)`. `0` is a valid value: it means
  every slot is already claimed by other categories and this category
  cannot be added at all right now.
- **`daysAvailableForPin`** — `available_days_for_pin(rule_set)` verbatim: an
  ascending array of the `1..7` weekdays not disabled. Note this does **not**
  exclude a day that already carries one pin — a day can hold two pins (lunch
  and dinner), so both slots of an available day stay offerable.
- **`daysAvailableToDisable`** — `available_days_to_disable(rule_set)`
  verbatim: an ascending array of the `1..7` weekdays that are neither
  disabled nor already carrying a pin.
- No new error shape, no new status code. Same `304`-on-unchanged-marker
  behaviour as today — `availableOptions` is only computed when the marker
  changed and the full `200` payload is built.

### 1.2 Doc-edit shape (for the owner to apply verbatim)

Extend the "Rules" table's `GET /v1/rules` row semantics cell in
`docs/rest_api_contract.md` §2, and add a short §3.x example mirroring
§3.1–§3.3's style, with the JSON block above and the three bullet
definitions. No row is removed or renumbered.

---

## 2. What this feature does NOT do

No `planner_core/domain/` or `planner_core/application/` change. The three
functions this feature calls (`max_selectable_count`,
`available_days_for_pin`, `available_days_to_disable`) already exist,
unmodified, in `backend/core/src/planner_core/domain/rules.py` (feature 6).
`rule_editing.py`'s `save_rule`/`delete_rule` whole-set `UnsatisfiableRuleSet`
validation (feature 27) is untouched (R5, R12) — it remains the reactive
last line of defense for a race between two concurrent edits; this feature
only narrows what a single well-behaved client can submit before it ever
sends a request.

---

## 3. Layering (`docs/architecture.md` §3)

| Piece | Layer | Why |
|---|---|---|
| `encode_available_options(rule_set)` | `backend/lambda_api/src/planner_api/serialization.py` | Wire encoding at the api boundary, alongside the existing `encode_rule` — not domain, not application; it calls three domain functions and shapes their output as JSON. |
| `_list_rules` addition | `backend/lambda_api/src/planner_api/routing.py` | Routing/dispatch already reads `view.rule_set` for the `rules` array; this feature adds one more encoder call on the same value. |
| `categoryCountOptions`, `pinDayOptions`, `disabledDayOptions` derivation | `frontend/src/hooks/useRules.js` | Custom hook: "derived values" per `docs/conventions.md` § Frontend conventions' hook/component table. |
| Select rendering (three `<select>`s) | `frontend/src/components/RulesView.jsx` | Pure function of props — renders whatever list the hook hands it, computes nothing (R11). |

No `domain/` or `application/` file is created or modified — satisfies
`feature_list.json`'s "no new domain logic, this feature only wires it
through the API."

---

## 4. Signatures

### Backend — `planner_api/serialization.py`

```python
def encode_available_options(rule_set: RuleSet) -> dict[str, Any]:
    """R1-R4: one call per already-built pure function (rules_model, feature 6);
    no arithmetic of its own."""
    return {
        "maxCountByCategory": {
            category.value: max_selectable_count(rule_set, category)
            for category in IngredientCategory
        },
        "daysAvailableForPin": list(available_days_for_pin(rule_set)),
        "daysAvailableToDisable": list(available_days_to_disable(rule_set)),
    }
```

New imports in `serialization.py`: `IngredientCategory` (already imported
elsewhere in the api package), `max_selectable_count`,
`available_days_for_pin`, `available_days_to_disable` from
`planner_core.domain.rules`.

### Backend — `planner_api/routing.py`, `_list_rules`

```python
return RouteResult(
    200,
    {"rules": rules, "availableOptions": ser.encode_available_options(rule_set)},
    etag=quoted_etag(view.marker),
)
```

`rule_set` is `view.rule_set`, already bound in `_list_rules` today (line
574). One added import: `IngredientCategory` plus the three functions, all
already public in `planner_core.domain.rules`.

### Frontend — `frontend/src/hooks/useRules.js`

```js
const availableOptions = poll.data?.availableOptions ?? null;
const maxCountByCategory = availableOptions?.maxCountByCategory ?? {};
const daysAvailableForPin = availableOptions?.daysAvailableForPin ?? [];
const daysAvailableToDisable = availableOptions?.daysAvailableToDisable ?? [];

const categoryCountOptions = useMemo(() => {
  if (categoryCountDraft.category === '') return [];
  const max = maxCountByCategory[categoryCountDraft.category] ?? 0;
  return Array.from({ length: max }, (_, i) => i + 1);
}, [categoryCountDraft.category, maxCountByCategory]);

const pinDayOptions = useMemo(
  () => Object.entries(DAY_LABELS).filter(([day]) => daysAvailableForPin.includes(Number(day))),
  [daysAvailableForPin],
);

const disabledDayOptions = useMemo(
  () =>
    Object.entries(DAY_LABELS).filter(([day]) => daysAvailableToDisable.includes(Number(day))),
  [daysAvailableToDisable],
);
```

`setCategoryCountCategory` (R8) becomes:

```js
const setCategoryCountCategory = useCallback(
  (category) =>
    setCategoryCountDraft((current) => {
      const max = maxCountByCategory[category] ?? 0;
      const stillValid = current.count !== '' && Number(current.count) <= max;
      return { category, count: stillValid ? current.count : '' };
    }),
  [maxCountByCategory],
);
```

`RULE_COUNT_OPTIONS` is removed from `useRules.js` (no remaining caller after
`RulesView.jsx` switches to `categoryCountOptions`; confirmed by grep — its
only two call sites are `useRules.js` itself and `RulesView.jsx`).

### Frontend — `frontend/src/components/RulesView.jsx`

`RulesView` gains three new props — `categoryCountOptions`, `pinDayOptions`,
`disabledDayOptions` — replacing the count select's
`RULE_COUNT_OPTIONS.map(...)` and the pin/disabled-day selects'
`Object.entries(DAY_LABELS).map(...)`. Each new prop is an array of
`[value, label]` pairs (day selects) or plain numbers (count select), mapped
into `<option>` exactly as today. The category select (all six
`IngredientCategory` members) and the pin's slot select stay unconstrained —
neither is named in `feature_list.json`'s acceptance criterion 3, and
neither has a corresponding pure function in `rules.py`: every category is
always a legal *choice*, only some of its *counts* are; every slot is always
legal for an available day.

No new export, no new component file.

---

## 5. Rejected alternatives

**A. A new domain-level `AvailableOptions` dataclass bundling all three
computations, in `planner_core/domain/rules.py`.**
Rejected — `rules_model`'s own design (`specs/rules_model/design.md` §8,
rejected alternative E) already turned this down for the same reason: three
independent pure functions each answer one dropdown's question directly, and
a bundling type would need its own shape decision to save three calls a
caller (here, `encode_available_options`) already has to make anyway. Adding
it now, one feature later, would just be relitigating a closed call.

**Recompute `maxCountByCategory` etc. client-side from the `rules` array as
a fallback when `availableOptions` is momentarily absent (e.g. an older
cached poll response).**
Rejected. This is exactly the arithmetic `docs/architecture.md` §1.1
forbids duplicating in the client ("rule satisfiability lives in
`backend/core`... two implementations... silently diverge"), and it directly
contradicts R11. A missing/`null` `availableOptions` renders empty option
lists (R7's shape, generalized) rather than a silent local re-derivation.

**Attach `available_options` to `rule_editing.RulesView` /
`read_rules` (application layer) instead of computing it in
`planner_api/serialization.py` (api layer).**
Considered. `RulesView` (the application-layer dataclass, feature 27) is a
plausible home since it already enriches the raw `RuleSet` with
`pin_recipe_names`. Rejected here because no other caller of `read_rules`
needs available options — only the `GET /v1/rules` wire response does — and
`planner_core/application` is a closed, tested module (feature 27) this
feature's own acceptance criterion ("no new domain logic, this feature only
wires it through the API") reads as a reason to leave alone. Keeping the
composition in `serialization.py`, beside `encode_rule`, keeps the diff
exactly where the acceptance criterion says it belongs.

---

## 6. Boundary checks

- **`docs/architecture.md` §2 (pending, human-owned):** nothing here needs
  any of P1–P7; all are already decided.
- **§2.1 decide-in-a-spec items:** none touched. The ingredient-category list
  is reused unchanged from feature 4/6; no new value is proposed.
- **Frozen docs:** none modified by this spec or its implementation.
  `docs/rest_api_contract.md` is edited by the **owner**, per §1 above, as
  the explicit human gate — not by `spec_author` or `implementer`.
- **`docs/data_model.md`:** no change. `availableOptions` is computed fresh
  on every `GET /v1/rules`, from the same `RuleSet` read `rules` already
  comes from; nothing new is persisted, no new item type, no new access
  pattern.
- **User-facing strings:** none added. No new error, no new message key —
  the dropdowns simply render fewer `<option>`s; the existing
  `UNSATISFIABLE_RULE_SET` message and `RULES_CONFLICT_PREFIX` handling are
  untouched (R12).
- **Runtime dependencies:** none added, either side.
- **Requirements invented:** none. Every `R<n>` cites `FR-RULE-07`, the one
  id `feature_list.json`'s description names (`covers` is empty, matching
  feature 28's precedent — see `requirements.md`'s note).
