# single_recipe_generation — Design

> Feature 28 · read `requirements.md` first. Builds on features 11, 12, 16, 17,
> 20, 27. Sources: `docs/rest_api_contract.md` §3.5/§3.6/§4/§7 Q3,
> `docs/data_model.md` §2/§4.6, `specs/ai_lambda/design.md` §6/§9.1.
> No `architecture.md` §2 item is needed. No `data_model.md` change is needed.

## 1. Request shape (as reconciled into the contract; gaps Part AB, G-92)

Body of `POST /v1/generations` with `type: "recipe"` (whole-week keeps
`type: "week"`, the default). No `attempt` field (§7 Q3).

```jsonc
{ "type": "recipe",
  "target": { "kind": "slot", "weekId": "2026-W34", "day": 3, "slot": 1 },
            // or { "kind": "library" }  (FR-CAND-03: library authoring has no slot)
  "source": { "kind": "specification", "ingredients": ["lentejas"], "tools": ["olla"] }
            // or { "kind": "reference", "recipeId": "01J8…", "extraSpecifications": ["sin gluten"] } }
```

- `202` + `Location`, body `{ "generationId", "status": "pending" }` (no `targets`).
- `200` with `{ generationId, status, result }` on an idempotent hit (existing branch).
- `GET` `result` on success is the recipe in the **wire recipe shape** (the same
  JSON `POST .../candidates` takes as `recipe`), so the existing
  `source:"generation"` accept path (`_resolve_meal_source`) works unchanged.
  On failure: `status: "failed"`, `result` = `{ "error": { "code": <reason>, "message": <es-ES> } }`.
- Empty `ingredients` / `tools` reuse `MissingIngredients` / `MissingTools`
  (`422`, already in the error table) in the api use case (R17, R18).
- **Attempt derivation** (owner-approved): **probe** `n = 0, 1, 2 …`; key(n) =
  `single_recipe_key(request, n)`; the first `n` whose record is absent is fresh
  (`202`); a `pending`/`running` record at `n` is returned (`200`, retry /
  double click); a terminal record advances `n`. Uses only `AP26` (`GetItem`),
  no new item type. A failed generation is a terminal record, so "regenerate
  after failure" advances.
- **Concurrency (FR-AI-09 as written):** there is no per-slot lock. Two users
  may generate for the same slot at once; different specifications derive
  different keys and both run (R16). Only an identical in-flight request
  dedupes (R12).

## 2. Layering (`architecture.md` §3)

| Piece | Layer |
|---|---|
| `SingleRecipeRequest`, `SpecificationSource`, `ReferenceSource`, `single_recipe_key` | `domain/generation.py` |
| `submit_single_recipe` (probe loop, reference snapshot, enqueue) | `application/single_recipe_submission.py` |
| `run_single_recipe_generation` | `application/single_recipe_generation.py` |
| `GenerationQueue.submit_recipe`, `record_result` widening | `ports/generation_queue.py` |
| `_submit_generation` `type:"recipe"` branch, body parsing | `planner_api/routing.py`, `serialization.py` |
| SQS message `type`, parsing, dispatch | `planner_ai/message.py`, `handler.py` |
| recipe wire encoder (copy) | `planner_ai/serialization.py` |
| AI form, polling, preview UI | `frontend/src/hooks`, `components` |

## 3. Signatures

```python
@dataclass(frozen=True) class SpecificationSource: ingredients: tuple[str, ...]; tools: tuple[str, ...]
@dataclass(frozen=True) class ReferenceSource: recipe_id: str; extra_specifications: tuple[str, ...]
@dataclass(frozen=True) class SingleRecipeRequest:
    target: SlotRef | None            # None = library
    source: SpecificationSource | ReferenceSource

def single_recipe_key(request: SingleRecipeRequest, attempt: int) -> str: ...
    # sha256 of canonical JSON {"type":"recipe","scope","source",...,"attempt"}; lists sorted (R8)

def submit_single_recipe(request, *, queue, recipes, author, config) -> SingleRecipeOutcome
    # SingleRecipeOutcome(idempotency_key, attempt, stored: StoredGeneration | None)
def run_single_recipe_generation(idempotency_key, source_prompt_inputs, prompt_version_id,
    *, provider, queue: GenerationResultSink, gate) -> SingleRecipeRunOutcome
```

