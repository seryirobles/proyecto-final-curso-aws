# Tasks — issue 19 `ai-week-dishes-still-similar`

- [x] T1 — Move `tests/backend/lambda_ai/tests/test_prompt_week_variety_v6.py` to `backend/lambda_ai/tests/` verbatim. Confirm 5 red (E2, E3, E4 x2, E5) and 7 green. Covers: E1-E5.
- [x] T2 — Add v6 to `PROMPT_INSTRUCTION_VERSIONS` with a needs-free category framing and a separate needs sentence; v1-v5 untouched. Covers: E4, E5.
- [x] T3 — Add the v6 avoid template: names plus main ingredient and style, followed by a positive cuisine/variety steer. Covers: E1, E2, E3.
- [x] T4 — `bedrock._render`: render the needs sentence only when needs exist; keep the v1-v5 output byte-identical. Covers: E4, E5.
- [x] T5 — Consequential edits: registry set in `core/tests/domain/test_ai_prompt.py` (plus the field set if a field is added), and `AI_PROMPT_VERSION_ID=v6` in `docs/local_development.md`. Covers: E5.
- [x] T6 — `./init.sh` green; record the trace in `progress/impl_ai_week_dishes_still_similar.md`. Owner: set `AI_PROMPT_VERSION_ID=v6` in the deployed config and re-run an AI-only week (best effort, no automated check).
