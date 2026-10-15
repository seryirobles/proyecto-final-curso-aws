# Issue 18 — AI-only week returns the same dish in every slot

**Defect:** every AI slot of a week run gets the same prompt, which has no field for dishes already chosen, so the model returns its most likely dish and only the protein changes.

## Root cause
- `week_generation.py:158-171`: `_fill_slots` builds one `CategoryPrompt` per run and sends it unchanged to every AI slot.
- `ai_prompt.py:248-253`: `CategoryPrompt` has no field for dishes to avoid, so `bedrock.py:33-62` (`_render`) has nothing to send.
- Prompt v4 says "vary protein across the household's meals", but the model never sees those meals.
- Temperature and topP are unset and there is no seed.
- Slots run sequentially in one worker call, not in parallel.

## Reproduction
Not re-run against the live model. The offline spy tests show identical, name-free prompts for every slot.

## Requirement check — `spec_gap`
No FR/NFR requires AI dishes of a week to differ. `FR-AI-06` only requires the prompt to ask for varied protein. `G-94`/R8 (no repeated name) covers library picks only. Lifted by owner: Part AE / `G-95` (`docs/gaps_and_resolutions.md`).

## Blast radius (owner ruling: general fix)
- Per-slot retry (`run_slot_retry` → `_fill_slots`): same cause.
- `mix`: AI slots are not told the library picks' names either.
- Category needs: earlier AI slots never reduce the needs given to later ones, so a category rule can overfill (`FR-AI-04`, `FR-AI-11`, `G-71`). Read from the code, not tested against the model.
- Single-recipe generation: separate path, not affected.

## Options
- (a) Name the week's meals and the run's earlier dishes in each AI slot's prompt. No extra call; keeps per-slot progress and retry. Needs prompt v5 (`FR-AI-14`). **Chosen (owner, alone).**
- (b) One call for several slots: breaks per-slot progress/retry (`FR-AI-12`), changes the port and tool schema.
- (c) Backend-assigned per-slot steer: needs a new vocabulary, may clash with category counts. Add later only if a live run shows (a) is not enough.
