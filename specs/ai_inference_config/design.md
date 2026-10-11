# ai_inference_config - Design

Layer: `lambda_ai` adapter only (`docs/architecture.md` section 3). `core/` and the
`AiProvider` port are untouched; both generation use cases already call
`AiProvider.generate`, so one adapter change covers single-recipe and week jobs (R20).

## Files

| File | Change |
|---|---|
| `backend/lambda_ai/src/planner_ai/adapters/inference_config.py` | new |
| `backend/lambda_ai/src/planner_ai/adapters/bedrock.py` | `generate` builds kwargs from the settings; `_MAX_TOKENS` replaced by `DEFAULT_MAX_TOKENS = 4096` in the new module |
| `docs/local_development.md` | section 3 worker block: add the six variables (commented, with defaults) and a short table; `AI_MODEL_ID` example becomes `eu.amazon.nova-2-lite-v1:0`; the GPT-5.6 Terra Marketplace paragraph is rewritten for Nova |
| `docs/architecture.md` | done by the leader on the owner's command (section 1.2.6 env table); the implementer does not touch it |
| `.vscode/launch.json` | owner edits (gitignored); not touched by the implementer |

## Signatures

```python
# adapters/inference_config.py
class InferenceConfigError(AiProviderError): ...   # reuses the existing per-slot failure path

@dataclass(frozen=True)
class InferenceSettings:
    max_tokens: int = 4096
    temperature: float | None = None
    top_p: float | None = None
    service_tier: Literal["standard", "priority", "flex"] = "standard"
    reasoning: bool = False
    effort: Literal["low", "medium", "high"] = "low"

def load_inference_settings(environ: Mapping[str, str]) -> InferenceSettings
def converse_kwargs(settings: InferenceSettings) -> dict[str, Any]
    # inferenceConfig, plus serviceTier / additionalModelRequestFields only when needed
```

`bedrock.generate` calls `load_inference_settings(os.environ)` on every call (R1) and
merges `converse_kwargs` into `converse(modelId=..., messages=..., **kwargs)`. A
config error raised there is outside the boto `try`, so it is not re-wrapped as
"Bedrock invocation failed". `_extract_text` already picks the first block whose
`text` is a string, so a `reasoningContent` block is skipped (R19); a test locks it in.

## Variables and domains

| Variable | Accepted | Default (unset) | Sent as |
|---|---|---|---|
| `AI_MODEL_ID` | non-empty string | code constant (unchanged) | `modelId` |
| `AI_REASONING_ENABLED` | `true` / `false` | `false` | `additionalModelRequestFields.reasoningConfig.type` |
| `AI_REASONING_EFFORT` | `low` / `medium` / `high` | `low` | `reasoningConfig.maxReasoningEffort`, only when reasoning on |
| `AI_MAX_TOKENS` | integer 1-65000 | 4096 | `inferenceConfig.maxTokens` |
| `AI_TEMPERATURE` | float 0-1 | unset (model default 0.7) | `inferenceConfig.temperature` |
| `AI_TOP_P` | float 0-1 | unset (model default 0.9) | `inferenceConfig.topP` |
| `AI_SERVICE_TIER` | `standard` / `priority` / `flex` | `standard` (omitted) | `serviceTier.type` |

Enums and booleans match exact lowercase; whitespace is stripped and empty means unset
(R18; Terraform often emits `""`). Floats must be finite. Effort is validated even when
reasoning is off, so a typo is caught before reasoning is switched on. Reasoning tokens
are billed as output and count against `maxTokens`; raise `AI_MAX_TOKENS` when enabling
reasoning.

## Decisions

- **Invalid values: fail fast.** An out-of-domain value raises `InferenceConfigError`
  (an `AiProviderError`) before Bedrock is called, plus one `logger.error` naming the
  variable and its domain, never credentials (R15-R17). A silent fallback would let a
  typo (`prioirty`, `AI_MAX_TOKENS=40960`) quietly change spend and output, the same
  fail-closed stance as the SSM kill-switch (NFR-AI-01).
- **Effort high + temperature/topP: fail fast** (owner decision 2026-10-11). Bedrock
  rejects the combination, and a silent drop would let a setting stop applying
  unnoticed. It raises `InferenceConfigError` with one `logger.error` naming the
  conflicting variables (R12, R13). The rule fires only while reasoning is on; with
  reasoning off, effort high is inert and temperature/topP are sent (R5, R6, R11).
- **Model default:** `BEDROCK_MODEL_ID` becomes `eu.amazon.nova-2-lite-v1:0` (R3);
  `test_bedrock.py:90` asserts the old constant and must be updated.
- **No separate reasoning-token cap** (owner decision 2026-10-11): `AI_MAX_TOKENS`
  bounds reasoning plus answer.
- **Fixed in code** (R14): no `topK`, `stopSequences`, guardrail or cache point;
  client timeouts and forced JSON stay as today.
- Defaults reproduce today's call exactly (R2): unset reasoning and standard tier add
  no keys, and `maxTokens` stays 4096.

## Rejected alternatives

1. **Fall back to the default on invalid values.** Friendlier, but a mistyped tier or
   token cap would silently run with different cost and length while the operator
   believes the setting applied. Failing closed surfaces it on the first generation.
2. **Drop temperature/topP with a warning under effort high.** Keeps the service up,
   but the operator's setting stops applying without any failure. Rejected by the
   owner 2026-10-11 in favour of fail fast.
3. **One JSON blob variable (`AI_INFERENCE_CONFIG`).** One variable to deploy, but a
   single field is hard to override in Terraform or `launch.json`, and per-field
   validation messages get worse. Flat variables match the existing `AI_*` style.

## Tests

New `backend/lambda_ai/tests/test_inference_config.py` (pure parsing, `monkeypatch`
env) and additions to `test_bedrock.py` (fake client records `converse` kwargs,
`caplog` for warnings/errors, sentinel `AWS_BEARER_TOKEN_BEDROCK` for R17). R20: drive
a single-recipe and a week job through the handler with the fake client and assert the
same kwargs. R21/R22: a doc test in the style of
`backend/lambda_api/tests/test_local_development_env.py` asserting every name appears
in both docs.
