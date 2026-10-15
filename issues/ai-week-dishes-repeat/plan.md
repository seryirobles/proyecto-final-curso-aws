# Plan — issue 18 `ai-week-dishes-repeat`

## Expected behaviour (cite `G-95`, Part AE)
- **E1** Each AI slot of a run SHALL receive the names of the dishes produced earlier in the run. (`FR-AI-06`, `G-95`)
- **E2** …the names of the meals already in the week (candidates and definitives). (`FR-AI-06`, `G-95`)
- **E3** In `mix`, …the library picks of the run. (`FR-AI-06`, `G-94`, `G-95`)
- **E4** A retried slot SHALL receive the week's other dishes. (`FR-AI-06`, `G-95`)
- **E5** Those names SHALL reach the model text. (`FR-AI-06`, `G-95`)
- **E6** After each AI slot, the category needs given to the next slot SHALL be reduced by the category of the recipe just written. (`FR-AI-04`, `FR-AI-11`, `G-71`, `G-95`)

## Fix design
- Add a field to `CategoryPrompt` for the names to avoid, and a new prompt version v5 with a template for them (`FR-AI-14`); v4 stays untouched.
- `_fill_slots` / `run_slot_retry` collect the names (week meals, library picks, dishes written so far) and reduce the needs after each AI slot.
- `bedrock._render` renders the names into the model text.
- v5 is selected through `AI_PROMPT_VERSION_ID` in the deployment config (the owner's).
- Name matching stays `domain.text.normalize`.

## Rejected
(b) one call for several slots, (c) per-slot steer — see analysis.md.

## Tests that define solved
`tests/backend/core/tests/application/test_week_generation_variety.py` (E1–E4) and `tests/backend/lambda_ai/tests/test_bedrock_week_variety.py` (E5). They use the newest prompt-registry key and assert no field name. **E6 has no test yet:** the implementer adds one (category needs shrink across AI slots; a rule capping a category is not overfilled).