Port changes (the feature 27 reopen precedent, owner-confirmed):
`GenerationQueue.submit_recipe(idempotency_key, request, *, reference_recipe:
Recipe | None, prompt_version_id, author)` (same create-if-absent put +
`send_message` with `"type":"recipe"`); `record_result`'s third parameter
widens to `list[PerSlotResult] | Mapping[str, object]` (the adapter already
does `json.dumps`), so the success payload is the bare recipe dict, which the
accept path already decodes. Fakes and both adapters follow; the shared
contract suite is extended.

Prompt-version resolution reuses `resolve_active_prompt_version` (feature 24)
in the submit use case, before any write. The worker holds no
`RecipeRepository`: the api puts the reference recipe snapshot on the message
(same principle as `ai_lambda` §8). Exceptions reused: `RecipeNotFound`,
`MalformedRequest`, `MissingIngredients`, `MissingTools`,
`UnknownPromptVersion`; none added.

Double-click (R14): the adapter's `submit` sends the message even when the
conditional put loses, so two fast clicks may enqueue twice; `claim` makes the
second delivery a no-op (R21). No change needed, a test proves it.

Inherent to §7 Q3 (owner-accepted): a client that lost the response *after*
completion and re-POSTs derives attempt+1 and pays again; a retry dedupes only
while in flight.

## 4. Frontend

Replace `AiStubFields` (`RecipeAuthoringForm.jsx`) and the `canSubmit=false`
branch of `useRecipeAuthoring.js`: new `useAiGeneration` hook (submit, poll with its
own `setTimeout` loop (`usePolling` is ETag-based; contract §3.6 says this GET is
not conditional), preview/accept/discard/regenerate state) and a preview
component. Accept reuses the existing candidate `source:"generation"` POST, or
the library-recipe POST with the previewed body. Messages go in `es-ES.js`; the
`AI_GENERATION_UNAVAILABLE` stub notice is removed. No hashing or attempt logic
in the client (`architecture.md` §1.1).

## 5. Rejected alternatives

**A per-scope lock (marker item, `429`/`409`) for FR-AI-09.** Would reject a
second generation for a busy slot. Rejected by the owner: two people should be
able to generate for the same slot, and FR-AI-09 as written allows it; the lock
would also add an item type and access patterns for no requirement.

**Widening `submit` to take `GenerationRequest | SingleRecipeRequest`.** One
method. Rejected: `effective_rules` is required and meaningless for a recipe
request, and the union forces `isinstance` branching inside every adapter and
fake; a separate `submit_recipe` keeps each signature honest.

**Worker reads the reference recipe from the library.** Smaller message.
Rejected: it needs a `RecipeRepository` adapter copy in `planner_ai` (the copy
`ai_lambda` §7 accepted only for `WeekRepository`) and the recipe could change
between submit and run.

## 6. Test strategy

Domain: key determinism, order-insensitivity, attempt sensitivity, week-key
golden hash (R7-R10). Use cases with fakes: probe sequences (fresh, in flight,
terminal, discarded, failed, different-key concurrent) (R11-R16), worker
branches, gate off, claim lost, spy that `WeekRepository` is never touched
(R19-R27). Contract: the encoder in `planner_ai/serialization.py` equals
`planner_api` `encode_recipe` (parity, as for the week adapter copies);
`submit_recipe`/`record_result` on fake and moto. Routing: body validation
table (R1-R6, R17, R18, R28-R30). Frontend (Vitest): each of R31-R41 with
mocked fetch.

## 7. Docs: state

Already reconciled by the leader: `docs/rest_api_contract.md` §3.6 (new), §3.5,
§4, §7 Q3 and the L171 table row; `docs/gaps_and_resolutions.md` Part AB
(G-92); the ports note. `docs/data_model.md` needs **no change**: no new item
type, key format or access pattern (the probe uses `AP26`). `architecture.md`:
untouched. Nothing further for the owner to edit before implementation.

## 8. Remaining questions

None.
