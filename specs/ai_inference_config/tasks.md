# ai_inference_config - Tasks

- [x] T1 - Add `adapters/inference_config.py`: `InferenceConfigError`, `InferenceSettings`, `load_inference_settings` with the domains, blank-as-unset and the error log (no credentials). Covers: R15, R16, R17, R18.
- [x] T2 - Add `converse_kwargs(settings)`: maxTokens/temperature/topP, serviceTier (omit standard), reasoningConfig (omit when off, default effort low), raise InferenceConfigError (one error log) for temperature/topP under effort high, never topK/stopSequences/guardrail/cache point. Covers: R2, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14.
- [x] T3 - Wire `bedrock.generate` to read settings per call and merge kwargs; keep the `AI_MODEL_ID` override; remove the hardcoded `_MAX_TOKENS` path. Covers: R1, R2, R3.
- [x] T4 - Test unset env gives exactly `modelId`, `messages`, `inferenceConfig={"maxTokens": 4096}`. Covers: R2.
- [x] T5 - Tests for each variable mapping (`AI_MODEL_ID`, `AI_MAX_TOKENS`, `AI_TEMPERATURE`, `AI_TOP_P`, tier priority/flex/standard, reasoning on with and without effort, reasoning off). Covers: R3, R4, R5, R6, R7, R8, R9, R10, R11.
- [x] T6 - Tests for effort high: temperature/topP set raises before the client is called with one error log naming them; reasoning off plus high keeps them; no topK/stopSequences/guardrail/cache point in any case. Covers: R12, R13, R14.
- [x] T7 - Tests for invalid values (each variable: out of range, non-numeric, NaN, bad enum): raises before the client is called, one error log naming the variable, sentinel credential absent from logs and message; blank string treated as unset. Covers: R15, R16, R17, R18.
- [x] T8 - Test a response with a `reasoningContent` block before the `toolUse` block parses. Covers: R19.
- [x] T9 - Test single-recipe and week jobs through the handler send identical kwargs. Covers: R20, R1.
- [x] T10 - Edit `docs/local_development.md` section 3 (six variables, accepted values, defaults, reasoning-tokens-bill-as-output note). The `AI_MODEL_ID` example and the Marketplace paragraph were already rewritten for Nova by the leader (owner command 2026-10-11); do not redo them. Covers: R21.
- [x] T11 - `docs/architecture.md` section 1.2.6 env table: done by the leader on the owner's command 2026-10-11. Covers: R22.
- [x] T2b - Under reasoning on + effort high, omit `maxTokens` from `converse_kwargs` even when `AI_MAX_TOKENS` is set (no error); tests for effort high with and without `AI_MAX_TOKENS`, and for reasoning off or low keeping `maxTokens`. Covers: R23.
- [x] T11b - Change `BEDROCK_MODEL_ID` to `eu.amazon.nova-2-lite-v1:0` and update `test_bedrock.py:90`. Covers: R3.
- [x] T12 - Add the doc test asserting all variable names appear in both docs. Covers: R21, R22.
- [x] T13 - Run `./init.sh`; record the R to test table in `progress/impl_ai_inference_config.md`. Covers: R1-R22.
