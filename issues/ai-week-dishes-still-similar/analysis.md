# Issue 19 — AI-only week still repeats dishes after prompt v5

**Defect:** the v5 avoid list reaches the model, but it is the only concrete dish content in a generic prompt and it bans names only, so Nova 2 Lite copies from it, sometimes verbatim. With no category rules, the prompt also carries a dangling `remaining needs: .` line.

Cross-reference: issue 18 (`issues/ai-week-dishes-repeat/`, `G-95`, Part AE) added the list. Issue 18 is not reopened; its E1-E6 hold.

## Reproduction (local DynamoDB, read-only scan)
- Run `PETICIONIA#103190fc…`: `ai_only`, `2026-W42`, `versionPrompt=v5`, no category counts, pins or disabled days; all 14 slots `done`.
- `SEMANA#2026-W42` holds 14 candidates, all from this run; the week was empty before it.
  - The first four slots vary: Ensalada de Quinoa…, Lasaña…, Burrito…, Budín de Lentejas…
  - From 3-1 on, 9 of the 10 dishes are "Budín de X con Quinoa y Yogur de Chía".
  - The exact name "Budín de Calabaza…" appears at 3-2, 5-1, 6-1, 6-2 and 7-1.
- Re-rendering the 6-1 prompt offline with `bedrock._render(build_category_prompt((), "v5", names))` gives `This week's remaining needs: .` and then `Dishes already planned …: …; Budín de Calabaza con Quinoa y Yogur de Chía; … Do not repeat or closely imitate any of them; produce a clearly different dish.` The model returned a name already in that list.
- The live model was not called again: its output varies per call and each call costs money. "Copies from the list" is inferred from the stored outcome.

## Evidence
- **The list is delivered.**
  - `week_generation.py:170-184` adds `written.name` (the `nombrePlato` the user sees) after every slot that writes a dish. It is `None` only on failure or when a definitive outranks the slot (`:133`); neither happened here.
  - `_render` (`bedrock.py:48-50`) does not truncate the list.
  - The local worker uses the same `handle` and `BedrockAiProvider` (`wiring.py:40`).
  - The issue 18 tests pass.
- **Why it still repeats.**
  - The instruction covers names only: it does not ask the model to avoid the same main ingredient or style, and nothing positively asks for variety.
  - The list is the last dish content before the output instruction.
  - Temperature and topP are unset (model defaults) and reasoning is off.
  - No prompt caching (`converse_kwargs`, R14).
- **Rules and pins:** ruled out; the run carried none.
- **Capturing the prompt:** nothing logs it. `_render` is pure, so the prompt for slot n is `_render(build_category_prompt(needs, version, names of slots 1..n-1))`.

## Root cause
- `ai_prompt.py:117-120` (`AVOID_NAMES_TEMPLATE_V5`): a negative, names-only instruction with no positive steer, rendered last before the output instruction (`bedrock.py:48-50`).
- `CATEGORY_FRAMING_TEMPLATE_V2` is always rendered with `${needs}`, even when there are none (`bedrock.py:46-47`).
- This falls short of `G-95`'s intent and of `FR-AI-06`'s varied menus.

## Classification — `defect` (prompt quality)
Owner ruling (2026-10-12): option (w) within `G-95` and `FR-AI-14`, as a new prompt version v6, no new Part. Best effort accepted for exact and near-duplicate names.

## Blast radius (owner ruling: general fix)
- Per-slot retry and `mix` use the same `_fill_slots` and `_render`, so v6 covers them.
- The empty-needs line affects every v1-v5 week-slot prompt without rules. Fixed in v6 only; v1-v5 stay byte-identical (`FR-AI-14`).
- Single-recipe generation is a separate path and is not affected.

## Options considered
(p) plan-then-fill and (c) per-slot steer were set aside by the owner (hallucination risk of naming first, new vocabulary); (w) chosen.
